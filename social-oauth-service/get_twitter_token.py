"""
Helper script to authenticate with Twitter and get a proper access token
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.database import db
import webbrowser

print("=" * 70)
print("🔑 TWITTER OAUTH AUTHENTICATION")
print("=" * 70)

print("\n📋 What this script does:")
print("   1. Generates an authorization URL")
print("   2. Opens it in your browser")
print("   3. You authorize the app")
print("   4. The token gets saved to your database")
print("   5. Then you can test media uploads")

print("\n⚠️  IMPORTANT:")
print("   - Your OAuth service must be running")
print("   - Your ngrok URL must be active")
print("   - Your redirect URI must match your Twitter app settings")

print(f"\n📍 Current callback URL: {settings.BASE_CALLBACK_URL}")
print(f"   Redirect URI: {settings.TWITTER_REDIRECT_URI}")

print("\n" + "=" * 70)

# Check database connection
print("\n1️⃣ Checking database connection...")
if db.test_connection():
    print("✓ Database connected")
else:
    print("❌ Database connection failed")
    print("\n💡 Make sure PostgreSQL is running:")
    print("   docker-compose up -d")
    sys.exit(1)

# Generate auth URL
print("\n2️⃣ Generating authorization URL...")
brand_id = 1

from app.oauth.twitter_oauth import twitter_oauth
from app.oauth.token_manager import token_manager

try:
    # Generate state token with PKCE
    state_data = token_manager.generate_state_token('twitter', brand_id)
    state = state_data['state']
    
    # Get authorization URL
    auth_url = twitter_oauth.get_authorization_url(
        state=state,
        code_challenge=state_data['code_challenge']
    )
    
    print(f"✓ Authorization URL generated")
    print(f"\n🔗 Authorization URL:")
    print(f"   {auth_url}")
    
    print("\n3️⃣ Opening browser...")
    print("   Please authorize the application in your browser")
    
    try:
        webbrowser.open(auth_url)
        print("✓ Browser opened")
    except:
        print("⚠️  Could not open browser automatically")
        print("   Please copy and paste the URL above into your browser")
    
    print("\n" + "=" * 70)
    print("📝 NEXT STEPS:")
    print("=" * 70)
    print("\n1. Complete the authorization in your browser")
    print("2. You'll be redirected back (callback will save the token)")
    print("3. Check if token was saved:")
    print("   cd social-oauth-service")
    print("   python -c \"from app.database import db; print(db.execute_query('SELECT platform, created_at FROM oauth_tokens WHERE platform=\\'twitter\\' ORDER BY created_at DESC LIMIT 1'))\"")
    print("\n4. Then run the test again:")
    print("   python test_quick.py")
    print("\n" + "=" * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
