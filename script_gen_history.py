"""
Claude-powered ENGLISH script + SEO generator for the Lost History channel.

Each run produces a fresh mystery (region-balanced, category-balanced),
plus 4 content-matching image search queries (one per section), plus theme
tags for image fallback, and a visual style hint for the renderer.
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


REGIONS = [
    "europe", "north_america", "south_america", "africa", "middle_east",
    "asia_east", "asia_south", "asia_southeast", "oceania",
    "polar_arctic", "polar_antarctic", "underwater", "global",
]

CATEGORIES = [
    "lost_civilization", "vanishing_people", "mysterious_death", "cryptid",
    "conspiracy", "curse", "lost_technology", "unsolved_event",
    "strange_artifact", "haunting", "forbidden_knowledge", "unsolved_crime",
    "supernatural_phenomenon", "lost_expedition",
]

# Theme tags MUST match keys in history_visuals.THEME_POOLS
THEME_TAGS = [
    "ruins_general", "egyptian_desert", "greek_roman", "mesoamerican",
    "asian_ancient", "african", "european_medieval", "european_megalith",
    "underwater_maritime", "polar_arctic", "manuscript_document",
    "artifact_museum", "portrait_historical", "map_exploration",
    "ship_maritime", "aircraft_aviation", "forest_wilderness",
    "cave_underground", "dark_atmospheric", "occult_supernatural",
]

VISUAL_STYLES = ["mystery", "discovery", "supernatural", "conspiracy"]


_SYSTEM = """\
You are THREE elite experts operating as one unified intelligence for the
"Lost History & Forgotten Mysteries" YouTube Shorts channel — covering
forgotten civilizations, unsolved historical events, ancient secrets,
mysterious vanishings, strange deaths, cryptids, curses, conspiracies,
lost expeditions, vanished people, and supernatural phenomena from
ALL CORNERS OF THE WORLD AND ALL OF HUMAN HISTORY.

1. ELITE TITLE STRATEGIST & VIRAL PATTERN FORENSIC ANALYST
   You reverse-engineer top-performing history/mystery Shorts (MrBallen,
   BuzzFeed Unsolved, Bedtime Stories style). For every title: identify
   formula, psychological trigger (curiosity gap / fear / awe / forbidden
   knowledge / authority), and CTR estimate. Generate 3 variants, self-select
   the highest CTR.

2. SCRIPT FORENSIC ANALYST & GHOSTWRITER (history/mystery niche)
   Atmospheric, cinematic English. Short sentences. Dramatic ellipses.
   You write like a forbidden secret whispered to one person — David
   Attenborough meets true-crime narration. Use HOOK → CURIOSITY GAP →
   REVEAL → PATTERN INTERRUPT → CTA. NEVER use "Did you know" or "Imagine if".

3. VISUAL DIRECTOR
   For every video you output 4 SPECIFIC Pexels search queries — one per
   on-screen section — that visually match what is being narrated in that
   exact moment. You also tag 2-3 theme pools for fallback imagery, and
   one overall visual style for the renderer to use."""


_PROMPT = """\
Generate ONE complete, monetization-ready Lost History Short.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI-DUPLICATION — do not repeat any of these topics:
{past_topics}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECENT REGIONS (last 10) — bias AWAY from these for global coverage:
{past_regions}

RECENT CATEGORIES (last 10) — bias AWAY from these for thematic variety:
{past_categories}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOPIC SELECTION RULES:
  • Cover the entire world over time — Europe is overused; favour Africa,
    South America, Asia, Oceania, polar regions, and underwater on most runs.
  • Mix categories aggressively — don't stay in "lost civilization" mode.
    Include vanishing people, mysterious deaths, cryptids, conspiracies,
    curses, haunted places, lost expeditions, strange artifacts, unsolved
    crimes, supernatural phenomena.
  • PEOPLE-CENTRED mysteries are highly engaging: pick eccentric figures,
    unexplained disappearances of individuals, mysterious deaths, alleged
    immortals, doppelgangers, historical madmen, lost royals, time-slip
    cases. Use these often.
  • Specific enough for 60s — one event, not a broad era.
  • Visually illustrable with stock photography of: ruins, manuscripts,
    portraits, ships, aircraft, caves, forests, ice, sea, artifacts.
  • Topic must NOT appear in the anti-dup list.

