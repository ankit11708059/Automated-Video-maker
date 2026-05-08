"""
Generic stock video maker — edit the section below, then: py make_video.py
"""

import os, sys
from moviepy import AudioFileClip

from config       import OUTPUT_DIR, CACHE_DIR
from news_fetcher import fetch_section_images
from script_gen   import make_timed_segments
from audio_gen    import generate_audio, get_best_voice
from video_gen    import create_video

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR,  exist_ok=True)

# ── EDIT EVERYTHING BELOW THIS LINE ──────────────────────────────────────────

TOPIC_SLUG    = "stock"          # used for cache/output filenames, e.g. "tata_motors"
COMPANY_QUERY = "india stock market business corporate"  # Pexels image search

STORY = {
    "title": "Stock Update",     # news headline shown at top of video
    "src":   "ET Markets",
}

AUDIO_SCRIPT = (
    "Hook text here. "
    "Section 1 text here. "
    "Section 2 text here. "
    "Section 3 text here. "
    "CTA text here."
)

# One entry per spoken section.
# time_weight = approximate word count of that section in AUDIO_SCRIPT.
# image_type choices: "breaking", "company", "market", "cta"
SECTIONS = [
    {
        "image_type":  "breaking",
        "time_weight": 20,
        "lines": [
            "Stock — IMPORTANT UPDATE!",
            "Yeh Video End Tak Zaroor Dekho!",
        ],
    },
    {
        "image_type":  "company",
        "time_weight": 40,
        "lines": [
            "Key fact line 1",
            "Key fact line 2",
            "Key fact line 3",
        ],
    },
    {
        "image_type":  "market",
        "time_weight": 40,
        "lines": [
            "Market data line 1",
            "Market data line 2",
            "Market data line 3",
        ],
    },
    {
        "image_type":  "market",
        "time_weight": 40,
        "lines": [
            "Analysis line 1",
            "Analysis line 2",
            "Analysis line 3",
        ],
    },
    {
        "image_type":  "cta",
        "time_weight": 20,
        "lines": [
            "Bullish Ya Bearish? Comment Karo!",
            "Subscribe — Daily Stock Updates!",
            "LIKE  |  SHARE  |  SUBSCRIBE",
        ],
    },
]

# ── DO NOT EDIT BELOW THIS LINE ───────────────────────────────────────────────

AUDIO_PATH  = os.path.join(CACHE_DIR,  f"{TOPIC_SLUG}_audio.mp3")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"{TOPIC_SLUG}_short.mp4")


def main():
    print("=" * 60)
    print(f"  {TOPIC_SLUG.upper().replace('_', ' ')} — YOUTUBE SHORT")
    print("=" * 60)

    if os.path.exists(OUTPUT_PATH):
        os.remove(OUTPUT_PATH)
        print("  Removed old video — regenerating fresh.")

    print("\n[1/4] Fetching section images from Pexels...")
    section_images = fetch_section_images(COMPANY_QUERY, seed=0)

    print("\n[2/4] Audio...")
    if os.path.exists(AUDIO_PATH):
        print(f"  Cached: {os.path.getsize(AUDIO_PATH) // 1024} KB  ->  {AUDIO_PATH}")
    else:
        print("  Generating ElevenLabs audio...")
        voice_id = get_best_voice()
        try:
            generate_audio(AUDIO_SCRIPT, AUDIO_PATH, voice_id)
        except Exception as e:
            print(f"  AUDIO ERROR: {e}")
            sys.exit(1)

    dur = AudioFileClip(AUDIO_PATH).duration
    print(f"  Duration: {dur:.1f}s")

    segments = make_timed_segments(SECTIONS, dur)
    print(f"\n[3/4] Segments:")
    for seg in segments:
        txt = seg['text'].encode('ascii', 'replace').decode()
        print(f"  [{seg['image_type']:8s}] {seg['start']:5.1f}s-{seg['end']:5.1f}s  \"{txt}\"")

    print("\n[4/4] Rendering video...")
    try:
        create_video(STORY, AUDIO_SCRIPT, segments, AUDIO_PATH, OUTPUT_PATH,
                     section_images=section_images, target_duration=60)
    except Exception as e:
        print(f"  VIDEO ERROR: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    fit_path = AUDIO_PATH.replace(".mp3", "_fit.mp3")
    final_dur = AudioFileClip(fit_path).duration if os.path.exists(fit_path) else dur
    size_mb = os.path.getsize(OUTPUT_PATH) / 1024 / 1024
    print(f"\n{'='*60}")
    print(f"  DONE  ->  {OUTPUT_PATH}")
    print(f"  Size  : {size_mb:.1f} MB")
    print(f"  Time  : {final_dur:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
