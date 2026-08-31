import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Calendar, Clock } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Post {
  BlogId:         number;
  Title:          string;
  Slug:           string;
  PostBody:       string;
  PublishedAt:    string | null;
  SeoTitle:       string;
  SeoDescription: string;
  EmbedUrls:      string[];
  FeaturedImageId: number | null;
}

const API_BASE     = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SITE_URL     = process.env.NEXT_PUBLIC_SITE_URL ?? "https://susdevos.com";
const SITE_NAME    = "SusDevOS";

async function getPost(slug: string): Promise<Post | null> {
  try {
    const res = await fetch(`${API_BASE}/api/public/blog/${slug}/`, {
      next: { revalidate: 300 },
    });
    if (res.status === 404) return null;
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

async function getAllSlugs(): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE}/api/public/blog/`, { next: { revalidate: 3600 } });
    if (!res.ok) return [];
    const posts: Pick<Post, "Slug">[] = await res.json();
    return posts.map((p) => p.Slug);
  } catch {
    return [];
  }
}

// Pre-generate all published post paths at build time
export async function generateStaticParams() {
  const slugs = await getAllSlugs();
  return slugs.map((slug) => ({ slug }));
}

// Per-post SEO metadata
export async function generateMetadata(
  { params }: { params: { slug: string } }
): Promise<Metadata> {
  const post = await getPost(params.slug);
  if (!post) return { title: "Not found" };

  const title       = post.SeoTitle ?? post.Title;
  const description = post.SeoDescription ?? `Read "${post.Title}" on the SusDevOS blog.`;
  const url         = `${SITE_URL}/blog/${post.Slug}`;

  return {
    title,
    description,
    alternates:  { canonical: url },
    openGraph: {
      title,
      description,
      url,
      type:        "article",
      siteName:    SITE_NAME,
      publishedTime: post.PublishedAt ?? undefined,
    },
    twitter: {
      card:        "summary_large_image",
      title,
      description,
    },
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function readingTime(body: string): number {
  return Math.max(1, Math.ceil(body.trim().split(/\s+/).length / 200));
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric", month: "long", year: "numeric",
  });
}

function formatDateISO(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toISOString();
}

// ─────────────────────────────────────────────────────────────────────────────
// JSON-LD structured data
// ─────────────────────────────────────────────────────────────────────────────

function ArticleJsonLd({ post }: { post: Post }) {
  const schema = {
    "@context":       "https://schema.org",
    "@type":          "Article",
    "headline":       post.SeoTitle ?? post.Title,
    "description":    post.SeoDescription ?? undefined,
    "url":            `${SITE_URL}/blog/${post.Slug}`,
    "datePublished":  formatDateISO(post.PublishedAt),
    "dateModified":   formatDateISO(post.PublishedAt),
    "publisher": {
      "@type": "Organization",
      "name":  SITE_NAME,
      "url":   SITE_URL,
    },
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id":   `${SITE_URL}/blog/${post.Slug}`,
    },
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema).replace(/</g, "\\u003c") }}
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

export default async function BlogPostPage({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug);
  if (!post) notFound();

  const mins = readingTime(post.PostBody);

  return (
    <>
      <ArticleJsonLd post={post} />

      {/* Header */}
      <section
        className="relative overflow-hidden py-16 sm:py-20"
        style={{
          background: [
            "radial-gradient(ellipse 70% 50% at 50% 0%, rgba(22,163,74,0.1) 0%, transparent 70%)",
            "#0f172a",
          ].join(", "),
        }}
      >
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage: "radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />
        <div className="relative mx-auto max-w-3xl px-4 sm:px-6">
          <Link
            href="/blog"
            className="mb-8 inline-flex items-center gap-1.5 text-sm text-surface-400 transition-colors hover:text-white"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            All articles
          </Link>

          {/* Meta */}
          <div className="mb-5 flex flex-wrap items-center gap-4 text-sm text-surface-400">
            {post.PublishedAt && (
              <span className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5" />
                <time dateTime={formatDateISO(post.PublishedAt)}>
                  {formatDate(post.PublishedAt)}
                </time>
              </span>
            )}
            <span className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              {mins} min read
            </span>
          </div>

          <h1 className="text-3xl font-bold leading-tight text-white sm:text-4xl lg:text-5xl">
            {post.Title}
          </h1>

          {post.SeoDescription && (
            <p className="mt-5 text-lg leading-relaxed text-surface-300">
              {post.SeoDescription}
            </p>
          )}
        </div>
      </section>

      {/* Body */}
      <section className="bg-white py-14 sm:py-16">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          {/* PostBody is Markdown — react-markdown renders it safely (no dangerouslySetInnerHTML). */}
          <div className="
            text-surface-700 leading-relaxed
            [&>h2]:mt-10 [&>h2]:mb-4 [&>h2]:text-2xl [&>h2]:font-bold [&>h2]:text-surface-900
            [&>h3]:mt-8 [&>h3]:mb-3 [&>h3]:text-xl [&>h3]:font-semibold [&>h3]:text-surface-900
            [&>p]:mb-5 [&>p]:text-[17px] [&>p]:leading-8
            [&>ul]:mb-5 [&>ul]:ml-6 [&>ul]:list-disc [&>ul]:space-y-2
            [&>ol]:mb-5 [&>ol]:ml-6 [&>ol]:list-decimal [&>ol]:space-y-2
            [&>li]:text-[17px] [&>li]:leading-7
            [&>blockquote]:my-6 [&>blockquote]:border-l-4 [&>blockquote]:border-brand-300
            [&>blockquote]:pl-5 [&>blockquote]:italic [&>blockquote]:text-surface-500
            [&>pre]:my-6 [&>pre]:overflow-x-auto [&>pre]:rounded-xl [&>pre]:bg-surface-900
            [&>pre]:p-5 [&>pre]:text-sm [&>pre]:text-surface-100
            [&>code]:rounded [&>code]:bg-surface-100 [&>code]:px-1.5 [&>code]:py-0.5
            [&>code]:text-sm [&>code]:font-mono [&>code]:text-surface-800
            [&>hr]:my-10 [&>hr]:border-surface-200
            [&>a]:text-brand-600 [&>a]:underline [&>a:hover]:text-brand-800
            [&>img]:my-8 [&>img]:rounded-xl [&>img]:shadow-md
            [&>table]:my-6 [&>table]:w-full [&>table]:border-collapse
            [&>table>thead>tr>th]:border [&>table>thead>tr>th]:border-surface-200
            [&>table>thead>tr>th]:bg-surface-50 [&>table>thead>tr>th]:px-4
            [&>table>thead>tr>th]:py-2 [&>table>thead>tr>th]:text-left
            [&>table>thead>tr>th]:text-sm [&>table>thead>tr>th]:font-semibold
            [&>table>tbody>tr>td]:border [&>table>tbody>tr>td]:border-surface-200
            [&>table>tbody>tr>td]:px-4 [&>table>tbody>tr>td]:py-2 [&>table>tbody>tr>td]:text-sm
          ">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {post.PostBody}
            </ReactMarkdown>
          </div>

          {/* Share + back */}
          <div className="mt-14 flex items-center justify-between border-t border-surface-200 pt-8">
            <Link
              href="/blog"
              className="inline-flex items-center gap-1.5 text-sm text-surface-500 transition-colors hover:text-surface-900"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              All articles
            </Link>
            <div className="flex items-center gap-3">
              <span className="text-xs text-surface-400">Share:</span>
              <a
                href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(post.Title)}&url=${encodeURIComponent(`${SITE_URL}/blog/${post.Slug}`)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-surface-500 underline underline-offset-4 hover:text-surface-800"
              >
                X / Twitter
              </a>
              <a
                href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(`${SITE_URL}/blog/${post.Slug}`)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-surface-500 underline underline-offset-4 hover:text-surface-800"
              >
                LinkedIn
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-surface-100 bg-surface-50 py-16">
        <div className="mx-auto max-w-xl px-4 sm:px-6 text-center">
          <h3 className="mb-2 text-xl font-bold text-surface-900">
            Ready to build your GHG inventory?
          </h3>
          <p className="mb-6 text-sm text-surface-500">
            SusDevOS calculates Scope 1, 2 and 3 emissions and generates audit-ready reports aligned to GHG Protocol, Verra, and TNFD. Free to start.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700"
          >
            Start for free
          </Link>
        </div>
      </section>
    </>
  );
}
