"""
Indian Stock Market news fetcher.
Sources: ET Markets, Moneycontrol, Livemint, Business Standard, Zeebiz,
         CNBC TV18, BusinessLine, Financial Express — all via free RSS + scraping.
No extra API keys needed.
"""

import feedparser, requests, re, os, hashlib
from bs4 import BeautifulSoup
from config import PEXELS_API_KEY, CACHE_DIR, STABILITY_API_KEY

# ─── Stock market RSS feeds (all free, no key) ───────────────────────────────
MARKET_RSS = [
    {"url": "https://economictimes.indiatimes.com/markets/stocks/news/rssfeeds/2146842.cms",  "src": "ET Markets"},
    {"url": "https://economictimes.indiatimes.com/markets/rss.cms",                           "src": "ET Markets"},
    {"url": "https://www.livemint.com/rss/markets",                                           "src": "LiveMint"},
    {"url": "https://www.business-standard.com/rss/markets-106.rss",                          "src": "Business Standard"},
    {"url": "https://www.thehindubusinessline.com/markets/stock-markets/feeder/default.rss",  "src": "BusinessLine"},
    {"url": "https://zeenews.india.com/rss/business-stock-market-news.xml",                   "src": "ZeeBiz"},
    {"url": "https://www.moneycontrol.com/rss/MCtopnews.xml",                                 "src": "Moneycontrol"},
    {"url": "https://www.cnbctv18.com/commonfeeds/v1/eng/rss/market.xml",                     "src": "CNBC TV18"},
    {"url": "https://economictimes.indiatimes.com/news/economy/rssfeeds/5311560.cms",         "src": "ET Economy"},
    {"url": "https://www.financialexpress.com/market/rss",                                    "src": "Financial Express"},
]

# ─── Impact keywords — higher = more dramatic story ──────────────────────────
HIGH_IMPACT = [
    "crash", "collapse", "circuit", "halt", "record high", "record low",
    "all-time high", "all-time low", "bankrupt", "fraud", "scam", "bust",
    "historic", "massive", "biggest", "worst", "best ever", "shock",
    "plunge", "surge", "soar", "tank", "wipe", "crisis", "warning",
    "fii", "rbi", "sebi", "budget", "sensex", "nifty", "ipo",
]
MED_IMPACT = [
    "rally", "gain", "rise", "fall", "dip", "bounce", "profit", "loss",
    "earnings", "results", "quarter", "dividend", "split", "buyback",
    "upgrade", "downgrade", "target", "buy", "sell", "overweight",
]

# ─── Pexels stock-market visuals ────────────────────────────────────────────
PEXELS_QUERIES = [
    "stock market india trading screen",
    "india stock exchange sensex nifty",
    "india finance money investment",
    "india business stock market graph",
    "india economy finance rupee",
]

# Per-section Pexels queries (for multi-bg support)
SECTION_QUERIES = {
    "breaking": [
        "india stock market red decline bearish",
        "stock market crash bear india red screen",
        "india finance stock market crisis",
    ],
    "market": [
        "india stock exchange bombay bse nse trading",
        "stock trader india monitor graphs charts",
        "india finance stock exchange floor busy",
    ],
    "cta": [
        "india investment growth wealth profit success",
        "india finance money growth chart upward green",
        "india stock market profit investor happy",
    ],
}

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _cache_path(url, ext="jpg"):
    h = hashlib.md5(url.encode()).hexdigest()[:14]
    return os.path.join(CACHE_DIR, f"{h}.{ext}")

def _download(url, timeout=10, ext="jpg"):
    path = _cache_path(url, ext)
    if os.path.exists(path) and os.path.getsize(path) > 5000:
        return path
    try:
        r = requests.get(url, timeout=timeout,
                         headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        if r.status_code == 200 and len(r.content) > 5000:
            with open(path, "wb") as f:
                f.write(r.content)
            return path
    except Exception:
        pass
    return None

def _og_image(url):
    try:
        r = requests.get(url, timeout=6,
                         headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        for prop in ("og:image", "twitter:image:src", "twitter:image"):
            tag = (soup.find("meta", property=prop) or
                   soup.find("meta", attrs={"name": prop}))
            if tag and tag.get("content","").startswith("http"):
                return _download(tag["content"])
    except Exception:
        pass
    return None

def _pexels_image_query(query, seed=0):
    """Fetch a Pexels portrait photo for an arbitrary query string."""
    if not PEXELS_API_KEY:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 8, "orientation": "portrait"},
            timeout=8,
        )
        photos = r.json().get("photos", [])
        if photos:
            photo = photos[seed % len(photos)]
            return _download(photo["src"]["portrait"])
    except Exception as e:
        print(f"    Pexels error ({query[:30]}): {e}")
    return None

