"""
Claude Sonnet-powered ENGLISH script + SEO generator for the
"Lost History & Forgotten Mysteries" YouTube Shorts channel.

Picks a fresh viral mystery each run (using the past-topics log for anti-dup)
and produces: viral title, 60s narration script, 4 on-screen sections,
30 SEO tags, YouTube description, Pexels query.
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


_SYSTEM = """\
You are THREE elite experts operating as one unified intelligence for the
"Lost History & Forgotten Mysteries" YouTube Shorts channel — a niche covering
forgotten civilizations, unsolved historical events, ancient secrets, lost
cities, mysterious artifacts, vanished peoples, and historical conspiracies.

1. ELITE YOUTUBE TITLE STRATEGIST & VIRAL PATTERN FORENSIC ANALYST
   You reverse-engineer the top-performing history/mystery Shorts (MrBallen,
   BuzzFeed Unsolved, Bedtime Stories style) to extract every replicable title
   formula, emotional trigger, and structural pattern. You treat title creation
   as forensic science. Your livelihood depends on 500k+ view performance.
   For every title: identify formula used, psychological trigger (curiosity gap
   / fear / awe / forbidden knowledge / authority), and estimated CTR potential.
   You generate 3 engineered title variations and self-select the highest CTR.

2. SENIOR YOUTUBE SCRIPT FORENSIC ANALYST & GHOSTWRITER (history niche)
   You have analysed hundreds of viral history Shorts (500k+ views in <1 month)
   and extracted every replicable writing pattern. Your scripts are built on:
   — HOOK SEQUENCE: pattern interrupt → instant intrigue → curiosity gap (first 5s)
   — PACING: short cinematic sentences, dramatic pauses (use commas + ellipses)
   — CURIOSITY GAP: tease the central mystery early, deliver the reveal at ~35s
   — PATTERN INTERRUPT: an unexpected angle, contrast, or revelation mid-script
     that re-engages viewers about to swipe
   — INFORMATION REVEAL: the payoff — a specific date, name, number, or theory
   — ENDING TECHNIQUE: an open question that demands a comment, then subscribe
   You write in atmospheric narrative English — like David Attenborough meets
   a true-crime narrator. Cinematic, never academic. NEVER use "Did you know..."
   or other lazy hooks.

3. SENIOR YOUTUBE SEO STRATEGIST for history/mystery audience
   You know which English-language history/mystery keywords drive Shorts
   discovery, which evergreen tags compound view velocity, and how to structure
   descriptions for the algorithm. You think in search intent: what is someone
   typing when they want to be shocked and informed?"""


_PROMPT = """\
Generate ONE complete, monetization-ready YouTube Short for the "Lost History
& Forgotten Mysteries" channel. Apply your full forensic viral framework.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI-DUPLICATION — DO NOT repeat these topics already covered:
{past_topics}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOPIC SELECTION:
Pick a SINGLE specific mystery, lost civilization, unexplained artifact, vanished
people, ancient megastructure, mysterious death, historical conspiracy, or
unsolved event from world history. It must be:
  • Visually atmospheric (must be possible to illustrate with stock footage of
    ruins, old maps, ancient art, dark caves, dramatic landscapes)
  • Genuinely intriguing (real historical mystery, not pop-culture hoax)
  • Specific enough to fit in 60 seconds (one event, not a broad era)
  • NOT in the anti-dup list above

Good niche examples (do not copy verbatim — generate something fresh):
  Roanoke Colony • Antikythera Mechanism • Voynich Manuscript • Göbekli Tepe •
  Yonaguni Monument • Dyatlov Pass • Tunguska Event • Lost Indus Valley •
  Mary Celeste • The Bog Bodies • The Green Children of Woolpit •
  Tarim Mummies • Hessdalen Lights • Cahokia Collapse • Tartessos •
  The Aluminium Wedge of Aiud • Bimini Road • Olmec Heads • The Nazca Lines •
  The Lost Roman Legion • Sea Peoples • The Anasazi Disappearance

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 1 — VIDEO METADATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"topic_name": The clean name of the mystery (e.g., "Roanoke Colony", "Antikythera Mechanism").
              This is used for deduplication. Keep it short (2-6 words).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 2 — AUDIO SCRIPT (English, ~150 words, ~60 seconds spoken)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Atmospheric, cinematic English. Short sentences. Dramatic pauses (use commas and
ellipses to guide ElevenLabs delivery). NEVER start with "Did you know" or
"Imagine if". Write like you are whispering a forbidden secret to one person.

HOOK (0-5s) — Pattern interrupt + instant intrigue + curiosity gap:
  Example openers:
  "In 1587, an entire colony of one hundred and fifteen people... vanished overnight."
  "Beneath the ocean floor near Japan lies a structure... that should not exist."
  "There is a manuscript no human alive can read."
  "Archaeologists in Turkey unearthed something... that rewrites human history."

CURIOSITY GAP BRIDGE (5-15s):
  • Establish what is known (authority signal — give a date, place, name)
  • Plant the central question without answering it yet
  • Tease the strangest detail

REVEAL + DETAILS (15-45s):
  • Deliver the specific mystery: who, what, when, where
  • The strangest evidence or detail (a specific number, name, artifact)
  • Pattern interrupt: a competing theory or unexpected contrast
  • Build toward the cliffhanger ("And then... they found this.")

CTA (45-60s):
  • Land the emotional weight ("To this day, no one knows what happened.")
  • Open question that demands a comment ("What do YOU think happened?")
  • Subscribe ask tied to the niche ("Follow for more lost history every day.")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 3 — VIRAL TITLE ENGINEERING (3 options → self-select best)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generate exactly 3 engineered title options in English (max 80 chars each).
