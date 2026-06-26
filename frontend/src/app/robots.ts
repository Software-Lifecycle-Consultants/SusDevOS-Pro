import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://susdevos.com";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/"],
        disallow: [
          "/api/",
          "/dashboard",
          "/emissions",
          "/inventories",
          "/targets",
          "/projects",
          "/land-parcels",
          "/ecosystem",
          "/restorations",
          "/offsets",
          "/reports",
          "/settings",
          "/notifications",
        ],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