def _pexels_image(query_idx=0):
    query = PEXELS_QUERIES[query_idx % len(PEXELS_QUERIES)]
    return _pexels_image_query(query, query_idx)

def fetch_section_images(company_query, seed=0):
    """
    Fetch 4 section images — one per video section type.
    If STABILITY_API_KEY is set: uses AI-generated cinematic images (cached).
    Otherwise: falls back to Pexels.
    Returns: {breaking: path, company: path, market: path, cta: path}
    """
    print(f"  Fetching section images (seed={seed})...")

    # ── AI generation (Stability AI) ─────────────────────────────────────
    if STABILITY_API_KEY:
        from image_gen import generate_section_images
        images = generate_section_images(company_query, seed)
        # Fill any failed sections with Pexels fallback
        if not images.get("breaking"):
            bq = SECTION_QUERIES["breaking"][seed % len(SECTION_QUERIES["breaking"])]
            images["breaking"] = _pexels_image_query(bq, seed)
        if not images.get("company"):
            images["company"] = _pexels_image_query(company_query, seed)
        if not images.get("market"):
            mq = SECTION_QUERIES["market"][seed % len(SECTION_QUERIES["market"])]
            images["market"] = _pexels_image_query(mq, seed)
        if not images.get("cta"):
            cq = SECTION_QUERIES["cta"][seed % len(SECTION_QUERIES["cta"])]
            images["cta"] = _pexels_image_query(cq, seed)
        for k, v in images.items():
            print(f"    {k}: {'AI OK' if v else 'MISSING'}")
        return images

    # ── Pexels fallback ───────────────────────────────────────────────────
    images = {}
    bq = SECTION_QUERIES["breaking"][seed % len(SECTION_QUERIES["breaking"])]
    images["breaking"] = _pexels_image_query(bq, seed)
    print(f"    breaking: {'OK' if images['breaking'] else 'MISSING'}")

    images["company"] = _pexels_image_query(company_query, seed)
    print(f"    company ({company_query[:35]}): {'OK' if images['company'] else 'MISSING'}")

    mq = SECTION_QUERIES["market"][seed % len(SECTION_QUERIES["market"])]
    images["market"] = _pexels_image_query(mq, seed)
    print(f"    market: {'OK' if images['market'] else 'MISSING'}")

    cq = SECTION_QUERIES["cta"][seed % len(SECTION_QUERIES["cta"])]
    images["cta"] = _pexels_image_query(cq, seed)
    print(f"    cta: {'OK' if images['cta'] else 'MISSING'}")

    return images

