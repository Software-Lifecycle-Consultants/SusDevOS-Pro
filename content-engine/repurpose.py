#!/usr/bin/env python3
"""
SusDevOS Content Repurposing Agent
===================================
Takes a blog post (markdown) and produces:
  - LinkedIn article (600-800 words)
  - 4 LinkedIn short posts (one insight each)
  - YouTube video script (7-10 min)
  - YouTube metadata (3 title options, description with chapters, 10 tags)

Optionally queues LinkedIn posts to Buffer for scheduled publishing.

Usage:
  python repurpose.py posts/my-blog-post.md
  python repurpose.py posts/my-blog-post.md --slug ghg-scope2-explainer --buffer
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL = "claude-opus-4-5"

BRAND_VOICE = """
You are writing content for SusDevOS — a GHG emissions tracking and ecosystem monitoring
platform built for sustainable development projects in the UK and internationally.

Audience: sustainability managers, ESG consultants, development project managers.
They are time-poor professionals who need to comply with UK SECR, CSRD, TNFD, and
GHG Protocol Corporate Standard. They want practical, credible, actionable information.

Tone: authoritative but accessible. Lead with value, not product features.
Avoid jargon where simpler words work. Never use filler phrases like
"In today's fast-paced world" or "It's more important than ever."
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_code_fence(text: str) -> str:
    """Remove ```json ... ``` wrappers if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop first line (```json or ```) and last line (```)
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return text.strip()


def _call(system: str, prompt: str, max_tokens: int = 2000) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Agent steps
# ---------------------------------------------------------------------------

def extract_insights(post: str) -> list[str]:
    """Pull 4 standalone insights from the post."""
    print("  → Extracting key insights")
    raw = _call(
        BRAND_VOICE,
        f"""Read this blog post and extract exactly 4 key insights that would work
as standalone LinkedIn posts. Each insight should be self-contained and
valuable without reading the full post.

Return ONLY a JSON array of 4 strings. No preamble, no markdown fences.

Blog post:
{post}""",
        max_tokens=800,
    )
    return json.loads(_strip_code_fence(raw))


def write_linkedin_article(post: str) -> str:
    """600-800 word LinkedIn article from the blog post."""
    print("  → Writing LinkedIn article")
    return _call(
        BRAND_VOICE,
        f"""Condense this blog post into a LinkedIn article (600–800 words).

Structure:
- Opening hook: 1–2 sentences that make a sustainability professional stop scrolling
- Body: preserve the main argument and key supporting evidence
- Close: one practical takeaway + a soft call to action to visit SusDevOS.com

Style rules:
- Short paragraphs (2–3 sentences max)
- No bullet points — flowing prose only
- Do not start with "I"

Blog post:
{post}""",
        max_tokens=1200,
    )


def write_linkedin_short_posts(insights: list[str]) -> list[str]:
    """Turn each insight into a 150-220 word LinkedIn post."""
    print("  → Writing LinkedIn short posts")
    posts = []
    for i, insight in enumerate(insights, 1):
        print(f"     Post {i}/4")
        text = _call(
            BRAND_VOICE,
            f"""Turn this insight into a LinkedIn post (150–220 words).

Rules:
- First line is the hook — a bold claim or surprising fact. Do NOT start with "I".
- 3–4 short paragraphs with line breaks between them
- End with a question or observation that invites comments
- Maximum 3 hashtags, placed at the very end on their own line
- Do NOT name SusDevOS — let the insight stand alone

Insight:
{insight}""",
            max_tokens=400,
        )
        posts.append(text)
    return posts


def write_youtube_script(post: str) -> str:
    """Full spoken-word video script, 7-10 minutes."""
    print("  → Writing YouTube script")
    return _call(
        BRAND_VOICE,
        f"""Turn this blog post into a YouTube video script (7–10 minutes at natural
speaking pace, approximately 1,000–1,400 words).

Use this structure and label each section with the tag in brackets:

[HOOK] 30 sec — open with the most surprising fact or problem statement
[INTRO] 30 sec — what this video covers and why it matters now
[SECTION 1] ~2 min — first main point
[SECTION 2] ~2 min — second main point
[SECTION 3] ~2 min — third main point (skip if post only has two main points)
[SUMMARY] 60 sec — tie the points together with a clear takeaway
[OUTRO] 30 sec — invite viewers to visit SusDevOS.com and subscribe

Style rules:
- Write as natural spoken English (contractions are fine)
- Add [PAUSE] where the presenter should let a point land
- Add [B-ROLL: description] suggestions where visuals would help
- No bullet lists mid-script — flowing narrative only

