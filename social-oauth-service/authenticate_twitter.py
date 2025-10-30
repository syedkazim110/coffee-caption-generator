"""
Simple Twitter Authentication Helper
Just visit the URL in your browser to authenticate
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

print("=" * 70)
print("🔑 TWITTER AUTHENTICATION")
print("=" * 70)

print("\n📍 Step 1: Visit this URL in your browser to authenticate:")
print(f"\n{settings.BASE_CALLBACK_URL}/api/v1/oauth/twitter/auth?brand_id=1")

print("\n📍 Step 2: After authorizing, your token will be saved automatically")

print("\n📍 Step 3: Then run the test:")
print("   cd social-oauth-service")
print("   python test_quick.py")

print("\n" + "=" * 70)
print("⚠️  IMPORTANT: Make sure your ngrok tunnel is running!")
print(f"   Current: {settings.BASE_CALLBACK_URL}")
print("=" * 70)
