#!/usr/bin/env python3
"""
Database Initialization Script
Initializes the brand_profiles table and verifies database connectivity
"""

import psycopg2
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def check_database_connection():
    """Test database connection"""
    try:
        logger.info("Testing database connection...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"✅ Connected to PostgreSQL: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def check_table_exists(table_name='brand_profiles'):
    """Check if a table exists in the database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table_name,))
        
        exists = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return exists
    except Exception as e:
        logger.error(f"Error checking table existence: {e}")
        return False

def initialize_schema():
    """Initialize the brand_profiles table from SQL file"""
    try:
        logger.info("Initializing database schema...")
        
        # Read the SQL file
        with open('init_brand_schema.sql', 'r') as f:
            sql_script = f.read()
        
        # Execute the SQL script
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Execute the entire script
        cursor.execute(sql_script)
        conn.commit()
        
        logger.info("✅ Schema initialized successfully")
        
        # Verify the table was created
        cursor.execute("""
            SELECT COUNT(*) FROM brand_profiles;
        """)
        count = cursor.fetchone()[0]
        logger.info(f"✅ brand_profiles table created with {count} default record(s)")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing schema: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_setup():
    """Verify the database setup is correct"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'brand_profiles'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        logger.info(f"\n📊 Table Structure ({len(columns)} columns):")
        for col_name, col_type in columns:
            logger.info(f"   • {col_name}: {col_type}")
        
        # Check data
        cursor.execute("SELECT id, brand_name, brand_type, is_active FROM brand_profiles;")
        brands = cursor.fetchall()
        
        logger.info(f"\n📦 Current Brands ({len(brands)}):")
        for brand_id, name, brand_type, is_active in brands:
            status = "✅ ACTIVE" if is_active else "⚪ Inactive"
            logger.info(f"   • [{brand_id}] {name} ({brand_type}) - {status}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying setup: {e}")
        return False

def main():
    """Main initialization workflow"""
    print("=" * 60)
    print("🗄️  DATABASE INITIALIZATION")
    print("=" * 60)
    
    # Step 1: Check database connection
    if not check_database_connection():
        print("\n❌ Cannot proceed without database connection")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running: sudo systemctl status postgresql")
        print("2. Check your .env file for correct credentials")
        print("3. Verify database exists: psql -U postgres -c '\\l'")
        return False
    
    # Step 2: Check if table exists
    print("\n" + "=" * 60)
    logger.info("Checking if brand_profiles table exists...")
    
    if check_table_exists('brand_profiles'):
        logger.info("✅ brand_profiles table already exists")
        
        # Ask if user wants to recreate
        response = input("\n⚠️  Table exists. Recreate? (this will DELETE all data) [y/N]: ")
        if response.lower() != 'y':
            logger.info("Skipping schema initialization")
            print("\n" + "=" * 60)
            verify_setup()
            return True
    else:
        logger.info("❌ brand_profiles table does NOT exist")
    
    # Step 3: Initialize schema
    print("\n" + "=" * 60)
    if not initialize_schema():
        print("\n❌ Schema initialization failed")
        return False
    
    # Step 4: Verify setup
    print("\n" + "=" * 60)
    logger.info("Verifying database setup...")
    if not verify_setup():
        print("\n❌ Verification failed")
        return False
    
    print("\n" + "=" * 60)
    print("✅ DATABASE INITIALIZATION COMPLETE")
    print("=" * 60)
    print("\nYou can now run your application without transaction errors.")
    print("The brand_profiles table is ready to use!")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
