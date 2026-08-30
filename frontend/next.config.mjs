/** @type {import('next').NextConfig} */

// CSP: strict defaults, allow same-origin scripts + Next.js inline scripts.
// Adjust connect-src if you add third-party analytics or Sentry.
const CSP = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",   // 'unsafe-inline' required by Next.js RSC inline scripts
  "style-src 'self' 'unsafe-inline'",    // Tailwind inlines styles
  "img-src 'self' data: blob: https://*.tile.openstreetmap.org https://unpkg.com",
  "font-src 'self'",
  "connect-src 'self'",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const SECURITY_HEADERS = [
  { key: "X-DNS-Prefetch-Control",   value: "on" },
  { key: "X-Content-Type-Options",   value: "nosniff" },
  { key: "X-Frame-Options",          value: "DENY" },
  { key: "Referrer-Policy",          value: "strict-origin-when-cross-origin" },
  // geolocation=(self): the land-parcel map offers a "My location" control, and
  // geolocation=() would block navigator.geolocation for the whole origin — the
  // button would fail in production while working on localhost. Camera and
  // microphone stay fully disabled; nothing in the app uses them.
  { key: "Permissions-Policy",       value: "camera=(), microphone=(), geolocation=(self)" },
  { key: "Content-Security-Policy",  value: CSP },
];

const nextConfig = {
  output: "standalone", // produces .next/standalone/server.js for Docker

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/:path*`,
      },
    ];
  },

  async headers() {
    return [
      // Security headers on everything
      { source: "/:path*", headers: SECURITY_HEADERS },
      // Cache static marketing pages at the CDN for 5 minutes, stale-while-revalidate 1 hour
      {
        source: "/(|features|pricing|integrations|standards|about|contact|security)",
        headers: [{ key: "Cache-Control", value: "public, s-maxage=300, stale-while-revalidate=3600" }],
      },
      // Blog list — 5-minute CDN cache
      {
        source: "/blog",
        headers: [{ key: "Cache-Control", value: "public, s-maxage=300, stale-while-revalidate=3600" }],
      },
      // Individual blog posts — 10-minute CDN cache
      {
        source: "/blog/:slug",
        headers: [{ key: "Cache-Control", value: "public, s-maxage=600, stale-while-revalidate=86400" }],
      },
      // Sitemap + robots — 1-hour CDN cache
      {
        source: "/(sitemap.xml|robots.txt|rss.xml)",
        headers: [{ key: "Cache-Control", value: "public, s-maxage=3600, stale-while-revalidate=86400" }],
      },
      // App routes — never cached at CDN (authenticated, tenant-scoped)
      {
        source: "/(dashboard|emissions|inventories|targets|projects|land-parcels|ecosystem|restorations|offsets|reports|settings|notifications)/:path*",
        headers: [{ key: "Cache-Control", value: "private, no-store" }],
      },
    ];
  },
};

export default nextConfig;
