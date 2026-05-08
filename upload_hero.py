"""Upload hero_short.mp4 to YouTube."""

import os, sys, re, pickle
sys.path.insert(0, r"C:\Users\user\Desktop\dashboard")
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

CHANNEL_SLUG = "stock_wizard"
VIDEO_PATH   = r"C:\Users\user\Desktop\YTShorts\output\hero_short.mp4"
TITLE        = "Hero MotoCorp DHAMAKA! 15% Profit Jump + Rs.110 Dividend + Euler EV Investment!"

SUMMARY = (
    "Hero MotoCorp strong results, dividend aur EV moves ki wajah se spotlight mein hai. "
    "Q3 FY26 profit 14-15% jump karke Rs.1,270 crore, revenue Rs.12,400 crore+ (21-22% growth), volumes 16% up. "
    "Board ne Rs.110/share interim dividend declare kiya. "
    "Euler Motors mein Rs.275 crore ka extra EV investment - electric 3-wheeler focus."
)

TAGS = [
    "HeroMotoCorp", "TwoWheelerStocks", "Q3Results", "Dividend", "EulerMotors",
    "EVGrowth", "AutoSector", "IndianStocks", "ShareMarketIndia", "EarningsSeason",
    "LongTermInvesting", "StockMarket", "NSE", "MarketToday", "StockNews",
    "HeroElectric", "MotorCorp", "BikeStocks", "Shorts", "YouTubeShorts",
]

def get_yt():
    tf = os.path.join(r"C:\Users\user\Desktop\dashboard\channels\youtube",
                      f"{CHANNEL_SLUG}_token.pickle")
    creds = pickle.load(open(tf, "rb"))
    if isinstance(creds, Credentials): return build("youtube", "v3", credentials=creds)
    c = Credentials(token=creds.get("token"), refresh_token=creds.get("refresh_token"),
                    token_uri=creds.get("token_uri","https://oauth2.googleapis.com/token"),
                    client_id=creds.get("client_id"), client_secret=creds.get("client_secret"))
    return build("youtube", "v3", credentials=c)

def sanitize(tags):
    clean, total = [], 0
    for t in tags:
        t = re.sub(r'[^\w\s\-\']', '', t, flags=re.UNICODE).strip()
        if not t or total + len(t) + 1 > 500: continue
        clean.append(t); total += len(t) + 1
    return clean

def main():
    print("=" * 60)
    print("  HERO MOTOCORP — YouTube Upload")
    print("=" * 60)
    if not os.path.exists(VIDEO_PATH):
        print("ERROR: Video not found."); sys.exit(1)
    print(f"  Video: {os.path.getsize(VIDEO_PATH)/1024/1024:.1f} MB")

    tags  = sanitize(TAGS)
    htags = " ".join(f"#{t}" for t in tags)
    desc  = (f"{TITLE}\n\n{SUMMARY}\n\n"
             f"💡 Bullish ya Bearish? Comment mein batao!\n"
             f"📈 Daily stock updates ke liye Subscribe karo!\n"
             f"🔔 Bell icon dabao!\n\n"
             f"{'━'*32}\n{htags}\n{'━'*32}\n"
             f"#Shorts #YouTubeShorts #StockMarket #IndianStocks")

    yt  = get_yt()
    req = yt.videos().insert(
        part="snippet,status",
        body={"snippet": {"title": TITLE[:100], "description": desc, "tags": tags,
                          "categoryId": "25", "defaultLanguage": "hi",
                          "defaultAudioLanguage": "hi"},
              "status":  {"privacyStatus": "public", "selfDeclaredMadeForKids": False,
                          "madeForKids": False}},
        media_body=MediaFileUpload(VIDEO_PATH, mimetype="video/mp4",
                                   chunksize=1024*1024, resumable=True)
    )
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st: print(f"  Uploading... {int(st.progress()*100)}%", end="\r")
    print(f"\n  UPLOADED -> https://www.youtube.com/shorts/{resp['id']}")

if __name__ == "__main__":
    main()
