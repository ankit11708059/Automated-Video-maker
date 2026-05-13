"""
YouTube upload helper for the "Lost History & Forgotten Mysteries" channel.
Uses a dedicated token (history_token.pickle) and English language metadata.

Token loading priority:
  1. history_token.pickle  (CI: written from HISTORY_YT_TOKEN secret)
  2. Raises if missing.
"""

import os
import re
import pickle

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

_HERE = os.path.dirname(os.path.abspath(__file__))
_TOKEN_PATH = os.path.join(_HERE, "history_token.pickle")


def _get_yt():
    if not os.path.exists(_TOKEN_PATH):
        raise FileNotFoundError(
            "history_token.pickle not found. Either:\n"
            "  • In CI:   set HISTORY_YT_TOKEN secret (base64 of token pickle)\n"
            "  • Locally: run py auth_history_channel.py"
        )

    with open(_TOKEN_PATH, "rb") as f:
        creds = pickle.load(f)

    if not isinstance(creds, Credentials):
        creds = Credentials(
            token=creds.get("token"),
            refresh_token=creds.get("refresh_token"),
            token_uri=creds.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=creds.get("client_id"),
            client_secret=creds.get("client_secret"),
        )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("youtube", "v3", credentials=creds)


def _sanitize_tags(tags: list[str]) -> list[str]:
    """Strict YouTube-safe tags: ASCII letters/digits/spaces only, max 25 chars each."""
    clean, total = [], 0
    seen = set()
    for t in tags:
        t = t.encode("ascii", "ignore").decode("ascii")
        t = re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()
        t = re.sub(r" +", " ", t)
        if not t or len(t) < 2 or len(t) > 25 or t in seen:
            continue
        if total + len(t) + 1 > 450:
            break
        clean.append(t)
        seen.add(t)
        total += len(t) + 1
    print(f"  Tags after sanitize ({len(clean)}): {clean}")
    return clean


def _build_description(seo_description: str, tags: list[str]) -> str:
    def _tag_to_hashtag(t):
        return "#" + re.sub(r'\s+', '', t)
    hashtags = " ".join(_tag_to_hashtag(t) for t in tags[:8] if len(t) > 2)
    return (
        f"{seo_description}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔔 Subscribe for daily lost history & mysteries\n"
        f"👍 Like if this gave you chills\n"
        f"💬 Comment: What do YOU think happened?\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{hashtags}\n"
        f"#Shorts #LostHistory #AncientMysteries #UnsolvedMysteries #HistoryShorts"
    )


def upload_video(video_path: str, title: str, seo_description: str, tags: list[str]) -> str:
    """Upload as a public English Short on the history channel."""
    clean = _sanitize_tags(tags)
    desc = _build_description(seo_description, clean)

    yt = _get_yt()
    req = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title":                title[:100],
                "description":          desc,
                "tags":                 clean,
                "categoryId":           "27",  # Education
                "defaultLanguage":      "en",
                "defaultAudioLanguage": "en",
            },
            "status": {
                "privacyStatus":           "public",
                "selfDeclaredMadeForKids": False,
                "madeForKids":             False,
            },
        },
        media_body=MediaFileUpload(video_path, mimetype="video/mp4",
                                   chunksize=1024 * 1024, resumable=True),
    )

    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  Uploading... {int(status.progress() * 100)}%", end="\r")

    url = f"https://www.youtube.com/shorts/{resp['id']}"
    print(f"\n  Uploaded -> {url}")
    return url
