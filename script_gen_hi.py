"""
Claude Sonnet-powered Hindi/Hinglish script + SEO generator.
Used for both Indian stock market and crypto channels.
Thinks like a senior SEO + finance content strategist for Indian audience.
"""

import json
import re
import anthropic
from config import ANTHROPIC_API_KEY

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


_SYSTEM = """\
You are two experts in one:

1. SENIOR HINDI FINANCE CONTENT CREATOR — You have grown Indian stock market and
   crypto YouTube channels to 500k+ subscribers. You know exactly what makes Indian
   retail investors stop scrolling: FOMO, fear of missing out, specific rupee/percentage
   numbers, and relatable Hinglish language. You write in the style of top Indian finance
   YouTubers (Pranjal Kamra, Akshat Shrivastava style hooks).

2. SENIOR YOUTUBE SEO STRATEGIST for India — You deeply understand how Indian users
   search on YouTube. You know which keywords have 100k+ monthly searches, how to
   structure descriptions for the algorithm, and which tags actually drive discovery.
   You think in terms of: search volume, competition, relevance, trending vs evergreen."""


_STOCK_PROMPT = """\
Create a complete, SEO-optimised Hindi YouTube Short for this Indian stock market news.

NEWS HEADLINE: {title}
NEWS DETAILS: {desc}
TODAY'S DATE: May 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 1 — AUDIO SCRIPT (Hinglish, ~130 words)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Language: Mix Hindi Devanagari words with English finance terms naturally.
ElevenLabs will speak this — write naturally, not like a news reader.

Hook (0–8s) — Make the FIRST sentence create instant FOMO or fear:
  Examples of powerful hooks:
  "अगर आपके portfolio में {company} है, तो यह video end तक देखो!"
  "आज {company} में जो हुआ वो किसी ने expect नहीं किया था!"
  "यह एक number आपकी investment strategy बदल देगा!"

Body (8–45s):
  • Exact news in simple Hinglish (no jargon without explanation)
  • WHY it matters to a small retail investor (relatable: "आपकी EMI", "आपका portfolio")
  • What expert analysts are saying or what could happen next
  • Include the specific percentage / rupee figure from the news

CTA (45–60s):
  "Bullish हो या Bearish — comment में बताओ!"
  "Daily market updates के लिए subscribe करो और bell icon दबाओ!"
  "Like करो अगर यह video helpful लगी!"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 2 — VIRAL YOUTUBE TITLE (max 80 chars)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use ROMAN/HINGLISH — mix Hindi words in Roman script + English.
Include: company name + number/% + power word + question or consequence.
Examples:
  "{Company} Stock +7% 🚀 | 52-Week High! Kya Abhi BUY Karna Chahiye?"
  "BREAKING: {Company} Ne Toda RECORD! {X}% Uda — Buy, Sell Ya Hold?"
Max 80 chars. The number/emoji should be early in the title.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 3 — ON-SCREEN DISPLAY SECTIONS (4 sections)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL: Use ROMAN SCRIPT ONLY (PIL cannot render Devanagari on video).
Hinglish transliteration: "Kya Abhi BUY Karna Chahiye?" NOT "क्या अभी BUY?"

image_type: "breaking" | "company" | "market" | "cta"
time_weight: word count in that audio section (all 4 must sum to ~130)
lines: exactly 3 lines, max 32 chars each, punchy, include numbers

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 4 — SEO TAGS (exactly 30 tags, think like a senior SEO)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Think: what are Indian investors actually typing in YouTube search right now?
Mix these categories (5-6 each):

A. HIGH VOLUME EVERGREEN (100k+ monthly searches):
   "share market", "stock market today", "nse bse", "sensex nifty today"

B. COMPANY + EVENT SPECIFIC:
   "{company} share price", "{company} q4 results", "{company} target price 2026"

C. TRENDING RIGHT NOW (include "2026", "may 2026", "aaj"):
   "{company} share aaj", "stocks hitting 52 week high may 2026"

D. HINDI LANGUAGE SEARCHES (how Indian users type):
   "share market khabar", "kaunsa stock kharide", "share market hindi mein"
   "{company} share kharidna chahiye"

E. QUESTION BASED (high intent, conversion):
   "is {company} a good investment", "should i buy {company} stock",
   "{company} share price target"

F. SHORTS DISCOVERY:
   "stock market shorts hindi", "share market shorts", "finance shorts hindi",
   "investment shorts india", "trading shorts hindi"

Rule: Each tag max 30 chars, no special characters, all lowercase.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 5 — YOUTUBE DESCRIPTION (SEO-optimised, ~200 words)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIRST LINE (150 chars max) — appears in search results, must contain main keyword:
  "{Company} share price today {date} — {key number}% {movement} | {reason in brief}"

Body (3-4 sentences):
  • Expand on the news and why it matters
  • Include 2-3 relevant keywords naturally
  • Mention "Indian stock market", "NSE", "BSE" for SEO

CTA block:
  "📈 Subscribe karo daily market updates ke liye"
  "🔔 Bell icon dabao — koi update miss mat karo"
  "💬 Comment: Bullish ya Bearish?"

Hashtags (last line, 8 tags):
  #StockMarket #ShareMarket #NSE #Shorts + 4 specific to this story

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 6 — PEXELS QUERY (3-4 words for background image)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pick based on sector: "automobile india", "india bank money", "india tech software", etc.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT — VALID JSON ONLY, no markdown, no explanation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{
  "audio_script":  "...",
  "viral_title":   "...",
  "sections": [
    {{"image_type": "breaking", "time_weight": 25, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "company",  "time_weight": 40, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "market",   "time_weight": 40, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "cta",      "time_weight": 25, "lines": ["LINE 1", "Line 2", "Line 3"]}}
  ],
  "tags":        ["tag1","tag2",...],
  "description": "...",
  "pexels_query":"..."
}}"""


