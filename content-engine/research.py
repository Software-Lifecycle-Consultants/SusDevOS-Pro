#!/usr/bin/env python3
"""
SusDevOS Weekly Research Agent
================================
Monitors sustainability, GHG, and climate regulation news every week.
Filters for items relevant to your audience (sustainability managers,
ESG consultants, development project managers in the UK/internationally).
Produces a ready-to-use content brief with:
  - 4–6 relevant news items from the past 7 days
  - A suggested blog post angle for the strongest story
  - 2–3 LinkedIn post hooks you can use standalone
  - Regulatory calendar: upcoming deadlines worth covering

Output: content-engine/briefs/YYYY-MM-DD.md

Usage:
  python research.py               # run now, save brief
  python research.py --days 14     # look back 14 days instead of 7
  python research.py --preview     # print brief to stdout, don't save
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import anthropic
import feedparser
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Feed list
# ---------------------------------------------------------------------------
# Each entry: (label, rss_url)
# Add or remove feeds freely.

FEEDS = [
    # UK government
    ("GOV.UK – Net Zero & Energy",
     "https://www.gov.uk/search/news-and-communications.atom"
     "?keywords=greenhouse+gas+emissions&organisations[]=department-for-energy-security-and-net-zero"),
    ("GOV.UK – DEFRA",
     "https://www.gov.uk/search/news-and-communications.atom"
     "?keywords=carbon+reporting&organisations[]=department-for-environment-food-rural-affairs"),

    # Standards bodies
    ("SBTi News",         "https://sciencebasedtargets.org/feed"),
    ("GHG Protocol",      "https://ghgprotocol.org/feed"),
    ("CDP Blog",          "https://www.cdp.net/en/articles.rss"),

    # Trade press
    ("Edie",              "https://www.edie.net/rss/"),
    ("BusinessGreen",     "https://www.businessgreen.com/rss"),
    ("Carbon Brief",      "https://www.carbonbrief.org/feed/"),
    ("Climate Home News", "https://www.climatechangenews.com/feed/"),
    ("ENDS Report",       "https://www.endsreport.com/rss/news"),

    # International
    ("UNFCCC News",       "https://unfccc.int/rss/news"),
    ("TNFD News",         "https://tnfd.global/feed/"),
]

# ---------------------------------------------------------------------------
# Relevance keywords — items must match at least one
# ---------------------------------------------------------------------------
RELEVANCE_KEYWORDS = [
    "greenhouse gas", "ghg", "scope 1", "scope 2", "scope 3",
    "carbon reporting", "secr", "csrd", "tcfd", "tnfd",
    "net zero", "sbti", "science based target", "cdp",
    "emission factor", "defra", "carbon footprint",
    "sustainability reporting", "esg", "climate disclosure",
    "biodiversity", "nature", "lulucf", "land use",
    "property", "development", "construction", "built environment",
    "real estate", "planning", "infrastructure",
]

MODEL = "claude-opus-4-5"

# ---------------------------------------------------------------------------
# Feed fetching
# ---------------------------------------------------------------------------

def fetch_feed(label: str, url: str, since: datetime) -> list[dict]:
    """Fetch an RSS feed and return entries published since `since`."""
    try:
        headers = {"User-Agent": "SusDevOS-ResearchAgent/1.0"}
        resp = requests.get(url, timeout=15, headers=headers)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"  ⚠  {label}: {e}")
        return []

    items = []
    for entry in feed.entries:
        # Parse published date
        pub = None
        for attr in ("published_parsed", "updated_parsed"):
            t = getattr(entry, attr, None)
            if t:
                import time
                pub = datetime(*t[:6], tzinfo=timezone.utc)
                break

        if pub and pub < since:
            continue  # too old

        title   = getattr(entry, "title",   "").strip()
        summary = getattr(entry, "summary", "").strip()
        link    = getattr(entry, "link",    "").strip()

        # Quick relevance pre-filter (saves Claude tokens)
        text = (title + " " + summary).lower()
        if not any(kw in text for kw in RELEVANCE_KEYWORDS):
            continue

        items.append({
            "source":  label,
            "title":   title,
            "summary": summary[:400],
            "url":     link,
            "date":    pub.strftime("%Y-%m-%d") if pub else "unknown",
        })

    return items


def collect_all_items(days_back: int) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days_back)
    print(f"\n📡 Fetching {len(FEEDS)} feeds (past {days_back} days)...")
    all_items = []
    for label, url in FEEDS:
        items = fetch_feed(label, url, since)
        print(f"  {'✓' if items else '·'} {label}: {len(items)} relevant items")
        all_items.extend(items)
    print(f"\n  Total pre-filtered items: {len(all_items)}")
    return all_items


# ---------------------------------------------------------------------------
# Claude analysis
# ---------------------------------------------------------------------------

def _call(system: str, prompt: str, max_tokens: int = 2000) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


SYSTEM = """You are the content strategist for SusDevOS — a GHG emissions and ecosystem
tracking platform for sustainable development projects.

