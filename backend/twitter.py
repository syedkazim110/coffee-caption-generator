import tweepy
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Twitter API configuration
bearer_token = "AAAAAAAAAAAAAAAAAAAAAD9W4QEAAAAAl8irL%2FuYuAeIZOK8j%2FKc%2FDnQSeY%3DQ6y9Mr3RtlaPAKpj01kSwT4khUmw6iL9EFbOstOoLKFLVtmaRP"

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'reddit_db',
    'user': 'postgres',
    'password': 'password'
}

# Initialize Twitter client
client = tweepy.Client(bearer_token=bearer_token)

# Coffee-related keywords
keywords = ['almond milk', 'ryze coffee', 'mushroom coffee benefits', 'decaf coffee caffeine', 'iced matcha', 'specialty coffee barcelona', 
               'nescafe decaf coffee', 'best flavored coffee', 'benefits of mushroom coffee', 'nitro coffee near me', 'mushroom coffee caffeine', 
               'decaf flavored coffee', 'ryze mushroom', 'cold brew latte', 'vanilla cream cold brew', 'what is specialty coffee', 'ryze coffee reviews', 
               'how much caffeine in coffee', 'four sigmatic', 'stok cold brew', 'the best mushroom coffee', 'best cold brew coffee', 'white cloud coffee', 
               'good decaf coffee', 'instant coffee packets', 'caffeine in cold brew', 'best mushroom coffee', 'swiss water decaf coffee', 'specialty coffee paris', 
               'coffee near me', 'calories in oat milk latte', 'decaf coffee caffeine content', 'specialty coffee amsterdam', 'ryze', 
               'ono specialty coffee & matcha', 'what is matcha', 'specialty coffee london', 'hazelnut flavored coffee', 'coffee shop', 'matcha latte powder', 
               'flavored coffee creamer', 'organic mushroom coffee', 'matcha latte recipe', 'matcha latte caffeine', 'matcha near me', 'specialty coffee madrid', 
               'folgers instant coffee', 'flavored coffee pods', 'akasa specialty coffee', 'nitro coffee can', 'decaf coffee while pregnant', 'oat latte calories', 
               'specialty coffee association', 'strawberry matcha', 'cold brew recipe', 'decaf coffee benefits', 'how much caffeine in instant coffee', 
               'calories in oat milk', 'best decaf coffee', 'four sigmatic mushroom coffee', 'iced brown sugar latte', 'cat and cloud coffee', 
               'cold brew concentrate', 'cold and brew', 'specialty coffee singapore', 'iced latte with oat milk', 'dose mushroom coffee', 
               'mushroom coffee reviews', 'nitro cold brew', 'how much caffeine is in decaf coffee', 'does decaf coffee have caffeine', 
               'nescafe instant coffee', 'indonesia specialty coffee', 'cold brew coffee', 'decaf coffee pods', 'blueberry flavored coffee', 
               'how to make cold brew', 'ryze mushroom coffee reviews', 'cat cloud coffee', 'what is instant coffee', 'chai latte', 
               'nitro coffee wisma nugra santana', 'matcha latte with oat milk', 'specialty coffee roasters', 'whole bean decaf coffee', 
               'chai matcha latte', 'speciality coffee', 'caffeine in instant coffee', 'multi functional coffee table', 'how to make cold brew coffee', 
               'what is nitro coffee', 'what is decaf coffee', 'oat milk latte calories', 'specialty coffee shop', 'instant coffee powder', 
               'caramel flavored coffee', 'decaf coffee instant', 'chocolate flavored coffee', 'good instant coffee', 'matcha tea', 
               'is mushroom coffee good for you', 'instant coffee caffeine content', 'what is a decaf coffee', 'coconut flavored coffee', 
               'matcha latte near me', 'mushroom tea', 'mushroom coffee near me', 'instant espresso', 'decaf coffee meaning', 
               'flavored coffee beans', 'oat milk calories', 'ground coffee', 'what is cold brew', 'vanilla cold brew', 'ryze reviews', 'instant coffee calories', 
               'how to make instant coffee', 'decaf coffee pregnancy', 'how to make matcha latte', 'navy specialty coffee', 'matcha strawberry latte', 
               'everyday dose coffee', 'cold brew', 'vanilla oat milk latte', 'mushroom coffee amazon', 'iced latte', 'iced matcha latte', 
               'what is mushroom coffee', 'mushroom coffee ryze', 'matcha coffee', 'what is matcha latte', 'ryze mushroom coffee benefits', 
               'how to make flavored coffee', 'best pod coffee', 'instant coffee caffeine', 'matcha latte', 'how to cold brew coffee', 
               'specialty coffee beans', 'everyday dose', 'sweet cream cold brew', 'nescafe gold instant coffee', 'tiong hoe specialty coffee', 
               'matcha tea latte', 'organic decaf coffee', 'specialty coffee meaning', 'specialty instant coffee', 'the best instant coffee', 
               'cold brew espresso', 'how much caffeine in cold brew', 'matcha latte calories', 'best instant coffee', 'decaf coffee near me', 
               'matcha powder', 'specialty coffee near me', 'caffeine in decaf coffee', 'cloud coffee recipe', 'cold brew tea', 'social specialty coffee', 
               'matcha oat milk latte', 'is decaf coffee bad for you', 'organic instant coffee', 'nescafe coffee', 'instant coffee brands', 
               'how much caffeine in decaf coffee', 'nescafe', 'how to make matcha', 'rita specialty coffee', 'iced oat milk latte']

