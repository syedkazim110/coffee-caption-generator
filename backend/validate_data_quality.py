#!/usr/bin/env python3
"""
Data Quality Validation Script
Validates data quality before and after cleaning operations
Generates comprehensive reports on data quality metrics
"""

import psycopg2
import pandas as pd
import os
import sys
from datetime import datetime
import json
import numpy as np

class DataQualityValidator:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': '5434',
            'database': 'reddit_db',
            'user': 'postgres',
            'password': 'password'
        }
        self.validation_results = {}
    
    def convert_numpy_types(self, obj):
        """Convert numpy types to native Python types for JSON serialization"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_numpy_types(item) for item in obj]
        return obj
    
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            return None
    
    def validate_database_quality(self):
        """Validate data quality in PostgreSQL database"""
        print("Validating database data quality...")
        
        conn = self.connect_to_database()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Reddit data validation
            reddit_metrics = self.validate_reddit_data(cursor)
            
            # Coffee articles validation
            coffee_metrics = self.validate_coffee_articles(cursor)
            
            # Twitter data validation
            twitter_metrics = self.validate_twitter_data(cursor)
            
            self.validation_results['database'] = {
                'reddit_data': reddit_metrics,
                'coffee_articles': coffee_metrics,
                'twitter_data': twitter_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Database validation failed: {str(e)}")
            return False
    
    def validate_reddit_data(self, cursor):
        """Validate Reddit data quality"""
        print("  Validating Reddit data...")
        
        metrics = {}
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM reddit_data")
        metrics['total_records'] = cursor.fetchone()[0]
        
        # Records with clean titles (no multiple spaces, not empty)
        cursor.execute("""
            SELECT COUNT(*) FROM reddit_data 
            WHERE title IS NOT NULL 
            AND title !~ '\s{2,}' 
            AND LENGTH(TRIM(title)) > 0
        """)
        metrics['clean_titles'] = cursor.fetchone()[0]
        
        # Records with clean content
        cursor.execute("""
            SELECT COUNT(*) FROM reddit_data 
            WHERE content IS NOT NULL 
            AND content !~ '\s{2,}' 
            AND LENGTH(TRIM(content)) > 0
        """)
        metrics['clean_content'] = cursor.fetchone()[0]
        
        # Records with valid keywords
        cursor.execute("""
            SELECT COUNT(*) FROM reddit_data 
            WHERE keyword IS NOT NULL 
            AND LENGTH(TRIM(keyword)) > 0
        """)
        metrics['valid_keywords'] = cursor.fetchone()[0]
        
        # Records with valid subreddits
        cursor.execute("""
            SELECT COUNT(*) FROM reddit_data 
            WHERE subreddit IS NOT NULL 
            AND LENGTH(TRIM(subreddit)) > 0
        """)
        metrics['valid_subreddits'] = cursor.fetchone()[0]
        
        # Duplicate check (based on title similarity)
        cursor.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT LOWER(TRIM(title))) as duplicates
            FROM reddit_data 
            WHERE title IS NOT NULL
        """)
        metrics['potential_duplicates'] = cursor.fetchone()[0]
        
        # Calculate quality percentages
        if metrics['total_records'] > 0:
            metrics['title_quality_percent'] = round((metrics['clean_titles'] / metrics['total_records']) * 100, 2)
            metrics['content_quality_percent'] = round((metrics['clean_content'] / metrics['total_records']) * 100, 2)
            metrics['keyword_completeness_percent'] = round((metrics['valid_keywords'] / metrics['total_records']) * 100, 2)
        
        return metrics
    
    def validate_coffee_articles(self, cursor):
        """Validate coffee articles data quality"""
        print("  Validating Coffee articles data...")
        
        metrics = {}
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM coffee_articles")
        metrics['total_records'] = cursor.fetchone()[0]
        
        # Records with clean titles
        cursor.execute("""
            SELECT COUNT(*) FROM coffee_articles 
            WHERE title IS NOT NULL 
            AND title !~ '\s{2,}' 
            AND LENGTH(TRIM(title)) > 0
        """)
        metrics['clean_titles'] = cursor.fetchone()[0]
        
        # Records with valid URLs
        cursor.execute("""
            SELECT COUNT(*) FROM coffee_articles 
            WHERE url IS NOT NULL 
            AND url ~ '^https?://[^\s/$.?#].[^\s]*$'
        """)
        metrics['valid_urls'] = cursor.fetchone()[0]
        
        # Records with standardized ratings
        cursor.execute("""
            SELECT COUNT(*) FROM coffee_articles 
            WHERE rating IS NOT NULL 
            AND rating ~ '^[0-9]+(\.[0-9]+)?/[0-9]+$'
        """)
        metrics['standardized_ratings'] = cursor.fetchone()[0]
        
        # Records with valid authors
        cursor.execute("""
            SELECT COUNT(*) FROM coffee_articles 
            WHERE author IS NOT NULL 
            AND LENGTH(TRIM(author)) > 0
        """)
        metrics['valid_authors'] = cursor.fetchone()[0]
        
        # Records with valid sources
        cursor.execute("""
            SELECT COUNT(*) FROM coffee_articles 
            WHERE source IS NOT NULL 
            AND LENGTH(TRIM(source)) > 0
        """)
        metrics['valid_sources'] = cursor.fetchone()[0]
        
        # Duplicate check (based on content hash)
        cursor.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT content_hash) as duplicates
            FROM coffee_articles
        """)
        metrics['potential_duplicates'] = cursor.fetchone()[0]
        
        # Calculate quality percentages
        if metrics['total_records'] > 0:
            metrics['title_quality_percent'] = round((metrics['clean_titles'] / metrics['total_records']) * 100, 2)
            metrics['url_quality_percent'] = round((metrics['valid_urls'] / metrics['total_records']) * 100, 2)
            metrics['rating_standardization_percent'] = round((metrics['standardized_ratings'] / metrics['total_records']) * 100, 2)
        
        return metrics
    
    def validate_twitter_data(self, cursor):
        """Validate Twitter data quality"""
        print("  Validating Twitter data...")
        
        metrics = {}
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM twitter_data")
        metrics['total_records'] = cursor.fetchone()[0]
        
        if metrics['total_records'] > 0:
            # Records with clean text
            cursor.execute("""
                SELECT COUNT(*) FROM twitter_data 
                WHERE text IS NOT NULL 
                AND text !~ '\s{2,}' 
                AND LENGTH(TRIM(text)) > 0
            """)
            metrics['clean_text'] = cursor.fetchone()[0]
            
            # Records with valid tweet IDs
            cursor.execute("""
                SELECT COUNT(*) FROM twitter_data 
                WHERE tweet_id IS NOT NULL 
                AND LENGTH(TRIM(tweet_id)) > 0
            """)
            metrics['valid_tweet_ids'] = cursor.fetchone()[0]
            
            # Duplicate check
            cursor.execute("""
                SELECT COUNT(*) - COUNT(DISTINCT tweet_id) as duplicates
                FROM twitter_data
            """)
            metrics['potential_duplicates'] = cursor.fetchone()[0]
            
            # Calculate quality percentages
            metrics['text_quality_percent'] = round((metrics['clean_text'] / metrics['total_records']) * 100, 2)
        else:
            metrics.update({
                'clean_text': 0,
                'valid_tweet_ids': 0,
                'potential_duplicates': 0,
                'text_quality_percent': 0
            })
        
        return metrics
    
    def validate_csv_quality(self, csv_file, data_type):
        """Validate CSV file data quality"""
        print(f"Validating CSV file: {csv_file}")
        
        if not os.path.exists(csv_file):
            print(f"  ⚠️  File not found: {csv_file}")
            return None
        
        try:
            # Read CSV in chunks to handle large files
            chunk_size = 1000
            total_rows = 0
            quality_metrics = {
                'total_rows': 0,
                'clean_rows': 0,
                'null_values': 0,
                'duplicate_rows': 0,
                'data_type': data_type
            }
            
            # Count total rows first
            for chunk in pd.read_csv(csv_file, chunksize=chunk_size):
                total_rows += len(chunk)
            
            quality_metrics['total_rows'] = total_rows
            
            # Analyze data quality
            seen_rows = set()
            
            for chunk in pd.read_csv(csv_file, chunksize=chunk_size):
                # Count null values
                quality_metrics['null_values'] += chunk.isnull().sum().sum()
                
                # Count clean rows (no multiple spaces in text fields)
                text_columns = []
                if data_type == 'reddit':
                    text_columns = ['title', 'content', 'keyword', 'subreddit']
                elif data_type == 'coffee':
                    text_columns = ['title', 'content', 'author', 'source']
                elif data_type == 'twitter':
                    text_columns = ['text', 'keyword']
                
                clean_rows_in_chunk = 0
                for _, row in chunk.iterrows():
                    is_clean = True
                    for col in text_columns:
                        if col in chunk.columns and pd.notna(row[col]):
                            if '  ' in str(row[col]):  # Multiple spaces
                                is_clean = False
                                break
                    if is_clean:
                        clean_rows_in_chunk += 1
                
                quality_metrics['clean_rows'] += clean_rows_in_chunk
                
                # Check for duplicates (simplified)
                if data_type == 'reddit' and 'title' in chunk.columns:
                    for title in chunk['title'].dropna():
                        title_key = str(title).lower().strip()
                        if title_key in seen_rows:
                            quality_metrics['duplicate_rows'] += 1
                        else:
                            seen_rows.add(title_key)
            
            # Calculate percentages
            if quality_metrics['total_rows'] > 0:
                quality_metrics['clean_percentage'] = round((quality_metrics['clean_rows'] / quality_metrics['total_rows']) * 100, 2)
                quality_metrics['null_percentage'] = round((quality_metrics['null_values'] / (quality_metrics['total_rows'] * len(chunk.columns))) * 100, 2)
            
            return quality_metrics
            
        except Exception as e:
            print(f"  ❌ Error validating {csv_file}: {str(e)}")
            return None
    
    def generate_quality_report(self):
        """Generate comprehensive data quality report"""
        report_filename = f"data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Validate CSV files
        csv_files = [
            ('reddit_data_export.csv', 'reddit'),
            ('coffee_articles_export.csv', 'coffee'),
            ('coffee_articles.csv', 'coffee'),
            # ('worldwide_coffee_habits.csv', 'coffee'),
        ]
        
        csv_results = {}
        for csv_file, data_type in csv_files:
            if os.path.exists(csv_file):
                csv_results[csv_file] = self.validate_csv_quality(csv_file, data_type)
        
        self.validation_results['csv_files'] = csv_results
        
        # Save report to JSON file
        with open(report_filename, 'w') as f:
            json.dump(self.convert_numpy_types(self.validation_results), f, indent=2)
        
        print(f"\n✅ Quality report saved to: {report_filename}")
        return report_filename
    
    def print_quality_summary(self):
        """Print a summary of data quality metrics"""
        print("\n" + "="*60)
        print("DATA QUALITY SUMMARY")
        print("="*60)
        
        if 'database' in self.validation_results:
            db_results = self.validation_results['database']
            
            print("\nDATABASE QUALITY:")
            print("-" * 30)
            
            # Reddit data summary
            reddit = db_results.get('reddit_data', {})
            if reddit.get('total_records', 0) > 0:
                print(f"Reddit Data:")
                print(f"  Total records: {reddit.get('total_records', 0)}")
                print(f"  Title quality: {reddit.get('title_quality_percent', 0)}%")
                print(f"  Content quality: {reddit.get('content_quality_percent', 0)}%")
                print(f"  Potential duplicates: {reddit.get('potential_duplicates', 0)}")
            
            # Coffee articles summary
            coffee = db_results.get('coffee_articles', {})
            if coffee.get('total_records', 0) > 0:
                print(f"\nCoffee Articles:")
                print(f"  Total records: {coffee.get('total_records', 0)}")
                print(f"  Title quality: {coffee.get('title_quality_percent', 0)}%")
                print(f"  URL quality: {coffee.get('url_quality_percent', 0)}%")
                print(f"  Rating standardization: {coffee.get('rating_standardization_percent', 0)}%")
                print(f"  Potential duplicates: {coffee.get('potential_duplicates', 0)}")
            
            # Twitter data summary
            twitter = db_results.get('twitter_data', {})
            print(f"\nTwitter Data:")
            print(f"  Total records: {twitter.get('total_records', 0)}")
            if twitter.get('total_records', 0) > 0:
                print(f"  Text quality: {twitter.get('text_quality_percent', 0)}%")
        
        if 'csv_files' in self.validation_results:
            print("\nCSV FILES QUALITY:")
            print("-" * 30)
            
            for filename, metrics in self.validation_results['csv_files'].items():
                if metrics:
                    print(f"\n{filename}:")
                    print(f"  Total rows: {metrics.get('total_rows', 0)}")
                    print(f"  Clean rows: {metrics.get('clean_percentage', 0)}%")
                    print(f"  Null values: {metrics.get('null_percentage', 0)}%")
                    print(f"  Duplicates: {metrics.get('duplicate_rows', 0)}")
        
        print("="*60)

def main():
    """Main function to run data quality validation"""
    validator = DataQualityValidator()
    
    print("Starting data quality validation...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Validate database quality
    if validator.validate_database_quality():
        print("✅ Database validation completed")
    else:
        print("❌ Database validation failed")
    
    # Generate comprehensive report
    report_file = validator.generate_quality_report()
    
    # Print summary
    validator.print_quality_summary()
    
    print(f"\n✅ Data quality validation completed")
    print(f"📊 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    main()
