"""
Atmospheric image fetching for the Lost History channel.

Strategy for massive image variety:
  1. Claude generates 4 content-specific image queries per video (one per section)
  2. Each query → Pexels search returning up to 80 portrait photos
  3. Random selection (NOT always index 0), avoiding URLs already used in prior videos
  4. Fallback to a large curated theme pool if Claude's query returns nothing
  5. Used-URL log written back so future videos avoid repeats
"""

import random
import requests
from news_fetcher import _download
from config import PEXELS_API_KEY


# ─── Huge curated atmospheric query pool, organised by theme ─────────────────
# ~100 queries total — Pexels returns up to 80 photos each → ~5000 potential images.
THEME_POOLS = {
    "ruins_general": [
        "ancient stone ruins dramatic sunset",
        "old crumbling temple atmospheric",
        "ancient stone pillars overgrown",
        "ruined fortress dramatic sky",
        "abandoned ancient site mist",
        "stone monolith mysterious sunset",
        "ancient ruins ivy overgrown",
        "broken stone columns dramatic",
    ],
    "egyptian_desert": [
        "egyptian pyramid sunset dramatic",
        "egyptian sphinx desert",
        "ancient egyptian temple columns",
        "egyptian hieroglyphs stone wall",
        "desert pyramid silhouette",
        "saharan desert dunes atmospheric",
        "egyptian tomb interior dark",
        "ancient egyptian artifact gold",
    ],
    "greek_roman": [
        "greek temple columns dramatic",
        "roman colosseum atmospheric",
        "ancient greek ruins mediterranean",
        "roman aqueduct stone arches",
        "greek statue marble close up",
        "ancient roman forum ruins",
        "mediterranean ruins sunset",
        "greek amphitheater atmospheric",
    ],
    "mesoamerican": [
        "mayan pyramid jungle mist",
        "aztec stone temple ancient",
        "incan ruins mountains peru",
        "ancient mexican stone carving",
        "mayan temple steps dramatic",
        "machu picchu mountain mist",
        "mesoamerican stone idol",
        "jungle covered ancient ruins",
    ],
    "asian_ancient": [
        "angkor wat temple cambodia",
        "chinese ancient temple",
        "japanese ancient shrine fog",
        "indian ancient temple stone",
        "tibetan monastery mountains",
        "asian ancient stone carving",
        "buddhist stupa atmospheric",
        "ancient asian pagoda mist",
    ],
    "african": [
        "african savanna dramatic sunset",
        "ancient african rock art",
        "great zimbabwe ruins stone",
        "ethiopian rock church",
        "african tribal artifact",
        "moroccan kasbah desert",
        "african ancient stone monument",
        "saharan caravan dunes",
    ],
    "european_medieval": [
        "medieval castle dramatic sky",
        "gothic cathedral atmospheric interior",
        "stone castle ruins ivy",
        "european monastery old stone",
        "viking artifact museum",
        "medieval village snow dusk",
        "european fortress dramatic",
        "old european watchtower mist",
    ],
    "european_megalith": [
        "stonehenge dramatic sky",
        "celtic stone circle moss",
        "european standing stones mist",
        "neolithic dolmen field",
        "old stone burial mound",
        "irish stone tower coast",
    ],
    "underwater_maritime": [
        "underwater shipwreck atmospheric",
        "old sunken ship divers",
        "ocean depths mysterious dark",
        "old wooden ship storm ocean",
        "lighthouse storm dramatic",
        "ancient port harbor old",
        "ghost ship fog ocean",
        "shipwreck coast atmospheric",
    ],
    "polar_arctic": [
        "arctic ice dramatic landscape",
        "antarctic research station",
        "frozen tundra mysterious",
        "polar night dramatic sky",
        "iceberg ocean atmospheric",
        "snowy mountain expedition",
        "frozen wasteland dramatic",
        "arctic explorer vintage",
    ],
    "manuscript_document": [
        "old manuscript candle dark",
        "ancient parchment scroll",
        "vintage handwritten letter",
        "old book leather library",
        "ancient writing stone tablet",
        "old map parchment dramatic",
        "dusty book library candle",
        "vintage manuscript ink quill",
    ],
    "artifact_museum": [
        "ancient artifact museum gold",
        "old coin vintage collection",
        "ancient relic dramatic light",
        "museum showcase ancient",
        "ornate ancient jewelry",
        "ceremonial dagger artifact",
        "ancient mask close up",
        "bronze age artifact",
    ],
    "portrait_historical": [
        "vintage black white portrait mysterious",
        "old photograph faded sepia",
        "antique portrait painting",
        "vintage daguerreotype",
        "victorian era portrait moody",
        "old photo person mysterious",
        "historical portrait shadow",
        "antique family photograph faded",
    ],
    "map_exploration": [
        "old vintage map exploration",
        "antique compass map dramatic",
        "explorer journal old",
        "ancient navigation chart",
        "vintage globe library",
        "treasure map parchment dramatic",
        "old maritime chart",
    ],
    "ship_maritime": [
        "old wooden ship sails",
        "vintage ocean liner sepia",
        "tall ship stormy ocean",
        "lighthouse coast dramatic",
        "harbor old boats fog",
        "abandoned shipyard atmospheric",
    ],
    "aircraft_aviation": [
        "vintage airplane dramatic sky",
        "old propeller plane",
        "abandoned aircraft wreck",
        "vintage aviator portrait",
        "old aircraft hangar",
        "biplane sunset dramatic",
    ],
    "forest_wilderness": [
        "dark forest fog atmospheric",
        "haunted forest dramatic",
        "deep woods mysterious mist",
        "ancient forest old trees",
        "moss covered forest stones",
        "swamp fog atmospheric",
        "abandoned cabin forest",
    ],
    "cave_underground": [
        "dark cave torch light",
        "underground cavern dramatic",
        "ancient cave painting wall",
        "deep cave stalactites",
        "mysterious cave entrance",
        "underground tunnel atmospheric",
        "catacombs skull bones",
    ],
    "dark_atmospheric": [
        "dark moody atmospheric mist",
        "abandoned building dramatic",
        "empty room dramatic light",
        "old door dramatic shadow",
        "silhouette dramatic sky",
        "candle flame dark moody",
        "stormy night dramatic",
    ],
    "occult_supernatural": [
        "occult ritual symbol dark",
        "tarot card vintage",
        "alchemical symbols ancient",
        "ouija board vintage dark",
        "ancient symbol stone",
        "mystical artifact dramatic",
        "ritual altar candle",
    ],
}


