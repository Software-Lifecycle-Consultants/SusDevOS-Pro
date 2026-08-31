"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { MermaidDiagram } from "@/components/MermaidDiagram";
import { DIAGRAMS } from "./_diagrams";

export default function ArchitecturePage() {
  const router = useRouter();
  const { user } = useAuthStore();

  useEffect(() => {
    if (user && !user.IsSuperAdmin) router.replace("/dashboard");
  }, [user, router]);

  // Render nothing while auth store hydrates or while redirecting
  if (!user || !user.IsSuperAdmin) return null;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* ── Header ── */}
      <div className="shrink-0 border-b border-surface-200 bg-white px-6 py-4">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-surface-900">Architecture</h1>
          <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-700">
            Super Admin
          </span>
        </div>
        <p className="mt-0.5 text-sm text-surface-500">
          C4 structural decomposition — four levels of zoom from user interactions to inner
          calculation code.
        </p>
      </div>

      {/* ── Tabs ── */}
      <div className="flex-1 overflow-y-auto">
        <Tabs defaultValue="l1" className="flex h-full flex-col">
          <div className="shrink-0 border-b border-surface-200 bg-white px-6 pt-3">
            <TabsList className="h-auto gap-1 bg-transparent p-0">
              {DIAGRAMS.map((d) => (
                <TabsTrigger
                  key={d.id}
                  value={d.id}
                  className="rounded-t-md border border-transparent px-3 py-2 text-xs font-medium data-[state=active]:border-surface-200 data-[state=active]:border-b-white data-[state=active]:bg-white data-[state=active]:shadow-none"
                >
                  <span className="text-surface-400 mr-1.5">{d.level}</span>
                  {d.tab}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          <div className="flex-1 overflow-y-auto">
            {DIAGRAMS.map((d) => (
              <TabsContent key={d.id} value={d.id} className="m-0 h-full p-6">
                <div className="mb-4">
                  <h2 className="text-base font-semibold text-surface-800">{d.title}</h2>
                  <p className="mt-1 text-sm text-surface-500">{d.description}</p>
                </div>
                <div className="rounded-lg border border-surface-200 bg-white p-4">
                  <MermaidDiagram chart={d.chart} />
                </div>
              </TabsContent>
            ))}
          </div>
        </Tabs>
      </div>
    </div>
  );
}