Variety inspiration (do NOT copy verbatim — generate fresh ideas across):
  Vanishings: Amelia Earhart, Roanoke, Flight 19, USS Cyclops, Antoine de Saint-Exupéry,
    Princes in the Tower, Elisa Lam, the Bermuda Triangle disappearances, Hoer Verde
    village, Ben McDaniel, Jim Sullivan, Lord Lucan, the Sodder Children.
  Strange deaths: Edgar Allan Poe, Mary Reeser, the Dyatlov Pass, Lead Masks Case,
    the Boy in the Box, Tamam Shud, the Isdal Woman, Elisa Lam.
  Cryptids/creatures: Mokele-mbembe, Tasmanian thylacine sightings, Mongolian
    death worm, Almas, Ahool, the Honey Island Swamp Monster, Ningen, Trunko.
  Lost places/civilizations: Rapa Nui collapse, Khmer empire abandonment,
    Cahokia, Catalhoyuk, Mohenjo-daro, Olmec heads, Lost City of Z, La Ciudad Perdida.
  Strange artifacts: Antikythera Mechanism, Voynich Manuscript, Baghdad Battery,
    Aluminium Wedge of Aiud, the Dropa Stones, Coso Artifact, the Saqqara Bird.
  Conspiracies/conspiracies: MKUltra, Operation Highjump, Project Iceworm,
    Tunguska theories, JFK alternative angles, Black Knight Satellite, Phoenix Lights.
  Curses/hauntings: King Tut, Hope Diamond, the Robert Doll, Annabelle origins,
    the Crying Boy paintings, Otzi Iceman curse.
  Lost expeditions: Franklin Expedition, Burke and Wills, the Greely Expedition,
    Mawson's Antarctic survival, the Polish 6th-century migration.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 1 — VIDEO METADATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"topic_name": Clean short name (2-6 words). Used for deduplication.
"region":     One of: {regions_list}
"category":   One of: {categories_list}
"visual_style": One of: {styles_list}
              mystery=cold sepia/blue grade
              discovery=warm gold parchment
              supernatural=purple-blue ethereal
              conspiracy=red-tinted high-contrast

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 2 — AUDIO SCRIPT (English, EXACTLY 95-115 words, ~50s spoken)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL PACING: Aim for ~50s of unhurried, dramatic audio. Use ellipses (...)
for pauses. Short sentences. Trust silence. NEVER "Did you know" / "Imagine if".

HOOK (0-6s, ~12-15 words): Pattern interrupt + curiosity gap with dramatic pause.
CURIOSITY GAP (6-18s, ~20-25 words): Place, date, name; tease strangest detail.
REVEAL + DETAILS (18-38s, ~40-50 words): Mystery delivered, specific number/name,
  one pattern-interrupt line (unexpected contrast or competing theory).
CTA (38-50s, ~20-25 words): Emotional landing, open question, follow ask.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 3 — VIRAL TITLE (3 options, self-select best)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 engineered options (max 80 chars each). Each uses a distinct formula:
  A: [specific number/date] + [mystery] + [cliffhanger]
  B: [forbidden knowledge framing] + [mystery] + [question]
  C: [authority claim] + [shocking detail] + [curiosity gap]
