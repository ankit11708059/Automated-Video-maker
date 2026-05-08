"""
One-time OAuth helper — run this ONCE locally to authorise the new YouTube channel.
Saves world_finance_token.pickle which you then base64-encode into GitHub Secrets.

Steps:
  1. Put client_secrets.json (from Google Cloud Console) in this folder
  2. Run: py auth_new_channel.py
  3. Browser opens -> sign in -> allow access
  4. world_finance_token.pickle is saved here
  5. In PowerShell, encode it:
       [Convert]::ToBase64String([IO.File]::ReadAllBytes("world_finance_token.pickle")) | Set-Clipboard
  6. Paste the clipboard value into GitHub Secret: WORLD_FINANCE_YT_TOKEN
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

CLIENT_SECRETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secrets.json")
TOKEN_OUT      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_finance_token.pickle")


def main():
    if not os.path.exists(CLIENT_SECRETS):
        print(f"ERROR: {CLIENT_SECRETS} not found.")
        print("Download it from Google Cloud Console -> APIs & Services -> Credentials -> OAuth 2.0 Client.")
        return

    print("Opening browser for Google OAuth...")
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_OUT, "wb") as f:
        pickle.dump(creds, f)

    print(f"\nSaved: {TOKEN_OUT}")
    print("\nNext step — encode for GitHub Secrets (run in PowerShell):")
    print(r'  [Convert]::ToBase64String([IO.File]::ReadAllBytes("world_finance_token.pickle")) | Set-Clipboard')
    print("Then paste into GitHub Secret: WORLD_FINANCE_YT_TOKEN")


if __name__ == "__main__":
    main()
