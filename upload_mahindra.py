"""
Upload mahindra_short.mp4 to YouTube with provided tags.
Run AFTER make_mahindra_video.py completes.
"""

import os, sys, json, re, pickle
sys.path.insert(0, r"C:\Users\user\Desktop\dashboard")

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

CHANNEL_SLUG = "stock_wizard"
VIDEO_PATH   = r"C:\Users\user\Desktop\YTShorts\output\mahindra_short.mp4"

TITLE = "Mahindra DHAMAKA! 14% Volume JUMP - SUV, Tractor, 1300+ Patents! M&M April 2026"

SCRIPT_SUMMARY = (
    "Mahindra & Mahindra abhi strong news flow mein hai. "
    "April 2026 mein 56,331 SUVs beche (8% growth), total auto volumes 94,627 vehicles (14% YoY). "
    "Tractor business mein 46,404 units (20% growth) - rural demand recovery ka strong signal. "
    "Tech side: patent portfolio 56 se 1,300+ tak, Carnot Technologies mein stake badhaya."
)

USER_TAGS = [
    "MahindraAndMahindra", "Mahindra", "MAndM", "AutoSector", "SUVSales",
    "TractorSales", "RuralDemand", "TechInnovation", "Patents",
    "CarnotTechnologies", "IndianStocks", "ShareMarketIndia",
    "StockMarket", "NSE", "MarketToday", "StockNews",
    "IndianAutoSector", "MahindraStock", "Shorts", "YouTubeShorts",
]


def get_yt_service():
    token_file = os.path.join(
        r"C:\Users\user\Desktop\dashboard\channels\youtube",
        f"{CHANNEL_SLUG}_token.pickle",
    )
    with open(token_file, "rb") as f:
        creds = pickle.load(f)
    if isinstance(creds, Credentials):
        return build("youtube", "v3", credentials=creds)
    if isinstance(creds, dict):
        c = Credentials(
            token=creds.get("token"), refresh_token=creds.get("refresh_token"),
            token_uri=creds.get("token_uri","https://oauth2.googleapis.com/token"),
            client_id=creds.get("client_id"), client_secret=creds.get("client_secret"),
        )
        return build("youtube", "v3", credentials=c)
    print("ERROR: Unrecognized credential format.")
    sys.exit(1)


def sanitize_tags(tags):
    clean, total = [], 0
    for t in tags:
        t = re.sub(r'[^\w\s\-\']', '', t, flags=re.UNICODE).strip()
        if not t or total + len(t) + 1 > 500: continue
        clean.append(t); total += len(t) + 1
    return clean


def build_description(tags):
    hashtags = " ".join(f"#{t.replace(' ','')}" for t in tags)
    return (
        f"{TITLE}\n\n"
        f"{SCRIPT_SUMMARY}\n\n"
        f"💡 Bullish ya Bearish? Comment mein batao!\n"
        f"📈 Daily stock updates ke liye Subscribe karo!\n"
        f"🔔 Bell icon dabao — koi update miss mat karo!\n\n"
        f"{'━'*32}\n"
        f"{hashtags}\n"
        f"{'━'*32}\n"
        f"#Shorts #YouTubeShorts #StockMarket #IndianStocks #ShareMarket"
    )


def main():
    print("=" * 60)
    print("  MAHINDRA SHORT — YouTube Upload")
    print("=" * 60)

    if not os.path.exists(VIDEO_PATH):
        print(f"  ERROR: Video not found — render first.")
        sys.exit(1)

    size_mb = os.path.getsize(VIDEO_PATH) / 1024 / 1024
    print(f"  Video: {size_mb:.1f} MB")

    final_tags  = sanitize_tags(USER_TAGS)
    description = build_description(final_tags)

    print(f"  Tags ({len(final_tags)}): {', '.join(final_tags[:6])}...")
    print(f"  Title: {TITLE[:70]}...")

    print("\n  Connecting to YouTube...")
    youtube = get_yt_service()

    body = {
        "snippet": {
            "title":                TITLE[:100],
            "description":          description,
            "tags":                 final_tags,
            "categoryId":           "25",
            "defaultLanguage":      "hi",
            "defaultAudioLanguage": "hi",
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids":             False,
        },
    }

    print("  Uploading...")
    media   = MediaFileUpload(VIDEO_PATH, mimetype="video/mp4",
                              chunksize=1024*1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Uploading... {int(status.progress()*100)}%", end="\r")

    video_id  = response["id"]
    video_url = f"https://www.youtube.com/shorts/{video_id}"

    print(f"\n{'='*60}")
    print(f"  UPLOADED!")
    print(f"  URL: {video_url}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
