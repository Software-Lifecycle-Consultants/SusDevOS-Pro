import type { NextConfig } from "next";

const SECURITY_HEADERS = [
  { key: "X-DNS-Prefetch-Control",   value: "on" },
  { key: "X-Content-Type-Options",   value: "nosniff" },
  { key: "X-Frame-Options",          value: "DENY" },
  { key: "Referrer-Policy",          value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy",       value: "camera=(), microphone=(), geolocation=()" },
];

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source:      "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/:path*`,
      },
    ];
  },

  async headers() {
    return [
      // Security headers on everything
      {
        source:  "/:path*",
        headers: SECURITY_HEADERS,
      },
      // Cache static marketing pages at the CDN for 5 minutes, stale-while-revalidate 1 hour
      {
        source: "/(|features|pricing|integrations|standards|about|contact|security)",
        headers: [
          { key: "Cache-Control", value: "public, s-maxage=300, stale-while-revalidate=3600" },
        ],
      },
      // Blog list — 5-minute CDN cache
      {
        source: "/blog",
        headers: [
          { key: "Cache-Control", value: "public, s-maxage=300, stale-while-revalidate=3600" },
        ],
      },
      // Individual blog posts — 10-minute CDN cache
      {
        source: "/blog/:slug",
        headers: [
          { key: "Cache-Control", value: "public, s-maxage=600, stale-while-revalidate=86400" },
        ],
      },
      // Sitemap + robots — 1-hour CDN cache
      {
        source: "/(sitemap.xml|robots.txt|rss.xml)",
        headers: [
          { key: "Cache-Control", value: "public, s-maxage=3600, stale-while-revalidate=86400" },
        ],
      },
      // App routes — never cached at CDN (authenticated, tenant-scoped)
      {
        source: "/(dashboard|emissions|inventories|targets|projects|land-parcels|ecosystem|restorations|offsets|reports|settings|notifications)/:path*",
        headers: [
          { key: "Cache-Control", value: "private, no-store" },
        ],
      },
    ];
  },
};

export default nextConfig;
