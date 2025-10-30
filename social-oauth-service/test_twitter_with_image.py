"""
Complete Twitter Media Upload Test with OAuth 2.0
Tests the fixed v1.1 endpoint implementation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.publishers.twitter_publisher import twitter_publisher
from app.oauth.token_manager import token_manager
from app.database import get_db
from app.config import settings
from PIL import Image
import io

def create_test_image():
    """Create a proper test image (100x100 red square)"""
    print("\n📸 Creating test image...")
    
    # Create a 100x100 red image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Add some text to make it identifiable
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Draw a simple pattern
    for i in range(0, 100, 20):
        draw.line([(0, i), (100, i)], fill='white', width=2)
        draw.line([(i, 0), (i, 100)], fill='white', width=2)
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=95)
    img_bytes.seek(0)
    
    image_data = img_bytes.read()
    print(f"✓ Test image created ({len(image_data)} bytes, 100x100 JPEG)")
    
    return image_data

def get_twitter_token(brand_id: int = 1):
    """Get a valid Twitter access token from database"""
    print(f"\n🔑 Fetching Twitter access token for brand {brand_id}...")
    
    db = next(get_db())
    try:
        result = db.execute(
            """
            SELECT access_token, refresh_token, expires_at 
            FROM oauth_tokens 
            WHERE brand_id = :brand_id 
            AND platform = 'twitter' 
            AND is_active = true
            ORDER BY created_at DESC 
            LIMIT 1
            """,
            {"brand_id": brand_id}
        ).fetchone()
        
        if not result:
            print(f"❌ No Twitter token found for brand {brand_id}")
            print("\n💡 Please connect your Twitter account first:")
            print(f"   Visit: {settings.BASE_CALLBACK_URL}/api/v1/oauth/twitter/auth?brand_id={brand_id}")
            return None
        
        access_token = result[0]
        refresh_token = result[1]
        expires_at = result[2]
        
        print(f"✓ Found Twitter token")
        print(f"  Token preview: {access_token[:20]}...")
        print(f"  Expires at: {expires_at}")
        
        # Check if token needs refresh
        from datetime import datetime, timezone
        if expires_at and datetime.fromisoformat(expires_at.replace('Z', '+00:00')) < datetime.now(timezone.utc):
            print("⚠️  Token expired, attempting refresh...")
            try:
                new_token = token_manager.refresh_token('twitter', brand_id)
                if new_token:
                    access_token = new_token['access_token']
                    print("✓ Token refreshed successfully")
                else:
                    print("❌ Token refresh failed")
                    return None
            except Exception as e:
                print(f"❌ Token refresh error: {e}")
                return None
        
        return access_token
        
    finally:
        db.close()

def test_media_upload_only(access_token: str, image_data: bytes):
    """Test media upload without posting"""
    print("\n📤 Testing media upload (v1.1 endpoint)...")
    
    try:
        media_id = twitter_publisher._upload_media(
            access_token=access_token,
            image_data=image_data
        )
        
        print(f"✅ Media uploaded successfully!")
        print(f"   Media ID: {media_id}")
        return media_id
        
    except Exception as e:
        print(f"❌ Media upload failed: {str(e)}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
        return None

def test_complete_post(access_token: str, image_data: bytes):
    """Test complete tweet with image"""
    print("\n🐦 Testing complete tweet post with image...")
    
    from datetime import datetime
    caption = f"Test tweet with image - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    try:
        result = twitter_publisher.publish_post(
            access_token=access_token,
            caption=caption,
            image_data=image_data
        )
        
        print(f"✅ Tweet posted successfully!")
        print(f"   Tweet ID: {result['post_id']}")
        print(f"   URL: {result['url']}")
        return result
        
    except Exception as e:
        print(f"❌ Tweet post failed: {str(e)}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
        return None

def main():
    print("=" * 70)
    print("🧪 TWITTER MEDIA UPLOAD TEST (OAuth 2.0 + v1.1 endpoint)")
    print("=" * 70)
    
    # Step 1: Check configuration
    print("\n1️⃣ Checking configuration...")
    if not settings.TWITTER_CLIENT_ID:
        print("❌ TWITTER_CLIENT_ID not configured")
        return False
    if not settings.TWITTER_CLIENT_SECRET:
        print("❌ TWITTER_CLIENT_SECRET not configured")
        return False
    
    print(f"✓ TWITTER_CLIENT_ID: {settings.TWITTER_CLIENT_ID[:10]}...")
    print(f"✓ TWITTER_CLIENT_SECRET: {settings.TWITTER_CLIENT_SECRET[:10]}...")
    
    # Step 2: Get access token
    print("\n2️⃣ Getting access token...")
    access_token = get_twitter_token(brand_id=1)
    
    if not access_token:
        print("\n" + "=" * 70)
        print("❌ TEST FAILED - No valid access token available")
        print("=" * 70)
        return False
    
    # Step 3: Create test image
    print("\n3️⃣ Creating test image...")
    try:
        image_data = create_test_image()
    except Exception as e:
        print(f"❌ Failed to create test image: {e}")
        print("💡 Installing Pillow: pip install Pillow")
        return False
    
    # Step 4: Test media upload only
    print("\n4️⃣ Testing media upload...")
    media_id = test_media_upload_only(access_token, image_data)
    
    if not media_id:
        print("\n" + "=" * 70)
        print("❌ TEST FAILED - Media upload failed")
        print("=" * 70)
        return False
    
    # Step 5: Test complete post with image
    print("\n5️⃣ Testing complete tweet post...")
    result = test_complete_post(access_token, image_data)
    
    if not result:
        print("\n" + "=" * 70)
        print("⚠️  PARTIAL SUCCESS - Media upload works but tweet post failed")
        print("=" * 70)
        return False
    
    # Success!
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\n🎉 Your Twitter integration is fully working!")
    print(f"   - Media upload (v1.1 endpoint): ✓")
    print(f"   - Tweet posting (v2 API): ✓")
    print(f"\n🔗 View your test tweet: {result['url']}")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
