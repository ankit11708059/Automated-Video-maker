"""
Premium video effects — Premiere Pro quality in Python.

Effects implemented:
  depth_of_field      — Gaussian blur on BG, sharp center (cinematic DoF)
  bloom               — Downsampled screen-blend glow on bright areas
  radial_zoom_blur    — Adobe-style zoom smear at section cuts
  anamorphic_flare    — Horizontal lens streak + ring artifacts at cuts
  color_mood          — Subtle bull-green / bear-red ambient tint
  draw_chart_widget   — Animated candlestick chart in top-right corner
  draw_money_rain     — Falling Rs/$ symbols (alpha composited)
  draw_counter        — Number counting up (e.g. "+8.90%" reveal)
  film_halation       — Red channel bloom in highlights (analog film look)
"""

import math, re, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920

# ─── Asset path ───────────────────────────────────────────────────────────────
_FONT_DISPLAY = os.path.join(os.path.dirname(__file__), "fonts", "BebasNeue.ttf")
_FONT_BOLD    = r"C:\Windows\Fonts\arialbd.ttf"

def _font(path, size):
    try:    return ImageFont.truetype(path, size)
    except: return ImageFont.truetype(_FONT_BOLD, size)

# ─── Fixed random data (seeded — same every render) ──────────────────────────
_rng  = np.random.default_rng(777)
_N    = 20   # particle count

_P_X     = (_rng.random(_N) * W).astype(int)
_P_Y     = (_rng.random(_N) * H).astype(int)
_P_SPEED = 0.05 + _rng.random(_N) * 0.10
_P_SIZE  = 14 + (_rng.random(_N) * 20).astype(int)
_P_ROT   = _rng.random(_N) * 360
_P_PHASE = _rng.random(_N) * math.pi * 2

# Realistic candlestick price data (slightly bullish, with dips)
_rng2 = np.random.default_rng(42)
_raw  = _rng2.standard_normal(16) * 0.5
_raw  = np.cumsum(_raw) + np.linspace(0, 3, 16)   # upward drift
_CHART_PRICES = _raw

# ─── Grain pool (pre-baked, cycled) ─────────────────────────────────────────
_GRAIN_POOL_SZ = 8
_GRAIN_POOL    = [
    np.random.default_rng(i * 9973).integers(-7, 8, (H, W, 3), dtype=np.int16)
    for i in range(_GRAIN_POOL_SZ)
]

def film_grain(frame: np.ndarray, frame_num: int) -> np.ndarray:
    return np.clip(frame.astype(np.int16) + _GRAIN_POOL[frame_num % _GRAIN_POOL_SZ],
                   0, 255).astype(np.uint8)

# ─── 1. Depth of Field ────────────────────────────────────────────────────────

def depth_of_field(frame: np.ndarray, blur_radius: int = 5) -> np.ndarray:
    """
    Blurs the background, keeps a center ellipse sharp.
    Simulates a wide-aperture camera lens — separates subject from BG.
    """
    img     = Image.fromarray(frame)
    blurred = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Mask: white = sharp (center ellipse), black = blurred (edges)
    mask = Image.new("L", (W, H), 0)
    d    = ImageDraw.Draw(mask)
    d.ellipse([160, 260, W - 160, H - 260], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=90))

    composite = Image.composite(img, blurred, mask)
    return np.array(composite)

# ─── 2. Bloom ────────────────────────────────────────────────────────────────

