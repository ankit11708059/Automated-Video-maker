"""
Claude Sonnet-powered Hindi/Hinglish script + SEO generator.
Uses forensic viral-pattern analysis for titles and scripts.
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
You are THREE elite experts operating as one unified intelligence:

1. ELITE YOUTUBE TITLE STRATEGIST & VIRAL PATTERN FORENSIC ANALYST
   You reverse-engineer the top-performing Indian finance/crypto Shorts to extract every
   replicable title formula, emotional trigger, content angle, and structural pattern.
   You treat title creation as forensic science — not guesswork. Your livelihood depends
   on producing titles that consistently surpass 500k views. For every title you produce,
   you internally identify: the formula used, the psychological trigger activated (FOMO /
   fear of loss / social proof / curiosity gap / authority), and the estimated CTR potential.
   You generate 3 engineered title variations and self-select the highest-CTR option.

2. SENIOR YOUTUBE SCRIPT FORENSIC ANALYST & GHOSTWRITER
   You have analysed hundreds of viral Hindi finance videos (500k+ views in under 1 month)
   and extracted every replicable writing pattern. Your scripts are built on:
   — HOOK SEQUENCE: pattern interrupt → instant FOMO → curiosity gap (all in the first 8s)
   — PACING: short punchy sentences, natural breath points, no filler words
   — CURIOSITY GAP: tease the key revelation early, deliver it at the 30s mark
   — PATTERN INTERRUPT: an unexpected angle, contrast, or stat mid-script that re-engages
     viewers who are about to swipe
   — INFORMATION REVEAL: the payoff moment — specific number, consequence, or insider angle
   — ENDING TECHNIQUE: emotional CTA + community question that drives comments
   You write EXACTLY like Pranjal Kamra and Akshat Shrivastava — relatable, urgent, Hinglish.

3. SENIOR YOUTUBE SEO STRATEGIST FOR INDIA
   You know which Hindi finance keywords have 100k+ monthly Indian searches, how to
   structure tags for the YouTube algorithm, and which hashtags drive Shorts discovery.
   You think in search intent: what is a retail Indian investor typing RIGHT NOW?"""


