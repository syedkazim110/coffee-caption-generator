#!/usr/bin/env python3
"""
Test script to verify hashtag loading from database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'reddit_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres123')
}

def test_hashtag_loading():
    """Test loading hashtags from database"""
    print("\n" + "="*60)
    print("TESTING HASHTAG DATABASE LOADING")
    print("="*60)
    
    try:
        # Connect to database
        print("\n1. Connecting to database...")
        connection = psycopg2.connect(**DB_CONFIG)
        print("   ✅ Connected successfully")
        
        # Ensure clean transaction state
        connection.rollback()
        print("   ✅ Transaction state cleaned")
        
        # Query hashtags
        print("\n2. Querying hashtag_knowledge table...")
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                hashtag,
                category,
                engagement_score,
                trending_score,
                platform
            FROM hashtag_knowledge
            ORDER BY trending_score DESC, engagement_score DESC
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        
        print(f"   ✅ Found {len(rows)} hashtags (showing top 10)")
        
        # Display sample hashtags
        print("\n3. Sample Hashtags:")
        print("-" * 60)
        for i, row in enumerate(rows, 1):
            print(f"   {i}. {row['hashtag']}")
            print(f"      Category: {row['category']}")
            print(f"      Engagement: {row['engagement_score']}")
            print(f"      Trending: {row['trending_score']}")
            print(f"      Platform: {row['platform']}")
            print()
        
        # Get total count
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM hashtag_knowledge")
        total_count = cursor.fetchone()[0]
        cursor.close()
        
        print(f"4. Total hashtags in database: {total_count}")
        
        connection.close()
        print("\n" + "="*60)
        print("✅ TEST PASSED: Hashtags are loading correctly!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("="*60)
        return False

if __name__ == '__main__':
    success = test_hashtag_loading()
    exit(0 if success else 1)