Your audience: sustainability managers, ESG consultants, and development project
managers. They care about UK regulatory compliance (SECR, TCFD, CSRD), GHG Protocol
methodology, SBTi targets, biodiversity reporting (TNFD), and practical tools to
make their reporting faster and more credible.

When analysing news, prioritise:
1. Regulatory changes that require action (DEFRA factor updates, new reporting requirements)
2. Methodology updates (GHG Protocol, IPCC, SBTi guidance)
3. Industry benchmarks or research that reveals a problem SusDevOS solves
4. Policy signals that will affect development projects (planning, EIA, net zero targets)
"""

def rank_and_select(items: list[dict]) -> list[dict]:
    """Ask Claude to pick the 5 most valuable items and explain why."""
    if not items:
        return []

    if len(items) > 30:
        items = items[:30]  # cap to avoid huge prompts

    items_text = "\n\n".join(
        f"[{i+1}] Source: {it['source']}\n"
        f"Date: {it['date']}\n"
        f"Title: {it['title']}\n"
        f"Summary: {it['summary']}\n"
        f"URL: {it['url']}"
        for i, it in enumerate(items)
    )

    print("  → Ranking items with Claude")
    raw = _call(
        SYSTEM,
        f"""From the news items below, select the 5 most valuable for our audience.

For each selected item return JSON with keys:
  index (1-based), title, source, date, url, why (1 sentence: why this matters to our audience)

Return ONLY a JSON array of 5 objects. No preamble.

Items:
{items_text}""",
        max_tokens=1200,
    )

    import json, re
    # Strip markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    selected = json.loads(raw.strip())

    # Map back to original item dicts, add the "why" field
    result = []
    for s in selected:
        idx = s["index"] - 1
        if 0 <= idx < len(items):
            item = dict(items[idx])
            item["why"] = s.get("why", "")
            result.append(item)
    return result


def generate_brief(selected: list[dict], week_of: str) -> str:
    """Generate the full content brief markdown."""
    if not selected:
        return f"# Content Brief — {week_of}\n\nNo relevant news found this week.\n"

    items_text = "\n\n".join(
        f"**{it['title']}** ({it['source']}, {it['date']})\n"
        f"Why it matters: {it['why']}\n"
        f"URL: {it['url']}\n"
        f"Summary: {it['summary']}"
        for it in selected
    )

    print("  → Generating content brief")
    brief_body = _call(
        SYSTEM,
        f"""Using these 5 curated news items, write a weekly content brief for a solo founder
who publishes one blog post, 4 LinkedIn posts, and one YouTube video per week.

Structure the brief exactly like this (use these exact markdown headings):

## This Week's Top Stories
[List each item as: **Title** — Source, Date. One sentence on why it matters to the audience. Link.]

## Recommended Blog Post Angle
[Pick the strongest story. Write: headline, 3-sentence pitch, target keyword, 3 H2 subheadings,
and a "hook" — the most surprising or counterintuitive fact from the story.]

## LinkedIn Post Hooks
[3 standalone opening lines (hooks only — not full posts). Each should be a bold claim
or surprising stat that would stop a sustainability professional mid-scroll.]

## Regulatory Calendar
[List any upcoming deadlines, consultation close dates, or reporting seasons mentioned
in the stories. If none, say "Nothing urgent this week."]

## Pass-on Stories
[1–2 items that didn't make the cut this week but could be revisited next month.]

News items:
{items_text}""",
        max_tokens=2000,
    )

    header = f"# SusDevOS Content Brief — Week of {week_of}\n\n"
    footer = (
        "\n\n---\n"
        f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · "
        f"{len(selected)} stories reviewed · SusDevOS Research Agent*\n"
    )
    return header + brief_body + footer


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_brief(content: str, week_of: str) -> Path:
    out_dir = Path("briefs")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{week_of}.md"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="SusDevOS weekly research agent")
    parser.add_argument("--days",    type=int, default=7, help="How many days back to look (default: 7)")
    parser.add_argument("--preview", action="store_true",  help="Print to stdout instead of saving")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Error: ANTHROPIC_API_KEY not set in .env")

    week_of = datetime.now().strftime("%Y-%m-%d")

    # 1. Collect
    all_items = collect_all_items(args.days)

    if not all_items:
        print("\n  No relevant items found. Try --days 14 to look back further.")
        sys.exit(0)

    # 2. Rank and select top 5
    print("\n🤖 Analysing with Claude...")
    selected = rank_and_select(all_items)

    # 3. Generate brief
    brief = generate_brief(selected, week_of)

    # 4. Output
    if args.preview:
        print("\n" + "─" * 60)
        print(brief)
    else:
        path = save_brief(brief, week_of)
        print(f"\n✅ Brief saved: {path}")
        print(f"   {len(selected)} stories · open the file to review")


if __name__ == "__main__":
    main()