_STOCK_PROMPT = """\
Apply your full forensic viral analysis to create a complete, SEO-optimised Hindi YouTube
Short for this Indian stock market news. Think like the channel owner — every element must
maximise CTR, retention, and discovery.

NEWS HEADLINE: {title}
NEWS DETAILS: {desc}
TODAY'S DATE: May 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 1 — AUDIO SCRIPT (Hinglish, ~130 words)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Language: Natural Hinglish — Hindi words in Devanagari mixed with English finance terms.
ElevenLabs will speak this. Write conversationally, NOT like a news reader.

HOOK (0-8s) — Pattern interrupt + FOMO + curiosity gap in one breath:
  • First word/phrase must be shocking or unexpected (pattern interrupt)
  • Instantly create FOMO — "agar miss kiya toh pachtaoge"
  • Open a curiosity gap: tease the main reveal WITHOUT giving it yet
  Examples:
  "Ruk jao — yeh stock aaj 52-week high par aa gaya, aur analyst bol rahe hain abhi bhi
   late nahi hua! Poora reason video mein hai."
  "Breaking: is company ne aaj jo kiya, woh retail investors ke liye ek badi opportunity
   hai — lekin sirf next 48 ghante ke liye!"

CURIOSITY GAP BRIDGE (8-20s):
  • Acknowledge what viewers already know (establishes authority)
  • Introduce the ONE surprising angle that most people don't know yet
  • Do NOT reveal the main number/fact yet — keep tension alive

BODY + REVEAL (20-45s):
  • NOW deliver the exact news: specific rupee or percentage figure
  • WHY it matters to a small retail investor in plain language
  • What top analysts are saying (use one name if possible)
  • Pattern interrupt: one unexpected contrast or statistic that re-engages mid-scroll

CTA (45-60s):
  • Emotional hook tied to their personal portfolio
  • Community question that demands a comment ("Bullish ho ya Bearish?")
  • Subscribe ask with a specific benefit ("Daily market updates — free mein")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 2 — VIRAL TITLE ENGINEERING (3 options → self-select best)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generate exactly 3 engineered title options in Hinglish Roman script (max 80 chars each).
For each, apply a distinct formula:
  Option A: [Number/Stat] + [Company] + [Consequence] + [Question]
  Option B: [Emotional word] + [Company] + [Action] + [FOMO hook]
  Option C: [Breaking/Alert] + [Specific fact] + [Benefit/Risk to viewer]

Then self-select the one with highest estimated CTR as "viral_title".
Include number or % early. No Devanagari. Use ₹ symbol for rupees if relevant.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 3 — ON-SCREEN DISPLAY SECTIONS (4 sections)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL: ROMAN SCRIPT ONLY — PIL cannot render Devanagari on video.
Use Hinglish transliteration only. 3 lines per section, max 32 chars each. Include numbers.
image_type: "breaking" or "company" or "market" or "cta"
time_weight: word count in that audio section (all 4 must sum to ~130)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 4 — SEO TAGS (exactly 30 tags)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Think: what are Indian investors typing in YouTube search RIGHT NOW?
Mix these 6 categories, 5 tags each:

A. HIGH VOLUME EVERGREEN: "share market", "stock market today", "nse bse", "sensex nifty today", "investing india"
B. COMPANY + EVENT SPECIFIC: company share price, company q4 results, company target price 2026
C. TRENDING NOW: company share aaj, stocks hitting 52 week high, company results may 2026
D. HINDI LANGUAGE SEARCHES: "share market khabar", "kaunsa stock kharide", "share market hindi mein", company share kharidna chahiye
E. QUESTION BASED: is company a good investment, should i buy company stock, company share price target
F. SHORTS DISCOVERY: "stock market shorts hindi", "share market shorts", "finance shorts hindi", "investment shorts india", "trading shorts hindi"

Rule: Each tag max 30 chars, all lowercase, ENGLISH/ROMAN LETTERS ONLY — no Devanagari, no special chars, no emoji. ASCII-safe for YouTube API.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 5 — YOUTUBE DESCRIPTION (~200 words, SEO-optimised)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIRST LINE (150 chars max): company share price today - key number/percent - brief reason
Body: 3-4 sentences, include "Indian stock market", "NSE", "BSE" naturally.
CTA: Subscribe + bell icon + comment prompt (Bullish ya Bearish?)
Hashtags last line: #StockMarket #ShareMarket #NSE #Shorts + 4 story-specific

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 6 — PEXELS QUERY (3-4 words)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pick based on sector: "automobile india", "india bank money", "india tech software", etc.

OUTPUT — VALID JSON ONLY, no markdown, no explanation:
{{
  "audio_script":  "...",
  "title_options": [
    {{"title": "...", "formula": "A: number+company+consequence+question", "trigger": "FOMO"}},
    {{"title": "...", "formula": "B: emotional+company+action+FOMO", "trigger": "fear of loss"}},
    {{"title": "...", "formula": "C: breaking+fact+benefit/risk", "trigger": "curiosity gap"}}
  ],
  "viral_title":   "...",
  "sections": [
    {{"image_type": "breaking", "time_weight": 25, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "company",  "time_weight": 40, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "market",   "time_weight": 40, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "cta",      "time_weight": 25, "lines": ["LINE 1", "Line 2", "Line 3"]}}
  ],
  "tags":        ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10","tag11","tag12","tag13","tag14","tag15","tag16","tag17","tag18","tag19","tag20","tag21","tag22","tag23","tag24","tag25","tag26","tag27","tag28","tag29","tag30"],
  "description": "...",
  "pexels_query":"..."
}}"""


