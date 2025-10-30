#!/usr/bin/env python3
"""
Re-migrate trending keywords with correct structure
"""

import json
import psycopg2
from psycopg2.extras import execute_batch

DB_CONFIG = {
    'dbname': 'reddit_db',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost',
    'port': '5434'
}

def migrate_trending_keywords():
    """Migrate all 169 trending keywords"""
    
    # Read the JSON file
    with open('trending_coffee_keywords.json', 'r') as f:
        data = json.load(f)
    
    keywords = data.get('trending_keywords', [])
    timestamp = data.get('timestamp')
    
    print(f"Found {len(keywords)} keywords in JSON file")
    
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Clear existing trending keywords
    cursor.execute("DELETE FROM trending_keywords WHERE source = 'trending_coffee_keywords.json'")
    
    # Insert all keywords
    insert_query = """
        INSERT INTO trending_keywords (keyword, trend_score, source, context)
        VALUES (%s, %s, %s, %s)
    """
    
    batch_data = []
    for idx, keyword in enumerate(keywords):
        # Use reverse index as trend score (first keywords are more trending)
        trend_score = len(keywords) - idx
        batch_data.append((
            keyword,
            trend_score,
            'trending_coffee_keywords.json',
            json.dumps({'timestamp': timestamp, 'rank': idx + 1})
        ))
    
    execute_batch(cursor, insert_query, batch_data, page_size=100)
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM trending_keywords WHERE source = 'trending_coffee_keywords.json'")
    count = cursor.fetchone()[0]
    
    print(f"✓ Successfully migrated {count} trending keywords to database")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    migrate_trending_keywords()
