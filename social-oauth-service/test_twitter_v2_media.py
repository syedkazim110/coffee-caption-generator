"""
Test Twitter API v2 Media Upload
Based on the recommended implementation using the new v2 endpoints
"""
import math
import time
import requests
from io import BytesIO
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.oauth.twitter_oauth import twitter_oauth

# === CONFIG ===
IMAGE_PATH = None  # or set to a local path
IMAGE_URL = "https://picsum.photos/800/600"  # Use this if IMAGE_PATH is None

UPLOAD_BASE = "https://api.x.com/2/media/upload"  # New v2 endpoint
CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB
STATUS_CHECK_INTERVAL = 5
MAX_STATUS_CHECKS = 10


def log(step, msg):
    print(f"[{step}] {msg}")


def get_image_data():
    if IMAGE_URL:
        log("INIT", f"Downloading image from {IMAGE_URL}")
        r = requests.get(IMAGE_URL, timeout=30)
        r.raise_for_status()
        return r.content
    elif IMAGE_PATH:
        log("INIT", f"Reading local file {IMAGE_PATH}")
        with open(IMAGE_PATH, "rb") as f:
            return f.read()
    else:
        raise ValueError("No IMAGE_PATH or IMAGE_URL provided")


def upload_media_v2(token, image_data, media_type="image/jpeg"):
    headers = {"Authorization": f"Bearer {token}"}
    total_bytes = len(image_data)

    # === STEP 1: INIT ===
    init_payload = {
        "command": "INIT",
        "total_bytes": str(total_bytes),
        "media_type": media_type,
    }
    log("INIT", f"Requesting INIT ({total_bytes} bytes)")
    r = requests.post(UPLOAD_BASE, headers=headers, data=init_payload)
    print("INIT response:", r.status_code, r.text)
    r.raise_for_status()
    
    # Parse response - could be in 'data' or at root level
    response_json = r.json()
    if 'data' in response_json:
        media_id = response_json["data"]["id"]
    else:
        media_id = response_json.get("media_id_string") or response_json.get("media_id")
    
    log("INIT", f"Got media_id: {media_id}")

    # === STEP 2: APPEND ===
    num_chunks = math.ceil(total_bytes / CHUNK_SIZE)
    for i in range(num_chunks):
        start = i * CHUNK_SIZE
        end = min(start + CHUNK_SIZE, total_bytes)
        chunk = image_data[start:end]
        log("APPEND", f"Uploading chunk {i+1}/{num_chunks} ({len(chunk)} bytes)")
        append_url = f"{UPLOAD_BASE}/{media_id}/append"
        files = {"media": ("chunk", BytesIO(chunk), "application/octet-stream")}
        data = {"segment_index": str(i)}
        r = requests.post(append_url, headers=headers, data=data, files=files)
        print("APPEND response:", r.status_code, r.text if r.text else "(no body)")
        r.raise_for_status()

    # === STEP 3: FINALIZE ===
    finalize_data = {"command": "FINALIZE", "media_id": media_id}
    log("FINALIZE", "Finalizing upload")
    r = requests.post(UPLOAD_BASE, headers=headers, data=finalize_data)
    print("FINALIZE response:", r.status_code, r.text)
    r.raise_for_status()
    finalize_result = r.json()

    # === STEP 4: STATUS ===
    # Check both 'data' and root level for processing_info
    processing_info = finalize_result.get("data", {}).get("processing_info") or finalize_result.get("processing_info")
    
    if processing_info:
        state = processing_info.get("state")
        count = 0
        while state in ("pending", "in_progress") and count < MAX_STATUS_CHECKS:
            delay = processing_info.get("check_after_secs", STATUS_CHECK_INTERVAL)
            log("STATUS", f"Waiting {delay}s before recheck...")
            time.sleep(delay)
            params = {"command": "STATUS", "media_id": media_id}
            r = requests.get(UPLOAD_BASE, headers=headers, params=params)
            print("STATUS response:", r.status_code, r.text)
            r.raise_for_status()
            status_json = r.json()
            processing_info = status_json.get("data", {}).get("processing_info", {}) or status_json.get("processing_info", {})
            state = processing_info.get("state")
            count += 1
        log("STATUS", f"Processing state: {state}")
    else:
        log("STATUS", "No processing required")

    log("DONE", f"Upload completed successfully. Media ID: {media_id}")
    return media_id


def test_with_auth(brand_id=1):
    """
    Test media upload using OAuth connection from database
    """
    print("=" * 70)
    print("Twitter API v2 Media Upload Test")
    print("=" * 70)
    
    # Get authentication
    print(f"\n1. Getting authentication for brand_id={brand_id}...")
    connection = twitter_oauth.get_connection(brand_id)
    
    if not connection:
        print("❌ Not authenticated with Twitter!")
        print("\nPlease authenticate first:")
        print("1. Start: cd social-oauth-service && python -m app.main")
        print("2. Visit: http://localhost:8000/oauth/twitter/authorize?brand_id=1")
        print("3. Complete authorization")
        print("4. Run this test again")
        return False
    
    print(f"✓ Authenticated as: {connection.get('account_metadata', {}).get('username', 'Unknown')}")
    
    access_token = connection.get('access_token')
    if not access_token:
        print("❌ No access token found!")
        print("Token may not have been decrypted properly. Try re-authenticating.")
        return False
    
    print(f"✓ Access token: {access_token[:20]}..." if len(access_token) > 20 else "✓ Access token obtained")
    
    # Run the upload test
    print("\n2. Starting media upload test...")
    try:
        data = get_image_data()
        media_id = upload_media_v2(access_token, data)
        print("\n" + "=" * 70)
        print("✅ SUCCESS! Media uploaded successfully")
        print(f"Media ID: {media_id}")
        print("=" * 70)
        print("\nYou can now use this media_id to post a tweet:")
        print(f"  POST https://api.twitter.com/2/tweets")
        print(f"  {{\"text\": \"Test tweet\", \"media\": {{\"media_ids\": [\"{media_id}\"]}}}}")
        return True
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ FAILED!")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Twitter v2 media upload")
    parser.add_argument("--brand-id", type=int, default=1, help="Brand ID (default: 1)")
    parser.add_argument("--token", type=str, help="Access token (if not using OAuth)")
    parser.add_argument("--url", type=str, help="Image URL (overrides default)")
    parser.add_argument("--path", type=str, help="Local image path")
    
    args = parser.parse_args()
    
    # Override globals if provided
    if args.url:
        IMAGE_URL = args.url
    if args.path:
        IMAGE_PATH = args.path
        IMAGE_URL = None
    
    try:
        if args.token:
            # Use provided token directly
            print("Using provided access token...")
            data = get_image_data()
            upload_media_v2(args.token, data)
        else:
            # Use OAuth from database
            success = test_with_auth(args.brand_id)
            sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
