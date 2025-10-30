import psycopg2
from psycopg2.extras import RealDictCursor
import csv
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseViewer:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5434,
            'database': 'reddit_db',
            'user': 'postgres',
            'password': 'password'
        }
        self.connection = None

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("✅ Successfully connected to PostgreSQL database")
            return True
        except psycopg2.Error as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    def get_table_data(self, table_name):
        """Get all data from a specific table"""
        if not self.connection:
            return []

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
                data = cursor.fetchall()
                logger.info(f"Retrieved {len(data)} records from {table_name}")
                return data
        except psycopg2.Error as e:
            logger.error(f"Error retrieving data from {table_name}: {e}")
            return []

    def get_table_stats(self, table_name):
        """Get statistics for a table"""
        if not self.connection:
            return {}

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get total count
                cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
                total = cursor.fetchone()['total']

                stats = {'total': total}

                # Get date range if scraped_at column exists
                try:
                    cursor.execute(f"SELECT MIN(scraped_at) as earliest, MAX(scraped_at) as latest FROM {table_name}")
                    date_range = cursor.fetchone()
                    if date_range['earliest']:
                        stats['earliest'] = date_range['earliest']
                        stats['latest'] = date_range['latest']
                except:
                    pass

                # Table-specific stats
                if table_name == 'reddit_data':
                    cursor.execute("SELECT COUNT(DISTINCT subreddit) as unique_subreddits FROM reddit_data")
                    stats['unique_subreddits'] = cursor.fetchone()['unique_subreddits']
                    
                    cursor.execute("SELECT COUNT(DISTINCT keyword) as unique_keywords FROM reddit_data")
                    stats['unique_keywords'] = cursor.fetchone()['unique_keywords']

                elif table_name == 'twitter_data':
                    cursor.execute("SELECT COUNT(DISTINCT keyword) as unique_keywords FROM twitter_data")
                    stats['unique_keywords'] = cursor.fetchone()['unique_keywords']
                    
                    cursor.execute("SELECT SUM(like_count) as total_likes, SUM(retweet_count) as total_retweets FROM twitter_data")
                    engagement = cursor.fetchone()
                    stats['total_likes'] = engagement['total_likes'] or 0
                    stats['total_retweets'] = engagement['total_retweets'] or 0

                elif table_name == 'coffee_articles':
                    cursor.execute("SELECT COUNT(DISTINCT source) as unique_sources FROM coffee_articles")
                    stats['unique_sources'] = cursor.fetchone()['unique_sources']
                    
                    cursor.execute("SELECT COUNT(*) as articles_with_ratings FROM coffee_articles WHERE rating IS NOT NULL AND rating != ''")
                    stats['articles_with_ratings'] = cursor.fetchone()['articles_with_ratings']

                return stats

        except psycopg2.Error as e:
            logger.error(f"Error getting stats for {table_name}: {e}")
            return {}

    def format_json_field(self, json_data):
        """Format JSON data for CSV display"""
        if not json_data:
            return ""
        
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except:
                return json_data

        if isinstance(json_data, list):
            return " | ".join(str(item) for item in json_data)
        elif isinstance(json_data, dict):
            return " | ".join(f"{k}: {v}" for k, v in json_data.items())
        else:
            return str(json_data)

    def format_datetime(self, dt):
        """Format datetime for CSV display"""
        if not dt:
            return ""
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return str(dt)

    def export_reddit_data(self):
        """Export Reddit data to CSV"""
        logger.info("Exporting Reddit data...")
        data = self.get_table_data('reddit_data')
        
        if not data:
            logger.warning("No Reddit data found")
            return

        filename = 'reddit_data_export.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'keyword', 'subreddit', 'title', 'content', 'score', 
                         'created_utc', 'comments', 'scraped_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in data:
                # Format the row for CSV
                csv_row = {
                    'id': row['id'],
                    'keyword': row['keyword'],
                    'subreddit': row['subreddit'],
                    'title': row['title'],
                    'content': row['content'][:500] + '...' if row['content'] and len(row['content']) > 500 else row['content'],
                    'score': row['score'],
                    'created_utc': row['created_utc'],
                    'comments': self.format_json_field(row['comments']),
                    'scraped_at': self.format_datetime(row['scraped_at'])
                }
                writer.writerow(csv_row)

        logger.info(f"✅ Reddit data exported to {filename}")

    def export_twitter_data(self):
        """Export Twitter data to CSV"""
        logger.info("Exporting Twitter data...")
        data = self.get_table_data('twitter_data')
        
        if not data:
            logger.warning("No Twitter data found")
            return

        filename = 'twitter_data_export.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'tweet_id', 'keyword', 'text', 'author_id', 'created_at',
                         'language', 'retweet_count', 'like_count', 'reply_count', 
                         'quote_count', 'scraped_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in data:
                csv_row = {
                    'id': row['id'],
                    'tweet_id': row['tweet_id'],
                    'keyword': row['keyword'],
                    'text': row['text'][:300] + '...' if row['text'] and len(row['text']) > 300 else row['text'],
                    'author_id': row['author_id'],
                    'created_at': self.format_datetime(row['created_at']),
                    'language': row['language'],
                    'retweet_count': row['retweet_count'],
                    'like_count': row['like_count'],
                    'reply_count': row['reply_count'],
                    'quote_count': row['quote_count'],
                    'scraped_at': self.format_datetime(row['scraped_at'])
                }
                writer.writerow(csv_row)

        logger.info(f"✅ Twitter data exported to {filename}")

    def export_coffee_articles(self):
        """Export Coffee articles data to CSV"""
        logger.info("Exporting Coffee articles data...")
        data = self.get_table_data('coffee_articles')
        
        if not data:
            logger.warning("No Coffee articles data found")
            return

        filename = 'coffee_articles_export.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'title', 'content', 'rating', 'published_date', 
                         'author', 'source', 'url', 'tags', 'scraped_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in data:
                csv_row = {
                    'id': row['id'],
                    'title': row['title'],
                    'content': row['content'][:500] + '...' if row['content'] and len(row['content']) > 500 else row['content'],
                    'rating': row['rating'],
                    'published_date': self.format_datetime(row['published_date']),
                    'author': row['author'],
                    'source': row['source'],
                    'url': row['url'],
                    'tags': self.format_json_field(row['tags']),
                    'scraped_at': self.format_datetime(row['scraped_at'])
                }
                writer.writerow(csv_row)

        logger.info(f"✅ Coffee articles data exported to {filename}")

    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        logger.info("Generating database summary report...")
        
        tables = ['reddit_data', 'twitter_data', 'coffee_articles']
        report_lines = []
        
        report_lines.append("=" * 60)
        report_lines.append("DATABASE SUMMARY REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        total_records = 0
        
        for table in tables:
            stats = self.get_table_stats(table)
            if stats:
                report_lines.append(f"{table.upper().replace('_', ' ')}:")
                report_lines.append("-" * 30)
                report_lines.append(f"  Total Records: {stats['total']:,}")
                total_records += stats['total']
                
                if 'earliest' in stats and stats['earliest']:
                    report_lines.append(f"  Date Range: {stats['earliest'].strftime('%Y-%m-%d')} to {stats['latest'].strftime('%Y-%m-%d')}")
                
                # Table-specific stats
                if table == 'reddit_data':
                    report_lines.append(f"  Unique Subreddits: {stats.get('unique_subreddits', 0)}")
                    report_lines.append(f"  Unique Keywords: {stats.get('unique_keywords', 0)}")
                
                elif table == 'twitter_data':
                    report_lines.append(f"  Unique Keywords: {stats.get('unique_keywords', 0)}")
                    report_lines.append(f"  Total Likes: {stats.get('total_likes', 0):,}")
                    report_lines.append(f"  Total Retweets: {stats.get('total_retweets', 0):,}")
                
                elif table == 'coffee_articles':
                    report_lines.append(f"  Unique Sources: {stats.get('unique_sources', 0)}")
                    report_lines.append(f"  Articles with Ratings: {stats.get('articles_with_ratings', 0)}")
                
                report_lines.append("")

        report_lines.append("=" * 60)
        report_lines.append(f"TOTAL RECORDS ACROSS ALL TABLES: {total_records:,}")
        report_lines.append("=" * 60)

        # Write to file
        with open('database_summary.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        # Also print to console
        print('\n'.join(report_lines))
        
        logger.info("✅ Summary report generated: database_summary.txt")

    def export_all_data(self):
        """Export all data from the database"""
        if not self.connect_to_database():
            return False

        try:
            # Export each table
            self.export_reddit_data()
            self.export_twitter_data()
            self.export_coffee_articles()
            
            # Generate summary report
            self.generate_summary_report()
            
            logger.info("🎉 All data exported successfully!")
            print("\n" + "="*50)
            print("EXPORT COMPLETE!")
            print("="*50)
            print("Files created:")
            print("  • reddit_data_export.csv")
            print("  • twitter_data_export.csv") 
            print("  • coffee_articles_export.csv")
            print("  • database_summary.txt")
            print("="*50)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during export: {e}")
            return False
        finally:
            self.close_connection()

def main():
    """Main function to run the database viewer"""
    print("🔍 Database Viewer - Exporting your existing data...")
    print("="*50)
    
    viewer = DatabaseViewer()
    success = viewer.export_all_data()
    
    if success:
        print("\n✅ Success! You can now view your data in the generated CSV files.")
        print("📊 Check database_summary.txt for an overview of your data.")
    else:
        print("\n❌ Export failed. Please check the logs for errors.")
        print("💡 Make sure your PostgreSQL database is running (docker-compose up)")

if __name__ == "__main__":
    main()
