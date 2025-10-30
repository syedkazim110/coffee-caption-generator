"""
Test Media Upload Only - Tests if we can upload media to Twitter
This isolates the media upload functionality from the tweet posting
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.publishers.twitter_publisher import twitter_publisher
from app.oauth.twitter_oauth import twitter_oauth
import requests
import asyncio


async def test_media_upload_only(brand_id: int = 1):
    """
    Test only the media upload functionality
    """
    print("=" * 70)
    print("Twitter Media Upload Test (Upload Only)")
    print("=" * 70)
    
    print(f"\n1. Testing with brand_id: {brand_id}")
    
    # Check authentication
    print("\n2. Checking Twitter authentication...")
    connection = twitter_oauth.get_connection(brand_id)
    
    if not connection:
        print("❌ Not authenticated with Twitter!")
        print("\nPlease authenticate first:")
        print("1. Start the OAuth service: cd social-oauth-service && python -m app.main")
        print("2. Visit: http://localhost:8000/oauth/twitter/authorize?brand_id=1")
        print("3. Complete the Twitter authorization")
        print("4. Run this script again")
        return False
    
    print(f"✓ Authenticated as: {connection.get('account_metadata', {}).get('username', 'Unknown')}")
    print(f"  Token type: {connection.get('token_type', 'unknown')}")
    print(f"  Has access_token: {bool(connection.get('access_token'))}")
    print(f"  Has refresh_token: {bool(connection.get('refresh_token'))}")
    
    # Download test image
    print("\n3. Downloading test image...")
    try:
        response = requests.get("https://picsum.photos/800/600", timeout=30)
        response.raise_for_status()
        image_data = response.content
        print(f"✓ Downloaded {len(image_data)} bytes")
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return False
    
    # Test media upload
    print("\n4. Testing media upload to Twitter...")
    try:
        access_token = connection['access_token']
        
        # Upload media
        media_id = twitter_publisher._upload_media(
            access_token=access_token,
            image_data=image_data
        )
        
        print(f"✓ Media uploaded successfully!")
        print(f"  Media ID: {media_id}")
        print(f"\n✅ MEDIA UPLOAD IS WORKING!")
        print(f"\nNow you can use this media_id to post a tweet.")
        print(f"The issue with posting is an authentication problem with Twitter API v2.")
        
        return True
        
    except Exception as e:
        print(f"❌ Media upload failed: {str(e)}")
        import traceback
        print("\nFull error:")
        print(traceback.format_exc())
        return False


def print_authentication_help():
    """Print help for authentication issues"""
    print("\n" + "=" * 70)
    print("AUTHENTICATION ISSUE DETECTED")
    print("=" * 70)
    
    print("""
The test shows you are authenticated, but Twitter is rejecting the token.

ISSUE:
The error "Authenticating with OAuth 2.0 Application-Only is forbidden"
means the access token is not properly configured for user context.

POSSIBLE SOLUTIONS:

1. Re-authenticate with proper scopes:
   - Visit: http://localhost:8000/oauth/twitter/authorize?brand_id=1
   - Complete the Twitter authorization again
   - This will get a fresh user context token

2. Check your Twitter App settings:
   - Go to: https://developer.twitter.com/en/portal/projects
   - Open your app settings
   - Ensure "OAuth 2.0" is enabled
   - Ensure you have the following scopes:
     * tweet.read
     * tweet.write
     * users.read
     * offline.access (for refresh tokens)

3. Token might be expired:
   - The refresh token should automatically refresh
   - But you may need to re-authenticate if refresh fails

4. Try using the API endpoint instead:
   - The API routes may handle authentication better
   - POST to http://localhost:8000/api/publish with:
     {
       "brand_id": 1,
       "caption": "Test tweet",
       "image_url": "https://picsum.photos/800/600",
       "platforms": ["twitter"]
     }
    """)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Twitter media upload only")
    parser.add_argument(
        "--brand-id",
        type=int,
        default=1,
        help="Brand ID to use for testing (default: 1)"
    )
    
    args = parser.parse_args()
    
    print("\nTesting Twitter Media Upload (Upload Only)...")
    
    try:
        success = asyncio.run(test_media_upload_only(args.brand_id))
        
        print("\n" + "=" * 70)
        if success:
            print("✅ MEDIA UPLOAD TEST PASSED!")
            print("\nThe media upload functionality is working correctly.")
            print("The issue is with the tweet posting authentication.")
        else:
            print("❌ MEDIA UPLOAD TEST FAILED")
        print("=" * 70)
        
        # Print authentication help
        print_authentication_help()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
