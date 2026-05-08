"""
Main pipeline — run this every day to produce 3 YouTube Shorts.

Usage:
    python run_pipeline.py

Output:
    C:\\Users\\user\\Desktop\\YTShorts\\output\\
        video_1_<slug>.mp4
        video_2_<slug>.mp4
        video_3_<slug>.mp4
"""

import os, re, sys, time
from datetime import datetime

from config       import OUTPUT_DIR, CACHE_DIR
from news_fetcher import get_top_stories, fetch_section_images
from script_gen   import generate_script, make_timed_segments
from audio_gen    import generate_audio, get_best_voice
from video_gen    import create_video

def slugify(text, max_len=30):
    s = re.sub(r"[^\w\s]", "", text.lower())
    s = re.sub(r"\s+", "_", s)
    return s[:max_len]

def run():
    print("=" * 60)
    print("  YOUTUBE SHORTS PIPELINE — INDIA NEWS")
    print(f"  {datetime.now().strftime('%d %b %Y  %H:%M')}")
    print("=" * 60)

    # ── 1. Fetch top 3 stories ───────────────────────────────────────────
    print("\n[1/4] Fetching top trending Indian news...")
    stories = get_top_stories(n=3)

    if not stories:
        print("ERROR: No stories fetched. Check your internet connection.")
        sys.exit(1)

    print(f"\nSelected {len(stories)} stories:")
    for i, s in enumerate(stories, 1):
        print(f"  {i}. {s['title'][:70]}")

    # ── 2. Get voice once (shared across all 3 videos) ──────────────────
    print("\n[2/4] Selecting ElevenLabs voice...")
    voice_id = get_best_voice()

    results = []

    # ── 3. Generate each video ───────────────────────────────────────────
    for idx, story in enumerate(stories, 1):
        print(f"\n{'─'*60}")
        print(f"VIDEO {idx}/3 — {story['title'][:60]}")
        print(f"{'─'*60}")

        slug = slugify(story["title"])
        audio_path  = os.path.join(CACHE_DIR,  f"audio_{idx}_{slug}.mp3")
        output_path = os.path.join(OUTPUT_DIR, f"video_{idx}_{slug}.mp4")

        if os.path.exists(output_path):
            print(f"  Already exists, skipping: {output_path}")
            results.append(output_path)
            continue

        # Script
        print(f"  Generating script...")
        result        = generate_script(story["title"], story["desc"])
        audio_script  = result["audio_script"]
        sections      = result["sections"]
        company_query = result["company_query"]
        print(f"  Audio script: {audio_script[:70]}...")
        print(f"  Sections: {len(sections)} | scenario: {result['scenario']}")

        # Section-specific background images
        section_images = fetch_section_images(company_query, seed=idx - 1)

        # Audio — Hindi Devanagari for proper ElevenLabs pronunciation
        print(f"  Generating ElevenLabs audio...")
        try:
            generate_audio(audio_script, audio_path, voice_id)
        except Exception as e:
            print(f"  AUDIO ERROR: {e}")
            continue

        # Timed segments mapped to audio duration
        from moviepy import AudioFileClip
        dur      = AudioFileClip(audio_path).duration
        segments = make_timed_segments(sections, dur)

        # Video
        print(f"  Creating video...")
        try:
            create_video(story, audio_script, segments, audio_path, output_path,
                         section_images=section_images)
            results.append(output_path)
        except Exception as e:
            print(f"  VIDEO ERROR: {e}")
            import traceback; traceback.print_exc()

    # ── 4. Summary ────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  DONE — {len(results)}/3 videos created")
    print(f"{'='*60}")
    for i, path in enumerate(results, 1):
        size = os.path.getsize(path) / (1024*1024) if os.path.exists(path) else 0
        print(f"  {i}. {os.path.basename(path)}  ({size:.1f} MB)")
    print(f"\n  Output folder: {OUTPUT_DIR}")

if __name__ == "__main__":
    run()
