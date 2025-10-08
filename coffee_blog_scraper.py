import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import logging
import psycopg2
from urllib.parse import urljoin, urlparse
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'reddit_db',
    'user': 'postgres',
    'password': 'password'
}

class CoffeeBlogScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.connection = None
        
        # Coffee blog sources
        self.blog_sources = {
            'sprudge': {
                'base_url': 'https://sprudge.com',
                'articles_selector': 'article',
                'title_selector': 'h2.entry-title a, h1.entry-title',
                'content_selector': '.entry-content',
                'date_selector': '.entry-date',
                'category_selector': '.entry-categories a'
            },
            'perfect_daily_grind': {
                'base_url': 'https://perfectdailygrind.com',
                'articles_selector': 'article',
                'title_selector': 'h2 a, h1',
                'content_selector': '.entry-content, .post-content',
                'date_selector': '.post-date, .entry-date',
                'category_selector': '.post-categories a'
            },
            'barista_magazine': {
                'base_url': 'https://www.baristamagazine.com',
                'articles_selector': 'article',
                'title_selector': 'h2 a, h1',
                'content_selector': '.entry-content, .post-content',
                'date_selector': '.post-date',
                'category_selector': '.post-categories a'
            }
        }
    
    def connect_to_database(self):
        """Establish connection to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            logger.info("Successfully connected to PostgreSQL database")
            return True
        except psycopg2.Error as e:
            logger.error(f"Error connecting to PostgreSQL database: {e}")
            return False
    
    def close_database_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def clean_text(self, text):
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove unwanted characters but keep emojis and basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\@\#\$\%\&\*\+\=\<\>\~\`\|\\\^\u00A0-\uFFFF]', '', text)
        
        return text[:5000]  # Limit length
    
    def extract_article_content(self, url, source_config):
        """Extract article content from a given URL"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.select_one(source_config['title_selector'])
            title = self.clean_text(title_elem.get_text()) if title_elem else ""
            
            # Extract content
            content_elem = soup.select_one(source_config['content_selector'])
            content = self.clean_text(content_elem.get_text()) if content_elem else ""
            
            # Extract date
            date_elem = soup.select_one(source_config['date_selector'])
            date_text = date_elem.get_text() if date_elem else ""
            
            # Extract categories/tags
            category_elems = soup.select(source_config['category_selector'])
            categories = [self.clean_text(cat.get_text()) for cat in category_elems]
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'date_text': date_text,
                'categories': categories,
                'scraped_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def get_article_urls(self, source_name, source_config, max_articles=20):
        """Get article URLs from a blog source"""
        try:
            # Try different common paths for recent articles
            paths_to_try = ['/', '/category/coffee/', '/coffee/', '/news/', '/articles/']
            
            all_urls = set()
            
            for path in paths_to_try:
                if len(all_urls) >= max_articles:
                    break
                    
                try:
                    url = urljoin(source_config['base_url'], path)
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find article links
                    articles = soup.select(source_config['articles_selector'])
                    
                    for article in articles[:max_articles]:
                        # Try to find article link
                        link_elem = article.select_one('a[href]')
                        if not link_elem:
                            link_elem = article.select_one(source_config['title_selector'])
                        
                        if link_elem and link_elem.get('href'):
                            article_url = urljoin(source_config['base_url'], link_elem['href'])
                            
                            # Filter for coffee-related content
                            if self.is_coffee_related(link_elem.get_text() or ""):
                                all_urls.add(article_url)
                                
                                if len(all_urls) >= max_articles:
                                    break
                    
                    time.sleep(1)  # Be respectful
                    
                except Exception as e:
                    logger.warning(f"Error getting articles from {url}: {e}")
                    continue
            
            logger.info(f"Found {len(all_urls)} article URLs from {source_name}")
            return list(all_urls)
            
        except Exception as e:
            logger.error(f"Error getting article URLs from {source_name}: {e}")
            return []
    
    def is_coffee_related(self, text):
        """Check if text is coffee-related"""
        coffee_keywords = [
            'coffee', 'espresso', 'latte', 'cappuccino', 'americano', 'macchiato',
            'cold brew', 'nitro', 'pour over', 'french press', 'aeropress',
            'barista', 'roast', 'bean', 'grind', 'brew', 'cafe', 'caffeine',
            'matcha', 'tea', 'specialty', 'origin', 'single origin', 'blend'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in coffee_keywords)
    
    def save_article_to_db(self, article_data, source_name):
        """Save article to database"""
        if not self.connection or not article_data:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            insert_query = """
                INSERT INTO blog_articles 
                (source, url, title, content, date_text, categories, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    content = EXCLUDED.content,
                    scraped_at = EXCLUDED.scraped_at
            """
            
            cursor.execute(insert_query, (
                source_name,
                article_data['url'],
                article_data['title'],
                article_data['content'],
                article_data['date_text'],
                json.dumps(article_data['categories']),
                article_data['scraped_at']
            ))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Error saving article to database: {e}")
            self.connection.rollback()
            return False
    
    def scrape_source(self, source_name, max_articles=20):
        """Scrape articles from a specific source"""
        if source_name not in self.blog_sources:
            logger.error(f"Unknown source: {source_name}")
            return 0
        
        source_config = self.blog_sources[source_name]
        logger.info(f"🔎 Scraping {source_name}...")
        
        # Get article URLs
        article_urls = self.get_article_urls(source_name, source_config, max_articles)
        
        if not article_urls:
            logger.warning(f"No articles found for {source_name}")
            return 0
        
        saved_count = 0
        
        for i, url in enumerate(article_urls, 1):
            logger.info(f"📄 Processing article {i}/{len(article_urls)}: {url}")
            
            # Extract article content
            article_data = self.extract_article_content(url, source_config)
            
            if article_data and article_data['content']:
                if self.save_article_to_db(article_data, source_name):
                    saved_count += 1
                    logger.info(f"✅ Saved: {article_data['title'][:100]}...")
                else:
                    logger.warning(f"❌ Failed to save: {article_data['title'][:100]}...")
            else:
                logger.warning(f"❌ No content extracted from: {url}")
            
            # Be respectful with delays
            time.sleep(2)
        
        logger.info(f"📊 Saved {saved_count}/{len(article_urls)} articles from {source_name}")
        return saved_count
    
    def scrape_all_sources(self, max_articles_per_source=15):
        """Scrape articles from all sources"""
        if not self.connect_to_database():
            logger.error("Failed to connect to database. Exiting.")
            return
        
        total_articles_saved = 0
        
        try:
            for source_name in self.blog_sources:
                logger.info(f"🚀 Starting scrape for {source_name}")
                
                articles_saved = self.scrape_source(source_name, max_articles_per_source)
                total_articles_saved += articles_saved
                
                # Delay between sources
                time.sleep(5)
            
            logger.info(f"🎉 Blog scraping completed! Total articles saved: {total_articles_saved}")
            
        except KeyboardInterrupt:
            logger.info("⚠️ Scraping interrupted by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error during scraping: {e}")
        finally:
            self.close_database_connection()
        
        return total_articles_saved

def main():
    """Main function to run the coffee blog scraper"""
    scraper = CoffeeBlogScraper()
    scraper.scrape_all_sources(max_articles_per_source=10)

if __name__ == "__main__":
    main()