def bloom(img: Image.Image, radius: int = 14, strength: float = 0.42) -> Image.Image:
    """
    Screen-blend bloom: bright areas emit a soft glow halo.
    Computed on 1/4-res image for speed, then upsampled back.
    Identical to Premiere Pro's 'Lens Blur' glow effect.
    """
    # Downsample
    small = img.resize((W // 4, H // 4), Image.BILINEAR)
    arr   = np.array(small).astype(np.float32)

    # Extract and blur bright areas (threshold=85)
    bright = np.clip(arr - 85, 0, 255)
    glow   = Image.fromarray(bright.astype(np.uint8)) \
                  .filter(ImageFilter.GaussianBlur(radius=radius))
    glow   = glow.resize((W, H), Image.BILINEAR)   # upsample

    # Screen blend: result = 1-(1-base)(1-glow)
    base_f = np.array(img).astype(np.float32) / 255.0
    glow_f = np.array(glow).astype(np.float32) * strength / 255.0
    out    = 1.0 - (1.0 - base_f) * (1.0 - glow_f)
    return Image.fromarray(np.clip(out * 255, 0, 255).astype(np.uint8))

# ─── 3. Film Halation ────────────────────────────────────────────────────────

def film_halation(img: Image.Image, strength: float = 0.28) -> Image.Image:
    """
    Analog film look: red channel bleeds into highlights.
    Happens when bright light hits film emulsion — seen in ARRI/RED footage.
    """
    arr    = np.array(img).astype(np.float32)
    # Red channel bleed in highlights only
    lum    = 0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]
    hi     = np.clip((lum - 180) / 75.0, 0, 1)[:,:,None]
    bleed  = Image.fromarray(arr[:,:,0].astype(np.uint8)) \
                  .filter(ImageFilter.GaussianBlur(radius=8))
    bleed_f = np.array(bleed).astype(np.float32)[:,:,None]
    arr[:,:,0] = np.clip(arr[:,:,0] + bleed_f[:,:,0] * hi[:,:,0] * strength, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))

# ─── 4. Radial Zoom Blur ─────────────────────────────────────────────────────

def radial_zoom_blur(frame: np.ndarray, t: float, seg_start: float,
                     steps: int = 6) -> np.ndarray:
    """
    Adobe Premiere 'Zoom Blur' transition effect.
    Creates an explosive zoom smear on the first 0.12s of each section cut.
    """
    dt = t - seg_start
    if dt >= 0.12 or dt < 0:
        return frame

    strength = 0.016 * (1.0 - dt / 0.12) ** 2
    img      = Image.fromarray(frame)
    acc      = np.zeros((H, W, 3), dtype=np.float64)

    for i in range(1, steps + 1):
        s    = 1.0 + strength * i
        nw   = max(W + 2, int(W * s))
        nh   = max(H + 2, int(H * s))
        big  = img.resize((nw, nh), Image.BILINEAR)
        ox   = (nw - W) // 2
        oy   = (nh - H) // 2
        crop = np.array(big)[oy:oy + H, ox:ox + W]
        acc  += crop.astype(np.float64) / steps

    # Blend: 60% zoomed, 40% original
    result = acc * 0.60 + frame.astype(np.float64) * 0.40
    return np.clip(result, 0, 255).astype(np.uint8)

# ─── 5. Anamorphic Lens Flare ────────────────────────────────────────────────

def anamorphic_flare(img: Image.Image, t: float, seg_start: float,
                     banner_color: tuple = (215, 0, 0)) -> Image.Image:
    """
    Horizontal anamorphic lens flare — seen in high-end Premiere / DaVinci edits.
    Appears at the first 0.30s of each cut: a bright horizontal streak + ring artifacts.
    """
    dt = t - seg_start
    if dt >= 0.30 or dt < 0:
        return img

    # Bell-curve intensity: rises then falls
    intensity = math.sin(dt / 0.30 * math.pi)

    overlay  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d        = ImageDraw.Draw(overlay)

    # Hot spot position: drifts from right to center
    hx = int(W * (0.85 - 0.35 * (dt / 0.30)))
    hy = H // 5

    # 1) Horizontal anamorphic streak (thin, full width)
    streak_a = int(120 * intensity)
    for thickness, alpha_mul in [(3, 1.0), (8, 0.4), (18, 0.15)]:
        a = int(streak_a * alpha_mul)
        if a > 0:
            d.rectangle([0, hy - thickness, W, hy + thickness],
                        fill=(200, 220, 255, a))

    # 2) Hot spot glow (bright center)
    for r, a_factor in [(80, 0.8), (140, 0.3), (220, 0.1)]:
        a = int(200 * intensity * a_factor)
        if a > 0:
            d.ellipse([hx - r, hy - r, hx + r, hy + r],
                      fill=(255, 255, 240, a))

    # 3) Ring artifacts (lens aperture reflections)
    br, bg_c, bb = banner_color
    for rx, ry, rw in [(hx * 0.4, hy * 1.6, 45), (W - hx * 0.6, hy * 0.8, 30)]:
        a = int(60 * intensity)
        if a > 0:
            d.ellipse([int(rx)-rw, int(ry)-rw, int(rx)+rw, int(ry)+rw],
                      outline=(br, bg_c, bb, a), width=3)

    merged = Image.alpha_composite(img.convert("RGBA"), overlay)
    return merged.convert("RGB")

