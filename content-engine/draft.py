#!/usr/bin/env python3
"""
SusDevOS Blog Draft Agent
==========================
Takes a topic (and optional brief/notes) and writes a full, publish-ready
blog post in the SusDevOS template format.

Produces:
  - posts/SLUG.md — the full blog post with SEO frontmatter
  - posts/SLUG-meta.json — SEO metadata for Ghost CMS import

Usage:
  # From a topic alone
  python draft.py "Why Scope 3 Category 15 matters for property developers"

  # From a topic + brief file (e.g. output from research agent)
  python draft.py "Scope 3 Category 15" --brief briefs/2024-01-15.md

  # Pass a specific keyword to optimise for
  python draft.py "Scope 3 Category 15" --keyword "scope 3 financed emissions property"

  # Specify output slug
  python draft.py "Scope 3 Category 15" --slug scope3-category-15-property

  # Push to Ghost CMS as a draft
  python draft.py "Scope 3 Category 15" --publish-ghost
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import anthropic
import requests
from dotenv import load_dotenv

load_dotenv()

MODEL   = "claude-opus-4-5"
OUT_DIR = Path("posts")

# ---------------------------------------------------------------------------
# Brand voice + template
# ---------------------------------------------------------------------------

BRAND_VOICE = """
You are the lead content writer for SusDevOS — a GHG emissions and ecosystem
tracking platform for sustainable development projects.

Audience: sustainability managers, ESG consultants, development project managers
in the UK and internationally. They are time-poor, technically literate, and
tired of vague "net zero journey" content. They want practical, methodology-correct,
regulation-aware articles they can act on.

Tone: authoritative, clear, direct. No marketing fluff. No filler openers.
Cite sources where possible (DEFRA, GHG Protocol, IPCC, UK legislation).
Lead every section with the most important point first (inverted pyramid).
"""

POST_TEMPLATE = """
Blog posts follow this structure (output the markdown only, no preamble):

---
title: [Post title — under 65 chars, front-load keyword]
description: [Meta description — 140–160 chars, include keyword, clear value prop]
keyword: [Primary target keyword]
tags: [comma-separated list of 4–6 relevant tags]
reading_time: [estimated minutes, e.g. "7 min read"]
cta: [Call-to-action line for the end of the post, linking to a SusDevOS feature]
---

# [Post title]

[Author byline placeholder: *By the SusDevOS Team*]

[Opening paragraph — 2–3 sentences. State the core problem or surprising fact.
Do NOT start with "In today's..." or "It's more important than ever..."]

---

## [H2: First main section]

[Body — 200–300 words. Practical, specific. Include at least one concrete example,
stat, or regulatory reference where relevant.]

---

## [H2: Second main section]

[Body]

---

## [H2: Third main section]

[Body]

---

## [H2: Fourth main section — optional if post warrants it]

[Body]

---

## The Practical Takeaway

[1–2 paragraphs that synthesise the article into one actionable conclusion.
What should the reader do next?]

[CTA paragraph: soft mention of SusDevOS and how it addresses the problem discussed.]
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _call(system: str, prompt: str, max_tokens: int = 4000) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")[:60]


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Split YAML-style frontmatter from post body."""
    meta: dict = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip()
            body = parts[2].strip()

    return meta, body


# ---------------------------------------------------------------------------
# Agent steps
# ---------------------------------------------------------------------------

def research_topic(topic: str, brief_text: str, keyword: str) -> str:
    """Ask Claude to outline what the post needs to cover."""
    print("  → Researching topic")
    kw_line = f"Primary keyword to optimise for: {keyword}" if keyword else ""
    brief_line = f"\n\nContext from this week's research brief:\n{brief_text[:2000]}" if brief_text else ""

    return _call(
        BRAND_VOICE,
        f"""Plan a blog post on this topic for the SusDevOS audience.

Topic: {topic}
{kw_line}
{brief_line}

Return a JSON object with:
{{
  "angle": "the specific angle that makes this post stand out from generic coverage",
  "hook_fact": "the most surprising or counterintuitive fact to open with",
  "sections": ["H2 title 1", "H2 title 2", "H2 title 3", "H2 title 4 (optional)"],
  "regulatory_refs": ["list of UK/international regulations or standards to cite"],
  "keyword": "best primary keyword if not provided",
  "word_count_target": 900
}}

Return ONLY valid JSON.""",
        max_tokens=800,
    )


def write_draft(topic: str, plan: dict, brief_text: str, keyword: str) -> str:
    """Write the full blog post."""
    print("  → Writing draft")
    kw   = keyword or plan.get("keyword", topic)
    hook = plan.get("hook_fact", "")
    sections = "\n".join(f"- {s}" for s in plan.get("sections", []))
    refs = ", ".join(plan.get("regulatory_refs", []))

    return _call(
        BRAND_VOICE + "\n\n" + POST_TEMPLATE,
        f"""Write a complete blog post using this plan.

Topic: {topic}
Primary keyword: {kw}
Angle: {plan.get('angle', '')}
Opening hook fact: {hook}
Planned sections:
{sections}
Regulatory references to weave in: {refs}
Target word count: {plan.get('word_count_target', 900)} words

{'Additional context from research brief:' + chr(10) + brief_text[:1500] if brief_text else ''}

