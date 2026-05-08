"""
Gemini-powered English script generator for viral YouTube Shorts.
Optimised for SEO, maximum watch time, and high CTR.
Uses gemini-2.0-flash (free tier: 1,500 requests/day).
"""

import json
import re
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

_client = None
# Try newest model first; fall back if quota exhausted
_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]


def _generate(prompt: str) -> str:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    for model in _MODELS:
        try:
            resp = _client.models.generate_content(model=model, contents=prompt)
            return resp.text
        except Exception as e:
            err = str(e).lower()
            if any(w in err for w in ("quota", "429", "resource_exhausted", "rate limit", "exhausted")):
                continue
            raise
    raise RuntimeError("All Gemini models hit quota. Enable billing at aistudio.google.com")


_SYSTEM = (
    "You are a YouTube Shorts strategist who has grown multiple finance channels to 1M+ subscribers. "
    "You deeply understand YouTube's algorithm: CTR, watch time, comments, and shares. "
    "You write scripts that stop scrollers in the first 3 seconds and hold them for 60 seconds. "
    "You are also an SEO expert who knows exactly which tags and titles rank on YouTube search."
)

_PROMPT = """\
{system}

Create a complete, fully optimised YouTube Short for this finance/crypto news.

NEWS HEADLINE: {title}
NEWS DETAILS: {desc}
CONTENT TYPE: {topic}
CURRENT YEAR: 2026

─── STEP 1: VIRAL ANGLE ───────────────────────────────────────────────
Before writing, identify:
• The most SHOCKING or SURPRISING element of this news (a number, a reversal, an impact on viewer)
• The specific audience this affects (retail investors, crypto holders, job seekers, homeowners)
• The emotion to trigger (fear of missing out, fear of losing money, excitement, urgency)

─── STEP 2: AUDIO SCRIPT (~130 words, spoken English) ─────────────────
Hook (0–8s):
  • Open with a dollar/percentage figure OR a "what if" that affects the viewer directly
  • Use power openers: "Just happened", "Breaking", "Warning", "This changes everything"
  • Address viewer: "If you own stocks...", "Your savings are...", "Every investor needs to..."
  • Max 2 sentences. Must make someone stop mid-scroll.

Body (8–45s):
  • One clear sentence: what happened, who did it, when
  • Two sentences: the cause / context
  • Two sentences: the direct impact on the viewer's money, portfolio, or daily life
  • One sentence: what experts / analysts are saying OR what happens next
  • Use short sentences. Max 15 words each. No jargon without explanation.

CTA (45–60s):
  • "Are you bullish or bearish on this? Comment below right now."
  • "Subscribe — we post daily finance and crypto alerts you won't find elsewhere."
  • "Like this video so more people see it."

─── STEP 3: VIRAL TITLE (for YouTube, max 80 chars) ───────────────────
Formula options (pick the highest CTR one for this story):
  A. [Company/Topic] [±X%] — [Shocking Question or Consequence]?
  B. BREAKING: [What Happened] — Here's How It Affects Your Money
  C. $[Amount] [CRASHED/SURGED] — [Viewer Impact in 5 Words]
  D. [Number] [Power Word]: [Topic] Just [Action] [Year]

Rules:
  • Put the most important keyword first
  • Include a specific number if possible
  • Max 80 chars. Target 60–70 for full display on mobile.
  • Do NOT use clickbait that misrepresents the story.

─── STEP 4: ON-SCREEN DISPLAY SECTIONS (4 sections) ──────────────────
Each section is shown on screen while the audio plays.
  • image_type: "breaking" (hook) | "company" (main fact) | "market" (impact/data) | "cta" (subscribe)
  • time_weight: word count in that audio section (all 4 must sum to ~130)
  • lines: exactly 3 lines. Max 32 chars each. Punchy. Numbers. ALL CAPS key words.
  • Make them scannable at a glance — someone reading silently must get the story.

─── STEP 5: SEO TAGS (exactly 25 tags) ────────────────────────────────
Distribute across these categories:
  • 5 broad evergreen: "stock market", "investing", "finance news", "how to invest", "make money"
  • 5 trending/timely: include specific companies, events, current year "2026"
  • 5 topic-specific: sector (crypto, banking, tech), asset type, event type
  • 5 question-based (how people search): "is bitcoin a good investment", "should I buy [X] stock"
  • 5 shorts-optimised: "finance shorts", "investing shorts", "money shorts", "financial news shorts", "stock market shorts"

─── STEP 6: YOUTUBE DESCRIPTION (for SEO, ~200 words) ────────────────
  • First 2 lines (150 chars): restate the key fact with the main keyword — this appears in search results
  • Body: 3–4 sentences expanding on the story and viewer impact
  • "Subscribe for daily alerts" + bell icon CTA
  • Hashtags section at end (8 hashtags, most relevant first)

─── STEP 7: PEXELS QUERY ──────────────────────────────────────────────
3–4 words for background image search. Examples:
  • crash story → "stock market crash red"
  • fed/rates → "federal reserve washington"
  • crypto bull → "bitcoin cryptocurrency digital"
  • earnings → "corporate office profit growth"

─── OUTPUT FORMAT ─────────────────────────────────────────────────────
Return ONLY valid JSON. No markdown fences. No explanation outside the JSON.

{{
  "viral_title":    "...",
  "audio_script":   "...",
  "sections": [
    {{"image_type": "breaking", "time_weight": 25, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "company",  "time_weight": 40, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "market",   "time_weight": 40, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "cta",      "time_weight": 25, "lines": ["LINE 1", "Line 2", "Line 3"]}}
  ],
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10",
           "tag11","tag12","tag13","tag14","tag15","tag16","tag17","tag18","tag19","tag20",
           "tag21","tag22","tag23","tag24","tag25"],
  "description":    "...",
  "pexels_query":   "..."
}}"""


def generate_en(title: str, desc: str, topic: str = "finance") -> dict:
    """
    Generate a fully SEO-optimised viral Short script using Gemini 2.0 Flash.

    Returns:
        {viral_title, audio_script, sections, tags, description, pexels_query}
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    prompt = _PROMPT.format(
        system=_SYSTEM,
        title=title,
        desc=(desc or "")[:500],
        topic=topic,
    )

    raw  = _generate(prompt).strip()
    raw  = re.sub(r"^```(?:json)?\s*", "", raw)
    raw  = re.sub(r"\s*```$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gemini returned invalid JSON: {e}\n\nRaw:\n{raw[:500]}")

    for key in ("viral_title", "audio_script", "sections", "tags", "description", "pexels_query"):
        if key not in data:
            raise RuntimeError(f"Missing key '{key}' in Gemini response.")

    return data


if __name__ == "__main__":
    result = generate_en(
        title="Federal Reserve Cuts Rates by 0.5% — Biggest Cut in 4 Years",
        desc="The Fed surprised markets with a 50 basis point cut, citing cooling inflation.",
        topic="finance",
    )
    print(json.dumps(result, indent=2))