# ─── 6. Color Mood ───────────────────────────────────────────────────────────

def color_mood(frame: np.ndarray, itype: str, text: str,
               strength: float = 0.10) -> np.ndarray:
    """
    Subtle ambient tint based on content sentiment:
      breaking + bullish text → warm green glow
      market + downside/risk  → cool red warning tone
      cta                     → golden/warm
    This is the Premiere Pro 'Color Grading Adjustment Layer' technique.
    """
    _bull = re.search(r'JUMP|SURGE|GAIN|GREEN|UP |BULLISH|\+', text, re.I)
    _bear = re.search(r'RISK|DOWNSIDE|CRASH|FALL|WARNING|BEARISH|DOWN', text, re.I)

    if itype == "cta":
        tint = np.array([255, 200, 80], dtype=np.float32)
    elif _bull and itype in ("breaking", "company"):
        tint = np.array([80, 255, 120], dtype=np.float32)
    elif _bear and itype == "market":
        tint = np.array([255, 80, 80], dtype=np.float32)
    else:
        return frame

    f      = frame.astype(np.float32)
    result = f * (1 - strength) + tint[None, None, :] * strength
    return np.clip(result, 0, 255).astype(np.uint8)

# ─── 7. Animated Candlestick Chart Widget ────────────────────────────────────

def draw_chart_widget(img: Image.Image, t: float, seg_start: float,
                      x: int = 668, y: int = 142,
                      w: int = 392, h: int = 215) -> Image.Image:
    """
    TradingView-style animated candlestick chart in top-right area.
    Candles reveal one by one for first 2s, then animate price line.
    """
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d       = ImageDraw.Draw(overlay)

    # Semi-transparent dark background
    d.rounded_rectangle([x, y, x + w, y + h], radius=10,
                        fill=(0, 0, 15, 200))
    d.rounded_rectangle([x, y, x + w, y + h], radius=10,
                        outline=(40, 80, 40, 180), width=2)

    # "NSE LIVE" label top-left of widget
    lf = _font(_FONT_DISPLAY, 22)
    d.text((x + 10, y + 8), "NSE  LIVE", fill=(80, 200, 100, 220), font=lf)

    n       = len(_CHART_PRICES)
    reveal  = min(n, max(2, int((t - seg_start) * 4 + 2)))
    cw      = (w - 20) // n   # candle slot width
    pad_b   = 30              # bottom padding for axis
    chart_h = h - 45 - pad_b

    prices  = _CHART_PRICES[:reveal]
    mn, mx  = _CHART_PRICES.min(), _CHART_PRICES.max()
    rng_p   = max(mx - mn, 0.01)

    def price_to_y(p):
        return int(y + 40 + chart_h * (1 - (p - mn) / rng_p))

    line_pts = []
    for i, price in enumerate(prices):
        cx_   = x + 10 + i * cw + cw // 2
        cy_   = price_to_y(price)
        line_pts.append((cx_, cy_))

        # Candle body
        open_ = _CHART_PRICES[max(0, i - 1)]
        is_up = price >= open_
        col   = (40, 210, 80, 220) if is_up else (220, 50, 50, 200)
        bh    = max(4, abs(int((price - open_) / rng_p * chart_h)))
        by1   = min(price_to_y(price), price_to_y(open_))
        by2   = max(price_to_y(price), price_to_y(open_)) + bh
        d.rectangle([cx_ - 4, by1, cx_ + 4, by2], fill=col)

        # Wick
        wick_top = by1 - int(rng_p * 0.08 * chart_h / rng_p)
        d.line([(cx_, wick_top), (cx_, by2 + 4)],
               fill=(col[0], col[1], col[2], 140), width=1)

    # Trend line over candles
    if len(line_pts) >= 2:
        for i in range(len(line_pts) - 1):
            d.line([line_pts[i], line_pts[i + 1]],
                   fill=(100, 255, 150, 200), width=2)

    # Glow under the line (simulate chart area fill)
    if len(line_pts) >= 2:
        poly_pts = list(line_pts) + [(line_pts[-1][0], y + h - pad_b),
                                     (line_pts[0][0],  y + h - pad_b)]
        d.polygon(poly_pts, fill=(40, 180, 80, 35))

    # Latest price label
    if len(prices):
        pf   = _font(_FONT_BOLD, 24)
        last = prices[-1]
        col  = (80, 255, 100, 255) if last >= prices[0] else (255, 80, 80, 255)
        pct  = (last - prices[0]) / abs(prices[0]) * 100
        sign = "+" if pct >= 0 else ""
        d.text((x + w - 110, y + 8), f"{sign}{pct:.1f}%", fill=col, font=pf)

    # Bottom axis ticks
    tf = _font(_FONT_BOLD, 16)
    for i in range(0, reveal, 4):
        tx = x + 10 + i * cw + cw // 2
        d.text((tx - 5, y + h - 22), f"T{i+1}", fill=(80, 80, 100, 160), font=tf)

    merged = Image.alpha_composite(img.convert("RGBA"), overlay)
    return merged.convert("RGB")

