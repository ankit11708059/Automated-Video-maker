import requests
from config import ELEVENLABS_API_KEY

sub = requests.get("https://api.elevenlabs.io/v1/user/subscription",
                   headers={"xi-api-key": ELEVENLABS_API_KEY})
if sub.status_code == 200:
    s = sub.json()
    print(f"Plan        : {s.get('tier')}")
    print(f"Chars used  : {s.get('character_count'):,} / {s.get('character_limit'):,}")
    print(f"Models avail: {s.get('available_models', [])}")

r = requests.get("https://api.elevenlabs.io/v1/voices",
                 headers={"xi-api-key": ELEVENLABS_API_KEY})
voices = r.json().get("voices", [])
print(f"\nTotal voices: {len(voices)}")
for v in voices:
    lb = v.get("labels", {})
    print(f"  {v['name']:<22} accent={lb.get('accent',''):<12} lang={lb.get('language','')}")
