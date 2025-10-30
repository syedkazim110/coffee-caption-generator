#!/usr/bin/env python3
"""
Utility script to clear old Twitter OAuth tokens and prepare for re-authentication
"""
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import db

def main():
    print("=" * 60)
    print("Twitter OAuth Token Management Utility")
    print("=" * 60)
    print()
    
    try:
        # Step 1: Show current Twitter tokens
        print("Step 1: Checking for existing Twitter OAuth tokens...")
        print("-" * 60)
        
        tokens = db.execute_query("""
            SELECT 
                id, 
                brand_id, 
                platform, 
                platform_user_id,
                platform_username,
                created_at,
                expires_at,
                is_active
            FROM social_connections 
            WHERE platform = 'twitter'
            ORDER BY created_at DESC
        """)
        
        if not tokens:
            print("✓ No existing Twitter tokens found.")
            print()
            print("You can now authenticate with Twitter through your app.")
            print("The new token will include the 'media.write' scope.")
            return
        
        print(f"Found {len(tokens)} Twitter token(s):")
        print()
        
        for i, token in enumerate(tokens, 1):
            print(f"Token {i}:")
            print(f"  ID: {token['id']}")
            print(f"  Brand ID: {token['brand_id']}")
            print(f"  Platform User ID: {token['platform_user_id']}")
            print(f"  Platform Username: {token['platform_username']}")
            print(f"  Created: {token['created_at']}")
            print(f"  Expires: {token['expires_at']}")
            print(f"  Active: {token['is_active']}")
            
            # All old tokens need to be refreshed
            print(f"  ✗ Token needs to be refreshed with new 'media.write' scope")
            print()
        
        # Step 2: Offer to delete old tokens
        print("Step 2: Clear old Twitter tokens")
        print("-" * 60)
        print("To upload media with OAuth 2.0, you need a token with 'media.write' scope.")
        print("Old tokens without this scope must be deleted.")
        print()
        
        response = input("Delete all Twitter tokens? (yes/no): ").lower().strip()
        
        if response not in ['yes', 'y']:
            print("Operation cancelled. No tokens were deleted.")
            return
        
        # Delete all Twitter tokens
        deleted_count = db.execute_delete("DELETE FROM social_connections WHERE platform = 'twitter'")
        
        print(f"✓ Deleted {deleted_count} Twitter token(s)")
        print()
        
        # Step 3: Next steps
        print("Step 3: Next Steps")
        print("-" * 60)
        print("1. Go to your application")
        print("2. Click 'Connect Twitter' or 'Login with Twitter'")
        print("3. Authorize the app (you should see 'Upload media' permission)")
        print("4. Try uploading a tweet with an image")
        print()
        print("The new token will include these scopes:")
        print("  - tweet.read")
        print("  - tweet.write")
        print("  - tweet.moderate.write")
        print("  - users.read")
        print("  - offline.access")
        print("  - media.write  ← Required for media upload")
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
