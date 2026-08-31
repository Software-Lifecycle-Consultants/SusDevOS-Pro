"use client";

import { useEffect, useRef, useId, useState } from "react";
import { cn } from "@/lib/utils";

interface Props {
  chart: string;
  className?: string;
}

// Diagram content is always static source code, not user input — loose security level is safe here.
export function MermaidDiagram({ chart, className }: Props) {
  const rawId = useId();
  const id = `mmd${rawId.replace(/\W/g, "")}`;
  const ref = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    import("mermaid").then(async ({ default: mermaid }) => {
      mermaid.initialize({
        startOnLoad: false,
        theme: "default",
        securityLevel: "loose",
      });
      try {
        const { svg } = await mermaid.render(id, chart);
        if (alive && ref.current) {
          ref.current.innerHTML = svg;
          setReady(true);
        }
      } catch (err) {
        if (alive)
          setError(err instanceof Error ? err.message : "Render failed");
      }
    });

    return () => {
      alive = false;
    };
  }, [chart, id]);

  if (error) {
    return (
      <div className="rounded border border-red-200 bg-red-50 p-4">
        <p className="mb-2 text-sm font-medium text-red-700">
          Diagram failed to render
        </p>
        <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-surface-600">
          {chart}
        </pre>
      </div>
    );
  }

  return (
    <div className={cn("min-h-[120px]", className)}>
      {!ready && (
        <div className="flex items-center gap-2 py-12 text-sm text-surface-400">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-surface-200 border-t-brand-500" />
          Rendering diagram…
        </div>
      )}
      <div
        ref={ref}
        className={cn(
          "overflow-x-auto [&_svg]:max-w-full [&_svg]:h-auto",
          !ready && "hidden",
        )}
      />
    </div>
  );
}
