import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://susdevos.com";
const API_BASE = process.env.NEXT_PUBLIC_API_URL  ?? "http://localhost:8000";

const STATIC_ROUTES: MetadataRoute.Sitemap = [
  { url: SITE_URL,                        priority: 1.0,  changeFrequency: "weekly"  },
  { url: `${SITE_URL}/features`,          priority: 0.9,  changeFrequency: "monthly" },
  { url: `${SITE_URL}/pricing`,           priority: 0.9,  changeFrequency: "monthly" },
  { url: `${SITE_URL}/founding-10`,       priority: 0.9,  changeFrequency: "weekly"  },
  { url: `${SITE_URL}/integrations`,      priority: 0.8,  changeFrequency: "monthly" },
  { url: `${SITE_URL}/standards`,         priority: 0.7,  changeFrequency: "monthly" },
  { url: `${SITE_URL}/blog`,             priority: 0.8,  changeFrequency: "daily"   },
  { url: `${SITE_URL}/register`,          priority: 0.6,  changeFrequency: "yearly"  },
  { url: `${SITE_URL}/login`,             priority: 0.4,  changeFrequency: "yearly"  },
  { url: `${SITE_URL}/legal/privacy`,     priority: 0.3,  changeFrequency: "yearly"  },
  { url: `${SITE_URL}/legal/terms`,       priority: 0.3,  changeFrequency: "yearly"  },
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Fetch published blog posts
  let blogRoutes: MetadataRoute.Sitemap = [];
  try {
    const res = await fetch(`${API_BASE}/api/public/blog/`, {
      next: { revalidate: 3600 },
    });
    if (res.ok) {
      const posts: { Slug: string; PublishedAt: string | null }[] = await res.json();
      blogRoutes = posts.map((p) => ({
        url:             `${SITE_URL}/blog/${p.Slug}`,
        lastModified:    p.PublishedAt ? new Date(p.PublishedAt) : new Date(),
        priority:        0.7,
        changeFrequency: "monthly" as const,
      }));
    }
  } catch {
    // Non-fatal — sitemap still returns static routes
  }

  return [...STATIC_ROUTES, ...blogRoutes];
}
