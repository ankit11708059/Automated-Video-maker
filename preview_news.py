"""Run: py preview_news.py — fetches top Indian stock story and shows script."""
import sys
sys.path.insert(0, ".")

from news_fetcher import get_top_stories
from script_gen   import generate_script

stories = get_top_stories(n=5)
story   = stories[0]

print("=" * 60)
print("  TOP STORY")
print("=" * 60)
print(f"  Title  : {story['title']}")
print(f"  Source : {story['src']}")
print(f"  Score  : {story['score']}")
print(f"  URL    : {story['url']}")
print()

script = generate_script(story["title"], story.get("desc", ""))

print("=" * 60)
print("  AUDIO SCRIPT (Hindi — spoken by ElevenLabs)")
print("=" * 60)
print(script["audio_script"])
print()
print("=" * 60)
print("  DISPLAY SECTIONS (shown on screen)")
print("=" * 60)
for i, sec in enumerate(script["sections"], 1):
    print(f"  Section {i} [{sec['image_type']}]:")
    for line in sec["lines"]:
        print(f"    {line}")
    print()
print("=" * 60)
print("  Pexels query :", script["company_query"])
print("  Scenario     :", script["scenario"])
print("=" * 60)
