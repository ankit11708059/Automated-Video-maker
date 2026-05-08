"""Run: py gen_tags.py — generates SEO tags for the current story via Gemini."""
import json, re, sys
sys.path.insert(0, ".")
from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)
_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]

def _call(prompt):
    for m in _MODELS:
        try:
            return client.models.generate_content(model=m, contents=prompt).text
        except Exception as e:
            err = str(e).lower()
            if any(w in err for w in ("quota", "429", "resource_exhausted", "rate limit", "exhausted")):
                print(f"  [{m}] quota hit, trying next...")
                continue
            raise
    raise RuntimeError("All Gemini models hit quota. Enable billing at aistudio.google.com")

STORY_TITLE = "Titan shares surge 7%, hit fresh 52-week high on 35% YoY PAT growth, 46% income surge"
STORY_DESC  = "Titan Company stock hit a fresh 52-week high after Q4 results showed 35% YoY PAT growth and 46% income surge. Jewellery segment drove growth. Stock rally on strong fundamentals."
LANGUAGE    = "Hindi (video is in Hindi for Indian audience)"

prompt = f"""
You are a YouTube SEO expert specialising in Indian finance content.
Generate the maximum-reach tag set for this YouTube Short.

Video details:
- Title: {STORY_TITLE}
- Description: {STORY_DESC}
- Language: {LANGUAGE}
- Format: YouTube Shorts (#shorts)
- Channel niche: Indian stock market, finance news

Generate EXACTLY 35 tags across these 7 categories (5 each):

1. HIGH VOLUME BROAD — terms millions search monthly
   (e.g. "stock market", "share market", "investing india")

2. STOCK SPECIFIC — Titan Company related searches
   (e.g. "titan share price", "titan q4 results")

3. TRENDING RIGHT NOW — what's being searched today
   (include "2026", "may 2026", "today" variants)

4. SECTOR/THEME — jewellery, FMCG, Tata group, large cap
   (e.g. "jewellery stocks india", "tata stocks")

5. QUESTION BASED — exactly how people type in YouTube search
   (e.g. "should i buy titan stock", "is titan a good investment 2026")

6. HINDI SEARCH TERMS — how Hindi speakers search
   (e.g. "titan share aaj", "share market aaj", "kaunsa stock kharide")

7. SHORTS OPTIMISED — shorts discovery tags
   (e.g. "stock market shorts", "finance shorts hindi", "share market shorts")

Rules:
- Each tag: 2–5 words, lowercase, no special characters
- No duplicate concepts
- Prioritise tags with HIGHEST estimated monthly search volume
- Think like someone searching from India on mobile

Return ONLY valid JSON:
{{
  "tags": {{
    "high_volume_broad":   ["tag1","tag2","tag3","tag4","tag5"],
    "stock_specific":      ["tag1","tag2","tag3","tag4","tag5"],
    "trending_now":        ["tag1","tag2","tag3","tag4","tag5"],
    "sector_theme":        ["tag1","tag2","tag3","tag4","tag5"],
    "question_based":      ["tag1","tag2","tag3","tag4","tag5"],
    "hindi_search":        ["tag1","tag2","tag3","tag4","tag5"],
    "shorts_optimised":    ["tag1","tag2","tag3","tag4","tag5"]
  }},
  "recommended_title": "...",
  "recommended_first_hashtag": "#..."
}}
"""

raw = _call(prompt).strip()
raw  = re.sub(r"^```(?:json)?\s*", "", raw)
raw  = re.sub(r"\s*```$", "", raw)
data = json.loads(raw)

tags = data["tags"]
all_tags = []

print("=" * 60)
print("  SEO TAGS — TITAN SHORTS")
print("=" * 60)

for category, tag_list in tags.items():
    label = category.replace("_", " ").upper()
    print(f"\n  [{label}]")
    for t in tag_list:
        print(f"    #{t}")
    all_tags.extend(tag_list)

print(f"\n{'=' * 60}")
print(f"  TOTAL TAGS : {len(all_tags)}")
print(f"  FLAT LIST  : {all_tags}")
print(f"\n  RECOMMENDED TITLE     : {data.get('recommended_title','')}")
print(f"  TOP HASHTAG           : {data.get('recommended_first_hashtag','')}")
print("=" * 60)
