"""
Cinematic atmospheric video renderer for the Lost History channel.
Style: sepia/parchment palette, slow cinematic zoom, soft vignette,
serif-typeset parchment text cards, crossfade transitions.

Public API matches video_gen.create_video() so it's a drop-in for the
history pipeline.
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (AudioFileClip, ImageClip, CompositeVideoClip,
                     concatenate_videoclips, VideoClip)
from moviepy.video.fx import FadeIn, FadeOut, CrossFadeIn

from config import VIDEO_WIDTH as W, VIDEO_HEIGHT as H, VIDEO_FPS

# ─── Palette ─────────────────────────────────────────────────────────────────
GOLD       = (212, 175, 55)
WARM_TEXT  = (245, 230, 205)
DARK_INK   = (16, 10, 4)


# ─── Fonts (cross-platform serif) ────────────────────────────────────────────
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


# ─── Color grade helpers ─────────────────────────────────────────────────────
def _sepia(arr: np.ndarray) -> np.ndarray:
    """Apply warm sepia tint, blended 60/40 with original for natural feel."""
    rgb = arr.astype(np.float32)
    sepia = np.array([
        [0.45, 0.50, 0.20],
        [0.40, 0.55, 0.20],
        [0.30, 0.45, 0.15],
    ])
    sepia_rgb = rgb @ sepia.T
    out = sepia_rgb * 0.60 + rgb * 0.40
    out[..., 0] *= 1.04
    out[..., 2] *= 0.92
    return np.clip(out, 0, 255).astype(np.uint8)


def _vignette_mask(h: int, w: int, strength: float = 0.55) -> np.ndarray:
    cx, cy = w / 2, h / 2
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    max_d = math.sqrt(cx ** 2 + cy ** 2)
    mask = 1 - (dist / max_d) ** 2 * strength
    return np.clip(mask, 0.25, 1.0)


def _load_and_grade(path: str, target_w: int, target_h: int) -> np.ndarray:
    """Load image, cover-fit, apply sepia + vignette. Returns RGB uint8 array."""
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
    arr = _sepia(arr)

    mask = _vignette_mask(target_h, target_w, 0.55)
    arr = (arr * mask[..., np.newaxis]).astype(np.uint8)
    return arr


# ─── Parchment text card ─────────────────────────────────────────────────────
def _render_text_card(lines: list[str]) -> np.ndarray:
    """RGBA parchment-style card with gold borders and serif text."""
    card_w = int(W * 0.88)
    pad = 38
    line_h = 84
    card_h = pad * 2 + len(lines) * line_h + 16

    img = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark semi-transparent backdrop
    draw.rounded_rectangle((0, 0, card_w, card_h), radius=20,
                           fill=DARK_INK + (215,))

    # Outer gold border
    draw.rounded_rectangle((0, 0, card_w, card_h), radius=20,
                           outline=GOLD + (255,), width=2)
    # Inner thin gold border
    inset = 9
    draw.rounded_rectangle(
        (inset, inset, card_w - inset, card_h - inset),
        radius=14, outline=GOLD + (170,), width=1,
    )

    # Decorative corner dots
    for cx, cy in [(20, 20), (card_w - 20, 20),
                   (20, card_h - 20), (card_w - 20, card_h - 20)]:
        draw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=GOLD + (255,))

    font = _serif(58)
    y = pad + 6
    for line in lines:
        # Clean line — strip if too long
        line = str(line)[:34]
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (card_w - tw) // 2
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 230))
        draw.text((x, y), line, font=font, fill=WARM_TEXT + (255,))
        y += line_h

    return np.array(img)


# ─── Per-section clip ────────────────────────────────────────────────────────
def _section_clip(image_path: str, lines: list[str], duration: float,
                  zoom_dir: int = 1) -> CompositeVideoClip:
    """Slow-zoom + drifting pan image with parchment text card overlay."""
    src_w = int(W * 1.22)
    src_h = int(H * 1.22)
    base_arr = _load_and_grade(image_path, src_w, src_h)

    zoom_from, zoom_to = (1.0, 1.14) if zoom_dir >= 0 else (1.14, 1.0)

    def make_frame(t: float) -> np.ndarray:
        p = min(t / duration, 1.0)
        scale = zoom_from + (zoom_to - zoom_from) * p
        crop_w = int(src_w / scale)
        crop_h = int(src_h / scale)
        # gentle drift
        pan_x = int(math.sin(p * math.pi * 0.6) * 22)
        pan_y = int(math.cos(p * math.pi * 0.4) * 14)
        left = max(0, min(src_w - crop_w, (src_w - crop_w) // 2 + pan_x))
        top  = max(0, min(src_h - crop_h, (src_h - crop_h) // 2 + pan_y))
        crop = base_arr[top:top + crop_h, left:left + crop_w]
        out = Image.fromarray(crop).resize((W, H), Image.LANCZOS)
        return np.array(out)

    video = VideoClip(make_frame, duration=duration)

    card = _render_text_card(lines)
    card_clip = ImageClip(card, is_mask=False).with_duration(duration)
    card_x = (W - card.shape[1]) // 2
    card_y = int(H * 0.60)
    card_clip = (card_clip
                 .with_position((card_x, card_y))
                 .with_effects([FadeIn(0.5), FadeOut(0.4)]))

    return CompositeVideoClip([video, card_clip], size=(W, H))


# ─── Public API ──────────────────────────────────────────────────────────────
def sections_to_segments(sections: list[dict], audio_duration: float) -> list[dict]:
    """
    Convert script sections (one per scene) into section-level timed segments.
    Differs from script_gen.make_timed_segments which flattens to one-per-line.
    """
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


def create_video(story, script, segments, audio_path, output_path,
                 section_images=None, target_duration=None,
                 **_unused):
    """
    Cinematic atmospheric history video.
    Signature mirrors video_gen.create_video so it's a drop-in.
    target_duration is honoured if set (audio is left untouched — video matches audio).
    """
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    print(f"  Audio duration: {duration:.1f}s")

    if not section_images:
        raise ValueError("section_images required for history renderer")

    # Scale segment timings to audio duration
    if segments:
        total = segments[-1]["end"]
        scale = duration / total if total > 0 else 1.0
        for seg in segments:
            seg["start"] *= scale
            seg["end"]   *= scale

    clips = []
    crossfade = 0.8

    for i, seg in enumerate(segments):
        img_type = seg.get("image_type", "company")
        img_path = (section_images.get(img_type)
                    or section_images.get("company")
                    or next((p for p in section_images.values() if p), None))
        if not img_path or not os.path.exists(img_path):
            print(f"    WARN: skipping section {i} ({img_type}) — image missing")
            continue

        seg_dur = max(seg["end"] - seg["start"], 1.0)
        clip_dur = seg_dur + (crossfade if i < len(segments) - 1 else 0)
        zoom_dir = 1 if i % 2 == 0 else -1
        clip = _section_clip(img_path, seg.get("lines", []), clip_dur, zoom_dir)
        if i > 0:
            clip = clip.with_effects([CrossFadeIn(crossfade)])
        clips.append(clip)

    if not clips:
        raise RuntimeError("No section clips were built — all images missing?")

    final = concatenate_videoclips(clips, method="compose", padding=-crossfade)
    final = final.with_duration(duration).with_audio(audio)

    print(f"  Rendering {duration:.1f}s cinematic video...")
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