Write the full post now, following the template structure exactly (frontmatter + body).
Every section should be substantive — no placeholder text.""",
        max_tokens=4000,
    )


def generate_ghost_metadata(meta: dict, body: str) -> dict:
    """Build Ghost CMS API payload for a draft post."""
    return {
        "posts": [{
            "title":        meta.get("title", ""),
            "slug":         slugify(meta.get("title", "draft")),
            "status":       "draft",
            "excerpt":      meta.get("description", ""),
            "tags":         [{"name": t.strip()} for t in meta.get("tags", "").split(",") if t.strip()],
            "html":         f"<p><em>Paste markdown content here or use Ghost's markdown card.</em></p>",
            "custom_excerpt": meta.get("description", ""),
            "meta_title":   meta.get("title", ""),
            "meta_description": meta.get("description", ""),
        }]
    }


def publish_to_ghost(meta: dict, body: str) -> None:
    """POST the draft to Ghost Admin API."""
    ghost_url   = os.environ.get("GHOST_ADMIN_URL", "")
    ghost_key   = os.environ.get("GHOST_ADMIN_API_KEY", "")

    if not ghost_url or not ghost_key:
        print("\n  ⚠  Ghost env vars not set — skipping publish.")
        print("     Set GHOST_ADMIN_URL and GHOST_ADMIN_API_KEY in .env")
        return

    # Ghost Admin API uses JWT from key id:secret
    import time, jwt as pyjwt
    key_id, secret = ghost_key.split(":")
    iat = int(time.time())
    header  = {"alg": "HS256", "kid": key_id, "typ": "JWT"}
    payload = {"iat": iat, "exp": iat + 300, "aud": "/admin/"}
    token   = pyjwt.encode(payload, bytes.fromhex(secret), algorithm="HS256", headers=header)

    payload = generate_ghost_metadata(meta, body)
    url     = f"{ghost_url.rstrip('/')}/ghost/api/admin/posts/"
    resp    = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Ghost {token}",
            "Content-Type":  "application/json",
        },
        timeout=15,
    )
    if resp.ok:
        post_id = resp.json()["posts"][0]["id"]
        print(f"  ✓ Draft created in Ghost (id: {post_id})")
        print(f"    Edit at: {ghost_url}/ghost/#/editor/post/{post_id}")
    else:
        print(f"  ✗ Ghost API error {resp.status_code}: {resp.text[:200]}")


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save(slug: str, content: str, meta: dict) -> tuple[Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    post_path = OUT_DIR / f"{slug}.md"
    meta_path = OUT_DIR / f"{slug}-meta.json"

    post_path.write_text(content, encoding="utf-8")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    return post_path, meta_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="SusDevOS blog draft agent")
    parser.add_argument("topic",            help="Blog post topic or title")
    parser.add_argument("--brief",          help="Path to a research brief .md file for extra context")
    parser.add_argument("--keyword",        help="Primary SEO keyword to optimise for", default="")
    parser.add_argument("--slug",           help="Output filename slug (auto-generated if omitted)", default="")
    parser.add_argument("--publish-ghost",  action="store_true", help="Push draft to Ghost CMS")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Error: ANTHROPIC_API_KEY not set in .env")

    # Load optional brief
    brief_text = ""
    if args.brief:
        p = Path(args.brief)
        if p.exists():
            brief_text = p.read_text(encoding="utf-8")
            print(f"📎 Using brief: {p.name}")
        else:
            print(f"⚠  Brief file not found: {args.brief} — continuing without it")

    print(f"\n✍️  Drafting: {args.topic}\n")

    # Step 1: Research / plan
    plan_raw = research_topic(args.topic, brief_text, args.keyword)
    try:
        plan_raw = plan_raw.strip()
        if plan_raw.startswith("```"):
            plan_raw = re.sub(r"^```[a-z]*\n?", "", plan_raw)
            plan_raw = re.sub(r"\n?```$", "", plan_raw)
        plan = json.loads(plan_raw.strip())
    except json.JSONDecodeError:
        print("  ⚠  Could not parse plan JSON — using defaults")
        plan = {"angle": args.topic, "sections": [], "regulatory_refs": [], "keyword": args.keyword}

    # Step 2: Write
    draft = write_draft(args.topic, plan, brief_text, args.keyword)

    # Step 3: Parse frontmatter
    meta, body = parse_frontmatter(draft)

    # Step 4: Determine slug
    slug = args.slug or slugify(meta.get("title", args.topic))
    print(f"  → Slug: {slug}")

    # Step 5: Save
    post_path, meta_path = save(slug, draft, meta)

    # Step 6: Optionally publish to Ghost
    if args.publish_ghost:
        print("  → Publishing draft to Ghost")
        publish_to_ghost(meta, body)

    print(f"""
✅ Draft saved!

  {post_path}   — full blog post (markdown + frontmatter)
  {meta_path}   — SEO metadata for Ghost

Word count: ~{len(body.split())} words
Keyword:    {meta.get('keyword', args.keyword or '—')}
""")

    # Quick preview of the title + description
    if meta.get("title"):
        print(f"  Title:       {meta['title']}")
    if meta.get("description"):
        print(f"  Description: {meta['description']}")
    print()


if __name__ == "__main__":
    main()
