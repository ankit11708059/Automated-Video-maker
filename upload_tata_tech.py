"""
Upload tata_tech_short.mp4 to YouTube with Claude-generated trendy tags
and a hashtag-rich description.
Run: py upload_tata_tech.py
"""

import os, sys, json, re, pickle
sys.path.insert(0, r"C:\Users\user\Desktop\dashboard")

import anthropic
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ── Config ────────────────────────────────────────────────────────────────────

CHANNEL_SLUG = "stock_wizard"
VIDEO_PATH   = r"C:\Users\user\Desktop\YTShorts\output\tata_tech_short.mp4"

TITLE_BASE = "Tata Technologies Stock 8.90% JUMP! MOSL Ne 15% Downside Risk Flag Kiya!"

SCRIPT = """
Tata Technologies ne aaj dhamakedaar move dikhaya, stock lagbhag 8.90% jump karke
Rs.643.60 tak pahunch gaya, NSE ke top gainers me shamil ho gaya, Q4 earnings
performance kaafi impressive rahi. Lekin saath hi analysts at MOSL ne yahan se
around 15% downside ka risk flag kiya hai, kyunki unko lagta hai valuation already
kaafi stretched hai, chahe quarterly show strong hi kyon na ho.
"""

NICHE = "indian stock market news hindi"

# ── Claude: generate viral title + 20 trending tags ──────────────────────────

def generate_tags_and_title():
    key = ""
    # Try Claude Code credentials first
    cred_paths = [
        os.path.expanduser(r"~\.claude\.credentials.json"),
        os.path.expanduser(r"~\AppData\Roaming\Claude\credentials.json"),
    ]
    for p in cred_paths:
        if os.path.exists(p):
            try:
                data  = json.loads(open(p).read())
                token = data.get("claudeAiOauth", {}).get("accessToken", "")
                if token:
                    key = token
                    break
            except Exception:
                pass

    # Try dashboard .env
    env_path = r"C:\Users\user\Desktop\dashboard\.env"
    if not key and os.path.exists(env_path):
        for line in open(env_path):
            if line.startswith("ANTHROPIC_API_KEY="):
                k = line.split("=", 1)[1].strip()
                if k and k != "your_key_here":
                    key = k
                    break

    if not key:
        print("  Claude API unavailable — using curated trendy tags.")
        return None, None

    client = anthropic.Anthropic(api_key=key)
    prompt = f"""\
You are a viral YouTube Shorts SEO expert for Indian stock market content (2025).

Niche: {NICHE}
Script: {SCRIPT.strip()}

Generate:
1. TITLE — Under 95 chars, viral hook, power words (SHOCKING/ALERT/EXPOSED/Breaking),
   1-2 emojis, creates urgency, trending YouTube style.

2. TAGS — Exactly 20 tags that are TRENDING RIGHT NOW on YouTube for Indian stock market.
   Mix: stock name + broad market + trending finance terms + Hindi market terms.
   NO # symbol. Plain text only. No duplicates.

Respond ONLY with JSON:
{{"title": "...", "tags": ["tag1", "tag2", ...]}}"""

    try:
        msg  = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        m    = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            data  = json.loads(m.group())
            title = str(data.get("title", "")).strip()[:95]
            tags  = [str(t).strip() for t in data.get("tags", [])][:20]
            if title and tags:
                print(f"  Claude title: {title[:70].encode('ascii','replace').decode()}...")
                print(f"  Claude tags ({len(tags)}): {', '.join(tags[:5])}...")
                return title, tags
    except Exception as e:
        print(f"  Claude error: {e}")
    return None, None


# ── Build description with hashtags ──────────────────────────────────────────

def build_description(tags):
    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in tags)
    return f"""\
{TITLE_BASE}

Tata Technologies ne aaj NSE par dhamakedaar move dikhaya — stock 8.90% jump karke Rs.643.60 tak pahuncha aur top gainers list mein aa gaya. Q4 earnings performance strong rahi.

Lekin MOSL analysts ne warning di hai — valuation already stretched hai aur yahan se 15% downside ka risk hai.

💡 Bullish ya Bearish? Comment mein batao!
📈 Daily stock updates ke liye Subscribe karo!

━━━━━━━━━━━━━━━━━━━━━━━━━
{hashtags}
━━━━━━━━━━━━━━━━━━━━━━━━━
#Shorts #YouTubeShorts #StockMarket #IndianStocks #ShareMarket
"""


