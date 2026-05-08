"""
YouTube Shorts video generator — v5 (FFmpeg-native + Multiprocessing)

Speed vs v4:
  v4 (moviepy loop):   ~20 min / 60s Short  (1.3 fps)
  v5 (this file):      ~3-5 min / 60s Short (5-8 fps)

How:
  1. Multiprocessing.Pool renders frames in parallel (N CPU cores)
  2. Raw RGB chunks piped directly to ffmpeg — no moviepy overhead
  3. ffmpeg libx264 fast-preset encodes the final MP4

New effects vs v4:
  - Bloomberg-style scrolling news ticker (bottom strip)
  - Electric neon glow on stat / number lines
  - Emoji + symbol particle rain (bullish 🚀 / bearish ↓)
  - Spotlight sweep beam on section transitions
  - Animated pulsing border on text cards
  - Sharper chromatic aberration glitch
"""

import os, math, re, subprocess, tempfile, multiprocessing as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import VIDEO_WIDTH as W, VIDEO_HEIGHT as H, VIDEO_FPS, CACHE_DIR

import effects as fx

# ─── Font helpers ─────────────────────────────────────────────────────────────

_FONT_DISPLAY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "BebasNeue.ttf")
_FONT_BOLD    = r"C:\Windows\Fonts\arialbd.ttf"
_FONT_NORMAL  = r"C:\Windows\Fonts\arial.ttf"

def _f(size, bold=True, display=False):
    path = _FONT_DISPLAY if display else (_FONT_BOLD if bold else _FONT_NORMAL)
    try:    return ImageFont.truetype(path, size)
    except: return ImageFont.truetype(_FONT_BOLD, size)

# ─── Stat-line detector ───────────────────────────────────────────────────────

_STAT_RE = re.compile(
    r'%|\$|Rs\.|\d{3,}|JUMP|SURGE|CRASH|UP\b|DOWN\b|GAIN|LOSS|'
    r'ALERT|WARNING|RISK|BULLISH|BEARISH|HIGH|LOW', re.IGNORECASE
)
def _is_stat(text): return bool(_STAT_RE.search(text))

# ─── Background helpers ───────────────────────────────────────────────────────

