"""
Atmospheric image fetching for the Lost History channel.
Uses Pexels with curated history/mystery query templates per section.
"""

from news_fetcher import _pexels_image_query


# Atmospheric, cinematic, history-themed Pexels queries per section role
SECTION_QUERIES = {
    "breaking": [
        "ancient ruins dramatic sunset",
        "old stone temple atmospheric mist",
        "dark forest fog mysterious",
        "ancient ruins moonlight cinematic",
        "stone monument silhouette dawn",
    ],
    "market": [
        "old manuscript candle dark",
        "ancient map parchment vintage",
        "old book library dusty",
        "ancient artifact museum gold",
        "vintage compass map exploration",
    ],
    "cta": [
        "ancient ruins golden hour",
        "old castle silhouette mist",
        "archaeological site dramatic sky",
        "ancient stone monument dusk",
        "sunset over old temple ruins",
    ],
}


def fetch_history_images(main_query: str, seed: int = 0) -> dict:
    """
    Fetch 4 atmospheric history-themed images.
    main_query: Claude-generated pexels_query for the specific mystery (e.g. "egyptian pyramid sunset desert").
    Returns {breaking, company, market, cta} -> file paths (or None on failure).
    """
    print(f"  Fetching history images (main_query='{main_query[:40]}')...")
    images = {}

    bq = SECTION_QUERIES["breaking"][seed % len(SECTION_QUERIES["breaking"])]
    images["breaking"] = _pexels_image_query(bq, seed)
    print(f"    breaking ({bq[:32]}): {'OK' if images['breaking'] else 'MISSING'}")

    images["company"] = _pexels_image_query(main_query, seed)
    print(f"    main    ({main_query[:32]}): {'OK' if images['company'] else 'MISSING'}")

    mq = SECTION_QUERIES["market"][seed % len(SECTION_QUERIES["market"])]
    images["market"] = _pexels_image_query(mq, seed + 1)
    print(f"    detail  ({mq[:32]}): {'OK' if images['market'] else 'MISSING'}")

    cq = SECTION_QUERIES["cta"][seed % len(SECTION_QUERIES["cta"])]
    images["cta"] = _pexels_image_query(cq, seed + 2)
    print(f"    closing ({cq[:32]}): {'OK' if images['cta'] else 'MISSING'}")

    # Fallback to main_query for any missing
    for k in list(images.keys()):
        if not images[k]:
            images[k] = _pexels_image_query(main_query, seed + 5)
            print(f"    {k} fallback: {'OK' if images[k] else 'STILL MISSING'}")

    return images
