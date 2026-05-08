import os

# ─── Load local .env file if present (for local dev without setting env vars) ─
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_file):
    for _line in open(_env_file):
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ─── API Keys (from env vars — set in GitHub Secrets or local .env) ───────────
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
PEXELS_API_KEY     = os.getenv("PEXELS_API_KEY",     "")
STABILITY_API_KEY  = os.getenv("STABILITY_API_KEY",  "")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY",  "")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY",     "")

# ─── Voice preferences ────────────────────────────────────────────────────────
# Aryaveer/Yatin = Indian voices (ElevenLabs Creator plan required)
PREFERRED_VOICES = ["Aryaveer", "Yatin", "Daniel", "George", "Brian", "Charlie", "Adam"]

# ─── Video settings ──────────────────────────────────────────────────────────
VIDEO_WIDTH  = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS    = 30

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CACHE_DIR  = os.path.join(BASE_DIR, "cache")
FONT_DIR   = os.path.join(BASE_DIR, "fonts")

for d in [OUTPUT_DIR, CACHE_DIR, FONT_DIR]:
    os.makedirs(d, exist_ok=True)