Each must apply a distinct formula:
  Option A: [Specific number/date] + [Mystery] + [Cliffhanger phrase]
            e.g., "In 1587, 115 People Vanished Without a Trace..."
  Option B: [Forbidden knowledge framing] + [Mystery] + [Question]
            e.g., "The Manuscript NO ONE Can Read | The Voynich Mystery"
  Option C: [Authority claim] + [Shocking detail] + [Curiosity gap]
            e.g., "Scientists Found a 2,000-Year-Old Computer in the Sea"

Then self-select the highest-CTR option as "viral_title".
Use ALL CAPS sparingly for emphasis (one or two words max). Pipe character allowed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 4 — ON-SCREEN DISPLAY SECTIONS (4 sections)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL: ASCII-safe English only. PIL cannot render special characters.
4 sections, 3 lines per section, max 32 chars each line. Include numbers/dates.

image_type: pick from "breaking", "company", "market", "cta" — semantic mapping:
  • "breaking" → opening hook scene (use for the dramatic opener)
  • "company"  → central subject scene (the mystery itself — site, artifact, people)
  • "market"   → evidence/detail scene (maps, documents, ruins detail)
  • "cta"      → closing/atmospheric scene (sunset over ruins, dark, mysterious)

time_weight: word count in that audio section (all 4 must sum to ~150)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 5 — SEO TAGS (exactly 30 tags)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Think: what is a history/mystery fan typing into YouTube right now?
Mix these 6 categories, 5 tags each:

A. HIGH VOLUME EVERGREEN: "lost history", "ancient mysteries", "unsolved mysteries", "history shorts", "mystery shorts"
B. TOPIC SPECIFIC: [specific mystery name] + variations (e.g., "voynich manuscript", "voynich decoded")
C. THEMATIC: "ancient civilizations", "forgotten history", "ancient secrets", "lost civilizations", "historical conspiracies"
D. EMOTIONAL/CURIOSITY: "creepy history", "things they dont teach you", "history you didnt know", "weird history", "scary history facts"
E. QUESTION/SEARCH: "what happened to", "who built", "the truth about", "real story of"
F. SHORTS DISCOVERY: "history shorts english", "mystery shorts", "ancient shorts", "unexplained shorts", "documentary shorts"

Rule: Each tag max 30 chars, all lowercase, ASCII English letters/digits/spaces only.
No special chars, no emoji, no hashtags inside tags. YouTube API safe.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 6 — YOUTUBE DESCRIPTION (~200 words, SEO-optimised)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIRST LINE (150 chars max): The mystery name + one-line hook with the central question.
Body: 3-4 sentences expanding the mystery with natural keyword placement:
  "ancient mysteries", "lost history", "unsolved", "forgotten civilization", etc.
End with: Subscribe + bell + comment prompt ("What do you think happened? Comment below.")
Hashtags last line: #LostHistory #Mystery #AncientMysteries #Shorts + 4 topic-specific

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 7 — PEXELS QUERY (3-4 words)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pick atmospheric, history-themed visual query that matches your mystery:
  • Lost city → "ancient ruins stone temple"
  • Manuscript → "old manuscript candle dark"
  • Ancient artifact → "ancient artifact museum gold"
  • Cave / underwater → "dark cave torch mysterious"
  • Egyptian → "egyptian pyramid sunset desert"
  • Greek/Roman → "greek temple ruins columns"
  • Disappearance/empty → "abandoned village mist forest"
  • Maritime → "old ship ocean fog mystery"
  • Tomb / death → "ancient tomb stone dark"
  • Astronomical → "ancient observatory stars night"

OUTPUT — VALID JSON ONLY, no markdown, no explanation:
{{
  "topic_name":   "...",
  "audio_script": "...",
  "title_options": [
    {{"title": "...", "formula": "A: number+mystery+cliffhanger", "trigger": "curiosity gap"}},
    {{"title": "...", "formula": "B: forbidden knowledge+question", "trigger": "forbidden knowledge"}},
    {{"title": "...", "formula": "C: authority+shocking detail", "trigger": "authority + awe"}}
  ],
  "viral_title":  "...",
  "sections": [
    {{"image_type": "breaking", "time_weight": 25, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "company",  "time_weight": 45, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "market",   "time_weight": 45, "lines": ["LINE 1", "Line 2", "Line 3"]}},
    {{"image_type": "cta",      "time_weight": 35, "lines": ["LINE 1", "Line 2", "Line 3"]}}
  ],
  "tags":        ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10","tag11","tag12","tag13","tag14","tag15","tag16","tag17","tag18","tag19","tag20","tag21","tag22","tag23","tag24","tag25","tag26","tag27","tag28","tag29","tag30"],
  "description": "...",
  "pexels_query": "..."
}}"""


def _call_claude(prompt: str) -> dict:
    msg = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
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
                "tags", "description", "pexels_query")
    for key in required:
        if key not in data:
            raise RuntimeError(f"Missing key '{key}' in Claude response.")
    if "title_options" in data:
        print(f"  Title options ({len(data['title_options'])}):")
        for i, o in enumerate(data["title_options"], 1):
            print(f"    [{i}] {o.get('title', '')}  [{o.get('trigger', '')}]")
        print(f"  Selected: {data['viral_title']}")
    return data


def generate_history_short(past_topics: list[str]) -> dict:
    """
    Generate a fresh mystery Short, avoiding any topic in past_topics.
    past_topics is a list of topic_name strings already covered.
    """
    if past_topics:
        topics_str = "\n".join(f"  - {t}" for t in past_topics[-200:])
    else:
        topics_str = "  (none yet — pick anything)"
    return _call_claude(_PROMPT.format(past_topics=topics_str))


if __name__ == "__main__":
    result = generate_history_short(past_topics=[])
    print(json.dumps(result, indent=2, ensure_ascii=False))
