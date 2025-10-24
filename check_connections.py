#!/usr/bin/env python3
"""
Script to check current OAuth connections in database
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'social-oauth-service'))

from app.database import db
import json

print("Checking OAuth connections in database...\n")

try:
    results = db.execute_query(
        """
        SELECT id, brand_id, platform, platform_user_id, platform_username, 
               expires_at, is_active, connection_error, account_metadata
        FROM social_connections 
        WHERE is_active = true 
        ORDER BY created_at DESC 
        LIMIT 10
        """
    )
    
    if not results:
        print("No active connections found.")
    else:
        for i, row in enumerate(results, 1):
            conn = dict(row)
            print(f"Connection #{i}:")
            print(f"  ID: {conn['id']}")
            print(f"  Brand ID: {conn['brand_id']}")
            print(f"  Platform: {conn['platform']}")
            print(f"  Platform User ID: {conn.get('platform_user_id')}")
            print(f"  Platform Username: {conn.get('platform_username')}")
            print(f"  Expires At: {conn.get('expires_at')}")
            print(f"  Is Active: {conn.get('is_active')}")
            print(f"  Connection Error: {conn.get('connection_error')}")
            
            # Parse and display account_metadata
            metadata = conn.get('account_metadata')
            if metadata:
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        pass
                
                print(f"  Account Metadata:")
                if isinstance(metadata, dict):
                    # For Instagram
                    if conn['platform'] == 'instagram':
                        print(f"    - User ID: {metadata.get('user_id')}")
                        print(f"    - Username: {metadata.get('username')}")
                        print(f"    - Page ID: {metadata.get('page_id')}")
                        print(f"    - Page Name: {metadata.get('page_name')}")
                        all_accounts = metadata.get('all_accounts', [])
                        print(f"    - All Accounts: {len(all_accounts)} accounts")
                        if all_accounts:
                            for j, acc in enumerate(all_accounts, 1):
                                print(f"      Account {j}:")
                                print(f"        - IG Account ID: {acc.get('ig_account_id')}")
                                print(f"        - Username: {acc.get('username')}")
                                print(f"        - Page ID: {acc.get('page_id')}")
                                print(f"        - Has page_token: {bool(acc.get('page_token'))}")
                    
                    # For Facebook
                    elif conn['platform'] == 'facebook':
                        print(f"    - User ID: {metadata.get('user_id')}")
                        print(f"    - Username: {metadata.get('username')}")
                        print(f"    - Email: {metadata.get('email')}")
                        pages = metadata.get('pages', [])
                        print(f"    - Pages: {len(pages)} pages")
                        if pages:
                            for j, page in enumerate(pages, 1):
                                print(f"      Page {j}:")
                                print(f"        - Page ID: {page.get('id')}")
                                print(f"        - Name: {page.get('name')}")
                                print(f"        - Category: {page.get('category')}")
                                print(f"        - Has access_token: {bool(page.get('access_token'))}")
                else:
                    print(f"    {metadata}")
            else:
                print(f"  Account Metadata: None")
            
            print()
    
except Exception as e:
    print(f"Error querying database: {e}")
    import traceback
    traceback.print_exc()