ALL CAPS only one or two words. Pipe character allowed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 4 — ON-SCREEN SECTIONS (4 sections, ASCII English, 3 lines each)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Max 32 chars per line. Include numbers/dates.
time_weight: word count for that section (all 4 must sum to ~105)
image_type: "breaking" (opener) / "company" (subject) / "market" (evidence) / "cta" (atmospheric close)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 5 — IMAGE SEARCH QUERIES (CRITICAL — must match what is narrated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Output a "section_queries" array with EXACTLY 4 Pexels search queries,
in section order [breaking, company, market, cta]. Each query must:
  • Visually match the content being narrated in that section.
  • Be 3-5 words, simple, descriptive, Pexels-friendly.
  • Be DIFFERENT for each section (no near-duplicates).
  • Aim for atmospheric, dramatic, photography terms (not cartoons/illustrations).
  Examples:
    breaking: "antarctic ice expedition dramatic" (for a polar mystery hook)
    company:  "amelia earhart vintage portrait" (for the central figure)
    market:   "old aviation map pacific" (for the evidence section)
    cta:      "lighthouse fog ocean dusk" (for the atmospheric close)

Also output "themes" — 2-3 tags from THIS LIST ONLY (used as fallback if a query fails):
{themes_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 6 — SEO TAGS (exactly 30, ASCII English, max 30 chars each, lowercase)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mix categories, ~5 each:
A. Evergreen: "lost history", "ancient mysteries", "unsolved mysteries", "history shorts", "mystery shorts"
B. Topic specific: mystery name and variants
C. Thematic: "ancient civilizations", "forgotten history", "creepy history"
D. Emotional: "scary history facts", "weird history", "things they dont teach you"
E. Search intent: "what happened to", "real story of"
F. Discovery: "history shorts english", "mystery shorts", "documentary shorts"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 7 — YOUTUBE DESCRIPTION (~200 words, SEO-optimised)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
First line (150 chars max): mystery name + central question.
Body: 3-4 sentences with natural keywords (ancient mysteries, lost history, unsolved).
End: Subscribe + bell + comment prompt.
Last line hashtags: #LostHistory #Mystery #AncientMysteries #Shorts + 4 specific.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 8 — LEGACY PEXELS QUERY (kept for compatibility; use the FIRST section_query)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT — VALID JSON ONLY, no markdown:
{{
  "topic_name":   "...",
  "region":       "one of regions list",
  "category":     "one of categories list",
  "visual_style": "one of styles list",
  "audio_script": "...",
  "title_options": [
    {{"title": "...", "formula": "A", "trigger": "curiosity gap"}},
    {{"title": "...", "formula": "B", "trigger": "forbidden knowledge"}},
    {{"title": "...", "formula": "C", "trigger": "authority + awe"}}
  ],
  "viral_title":  "...",
  "sections": [
    {{"image_type": "breaking", "time_weight": 14, "lines": ["LINE 1","Line 2","Line 3"]}},
    {{"image_type": "company",  "time_weight": 25, "lines": ["LINE 1","Line 2","Line 3"]}},
    {{"image_type": "market",   "time_weight": 45, "lines": ["LINE 1","Line 2","Line 3"]}},
    {{"image_type": "cta",      "time_weight": 22, "lines": ["LINE 1","Line 2","Line 3"]}}
  ],
  "section_queries": ["query1","query2","query3","query4"],
  "themes":          ["theme_tag_1","theme_tag_2","theme_tag_3"],
  "tags":            ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10","tag11","tag12","tag13","tag14","tag15","tag16","tag17","tag18","tag19","tag20","tag21","tag22","tag23","tag24","tag25","tag26","tag27","tag28","tag29","tag30"],
  "description":     "...",
  "pexels_query":    "..."
}}"""


def _call_claude(prompt: str) -> dict:
    msg = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
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

    required = ("topic_name", "audio_script", "viral_title", "sections",
                "tags", "description", "section_queries")
    for key in required:
        if key not in data:
            raise RuntimeError(f"Missing key '{key}' in Claude response.")

    # Defaults for newer fields (graceful if Claude omits)
    data.setdefault("region", "global")
    data.setdefault("category", "unsolved_event")
    data.setdefault("visual_style", "mystery")
    data.setdefault("themes", ["ruins_general", "dark_atmospheric"])
    data.setdefault("pexels_query", data["section_queries"][0])

    print(f"  Region: {data['region']}  Category: {data['category']}  Style: {data['visual_style']}")
    print(f"  Section queries:")
    for i, q in enumerate(data["section_queries"][:4]):
        print(f"    [{i}] {q}")
    print(f"  Themes: {data['themes']}")
    if "title_options" in data:
        print(f"  Title options:")
        for i, o in enumerate(data["title_options"], 1):
            print(f"    [{i}] {o.get('title', '')}  [{o.get('trigger', '')}]")
        print(f"  Selected: {data['viral_title']}")
    return data


def generate_history_short(past_topics: list[str],
                            past_regions: list[str] | None = None,
                            past_categories: list[str] | None = None) -> dict:
    """
    Generate a fresh mystery, biased to underrepresented regions and categories.
    """
    topics_str = ("\n".join(f"  - {t}" for t in past_topics[-200:])
                  if past_topics else "  (none yet)")
    regions_str = ("\n".join(f"  - {r}" for r in (past_regions or [])[-10:])
                   if past_regions else "  (none yet)")
    cats_str = ("\n".join(f"  - {c}" for c in (past_categories or [])[-10:])
                if past_categories else "  (none yet)")

    return _call_claude(_PROMPT.format(
        past_topics=topics_str,
        past_regions=regions_str,
        past_categories=cats_str,
        regions_list=", ".join(REGIONS),
        categories_list=", ".join(CATEGORIES),
        styles_list=", ".join(VISUAL_STYLES),
        themes_list=", ".join(THEME_TAGS),
    ))


if __name__ == "__main__":
    result = generate_history_short(past_topics=[])
    print(json.dumps(result, indent=2, ensure_ascii=False))
