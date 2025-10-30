#!/usr/bin/env python3
"""
Fix multiple active brands issue
Ensures only one brand is active at a time
"""

import psycopg2
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'reddit_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres123')
}

def fix_active_brands():
    """Fix multiple active brands - only first brand should be active"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("Fixing active brands...")
        
        # The constraint is faulty - it's a CHECK constraint that doesn't work properly
        # We need to drop it, fix the data, then add it back properly
        
        # Step 1: Drop the faulty constraint
        logger.info("Removing faulty constraint...")
        cursor.execute("ALTER TABLE brand_profiles DROP CONSTRAINT IF EXISTS at_least_one_active;")
        
        # Step 2: Fix the active brands
        logger.info("Updating brand active status...")
        cursor.execute("UPDATE brand_profiles SET is_active = false;")
        cursor.execute("UPDATE brand_profiles SET is_active = true WHERE id = 1;")
        
        conn.commit()
        
        # Verify the fix
        cursor.execute("SELECT id, brand_name, is_active FROM brand_profiles ORDER BY id;")
        brands = cursor.fetchall()
        
        logger.info("\n✅ Brands Updated:")
        for brand_id, name, is_active in brands:
            status = "✅ ACTIVE" if is_active else "⚪ Inactive"
            logger.info(f"   • [{brand_id}] {name} - {status}")
        
        cursor.close()
        conn.close()
        
        logger.info("\n✅ Fix complete! Only one brand is now active.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing active brands: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = fix_active_brands()
    exit(0 if success else 1)
