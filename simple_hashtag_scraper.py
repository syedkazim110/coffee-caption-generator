import json
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from datetime import datetime
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleHashtagScraper:
    def __init__(self):
        """Initialize simple hashtag scraper using coffee keywords"""
        # Load trending coffee keywords
        with open('trending_coffee_keywords.json', 'r') as f:
            data = json.load(f)
            self.coffee_keywords = data['trending_keywords']
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        logger.info(f"Loaded {len(self.coffee_keywords)} coffee keywords")

    def generate_logical_hashtags(self, keyword: str) -> List[Dict]:
        """Generate logical hashtags based on coffee knowledge"""
        hashtags = []
        
        # Clean keyword for hashtag creation
        clean_keyword = keyword.lower().replace(' ', '').replace('_', '')
        
        # Direct hashtag from keyword
        if len(clean_keyword) <= 25:  # Instagram hashtag limit
            hashtags.append({
                'hashtag': f'#{clean_keyword}',
                'source': 'generated_direct',
                'popularity_score': 70,
                'relevance_score': 1.0
            })
        
        # Word-based hashtags
        words = keyword.lower().split()
        for word in words:
            if len(word) > 2 and word not in ['the', 'is', 'to', 'in', 'how', 'what', 'with', 'and']:
                hashtags.append({
                    'hashtag': f'#{word}',
                    'source': 'generated_word',
                    'popularity_score': 60,
                    'relevance_score': 0.8
                })
        
        # Coffee-specific mappings
        coffee_mappings = {
            'cold brew': ['#coldbrew', '#coldbrewcoffee', '#icedcoffee'],
            'latte': ['#latte', '#latteart', '#coffeeart'],
            'matcha': ['#matcha', '#matchalatte', '#greentea'],
            'espresso': ['#espresso', '#espressoshot', '#strongcoffee'],
            'decaf': ['#decaf', '#decafcoffee', '#caffeinefree'],
            'instant coffee': ['#instantcoffee', '#quickcoffee'],
            'specialty coffee': ['#specialtycoffee', '#craftcoffee', '#artisancoffee'],
            'mushroom coffee': ['#mushroomcoffee', '#functionalcoffee'],
            'oat milk': ['#oatmilk', '#plantbased', '#dairyfreecoffee'],
            'almond milk': ['#almondmilk', '#nutmilk', '#plantbased'],
            'nitro coffee': ['#nitrocoffee', '#nitrobrew'],
            'chai latte': ['#chailatte', '#spicedlatte', '#chai']
        }
        
        # Add specific mappings
        for coffee_type, tags in coffee_mappings.items():
            if coffee_type in keyword.lower():
                for tag in tags:
                    hashtags.append({
                        'hashtag': tag,
                        'source': 'generated_mapped',
                        'popularity_score': 85,
                        'relevance_score': 0.9
                    })
        
        # General coffee hashtags (always relevant)
        general_tags = ['#coffee', '#coffeelover', '#coffeetime', '#caffeine', '#coffeegram']
        for tag in general_tags:
            hashtags.append({
                'hashtag': tag,
                'source': 'generated_general',
                'popularity_score': 95,
                'relevance_score': 0.7
            })
        
        return hashtags

    def scrape_hashtag_suggestions(self, keyword: str) -> List[Dict]:
        """Scrape hashtag suggestions from web sources"""
        hashtags = []
        
        try:
            # Try all-hashtag.com
            url = "https://www.all-hashtag.com/hashtag-generator.php"
            data = {'keyword': keyword}
            
            response = self.session.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                # Find hashtags in response
                found_hashtags = re.findall(r'#[a-zA-Z0-9_]{2,25}', text_content)
                
                for tag in found_hashtags:
                    hashtags.append({
                        'hashtag': tag.lower(),
                        'source': 'scraped_web',
                        'popularity_score': 75,
                        'relevance_score': self.calculate_relevance(tag, keyword)
                    })
                
                logger.info(f"Scraped {len(hashtags)} hashtags for '{keyword}'")
            
        except Exception as e:
            logger.warning(f"Failed to scrape hashtags for '{keyword}': {e}")
        
        return hashtags

    def calculate_relevance(self, hashtag: str, keyword: str) -> float:
        """Calculate relevance score between hashtag and keyword"""
        hashtag_clean = hashtag.replace('#', '').lower()
        keyword_clean = keyword.lower()
        
        # Exact match
        if hashtag_clean == keyword_clean.replace(' ', ''):
            return 1.0
        
        # Contains keyword words
        keyword_words = keyword_clean.split()
        for word in keyword_words:
            if word in hashtag_clean and len(word) > 2:
                return 0.8
        
        # Coffee-related terms
        coffee_terms = ['coffee', 'cafe', 'brew', 'espresso', 'latte', 'cappuccino', 
                       'matcha', 'chai', 'mocha', 'americano', 'macchiato', 'barista']
        
        for term in coffee_terms:
            if term in hashtag_clean:
                return 0.6
        
        return 0.3

    def process_keyword(self, keyword: str) -> List[Dict]:
        """Process a single keyword to get all relevant hashtags"""
        all_hashtags = []
        
        logger.info(f"Processing keyword: {keyword}")
        
        # 1. Generate logical hashtags
        generated = self.generate_logical_hashtags(keyword)
        all_hashtags.extend(generated)
        
        # 2. Try to scrape additional hashtags
        try:
            scraped = self.scrape_hashtag_suggestions(keyword)
            all_hashtags.extend(scraped)
            time.sleep(1)  # Rate limiting
        except Exception as e:
            logger.warning(f"Scraping failed for '{keyword}': {e}")
        
        # 3. Remove duplicates and merge
        unique_hashtags = self.remove_duplicates(all_hashtags)
        
        # 4. Sort by popularity and relevance
        unique_hashtags.sort(key=lambda x: (x['popularity_score'] + x['relevance_score'] * 50), reverse=True)
        
        logger.info(f"Found {len(unique_hashtags)} hashtags for '{keyword}'")
        return unique_hashtags

    def remove_duplicates(self, hashtags: List[Dict]) -> List[Dict]:
        """Remove duplicate hashtags and merge their data"""
        seen = {}
        
        for hashtag in hashtags:
            tag = hashtag['hashtag']
            
            if tag in seen:
                # Keep the one with higher popularity
                if hashtag['popularity_score'] > seen[tag]['popularity_score']:
                    seen[tag] = hashtag
            else:
                seen[tag] = hashtag
        
        return list(seen.values())

    def create_hashtag_knowledge_base(self) -> List[Dict]:
        """Create hashtag knowledge base for RAG system"""
        knowledge_base = []
        
        # Process a subset of keywords (or all if you want)
        sample_keywords = self.coffee_keywords[:20]  # Start with 20 keywords
        
        logger.info(f"Creating knowledge base for {len(sample_keywords)} keywords")
        
        for keyword in sample_keywords:
            hashtags = self.process_keyword(keyword)
            
            # Add to knowledge base
            for hashtag_data in hashtags:
                content = f"Hashtag {hashtag_data['hashtag']} is relevant for '{keyword}' coffee content. "
                content += f"It has popularity score {hashtag_data['popularity_score']} and relevance {hashtag_data['relevance_score']:.2f}. "
                content += f"Use this hashtag for posts about {keyword}."
                
                knowledge_base.append({
                    'hashtag': hashtag_data['hashtag'],
                    'content': content,
                    'metadata': {
                        'keyword': keyword,
                        'popularity_score': hashtag_data['popularity_score'],
                        'relevance_score': hashtag_data['relevance_score'],
                        'source': hashtag_data['source'],
                        'type': 'hashtag_knowledge'
                    }
                })
            
            # Small delay to be respectful
            time.sleep(0.5)
        
        logger.info(f"Created knowledge base with {len(knowledge_base)} hashtag entries")
        return knowledge_base

    def save_knowledge_base(self, knowledge_base: List[Dict], filename: str = 'coffee_hashtag_knowledge_base.json'):
        """Save hashtag knowledge base"""
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_entries': len(knowledge_base),
            'source': 'Coffee Keywords + Web Scraping',
            'description': 'Hashtag knowledge base for coffee content RAG system',
            'hashtags': knowledge_base
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Saved hashtag knowledge base to {filename}")

def main():
    """Run simple hashtag scraping"""
    scraper = SimpleHashtagScraper()
    
    print("🏷️  Simple Coffee Hashtag Scraper")
    print("=" * 40)
    
    # Create knowledge base
    print("\n📚 Creating hashtag knowledge base...")
    knowledge_base = scraper.create_hashtag_knowledge_base()
    
    # Save knowledge base
    scraper.save_knowledge_base(knowledge_base)
    
    print(f"\n✅ Successfully created hashtag knowledge base!")
    print(f"📊 Total hashtag entries: {len(knowledge_base)}")
    
    # Show sample results
    print("\n📋 Sample Hashtag Entries:")
    sample_hashtags = {}
    for entry in knowledge_base[:15]:
        hashtag = entry['hashtag']
        keyword = entry['metadata']['keyword']
        
        if keyword not in sample_hashtags:
            sample_hashtags[keyword] = []
        sample_hashtags[keyword].append(hashtag)
    
    for keyword, hashtags in list(sample_hashtags.items())[:5]:
        print(f"\n{keyword}:")
        print(f"  {', '.join(hashtags[:5])}")

if __name__ == "__main__":
    main()
