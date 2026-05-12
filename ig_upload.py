"""
Instagram Reels upload — official Graph API with resumable upload.
No public URL needed; video bytes are sent directly to Facebook's servers.

Env vars:
  IG_ACCESS_TOKEN  — long-lived user token (instagram_basic + instagram_content_publish)
  IG_USER_ID       — numeric Instagram Business/Creator account ID

Run auth_instagram.py once locally to generate these.
"""

import os
import time
import requests

_API = "https://graph.facebook.com/v21.0"


def _creds():
    token = os.getenv("IG_ACCESS_TOKEN", "").strip()
    uid = os.getenv("IG_USER_ID", "").strip()
    return (token, uid) if token and uid else (None, None)


def upload_reel(video_path: str, caption: str) -> str | None:
    """
    Upload a local .mp4 as an Instagram Reel.
    Returns the Reel URL, or None if credentials are not configured.
    """
    token, uid = _creds()
    if not token:
        print("  [IG] Skipping — IG_ACCESS_TOKEN / IG_USER_ID not set")
        return None

    file_size = os.path.getsize(video_path)

    # Step 1: Create upload session + container
    print("  [IG] Creating upload session...")
    r = requests.post(
        f"{_API}/{uid}/media",
        params={
            "media_type": "REELS",
            "upload_type": "resumable",
            "caption": caption,
            "share_to_feed": "true",
            "access_token": token,
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    container_id = data["id"]
    upload_uri = data["uri"]
    print(f"  [IG] Container ID: {container_id}")

    # Step 2: Stream video bytes to Facebook's resumable upload endpoint
    print(f"  [IG] Uploading {file_size // 1024 // 1024} MB...")
    with open(video_path, "rb") as f:
        r = requests.post(
            upload_uri,
            headers={
                "Authorization": f"OAuth {token}",
                "offset": "0",
                "file_size": str(file_size),
            },
            data=f,
            timeout=300,
        )
    r.raise_for_status()

    # Step 3: Poll until container is ready (can take 1-5 minutes)
    print("  [IG] Waiting for video processing...")
    for i in range(36):
        time.sleep(10)
        r = requests.get(
            f"{_API}/{container_id}",
            params={"fields": "status_code,status", "access_token": token},
            timeout=15,
        )
        r.raise_for_status()
        info = r.json()
        status = info.get("status_code", "IN_PROGRESS")
        print(f"  [IG] Status ({i + 1}/36): {status}")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"IG container failed: {info.get('status', info)}")
    else:
        raise TimeoutError("IG container did not finish processing within 6 minutes")

    # Step 4: Publish
    print("  [IG] Publishing Reel...")
    r = requests.post(
        f"{_API}/{uid}/media_publish",
        params={"creation_id": container_id, "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    media_id = r.json()["id"]
    url = f"https://www.instagram.com/reel/{media_id}/"
    print(f"  [IG] Published: {url}")
    return url