def _pexels_video(query_idx=0):
    if not PEXELS_API_KEY:
        return None
    query = PEXELS_QUERIES[query_idx % len(PEXELS_QUERIES)]
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 5, "orientation": "portrait", "size": "medium"},
            timeout=10,
        )
        for v in r.json().get("videos", []):
            for f in sorted(v.get("video_files", []),
                            key=lambda x: x.get("width", 0), reverse=True):
                if f.get("width", 0) >= 720:
                    vpath = _cache_path(f["link"], "mp4")
                    if os.path.exists(vpath) and os.path.getsize(vpath) > 50000:
                        return vpath
                    resp = requests.get(f["link"], timeout=30,
                                        headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        with open(vpath, "wb") as fp:
                            fp.write(resp.content)
                        return vpath
    except Exception as e:
        print(f"    Pexels video error: {e}")
    return None

# ─── Scrape Moneycontrol market headlines ─────────────────────────────────────
def _scrape_moneycontrol():
    stories = []
    try:
        r = requests.get(
            "https://www.moneycontrol.com/news/tags/stocks.html",
            timeout=8, headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(r.text, "html.parser")
        for li in soup.select("li.clearfix")[:10]:
            a = li.find("a", href=True)
            if not a:
                continue
            title = a.get_text(strip=True)
            url   = a["href"]
            if not url.startswith("http"):
                url = "https://www.moneycontrol.com" + url
            p = li.find("p")
            desc = p.get_text(strip=True) if p else ""
            if title:
                stories.append({"title": title, "desc": desc, "url": url, "src": "Moneycontrol"})
    except Exception as e:
        print(f"    Moneycontrol scrape failed: {e}")
    return stories

# ─── Scrape ET Markets headlines ─────────────────────────────────────────────
def _scrape_et_markets():
    stories = []
    try:
        r = requests.get(
            "https://economictimes.indiatimes.com/markets/stocks/news",
            timeout=8, headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(r.text, "html.parser")
        for div in soup.select("div.eachStory, article.story-box, div.story-box")[:10]:
            a = div.find("a", href=True)
            if not a:
                continue
            title = a.get_text(strip=True)
            url   = a["href"]
            if not url.startswith("http"):
                url = "https://economictimes.indiatimes.com" + url
            p = div.find("p")
            desc = p.get_text(strip=True) if p else ""
            if len(title) > 15:
                stories.append({"title": title, "desc": desc, "url": url, "src": "ET Markets"})
    except Exception as e:
        print(f"    ET Markets scrape failed: {e}")
    return stories

# ─── Story scoring (higher = more impactful) ─────────────────────────────────
def _score(title, desc):
    text = (title + " " + desc).lower()
    score = 0

    # Keyword impact
    for kw in HIGH_IMPACT:
        if kw in text:
            score += 3
    for kw in MED_IMPACT:
        if kw in text:
            score += 1

    # Numbers boost (crore > lakh > percent)
    crore_match = re.findall(r"(\d[\d,]*)\s*crore", text)
    for m in crore_match:
        val = int(m.replace(",", ""))
        if val >= 10000:   score += 5
        elif val >= 1000:  score += 3
        else:              score += 1

    pct_match = re.findall(r"(\d+\.?\d*)\s*%", text)
    for p in pct_match:
        val = float(p)
        if val >= 5:   score += 4
        elif val >= 2: score += 2
        else:          score += 1

    return score

# ─── Main entry point ─────────────────────────────────────────────────────────

def get_top_stories(n=3):
    """Return top n most impactful Indian stock market stories with images."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    all_raw = []
    seen    = set()

    # ── RSS feeds ──────────────────────────────────────────────────────────
    for feed_info in MARKET_RSS:
        try:
            print(f"  RSS: {feed_info['src']}...")
            fd = feedparser.parse(feed_info["url"])
            for e in fd.entries[:8]:
                title = e.get("title", "").strip()
                if not title or title[:40].lower() in seen:
                    continue
                seen.add(title[:40].lower())
                desc = BeautifulSoup(
                    e.get("summary", e.get("description", "")), "html.parser"
                ).get_text()[:600].strip()
                url = e.get("link", "")
                all_raw.append({"title": title, "desc": desc, "url": url,
                                 "src": feed_info["src"]})
        except Exception as ex:
            print(f"    RSS failed ({feed_info['src']}): {ex}")

    # ── Web scraping ───────────────────────────────────────────────────────
    print("  Scraping Moneycontrol...")
    all_raw.extend(_scrape_moneycontrol())
    print("  Scraping ET Markets...")
    all_raw.extend(_scrape_et_markets())

    print(f"  Total raw stories: {len(all_raw)}")

    # ── Deduplicate + score ────────────────────────────────────────────────
    unique = {}
    for s in all_raw:
        key = s["title"][:40].lower()
        if key not in unique:
            unique[key] = {**s, "score": _score(s["title"], s["desc"])}
        else:
            # Keep the one with more description
            if len(s["desc"]) > len(unique[key]["desc"]):
                unique[key]["desc"] = s["desc"]

    ranked = sorted(unique.values(), key=lambda x: x["score"], reverse=True)
    print(f"  Unique stories: {len(ranked)}, picking top {n}")
    for i, s in enumerate(ranked[:n], 1):
        print(f"  #{i} score={s['score']:3d}  [{s['src']}] {s['title'][:65]}")

    # ── Fetch images for top stories ───────────────────────────────────────
    top = ranked[:n]
    for idx, story in enumerate(top):
        img = None

        # 1) Try RSS media / enclosure (already raw, not in this path — handled below)
        # 2) Scrape og:image from article
        if story.get("url"):
            print(f"  Getting image for story {idx+1}...")
            img = _og_image(story["url"])

        # 3) Pexels photo as fallback
        if not img:
            print(f"  Pexels photo fallback for story {idx+1}...")
            img = _pexels_image(idx)

        story["image"]    = img
        story["bg_video"] = _pexels_video(idx)  # always try for video bg

        if img:
            print(f"  Image OK: {os.path.basename(img)}")
        if story["bg_video"]:
            print(f"  Video BG OK: {os.path.basename(story['bg_video'])}")

    return top
