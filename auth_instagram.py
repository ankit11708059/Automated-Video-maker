"""
auth_instagram.py — One-time setup to get Instagram API credentials.

BEFORE RUNNING — complete these steps:

  1. Switch Instagram to a Professional account (Creator or Business):
     Instagram app → Profile → Menu (3 lines) → Settings → Account
     → "Switch to Professional Account" → Creator → follow prompts

  2. Link Instagram to a Facebook Page:
     Instagram → Settings → Account → Linked Accounts → Facebook
     Log in with Facebook → choose or create a Page → Link

  3. Create a Facebook Developer App:
     https://developers.facebook.com → My Apps → Create App
     → Type: Other → Business → give it any name
     → Dashboard → Add Product → Instagram Graph API

  4. Add your Instagram as a test user (only needed during development):
     App Dashboard → Roles → Instagram Test Users → Add your @username

  5. Get a short-lived access token:
     https://developers.facebook.com/tools/explorer/
     → Select your app (top right)
     → "Generate Access Token"
     → Tick these permissions:
         instagram_basic
         instagram_content_publish
         pages_show_list
         pages_read_engagement
     → Generate Token → copy it

  6. Run this script:
     py auth_instagram.py

The script will:
  - Exchange the short-lived token for a 60-day long-lived token
  - Detect your Instagram Business Account ID automatically
  - Save IG_ACCESS_TOKEN and IG_USER_ID to .env
  - Print the GitHub Actions secrets you need to add
"""

import os
import requests


def main():
    print("=" * 60)
    print("  Instagram API Credentials Setup")
    print("=" * 60)
    print()

    app_id = input("  Facebook App ID (from App Dashboard): ").strip()
    app_secret = input("  Facebook App Secret (Settings → Basic): ").strip()
    short_token = input("  Short-lived token (from Graph API Explorer): ").strip()

    # Exchange short-lived token for long-lived token (valid ~60 days)
    print("\n  Exchanging for long-lived token (valid 60 days)...")
    r = requests.get(
        "https://graph.facebook.com/v21.0/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_token,
        },
        timeout=15,
    )
    if not r.ok:
        print(f"\n  ERROR: {r.json()}")
        return
    long_token = r.json()["access_token"]
    expires_days = r.json().get("expires_in", 0) // 86400
    print(f"  Long-lived token obtained — expires in ~{expires_days} days")

    # Find Instagram Business/Creator account linked to a Facebook Page
    print("\n  Looking for your Instagram account via Facebook Pages...")
    r = requests.get(
        "https://graph.facebook.com/v21.0/me/accounts",
        params={"access_token": long_token},
        timeout=15,
    )
    r.raise_for_status()
    pages = r.json().get("data", [])

    if not pages:
        print("\n  ERROR: No Facebook Pages found under your account.")
        print("  Make sure you have at least one Facebook Page and it is linked to Instagram.")
        return

    ig_user_id = None
    for page in pages:
        print(f"  Page found: {page['name']} (ID: {page['id']})")
        r2 = requests.get(
            f"https://graph.facebook.com/v21.0/{page['id']}",
            params={
                "fields": "instagram_business_account",
                "access_token": page["access_token"],
            },
            timeout=15,
        )
        r2.raise_for_status()
        ig_data = r2.json().get("instagram_business_account", {})
        if ig_data:
            ig_user_id = ig_data["id"]
            print(f"  → Linked Instagram account ID: {ig_user_id}")
            break

    if not ig_user_id:
        print("\n  ERROR: No Instagram Business/Creator account linked to your Facebook Pages.")
        print("  Steps to fix:")
        print("    1. In Instagram: Settings → Account → Switch to Professional Account")
        print("    2. In Instagram: Settings → Account → Linked Accounts → Facebook → Link")
        return

    # Confirm the Instagram account details
    r = requests.get(
        f"https://graph.facebook.com/v21.0/{ig_user_id}",
        params={"fields": "username,followers_count,account_type", "access_token": long_token},
        timeout=15,
    )
    info = r.json()
    username = info.get("username", "unknown")
    followers = info.get("followers_count", "?")
    acct_type = info.get("account_type", "?")
    print(f"\n  Confirmed Instagram account:")
    print(f"    @{username}  |  {followers} followers  |  type: {acct_type}")

    # Save to .env
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            lines = [l for l in f.readlines() if not l.startswith("IG_")]
    else:
        lines = []
    lines.append(f"IG_ACCESS_TOKEN={long_token}\n")
    lines.append(f"IG_USER_ID={ig_user_id}\n")
    with open(env_path, "w") as f:
        f.writelines(lines)

    print(f"\n  Saved to .env:")
    print(f"    IG_USER_ID      = {ig_user_id}")
    print(f"    IG_ACCESS_TOKEN = {long_token[:20]}...  (truncated)")

    print(f"\n  For GitHub Actions — add these two repository secrets:")
    print(f"    Name: IG_ACCESS_TOKEN   Value: {long_token[:20]}... (use full token)")
    print(f"    Name: IG_USER_ID        Value: {ig_user_id}")
    print(f"    Settings → Secrets and variables → Actions → New repository secret")

    print(f"\n  REMINDER: Token expires in ~{expires_days} days.")
    print(f"  Re-run this script before it expires to refresh.")
    print(f"\n  Setup complete! Test with: py auto_stocks.py")


if __name__ == "__main__":
    main()
