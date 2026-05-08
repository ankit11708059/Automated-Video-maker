"""
Upload a YouTube Short to your channel with optimized metadata for maximum reach.

ONE-TIME SETUP (do this once):
  1. Go to https://console.cloud.google.com
  2. Create a new project (name it anything, e.g. "YTShorts")
  3. Search "YouTube Data API v3" → Enable it
  4. Go to APIs & Services → Credentials → Create Credentials → OAuth client ID
  5. Application type: Desktop App → Name it "YTShorts Uploader" → Create
  6. Click Download JSON → rename file to client_secrets.json
  7. Place client_secrets.json in: C:\\Users\\user\\Desktop\\YTShorts\\

Then run:
  py upload_youtube.py                      <- uploads tata_motors_short.mp4
  py upload_youtube.py output\my_video.mp4  <- uploads a specific file
"""

import os, sys, pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

BASE_DIR       = r"C:\Users\user\Desktop\YTShorts"
CLIENT_SECRETS = os.path.join(BASE_DIR, "client_secrets.json")
TOKEN_FILE     = os.path.join(BASE_DIR, "youtube_token.pickle")
OUTPUT_DIR     = os.path.join(BASE_DIR, "output")
SCOPES         = ["https://www.googleapis.com/auth/youtube.upload",
                  "https://www.googleapis.com/auth/youtube"]

# ── Per-video metadata — edit this for each new video ─────────────────────────
VIDEO_FILE = os.path.join(OUTPUT_DIR, "vodafone_short.mp4")

TITLE = "Vodafone Idea AGR Bill \U0001f4c9 Rs.87K → Rs.64K Crore! | Investor Update | #Shorts"

DESCRIPTION = """\
Vodafone Idea ka Adjusted Gross Revenue dues officially revise ho gaya — Rs.87,695 crore se ghatakar Rs.64,046 crore!

\U0001f4ca Kya Hua:
• DoT ne AGR dues Dec 2025 tak Rs.87,695 Cr pe freeze kiye the
• Government committee ne re-check ke baad Rs.64,046 Cr final kiya
• Bill mein roughly Rs.23,000 crore ki reduction

\U0001f4c5 Payment Plan:
• FY 2031-32 to 2034-35: Minimum Rs.100 crore/year
• FY 2035-36 to 2040-41: Remaining amount in 6 equal installments
• Ek saath nahi dena — long-term structured payment

\U0001f4a1 Investor Angle:
• Short-term cashflow pressure kaafi kam hua
• AGR chapter structured ho gaya — khatam nahi
• Vodafone Idea abhi bhi high-risk stock hai
• Lekin AGR front pe sentiment clearly positive

\U0001f514 Aise hi tough financial news ko simple Hinglish mein samajhne ke liye follow karo!
\U0001f44d Like karo | \U0001f501 Share karo | \U0001f514 Subscribe karo

#VodafoneIdea #Vi #AGR #AdjustedGrossRevenue #Telecom #IndianStocks \
#StockMarket #ShareMarket #DoT #TelecomIndia #NSE #BSE \
#Shorts #YouTubeShorts #StockMarketHindi #FinanceIndia #InvestIndia
"""

TAGS = [
    "Vodafone Idea", "Vi stock", "AGR dues", "telecom india",
    "indian stocks", "stock market", "share market", "DoT telecom",
    "NSE", "BSE", "trading india", "stock alert",
    "shorts", "youtube shorts", "stock market hindi",
]

CATEGORY_ID  = "25"   # News & Politics — best for stock news reach
PRIVACY      = "public"
LANGUAGE     = "hi"


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS):
                print("\nERROR: client_secrets.json not found!")
                print("Follow the setup steps at the top of this file.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return creds


def upload(video_path):
    if not os.path.exists(video_path):
        print(f"ERROR: Video not found: {video_path}")
        sys.exit(1)

    size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"\nUploading: {os.path.basename(video_path)}  ({size_mb:.1f} MB)")
    print(f"Title    : {TITLE}")
    print(f"Privacy  : {PRIVACY}")

    creds   = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title":                TITLE,
            "description":          DESCRIPTION,
            "tags":                 TAGS,
            "categoryId":           CATEGORY_ID,
            "defaultLanguage":      LANGUAGE,
            "defaultAudioLanguage": LANGUAGE,
        },
        "status": {
            "privacyStatus":           PRIVACY,
            "selfDeclaredMadeForKids": False,
            "madeForKids":             False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4",
                            chunksize=1024 * 1024, resumable=True)

    request = youtube.videos().insert(part="snippet,status", body=body,
                                      media_body=media)

    print("\nUploading", end="", flush=True)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"\r  Progress: {pct}%  ", end="", flush=True)

    video_id  = response["id"]
    video_url = f"https://www.youtube.com/shorts/{video_id}"

    print(f"\n\n{'='*60}")
    print(f"  UPLOADED SUCCESSFULLY!")
    print(f"  Video ID : {video_id}")
    print(f"  URL      : {video_url}")
    print(f"  Title    : {response['snippet']['title']}")
    print(f"{'='*60}")
    return video_url


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else VIDEO_FILE
    upload(path)
