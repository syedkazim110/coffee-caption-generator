#!/usr/bin/env python3
"""
Diagnostic script to identify OAuth 1.0a authentication issue
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import db
from app.utils.encryption import token_encryption
from app.oauth.token_manager import token_manager
from app.config import settings
from requests_oauthlib import OAuth1Session

print("=" * 70)
print("OAUTH 1.0A DIAGNOSTIC TOOL")
print("=" * 70)

# Step 1: Check database for brand_id=1
print("\n📊 STEP 1: Checking database for brand_id=1 Twitter connection")
print("-" * 70)

result = db.execute_query("""
    SELECT id, brand_id, platform, 
           oauth1_enabled,
           CASE WHEN oauth1_access_token IS NOT NULL THEN 'YES' ELSE 'NO' END as has_oauth1_token,
           CASE WHEN oauth1_access_token_secret IS NOT NULL THEN 'YES' ELSE 'NO' END as has_oauth1_secret
    FROM social_connections
    WHERE brand_id = 1 AND platform = 'twitter'
""")

if not result or len(result) == 0:
    print("❌ No Twitter connection found for brand_id=1")
    print("   Please authenticate Twitter first")
    sys.exit(1)

row = dict(result[0])
print(f"✅ Connection found:")
print(f"   - ID: {row['id']}")
print(f"   - Brand ID: {row['brand_id']}")
print(f"   - Platform: {row['platform']}")
print(f"   - OAuth1 Enabled: {row['oauth1_enabled']}")
print(f"   - Has OAuth1 Token: {row['has_oauth1_token']}")
print(f"   - Has OAuth1 Secret: {row['has_oauth1_secret']}")

if not row['oauth1_enabled']:
    print("\n❌ OAuth 1.0a is not enabled for this connection")
    print("   Run add_oauth1_tokens.py first")
    sys.exit(1)

# Step 2: Get connection via token_manager (with decryption)
print("\n🔐 STEP 2: Retrieving and decrypting OAuth 1.0a tokens")
print("-" * 70)

connection = token_manager.get_connection(brand_id=1, platform='twitter', decrypt=True)

if not connection:
    print("❌ Failed to retrieve connection")
    sys.exit(1)

oauth1_token = connection.get('oauth1_access_token')
oauth1_secret = connection.get('oauth1_access_token_secret')

print(f"✅ Tokens retrieved:")
print(f"   - OAuth1 Token: {oauth1_token[:30] if oauth1_token else 'NONE'}...")
print(f"   - OAuth1 Secret: {oauth1_secret[:30] if oauth1_secret else 'NONE'}...")
print(f"   - OAuth1 Enabled: {connection.get('oauth1_enabled')}")

if not oauth1_token or not oauth1_secret:
    print("\n❌ OAuth 1.0a tokens are missing or not decrypted properly")
    sys.exit(1)

# Step 3: Check app credentials
print("\n🔑 STEP 3: Checking app credentials")
print("-" * 70)

print(f"✅ App credentials loaded:")
print(f"   - API Key: {settings.TWITTER_API_KEY[:20] if settings.TWITTER_API_KEY else 'MISSING'}...")
print(f"   - API Secret: {settings.TWITTER_API_SECRET[:20] if settings.TWITTER_API_SECRET else 'MISSING'}...")

if not settings.TWITTER_API_KEY or not settings.TWITTER_API_SECRET:
    print("\n❌ Twitter app credentials missing in .env")
    sys.exit(1)

# Step 4: Test OAuth 1.0a signature generation
print("\n🔬 STEP 4: Testing OAuth 1.0a authentication")
print("-" * 70)

try:
    # Test image
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
    
    # Create OAuth session with retrieved tokens
    oauth = OAuth1Session(
        settings.TWITTER_API_KEY,
        client_secret=settings.TWITTER_API_SECRET,
        resource_owner_key=oauth1_token,
        resource_owner_secret=oauth1_secret
    )
    
    upload_url = "https://upload.twitter.com/1.1/media/upload.json"
    
    print("📤 Testing INIT command...")
    init_response = oauth.post(
        upload_url,
        data={
            "command": "INIT",
            "total_bytes": len(TEST_IMAGE),
            "media_type": "image/jpeg"
        }
    )
    
    if init_response.status_code in [200, 202]:
        media_id = init_response.json()["media_id_string"]
        print(f"✅ INIT successful - media_id: {media_id}")
        print("\n" + "=" * 70)
        print("🎉 SUCCESS! OAuth 1.0a authentication is working correctly")
        print("=" * 70)
        print("\n✅ The tokens in the database are valid and decrypted properly")
        print("✅ OAuth 1.0a signature generation is working")
        print("✅ Twitter media upload endpoint accepting requests")
        print("\n🔧 Next step: Restart the oauth-service to load the updated code")
        print("   Run: docker-compose restart oauth-service")
    else:
        print(f"❌ INIT failed with status: {init_response.status_code}")
        print(f"   Response: {init_response.text}")
        
        if init_response.status_code == 401 and "Bad Authentication" in init_response.text:
            print("\n🔍 DIAGNOSIS: Bad Authentication Error")
            print("   This means the OAuth 1.0a credentials don't match.")
            print("\n   Possible causes:")
            print("   1. The tokens belong to a different Twitter app")
            print("   2. The tokens are expired")
            print("   3. The API Key/Secret don't match the tokens")
            print("\n   Let's verify the token ownership...")
            
            # Print first/last chars for comparison
            print(f"\n   Token (first 30 chars): {oauth1_token[:30]}")
            print(f"   Secret (first 30 chars): {oauth1_secret[:30]}")
            print(f"   Expected token: 1970418056510803968-CWbVYDumI8JyALLKclk4kK0GVLl1TK")
            print(f"   Expected secret: gSluZjhPGyUFTXdSzazMjbEHq2vU6dAkPQTmqQC3KxlgY")

except Exception as e:
    print(f"❌ Error during test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