_CRYPTO_PROMPT = """\
Create a complete, SEO-optimised Hindi YouTube Short for this crypto news.

NEWS HEADLINE: {title}
NEWS DETAILS: {desc}
TODAY'S DATE: May 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 1 — AUDIO SCRIPT (Hinglish, ~130 words)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Language: Natural Hinglish for Indian crypto investors (beginner to intermediate).
ElevenLabs speaks this — write conversationally, like a knowledgeable friend.

Hook (0–8s):
  "Bitcoin holders — यह news आपके लिए है!"
  "Crypto में invest किया है? यह 60 seconds बहुत important हैं!"
  "{Coin} ने आज जो किया — market हिल गया!"

Body (8–45s):
  • What happened, specific price/% figure
  • India-specific angle: Rupee value, Indian exchange, RBI impact if any
  • Is this buying opportunity ya danger signal?
  • What on-chain data / analysts say

CTA (45–60s):
  "Bullish ya Bearish? Comment mein batao!"
  "Daily crypto updates — free mein — subscribe karo!"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 2 — VIRAL TITLE (max 80 chars, Hinglish Roman)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Include coin name + price/% + emotion/urgency.
Examples:
  "Bitcoin ₹{X} Lakh Par! Kya Abhi Buy Karna Chahiye? 🚀"
  "BREAKING: {Coin} +{X}% Uda! India Mein Invest Karo Ya Nahi?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 3 — ON-SCREEN SECTIONS (ROMAN SCRIPT ONLY, 4 sections)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Same rules as stocks. Roman Hinglish only. 3 lines per section, max 32 chars each.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 4 — SEO TAGS (exactly 30, senior SEO thinking for Indian crypto audience)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Categories (5-6 each):

A. HIGH VOLUME CRYPTO INDIA (100k+ searches):
   "bitcoin india", "crypto news hindi", "bitcoin price today india",
   "cryptocurrency india", "bitcoin kaise khareedein"

B. COIN SPECIFIC:
   "{coin} price today", "{coin} india", "{coin} 2026 prediction"

C. TRENDING:
   "{coin} price may 2026", "crypto market today hindi", "bitcoin all time high 2026"

D. HINDI SEARCHES:
   "bitcoin aaj ka bhav", "crypto mein invest karna chahiye",
   "kaunsa crypto khareedein", "crypto news aaj hindi mein"

E. QUESTION BASED:
   "is {coin} good investment india", "should i buy {coin} in india",
   "bitcoin 2026 mein kya hoga"

F. SHORTS DISCOVERY:
   "crypto shorts hindi", "bitcoin shorts india", "cryptocurrency shorts",
   "crypto news shorts", "bitcoin news shorts hindi"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 5 — YOUTUBE DESCRIPTION (~200 words, SEO)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
First line: "{Coin} price today India — {key fact} | {date} crypto news Hindi"
Body: explain news, India angle, investment angle with natural keyword placement.
CTA + 8 hashtags: #Bitcoin #Crypto #CryptoIndia #Shorts + 4 story-specific.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 6 — PEXELS QUERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"bitcoin cryptocurrency digital gold" or similar.

OUTPUT — VALID JSON ONLY:
{{
  "audio_script":  "...",
  "viral_title":   "...",
  "sections": [
    {{"image_type": "breaking", "time_weight": 25, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "company",  "time_weight": 40, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "market",   "time_weight": 40, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "cta",      "time_weight": 25, "lines": ["LINE 1", "Line 2", "Line 3"]}}
  ],
  "tags":        ["tag1","tag2",...],
  "description": "...",
  "pexels_query":"..."
}}"""


def _call_claude(prompt: str) -> dict:
    msg = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Claude returned invalid JSON: {e}\n\n{raw[:400]}")
    for key in ("audio_script", "viral_title", "sections", "tags", "description", "pexels_query"):
        if key not in data:
            raise RuntimeError(f"Missing key '{key}' in Claude response.")
    return data


def generate_hindi_stock(title: str, desc: str) -> dict:
    """Generate Hindi Hinglish script + SEO for Indian stock market video."""
    return _call_claude(_STOCK_PROMPT.format(title=title, desc=(desc or "")[:500]))


def generate_hindi_crypto(title: str, desc: str) -> dict:
    """Generate Hindi Hinglish script + SEO for crypto video."""
    return _call_claude(_CRYPTO_PROMPT.format(title=title, desc=(desc or "")[:500]))


if __name__ == "__main__":
    result = generate_hindi_stock(
        title="Titan shares surge 7%, hit fresh 52-week high on 35% YoY PAT growth",
        desc="Titan Company Q4 results beat expectations. Jewellery segment drove growth.",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
