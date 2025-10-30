import requests
from bs4 import BeautifulSoup
import time
import csv
import json
import logging
from datetime import datetime
from dateutil import parser
import re
from urllib.parse import urljoin, urlparse
import hashlib
import random
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from psycopg2 import sql
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coffee_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CoffeeBlogScraper:
    def __init__(self):
        self.session = requests.Session()
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        self.current_ua_index = 0
        self.update_headers()
        self.articles = []
        self.seen_urls = set()
        self.seen_content_hashes = set()
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'port': 5434,
            'database': 'reddit_db',
            'user': 'postgres',
            'password': 'password'
        }
        self.db_connection = None
        
        # Source configurations with updated selectors and URLs
        self.sources = {
            'coffeereview': {
                'name': 'Coffee Review',
                'base_url': 'https://www.coffeereview.com',
                'list_url': 'https://www.coffeereview.com/reviews/',
                'article_selector': 'h3 a, .review-title a, .entry-title a, h2 a',
                'parser': self.parse_coffeereview
            },
            'perfectdailygrind': {
                'name': 'Perfect Daily Grind',
                'base_url': 'https://perfectdailygrind.com',
                'list_url': 'https://perfectdailygrind.com/',
                'article_selector': 'h2 a, .entry-title a, .post-title a, article h3 a',
                'parser': self.parse_perfectdailygrind
            },
            'sprudge': {
                'name': 'Sprudge',
                'base_url': 'https://sprudge.com',
                'list_url': 'https://sprudge.com/',
                'article_selector': 'h2 a, .entry-title a, .post-title a, h3 a',
                'parser': self.parse_sprudge
            },
            'baristamagazine': {
                'name': 'Barista Magazine',
                'base_url': 'https://www.baristamagazine.com',
                'list_url': 'https://www.baristamagazine.com/category/coffee/',
                'article_selector': '.entry-title a, h2 a',
                'parser': self.parse_baristamagazine
            },
            'coffeegeek': {
                'name': 'CoffeeGeek',
                'base_url': 'https://coffeegeek.com',
                'list_url': 'https://coffeegeek.com/reviews/',
                'article_selector': 'h2 a, .entry-title a, .post-title a',
                'parser': self.parse_generic_coffee_site
            },
            'sweetmarias': {
                'name': 'Sweet Marias Coffee Supply',
                'base_url': 'https://sweetmarias.com',
                'list_url': 'https://sweetmarias.com/library/',
                'article_selector': 'h3 a, .entry-title a, .post-title a',
                'parser': self.parse_generic_coffee_site
            },
            'homebarista': {
                'name': 'Home-Barista',
                'base_url': 'https://www.home-barista.com',
                'list_url': 'https://www.home-barista.com/reviews/',
                'article_selector': 'h2 a, .entry-title a, .topic-title a',
                'parser': self.parse_generic_coffee_site
            },
            'coffeechronicler': {
                'name': 'Coffee Chronicler',
                'base_url': 'https://coffeechronicler.com',
                'list_url': 'https://coffeechronicler.com/',
                'article_selector': 'h2 a, .entry-title a, .post-title a',
                'parser': self.parse_generic_coffee_site
            },
            'driftaway': {
                'name': 'Driftaway Coffee',
                'base_url': 'https://driftaway.coffee',
                'list_url': 'https://driftaway.coffee/blog/',
                'article_selector': 'h2 a, .entry-title a, .post-title a',
                'parser': self.parse_generic_coffee_site
            },
            'coffeereviewmagazine': {
                'name': 'Coffee & Cocoa International',
                'base_url': 'https://www.coffeeandcocoa.net',
                'list_url': 'https://www.coffeeandcocoa.net/news/',
                'article_selector': 'h2 a, .entry-title a, .news-title a',
                'parser': self.parse_generic_coffee_site
            },
            'worldcoffeeresearch': {
                'name': 'World Coffee Research',
                'base_url': 'https://worldcoffeeresearch.org',
                'list_url': 'https://worldcoffeeresearch.org/news-and-resources/',
                'article_selector': 'h3 a, .entry-title a, .post-title a',
                'parser': self.parse_generic_coffee_site
            },
            'coffeeproject': {
                'name': 'The Coffee Project',
                'base_url': 'https://thecoffeeproject.com',
                'list_url': 'https://thecoffeeproject.com/blog/',
                'article_selector': 'h2 a, .entry-title a, .post-title a',
                'parser': self.parse_generic_coffee_site
            },
            'beancoffee': {
                'name': 'Bean Coffee',
                'base_url': 'https://www.beancoffee.com',
                'list_url': 'https://www.beancoffee.com/blog/',
                'article_selector': 'h2 a, .entry-title a, .post-title a',
                'parser': self.parse_generic_coffee_site
            },
            'coffeeaffection': {
                'name': 'Coffee Affection',
                'base_url': 'https://coffeeaffection.com',
                'list_url': 'https://coffeeaffection.com/',
                'article_selector': 'h2 a, .entry-title a, .post-title a',
                'parser': self.parse_generic_coffee_site
            }
        }

    def update_headers(self):
        """Update session headers with rotating user agent"""
        self.session.headers.update({
            'User-Agent': self.user_agents[self.current_ua_index],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)

    def make_request(self, url, retries=3, delay=2):
        """Make HTTP request with retry logic and anti-bot measures"""
        for attempt in range(retries):
            try:
                # Rotate user agent for each request
                self.update_headers()
                
                # Add random delay to appear more human-like
                if attempt > 0:
                    time.sleep(delay * (2 ** attempt) + random.uniform(1, 3))
                
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                # Additional delay after successful request
                time.sleep(random.uniform(1, 2))
                return response
                
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay * (2 ** attempt) + random.uniform(2, 5))
                else:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None

    def get_article_links(self, source_config):
        """Extract article links from a source's listing page"""
        logger.info(f"Fetching articles from {source_config['name']}")
        
        response = self.make_request(source_config['list_url'])
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        try:
            for link_elem in soup.select(source_config['article_selector']):
                href = link_elem.get('href')
                if href:
                    # Convert relative URLs to absolute
                    full_url = urljoin(source_config['base_url'], href)
                    if full_url not in self.seen_urls:
                        links.append(full_url)
                        self.seen_urls.add(full_url)
        except Exception as e:
            logger.error(f"Error extracting links from {source_config['name']}: {e}")
        
        logger.info(f"Found {len(links)} new articles from {source_config['name']}")
        return links

    def is_coffee_related(self, text):
        """Check if content is coffee-related"""
        coffee_keywords = [
            'coffee', 'espresso', 'latte', 'cappuccino', 'americano', 'mocha',
            'barista', 'brew', 'roast', 'bean', 'grind', 'cafe', 'caffeine',
            'arabica', 'robusta', 'specialty coffee', 'third wave', 'pour over',
            'french press', 'aeropress', 'chemex', 'v60', 'cold brew', 'nitro'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in coffee_keywords)

    def clean_text(self, text):
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        return text

    def get_content_hash(self, title, content):
        """Generate hash for duplicate detection"""
        combined = f"{title}{content}".lower()
        return hashlib.md5(combined.encode()).hexdigest()

    # Database Operations
    def connect_to_database(self):
        """Establish connection to PostgreSQL database"""
        try:
            self.db_connection = psycopg2.connect(**self.db_config)
            logger.info("Connected to PostgreSQL database")
            return True
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def close_database_connection(self):
        """Close database connection"""
        if self.db_connection:
            self.db_connection.close()
            logger.info("Database connection closed")

    def check_url_exists(self, url):
        """Check if URL already exists in database"""
        if not self.db_connection:
            return False
        
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("SELECT id FROM coffee_articles WHERE url = %s", (url,))
                return cursor.fetchone() is not None
        except psycopg2.Error as e:
            logger.error(f"Error checking URL existence: {e}")
            return False

    def check_content_hash_exists(self, content_hash):
        """Check if content hash already exists in database"""
        if not self.db_connection:
            return False
        
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("SELECT id FROM coffee_articles WHERE content_hash = %s", (content_hash,))
                return cursor.fetchone() is not None
        except psycopg2.Error as e:
            logger.error(f"Error checking content hash: {e}")
            return False

    def insert_article_to_db(self, article):
        """Insert single article into database with upsert logic"""
        if not self.db_connection:
            logger.error("No database connection available")
            return False

        try:
            # Generate content hash
            content_hash = self.get_content_hash(article['title'], article['content'])
            
            # Parse date
            published_date = None
            if article.get('date'):
                try:
                    published_date = parser.parse(article['date'])
                except:
                    pass

            with self.db_connection.cursor() as cursor:
                # Use ON CONFLICT to handle duplicates gracefully
                insert_query = """
                INSERT INTO coffee_articles 
                (title, content, rating, published_date, author, source, url, tags, content_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    rating = EXCLUDED.rating,
                    published_date = EXCLUDED.published_date,
                    author = EXCLUDED.author,
                    tags = EXCLUDED.tags,
                    content_hash = EXCLUDED.content_hash,
                    scraped_at = CURRENT_TIMESTAMP
                RETURNING id;
                """
                
                cursor.execute(insert_query, (
                    article['title'],
                    article['content'],
                    article.get('rating'),
                    published_date,
                    article.get('author'),
                    article['source'],
                    article['url'],
                    article.get('tags', []),
                    content_hash
                ))
                
                result = cursor.fetchone()
                self.db_connection.commit()
                
                if result:
                    logger.info(f"Article saved to database: {article['title'][:50]}...")
                    return True
                    
        except psycopg2.Error as e:
            logger.error(f"Database insert failed: {e}")
            self.db_connection.rollback()
            return False

    def batch_insert_articles(self, articles):
        """Batch insert articles into database for better performance"""
        if not self.db_connection or not articles:
            return 0

        successful_inserts = 0
        
        try:
            with self.db_connection.cursor() as cursor:
                # Prepare data for batch insert
                insert_data = []
                for article in articles:
                    # Generate content hash
                    content_hash = self.get_content_hash(article['title'], article['content'])
                    
                    # Parse date
                    published_date = None
                    if article.get('date'):
                        try:
                            published_date = parser.parse(article['date'])
                        except:
                            pass

                    insert_data.append((
                        article['title'],
                        article['content'],
                        article.get('rating'),
                        published_date,
                        article.get('author'),
                        article['source'],
                        article['url'],
                        article.get('tags', []),
                        content_hash
                    ))

                # Batch insert with ON CONFLICT handling
                insert_query = """
                INSERT INTO coffee_articles 
                (title, content, rating, published_date, author, source, url, tags, content_hash)
                VALUES %s
                ON CONFLICT (url) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    rating = EXCLUDED.rating,
                    published_date = EXCLUDED.published_date,
                    author = EXCLUDED.author,
                    tags = EXCLUDED.tags,
                    content_hash = EXCLUDED.content_hash,
                    scraped_at = CURRENT_TIMESTAMP;
                """
                
                from psycopg2.extras import execute_values
                execute_values(cursor, insert_query, insert_data, template=None, page_size=100)
                
                successful_inserts = len(insert_data)
                self.db_connection.commit()
                logger.info(f"Batch inserted {successful_inserts} articles to database")
                
        except psycopg2.Error as e:
            logger.error(f"Batch insert failed: {e}")
            self.db_connection.rollback()
            
        return successful_inserts

    def get_articles_from_db(self, source=None, limit=None, days_back=None):
        """Retrieve articles from database with optional filters"""
        if not self.db_connection:
            return []

        try:
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM coffee_articles"
                params = []
                conditions = []

                if source:
                    conditions.append("source = %s")
                    params.append(source)

                if days_back:
                    conditions.append("scraped_at >= NOW() - INTERVAL '%s days'")
                    params.append(days_back)

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY scraped_at DESC"

                if limit:
                    query += " LIMIT %s"
                    params.append(limit)

                cursor.execute(query, params)
                return cursor.fetchall()

        except psycopg2.Error as e:
            logger.error(f"Error retrieving articles from database: {e}")
            return []

    def get_database_stats(self):
        """Get database statistics"""
        if not self.db_connection:
            return {}

        try:
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Total articles
                cursor.execute("SELECT COUNT(*) as total FROM coffee_articles")
                total = cursor.fetchone()['total']

                # Articles by source
                cursor.execute("""
                    SELECT source, COUNT(*) as count 
                    FROM coffee_articles 
                    GROUP BY source 
                    ORDER BY count DESC
                """)
                by_source = cursor.fetchall()

                # Recent articles (last 7 days)
                cursor.execute("""
                    SELECT COUNT(*) as recent 
                    FROM coffee_articles 
                    WHERE scraped_at >= NOW() - INTERVAL '7 days'
                """)
                recent = cursor.fetchone()['recent']

                # Articles with ratings
                cursor.execute("""
                    SELECT COUNT(*) as with_ratings 
                    FROM coffee_articles 
                    WHERE rating IS NOT NULL AND rating != ''
                """)
                with_ratings = cursor.fetchone()['with_ratings']

                return {
                    'total_articles': total,
                    'by_source': by_source,
                    'recent_articles': recent,
                    'articles_with_ratings': with_ratings
                }

        except psycopg2.Error as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

    def parse_coffeereview(self, url):
        """Parse Coffee Review articles"""
        response = self.make_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        try:
            title_elem = soup.select_one('h1, .entry-title, .post-title')
            title = title_elem.get_text(strip=True) if title_elem else "No Title"
            
            # Try multiple selectors for rating
            rating_elem = soup.select_one('.review-template-rating, .rating, .score')
            rating = rating_elem.get_text(strip=True) if rating_elem else None
            
            # Extract content sections
            content_parts = []
            
            # Look for specific sections
            for section_name in ['Blind Assessment', 'Notes', 'Bottom Line', 'Review']:
                section = soup.find('h2', string=lambda t: t and section_name.lower() in t.lower())
                if section:
                    next_elem = section.find_next(['p', 'div'])
                    if next_elem:
                        content_parts.append(f"{section_name}: {next_elem.get_text(' ', strip=True)}")
            
            # If no specific sections found, get general content
            if not content_parts:
                content_elem = soup.select_one('.entry-content, .post-content, .content')
                if content_elem:
                    content_parts.append(content_elem.get_text(' ', strip=True))
            
            content = ' '.join(content_parts)
            
            # Extract date
            date_elem = soup.select_one('.date, .published, time')
            date = None
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                try:
                    date = parser.parse(date_text).isoformat()
                except:
                    pass
            
            return {
                'title': self.clean_text(title),
                'content': self.clean_text(content),
                'rating': rating,
                'date': date,
                'author': None,
                'source': 'Coffee Review',
                'url': url,
                'tags': ['coffee review', 'rating']
            }
            
        except Exception as e:
            logger.error(f"Error parsing Coffee Review article {url}: {e}")
            return None

    def parse_perfectdailygrind(self, url):
        """Parse Perfect Daily Grind articles"""
        response = self.make_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        try:
            title_elem = soup.select_one('h1, .entry-title')
            title = title_elem.get_text(strip=True) if title_elem else "No Title"
            
            content_elem = soup.select_one('.entry-content, .post-content, article')
            content = content_elem.get_text(' ', strip=True) if content_elem else ""
            
            author_elem = soup.select_one('.author, .by-author, .post-author')
            author = author_elem.get_text(strip=True) if author_elem else None
            
            date_elem = soup.select_one('.date, .published, time')
            date = None
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                try:
                    date = parser.parse(date_text).isoformat()
                except:
                    pass
            
            return {
                'title': self.clean_text(title),
                'content': self.clean_text(content),
                'rating': None,
                'date': date,
                'author': author,
                'source': 'Perfect Daily Grind',
                'url': url,
                'tags': ['coffee news', 'specialty coffee']
            }
            
        except Exception as e:
            logger.error(f"Error parsing Perfect Daily Grind article {url}: {e}")
            return None

    def parse_sprudge(self, url):
        """Parse Sprudge articles"""
        response = self.make_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        try:
            title_elem = soup.select_one('h1, .entry-title')
            title = title_elem.get_text(strip=True) if title_elem else "No Title"
            
            content_elem = soup.select_one('.entry-content, .post-content')
            content = content_elem.get_text(' ', strip=True) if content_elem else ""
            
            author_elem = soup.select_one('.author, .byline')
            author = author_elem.get_text(strip=True) if author_elem else None
            
            date_elem = soup.select_one('.date, time')
            date = None
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                try:
                    date = parser.parse(date_text).isoformat()
                except:
                    pass
            
            return {
                'title': self.clean_text(title),
                'content': self.clean_text(content),
                'rating': None,
                'date': date,
                'author': author,
                'source': 'Sprudge',
                'url': url,
                'tags': ['coffee news', 'coffee culture']
            }
            
        except Exception as e:
            logger.error(f"Error parsing Sprudge article {url}: {e}")
            return None

    def parse_baristamagazine(self, url):
        """Parse Barista Magazine articles"""
        response = self.make_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        try:
            title_elem = soup.select_one('h1, .entry-title')
            title = title_elem.get_text(strip=True) if title_elem else "No Title"
            
            content_elem = soup.select_one('.entry-content, .post-content')
            content = content_elem.get_text(' ', strip=True) if content_elem else ""
            
            author_elem = soup.select_one('.author, .post-author')
            author = author_elem.get_text(strip=True) if author_elem else None
            
            date_elem = soup.select_one('.date, time')
            date = None
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                try:
                    date = parser.parse(date_text).isoformat()
                except:
                    pass
            
            return {
                'title': self.clean_text(title),
                'content': self.clean_text(content),
                'rating': None,
                'date': date,
                'author': author,
                'source': 'Barista Magazine',
                'url': url,
                'tags': ['barista', 'coffee industry']
            }
            
        except Exception as e:
            logger.error(f"Error parsing Barista Magazine article {url}: {e}")
            return None

    def parse_generic_coffee_site(self, url):
        """Generic parser for coffee websites"""
        response = self.make_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        try:
            # Extract title using multiple selectors
            title_elem = soup.select_one('h1, .entry-title, .post-title, .article-title, .page-title')
            title = title_elem.get_text(strip=True) if title_elem else "No Title"
            
            # Extract content using multiple selectors
            content_elem = soup.select_one('.entry-content, .post-content, .article-content, .content, main, article')
            content = ""
            if content_elem:
                # Remove script and style elements
                for script in content_elem(["script", "style"]):
                    script.decompose()
                content = content_elem.get_text(' ', strip=True)
            
            # Extract author using multiple selectors
            author_elem = soup.select_one('.author, .by-author, .post-author, .article-author, .byline')
            author = author_elem.get_text(strip=True) if author_elem else None
            
            # Extract date using multiple selectors
            date_elem = soup.select_one('.date, .published, time, .post-date, .article-date')
            date = None
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                try:
                    date = parser.parse(date_text).isoformat()
                except:
                    pass
            
            # Determine source name from URL
            domain = urlparse(url).netloc.replace('www.', '')
            source_name = domain.replace('.com', '').replace('.org', '').replace('.net', '').title()
            
            return {
                'title': self.clean_text(title),
                'content': self.clean_text(content),
                'rating': None,
                'date': date,
                'author': author,
                'source': source_name,
                'url': url,
                'tags': ['coffee', 'specialty coffee']
            }
            
        except Exception as e:
            logger.error(f"Error parsing generic coffee site {url}: {e}")
            return None

    def scrape_source(self, source_key, max_articles=10):
        """Scrape articles from a specific source"""
        source_config = self.sources[source_key]
        logger.info(f"Starting to scrape {source_config['name']}")
        
        # Get article links
        links = self.get_article_links(source_config)
        
        # Limit number of articles
        links = links[:max_articles]
        
        scraped_count = 0
        for i, url in enumerate(links, 1):
            logger.info(f"Scraping article {i}/{len(links)} from {source_config['name']}")
            
            # Parse article
            article_data = source_config['parser'](url)
            
            if article_data:
                # Check if content is coffee-related
                if self.is_coffee_related(article_data['title'] + ' ' + article_data['content']):
                    # Check for duplicates
                    content_hash = self.get_content_hash(article_data['title'], article_data['content'])
                    if content_hash not in self.seen_content_hashes:
                        self.articles.append(article_data)
                        self.seen_content_hashes.add(content_hash)
                        scraped_count += 1
                        logger.info(f"Scraped: {article_data['title'][:100]}...")
                    else:
                        logger.info(f"Duplicate content skipped: {article_data['title'][:50]}...")
                else:
                    logger.info(f"Non-coffee content skipped: {article_data['title'][:50]}...")
            
            # Be respectful to servers
            time.sleep(1)
        
        logger.info(f"Completed scraping {source_config['name']}: {scraped_count} articles added")
        return scraped_count

    def scrape_all_sources(self, max_articles_per_source=10, save_to_db=True):
        """Scrape articles from all configured sources with database integration"""
        logger.info("Starting comprehensive coffee blog scraping with database integration")
        
        # Connect to database if requested
        db_connected = False
        if save_to_db:
            db_connected = self.connect_to_database()
            if db_connected:
                # Load existing URLs and content hashes to avoid duplicates
                self.load_existing_data_from_db()
        
        total_articles = 0
        
        for source_key in self.sources:
            try:
                count = self.scrape_source(source_key, max_articles_per_source)
                total_articles += count
            except Exception as e:
                logger.error(f"Error scraping {source_key}: {e}")
        
        # Save to database if connected and articles were scraped
        if db_connected and self.articles:
            try:
                db_count = self.batch_insert_articles(self.articles)
                logger.info(f"Database integration: {db_count} articles saved to PostgreSQL")
            except Exception as e:
                logger.error(f"Database save failed: {e}")
        
        # Close database connection
        if db_connected:
            self.close_database_connection()
        
        logger.info(f"Scraping completed! Total articles collected: {total_articles}")
        return total_articles

    def load_existing_data_from_db(self):
        """Load existing URLs and content hashes from database to avoid duplicates"""
        if not self.db_connection:
            return
        
        try:
            with self.db_connection.cursor() as cursor:
                # Load existing URLs
                cursor.execute("SELECT url FROM coffee_articles")
                existing_urls = cursor.fetchall()
                self.seen_urls.update([row[0] for row in existing_urls])
                
                # Load existing content hashes
                cursor.execute("SELECT content_hash FROM coffee_articles")
                existing_hashes = cursor.fetchall()
                self.seen_content_hashes.update([row[0] for row in existing_hashes])
                
                logger.info(f"Loaded {len(existing_urls)} existing URLs and {len(existing_hashes)} content hashes from database")
                
        except psycopg2.Error as e:
            logger.error(f"Error loading existing data from database: {e}")

    def save_to_csv(self, filename='coffee_articles.csv'):
        """Save articles to CSV file"""
        if not self.articles:
            logger.warning("No articles to save")
            return
        
        fieldnames = ['title', 'content', 'rating', 'date', 'author', 'source', 'url', 'tags']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for article in self.articles:
                # Convert tags list to string
                article_copy = article.copy()
                article_copy['tags'] = ', '.join(article['tags']) if article['tags'] else ''
                writer.writerow(article_copy)
        
        logger.info(f"Articles saved to {filename}")

    def save_to_json(self, filename='coffee_articles.json'):
        """Save articles to JSON file"""
        if not self.articles:
            logger.warning("No articles to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.articles, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"Articles saved to {filename}")

    def generate_summary(self, include_db_stats=True):
        """Generate comprehensive summary statistics"""
        summary_parts = []
        
        # Scraping session summary
        if self.articles:
            sources = {}
            total_articles = len(self.articles)
            
            for article in self.articles:
                source = article['source']
                sources[source] = sources.get(source, 0) + 1
            
            summary_parts.append(f"""
Current Scraping Session Summary
================================
Total Articles Scraped: {total_articles}
Unique Sources: {len(sources)}

Articles per Source:""")
            
            for source, count in sources.items():
                summary_parts.append(f"  • {source}: {count} articles")
            
            # Recent articles from this session
            dated_articles = [a for a in self.articles if a.get('date')]
            if dated_articles:
                dated_articles.sort(key=lambda x: x['date'], reverse=True)
                summary_parts.append(f"\nMost Recent Articles (This Session):")
                for article in dated_articles[:5]:
                    summary_parts.append(f"  • {article['title'][:60]}... ({article['source']})")
        else:
            summary_parts.append("No articles scraped in current session")
        
        # Database statistics
        if include_db_stats:
            try:
                # Temporarily connect to get stats
                temp_connected = False
                if not self.db_connection:
                    temp_connected = self.connect_to_database()
                
                if self.db_connection:
                    db_stats = self.get_database_stats()
                    if db_stats:
                        summary_parts.append(f"""

Database Statistics
===================
Total Articles in Database: {db_stats['total_articles']}
Recent Articles (7 days): {db_stats['recent_articles']}
Articles with Ratings: {db_stats['articles_with_ratings']}

Articles by Source (Database):""")
                        
                        for source_stat in db_stats['by_source']:
                            summary_parts.append(f"  • {source_stat['source']}: {source_stat['count']} articles")
                
                # Close temporary connection
                if temp_connected:
                    self.close_database_connection()
                    
            except Exception as e:
                logger.error(f"Error getting database stats for summary: {e}")
        
        return '\n'.join(summary_parts)

    def generate_database_report(self):
        """Generate detailed database report"""
        if not self.connect_to_database():
            return "Could not connect to database for report"
        
        try:
            report_parts = []
            
            # Get recent articles
            recent_articles = self.get_articles_from_db(limit=10)
            
            report_parts.append("""
Coffee Articles Database Report
===============================""")
            
            # Database stats
            db_stats = self.get_database_stats()
            if db_stats:
                report_parts.append(f"""
Overview:
  • Total Articles: {db_stats['total_articles']}
  • Recent Articles (7 days): {db_stats['recent_articles']}
  • Articles with Ratings: {db_stats['articles_with_ratings']}

By Source:""")
                
                for source_stat in db_stats['by_source']:
                    report_parts.append(f"  • {source_stat['source']}: {source_stat['count']} articles")
            
            # Recent articles
            if recent_articles:
                report_parts.append(f"\nMost Recent Articles:")
                for i, article in enumerate(recent_articles[:10], 1):
                    rating_text = f" (Rating: {article['rating']})" if article['rating'] else ""
                    report_parts.append(f"  {i}. {article['title'][:70]}...{rating_text}")
                    report_parts.append(f"     Source: {article['source']} | Scraped: {article['scraped_at'].strftime('%Y-%m-%d %H:%M')}")
            
            self.close_database_connection()
            return '\n'.join(report_parts)
            
        except Exception as e:
            logger.error(f"Error generating database report: {e}")
            self.close_database_connection()
            return f"Error generating database report: {e}"

def main():
    """Main function to run the coffee blog scraper with database integration"""
    scraper = CoffeeBlogScraper()
    
    # Scrape articles from all sources with database integration
    total_articles = scraper.scrape_all_sources(max_articles_per_source=5, save_to_db=True)
    
    if total_articles > 0:
        # Save results to files (dual storage)
        scraper.save_to_csv()
        scraper.save_to_json()
        
        # Print comprehensive summary
        print(scraper.generate_summary())
        
        # Show sample articles
        print("\nSample Articles:")
        print("=" * 50)
        for i, article in enumerate(scraper.articles[:3], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Content: {article['content'][:200]}...")
            if article['rating']:
                print(f"   Rating: {article['rating']}")
        
        # Generate database report
        print("\n" + scraper.generate_database_report())
        
    else:
        print("No articles were scraped. Check the logs for errors.")

if __name__ == "__main__":
    main()
