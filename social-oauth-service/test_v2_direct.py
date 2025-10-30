"""
Direct test of Twitter v2 media upload without database
Provide token directly from your authenticated app
"""
import math
import time
import requests
from io import BytesIO
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# === CONFIG ===
IMAGE_URL = "https://picsum.photos/800/600"
UPLOAD_BASE = "https://api.x.com/2/media/upload"
CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB
STATUS_CHECK_INTERVAL = 5
MAX_STATUS_CHECKS = 10


def log(step, msg):
    print(f"[{step}] {msg}")


def get_image_data(url):
    log("DOWNLOAD", f"Downloading image from {url}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def upload_media_v2(token, image_data, media_type="image/jpeg"):
    """
    Upload media using Twitter v2 chunked upload
    INIT → APPEND → FINALIZE → STATUS
    """
    headers = {"Authorization": f"Bearer {token}"}
    total_bytes = len(image_data)

    # === STEP 1: INIT ===
    init_payload = {
        "command": "INIT",
        "total_bytes": str(total_bytes),
        "media_type": media_type,
    }
    log("INIT", f"Creating upload session ({total_bytes} bytes)")
    r = requests.post(UPLOAD_BASE, headers=headers, data=init_payload)
    print(f"  Response: {r.status_code}")
    print(f"  Body: {r.text}")
    r.raise_for_status()
    
    # Parse response
    response_json = r.json()
    if 'data' in response_json:
        media_id = response_json["data"]["id"]
    else:
        media_id = response_json.get("media_id_string") or response_json.get("media_id")
    
    log("INIT", f"✓ Got media_id: {media_id}")

    # === STEP 2: APPEND ===
    num_chunks = math.ceil(total_bytes / CHUNK_SIZE)
    log("APPEND", f"Uploading {num_chunks} chunk(s)")
    
    for i in range(num_chunks):
        start = i * CHUNK_SIZE
        end = min(start + CHUNK_SIZE, total_bytes)
        chunk = image_data[start:end]
        
        log("APPEND", f"  Chunk {i+1}/{num_chunks} ({len(chunk)} bytes)")
        append_url = f"{UPLOAD_BASE}/{media_id}/append"
        files = {"media": ("chunk", BytesIO(chunk), "application/octet-stream")}
        data = {"segment_index": str(i)}
        r = requests.post(append_url, headers=headers, data=data, files=files)
        print(f"    Response: {r.status_code}")
        r.raise_for_status()
    
    log("APPEND", "✓ All chunks uploaded")

    # === STEP 3: FINALIZE ===
    finalize_data = {"command": "FINALIZE", "media_id": media_id}
    log("FINALIZE", "Finalizing upload")
    r = requests.post(UPLOAD_BASE, headers=headers, data=finalize_data)
    print(f"  Response: {r.status_code}")
    print(f"  Body: {r.text}")
    r.raise_for_status()
    finalize_result = r.json()
    
    log("FINALIZE", "✓ Upload finalized")

    # === STEP 4: STATUS ===
    processing_info = finalize_result.get("data", {}).get("processing_info") or finalize_result.get("processing_info")
    
    if processing_info:
        state = processing_info.get("state")
        log("STATUS", f"Processing required (state: {state})")
        
        count = 0
        while state in ("pending", "in_progress") and count < MAX_STATUS_CHECKS:
            delay = processing_info.get("check_after_secs", STATUS_CHECK_INTERVAL)
            log("STATUS", f"  Waiting {delay}s...")
            time.sleep(delay)
            
            params = {"command": "STATUS", "media_id": media_id}
            r = requests.get(UPLOAD_BASE, headers=headers, params=params)
            r.raise_for_status()
            status_json = r.json()
            processing_info = status_json.get("data", {}).get("processing_info", {}) or status_json.get("processing_info", {})
            state = processing_info.get("state")
            count += 1
        
        log("STATUS", f"✓ Final state: {state}")
    else:
        log("STATUS", "✓ No processing required (ready immediately)")

    return media_id


def main():
    print("=" * 70)
    print("Twitter v2 Media Upload - Direct Test")
    print("=" * 70)
    
    # Get token
    print("\n📝 You need a USER ACCESS TOKEN (not bearer token)")
    print("   This token must have 'media.write' scope")
    print()
    
    token = input("Enter your access token (or press Enter to use env TWITTER_ACCESS_TOKEN): ").strip()
    
    if not token:
        token = os.getenv("TWITTER_ACCESS_TOKEN")
    
    if not token:
        print("\n❌ No token provided!")
        print("\nOptions:")
        print("1. Run with: TWITTER_ACCESS_TOKEN=your_token python test_v2_direct.py")
        print("2. Or paste token when prompted")
        print("\nTo get a user access token:")
        print("- Go through OAuth flow at: http://localhost:8001/oauth/twitter/authorize?brand_id=1")
        print("- Or use your app's existing user token")
        return
    
    print(f"\n✓ Using token: {token[:20]}...")
    
    # Get image
    print(f"\n📥 Downloading test image...")
    try:
        image_data = get_image_data(IMAGE_URL)
        print(f"✓ Downloaded {len(image_data)} bytes")
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return
    
    # Upload
    print(f"\n🚀 Starting v2 media upload...")
    print()
    try:
        media_id = upload_media_v2(token, image_data)
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print(f"\nMedia ID: {media_id}")
        print("\nYou can now post a tweet with this media:")
        print(f"""
curl -X POST https://api.twitter.com/2/tweets \\
  -H "Authorization: Bearer {token[:20]}..." \\
  -H "Content-Type: application/json" \\
  -d '{{"text": "Test tweet with image!", "media": {{"media_ids": ["{media_id}"]}}}}'
        """)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ FAILED!")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
        print("\n💡 Common issues:")
        print("1. Token doesn't have 'media.write' scope")
        print("2. Token is app-only (needs user context)")
        print("3. Token expired")
        print("\nSolution: Re-authenticate with proper scopes")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