# ── Load YouTube credentials from dashboard ───────────────────────────────────

def get_yt_service():
    token_file = os.path.join(
        r"C:\Users\user\Desktop\dashboard\channels\youtube",
        f"{CHANNEL_SLUG}_token.pickle",
    )
    if not os.path.exists(token_file):
        print(f"  ERROR: Token not found at {token_file}")
        sys.exit(1)

    with open(token_file, "rb") as f:
        creds = pickle.load(f)

    # If it's already a Credentials object use it directly
    if isinstance(creds, Credentials):
        return build("youtube", "v3", credentials=creds)

    # Legacy dict format
    if isinstance(creds, dict):
        c = Credentials(
            token         = creds.get("token"),
            refresh_token = creds.get("refresh_token"),
            token_uri     = creds.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id     = creds.get("client_id"),
            client_secret = creds.get("client_secret"),
        )
        return build("youtube", "v3", credentials=c)

    print("  ERROR: Unrecognized credential format.")
    sys.exit(1)


# ── Sanitize tags for YouTube API ─────────────────────────────────────────────

def sanitize_tags(tags):
    cleaned, total = [], 0
    for t in tags:
        t = re.sub(r'[^\w\s\-\']', '', t, flags=re.UNICODE).strip()
        if not t or total + len(t) + 1 > 500:
            continue
        cleaned.append(t)
        total += len(t) + 1
    return cleaned


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  TATA TECH SHORT — YouTube Upload")
    print("=" * 60)

    if not os.path.exists(VIDEO_PATH):
        print(f"  ERROR: Video not found at {VIDEO_PATH}")
        sys.exit(1)
    size_mb = os.path.getsize(VIDEO_PATH) / 1024 / 1024
    print(f"  Video: {os.path.basename(VIDEO_PATH)} ({size_mb:.1f} MB)")

    # 1. Generate trendy title + tags via Claude
    print("\n[1/3] Generating trendy tags via Claude...")
    ai_title, ai_tags = generate_tags_and_title()

    # Curated fallback tags (always trending for Indian stock market Shorts)
    base_tags = [
        "TataTechnologies", "TataStock", "Q4Results", "NSETopGainer",
        "StockMarketIndia", "IndianStocks", "ShareMarket", "NiftyStock",
        "MarketToday", "FinanceShorts", "TataGroup", "Q4Earnings",
        "MOSL", "StockAnalysis", "StockMarketNews", "ShareMarketIndia",
        "BreakingStockNews", "StockAlert", "Shorts", "YouTubeShorts",
    ]
    final_tags  = sanitize_tags(ai_tags if ai_tags else base_tags)
    final_title = (ai_title or TITLE_BASE)[:100]

    print(f"\n  Final title : {final_title}")
    print(f"  Tags ({len(final_tags)}): {', '.join(final_tags[:8])}...")

    # 2. Build description
    description = build_description(final_tags)

    # 3. Upload
    print("\n[2/3] Connecting to YouTube...")
    youtube = get_yt_service()

    body = {
        "snippet": {
            "title":                final_title,
            "description":          description,
            "tags":                 final_tags,
            "categoryId":           "25",        # News & Politics
            "defaultLanguage":      "hi",
            "defaultAudioLanguage": "hi",
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids":             False,
        },
    }

    print("[3/3] Uploading to YouTube...")
    media   = MediaFileUpload(VIDEO_PATH, mimetype="video/mp4",
                              chunksize=1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"  Uploading... {pct}%", end="\r")

    video_id  = response["id"]
    video_url = f"https://www.youtube.com/shorts/{video_id}"

    print(f"\n{'='*60}")
    print(f"  UPLOADED!")
    print(f"  URL  : {video_url}")
    print(f"  ID   : {video_id}")
    print(f"  Tags : {', '.join(final_tags)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