def _load_bg(path):
    img = Image.open(path).convert("RGB")
    sw, sh = img.size
    ratio = W / H
    if sw / sh > ratio:
        nw = int(sh * ratio)
        img = img.crop(((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh))
    else:
        nh = int(sw / ratio)
        img = img.crop((0, (sh - nh) // 4, sw, (sh - nh) // 4 + nh))
    return np.array(img.resize((W, H), Image.LANCZOS))


def _ken_burns(bg_np, t, seg_start, duration, style="in"):
    punch_t = max(0.0, t - seg_start)
    punch   = 0.14 * max(0.0, (1.0 - punch_t / 0.22) ** 2) if punch_t < 0.22 else 0.0
    p = t / max(duration, 0.01)
    if   style == "in":       scale, px, py = 1.0 + 0.10*p + punch, 0.0, 0.02*p
    elif style == "out":      scale, px, py = max(1.0, 1.16 - 0.09*p + punch), 0.02*(1-p), 0.0
    elif style == "pan_left": scale, px, py = 1.08 + punch, -0.04*p, 0.0
    else:                     scale, px, py = 1.08 + punch,  0.04*p, 0.0
    scale = max(1.01, scale)
    cx = int(W/2 + px*W); cy = int(H/2 + py*H)
    cw = int(W/scale);    ch = int(H/scale)
    x1 = max(0, min(cx - cw//2, W - cw))
    y1 = max(0, min(cy - ch//2, H - ch))
    return np.array(Image.fromarray(bg_np[y1:y1+ch, x1:x1+cw]).resize((W, H), Image.LANCZOS))


def _chromatic_glitch(frame, t, seg_start, intensity=9):
    pt = t - seg_start
    if pt < 0 or pt >= 0.07: return frame
    s = max(1, int(intensity * (1.0 - pt / 0.07) ** 1.5))
    out = frame.copy()
    out[:, :W-s, 0] = frame[:, s:,   0]
    out[:, s:,   2] = frame[:, :W-s, 2]
    return out


def _vignette(frame, top_a=0.35, bot_a=0.68, vstr=0.44):
    grad   = np.linspace(top_a, bot_a, H, dtype=np.float32)
    result = frame.astype(np.float32) * (1 - grad[:, None, None])
    yi = np.linspace(-1, 1, H, dtype=np.float32)
    xi = np.linspace(-1, 1, W, dtype=np.float32)
    xx, yy = np.meshgrid(xi, yi)
    mask = np.clip(1.0 - np.sqrt(xx**2 + yy**2) * vstr, 0.18, 1.0)
    return (result * mask[:, :, None]).astype(np.uint8)


def _color_grade(frame):
    f   = frame.astype(np.float32) / 255.0
    lum = 0.299*f[:,:,0] + 0.587*f[:,:,1] + 0.114*f[:,:,2]
    sh = np.clip(1.0 - lum * 2.8, 0, 1)[:,:,None]
    f[:,:,0] -= sh[:,:,0] * 0.06; f[:,:,1] += sh[:,:,0] * 0.03; f[:,:,2] += sh[:,:,0] * 0.08
    hi = np.clip(lum * 2.2 - 1.0, 0, 1)[:,:,None]
    f[:,:,0] += hi[:,:,0] * 0.09; f[:,:,2] -= hi[:,:,0] * 0.05
    f = np.clip(f * 1.08 - 0.03, 0, 1)
    f = np.clip(f + (f - 0.5) * 0.12, 0, 1)
    gray = (0.299*f[:,:,0] + 0.587*f[:,:,1] + 0.114*f[:,:,2])[:,:,None]
    f    = np.clip(gray + (f - gray) * 1.20, 0, 1)
    return (f * 255).astype(np.uint8)


def _light_leak(frame, t, seg_start):
    dt = t - seg_start
    if dt < 0 or dt >= 0.22: return frame
    intensity = math.sin(dt / 0.22 * math.pi) * 0.52
    leak = np.zeros((H, W, 3), dtype=np.float32)
    for row in range(0, H, 2):
        cx  = int(W * 0.84 - row * 0.11)
        hw  = int(W * 0.20)
        x1, x2 = max(0, cx-hw), min(W, cx+hw)
        if x1 < x2:
            fade = max(0, 1.0 - abs(row/H - 0.28) * 2.5)
            leak[row, x1:x2, 0] = 255 * fade
            leak[row, x1:x2, 1] = 195 * fade
            leak[row, x1:x2, 2] = 75  * fade
    return np.clip(frame.astype(np.float32) + leak * intensity, 0, 255).astype(np.uint8)


def _gradient_bg(t):
    bg    = np.zeros((H, W, 3), dtype=np.uint8)
    y     = np.arange(H, dtype=np.float32)
    pulse = 0.5 + 0.5 * math.sin(t * 1.5)
    bg[:, :, 0] = np.clip(15 + 30*y[:,None]/H + 12*pulse, 0, 65).astype(np.uint8)
    bg[:, :, 2] = np.clip(8  + 12*y[:,None]/H,            0, 22).astype(np.uint8)
    return bg

# ─── Text helpers ─────────────────────────────────────────────────────────────

def _tw(draw, text, font):
    bb = draw.textbbox((0,0), text, font=font)
    return bb[2]-bb[0], bb[3]-bb[1]

def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if _tw(draw, test, font)[0] <= max_w: cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def _stroke(draw, text, x, y, font, color, sw=6, sc=(0,0,0)):
    for dx in range(-sw, sw+1, 2):
        for dy in range(-sw, sw+1, 2):
            if dx or dy: draw.text((x+dx, y+dy), text, fill=sc, font=font)
    draw.text((x, y), text, fill=color, font=font)

def _text_card(img_rgb, x1, y1, x2, y2, radius=22, alpha=158):
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    ImageDraw.Draw(ov).rounded_rectangle([x1,y1,x2,y2], radius=radius, fill=(0,0,0,alpha))
    return Image.alpha_composite(img_rgb.convert("RGBA"), ov).convert("RGB")

# ─── NEW EFFECT 1: Neon glow on stat lines ────────────────────────────────────

def _neon_stroke(draw, text, x, y, font, glow_color, sw=6):
    """Electric neon glow: coloured outer glow + bright white core."""
    gr, gg, gb = glow_color
    for radius in (12, 7, 4):
        a = max(30, 90 - radius * 5)
        for dx in range(-radius, radius+1, 2):
            for dy in range(-radius, radius+1, 2):
                if dx or dy:
                    draw.text((x+dx, y+dy), text, fill=(gr, gg, gb, a), font=font)
    _stroke(draw, text, x, y, font, (255, 255, 255), sw=sw, sc=(0,0,0))

# ─── NEW EFFECT 2: Spotlight sweep ───────────────────────────────────────────

def _spotlight_sweep(img, t, seg_start):
    """Diagonal light beam sweeping across at section transitions."""
    dt = t - seg_start
    if dt < 0 or dt > 0.55: return img
    intensity = math.sin(dt / 0.55 * math.pi) * 0.18
    if intensity < 0.01: return img
    arr = np.array(img).astype(np.float32)
    beam_x = int(W * (-0.2 + dt / 0.55 * 1.4))
    beam_w = 180
    for col in range(max(0, beam_x - beam_w), min(W, beam_x + beam_w)):
        fade = max(0.0, 1.0 - abs(col - beam_x) / beam_w) ** 2
        arr[:, col, :] = np.clip(arr[:, col, :] + 255 * intensity * fade, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))

# ─── NEW EFFECT 3: Pulsing border on text card ───────────────────────────────

def _pulsing_border(img_rgba, x1, y1, x2, y2, t, color):
    pulse = 0.5 + 0.5 * math.sin(t * 5.5)
    alpha = int(80 + 140 * pulse)
    r, g, b = color
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    for thickness, a_mul in [(4, 1.0), (8, 0.4), (14, 0.15)]:
        d.rounded_rectangle([x1-thickness, y1-thickness, x2+thickness, y2+thickness],
                            radius=28, outline=(r, g, b, int(alpha * a_mul)), width=2)
    return Image.alpha_composite(img_rgba, ov)

# ─── NEW EFFECT 4: Bloomberg scrolling ticker ─────────────────────────────────

def _scrolling_ticker(img, t, headline, banner_color=(215, 0, 0)):
    TICKER_Y = H - 52
    TICKER_H = 52
    br, bg_c, bb = banner_color

    ov   = Image.new("RGBA", (W, H), (0,0,0,0))
    d    = ImageDraw.Draw(ov)

    # Background strip
    d.rectangle([0, TICKER_Y, W, H], fill=(8, 8, 8, 230))
    d.line([0, TICKER_Y, W, TICKER_Y], fill=(br, bg_c, bb, 255), width=3)

    # Channel label box (left)
    d.rectangle([0, TICKER_Y, 170, H], fill=(br, bg_c, bb, 255))
    lf = _f(26, display=True)
    label_w, _ = _tw(d, "MARKETS", lf)
    d.text(((170 - label_w)//2, TICKER_Y + 13), "MARKETS",
           fill=(255, 255, 255, 255), font=lf)

    # Scrolling headline text
    tf   = _f(26, bold=False)
    text = f"  ●  {headline}  ●  {headline}  ●  {headline}  "
    tw_, _ = _tw(d, text, tf)
    speed = 80   # pixels per second
    offset = int(t * speed) % max(tw_, W)
    d.text((175 + (W - offset), TICKER_Y + 13), text,
           fill=(220, 220, 220, 240), font=tf)

    merged = Image.alpha_composite(img.convert("RGBA"), ov)
    return merged.convert("RGB")

# ─── Lower third ──────────────────────────────────────────────────────────────

def _lower_third(img_rgb, company, source, t, seg_start, banner_color):
    DELAY, SLIDE, HOLD, FADE = 0.38, 0.32, 3.2, 0.22
    dt = t - seg_start - DELAY
    if dt < 0: return img_rgb
    if   dt < SLIDE:            x_off, alpha = int((1-(dt/SLIDE)**0.4*(3-2*dt/SLIDE)) * -(W+60)), 255
    elif dt < SLIDE + HOLD:     x_off, alpha = 0, 255
    elif dt < SLIDE+HOLD+FADE:  x_off, alpha = 0, int(255*(1-(dt-SLIDE-HOLD)/FADE))
    else: return img_rgb
    if alpha <= 0: return img_rgb

    LT_Y, LT_H, BAR = H - 448, 88, 12
    br, bg_c, bb = banner_color
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    d.rounded_rectangle([x_off, LT_Y, x_off+W-36, LT_Y+LT_H],
                        radius=8, fill=(6, 6, 22, int(alpha*0.90)))
    d.rounded_rectangle([x_off, LT_Y, x_off+BAR, LT_Y+LT_H],
                        radius=4, fill=(br, bg_c, bb, alpha))
    d.text((x_off+BAR+16, LT_Y+7),  company[:30].upper(),
           fill=(255,255,255,alpha), font=_f(40, display=True))
    d.text((x_off+BAR+16, LT_Y+54), source[:38],
           fill=(170,170,170,alpha), font=_f(28))
    bx = x_off + W - 110
    d.rounded_rectangle([bx, LT_Y+20, bx+70, LT_Y+68],
                        radius=6, fill=(br, bg_c, bb, alpha))
    d.text((bx+9, LT_Y+28), "LIVE", fill=(255,255,255,alpha), font=_f(26))
    return Image.alpha_composite(img_rgb.convert("RGBA"), ov).convert("RGB")

# ─── Frame builder (picklable for multiprocessing) ───────────────────────────

_KB_STYLES = ["in", "out", "pan_left", "pan_right"]


class FrameBuilder:
    """Stateless callable — one instance per worker process."""

    def __init__(self, bg_paths, segments, source, title, duration,
                 headline="", banner_color=None, cta_color=None, ticker_color=None):
        self.bgs = {}
        for itype, path in (bg_paths or {}).items():
            if path and os.path.exists(str(path)):
                try:    self.bgs[itype] = _load_bg(path)
                except: pass

        self._banner   = tuple(banner_color)  if banner_color  else (215, 0, 0)
        self._cta      = tuple(cta_color)     if cta_color     else (180, 0, 0)
        self._ticker   = tuple(ticker_color)  if ticker_color  else (255, 215, 0)
        self.segments  = segments
        self.source    = source
        self.title     = title
        self.duration  = duration
        self.headline  = headline or title
        self._kb       = {i: _KB_STYLES[i % 4] for i in range(len(segments))}
        self._company  = " ".join(title.split()[:4])

    def _current(self, t):
        for s in self.segments:
            if s["start"] <= t < s["end"]: return s
        return self.segments[-1] if self.segments else {"text":"","start":0,"end":1,"image_type":"breaking"}

    def _raw_bg(self, itype):
        bg = self.bgs.get(itype)
        return bg if bg is not None else (next(iter(self.bgs.values()), None))

    def _build_bg(self, t, seg):
        itype = seg.get("image_type", "breaking")
        try:   idx = self.segments.index(seg)
        except: idx = 0
        style   = self._kb.get(idx, "in")
        cur_np  = self._raw_bg(itype)
        cur     = _ken_burns(cur_np, t, seg["start"], self.duration, style) \
                  if cur_np is not None else _gradient_bg(t)

        # Crossfade
        prev_itype = None
        for s in self.segments:
            if s["end"] <= seg["start"]: prev_itype = s.get("image_type","breaking")
        if prev_itype and prev_itype != itype:
            a = min(1.0, (t - seg["start"]) / 0.32)
            if a < 1.0:
                p_np = self._raw_bg(prev_itype)
                prev = _ken_burns(p_np, t, seg["start"], self.duration, style) \
                       if p_np is not None else _gradient_bg(t)
                cur  = ((1-a)*prev.astype(np.float32) + a*cur.astype(np.float32)).astype(np.uint8)

        cur = _chromatic_glitch(cur, t, seg["start"])
        return cur

    def __call__(self, t):
        seg   = self._current(t)
        itype = seg.get("image_type","breaking")
        fn    = int(round(t * VIDEO_FPS))
        text  = seg.get("text","")

        # ── BACKGROUND ──────────────────────────────────────────────────────
        frame = self._build_bg(t, seg)
        frame = fx.depth_of_field(frame, blur_radius=4)
        frame = _color_grade(frame)
        frame = fx.color_mood(frame, itype, text)
        frame = fx.radial_zoom_blur(frame, t, seg["start"])
        frame = _light_leak(frame, t, seg["start"])
        frame = _vignette(frame)
        frame = fx.film_grain(frame, fn)
        img   = Image.fromarray(frame)

        # ── NEW: Spotlight sweep ─────────────────────────────────────────────
        img = _spotlight_sweep(img, t, seg["start"])

        # ── PARTICLES ───────────────────────────────────────────────────────
        img = fx.draw_money_rain(img, t, count=14)
        # Bullish/bearish emoji rain
        img = fx.emoji_rain(img, t, itype, text)

        draw = ImageDraw.Draw(img)

        # ── BANNER (top) ─────────────────────────────────────────────────────
        br, bg_c, bb = self._banner
        flash = int(t * 3) % 2 == 0
        b_col = self._banner if flash else (max(0, br-55), bg_c, bb)
        draw.rectangle([0, 0, W, 86], fill=b_col)
        for sx in range(-40, W+40, 46):
            off = int(t*75) % 46
            draw.polygon([(sx+off,0),(sx+off+20,0),(sx+off+13,86),(sx+off-7,86)],
                         fill=(min(255,br+60), int(12+8*math.sin(t*5+sx*0.12)), bb))
        dot = (255,255,255) if flash else (255,70,70)
        draw.ellipse([16,26,42,52], fill=dot)
        bw, _ = _tw(draw, "BREAKING NEWS", _f(52, display=True))
        _stroke(draw, "BREAKING NEWS", (W-bw)//2, 17, _f(52,display=True), (255,255,255), sw=3)
        draw.text((56, 20), "LIVE", fill=(255,255,255), font=_f(26))

        # ── SOURCE STRIP ─────────────────────────────────────────────────────
        draw.rectangle([0, 86, W, 128], fill=(10, 0, 0))
        draw.line([0, 86, W, 86], fill=self._ticker, width=3)
        draw.text((18, 93), f"{self.source}  |  Global Markets  |  Live Update",
                  fill=(210,210,0), font=_f(27))

        # ── CHART WIDGET ─────────────────────────────────────────────────────
        img  = fx.draw_chart_widget(img, t, seg["start"], x=662, y=135, w=398, h=218)
        draw = ImageDraw.Draw(img)

        # ── SECTION TEXT ─────────────────────────────────────────────────────
        anim = min(1.0, (t - seg["start"]) * 7)
        ease = 1.0 - (1.0 - anim) ** 3
        cc   = len(text)
        fs   = 108 if cc <= 12 else 88 if cc <= 22 else 70 if cc <= 38 else 56
        mfont = _f(fs, display=True)
        lines = _wrap(draw, text, mfont, W - 100)
        lh    = fs + 22
        th    = len(lines) * lh
        cy    = H // 2 - th // 2 - 55

        x_off, y_off = 0, 0
        if   itype == "breaking": x_off = int((1-ease) * -165)
        elif itype == "company":  x_off = int((1-ease) *  165)
        elif itype == "market":   y_off = int((1-ease) *  115)
        else:                     y_off = int((1-ease) * -95)
        sy = cy + y_off
        pad = 30

        # Pulsing border card
        img_rgba = img.convert("RGBA")
        img_rgba = _pulsing_border(img_rgba, 34-pad, sy-pad, W-34+pad, sy+th+pad,
                                   t, self._banner)
        img = _text_card(img_rgba.convert("RGB"), 34-pad, sy-pad, W-34+pad, sy+th+pad, alpha=155)
        draw = ImageDraw.Draw(img)

        for i, line in enumerate(lines):
            if _is_stat(line):
                # NEW: neon glow on stat lines
                pw, _ = _tw(draw, line, mfont)
                img_rgba2 = img.convert("RGBA")
                d2 = ImageDraw.Draw(img_rgba2)
                _neon_stroke(d2, line, (W-pw)//2+x_off, sy+i*lh, mfont, (255, 215, 0))
                img  = img_rgba2.convert("RGB")
                draw = ImageDraw.Draw(img)
            else:
                pw, _ = _tw(draw, line, mfont)
                _stroke(draw, line, (W-pw)//2+x_off, sy+i*lh, mfont, (255,255,255), sw=7)

        # ── COUNTER (breaking) ───────────────────────────────────────────────
        if itype == "breaking":
            stat = fx.extract_stat(lines)
            if stat:
                val, unit, label = stat
                img  = fx.draw_counter(img, val, unit, label, t, seg["start"],
                                       cx=W//2, cy=sy+th+40)
                draw = ImageDraw.Draw(img)

        # ── LENS FLARE ───────────────────────────────────────────────────────
        img  = fx.anamorphic_flare(img, t, seg["start"], self._banner)
        draw = ImageDraw.Draw(img)

        # ── LOWER THIRD ──────────────────────────────────────────────────────
        img  = _lower_third(img, self._company, self.source, t, seg["start"], self._banner)
        draw = ImageDraw.Draw(img)

        # ── CTA BAR ──────────────────────────────────────────────────────────
        by = H - 144
        pr = 0.5 + 0.5 * math.sin(t * 4.2)
        cr, cg, cb = self._cta
        draw.rectangle([0, by, W, H - 52], fill=(int(cr+(255-cr)*0.22*pr), cg, cb))
        for sx in range(-28, W+28, 40):
            off = int(t*52) % 40
            draw.polygon([(sx+off,by),(sx+off+16,by),(sx+off+10,H-52),(sx+off-6,H-52)],
                         fill=(min(255,cr+35), cg, cb))
        ctaf   = _f(46, display=True)
        ctatxt = "LIKE  |  SUBSCRIBE  |  SHARE"
        cw, _  = _tw(draw, ctatxt, ctaf)
        _stroke(draw, ctatxt, (W-cw)//2, by+34, ctaf, (255,255,255), sw=4)

        # ── NEW: Scrolling ticker (bottom strip) ──────────────────────────────
        img = _scrolling_ticker(img, t, self.headline, self._banner)

        # ── PROGRESS BAR ─────────────────────────────────────────────────────
        draw = ImageDraw.Draw(img)
        pw_  = int(W * t / max(self.duration, 0.01))
        draw.rectangle([0, 0, W,   5], fill=(25, 25, 25))
        draw.rectangle([0, 0, pw_, 5], fill=self._ticker)

        # ── POST: BLOOM + HALATION ────────────────────────────────────────────
        img = fx.bloom(img, radius=12, strength=0.40)
        img = fx.film_halation(img, strength=0.24)

        return np.array(img)

# ─── Multiprocessing worker ───────────────────────────────────────────────────

def _worker(args):
    """Render a range of frames and write raw RGB to a temp file."""
    (chunk_id, start_f, end_f, fps,
     bg_paths, segments, source, title, duration, headline,
     banner, cta, ticker, tmp_dir) = args

    builder = FrameBuilder(bg_paths=bg_paths, segments=segments,
                           source=source, title=title, duration=duration,
                           headline=headline, banner_color=banner,
                           cta_color=cta, ticker_color=ticker)

    out_path = os.path.join(tmp_dir, f"chunk_{chunk_id:03d}.raw")
    with open(out_path, "wb") as f:
        for i in range(start_f, end_f):
            t     = i / fps
            frame = builder(t)        # returns (H, W, 3) uint8
            f.write(frame.tobytes())
    return out_path

# ─── FFmpeg helpers ───────────────────────────────────────────────────────────

def _ffmpeg():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        return "ffmpeg"


def _fit_audio(audio_path, target_dur):
    from moviepy import AudioFileClip
    actual = AudioFileClip(audio_path).duration
    if actual <= target_dur + 0.5: return audio_path
    factor = actual / target_dur
    af  = f"atempo={factor:.4f}" if factor <= 2.0 else f"atempo=2.0,atempo={factor/2.0:.4f}"
    out = audio_path.replace(".mp3", "_fit.mp3")
    subprocess.run([_ffmpeg(), "-y", "-i", audio_path, "-filter:a", af, out],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    from moviepy import AudioFileClip as AC
    print(f"  Audio: {actual:.1f}s -> {AC(out).duration:.1f}s  ({factor:.2f}x)")
    return out

# ─── Main entry point ─────────────────────────────────────────────────────────

def create_video(story, script, segments, audio_path, output_path,
                 section_images=None, target_duration=None,
                 banner_color=None, cta_color=None,
                 ticker_color=None, overlay_opacity=None):

    from moviepy import AudioFileClip
    audio    = AudioFileClip(audio_path)
    duration = audio.duration

    if target_duration and duration > target_duration + 0.5:
        audio_path = _fit_audio(audio_path, target_duration)
        audio      = AudioFileClip(audio_path)
        duration   = audio.duration

    # Scale segment timings to match audio duration
    if segments:
        total = segments[-1]["end"]
        scale = duration / total if total > 0 else 1.0
        for seg in segments:
            seg["start"] *= scale
            seg["end"]   *= scale

    if not section_images:
        single = story.get("image")
        section_images = {t: single for t in ["breaking","company","market","cta"]}

    # Resolve bg_paths (str paths only, for pickling)
    bg_paths = {k: str(v) for k, v in (section_images or {}).items() if v}

    total_frames = int(duration * VIDEO_FPS)
    num_workers  = min(mp.cpu_count(), 6)
    chunk_size   = math.ceil(total_frames / num_workers)

    headline = story.get("title", "")
    source   = story.get("source", story.get("src", "Markets"))
    title    = story.get("title", "")
    banner   = tuple(banner_color)  if banner_color  else (215, 0, 0)
    cta      = tuple(cta_color)     if cta_color     else (180, 0, 0)
    ticker   = tuple(ticker_color)  if ticker_color  else (255, 215, 0)

    print(f"  Rendering {duration:.1f}s @ {VIDEO_FPS}fps -> {W}x{H}  "
          f"({total_frames} frames, {num_workers} workers)...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Build worker args
        worker_args = []
        for i in range(num_workers):
            sf = i * chunk_size
            ef = min(sf + chunk_size, total_frames)
            if sf >= total_frames: break
            worker_args.append((
                i, sf, ef, VIDEO_FPS,
                bg_paths, segments, source, title, duration, headline,
                banner, cta, ticker, tmp_dir
            ))

        # Render in parallel
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=len(worker_args)) as pool:
            chunk_files = pool.map(_worker, worker_args)

        # Pipe raw chunks to ffmpeg for encoding
        print(f"  Encoding with ffmpeg ({len(chunk_files)} chunks)...")
        ffmpeg_cmd = [
            _ffmpeg(), "-y",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}", "-pix_fmt", "rgb24",
            "-r", str(VIDEO_FPS), "-i", "pipe:0",
            "-i", audio_path,
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path
        ]

        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for chunk_file in chunk_files:
            with open(chunk_file, "rb") as f:
                while True:
                    data = f.read(4 * 1024 * 1024)  # 4 MB at a time
                    if not data: break
                    proc.stdin.write(data)
        proc.stdin.close()
        proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg encoding failed (exit {proc.returncode})")

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"  Done -> {output_path}  ({size_mb:.1f} MB)")
    return output_path
