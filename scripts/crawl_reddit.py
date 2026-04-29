#!/usr/bin/env python3
"""Crawl top-of-week posts + top comments from B2B/Sales/Marketing subreddits.

Reddit's public JSON API works without auth for read-only access.
Output: scripts/raw/reddit_raw.json (gitignored) and reddit.json (public, gh-pages).
Used by /content vorschlaege as external customer-voice signal.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).parent
REPO_DIR = SCRIPT_DIR.parent
RAW_DIR = SCRIPT_DIR / "raw"
PUBLIC_PATH = REPO_DIR / "reddit.json"

SUBREDDITS = [
    "sales",
    "b2bmarketing",
    "marketing",
    "SaaS",
    "startups",
    "coldemail",
    "Entrepreneur",
]

POSTS_PER_SUB = 15
COMMENTS_PER_POST = 5
TIMEFRAME = "week"

HEADERS = {
    "User-Agent": "ai-content-hub/0.1 (CegTec content-orchestrator; contact: frederik.kaiser@cegtec.net)"
}


def fetch_top_posts(subreddit):
    url = f"https://www.reddit.com/r/{subreddit}/top.json?t={TIMEFRAME}&limit={POSTS_PER_SUB}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json().get("data", {}).get("children", [])


def fetch_post_with_comments(subreddit, post_id):
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?limit={COMMENTS_PER_POST}&sort=top"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    listings = resp.json()
    if len(listings) < 2:
        return []
    comments = []
    for c in listings[1].get("data", {}).get("children", [])[:COMMENTS_PER_POST]:
        body = c.get("data", {}).get("body", "")
        score = c.get("data", {}).get("score", 0)
        if not body or body in ("[removed]", "[deleted]"):
            continue
        comments.append({"score": score, "body": body[:1500]})
    return comments


def main():
    RAW_DIR.mkdir(exist_ok=True)
    all_posts = []

    print(f"Reddit (top of {TIMEFRAME}, {len(SUBREDDITS)} subs):")
    for sub in SUBREDDITS:
        print(f"  r/{sub}... ", end="", flush=True)
        try:
            children = fetch_top_posts(sub)
        except Exception as e:
            print(f"ERROR {e}")
            continue

        sub_posts = []
        for child in children:
            data = child.get("data", {})
            post_id = data.get("id")
            if not post_id:
                continue
            entry = {
                "subreddit": sub,
                "id": post_id,
                "title": data.get("title", ""),
                "selftext": (data.get("selftext", "") or "")[:2000],
                "score": data.get("score", 0),
                "num_comments": data.get("num_comments", 0),
                "url": f"https://reddit.com{data.get('permalink', '')}",
                "created_utc": data.get("created_utc"),
                "comments": [],
            }
            try:
                entry["comments"] = fetch_post_with_comments(sub, post_id)
                time.sleep(1)  # gentle on rate-limit
            except Exception as e:
                entry["comments_error"] = str(e)
            sub_posts.append(entry)

        print(f"{len(sub_posts)} posts")
        all_posts.extend(sub_posts)
        time.sleep(2)

    output = {
        "_fetched_at": datetime.now(timezone.utc).isoformat(),
        "timeframe": TIMEFRAME,
        "subreddits": SUBREDDITS,
        "count": len(all_posts),
        "posts": all_posts,
    }

    payload = json.dumps(output, indent=2, ensure_ascii=False)
    raw_path = RAW_DIR / "reddit_raw.json"
    raw_path.write_text(payload, encoding="utf-8")
    PUBLIC_PATH.write_text(payload, encoding="utf-8")
    print(f"\n{len(all_posts)} posts -> {raw_path} + {PUBLIC_PATH}")


if __name__ == "__main__":
    main()
    sys.exit(0)
