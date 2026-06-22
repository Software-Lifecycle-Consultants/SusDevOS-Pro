import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default:  "SusDevOS — GHG Reporting & Ecosystem Tracking",
    template: "%s | SusDevOS",
  },
  description:
    "Calculate Scope 1, 2 and 3 emissions, track biodiversity impacts, and generate audit-ready GHG inventory reports. Aligned to GHG Protocol, SBTi, CDP and TNFD.",
  metadataBase: new URL("https://susdevos.com"),
  openGraph: {
    siteName: "SusDevOS",
    type:     "website",
    locale:   "en_GB",
  },
  twitter: {
    card: "summary_large_image",
  },
  robots: {
    index:  true,
    follow: true,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
