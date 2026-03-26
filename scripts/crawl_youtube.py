#!/usr/bin/env python3
"""Crawl YouTube channels for recent videos and extract transcripts."""

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

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


def get_recent_videos(channel_id, channel_name, max_results=5):
    """Get recent video IDs from a YouTube channel via RSS feed."""
    # YouTube provides RSS feeds for channels
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    print(f"  Fetching {channel_name}... ", end="", flush=True)

    try:
        import feedparser
        feed = feedparser.parse(rss_url)

        videos = []
        for entry in feed.entries[:max_results]:
            video_id = entry.get("yt_videoid", "")
            if not video_id:
                # Extract from link
                link = entry.get("link", "")
                match = re.search(r"v=([a-zA-Z0-9_-]+)", link)
                if match:
                    video_id = match.group(1)

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            videos.append({
                "video_id": video_id,
                "title": entry.get("title", "Untitled"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "date": published.isoformat() if published else datetime.now(timezone.utc).isoformat(),
                "channel": channel_name,
            })

        print(f"{len(videos)} videos")
        return videos

    except Exception as e:
        print(f"ERROR: {e}")
        return []


def get_transcript(video_id):
    """Get transcript for a YouTube video."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=["en", "de"])

        # Combine all text snippets
        full_text = " ".join(snippet.text for snippet in transcript.snippets)

        # Limit to ~5000 chars
        return full_text[:5000]

    except Exception as e:
        return f"[Transcript unavailable: {e}]"


def main():
    RAW_DIR.mkdir(exist_ok=True)
    config = load_config()
    last_crawl = load_last_crawl()

    # Default: look back 3 days for YouTube
    default_since = datetime.now(timezone.utc) - timedelta(days=3)
    if "last_run" in last_crawl:
        since_date = datetime.fromisoformat(last_crawl["last_run"])
    else:
        since_date = default_since

    print(f"Fetching YouTube videos since {since_date.strftime('%Y-%m-%d %H:%M')}\n")

    all_videos = []

    print("YouTube Channels:")
    for channel_config in config.get("youtube_channels", []):
        videos = get_recent_videos(
            channel_config["channel_id"],
            channel_config["name"],
        )

        for video in videos:
            # Filter by date
            video_date = datetime.fromisoformat(video["date"])
            if video_date < since_date:
                continue

            # Get transcript
            print(f"    Transcript: {video['title'][:50]}... ", end="", flush=True)
            transcript = get_transcript(video["video_id"])
            video["transcript"] = transcript
            video["tags"] = channel_config.get("tags", [])
            video["type"] = "youtube"
            video["source"] = channel_config["name"]

            has_transcript = not transcript.startswith("[Transcript unavailable")
            print("OK" if has_transcript else "SKIP")

            all_videos.append(video)

    # Write output
    output_path = RAW_DIR / "youtube_raw.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_videos, f, indent=2, ensure_ascii=False)

    # Update last crawl
    last_crawl["last_run"] = datetime.now(timezone.utc).isoformat()
    last_crawl["youtube_count"] = len(all_videos)
    save_last_crawl(last_crawl)

    print(f"\nTotal: {len(all_videos)} videos saved to {output_path}")
    return len(all_videos)


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count >= 0 else 1)
