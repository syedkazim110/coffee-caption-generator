"""
Test script matching the Node.js example for Twitter media upload and posting
This demonstrates the complete flow: download image → upload media → post tweet
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.publishers.twitter_publisher import twitter_publisher
from app.oauth.twitter_oauth import twitter_oauth
from app.utils.download_helper import download
from app.config import settings
import asyncio
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def tweet_with_media(brand_id: int = 1):
    """
    Post a tweet with media - Python version of the Node.js example
    
    This function replicates the Node.js code:
    ```javascript
    const download = require("./utilities");
    
    const tweet = async () => {
        const uri = "https://i.imgur.com/Zl2GLjnh.jpg";
        const filename = "image.png";
        
        download(uri, filename, async function(){
            try {
                const mediaId = await twitterClient.v1.uploadMedia("./image.png");
                await twitterClient.v2.tweet({
                    text: "Hello world! This is an image in Ukraine!",
                    media: { media_ids: [mediaId] }
                });
            } catch (e) {
                console.log(e)
            }
        });
    }
    ```
    """
    print("=" * 70)
    print("Twitter Media Tweet Test - Matching Node.js Example")
    print("=" * 70)
    
    # Image URL and filename - using a reliable public image
    uri = "https://picsum.photos/800/600"  # Random image from Lorem Picsum
    filename = "image.png"
    
    print(f"\n1. Testing with brand_id: {brand_id}")
    
    # Check if authenticated
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
    
    # Download image using the download helper (matching Node.js pattern)
    print(f"\n3. Downloading image from {uri}...")
    
    async def post_tweet():
        """Callback function that posts the tweet after download"""
        try:
            print("\n4. Uploading media to Twitter...")
            
            # Read the downloaded image
            with open(filename, 'rb') as f:
                image_data = f.read()
            
            # Get access token
            access_token = connection['access_token']
            
            # Upload media and get media_id
            media_id = twitter_publisher._upload_media(
                access_token=access_token,
                image_data=image_data
            )
            print(f"✓ Media uploaded successfully!")
            print(f"  Media ID: {media_id}")
            
            print("\n5. Posting tweet with media...")
            
            # Post tweet with media (matching Node.js example text)
            result = twitter_publisher.publish_post(
                access_token=access_token,
                caption="Hello world! This is an image in Ukraine!",
                image_data=image_data
            )
            
            print(f"✓ Tweet posted successfully!")
            print(f"  Tweet ID: {result['post_id']}")
            print(f"  URL: {result['url']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error posting tweet: {str(e)}")
            import traceback
            print("\nFull error:")
            print(traceback.format_exc())
            return False
    
    try:
        # Download image with callback (matching Node.js pattern)
        from app.utils.download_helper import download_async
        await download_async(uri, filename, post_tweet)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in tweet flow: {str(e)}")
        import traceback
        print("\nFull error:")
        print(traceback.format_exc())
        return False


async def test_simple_tweet_with_media(brand_id: int = 1):
    """
    Simplified version - directly post tweet with media from URL
    This uses the publisher's built-in download capability
    """
    print("\n" + "=" * 70)
    print("Simplified Tweet with Media Test")
    print("=" * 70)
    
    print(f"\n1. Testing with brand_id: {brand_id}")
    
    # Check authentication
    print("\n2. Checking Twitter authentication...")
    connection = twitter_oauth.get_connection(brand_id)
    
    if not connection:
        print("❌ Not authenticated with Twitter!")
        return False
    
    print(f"✓ Authenticated as: {connection.get('account_metadata', {}).get('username', 'Unknown')}")
    
    try:
        print("\n3. Posting tweet with media from URL...")
        
        # Get access token
        access_token = connection['access_token']
        
        # Post tweet with media URL - the publisher handles download automatically
        result = twitter_publisher.publish_post(
            access_token=access_token,
            caption="Hello world! This is a test image! 📸",
            image_url="https://picsum.photos/800/600"
        )
        
        print(f"✓ Tweet posted successfully!")
        print(f"  Tweet ID: {result['post_id']}")
        print(f"  URL: {result['url']}")
        print(f"  Caption: {result['caption']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error posting tweet: {str(e)}")
        import traceback
        print("\nFull error:")
        print(traceback.format_exc())
        return False


def print_usage_examples():
    """Print usage examples matching the Node.js patterns"""
    print("\n" + "=" * 70)
    print("USAGE EXAMPLES")
    print("=" * 70)
    
    print("\n1. Node.js Style (with download callback):")
    print("-" * 70)
    print("""
from app.utils.download_helper import download_async
from app.publishers.twitter_publisher import twitter_publisher
from app.oauth.twitter_oauth import twitter_oauth

async def tweet():
    uri = "https://picsum.photos/800/600"
    filename = "image.png"
    
    # Get connection
    connection = twitter_oauth.get_connection(brand_id=1)
    access_token = connection['access_token']
    
    # Define callback
    async def post_after_download():
        with open(filename, 'rb') as f:
            image_data = f.read()
        
        result = twitter_publisher.publish_post(
            access_token=access_token,
            caption="Hello world! This is an image!",
            image_data=image_data
        )
        print(f"Posted: {result['url']}")
    
    # Download and post
    await download_async(uri, filename, post_after_download)

# Run it
asyncio.run(tweet())
    """)
    
    print("\n2. Simplified Style (recommended):")
    print("-" * 70)
    print("""
from app.publishers.twitter_publisher import twitter_publisher
from app.oauth.twitter_oauth import twitter_oauth

# Get connection
connection = twitter_oauth.get_connection(brand_id=1)
access_token = connection['access_token']

# Post directly with image URL
result = twitter_publisher.publish_post(
    access_token=access_token,
    caption="Hello world! This is an image!",
    image_url="https://picsum.photos/800/600"
)

print(f"Posted: {result['url']}")
    """)
    
    print("\n3. Using the API endpoint:")
    print("-" * 70)
    print("""
import requests

# Post to the API
response = requests.post(
    "http://localhost:8000/api/publish",
    json={
        "brand_id": 1,
        "caption": "Hello world! This is an image!",
        "image_url": "https://picsum.photos/800/600",
        "platforms": ["twitter"],
        "hashtags": ["Test", "HelloWorld"]
    }
)

result = response.json()
print(f"Posted: {result['results']['twitter']['url']}")
    """)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Twitter media upload and posting")
    parser.add_argument(
        "--brand-id",
        type=int,
        default=1,
        help="Brand ID to use for testing (default: 1)"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simplified version (directly post with URL)"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show usage examples"
    )
    
    args = parser.parse_args()
    
    if args.examples:
        print_usage_examples()
        sys.exit(0)
    
    print("\nTesting Twitter Media Upload & Posting (Python Version)...")
    
    try:
        if args.simple:
            success = asyncio.run(test_simple_tweet_with_media(args.brand_id))
        else:
            success = asyncio.run(tweet_with_media(args.brand_id))
        
        print("\n" + "=" * 70)
        if success:
            print("✅ TEST PASSED - Media tweet posted successfully!")
        else:
            print("❌ TEST FAILED - Could not post media tweet")
        print("=" * 70)
        
        # Show usage examples
        print_usage_examples()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
