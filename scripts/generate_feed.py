#!/usr/bin/env python3
"""Generate RSS feed.xml from all content markdown files."""

import os
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_DIR = Path(__file__).parent.parent
CONTENT_DIR = REPO_DIR / "content"
FEED_PATH = REPO_DIR / "feed.xml"
SITE_URL = "https://frederikkaiser-cegtec.github.io/ai-content-hub"


def parse_frontmatter(filepath):
    """Parse YAML frontmatter from a markdown file."""
    text = filepath.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not match:
        return None, text

    frontmatter = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            value = value.strip().strip('"').strip("'")
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",")]
            frontmatter[key.strip()] = value

    return frontmatter, match.group(2)


def escape_xml(text):
    """Escape special XML characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def generate_feed():
    """Generate RSS 2.0 feed from content files."""
    items = []

    if not CONTENT_DIR.exists():
        print("No content directory found.")
        return

    for md_file in sorted(CONTENT_DIR.rglob("*.md"), reverse=True):
        frontmatter, body = parse_frontmatter(md_file)
        if not frontmatter:
            continue

        title = frontmatter.get("title", md_file.stem)
        date = frontmatter.get("date", "")
        source_url = frontmatter.get("source_url", "")
        source = frontmatter.get("source", "")
        tags = frontmatter.get("tags", [])

        # Build description from body (first 500 chars)
        description = body.strip()[:500]

        items.append({
            "title": title,
            "link": source_url or f"{SITE_URL}/{md_file.relative_to(REPO_DIR)}",
            "description": description,
            "date": date,
            "source": source,
            "tags": tags if isinstance(tags, list) else [tags],
        })

    # Limit to 50 most recent
    items = items[:50]

    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    feed_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>AI Content Hub</title>
    <link>{SITE_URL}</link>
    <description>Curated daily summaries from top AI blogs and YouTube channels</description>
    <language>de</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
"""

    for item in items:
        pub_date = ""
        if item["date"]:
            try:
                dt = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
                pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
            except (ValueError, AttributeError):
                pub_date = now

        categories = ""
        for tag in item["tags"]:
            categories += f"      <category>{escape_xml(str(tag))}</category>\n"

        feed_xml += f"""    <item>
      <title>{escape_xml(str(item['title']))}</title>
      <link>{escape_xml(str(item['link']))}</link>
      <description>{escape_xml(str(item['description']))}</description>
      <pubDate>{pub_date}</pubDate>
      <source>{escape_xml(str(item['source']))}</source>
{categories}    </item>
"""

    feed_xml += """  </channel>
</rss>"""

    FEED_PATH.write_text(feed_xml, encoding="utf-8")
    print(f"Feed generated with {len(items)} items: {FEED_PATH}")


if __name__ == "__main__":
    generate_feed()
