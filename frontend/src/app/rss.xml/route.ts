import { NextResponse } from "next/server";

const SITE_URL  = process.env.NEXT_PUBLIC_SITE_URL ?? "https://susdevos.com";
const API_BASE  = process.env.NEXT_PUBLIC_API_URL  ?? "http://localhost:8000";
const SITE_NAME = "SusDevOS Blog";
const SITE_DESC = "Practical guides on GHG reporting, SBTi, TNFD and sustainable development.";

interface Post {
  BlogId:         number;
  Title:          string;
  Slug:           string;
  PostBody:       string;
  PublishedAt:    string | null;
  SeoTitle:       string | null;
  SeoDescription: string | null;
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g,  "&amp;")
    .replace(/</g,  "&lt;")
    .replace(/>/g,  "&gt;")
    .replace(/"/g,  "&quot;")
    .replace(/'/g,  "&apos;");
}

function excerpt(post: Post): string {
  if (post.SeoDescription) return post.SeoDescription;
  return post.PostBody.replace(/<[^>]+>/g, "").slice(0, 200).trim() + "…";
}

export async function GET() {
  let posts: Post[] = [];
  try {
    const res = await fetch(`${API_BASE}/api/public/blog/`, {
      next: { revalidate: 600 },
    });
    if (res.ok) posts = await res.json();
  } catch { /* return empty feed */ }

  const items = posts
    .map((post) => {
      const title   = escapeXml(post.SeoTitle ?? post.Title);
      const desc    = escapeXml(excerpt(post));
      const link    = `${SITE_URL}/blog/${post.Slug}`;
      const pubDate = post.PublishedAt
        ? new Date(post.PublishedAt).toUTCString()
        : new Date().toUTCString();

      return `
    <item>
      <title>${title}</title>
      <link>${link}</link>
      <guid isPermaLink="true">${link}</guid>
      <description>${desc}</description>
      <pubDate>${pubDate}</pubDate>
    </item>`.trim();
    })
    .join("\n    ");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${escapeXml(SITE_NAME)}</title>
    <link>${SITE_URL}/blog</link>
    <description>${escapeXml(SITE_DESC)}</description>
    <language>en-gb</language>
    <atom:link href="${SITE_URL}/rss.xml" rel="self" type="application/rss+xml"/>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    ${items}
  </channel>
</rss>`;

  return new NextResponse(xml, {
    headers: {
      "Content-Type":  "application/rss+xml; charset=utf-8",
      "Cache-Control": "public, s-maxage=600, stale-while-revalidate=300",
    },
  });
}
