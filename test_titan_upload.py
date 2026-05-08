"""
Test run: Titan stock Short — fetch, generate, render, upload.
Run: py test_titan_upload.py
Shows rendered video path before uploading. Press Enter to confirm upload.
"""
import os, sys
sys.path.insert(0, ".")

from moviepy import AudioFileClip
from config        import OUTPUT_DIR, CACHE_DIR
from news_fetcher  import get_top_stories, fetch_section_images
from script_gen    import generate_script, make_timed_segments
from audio_gen     import generate_audio, get_best_voice
from video_gen     import create_video
from yt_upload     import upload_video

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR,  exist_ok=True)

# ── SEO tags (Gemini-optimised, manually curated) ─────────────────────────────
TAGS = [
    # High volume broad
    "stock market today", "share market today", "indian stock market",
    "best stocks to buy", "investing india",
    # Stock specific
    "titan share price", "titan share price today", "titan q4 results 2026",
    "titan company stock", "titan stock analysis",
    # Trending now
    "titan 52 week high", "stocks hitting 52 week high", "best performing stocks may 2026",
    "titan pat growth", "titan share surge today",
    # Sector / theme
    "jewellery stocks india", "tata group stocks", "nifty 50 stocks today",
    "large cap stocks india", "consumer stocks india",
    # Question based
    "should i buy titan stock", "is titan a good investment 2026",
    "titan share target price 2026", "titan stock buy or sell",
    "best jewellery stocks to buy",
    # Hindi search terms
    "titan share aaj", "share market aaj ka", "kaunsa stock kharide aaj",
    "share market news hindi", "titan share price hindi",
    # Shorts optimised
    "stock market shorts", "finance shorts hindi", "share market shorts",
    "investing shorts india", "money shorts hindi",
]

YT_TITLE = "Titan Stock UP 7% \U0001f680 52-Week HIGH! Q4 Results Dhamaka | Buy, Sell or Hold?"

AUDIO_PATH  = os.path.join(CACHE_DIR,  "titan_test_audio.mp3")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "titan_test_short.mp4")

def main():
    print("=" * 60)
    print("  TITAN STOCK SHORT — TEST RUN")
    print("=" * 60)

    # 1. Fetch story
    print("\n[1/5] Fetching top Indian stock story...")
    stories = get_top_stories(n=5)
    story   = next((s for s in stories if "titan" in s["title"].lower()), stories[0])
    print(f"  Story  : {story['title'][:70]}")
    print(f"  Source : {story['src']}")

    # 2. Generate Hindi script
    print("\n[2/5] Generating Hindi script...")
    script = generate_script(story["title"], story.get("desc", ""))
    print(f"  Scenario : {script['scenario']}")
    print(f"\n  AUDIO SCRIPT:\n  {script['audio_script'][:200]}...")
    print(f"\n  SECTIONS:")
    for sec in script["sections"]:
        print(f"    [{sec['image_type']}] {' / '.join(sec['lines'])}")

    # 3. Fetch background images
    print("\n[3/5] Fetching Pexels images...")
    section_images = fetch_section_images("titan jewellery india luxury retail", seed=0)

    # 4. Generate audio
    print("\n[4/5] Generating audio (ElevenLabs)...")
    if os.path.exists(AUDIO_PATH):
        print(f"  Cached: {os.path.getsize(AUDIO_PATH)//1024} KB")
    else:
        voice_id = get_best_voice()
        generate_audio(script["audio_script"], AUDIO_PATH, voice_id)

    dur = AudioFileClip(AUDIO_PATH).duration
    print(f"  Duration: {dur:.1f}s")

    # 5. Render video
    print("\n[5/5] Rendering video...")
    segments = make_timed_segments(script["sections"], dur)

    if os.path.exists(OUTPUT_PATH) and os.path.getsize(OUTPUT_PATH) > 1_000_000:
        print(f"  Using existing render: {os.path.getsize(OUTPUT_PATH) // 1024 // 1024} MB")
    else:
        story_meta = {"title": YT_TITLE, "src": story["src"]}
        create_video(story_meta, script["audio_script"], segments,
                     AUDIO_PATH, OUTPUT_PATH,
                     section_images=section_images, target_duration=60)

    size_mb = os.path.getsize(OUTPUT_PATH) / 1024 / 1024
    print(f"\n  Video ready: {OUTPUT_PATH}  ({size_mb:.1f} MB)")

    # ── Confirm before uploading ──────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  READY TO UPLOAD")
    print(f"  Title : {YT_TITLE}")
    print(f"  Tags  : {len(TAGS)} tags")
    print(f"{'='*60}")
    confirm = input("\n  Upload to YouTube now? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("  Upload cancelled. Video saved at:", OUTPUT_PATH)
        return

    print("\n  Uploading...")
    url = upload_video(OUTPUT_PATH, YT_TITLE, story.get("desc", story["title"]), TAGS)
    print(f"\n  LIVE: {url}")

if __name__ == "__main__":
    main()
