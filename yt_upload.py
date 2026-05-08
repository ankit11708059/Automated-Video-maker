"""
YouTube upload helper for the English finance/crypto pipeline.

Token loading priority:
  1. youtube_token.pickle  (written by GitHub Actions from the YOUTUBE_TOKEN secret)
  2. stock_wizard_token.pickle in the dashboard folder (local dev fallback — no setup needed)
"""

import os
import re
import pickle

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

_HERE = os.path.dirname(os.path.abspath(__file__))

# Try local CI-written token first, then fall back to the existing dashboard token
_TOKEN_CANDIDATES = [
    os.path.join(_HERE, "youtube_token.pickle"),
    os.path.join(_HERE, "..", "dashboard", "channels", "youtube", "stock_wizard_token.pickle"),
]


def _get_yt():
    for path in _TOKEN_CANDIDATES:
        if os.path.exists(path):
            with open(path, "rb") as f:
                creds = pickle.load(f)
            break
    else:
        raise FileNotFoundError(
            "No YouTube token found. Either:\n"
            "  • In CI:    set YOUTUBE_TOKEN secret (base64 of your token pickle)\n"
            "  • Locally:  run py auth_new_channel.py  OR  ensure stock_wizard_token.pickle exists"
        )

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
        # Strip to pure ASCII
        t = t.encode("ascii", "ignore").decode("ascii")
        # Only a-z, 0-9, spaces — no hyphens, apostrophes, special chars
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


def _build_description(title: str, seo_description: str, tags: list[str]) -> str:
    """
    Build a YouTube-optimised description.
    First ~150 chars are visible in search results — lead with key info.
    """
    # Pick the 8 best hashtags for the description footer
    def _tag_to_hashtag(t):
        return "#" + re.sub(r'\s+', '', t)
    hashtags = " ".join(_tag_to_hashtag(t) for t in tags[:8] if len(t) > 2)

    return (
        f"{seo_description}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔔 Subscribe for daily finance & crypto alerts\n"
        f"👍 Like this video if it was useful\n"
        f"💬 Comment: Bullish or Bearish?\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{hashtags}\n"
        f"#Shorts #YouTubeShorts #FinanceShorts #InvestingShorts #MoneyShorts"
    )


def upload_video(video_path: str, title: str, seo_description: str, tags: list[str]) -> str:
    """
    Upload video_path to YouTube as a public Short.
    Returns the YouTube Shorts URL.

    Args:
        video_path:       Path to the .mp4 file
        title:            Viral title from script_gen_en (max 100 chars enforced)
        seo_description:  Full description from script_gen_en
        tags:             25 SEO tags from script_gen_en
    """
    clean = _sanitize_tags(tags)
    desc  = _build_description(title, seo_description, clean)

    yt = _get_yt()
    req = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title":                title[:100],
                "description":          desc,
                "tags":                 clean,
                "categoryId":           "25",
                "defaultLanguage":      "hi",
                "defaultAudioLanguage": "hi",
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