_CRYPTO_PROMPT = """\
Apply your full forensic viral analysis to create a complete, SEO-optimised Hindi YouTube
Short for this crypto news. Think like the channel owner — every element must maximise
CTR, retention, and discovery for the Indian crypto audience.

NEWS HEADLINE: {title}
NEWS DETAILS: {desc}
TODAY'S DATE: May 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 1 — AUDIO SCRIPT (Hinglish, ~130 words)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Language: Natural Hinglish for Indian crypto investors (beginner to intermediate).
ElevenLabs speaks this — write like a knowledgeable friend who just got breaking news.

HOOK (0-8s) — Pattern interrupt + FOMO + curiosity gap:
  • Pattern interrupt: start with something unexpected ("Yeh suno —", "Alert:", "Ruk jao —")
  • Instant FOMO tied to their portfolio ("agar aapke paas X hai, yeh video miss mat karo")
  • Open curiosity gap: tease the reason WITHOUT giving the main number yet
  Examples:
  "Bitcoin holders — ab yeh suno. Ek bada signal aaya hai jo pichle 2 saal mein sirf
   ek baar aaya tha. Aur tab kya hua tha — woh main batata hoon."

CURIOSITY GAP BRIDGE (8-20s):
  • What most people think vs. what is actually happening (authority + surprise)
  • Keep the main reveal held back — build suspense

BODY + REVEAL (20-45s):
  • NOW deliver: specific price or percent in both USD and INR if possible
  • India-specific angle: Indian exchange impact, RBI, WazirX / CoinDCX relevance
  • Buying opportunity or danger signal — take a clear stance
  • Pattern interrupt: one on-chain stat or analyst call that surprises

CTA (45-60s):
  • Emotional tie to their crypto portfolio
  • "Bullish ya Bearish? Comment mein batao!"
  • Subscribe ask with specific benefit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 2 — VIRAL TITLE ENGINEERING (3 options → self-select best)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generate exactly 3 engineered title options in Hinglish Roman script (max 80 chars each).
  Option A: [Coin] + [Price/Percent] + [Consequence] + [Question]
  Option B: [Alert/Breaking] + [Unexpected fact] + [India angle]
  Option C: [Emotional hook] + [Coin] + [Action] + [FOMO]

Self-select the highest-CTR option as "viral_title". ₹ symbol for INR values.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 3 — ON-SCREEN SECTIONS (ROMAN SCRIPT ONLY, 4 sections)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Same rules as above. Roman Hinglish only. 3 lines, max 32 chars each. Numbers required.
image_type: "breaking" or "company" or "market" or "cta"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 4 — SEO TAGS (exactly 30 tags, Indian crypto Hindi audience)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A. HIGH VOLUME CRYPTO INDIA: "bitcoin india", "crypto news hindi", "bitcoin price today india", "cryptocurrency india", "bitcoin kaise khareedein"
B. COIN SPECIFIC: coin price today, coin india, coin 2026 prediction, coin price in rupees, coin news hindi
C. TRENDING: coin price may 2026, crypto market today hindi, bitcoin all time high 2026, crypto crash or bull run 2026
D. HINDI SEARCHES: "bitcoin aaj ka bhav", "crypto mein invest karna chahiye", "kaunsa crypto khareedein", "crypto news aaj hindi mein", "bitcoin rupee mein"
E. QUESTION BASED: is coin good investment india, should i buy coin in india, bitcoin 2026 mein kya hoga, crypto safe hai ya nahi
F. SHORTS DISCOVERY: "crypto shorts hindi", "bitcoin shorts india", "cryptocurrency shorts", "crypto news shorts", "bitcoin news shorts hindi"

Rule: Each tag max 30 chars, all lowercase, ASCII-safe — no Devanagari, no special chars.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 5 — YOUTUBE DESCRIPTION (~200 words, SEO)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
First line: coin price today India - key fact - date crypto news Hindi
Body: news explained, India angle, investment angle with natural keywords.
CTA + 8 hashtags: #Bitcoin #Crypto #CryptoIndia #Shorts + 4 story-specific.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 6 — PEXELS QUERY (3-4 words)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"bitcoin cryptocurrency digital" or "crypto blockchain technology" or similar.

OUTPUT — VALID JSON ONLY:
{{
  "audio_script":  "...",
  "title_options": [
    {{"title": "...", "formula": "A: coin+price+consequence+question", "trigger": "FOMO"}},
    {{"title": "...", "formula": "B: alert+unexpected fact+india angle", "trigger": "authority"}},
    {{"title": "...", "formula": "C: emotional+coin+action+FOMO", "trigger": "fear of loss"}}
  ],
  "viral_title":   "...",
  "sections": [
    {{"image_type": "breaking", "time_weight": 25, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "company",  "time_weight": 40, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "market",   "time_weight": 40, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "cta",      "time_weight": 25, "lines": ["LINE 1", "Line 2", "Line 3"]}}
  ],
  "tags":        ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10","tag11","tag12","tag13","tag14","tag15","tag16","tag17","tag18","tag19","tag20","tag21","tag22","tag23","tag24","tag25","tag26","tag27","tag28","tag29","tag30"],
  "description": "...",
  "pexels_query":"..."
}}"""


def _call_claude(prompt: str) -> dict:
    msg = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
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
    if "title_options" in data:
        opts = data["title_options"]
        print(f"  Title options generated: {len(opts)}")
        for i, o in enumerate(opts, 1):
            print(f"    [{i}] {o.get('title', '')}  [{o.get('trigger', '')}]")
        print(f"  Selected: {data['viral_title']}")
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
