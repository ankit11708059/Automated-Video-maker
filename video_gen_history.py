"""
Cinematic atmospheric video renderer for the Lost History channel.

Designed for VISUAL UNPREDICTABILITY — each video randomises:
  • Style preset    (4 options): sepia / cold_mystery / crimson / ethereal
  • Transition type (4 options): crossfade / black_flash / zoom_punch / light_leak
  • Text animation  (3 options): slide_up_fade / slow_glow / drift_down
  • Card position   (3 options): top / middle / bottom
  • Zoom pattern    (4 options): in / out / pan_lr / pan_rl

Random selection is seeded by the topic name so a given topic always renders
identically (helpful for debugging), but different topics get different feels.

The renderer also accepts a `visual_style` hint from script_gen_history.
"""

import os
import math
import random
import hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (AudioFileClip, ImageClip, ColorClip, CompositeVideoClip,
                     concatenate_videoclips, VideoClip)
from moviepy.video.fx import FadeIn, FadeOut, CrossFadeIn

from config import VIDEO_WIDTH as W, VIDEO_HEIGHT as H, VIDEO_FPS


# ─── Style presets ───────────────────────────────────────────────────────────
# Each preset is (sepia_matrix, blend_ratio, vignette_strength, text_color, border_color)
STYLE_PRESETS = {
    "sepia": {
        "matrix": np.array([
            [0.45, 0.50, 0.20],
            [0.40, 0.55, 0.20],
            [0.30, 0.45, 0.15],
        ]),
        "blend": 0.60,
        "channel_mult": (1.04, 1.00, 0.92),
        "vignette": 0.55,
        "text": (245, 230, 205),
        "border": (212, 175, 55),
        "ink": (16, 10, 4),
    },
    "cold_mystery": {
        "matrix": np.array([
            [0.30, 0.35, 0.45],
            [0.25, 0.40, 0.45],
            [0.30, 0.45, 0.50],
        ]),
        "blend": 0.55,
        "channel_mult": (0.85, 0.95, 1.10),
        "vignette": 0.68,
        "text": (220, 232, 245),
        "border": (160, 190, 220),
        "ink": (6, 10, 18),
    },
    "crimson": {
        "matrix": np.array([
            [0.55, 0.30, 0.15],
            [0.35, 0.30, 0.15],
            [0.30, 0.25, 0.15],
        ]),
        "blend": 0.60,
        "channel_mult": (1.10, 0.85, 0.80),
        "vignette": 0.72,
        "text": (250, 220, 200),
        "border": (200, 60, 50),
        "ink": (16, 4, 4),
    },
    "ethereal": {
        "matrix": np.array([
            [0.40, 0.30, 0.50],
            [0.35, 0.40, 0.50],
            [0.40, 0.40, 0.60],
        ]),
        "blend": 0.55,
        "channel_mult": (0.95, 0.95, 1.15),
        "vignette": 0.60,
        "text": (235, 220, 250),
        "border": (170, 140, 220),
        "ink": (12, 8, 22),
    },
}


TRANSITION_TYPES   = ["crossfade", "black_flash", "zoom_punch", "light_leak"]
TEXT_ANIMATIONS    = ["slide_up_fade", "slow_glow", "drift_down"]
CARD_POSITIONS     = ["top", "middle", "bottom"]
ZOOM_PATTERNS      = ["in", "out", "pan_lr", "pan_rl"]


