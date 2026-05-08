"""
Download premium assets for video_gen.
Run once: py setup_assets.py
Downloads: Bebas Neue font (bold condensed — used in every pro finance video)
"""

import os, requests, zipfile, io

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
os.makedirs(FONTS_DIR, exist_ok=True)

BEBAS_PATH = os.path.join(FONTS_DIR, "BebasNeue.ttf")

# Multiple fallback URLs for Bebas Neue (free / OFL licensed)
_BEBAS_URLS = [
    "https://github.com/google/fonts/raw/main/ofl/bebasneuepro/BebasNeuePro-Regular.ttf",
    "https://github.com/dharmatype/Bebas-Neue/raw/master/fonts/Bebas%20Neue%20Regular.otf",
    "https://fonts.gstatic.com/s/bebasneuepro/v3/UhS52XSkx-FVala29oGXfDwiQKbQBnpg.ttf",
]

def download_bebas_neue():
    if os.path.exists(BEBAS_PATH) and os.path.getsize(BEBAS_PATH) > 10000:
        print(f"  Bebas Neue already at {BEBAS_PATH}")
        return BEBAS_PATH

    for url in _BEBAS_URLS:
        print(f"  Trying: {url[:65]}...")
        try:
            r = requests.get(url, timeout=15,
                             headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200 and len(r.content) > 10000:
                with open(BEBAS_PATH, "wb") as f:
                    f.write(r.content)
                print(f"  Downloaded Bebas Neue -> {BEBAS_PATH}")
                return BEBAS_PATH
        except Exception as e:
            print(f"  Failed: {e}")

    # Fallback: copy Impact font
    impact = r"C:\Windows\Fonts\impact.ttf"
    if os.path.exists(impact):
        import shutil
        shutil.copy(impact, BEBAS_PATH)
        print(f"  Bebas Neue unavailable — using Impact font instead.")
        return BEBAS_PATH

    print("  WARNING: Could not get display font. Arial Bold will be used.")
    return None


if __name__ == "__main__":
    print("=" * 50)
    print("  YTShorts Asset Setup")
    print("=" * 50)
    result = download_bebas_neue()
    print(f"\n  Font ready: {result}")
    print("  Done.")
