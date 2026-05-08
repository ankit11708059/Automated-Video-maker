# YTShorts — YouTube Shorts Automation Pipeline

## What this project does
Generates YouTube Shorts (1080×1920, 60s) on Indian stock market news.
Each video: ElevenLabs Hindi/Hinglish voiceover + Pexels background images (one per section) + animated news graphics.

## Run the daily pipeline (3 videos from live news)
```
py run_pipeline.py
```
Output: `output/video_1_*.mp4`, `video_2_*.mp4`, `video_3_*.mp4`

---

## When the user provides a custom script

**This is the most common task. Follow this exact pattern:**

### Step 1 — Read the script
The user will give you a script like:
```
Hook (0-5s): "Ek important update..."
Section 1 (5-20s): "Company ne..."
Section 2 (20-35s): "Stock aaj..."
Section 3 (35-50s): "Long-term..."
CTA (50-60s): "Subscribe karo..."
```

### Step 2 — Edit `make_video.py` (single generic file for all stocks)

**NEVER create topic-specific files like `make_tata_video.py`. Always edit `make_video.py`.**

Key things to set:
```python
TOPIC_SLUG    = "tata_motors"   # → cache/tata_motors_audio.mp3, output/tata_motors_short.mp4
COMPANY_QUERY = "automobile india tata motors car"  # Pexels image search

STORY = {
    "title": "<news headline>",
    "src":   "ET Markets",
}

AUDIO_SCRIPT = (
    # Paste the EXACT user script here as one string.
    "Hook text. "
    "Section 1 text. "
    "Section 2 text. "
    "Section 3 text. "
    "CTA text."
)

SECTIONS = [
    # One entry per spoken section.
    # time_weight = approximate word count in that audio section.
    # image_type choices: "breaking", "company", "market", "cta"
    {"image_type": "breaking", "time_weight": 26, "lines": [
        "Line 1 shown on screen",
        "Line 2 shown on screen",
        "Line 3 shown on screen",
    ]},
    {"image_type": "company",  "time_weight": 47, "lines": [...]},
    {"image_type": "market",   "time_weight": 53, "lines": [...]},
    {"image_type": "market",   "time_weight": 62, "lines": [...]},
    {"image_type": "cta",      "time_weight": 48, "lines": [...]},
]
```

**time_weight = count the words in that section of AUDIO_SCRIPT.**
Example: "Tata Motors ne prices badhaye hain 1.5 percent tak" = 10 words → time_weight=10.

**COMPANY_QUERY guide:**
- Auto/EV stocks → `"automobile india tata motors car"`
- IT/Software   → `"india software technology coding"`
- Banking       → `"india bank finance money"`
- Energy/Oil    → `"india energy oil power"`
- Pharma        → `"india pharmaceutical medicine"`
- Generic       → `"india business corporate office"`

### Step 3 — Run it
```
py make_video.py
```
The video will be exactly **60 seconds** (audio is automatically sped up to fit).
Audio is **cached** — re-running skips ElevenLabs and uses the cached file.
To regenerate audio, delete `cache/<topic>_audio.mp3`.

---

## File map

| File | Purpose |
|------|---------|
| `run_pipeline.py` | Daily pipeline — fetches top 3 news, makes 3 videos |
| `make_video.py` | Generic script for all user-provided custom videos |
| `script_gen.py` | Auto-generates scripts from news headlines (used by pipeline) |
| `news_fetcher.py` | Fetches RSS + scrapes ET Markets / Moneycontrol |
| `audio_gen.py` | ElevenLabs TTS — tries Aryaveer first, falls back to Daniel |
| `video_gen.py` | Renders video — Ken Burns BG, crossfade between sections, news graphics |
| `config.py` | API keys, paths, video dimensions |

---

## API subscriptions

| Service | Free tier | What you need for production |
|---------|-----------|------------------------------|
| **ElevenLabs** | 10,000 chars/month, Western voices only | **Creator $22/mo** — unlocks Aryaveer (Indian), 100k chars/month |
| **Pexels** | Unlimited | Free forever |

**Without Creator plan:** Falls back to Daniel (British voice). Video is still 60s but sounds Western.  
**With Creator plan:** Aryaveer is selected automatically — sounds Indian, naturally faster speech.

---

## Common issues

**"quota_exceeded" from ElevenLabs**
→ Free tier (10k chars/month) is used up. Upgrade to Creator or wait for monthly reset.
→ Cached audio in `cache/` is reused automatically — delete the .mp3 to force regeneration.

**"paid_plan_required" for Aryaveer/Yatin**
→ These are library voices, need Creator plan. Code auto-falls back to Daniel.

**Video is longer than 60s**
→ `target_duration=60` in `create_video()` handles this via ffmpeg speed-up.
→ Speed factor > 2.0 is handled by chaining two atempo filters.

**Text shows as boxes (□□□□)**
→ PIL can't render Devanagari. All video text must be in Hinglish (Roman script).
→ Audio script can still be Hindi Devanagari — ElevenLabs handles it fine.

**No stories fetched**
→ Check internet. RSS feeds sometimes timeout — re-run.

---

## Image types for sections

| image_type | Pexels query used | When to use |
|------------|------------------|-------------|
| `breaking` | India stock market red decline | Hook / dramatic opening |
| `company`  | User-specified company query | Company-specific news section |
| `market`   | India stock exchange trading | Market data / numbers section |
| `cta`      | India investment growth profit | Long-term / subscribe section |