# ─── Pexels helpers ──────────────────────────────────────────────────────────
def _pexels_random(query: str, exclude_urls: set) -> tuple[str | None, str | None]:
    """
    Search Pexels and pick a RANDOM portrait photo that isn't in exclude_urls.
    Returns (local_path, photo_url) — both None if nothing usable.
    """
    if not PEXELS_API_KEY:
        return None, None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 80, "orientation": "portrait"},
            timeout=10,
        )
        photos = r.json().get("photos", [])
    except Exception as e:
        print(f"    Pexels error ({query[:30]}): {e}")
        return None, None

    if not photos:
        return None, None

    # Prefer unseen photos; fall back to anything if all seen
    unseen = [p for p in photos if p["src"]["portrait"] not in exclude_urls]
    pool = unseen if unseen else photos
    chosen = random.choice(pool)
    url = chosen["src"]["portrait"]
    try:
        path = _download(url)
        return path, url
    except Exception as e:
        print(f"    Download error: {e}")
        return None, url


def _theme_fallback_query(themes: list[str]) -> str:
    """Pick a random query from any of the given theme pools."""
    pools = [THEME_POOLS[t] for t in themes if t in THEME_POOLS]
    if not pools:
        pools = list(THEME_POOLS.values())
    pool = random.choice(pools)
    return random.choice(pool)


# ─── Public API ──────────────────────────────────────────────────────────────
def fetch_history_images(section_queries: list[str],
                         themes: list[str] | None = None,
                         exclude_urls: set | None = None
                         ) -> tuple[dict, list[str]]:
    """
    Fetch 4 atmospheric images using Claude-generated per-section queries.

    Args:
        section_queries: 4 specific queries, one per section, content-matching
                         Order: [breaking, company, market, cta]
        themes:          fallback theme tags (e.g. ["egyptian_desert", "manuscript_document"])
                         used if a section_query returns no results
        exclude_urls:    set of photo URLs already used in prior videos (dedup)

    Returns: (images_dict, used_urls)
        images_dict: {breaking, company, market, cta} → local file paths
        used_urls:   list of photo URLs picked this run (caller should log them)
    """
    exclude = set(exclude_urls or [])
    themes = themes or ["ruins_general", "dark_atmospheric"]
    roles = ["breaking", "company", "market", "cta"]

    # Pad queries if Claude returned fewer than 4
    while len(section_queries) < 4:
        section_queries.append(_theme_fallback_query(themes))

    images: dict[str, str | None] = {}
    used: list[str] = []

    print(f"  Fetching {len(roles)} unique images (excluding {len(exclude)} prior URLs)...")
    for role, query in zip(roles, section_queries[:4]):
        path, url = _pexels_random(query, exclude)
        if not path:
            # Fallback to theme pool
            fallback_q = _theme_fallback_query(themes)
            print(f"    {role}: primary failed → fallback '{fallback_q[:30]}'")
            path, url = _pexels_random(fallback_q, exclude)
        if not path:
            # Last-resort generic
            for _ in range(3):
                generic_q = _theme_fallback_query(list(THEME_POOLS.keys()))
                path, url = _pexels_random(generic_q, exclude)
                if path:
                    print(f"    {role}: generic fallback '{generic_q[:30]}'")
                    break
        images[role] = path
        if url:
            used.append(url)
            exclude.add(url)
        print(f"    {role:8s} ({query[:34]:34s}): {'OK' if path else 'MISSING'}")

    return images, used
