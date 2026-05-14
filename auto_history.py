"""
Lost History & Forgotten Mysteries pipeline.
Runs every 1.5 hours via GitHub Actions. Each run produces a fresh, non-duplicate
mystery Short in English (world-wide topic coverage, randomised visual style),
uploads to YouTube + Instagram.
"""

import os, sys, json, base64, re
from datetime import datetime, timezone
from moviepy import AudioFileClip

from config              import OUTPUT_DIR, CACHE_DIR
from history_visuals     import fetch_history_images
from script_gen_history  import generate_history_short
from audio_gen           import generate_audio, get_best_voice
from video_gen_history   import create_video, sections_to_segments
from yt_upload_history   import upload_video
from ig_upload           import upload_reel

LOG_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history_log.json")
TOKEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history_token.pickle")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR,  exist_ok=True)


def _load_log() -> list[dict]:
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            return json.load(f)
    return []


def _save_log(entry: dict):
    entries = _load_log()
    entries.append(entry)
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2, default=str)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_-]+", "_", slug).strip("_")[:40]


def _decode_token():
    token_b64 = os.getenv("HISTORY_YT_TOKEN")
    if token_b64 and not os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "wb") as f:
            f.write(base64.b64decode(token_b64))
        print("  History YouTube token decoded from env var.")


def _used_image_urls(log: list[dict]) -> set:
    """Collect all photo URLs used in prior videos to avoid reuse."""
    used = set()
    for entry in log:
        for u in entry.get("image_urls", []) or []:
            used.add(u)
    return used


def main():
    print("=" * 60)
    print("  LOST HISTORY & FORGOTTEN MYSTERIES — AUTO PIPELINE")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    _decode_token()

    log = _load_log()
    past_topics     = [e["topic_name"] for e in log if e.get("topic_name")]
    past_regions    = [e["region"]     for e in log if e.get("region")]
    past_categories = [e["category"]   for e in log if e.get("category")]
    used_urls       = _used_image_urls(log)
    print(f"\n  Past topics: {len(past_topics)} | regions: {len(past_regions)} | categories: {len(past_categories)}")
    print(f"  Used image URLs (dedup pool): {len(used_urls)}")

    print("\n[1] Generating fresh mystery via Claude Sonnet...")
    try:
        script = generate_history_short(
            past_topics=past_topics,
            past_regions=past_regions,
            past_categories=past_categories,
        )
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    topic = script["topic_name"]
    if topic.lower() in (t.lower() for t in past_topics):
        print(f"  WARNING: duplicate topic '{topic}' — retrying once...")
        script = generate_history_short(
            past_topics=past_topics + [topic],
            past_regions=past_regions,
            past_categories=past_categories,
        )
        topic = script["topic_name"]

    print(f"  Topic    : {topic}")
    print(f"  Title    : {script['viral_title']}")
    print(f"  Region/Cat: {script.get('region')} / {script.get('category')}")

    slug        = _slugify(topic)
    audio_path  = os.path.join(CACHE_DIR,  f"history_{slug}_audio.mp3")
    output_path = os.path.join(OUTPUT_DIR, f"history_{slug}_short.mp4")

    print("\n[2] Fetching atmospheric background images (content-matched, dedup'd)...")
    section_images, picked_urls = fetch_history_images(
        section_queries=script.get("section_queries", []),
        themes=script.get("themes"),
        exclude_urls=used_urls,
    )

    print("\n[3] Generating English narration (ElevenLabs)...")
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

    print("\n[4] Rendering video (cinematic, randomised style)...")
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1_000_000:
        print(f"  Using existing: {os.path.getsize(output_path)//1024//1024} MB")
    else:
        segments   = sections_to_segments(script["sections"], dur)
        story_meta = {"title": script["viral_title"], "src": "Lost History"}
        try:
            create_video(story_meta, script["audio_script"], segments,
                         audio_path, output_path,
                         section_images=section_images,
                         visual_style=script.get("visual_style"),
                         topic_seed=topic)
        except Exception as e:
            print(f"  VIDEO ERROR: {e}")
            import traceback; traceback.print_exc()
            sys.exit(1)

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"  Size: {size_mb:.1f} MB")

    print("\n[5] Uploading to YouTube...")
    try:
        yt_url = upload_video(output_path, script["viral_title"],
                              script["description"], script["tags"])
    except Exception as e:
        print(f"  UPLOAD ERROR: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    print("\n[6] Uploading to Instagram...")
    ig_caption = (
        f"{script['viral_title']}\n\n"
        "#losthistory #ancientmysteries #unsolvedmysteries #history "
        "#mystery #ancientcivilizations #forgottenhistory #archaeology "
        "#historyfacts #weirdhistory #conspiracy #shorts #reels "
        "#historytok #ancientsecrets"
    )
    try:
        ig_url = upload_reel(output_path, ig_caption)
    except Exception as e:
        print(f"  IG UPLOAD ERROR: {e}")
        ig_url = None

    _save_log({
        "topic_name":  topic,
        "title":       script["viral_title"],
        "region":      script.get("region"),
        "category":    script.get("category"),
        "visual_style": script.get("visual_style"),
        "image_urls":  picked_urls,
        "yt_url":      yt_url,
        "ig_url":      ig_url,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    })

    print(f"\n{'='*60}")
    print(f"  YouTube   ->  {yt_url}")
    if ig_url:
        print(f"  Instagram ->  {ig_url}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
