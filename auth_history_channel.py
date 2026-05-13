"""
One-time OAuth — authorise the new "Lost History & Forgotten Mysteries" channel.
Saves history_token.pickle for both local runs and base64-encoded CI use.

Steps:
  1. Create the new YouTube channel under your Google account
  2. In Google Cloud Console, ensure the OAuth client (client_secrets.json) is
     present in this folder. You can reuse the existing one if it's set to
     "Desktop app" client type.
  3. Run: py auth_history_channel.py
  4. Browser opens -> sign in -> CHOOSE THE NEW HISTORY CHANNEL -> Allow
  5. history_token.pickle is saved here
  6. In PowerShell:
       [Convert]::ToBase64String([IO.File]::ReadAllBytes("history_token.pickle")) | Set-Clipboard
  7. Paste into GitHub Secret: HISTORY_YT_TOKEN
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

CLIENT_SECRETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secrets.json")
TOKEN_OUT      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history_token.pickle")


def main():
    if not os.path.exists(CLIENT_SECRETS):
        print(f"ERROR: {CLIENT_SECRETS} not found.")
        print("Download it from Google Cloud Console -> APIs & Services -> Credentials.")
        return

    print("Opening browser for Google OAuth...")
    print("IMPORTANT: When prompted, select your NEW HISTORY YouTube channel.")
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_OUT, "wb") as f:
        pickle.dump(creds, f)

    print(f"\nSaved: {TOKEN_OUT}")
    print("\nNext step — encode for GitHub Secrets (run in PowerShell):")
    print(r'  [Convert]::ToBase64String([IO.File]::ReadAllBytes("history_token.pickle")) | Set-Clipboard')
    print("Then paste into GitHub Secret: HISTORY_YT_TOKEN")


if __name__ == "__main__":
    main()
