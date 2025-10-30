#!/usr/bin/env python3
"""
Script to add OAuth 1.0a tokens to existing Twitter connection
and test media upload
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import db
from app.utils.encryption import token_encryption
from app.config import settings

# Your OAuth 1.0a credentials from the test
OAUTH1_ACCESS_TOKEN = "1970418056510803968-CWbVYDumI8JyALLKclk4kK0GVLl1TK"
OAUTH1_ACCESS_TOKEN_SECRET = "gSluZjhPGyUFTXdSzazMjbEHq2vU6dAkPQTmqQC3KxlgY"

def run_migration():
    """Run the database migration to add OAuth 1.0a columns"""
    print("=" * 70)
    print("STEP 1: Running database migration")
    print("=" * 70)
    
    try:
        # Add OAuth 1.0a columns
        db.execute_update("""
            ALTER TABLE social_connections
            ADD COLUMN IF NOT EXISTS oauth1_access_token TEXT,
            ADD COLUMN IF NOT EXISTS oauth1_access_token_secret TEXT,
            ADD COLUMN IF NOT EXISTS oauth1_enabled BOOLEAN DEFAULT false
        """)
        
        print("✅ Migration successful - OAuth 1.0a columns added")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def add_oauth1_to_twitter_connection(brand_id: int = 1):
    """Add OAuth 1.0a credentials to existing Twitter connection"""
    print("\n" + "=" * 70)
    print(f"STEP 2: Adding OAuth 1.0a credentials to Twitter connection (brand_id={brand_id})")
    print("=" * 70)
    
    try:
        # Check if connection exists
        result = db.execute_query(
            "SELECT id FROM social_connections WHERE brand_id = %s AND platform = 'twitter'",
            (brand_id,)
        )
        
        if not result or len(result) == 0:
            print(f"❌ No Twitter connection found for brand_id {brand_id}")
            print("   Please authenticate Twitter first via the OAuth flow")
            return False
        
        # Encrypt OAuth 1.0a credentials
        encrypted_token = token_encryption.encrypt_token(OAUTH1_ACCESS_TOKEN)
        encrypted_secret = token_encryption.encrypt_token(OAUTH1_ACCESS_TOKEN_SECRET)
        
        # Update connection with OAuth 1.0a credentials
        db.execute_update("""
            UPDATE social_connections
            SET oauth1_access_token = %s,
                oauth1_access_token_secret = %s,
                oauth1_enabled = true,
                updated_at = CURRENT_TIMESTAMP
            WHERE brand_id = %s AND platform = 'twitter'
        """, (encrypted_token, encrypted_secret, brand_id))
        
        print(f"✅ OAuth 1.0a credentials added to Twitter connection")
        print(f"   - Token: {OAUTH1_ACCESS_TOKEN[:20]}...")
        print(f"   - Secret: {OAUTH1_ACCESS_TOKEN_SECRET[:20]}...")
        return True
        
    except Exception as e:
        print(f"❌ Failed to add OAuth 1.0a credentials: {e}")
        return False

def test_media_upload():
    """Test media upload with OAuth 1.0a"""
    print("\n" + "=" * 70)
    print("STEP 3: Testing media upload with OAuth 1.0a")
    print("=" * 70)
    
    try:
        from requests_oauthlib import OAuth1Session
        
        # Test image (1x1 red pixel JPEG)
        TEST_IMAGE = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x03, 0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
            0x37, 0xFF, 0xD9
        ])
        
        # Create OAuth 1.0a session
        oauth = OAuth1Session(
            settings.TWITTER_API_KEY,
            client_secret=settings.TWITTER_API_SECRET,
            resource_owner_key=OAUTH1_ACCESS_TOKEN,
            resource_owner_secret=OAUTH1_ACCESS_TOKEN_SECRET
        )
        
        upload_url = "https://upload.twitter.com/1.1/media/upload.json"
        
        print("\n📤 Testing INIT command...")
        init_response = oauth.post(
            upload_url,
            data={
                "command": "INIT",
                "total_bytes": len(TEST_IMAGE),
                "media_type": "image/jpeg"
            }
        )
        init_response.raise_for_status()
        media_id = init_response.json()["media_id_string"]
        print(f"✅ INIT successful - media_id: {media_id}")
        
        print("\n📤 Testing APPEND command...")
        append_response = oauth.post(
            upload_url,
            data={
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": 0
            },
            files={"media": TEST_IMAGE}
        )
        append_response.raise_for_status()
        print("✅ APPEND successful")
        
        print("\n📤 Testing FINALIZE command...")
        finalize_response = oauth.post(
            upload_url,
            data={
                "command": "FINALIZE",
                "media_id": media_id
            }
        )
        finalize_response.raise_for_status()
        print("✅ FINALIZE successful")
        
        print("\n" + "=" * 70)
        print("🎉 SUCCESS! Media upload working with OAuth 1.0a")
        print("=" * 70)
        print(f"✅ Media ID: {media_id}")
        print("✅ The 403 error is now fixed!")
        print("\nYour Twitter media uploads will now work correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Media upload test failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
        return False

if __name__ == "__main__":
    print("\n🔧 Twitter OAuth 1.0a Fix - Setup and Test")
    print("=" * 70)
    
    # Step 1: Run migration
    if not run_migration():
        print("\n❌ Setup failed at migration step")
        sys.exit(1)
    
    # Step 2: Add OAuth 1.0a credentials
    if not add_oauth1_to_twitter_connection():
        print("\n❌ Setup failed at credential addition step")
        sys.exit(1)
    
    # Step 3: Test media upload
    if not test_media_upload():
        print("\n❌ Media upload test failed")
        sys.exit(1)
    
    print("\n✅ All steps completed successfully!")
    print("\nNext steps:")
    print("1. Restart your oauth-service: docker-compose restart oauth-service")
    print("2. Try posting a tweet with an image")
    print("3. The 403 error should be resolved!")
