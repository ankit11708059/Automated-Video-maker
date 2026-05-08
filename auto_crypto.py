"""
Crypto pipeline — runs every 6 hours via GitHub Actions.
Fetches top crypto story, generates Hindi video, uploads to YouTube.
"""

import os, sys, json, base64, re
from datetime import datetime, timezone
from moviepy import AudioFileClip

from config        import OUTPUT_DIR, CACHE_DIR
from news_sources  import get_crypto_stories
from script_gen_hi import generate_hindi_crypto
from news_fetcher  import fetch_section_images
from script_gen    import make_timed_segments
from audio_gen     import generate_audio, get_best_voice
from video_gen     import create_video
from yt_upload     import upload_video

LOG_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crypto_log.json")
TOKEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_token.pickle")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR,  exist_ok=True)


def _load_log() -> set:
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            return {e["url"] for e in json.load(f)}
    return set()


def _save_log(entry: dict):
    entries = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            entries = json.load(f)
    entries.append(entry)
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2, default=str)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_-]+", "_", slug).strip("_")[:40]


def _decode_token():
    token_b64 = os.getenv("YOUTUBE_TOKEN")
    if token_b64 and not os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "wb") as f:
            f.write(base64.b64decode(token_b64))
        print("  Token decoded from env var.")


def main():
    print("=" * 60)
    print("  CRYPTO — HINDI AUTO PIPELINE")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    _decode_token()

    uploaded_urls = _load_log()
    print(f"\n  Already uploaded: {len(uploaded_urls)} stories")

    print("\n[1] Fetching top crypto stories...")
    stories = get_crypto_stories(n=15)
    fresh   = [s for s in stories if s["url"] not in uploaded_urls]

    if not fresh:
        print("  No new stories — all top stories already uploaded. Skipping.")
        return

    story = fresh[0]
    print(f"  Selected : [{story['score']:.0f}] {story['title'][:70]}")
    print(f"  Source   : {story['src']}")

    print("\n[2] Generating Hindi crypto script + SEO via Claude Sonnet...")
    try:
        script = generate_hindi_crypto(story["title"], story.get("desc", ""))
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    print(f"  Title    : {script['viral_title']}")
    print(f"  Tags     : {len(script['tags'])} tags")
    print(f"  Query    : {script['pexels_query']}")

    slug        = _slugify(story["title"])
    audio_path  = os.path.join(CACHE_DIR,  f"crypto_{slug}_audio.mp3")
    output_path = os.path.join(OUTPUT_DIR, f"crypto_{slug}_short.mp4")

    print("\n[3] Fetching Pexels background images...")
    section_images = fetch_section_images(script["pexels_query"], seed=0)

    print("\n[4] Generating audio (ElevenLabs — Hindi voice)...")
    if os.path.exists(audio_path):
        print(f"  Cached: {os.path.getsize(audio_path) // 1024} KB")
    else:
        voice_id = get_best_voice()
        try:
            generate_audio(script["audio_script"], audio_path, voice_id)
        except Exception as e:
            print(f"  AUDIO ERROR: {e}")
            sys.exit(1)

    dur = AudioFileClip(audio_path).duration
    print(f"  Duration: {dur:.1f}s")

    print("\n[5] Rendering video (multiprocessing + ffmpeg)...")
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1_000_000:
        print(f"  Using existing: {os.path.getsize(output_path)//1024//1024} MB")
    else:
        segments   = make_timed_segments(script["sections"], dur)
        story_meta = {"title": script["viral_title"], "src": story["src"]}
        try:
            create_video(story_meta, script["audio_script"], segments,
                         audio_path, output_path,
                         section_images=section_images, target_duration=60)
        except Exception as e:
            print(f"  VIDEO ERROR: {e}")
            import traceback; traceback.print_exc()
            sys.exit(1)

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"  Size: {size_mb:.1f} MB")

    print("\n[6] Uploading to YouTube...")
    try:
        yt_url = upload_video(output_path, script["viral_title"],
                              script["description"], script["tags"])
    except Exception as e:
        print(f"  UPLOAD ERROR: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    _save_log({
        "url":         story["url"],
        "title":       story["title"],
        "yt_url":      yt_url,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    })

    print(f"\n{'='*60}")
    print(f"  DONE  ->  {yt_url}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
