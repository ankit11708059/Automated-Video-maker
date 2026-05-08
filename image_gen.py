"""
AI image generation for stock-specific video backgrounds.
Uses Stability AI stable-image-core — 9:16 portrait, cached, parallel.
Falls back gracefully if STABILITY_API_KEY is not set.

Cost: ~$0.003 per image × 4 sections = ~$0.012 per video.
"""

import os, hashlib, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import CACHE_DIR, STABILITY_API_KEY

AI_CACHE = os.path.join(CACHE_DIR, "ai_images")
os.makedirs(AI_CACHE, exist_ok=True)

_API_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"

_NEGATIVE = (
    "cartoon, anime, illustration, painting, drawing, text, watermark, "
    "logo, low quality, blurry, ugly, bad anatomy, duplicate, frame, border"
)

# ─── Per-section prompt templates ────────────────────────────────────────────

def build_prompts(company_query: str) -> dict:
    """
    Build Stability AI prompts for each section type.
    company_query: e.g. "maruti suzuki automobile india" or "adani ports mumbai"
    """
    c = company_query.strip()
    return {
        "breaking": (
            f"{c} india stock market breaking news, red dramatic cinematic lighting, "
            "financial crisis atmosphere, moody dark background, neon red reflections, "
            "ultra realistic 8K photography, shallow depth of field, professional"
        ),
        "company": (
            f"{c} india corporate headquarters modern building, aerial drone view, "
            "golden hour sunlight, glass facade reflections, photorealistic 8K, "
            "cinematic bokeh, dramatic sky, commercial photography"
        ),
        "market": (
            "bombay stock exchange NSE trading floor india, digital holographic "
            "stock charts glowing, busy professional traders, cinematic blue teal "
            "lighting, ultra realistic 8K, futuristic financial hub"
        ),
        "cta": (
            f"{c} india investment success, golden bull statue stock market symbol, "
            "coins and wealth visualization, 3D render, dramatic gold cinematic lighting, "
            "luxury financial concept, 8K photorealistic, rising charts"
        ),
    }


_STYLE_PRESETS = {
    "breaking": "cinematic",
    "company":  "photographic",
    "market":   "cinematic",
    "cta":      "3d-model",
}


# ─── Core generation ─────────────────────────────────────────────────────────

def _cache_path(prompt: str, seed: int) -> str:
    key = hashlib.md5(f"{prompt}|{seed}".encode()).hexdigest()[:16]
    return os.path.join(AI_CACHE, f"{key}.jpg")


def generate_ai_image(prompt: str, seed: int = 0,
                      style_preset: str = "photographic") -> str | None:
    """
    Generate a 9:16 portrait image. Returns local file path or None.
    Results are cached — same prompt+seed always returns the cached file.
    """
    if not STABILITY_API_KEY:
        return None

    path = _cache_path(prompt, seed)
    if os.path.exists(path) and os.path.getsize(path) > 5000:
        print(f"    AI cached [{style_preset}]: {os.path.basename(path)}")
        return path

    print(f"    Generating [{style_preset}]: {prompt[:55]}...")
    try:
        resp = requests.post(
            _API_URL,
            headers={
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Accept": "image/*",
            },
            files={
                "prompt":          (None, prompt),
                "aspect_ratio":    (None, "9:16"),
                "output_format":   (None, "jpeg"),
                "seed":            (None, str(seed % 4294967294)),
                "style_preset":    (None, style_preset),
                "negative_prompt": (None, _NEGATIVE),
            },
            timeout=40,
        )
        if resp.status_code == 200:
            with open(path, "wb") as f:
                f.write(resp.content)
            print(f"    AI image saved: {os.path.basename(path)}")
            return path
        else:
            print(f"    Stability AI {resp.status_code}: {resp.text[:120]}")
    except Exception as e:
        print(f"    AI generation error: {e}")
    return None


def generate_section_images(company_query: str, seed: int = 0) -> dict:
    """
    Generate all 4 section images in parallel.
    Returns {breaking, company, market, cta} → file path or None.
    """
    if not STABILITY_API_KEY:
        return {}

    prompts = build_prompts(company_query)
    results = {}

    def _gen(section):
        return section, generate_ai_image(
            prompts[section], seed, _STYLE_PRESETS.get(section, "photographic")
        )

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(_gen, s): s for s in prompts}
        for fut in as_completed(futures):
            section, path = fut.result()
            results[section] = path

    ok = sum(1 for v in results.values() if v)
    print(f"  AI images: {ok}/4 generated for '{company_query[:40]}'")
    return results
