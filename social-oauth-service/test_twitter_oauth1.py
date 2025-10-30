"""
Test Twitter Media Upload with OAuth 1.0a
Uses Access Token + Secret with Read and Write permissions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from requests_oauthlib import OAuth1Session
from app.config import settings
import time

# Your OAuth 1.0a credentials
ACCESS_TOKEN = "1970418056510803968-CWbVYDumI8JyALLKclk4kK0GVLl1TK"
ACCESS_TOKEN_SECRET = "gSluZjhPGyUFTXdSzazMjbEHq2vU6dAkPQTmqQC3KxlgY"

# Simple 1x1 red pixel JPEG
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

print("=" * 70)
print("🧪 TWITTER MEDIA UPLOAD TEST (OAuth 1.0a)")
print("=" * 70)

# Create OAuth1 session
print("\n1️⃣ Setting up OAuth 1.0a authentication...")
print(f"   API Key: {settings.TWITTER_API_KEY[:10]}...")
print(f"   Access Token: {ACCESS_TOKEN[:20]}...")

oauth = OAuth1Session(
    settings.TWITTER_API_KEY,
    client_secret=settings.TWITTER_API_SECRET,
    resource_owner_key=ACCESS_TOKEN,
    resource_owner_secret=ACCESS_TOKEN_SECRET
)
print("✓ OAuth session created")

# Test media upload with v1.1 endpoint
print("\n2️⃣ Testing media upload...")
print(f"   Endpoint: https://upload.twitter.com/1.1/media/upload.json")
print(f"   Image size: {len(TEST_IMAGE)} bytes")

try:
    # INIT
    print("\n   Step 1: INIT")
    init_response = oauth.post(
        "https://upload.twitter.com/1.1/media/upload.json",
        data={
            "command": "INIT",
            "total_bytes": len(TEST_IMAGE),
            "media_type": "image/jpeg"
        }
    )
    init_response.raise_for_status()
    media_id = init_response.json()["media_id_string"]
    print(f"   ✓ INIT successful - media_id: {media_id}")
    
    # APPEND
    print("\n   Step 2: APPEND")
    append_response = oauth.post(
        "https://upload.twitter.com/1.1/media/upload.json",
        data={
            "command": "APPEND",
            "media_id": media_id,
            "segment_index": 0
        },
        files={"media": TEST_IMAGE}
    )
    append_response.raise_for_status()
    print("   ✓ APPEND successful")
    
    # FINALIZE
    print("\n   Step 3: FINALIZE")
    finalize_response = oauth.post(
        "https://upload.twitter.com/1.1/media/upload.json",
        data={
            "command": "FINALIZE",
            "media_id": media_id
        }
    )
    finalize_response.raise_for_status()
    print("   ✓ FINALIZE successful")
    
    print(f"\n✅ MEDIA UPLOAD SUCCESSFUL!")
    print(f"   Media ID: {media_id}")
    
    # Wait a moment for Twitter to process the media
    print("\n⏳ Waiting 2 seconds for media processing...")
    time.sleep(2)
    
    # Now post a tweet with the image using v1.1 endpoint (compatible with OAuth 1.0a)
    print("\n3️⃣ Posting tweet with image...")
    from datetime import datetime
    tweet_text = f"Test tweet with image - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    tweet_response = oauth.post(
        "https://api.twitter.com/1.1/statuses/update.json",
        data={
            "status": tweet_text,
            "media_ids": media_id
        }
    )
    tweet_response.raise_for_status()
    tweet_data = tweet_response.json()
    tweet_id = tweet_data["id_str"]
    
    print(f"✅ TWEET POSTED SUCCESSFULLY!")
    print(f"   Tweet ID: {tweet_id}")
    print(f"   URL: https://twitter.com/i/web/status/{tweet_id}")
    
    print("\n" + "=" * 70)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 70)
    print("\n✅ The v1.1 endpoint fix is working perfectly!")
    print("✅ Media upload successful")
    print("✅ Tweet with image posted")
    print(f"\n🔗 View your tweet: https://twitter.com/i/web/status/{tweet_id}")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Status: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
