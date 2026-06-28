"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#f8fafc" }}>
        <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}>
          <div style={{ maxWidth: "400px", textAlign: "center" }}>
            <AlertTriangle style={{ width: 48, height: 48, color: "#ef4444", margin: "0 auto 16px" }} />
            <h1 style={{ fontSize: "1.25rem", fontWeight: 600, marginBottom: "8px", color: "#0f172a" }}>
              Something went wrong
            </h1>
            <p style={{ fontSize: "0.875rem", color: "#64748b", marginBottom: "24px" }}>
              An unexpected error occurred. Please try again or{" "}
              <a href="/contact" style={{ color: "#16a34a" }}>contact support</a>.
            </p>
            <button
              onClick={reset}
              style={{ background: "#16a34a", color: "#fff", border: "none", borderRadius: "8px", padding: "10px 20px", fontSize: "0.875rem", fontWeight: 600, cursor: "pointer" }}
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
