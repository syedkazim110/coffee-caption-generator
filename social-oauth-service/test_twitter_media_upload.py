"""
Test script to verify Twitter media upload functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.publishers.twitter_publisher import twitter_publisher
from app.config import settings
import requests
from io import BytesIO

def test_media_upload():
    """Test Twitter media upload with OAuth 1.0a"""
    
    print("=" * 60)
    print("Twitter Media Upload Test")
    print("=" * 60)
    
    # Check if credentials are configured
    print("\n1. Checking credentials...")
    if not settings.TWITTER_API_KEY:
        print("❌ TWITTER_API_KEY not configured")
        return False
    if not settings.TWITTER_API_SECRET:
        print("❌ TWITTER_API_SECRET not configured")
        return False
    
    print(f"✓ TWITTER_API_KEY: {settings.TWITTER_API_KEY[:10]}...")
    print(f"✓ TWITTER_API_SECRET: {settings.TWITTER_API_SECRET[:10]}...")
    
    # Create a test image (1x1 red pixel JPEG)
    print("\n2. Creating test image...")
    test_image_data = bytes([
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
    print(f"✓ Test image created ({len(test_image_data)} bytes)")
    
    # Test media upload
    print("\n3. Testing media upload...")
    try:
        # Note: We pass a dummy access_token since we're using app-level OAuth 1.0a credentials
        media_id = twitter_publisher._upload_media(
            access_token="dummy_token",  # Not used for OAuth 1.0a upload
            image_data=test_image_data
        )
        print(f"✓ Media uploaded successfully!")
        print(f"  Media ID: {media_id}")
        return True
        
    except Exception as e:
        print(f"❌ Media upload failed: {str(e)}")
        import traceback
        print("\nFull error:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("\nTesting Twitter Media Upload with OAuth 1.0a...")
    success = test_media_upload()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED - Media upload is working!")
        print("\nYour Twitter integration is now ready to upload images.")
    else:
        print("❌ TEST FAILED - Media upload is not working")
        print("\nPlease check:")
        print("1. TWITTER_API_KEY and TWITTER_API_SECRET are correctly set")
        print("2. Twitter app has 'Read and write' permissions")
        print("3. Twitter API credentials are valid")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
