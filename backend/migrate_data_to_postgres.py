#!/usr/bin/env python3
"""
Migration Script: JSON/CSV → PostgreSQL
Migrates all file-based data to the PostgreSQL database
"""

import json
import csv
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
import os
from pathlib import Path

# Database connection parameters - use environment variables for Docker compatibility
import os
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'reddit_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres123'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

class DataMigrator:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.stats = {
            'generated_captions': 0,
            'coffee_context': 0,
            'hashtag_knowledge': 0,
            'trending_keywords': 0,
            'coffee_habits': 0,
            'social_media_posts': 0,
            'data_quality_reports': 0,
            'image_prompts': 0,
            'rag_documents': 0
        }
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("✓ Connected to PostgreSQL database")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to database: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✓ Database connection closed")
    
    def migrate_generated_captions(self):
        """Migrate llm_rag_captions.json and rag_generated_captions.json"""
        print("\n=== Migrating Generated Captions ===")
        
        json_files = [
            'llm_rag_captions.json',
            'rag_generated_captions.json'
        ]
        
        for json_file in json_files:
            if not os.path.exists(json_file):
                print(f"⊘ File not found: {json_file}")
                continue
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                captions = data.get('captions', [])
                timestamp = data.get('timestamp')
                method = data.get('method', 'Unknown')
                sources_used = data.get('sources_used', [])
                total_documents = data.get('total_documents', 0)
                llm_model = data.get('llm_used', 'Unknown')
                
                insert_query = """
                    INSERT INTO generated_captions 
                    (caption_text, base_caption, hashtags, keyword, context_snippets, 
                     method, sources_used, total_documents, llm_model, generation_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """
                
                batch_data = []
                for caption in captions:
                    batch_data.append((
                        caption.get('caption', ''),
                        caption.get('base_caption', ''),
                        json.dumps(caption.get('hashtags', [])),
                        caption.get('keyword', ''),
                        json.dumps(caption.get('context_snippets', [])),
                        caption.get('method', method),
                        json.dumps(sources_used),
                        total_documents,
                        llm_model,
                        caption.get('timestamp', timestamp)
                    ))
                
                execute_batch(self.cursor, insert_query, batch_data, page_size=100)
                self.conn.commit()
                
                count = len(batch_data)
                self.stats['generated_captions'] += count
                print(f"✓ Migrated {count} captions from {json_file}")
                
            except Exception as e:
                print(f"✗ Error migrating {json_file}: {e}")
                self.conn.rollback()
    
    def migrate_coffee_context(self):
        """Migrate coffee_context.json"""
        print("\n=== Migrating Coffee Context ===")
        
        json_file = 'coffee_context.json'
        if not os.path.exists(json_file):
            print(f"⊘ File not found: {json_file}")
            return
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            insert_query = """
                INSERT INTO coffee_context (category, term, usage_count)
                VALUES (%s, %s, %s)
                ON CONFLICT (category, term) DO UPDATE
                SET usage_count = coffee_context.usage_count + EXCLUDED.usage_count,
                    last_updated = NOW()
            """
            
            batch_data = []
            for category, terms in data.items():
                if category in ['timestamp', 'total_terms']:
                    continue
                
                if isinstance(terms, list):
                    for term in terms:
                        batch_data.append((category, term, 1))
            
            execute_batch(self.cursor, insert_query, batch_data, page_size=100)
            self.conn.commit()
            
            count = len(batch_data)
            self.stats['coffee_context'] += count
            print(f"✓ Migrated {count} coffee context terms")
            
        except Exception as e:
            print(f"✗ Error migrating coffee context: {e}")
            self.conn.rollback()
    
    def migrate_hashtag_knowledge(self):
        """Migrate hashtag_knowledge_base.json and coffee_hashtag_knowledge_base.json"""
        print("\n=== Migrating Hashtag Knowledge ===")
        
        json_files = [
            'hashtag_knowledge_base.json',
            'coffee_hashtag_knowledge_base.json'
        ]
        
        for json_file in json_files:
            if not os.path.exists(json_file):
                print(f"⊘ File not found: {json_file}")
                continue
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                insert_query = """
                    INSERT INTO hashtag_knowledge 
                    (hashtag, category, engagement_score, trending_score, platform, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (hashtag) DO UPDATE
                    SET engagement_score = GREATEST(hashtag_knowledge.engagement_score, EXCLUDED.engagement_score),
                        trending_score = GREATEST(hashtag_knowledge.trending_score, EXCLUDED.trending_score),
                        last_seen = NOW()
                """
                
                batch_data = []
                # Handle different JSON structures
                if isinstance(data, dict):
                    # Check if data has 'hashtags' key (coffee_hashtag_knowledge_base.json structure)
                    if 'hashtags' in data and isinstance(data['hashtags'], list):
                        for item in data['hashtags']:
                            if isinstance(item, dict):
                                hashtag = item.get('hashtag', '')
                                metadata = item.get('metadata', {})
                                batch_data.append((
                                    hashtag,
                                    metadata.get('keyword', 'general'),
                                    metadata.get('popularity_score', 0),
                                    metadata.get('relevance_score', 0),
                                    metadata.get('source', 'general'),
                                    json.dumps(item)
                                ))
                    else:
                        # Handle other dict structures
                        for key, value in data.items():
                            if isinstance(value, dict):
                                hashtag = value.get('hashtag', key)
                                batch_data.append((
                                    hashtag,
                                    value.get('category', 'general'),
                                    value.get('engagement_score', 0),
                                    value.get('trending_score', 0),
                                    value.get('platform', 'general'),
                                    json.dumps(value)
                                ))
                            elif isinstance(value, list):
                                for hashtag_item in value:
                                    # Check if item is a string or dict
                                    if isinstance(hashtag_item, str):
                                        hashtag = hashtag_item if hashtag_item.startswith('#') else f'#{hashtag_item}'
                                        batch_data.append((
                                            hashtag,
                                            key,
                                            0,
                                            0,
                                            'general',
                                            json.dumps({})
                                        ))
                                    elif isinstance(hashtag_item, dict):
                                        hashtag = hashtag_item.get('hashtag', '')
                                        batch_data.append((
                                            hashtag,
                                            key,
                                            hashtag_item.get('engagement_score', 0),
                                            hashtag_item.get('trending_score', 0),
                                            hashtag_item.get('platform', 'general'),
                                            json.dumps(hashtag_item)
                                        ))
                
                execute_batch(self.cursor, insert_query, batch_data, page_size=100)
                self.conn.commit()
                
                count = len(batch_data)
                self.stats['hashtag_knowledge'] += count
                print(f"✓ Migrated {count} hashtags from {json_file}")
                
            except Exception as e:
                print(f"✗ Error migrating {json_file}: {e}")
                self.conn.rollback()
    
    def migrate_trending_keywords(self):
        """Migrate trending_coffee_keywords.json and coffee_hashtags_trending.json"""
        print("\n=== Migrating Trending Keywords ===")
        
        json_files = [
            'trending_coffee_keywords.json',
            'coffee_hashtags_trending.json'
        ]
        
        for json_file in json_files:
            if not os.path.exists(json_file):
                print(f"⊘ File not found: {json_file}")
                continue
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                insert_query = """
                    INSERT INTO trending_keywords 
                    (keyword, trend_score, source, context)
                    VALUES (%s, %s, %s, %s)
                """
                
                batch_data = []
                
                # Handle trending_coffee_keywords.json structure
                if json_file == 'trending_coffee_keywords.json' and isinstance(data, dict):
                    # Extract the actual keyword list from the 'trending_keywords' key
                    keywords_list = data.get('trending_keywords', [])
                    
                    if isinstance(keywords_list, list):
                        for keyword in keywords_list:
                            # Validate it's actually a coffee keyword, not a metadata field
                            if isinstance(keyword, str) and len(keyword) > 0 and keyword not in ['timestamp', 'total_keywords']:
                                batch_data.append((
                                    keyword,
                                    50,  # Default trend score
                                    'trending_coffee_keywords.json',
                                    json.dumps({'source_file': json_file})
                                ))
                    
                    print(f"   Extracted {len(batch_data)} keywords from {json_file}")
                
                # Handle other JSON structures (coffee_hashtags_trending.json, etc.)
                elif isinstance(data, dict) and 'trending_keywords' not in data:
                    for keyword, info in data.items():
                        # Skip metadata fields
                        if keyword in ['timestamp', 'total_keywords', 'total', 'metadata']:
                            continue
                        
                        if isinstance(info, dict):
                            batch_data.append((
                                keyword,
                                info.get('score', 0),
                                info.get('source', 'unknown'),
                                json.dumps(info)
                            ))
                        else:
                            batch_data.append((
                                keyword,
                                0,
                                'json_file',
                                json.dumps({})
                            ))
                
                # Handle direct list format
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            keyword = item.get('keyword', '')
                            if keyword:
                                batch_data.append((
                                    keyword,
                                    item.get('score', 0),
                                    item.get('source', 'unknown'),
                                    json.dumps(item)
                                ))
                        elif isinstance(item, str):
                            batch_data.append((
                                item,
                                0,
                                json_file,
                                json.dumps({})
                            ))
                
                if batch_data:
                    execute_batch(self.cursor, insert_query, batch_data, page_size=100)
                    self.conn.commit()
                    
                    count = len(batch_data)
                    self.stats['trending_keywords'] += count
                    print(f"✓ Migrated {count} trending keywords from {json_file}")
                else:
                    print(f"⊘ No valid keywords found in {json_file}")
                
            except Exception as e:
                print(f"✗ Error migrating {json_file}: {e}")
                self.conn.rollback()
    
    def migrate_coffee_habits(self):
        """Migrate worldwide_coffee_habits.csv"""
        print("\n=== Migrating Coffee Habits ===")
        
        csv_file = 'worldwide_coffee_habits.csv'
        if not os.path.exists(csv_file):
            print(f"⊘ File not found: {csv_file}")
            return
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                insert_query = """
                    INSERT INTO coffee_habits 
                    (country, region, consumption_metric, metric_value, habit_type, data_source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                batch_data = []
                for row in reader:
                    # Extract relevant fields (adjust based on actual CSV structure)
                    batch_data.append((
                        row.get('country', ''),
                        row.get('region', ''),
                        row.get('metric', ''),
                        float(row.get('value', 0)) if row.get('value', '').replace('.', '').isdigit() else 0,
                        row.get('habit_type', ''),
                        'worldwide_coffee_habits.csv'
                    ))
                
                execute_batch(self.cursor, insert_query, batch_data, page_size=100)
                self.conn.commit()
                
                count = len(batch_data)
                self.stats['coffee_habits'] += count
                print(f"✓ Migrated {count} coffee habits records")
                
        except Exception as e:
            print(f"✗ Error migrating coffee habits: {e}")
            self.conn.rollback()
    
    def migrate_social_media_posts(self):
        """Migrate complete_social_media_posts.json"""
        print("\n=== Migrating Social Media Posts ===")
        
        json_file = 'complete_social_media_posts.json'
        if not os.path.exists(json_file):
            print(f"⊘ File not found: {json_file}")
            return
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            insert_query = """
                INSERT INTO social_media_posts 
                (platform, post_content, image_prompt, hashtags, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            batch_data = []
            posts = data if isinstance(data, list) else data.get('posts', [])
            
            for post in posts:
                batch_data.append((
                    post.get('platform', 'unknown'),
                    post.get('content', ''),
                    post.get('image_prompt', ''),
                    json.dumps(post.get('hashtags', [])),
                    'draft'
                ))
            
            execute_batch(self.cursor, insert_query, batch_data, page_size=100)
            self.conn.commit()
            
            count = len(batch_data)
            self.stats['social_media_posts'] += count
            print(f"✓ Migrated {count} social media posts")
            
        except Exception as e:
            print(f"✗ Error migrating social media posts: {e}")
            self.conn.rollback()
    
    def migrate_data_quality_reports(self):
        """Migrate data quality report JSON files"""
        print("\n=== Migrating Data Quality Reports ===")
        
        report_files = [f for f in os.listdir('.') if f.startswith('data_quality_report_') and f.endswith('.json')]
        
        if not report_files:
            print("⊘ No data quality report files found")
            return
        
        try:
            insert_query = """
                INSERT INTO data_quality_reports 
                (report_type, report_data, validation_status, issues_found, validation_timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            batch_data = []
            for report_file in report_files:
                with open(report_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract timestamp from filename
                timestamp_str = report_file.replace('data_quality_report_', '').replace('.json', '')
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                batch_data.append((
                    'data_quality',
                    json.dumps(data),
                    data.get('status', 'unknown'),
                    data.get('issues_count', 0),
                    timestamp
                ))
            
            execute_batch(self.cursor, insert_query, batch_data, page_size=100)
            self.conn.commit()
            
            count = len(batch_data)
            self.stats['data_quality_reports'] += count
            print(f"✓ Migrated {count} data quality reports")
            
        except Exception as e:
            print(f"✗ Error migrating data quality reports: {e}")
            self.conn.rollback()
    
    def migrate_image_prompts(self):
        """Migrate image prompts from various JSON files"""
        print("\n=== Migrating Image Prompts ===")
        
        # Check for image prompt files
        json_files = [f for f in os.listdir('.') if 'image' in f.lower() and f.endswith('.json')]
        
        if not json_files:
            print("⊘ No image prompt files found")
            return
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                insert_query = """
                    INSERT INTO image_prompts 
                    (prompt_text, style_keywords, generation_status)
                    VALUES (%s, %s, %s)
                """
                
                batch_data = []
                prompts = data if isinstance(data, list) else data.get('prompts', [])
                
                for prompt in prompts:
                    if isinstance(prompt, dict):
                        batch_data.append((
                            prompt.get('prompt', ''),
                            json.dumps(prompt.get('keywords', [])),
                            'pending'
                        ))
                    elif isinstance(prompt, str):
                        batch_data.append((prompt, json.dumps([]), 'pending'))
                
                if batch_data:
                    execute_batch(self.cursor, insert_query, batch_data, page_size=100)
                    self.conn.commit()
                    
                    count = len(batch_data)
                    self.stats['image_prompts'] += count
                    print(f"✓ Migrated {count} image prompts from {json_file}")
                
            except Exception as e:
                print(f"✗ Error migrating {json_file}: {e}")
                self.conn.rollback()
    
    def migrate_rag_documents(self):
        """Migrate coffee articles and other content to RAG documents"""
        print("\n=== Migrating RAG Documents ===")
        
        # Migrate from coffee_articles table
        try:
            select_query = """
                SELECT title, content, source, url, tags, scraped_at
                FROM coffee_articles
            """
            self.cursor.execute(select_query)
            articles = self.cursor.fetchall()
            
            insert_query = """
                INSERT INTO rag_documents 
                (document_text, document_title, source_type, source_url, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            batch_data = []
            for article in articles:
                title, content, source, url, tags, scraped_at = article
                batch_data.append((
                    content or '',
                    title,
                    'coffee_article',
                    url,
                    json.dumps({
                        'source': source,
                        'tags': tags,
                        'scraped_at': str(scraped_at)
                    })
                ))
            
            if batch_data:
                execute_batch(self.cursor, insert_query, batch_data, page_size=100)
                self.conn.commit()
                
                count = len(batch_data)
                self.stats['rag_documents'] += count
                print(f"✓ Migrated {count} coffee articles to RAG documents")
        
        except Exception as e:
            print(f"✗ Error migrating RAG documents: {e}")
            self.conn.rollback()
    
    def print_stats(self):
        """Print migration statistics"""
        print("\n" + "="*60)
        print("MIGRATION STATISTICS")
        print("="*60)
        
        total_records = 0
        for table, count in self.stats.items():
            if count > 0:
                print(f"{table:.<40} {count:>6} records")
                total_records += count
        
        print("-" * 60)
        print(f"{'TOTAL':.<40} {total_records:>6} records")
        print("="*60)
    
    def run_full_migration(self):
        """Run complete migration process"""
        print("\n" + "="*60)
        print("STARTING DATA MIGRATION TO POSTGRESQL")
        print("="*60)
        
        if not self.connect():
            return False
        
        try:
            # Run all migrations
            self.migrate_generated_captions()
            self.migrate_coffee_context()
            self.migrate_hashtag_knowledge()
            self.migrate_trending_keywords()
            self.migrate_coffee_habits()
            self.migrate_social_media_posts()
            self.migrate_data_quality_reports()
            self.migrate_image_prompts()
            self.migrate_rag_documents()
            
            # Print statistics
            self.print_stats()
            
            print("\n✓ Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            return False
        
        finally:
            self.close()

if __name__ == '__main__':
    migrator = DataMigrator()
    success = migrator.run_full_migration()
    exit(0 if success else 1)
