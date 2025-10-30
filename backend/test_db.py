import psycopg2
import json

# Test database connection
try:
    conn = psycopg2.connect(
        host="localhost",
        port="5434",
        database="reddit_db",
        user="postgres",
        password="password"
    )
    cursor = conn.cursor()
    
    print("✅ Successfully connected to PostgreSQL database!")
    
    # Test table creation
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cursor.fetchall()
    print(f"📋 Available tables: {tables}")
    
    # Test inserting sample data
    sample_data = {
        "keyword": "test coffee",
        "subreddit": "test_subreddit",
        "title": "Test Post Title",
        "content": "This is test content",
        "score": 42,
        "created_utc": 1234567890,
        "comments": ["Test comment 1", "Test comment 2"]
    }
    
    cursor.execute("""
        INSERT INTO reddit_data (keyword, subreddit, title, content, score, created_utc, comments)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (sample_data['keyword'], sample_data['subreddit'], sample_data['title'], 
          sample_data['content'], sample_data['score'], sample_data['created_utc'], 
          json.dumps(sample_data['comments'])))
    
    conn.commit()
    print("✅ Successfully inserted test data!")
    
    # Verify data was inserted
    cursor.execute("SELECT COUNT(*) FROM reddit_data;")
    count = cursor.fetchone()[0]
    print(f"📊 Total records in database: {count}")
    
    cursor.close()
    conn.close()
    print("✅ Database test completed successfully!")
    
except Exception as e:
    print(f"❌ Database test failed: {e}")
