#!/usr/bin/env python3
"""Crawl RSS feeds and website sources, output raw JSON for Claude Code to summarize."""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR / "raw"
CONFIG_PATH = SCRIPT_DIR / "config.yaml"
LAST_CRAWL_PATH = SCRIPT_DIR / "last_crawl.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_last_crawl():
    if LAST_CRAWL_PATH.exists():
        with open(LAST_CRAWL_PATH) as f:
            return json.load(f)
    return {}


def save_last_crawl(data):
    with open(LAST_CRAWL_PATH, "w") as f:
        json.dump(data, f, indent=2)


def crawl_rss_feed(feed_config, since_date):
    """Fetch and parse a single RSS/Atom feed."""
    url = feed_config["url"]
    name = feed_config["name"]
    tags = feed_config.get("tags", [])

    print(f"  Fetching {name}... ", end="", flush=True)

    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            print(f"FAILED ({feed.bozo_exception})")
            return []

        articles = []
        for entry in feed.entries[:10]:  # Max 10 per feed
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            if published and published < since_date:
                continue

            content = ""
            if hasattr(entry, "content") and entry.content:
                content = entry.content[0].get("value", "")
            elif hasattr(entry, "summary"):
                content = entry.summary or ""

            # Strip HTML
            if content:
                soup = BeautifulSoup(content, "html.parser")
                content = soup.get_text(separator="\n", strip=True)[:3000]

            articles.append({
                "title": entry.get("title", "Untitled"),
                "url": entry.get("link", ""),
                "content": content,
                "date": published.isoformat() if published else datetime.now(timezone.utc).isoformat(),
                "source": name,
                "tags": tags,
                "type": "blog",
            })

        print(f"{len(articles)} new articles")
        return articles

    except Exception as e:
        print(f"ERROR: {e}")
        return []


def crawl_website(site_config, since_date):
    """Scrape articles from a website page (for Anthropic, Perplexity etc.)."""
    url = site_config["url"]
    name = site_config["name"]
    tags = site_config.get("tags", [])

    print(f"  Scraping {name}... ", end="", flush=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        articles = []
        # Generic: find article links
        for link in soup.find_all("a", href=True):
            title_el = link.find(["h2", "h3", "h4", "span"])
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if len(title) < 10:
                continue

            href = link["href"]
            if not href.startswith("http"):
                from urllib.parse import urljoin
                href = urljoin(url, href)

            articles.append({
                "title": title,
                "url": href,
                "content": "",
                "date": datetime.now(timezone.utc).isoformat(),
                "source": name,
                "tags": tags,
                "type": "blog",
            })

        # Deduplicate by URL
        seen = set()
        unique = []
        for a in articles[:10]:
            if a["url"] not in seen:
                seen.add(a["url"])
                unique.append(a)

        print(f"{len(unique)} articles found")
        return unique

    except Exception as e:
        print(f"ERROR: {e}")
        return []


def main():
    RAW_DIR.mkdir(exist_ok=True)
    config = load_config()
    last_crawl = load_last_crawl()

    # Default: look back 2 days. Per-crawler key so YouTube/Reddit don't collide.
    default_since = datetime.now(timezone.utc) - timedelta(days=2)
    if "last_run_rss" in last_crawl:
        since_date = datetime.fromisoformat(last_crawl["last_run_rss"])
    else:
        since_date = default_since

    print(f"Crawling articles since {since_date.strftime('%Y-%m-%d %H:%M')}\n")

    all_articles = []

    # RSS Feeds
    print("RSS Feeds:")
    for feed_config in config.get("rss_feeds", []):
        articles = crawl_rss_feed(feed_config, since_date)
        all_articles.extend(articles)

    # Website Sources
    print("\nWebsite Sources:")
    for site_config in config.get("website_sources", []):
        articles = crawl_website(site_config, since_date)
        all_articles.extend(articles)

    # Write output
    output_path = RAW_DIR / "rss_raw.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2, ensure_ascii=False)

    # Update last crawl (per-crawler key — see crawl_youtube.py / crawl_reddit.py)
    last_crawl["last_run_rss"] = datetime.now(timezone.utc).isoformat()
    last_crawl["rss_count"] = len(all_articles)
    save_last_crawl(last_crawl)

    print(f"\nTotal: {len(all_articles)} articles saved to {output_path}")
    return len(all_articles)


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count >= 0 else 1)