# ─── Fonts ───────────────────────────────────────────────────────────────────
def _find_serif():
    for p in [
        r"C:\Windows\Fonts\georgiab.ttf",
        r"C:\Windows\Fonts\georgia.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ]:
        if os.path.exists(p):
            return p
    return None

_SERIF = _find_serif()


def _serif(size):
    if _SERIF:
        try:
            return ImageFont.truetype(_SERIF, size)
        except Exception:
            pass
    return ImageFont.load_default()


# ─── Color grade ─────────────────────────────────────────────────────────────
def _apply_style(arr: np.ndarray, preset: dict) -> np.ndarray:
    rgb = arr.astype(np.float32)
    toned = rgb @ preset["matrix"].T
    out = toned * preset["blend"] + rgb * (1 - preset["blend"])
    mr, mg, mb = preset["channel_mult"]
    out[..., 0] *= mr
    out[..., 1] *= mg
    out[..., 2] *= mb
    return np.clip(out, 0, 255).astype(np.uint8)


def _vignette_mask(h: int, w: int, strength: float) -> np.ndarray:
    cx, cy = w / 2, h / 2
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    max_d = math.sqrt(cx ** 2 + cy ** 2)
    mask = 1 - (dist / max_d) ** 2 * strength
    return np.clip(mask, 0.20, 1.0)


def _load_and_grade(path: str, target_w: int, target_h: int,
                    preset: dict) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    sw, sh = img.size
    ratio = target_w / target_h
    if sw / sh > ratio:
        new_w = int(sh * ratio)
        left = (sw - new_w) // 2
        img = img.crop((left, 0, left + new_w, sh))
    else:
        new_h = int(sw / ratio)
        top = (sh - new_h) // 2
        img = img.crop((0, top, sw, top + new_h))
    img = img.resize((target_w, target_h), Image.LANCZOS)
    arr = np.array(img)
    arr = _apply_style(arr, preset)
    mask = _vignette_mask(target_h, target_w, preset["vignette"])
    arr = (arr * mask[..., np.newaxis]).astype(np.uint8)
    return arr


# ─── Text card ───────────────────────────────────────────────────────────────
def _render_text_card(lines: list[str], preset: dict) -> np.ndarray:
    card_w = int(W * 0.88)
    pad = 38
    line_h = 84
    card_h = pad * 2 + len(lines) * line_h + 16

    img = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    ink = preset["ink"]
    border = preset["border"]
    text_color = preset["text"]

    draw.rounded_rectangle((0, 0, card_w, card_h), radius=20,
                           fill=ink + (215,))
    draw.rounded_rectangle((0, 0, card_w, card_h), radius=20,
                           outline=border + (255,), width=2)
    inset = 9
    draw.rounded_rectangle(
        (inset, inset, card_w - inset, card_h - inset),
        radius=14, outline=border + (170,), width=1,
    )
    for cx, cy in [(20, 20), (card_w - 20, 20),
                   (20, card_h - 20), (card_w - 20, card_h - 20)]:
        draw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3),
                     fill=border + (255,))

    font = _serif(58)
    y = pad + 6
    for line in lines:
        line = str(line)[:34]
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (card_w - tw) // 2
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 230))
        draw.text((x, y), line, font=font, fill=text_color + (255,))
        y += line_h

    return np.array(img)


def _card_y_for_position(position: str, card_h: int) -> int:
    if position == "top":
        return int(H * 0.08)
    if position == "middle":
        return (H - card_h) // 2
    return int(H * 0.60)  # bottom