class TwitterScraper:
    def __init__(self):
        self.client = client
        self.connection = None
        
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
    
    def save_tweet_to_db(self, tweet, keyword):
        """Save a single tweet to the database"""
        if not self.connection:
            logger.error("No database connection available")
            return False
            
        try:
            cursor = self.connection.cursor()
            
            # Extract public metrics safely
            public_metrics = tweet.public_metrics or {}
            retweet_count = public_metrics.get('retweet_count', 0)
            like_count = public_metrics.get('like_count', 0)
            reply_count = public_metrics.get('reply_count', 0)
            quote_count = public_metrics.get('quote_count', 0)
            
            # Prepare the insert query
            insert_query = """
                INSERT INTO twitter_data 
                (tweet_id, keyword, text, author_id, created_at, language, 
                 retweet_count, like_count, reply_count, quote_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tweet_id) DO NOTHING
            """
            
            cursor.execute(insert_query, (
                tweet.id,
                keyword,
                tweet.text,
                tweet.author_id,
                tweet.created_at,
                tweet.lang,
                retweet_count,
                like_count,
                reply_count,
                quote_count
            ))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Error saving tweet to database: {e}")
            self.connection.rollback()
            return False
    
    def scrape_tweets_for_keyword(self, keyword, max_results=10):
        """Scrape tweets for a specific keyword and save to database"""
        try:
            logger.info(f"🔎 Searching Twitter for: {keyword}")
            
            tweets = self.client.search_recent_tweets(
                query=keyword,
                max_results=max_results,
                tweet_fields=["id", "text", "author_id", "created_at", "lang", "public_metrics"]
            )
            
            if tweets.data:
                saved_count = 0
                for tweet in tweets.data:
                    if self.save_tweet_to_db(tweet, keyword):
                        saved_count += 1
                        logger.info(f"✅ Saved tweet: {tweet.text[:100]}...")
                    else:
                        logger.warning(f"❌ Failed to save tweet: {tweet.text[:100]}...")
                
                logger.info(f"📊 Saved {saved_count}/{len(tweets.data)} tweets for keyword: {keyword}")
                return saved_count
            else:
                logger.info(f"❌ No tweets found for keyword: {keyword}")
                return 0
                
        except tweepy.TooManyRequests:
            logger.warning("⚠️ Rate limit exceeded. Waiting 15 minutes...")
            time.sleep(15 * 60)  # Wait 15 minutes
            return 0
        except tweepy.Unauthorized:
            logger.error("❌ Unauthorized access. Check your bearer token.")
            return 0
        except Exception as e:
            logger.error(f"❌ Error scraping tweets for '{keyword}': {e}")
            return 0
    
    def scrape_all_keywords(self, max_results_per_keyword=10, delay_between_requests=1):
        """Scrape tweets for all keywords"""
        if not self.connect_to_database():
            logger.error("Failed to connect to database. Exiting.")
            return
        
        total_tweets_saved = 0
        
        try:
            for i, keyword in enumerate(keywords, 1):
                logger.info(f"🚀 Processing keyword {i}/{len(keywords)}: {keyword}")
                
                tweets_saved = self.scrape_tweets_for_keyword(keyword, max_results_per_keyword)
                total_tweets_saved += tweets_saved
                
                # Add delay between requests to avoid rate limiting
                if i < len(keywords):  # Don't sleep after the last keyword
                    time.sleep(delay_between_requests)
            
            logger.info(f"🎉 Scraping completed! Total tweets saved: {total_tweets_saved}")
            
        except KeyboardInterrupt:
            logger.info("⚠️ Scraping interrupted by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error during scraping: {e}")
        finally:
            self.close_database_connection()
    
    def get_tweet_stats(self):
        """Get statistics about saved tweets"""
        if not self.connect_to_database():
            return
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Total tweets
            cursor.execute("SELECT COUNT(*) as total_tweets FROM twitter_data")
            total_tweets = cursor.fetchone()['total_tweets']
            
            # Tweets per keyword
            cursor.execute("""
                SELECT keyword, COUNT(*) as tweet_count 
                FROM twitter_data 
                GROUP BY keyword 
                ORDER BY tweet_count DESC 
                LIMIT 10
            """)
            top_keywords = cursor.fetchall()
            
            # Recent tweets
            cursor.execute("""
                SELECT COUNT(*) as recent_tweets 
                FROM twitter_data 
                WHERE scraped_at >= NOW() - INTERVAL '24 hours'
            """)
            recent_tweets = cursor.fetchone()['recent_tweets']
            
            logger.info(f"📊 Database Statistics:")
            logger.info(f"   Total tweets: {total_tweets}")
            logger.info(f"   Tweets in last 24h: {recent_tweets}")
            logger.info(f"   Top keywords by tweet count:")
            
            for row in top_keywords:
                logger.info(f"     - {row['keyword']}: {row['tweet_count']} tweets")
            
            cursor.close()
            
        except psycopg2.Error as e:
            logger.error(f"Error getting tweet statistics: {e}")
        finally:
            self.close_database_connection()

def main():
    """Main function to run the Twitter scraper"""
    scraper = TwitterScraper()
    
    # Show current stats
    scraper.get_tweet_stats()
    
    # Start scraping
    scraper.scrape_all_keywords(max_results_per_keyword=10, delay_between_requests=2)
    
    # Show updated stats
    scraper.get_tweet_stats()

if __name__ == "__main__":
    main()
