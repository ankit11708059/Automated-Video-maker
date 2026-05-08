"""Quick test: generate a short audio and verify 60s speed-up works."""
import os
from moviepy import AudioFileClip
from config    import CACHE_DIR, OUTPUT_DIR
from audio_gen import generate_audio, get_best_voice
from video_gen import _fit_audio_to_duration

os.makedirs(CACHE_DIR, exist_ok=True)

TEST_SCRIPT = "Tata Motors stock update. Price hike of 1.5 percent from April 2026. Stock trading 1 percent up today. Long term outlook positive. Subscribe for daily updates."
AUDIO_PATH  = os.path.join(CACHE_DIR, "test_speed.mp3")
FIT_PATH    = AUDIO_PATH.replace(".mp3", "_fit.mp3")

for p in [AUDIO_PATH, FIT_PATH]:
    if os.path.exists(p):
        os.remove(p)

print("Generating test audio...")
voice_id = get_best_voice()
generate_audio(TEST_SCRIPT, AUDIO_PATH, voice_id)

orig_dur = AudioFileClip(AUDIO_PATH).duration
print(f"Original: {orig_dur:.1f}s")

fit = _fit_audio_to_duration(AUDIO_PATH, 5.0)
fit_dur = AudioFileClip(fit).duration
print(f"After speed-up to 5s target: {fit_dur:.1f}s")
print("Speed-up works!" if abs(fit_dur - 5.0) < 0.5 else "ERROR: duration mismatch")