Blog post:
{post}""",
        max_tokens=2500,
    )


def write_youtube_metadata(post_intro: str, script_headers: str) -> dict:
    """Generate titles, description with chapters, and tags."""
    print("  → Generating YouTube metadata")
    raw = _call(
        BRAND_VOICE,
        f"""Generate YouTube metadata based on this blog post intro and script structure.

Return ONLY valid JSON with exactly these keys:
{{
  "titles": ["title 1", "title 2", "title 3"],
  "description": "full description string",
  "tags": ["tag1", "tag2", ..., "tag10"]
}}

Rules:
- titles: 3 options, each under 70 characters, front-load the main keyword
- description: first 150 characters are the preview (make them count).
  Include chapter markers based on the script sections, e.g.:
  "0:00 Introduction\\n1:30 The hidden cost of Scope 2\\n..."
  Include a link to https://susdевos.com and a subscribe reminder.
- tags: exactly 10 tags mixing broad (e.g. "sustainability reporting") and
  specific (e.g. "GHG Protocol Scope 2") keywords

Blog intro (first 500 chars):
{post_intro}

Script section headers:
{script_headers}""",
        max_tokens=1000,
    )
    return json.loads(_strip_code_fence(raw))


# ---------------------------------------------------------------------------
# Buffer integration
# ---------------------------------------------------------------------------

def queue_to_buffer(posts: list[str]) -> None:
    token      = os.environ.get("BUFFER_ACCESS_TOKEN", "")
    profile_id = os.environ.get("BUFFER_LINKEDIN_PROFILE_ID", "")

    if not token or not profile_id:
        print("\n  ⚠  Buffer env vars not set — skipping queue.")
        print("     Set BUFFER_ACCESS_TOKEN and BUFFER_LINKEDIN_PROFILE_ID in .env")
        return

    print(f"  → Queuing {len(posts)} posts to Buffer")
    queued = 0
    for i, post in enumerate(posts, 1):
        resp = requests.post(
            "https://api.bufferapp.com/1/updates/create.json",
            data={
                "text": post,
                "profile_ids[]": profile_id,
                "access_token": token,
            },
            timeout=15,
        )
        data = resp.json()
        if data.get("success"):
            queued += 1
            print(f"     ✓ Post {i} queued")
        else:
            print(f"     ✗ Post {i} failed: {data.get('message', 'unknown error')}")

    print(f"  → {queued}/{len(posts)} posts queued to Buffer")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_outputs(
    slug: str,
    article: str,
    short_posts: list[str],
    script: str,
    metadata: dict,
) -> Path:
    out = Path("output") / slug
    out.mkdir(parents=True, exist_ok=True)

    (out / "linkedin_article.md").write_text(article, encoding="utf-8")

    shorts = "\n\n---\n\n".join(
        f"## Post {i+1}\n\n{p}" for i, p in enumerate(short_posts)
    )
    (out / "linkedin_posts.md").write_text(shorts, encoding="utf-8")
    (out / "youtube_script.md").write_text(script, encoding="utf-8")
    (out / "youtube_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Repurpose a blog post into LinkedIn + YouTube content"
    )
    parser.add_argument("blog_post", help="Path to the blog post (.md file)")
    parser.add_argument(
        "--slug",
        help="Output folder name (default: timestamp)",
        default=None,
    )
    parser.add_argument(
        "--buffer",
        action="store_true",
        help="Queue LinkedIn short posts to Buffer after generating",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Error: ANTHROPIC_API_KEY not set in .env")

    post_path = Path(args.blog_post)
    if not post_path.exists():
        sys.exit(f"Error: file not found — {args.blog_post}")

    slug = args.slug or datetime.now().strftime("%Y%m%d-%H%M%S")
    post = post_path.read_text(encoding="utf-8")

    print(f"\n🚀 Repurposing: {post_path.name}")
    print(f"   Output folder: output/{slug}/\n")

    # Run agent steps
    insights    = extract_insights(post)
    article     = write_linkedin_article(post)
    short_posts = write_linkedin_short_posts(insights)
    script      = write_youtube_script(post)

    # Pass only the first 500 chars of post + script section headers to metadata
    script_headers = "\n".join(
        line for line in script.splitlines() if line.startswith("[")
    )
    metadata = write_youtube_metadata(post[:500], script_headers)

    # Save
    out_dir = save_outputs(slug, article, short_posts, script, metadata)

    # Optionally queue to Buffer
    if args.buffer:
        queue_to_buffer(short_posts)

    print(f"""
✅ Done! Files saved to: {out_dir}/

  linkedin_article.md   — 600-800 word LinkedIn article
  linkedin_posts.md     — 4 short posts (paste or schedule via Buffer)
  youtube_script.md     — Full video script with B-roll cues
  youtube_metadata.json — 3 title options, description + chapters, 10 tags
""")


if __name__ == "__main__":
    main()
