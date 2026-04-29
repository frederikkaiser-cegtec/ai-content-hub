#!/usr/bin/env python3
"""Crawl Google Trends rising queries for a seed list of B2B-GTM topics.

Output: raw/trends_raw.json — one entry per seed with top + rising queries.
Used by /content vorschlaege as external trend-volume signal.

pytrends is rate-limited and occasionally returns 429. Errors are swallowed
per-seed so a single bad seed doesn't kill the run.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from pytrends.request import TrendReq

SCRIPT_DIR = Path(__file__).parent
REPO_DIR = SCRIPT_DIR.parent
RAW_DIR = SCRIPT_DIR / "raw"
PUBLIC_PATH = REPO_DIR / "trends.json"

# Seeds chosen to overlap CegTec ICP topics. Keep <= 15 to avoid rate-limits.
SEEDS = [
    "ai outbound",
    "ai sales",
    "cold email",
    "b2b lead generation",
    "sales automation",
    "lead enrichment",
    "linkedin outreach",
    "gtm strategy",
    "ai sdr",
    "sales intelligence",
    "ai agents",
    "prompt engineering",
]

TIMEFRAME = "now 7-d"
GEO = ""  # global; use "DE" for Germany-only


def fetch_seed(pytrends, seed):
    try:
        pytrends.build_payload([seed], timeframe=TIMEFRAME, geo=GEO)
        related = pytrends.related_queries()
        bucket = related.get(seed, {}) or {}
        top = bucket.get("top")
        rising = bucket.get("rising")

        return {
            "seed": seed,
            "top": top.head(10).to_dict(orient="records") if top is not None else [],
            "rising": rising.head(10).to_dict(orient="records") if rising is not None else [],
        }
    except Exception as e:
        print(f"  {seed}: ERROR {e}")
        return {"seed": seed, "error": str(e), "top": [], "rising": []}


def main():
    RAW_DIR.mkdir(exist_ok=True)
    pytrends = TrendReq(hl="en-US", tz=60)

    results = []
    print(f"Google Trends ({TIMEFRAME}, {len(SEEDS)} seeds):")
    for seed in SEEDS:
        print(f"  {seed}... ", end="", flush=True)
        result = fetch_seed(pytrends, seed)
        rising_count = len(result.get("rising", []))
        top_count = len(result.get("top", []))
        print(f"top={top_count} rising={rising_count}")
        results.append(result)
        time.sleep(2)  # gentle on rate-limit

    output = {
        "_fetched_at": datetime.now(timezone.utc).isoformat(),
        "timeframe": TIMEFRAME,
        "geo": GEO or "global",
        "seeds": results,
    }

    payload = json.dumps(output, indent=2, ensure_ascii=False)
    raw_path = RAW_DIR / "trends_raw.json"
    raw_path.write_text(payload, encoding="utf-8")
    PUBLIC_PATH.write_text(payload, encoding="utf-8")
    print(f"\nSaved {raw_path} and {PUBLIC_PATH}")


if __name__ == "__main__":
    main()
    sys.exit(0)
