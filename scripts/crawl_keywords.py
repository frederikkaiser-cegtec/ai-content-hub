#!/usr/bin/env python3
"""Keyword-based discovery crawler.

Source-basiertes Crawling holt nur was die 24 RSS/Site-Quellen schreiben.
Dieser Crawler dreht es um: pro Topic-Seed wird Google News RSS abgefragt,
sodass auch Quellen auftauchen die wir nicht kennen.

Output: scripts/raw/keywords_raw.json + repo-root keywords.json (gh-pages).
Schema: {seeds: [{seed, items: [{title, link, source, published, summary}]}]}
"""

import json
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import requests

SCRIPT_DIR = Path(__file__).parent
REPO_DIR = SCRIPT_DIR.parent
RAW_DIR = SCRIPT_DIR / "raw"
PUBLIC_PATH = REPO_DIR / "keywords.json"

# Topic-Seeds: was wir aktiv beobachten wollen unabhaengig von Source-Liste.
# Bewusst eng auf B2B-GTM/AI-Marketing/Outreach gehalten.
SEEDS = [
    "GEO marketing",
    "AI agent readiness",
    "llms.txt",
    "AI friendliness",
    "B2B outbound 2026",
    "cold email reply rate",
    "AI SDR",
    "ChatGPT brand mentions",
    "MEDDIC AI",
    "ICP enrichment AI",
]

ITEMS_PER_SEED = 10
HEADERS = {
    "User-Agent": "ai-content-hub/0.1 (CegTec content-orchestrator; contact: frederik.kaiser@cegtec.net)"
}
NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch_seed(seed):
    url = f"https://news.google.com/rss/search?q={quote_plus(seed)}&hl=en-US&gl=US&ceid=US:en"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = (it.findtext("pubDate") or "").strip()
        src_el = it.find("source")
        source = (src_el.text if src_el is not None else "") or ""
        summary = (it.findtext("description") or "").strip()
        if not title or not link:
            continue
        items.append({
            "title": title,
            "link": link,
            "source": source,
            "published": pub,
            "summary": summary[:500],
        })
        if len(items) >= ITEMS_PER_SEED:
            break
    return items


def main():
    RAW_DIR.mkdir(exist_ok=True)
    seeds_out = []

    print(f"Keyword-Discovery ({len(SEEDS)} seeds):")
    for seed in SEEDS:
        print(f"  '{seed}'... ", end="", flush=True)
        try:
            items = fetch_seed(seed)
            print(f"{len(items)} items")
            seeds_out.append({"seed": seed, "items": items})
        except Exception as e:
            print(f"ERROR {e}")
            seeds_out.append({"seed": seed, "items": [], "error": str(e)})
        time.sleep(2)

    output = {
        "_fetched_at": datetime.now(timezone.utc).isoformat(),
        "_source": "Google News RSS via news.google.com/rss/search",
        "count": sum(len(s["items"]) for s in seeds_out),
        "seeds": seeds_out,
    }

    payload = json.dumps(output, indent=2, ensure_ascii=False)
    raw_path = RAW_DIR / "keywords_raw.json"
    raw_path.write_text(payload, encoding="utf-8")
    PUBLIC_PATH.write_text(payload, encoding="utf-8")
    print(f"\n{output['count']} items quer ueber {len(SEEDS)} seeds -> {raw_path} + {PUBLIC_PATH}")


if __name__ == "__main__":
    main()
    sys.exit(0)
