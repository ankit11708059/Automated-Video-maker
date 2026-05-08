"""
ElevenLabs TTS — natural Indian voiceover.

Voice priority:
  1. Aryaveer / Yatin  (Indian, lang=hi) — requires ElevenLabs Creator plan ($22/mo)
  2. Daniel            (British broadcaster — best free fallback for news delivery)
  3. George / Brian    (resonant, good for dramatic content)
  4. First available   (last resort)

To unlock Indian voices: upgrade to ElevenLabs Creator at elevenlabs.io/pricing
"""

import requests, os
from config import ELEVENLABS_API_KEY, PREFERRED_VOICES

# Free-tier fallback order — best voices for news-style Hinglish delivery
FREE_FALLBACK = ["Daniel", "George", "Brian", "Charlie", "Adam"]

def _name_matches(voice_name: str, pref: str) -> bool:
    n = voice_name.lower()
    p = pref.lower()
    return n == p or n.startswith(p + " ") or n.startswith(p + "-")

def _fetch_voices():
    r = requests.get("https://api.elevenlabs.io/v1/voices",
                     headers={"xi-api-key": ELEVENLABS_API_KEY}, timeout=10)
    return r.json().get("voices", [])

def get_best_voice():
    print("  Fetching ElevenLabs voices...")
    voices = _fetch_voices()
    # Try preferred list (includes Indian voices first)
    for pref in PREFERRED_VOICES:
        for v in voices:
            if _name_matches(v["name"], pref):
                print(f"  Voice selected: {v['name']}  [{v['voice_id']}]")
                return v["voice_id"]
    if voices:
        print(f"  Voice: {voices[0]['name']} (first available)")
        return voices[0]["voice_id"]
    return "21m00Tcm4TlvDq8ikWAM"  # Rachel hardcoded fallback

def _post_tts(voice_id, script):
    return requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key":   ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept":       "audio/mpeg",
        },
        json={
            "text":     script,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                # Balanced settings — natural delivery, moderate expressiveness.
                # Works well for both Indian voices (Aryaveer/Yatin) and Western fallbacks.
                "stability":         0.45,
                "similarity_boost":  0.75,
                "style":             0.40,
                "use_speaker_boost": True,
            },
        },
        timeout=60,
    )

def generate_audio(script, output_path, voice_id=None):
    if voice_id is None:
        voice_id = get_best_voice()

    print(f"  Generating audio ({len(script)} chars)...")
    r = _post_tts(voice_id, script)

    # 402 = library voice requires paid plan — auto-retry with free fallback
    if r.status_code == 402:
        print("  NOTE: Indian voice requires ElevenLabs Creator plan ($22/mo).")
        print("  Falling back to best available free voice...")
        voices = _fetch_voices()
        fallback_id = None
        for name in FREE_FALLBACK:
            for v in voices:
                if _name_matches(v["name"], name):
                    fallback_id = v["voice_id"]
                    print(f"  Fallback voice: {v['name']}")
                    break
            if fallback_id:
                break
        if not fallback_id and voices:
            fallback_id = voices[0]["voice_id"]
            print(f"  Fallback voice: {voices[0]['name']}")
        if fallback_id:
            r = _post_tts(fallback_id, script)

    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs error {r.status_code}: {r.text[:300]}")

    with open(output_path, "wb") as f:
        f.write(r.content)
    size_kb = os.path.getsize(output_path) // 1024
    print(f"  Audio saved: {size_kb} KB  ->  {output_path}")
    return output_path
