#!/usr/bin/env python3
"""
Fix script to clear bad trending keywords and re-migrate correctly
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5433)),  # Docker maps to 5433 on host
    'database': os.getenv('DB_NAME', 'reddit_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres123')
}

def fix_trending_keywords():
    """Clear bad data and re-migrate trending keywords"""
    print("\n" + "="*60)
    print("FIXING TRENDING KEYWORDS")
    print("="*60)
    
    try:
        # Connect to database
        print("\n1. Connecting to database...")
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        print("   ✅ Connected successfully")
        
        # Step 1: Check current data
        print("\n2. Checking current trending keywords...")
        cursor.execute("SELECT keyword, trend_score, source FROM trending_keywords ORDER BY recorded_date DESC LIMIT 10")
        current_keywords = cursor.fetchall()
        print(f"   Found {len(current_keywords)} keywords (showing last 10):")
        for kw in current_keywords:
            print(f"      - {kw['keyword']} (score: {kw['trend_score']}, source: {kw['source']})")
        
        # Step 2: Clear all existing data
        print("\n3. Clearing existing trending keywords...")
        cursor.execute("DELETE FROM trending_keywords")
        deleted_count = cursor.rowcount
        connection.commit()
        print(f"   ✅ Deleted {deleted_count} old records")
        
        # Step 3: Load correct data from JSON
        print("\n4. Loading correct keywords from JSON...")
        with open('trending_coffee_keywords.json', 'r') as f:
            data = json.load(f)
        
        keywords_list = data.get('trending_keywords', [])
        print(f"   Found {len(keywords_list)} keywords in JSON file")
        
        # Step 4: Insert correct keywords
        print("\n5. Inserting correct keywords into database...")
        insert_query = """
            INSERT INTO trending_keywords (keyword, trend_score, source, context)
            VALUES (%s, %s, %s, %s)
        """
        
        inserted_count = 0
        for keyword in keywords_list:
            if isinstance(keyword, str) and len(keyword) > 0:
                cursor.execute(insert_query, (
                    keyword,
                    50,  # Default trend score
                    'trending_coffee_keywords.json',
                    json.dumps({'source_file': 'trending_coffee_keywords.json'})
                ))
                inserted_count += 1
        
        connection.commit()
        print(f"   ✅ Inserted {inserted_count} keywords")
        
        # Step 5: Verify the fix
        print("\n6. Verifying the fix...")
        cursor.execute("SELECT COUNT(*) as total FROM trending_keywords")
        total = cursor.fetchone()['total']
        print(f"   Total keywords in database: {total}")
        
        cursor.execute("""
            SELECT keyword, trend_score, source 
            FROM trending_keywords 
            ORDER BY recorded_date DESC 
            LIMIT 10
        """)
        sample_keywords = cursor.fetchall()
        print(f"\n   Sample keywords (first 10):")
        for i, kw in enumerate(sample_keywords, 1):
            print(f"      {i}. {kw['keyword']} (score: {kw['trend_score']})")
        
        cursor.close()
        connection.close()
        
        print("\n" + "="*60)
        print(f"✅ FIX COMPLETED SUCCESSFULLY!")
        print(f"   - Cleared {deleted_count} bad records")
        print(f"   - Inserted {inserted_count} correct keywords")
        print(f"   - Total keywords now: {total}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ FIX FAILED: {e}")
        print("="*60)
        if 'connection' in locals():
            connection.rollback()
            connection.close()
        return False

if __name__ == '__main__':
    success = fix_trending_keywords()
    exit(0 if success else 1)