# ─── 8. Money / Rs Particle Rain ─────────────────────────────────────────────

def draw_money_rain(img: Image.Image, t: float,
                    symbols: tuple = ("Rs", "$", "+"), count: int = 18) -> Image.Image:
    """
    Falling money particles — Rs/$ symbols floating downward with rotation.
    Alpha-composited so they don't overpower the main content.
    Seeded positions = consistent animation, no flicker.
    """
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    for i in range(count):
        sym   = symbols[i % len(symbols)]
        speed = _P_SPEED[i]
        phase = _P_PHASE[i]

        # Y position wraps: particle falls from top, reappears at top
        y_frac = ((_P_Y[i] / H) + speed * t * 0.18 + phase * 0.05) % 1.0
        px     = _P_X[i] + int(18 * math.sin(t * 0.6 + phase))
        py     = int(y_frac * H)

        # Fade out near top and bottom
        edge_fade = min(y_frac, 1.0 - y_frac) * 8
        alpha     = int(min(1.0, edge_fade) * 55)

        if alpha < 5:
            continue

        sz = _P_SIZE[i]
        pf = _font(_FONT_DISPLAY, sz)

        # Draw on tiny sub-image for rotation
        tile_sz = sz * 3
        tile    = Image.new("RGBA", (tile_sz, tile_sz), (0, 0, 0, 0))
        td      = ImageDraw.Draw(tile)
        gold    = (255, 210, 50, alpha)
        td.text((tile_sz // 4, tile_sz // 4), sym, fill=gold, font=pf)

        rot   = (_P_ROT[i] + t * 25) % 360
        tile  = tile.rotate(rot, expand=False)
        ox, oy = px - tile_sz // 2, py - tile_sz // 2
        if 0 <= ox < W - tile_sz and 0 <= oy < H - tile_sz:
            overlay.paste(tile, (ox, oy), tile)

    merged = Image.alpha_composite(img.convert("RGBA"), overlay)
    return merged.convert("RGB")

# ─── 9. Animated Percentage Counter ──────────────────────────────────────────

def draw_counter(img: Image.Image, value: float, unit: str,
                 label: str, t: float, seg_start: float,
                 cx: int = W // 2, cy: int = H // 2 + 220) -> Image.Image:
    """
    Counts from 0 to `value` over 1.4s with ease-out, then pulses.
    Used in breaking section to animate stock percentage.
    """
    dt = t - seg_start
    if dt < 0.2:
        return img   # slight delay before starting

    elapsed = dt - 0.2
    COUNT   = 1.4

    if elapsed < COUNT:
        cur = value * math.sin(elapsed / COUNT * math.pi / 2) ** 2
    else:
        cur = value

    # Pulse after counting
    if elapsed > COUNT:
        pulse = 0.92 + 0.08 * math.sin((elapsed - COUNT) * 7)
    else:
        pulse = 1.0

    sign    = "+" if value >= 0 else ""
    display = f"{sign}{cur:.2f}{unit}"

    color   = (50, 255, 100) if value >= 0 else (255, 70, 70)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d       = ImageDraw.Draw(overlay)

    # Background pill
    fs = int(96 * pulse)
    cf = _font(_FONT_DISPLAY, fs)
    bb = d.textbbox((0, 0), display, font=cf)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad = 20
    pill_x1 = cx - tw // 2 - pad
    pill_y1 = cy - pad
    pill_x2 = cx + tw // 2 + pad
    pill_y2 = cy + th + pad
    d.rounded_rectangle([pill_x1, pill_y1, pill_x2, pill_y2],
                        radius=14, fill=(0, 0, 0, 180))

    # Outer glow ring
    glow_col = (*color, 50)
    d.rounded_rectangle([pill_x1 - 4, pill_y1 - 4, pill_x2 + 4, pill_y2 + 4],
                        radius=18, outline=glow_col, width=3)

    # Counter text — stroke then fill
    for dx in range(-4, 5, 2):
        for dy in range(-4, 5, 2):
            if dx or dy:
                d.text((cx - tw // 2 + dx, cy + dy), display,
                       fill=(0, 0, 0, 200), font=cf)
    d.text((cx - tw // 2, cy), display, fill=(*color, 255), font=cf)

    # Label below
    lf = _font(_FONT_BOLD, 28)
    d.text((cx, cy + th + 8), label, fill=(200, 200, 200, 180),
           font=lf, anchor="mm")

    merged = Image.alpha_composite(img.convert("RGBA"), overlay)
    return merged.convert("RGB")

# ─── Utility: extract percentage from segment lines ───────────────────────────

def extract_stat(lines: list):
    combined = " ".join(lines)
    m = re.search(r'(\d+\.?\d*)\s*%', combined)
    if m:
        return float(m.group(1)), "%", "TOP MOVER"
    return None

# ─── 10. Emoji / Symbol Particle Rain ────────────────────────────────────────

_rng3      = np.random.default_rng(321)
_EP_N      = 14
_EP_X      = (_rng3.random(_EP_N) * W).astype(int)
_EP_Y      = (_rng3.random(_EP_N) * H).astype(int)
_EP_SPEED  = 0.04 + _rng3.random(_EP_N) * 0.08
_EP_SIZE   = 18 + (_rng3.random(_EP_N) * 18).astype(int)
_EP_PHASE  = _rng3.random(_EP_N) * math.pi * 2

_BULL_SYMS = ["^", "+", "$", "UP", "^"]
_BEAR_SYMS = ["v", "-", "!", "DN", "v"]


def emoji_rain(img: Image.Image, t: float, itype: str, text: str) -> Image.Image:
    """
    Subtle floating symbol rain — bullish (^/$) or bearish (v/!) depending
    on section content. Seeded so animation is consistent across renders.
    """
    bull = re.search(r'JUMP|SURGE|GAIN|GREEN|UP |BULLISH|\+|HIGH', text, re.I)
    bear = re.search(r'CRASH|FALL|RISK|BEARISH|DOWN|LOSS|WARNING', text, re.I)

    if not (bull or bear): return img
    symbols = _BULL_SYMS if bull else _BEAR_SYMS
    color   = (80, 255, 120) if bull else (255, 80, 80)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i in range(_EP_N):
        phase  = _EP_PHASE[i]
        y_frac = ((_EP_Y[i] / H) + _EP_SPEED[i] * t * 0.14 + phase * 0.04) % 1.0
        px     = _EP_X[i] + int(22 * math.sin(t * 0.5 + phase))
        py     = int(y_frac * H)

        edge_fade = min(y_frac, 1.0 - y_frac) * 6
        alpha     = int(min(1.0, edge_fade) * 40)
        if alpha < 4: continue

        sz   = _EP_SIZE[i]
        sym  = symbols[i % len(symbols)]
        pf   = _font(_FONT_DISPLAY, sz)
        tile_sz = sz * 3
        tile    = Image.new("RGBA", (tile_sz, tile_sz), (0, 0, 0, 0))
        td      = ImageDraw.Draw(tile)
        td.text((tile_sz//4, tile_sz//4), sym, fill=(*color, alpha), font=pf)
        ox, oy = px - tile_sz//2, py - tile_sz//2
        if 0 <= ox < W - tile_sz and 0 <= oy < H - tile_sz:
            overlay.paste(tile, (ox, oy), tile)

    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
