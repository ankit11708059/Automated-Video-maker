"""
Global finance and crypto news fetcher.
Scores stories by trending keywords + recency for maximum YouTube view potential.
"""

import re
import time
import hashlib
import requests
import feedparser
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# ─── RSS Feed Definitions ─────────────────────────────────────────────────────

FINANCE_FEEDS = [
    ("Reuters Business",   "https://feeds.reuters.com/reuters/businessNews"),
    ("BBC Business",       "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("CNBC Top News",      "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("MarketWatch",        "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ("Yahoo Finance",      "https://finance.yahoo.com/rss/"),
    ("Investopedia",       "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline"),
    ("FT Markets",         "https://www.ft.com/rss/home/uk"),
    ("The Guardian Biz",   "https://www.theguardian.com/business/rss"),
]

CRYPTO_FEEDS = [
    ("CoinDesk",           "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("CoinTelegraph",      "https://cointelegraph.com/rss"),
    ("Decrypt",            "https://decrypt.co/feed"),
    ("The Block",          "https://www.theblock.co/rss.xml"),
    ("CryptoSlate",        "https://cryptoslate.com/feed/"),
    ("BeInCrypto",         "https://beincrypto.com/feed/"),
]

# ─── Trending Keyword Scoring ─────────────────────────────────────────────────

HIGH_IMPACT = [
    "crash", "collapse", "record high", "all-time high", "ath", "trillion",
    "surge", "soar", "plunge", "meltdown", "fed", "federal reserve",
    "rate cut", "rate hike", "recession", "layoffs", "bankrupt", "default",
    "hack", "sec", "ban", "sanction", "inflation", "war", "tariff",
    "bitcoin", "crypto", "etf approved", "halving", "rug pull", "scam",
    "billion", "million jobs", "historic",
]

MED_IMPACT = [
    "earnings", "profit", "ipo", "merger", "acquisition", "deal",
    "gdp", "unemployment", "interest rate", "bond", "stock market",
    "nasdaq", "s&p", "dow jones", "bull", "bear", "rally",
    "ethereum", "solana", "xrp", "altcoin", "defi", "nft",
    "elon", "trump", "apple", "google", "amazon", "microsoft",
]


def _score(title: str, desc: str, published: datetime | None) -> float:
    text = (title + " " + (desc or "")).lower()
    score = 0.0

    for kw in HIGH_IMPACT:
        if kw in text:
            score += 5

    for kw in MED_IMPACT:
        if kw in text:
            score += 2

    # Recency bonus
    if published:
        try:
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - published).total_seconds() / 3600
            if age_hours <= 2:
                score *= 3
            elif age_hours <= 6:
                score *= 1.5
        except Exception:
            pass

    # Penalise very short titles (usually nav links / ads)
    if len(title) < 20:
        score *= 0.2

    return score


def _parse_date(entry) -> datetime | None:
    for field in ("published", "updated"):
        raw = entry.get(field)
        if raw:
            try:
                return parsedate_to_datetime(raw)
            except Exception:
                pass
    return None


def _fetch_feed(url: str, source: str, timeout: int = 8) -> list[dict]:
    try:
        resp = requests.get(url, timeout=timeout,
                            headers={"User-Agent": "Mozilla/5.0 (compatible; YTShorts/1.0)"})
        feed = feedparser.parse(resp.text)
    except Exception:
        return []

    stories = []
    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        desc  = re.sub(r"<[^>]+>", " ", entry.get("summary") or entry.get("description") or "")
        url_  = entry.get("link") or ""
        pub   = _parse_date(entry)
        if not title or not url_:
            continue
        stories.append({
            "title":  title,
            "desc":   desc[:500],
            "url":    url_,
            "src":    source,
            "published": pub,
            "score":  _score(title, desc, pub),
        })
    return stories


def _dedup(stories: list[dict]) -> list[dict]:
    seen, out = set(), []
    for s in stories:
        key = s["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out


def get_finance_stories(n: int = 10) -> list[dict]:
    """Return top-n finance stories sorted by view-potential score."""
    all_stories = []
    for source, url in FINANCE_FEEDS:
        all_stories.extend(_fetch_feed(url, source))
    all_stories = _dedup(all_stories)
    all_stories.sort(key=lambda s: s["score"], reverse=True)
    return all_stories[:n]


def get_crypto_stories(n: int = 10) -> list[dict]:
    """Return top-n crypto stories sorted by view-potential score."""
    all_stories = []
    for source, url in CRYPTO_FEEDS:
        all_stories.extend(_fetch_feed(url, source))
    all_stories = _dedup(all_stories)
    all_stories.sort(key=lambda s: s["score"], reverse=True)
    return all_stories[:n]


if __name__ == "__main__":
    print("=== TOP 5 FINANCE ===")
    for s in get_finance_stories(5):
        print(f"  [{s['score']:.0f}] {s['title'][:80]}  ({s['src']})")
    print("\n=== TOP 5 CRYPTO ===")
    for s in get_crypto_stories(5):
        print(f"  [{s['score']:.0f}] {s['title'][:80]}  ({s['src']})")