# ─── Per-section clip with random zoom pattern ───────────────────────────────
def _section_clip(image_path: str, lines: list[str], duration: float,
                  preset: dict, zoom_pattern: str, text_anim: str,
                  card_position: str) -> CompositeVideoClip:
    src_w = int(W * 1.22)
    src_h = int(H * 1.22)
    base_arr = _load_and_grade(image_path, src_w, src_h, preset)

    # Decide zoom & pan parameters from pattern
    if zoom_pattern == "in":
        z_from, z_to = 1.0, 1.14
        pan_x_amp, pan_y_amp = 18, 12
    elif zoom_pattern == "out":
        z_from, z_to = 1.14, 1.0
        pan_x_amp, pan_y_amp = 18, 12
    elif zoom_pattern == "pan_lr":
        z_from = z_to = 1.10
        pan_x_amp, pan_y_amp = 55, 0
    else:  # pan_rl
        z_from = z_to = 1.10
        pan_x_amp, pan_y_amp = -55, 0

    def make_frame(t: float) -> np.ndarray:
        p = min(t / duration, 1.0)
        scale = z_from + (z_to - z_from) * p
        crop_w = int(src_w / scale)
        crop_h = int(src_h / scale)
        if zoom_pattern in ("pan_lr", "pan_rl"):
            pan_x = int((p - 0.5) * 2 * pan_x_amp)
            pan_y = 0
        else:
            pan_x = int(math.sin(p * math.pi * 0.6) * pan_x_amp)
            pan_y = int(math.cos(p * math.pi * 0.4) * pan_y_amp)
        left = max(0, min(src_w - crop_w, (src_w - crop_w) // 2 + pan_x))
        top  = max(0, min(src_h - crop_h, (src_h - crop_h) // 2 + pan_y))
        crop = base_arr[top:top + crop_h, left:left + crop_w]
        out = Image.fromarray(crop).resize((W, H), Image.LANCZOS)
        return np.array(out)

    video = VideoClip(make_frame, duration=duration)

    # Text card with chosen position + animation
    card = _render_text_card(lines, preset)
    card_h = card.shape[0]
    card_x = (W - card.shape[1]) // 2
    card_y = _card_y_for_position(card_position, card_h)

    card_clip = ImageClip(card).with_duration(duration)

    if text_anim == "slide_up_fade":
        # Slides up from 40px below final position, fades in
        slide_dist = 40
        def pos_fn(t):
            p = min(t / 0.6, 1.0)
            return (card_x, int(card_y + (1 - p) * slide_dist))
        card_clip = (card_clip
                     .with_position(pos_fn)
                     .with_effects([FadeIn(0.6), FadeOut(0.4)]))
    elif text_anim == "drift_down":
        slide_dist = 40
        def pos_fn(t):
            p = min(t / 0.6, 1.0)
            return (card_x, int(card_y - (1 - p) * slide_dist))
        card_clip = (card_clip
                     .with_position(pos_fn)
                     .with_effects([FadeIn(0.6), FadeOut(0.4)]))
    else:  # slow_glow — no motion, longer fade
        card_clip = (card_clip
                     .with_position((card_x, card_y))
                     .with_effects([FadeIn(0.9), FadeOut(0.5)]))

    return CompositeVideoClip([video, card_clip], size=(W, H))


# ─── Transition builders ─────────────────────────────────────────────────────
def _black_clip(duration: float) -> ColorClip:
    return ColorClip(size=(W, H), color=(0, 0, 0), duration=duration)


def _flash_clip(duration: float, color: tuple) -> ColorClip:
    return (ColorClip(size=(W, H), color=color, duration=duration)
            .with_effects([FadeIn(duration / 2), FadeOut(duration / 2)]))


def _concat_with_transition(clips: list, transition: str):
    """Concatenate clips applying a chosen transition style between them."""
    if transition == "crossfade":
        out = []
        d = 0.7
        for i, c in enumerate(clips):
            if i > 0:
                c = c.with_effects([CrossFadeIn(d)])
            out.append(c)
        return concatenate_videoclips(out, method="compose", padding=-d)

    if transition == "black_flash":
        out = []
        for i, c in enumerate(clips):
            out.append(c.with_effects([FadeIn(0.25), FadeOut(0.25)]))
            if i < len(clips) - 1:
                out.append(_black_clip(0.18))
        return concatenate_videoclips(out, method="compose")

    if transition == "zoom_punch":
        # Each clip cross-fades in over 0.35s while the previous fades out;
        # a brief white flash punctuates the cut.
        out = []
        d = 0.35
        for i, c in enumerate(clips):
            if i > 0:
                c = c.with_effects([CrossFadeIn(d)])
            out.append(c)
        joined = concatenate_videoclips(out, method="compose", padding=-d)
        # Overlay brief white flashes at each cut
        flashes = []
        offset = 0.0
        for i, c in enumerate(clips[:-1]):
            offset += c.duration - d
            flash = (_flash_clip(0.18, (255, 240, 220))
                     .with_start(offset)
                     .with_opacity(0.55))
            flashes.append(flash)
        return CompositeVideoClip([joined] + flashes, size=(W, H))

    if transition == "light_leak":
        # Warm orange flash overlay at transition points
        out = []
        d = 0.55
        for i, c in enumerate(clips):
            if i > 0:
                c = c.with_effects([CrossFadeIn(d)])
            out.append(c)
        joined = concatenate_videoclips(out, method="compose", padding=-d)
        leaks = []
        offset = 0.0
        for i, c in enumerate(clips[:-1]):
            offset += c.duration - d
            leak = (_flash_clip(0.35, (255, 180, 90))
                    .with_start(offset - 0.1)
                    .with_opacity(0.40))
            leaks.append(leak)
        return CompositeVideoClip([joined] + leaks, size=(W, H))

    # Default
    return concatenate_videoclips(clips, method="compose")


# ─── Public API ──────────────────────────────────────────────────────────────
def sections_to_segments(sections: list[dict], audio_duration: float) -> list[dict]:
    weights = [s.get("time_weight", len(s.get("lines", []))) or 1 for s in sections]
    total_w = sum(weights) or 1
    segments = []
    elapsed = 0.0
    for sec, w in zip(sections, weights):
        dur = (w / total_w) * audio_duration
        segments.append({
            "image_type": sec.get("image_type", "company"),
            "lines":      sec.get("lines", []),
            "start":      elapsed,
            "end":        elapsed + dur,
        })
        elapsed += dur
    return segments


def _pick_style_from_hint(visual_style: str) -> str:
    return {
        "mystery":      "cold_mystery",
        "discovery":    "sepia",
        "supernatural": "ethereal",
        "conspiracy":   "crimson",
    }.get(visual_style or "mystery", "sepia")


def create_video(story, script, segments, audio_path, output_path,
                 section_images=None, target_duration=None,
                 visual_style: str | None = None,
                 topic_seed: str | None = None,
                 **_unused):
    """
    Cinematic atmospheric history video with randomised, per-video styling.
    """
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    print(f"  Audio duration: {duration:.1f}s")

    if not section_images:
        raise ValueError("section_images required")

    # Seeded RNG — same topic always renders the same way
    seed_src = (topic_seed or story.get("title", "") or "history").encode()
    seed = int(hashlib.md5(seed_src).hexdigest(), 16) & 0xFFFFFFFF
    rng = random.Random(seed)

    # Style is hinted by Claude but with a 20% chance of random override
    base_style = _pick_style_from_hint(visual_style)
    if rng.random() < 0.20:
        base_style = rng.choice(list(STYLE_PRESETS.keys()))
    preset = STYLE_PRESETS[base_style]

    transition  = rng.choice(TRANSITION_TYPES)
    text_anim   = rng.choice(TEXT_ANIMATIONS)
    card_pos    = rng.choice(CARD_POSITIONS)

    # Per-section unique zoom patterns
    zoom_patterns = rng.sample(ZOOM_PATTERNS, k=min(4, len(ZOOM_PATTERNS)))

    print(f"  Style: {base_style}  Transition: {transition}  TextAnim: {text_anim}  Card: {card_pos}")
    print(f"  Zoom patterns: {zoom_patterns}")

    # Each transition shifts the relationship between clip durations and final video length.
    # Overlapping transitions need extra clip length; black_flash inserts gaps so clips must be shorter.
    OVERLAP_PER_T = {
        "crossfade":   0.7,
        "zoom_punch":  0.35,
        "light_leak":  0.55,
        "black_flash": -0.18,
    }
    n_segs = len(segments) if segments else 0
    total_overlap = OVERLAP_PER_T.get(transition, 0.0) * max(n_segs - 1, 0)
    target_clip_sum = max(duration + total_overlap, 1.0)

    # Scale segments so their durations sum to target_clip_sum
    if segments:
        original_total = segments[-1]["end"]
        if original_total > 0:
            scale = target_clip_sum / original_total
            for seg in segments:
                seg["start"] *= scale
                seg["end"]   *= scale

    # Build clips
    clips = []
    for i, seg in enumerate(segments):
        img_type = seg.get("image_type", "company")
        img_path = (section_images.get(img_type)
                    or next((p for p in section_images.values() if p), None))
        if not img_path or not os.path.exists(img_path):
            print(f"    WARN: skipping section {i} ({img_type}) — image missing")
            continue
        seg_dur = max(seg["end"] - seg["start"], 1.0)
        clip = _section_clip(
            img_path, seg.get("lines", []), seg_dur,
            preset, zoom_patterns[i % len(zoom_patterns)],
            text_anim, card_pos,
        )
        clips.append(clip)

    if not clips:
        raise RuntimeError("No section clips were built — all images missing?")

    final = _concat_with_transition(clips, transition)
    # Match audio duration exactly
    final = final.with_duration(duration).with_audio(audio)

    print(f"  Rendering {duration:.1f}s cinematic video ({base_style}/{transition})...")
    final.write_videofile(
        output_path,
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        logger=None,
    )
    return output_path
