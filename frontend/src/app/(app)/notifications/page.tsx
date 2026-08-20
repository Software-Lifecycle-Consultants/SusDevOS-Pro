"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, BellOff, CheckCheck } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

interface Notification {
  NotificationId:  number;
  Type:            string;
  Title:           string;
  Body:            string | null;
  RelatedModule:   string | null;
  RelatedRecordId: number | null;
  IsRead:          boolean;
  CreatedAt:       string;
}

const TYPE_ICONS: Record<string, string> = {
  inventory_verified:  "✅",
  inventory_submitted: "📋",
  target_milestone:    "🎯",
  report_ready:        "📄",
  report_failed:       "❌",
  user_invited:        "👤",
  offset_validated:    "🌿",
  restoration_alert:   "⚠️",
};

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(mins / 60);
  const days  = Math.floor(hours / 24);
  if (days >= 1)  return `${days}d ago`;
  if (hours >= 1) return `${hours}h ago`;
  if (mins >= 1)  return `${mins}m ago`;
  return "just now";
}

export default function NotificationsPage() {
  const { activeEntityId } = useAuthStore();
  const queryClient = useQueryClient();
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};
  const qKey = ["notifications", activeEntityId, showUnreadOnly];

  const { data, isLoading } = useQuery<{ results: Notification[] }>({
    queryKey: qKey,
    queryFn: () => {
      const params = showUnreadOnly ? "?unread=true" : "";
      return axiosInstance.get(`/api/notifications/${params}`, { headers }).then((r) => r.data);
    },
    enabled: !!activeEntityId,
    refetchInterval: 30_000,
  });

  const markRead = useMutation({
    mutationFn: (id: number) =>
      axiosInstance.patch(`/api/notifications/${id}/`, { IsRead: true }, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllRead = useMutation({
    mutationFn: () =>
      axiosInstance.post("/api/notifications/read-all/", {}, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const notifications = data?.results ?? [];
  const unreadCount = notifications.filter((n) => !n.IsRead).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Notifications</h1>
          <p className="page-subtitle">
            {unreadCount > 0 ? `${unreadCount} unread` : "All caught up"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            className={`btn-sm ${showUnreadOnly ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setShowUnreadOnly((v) => !v)}
          >
            {showUnreadOnly ? "Showing unread" : "All"}
          </button>
          {unreadCount > 0 && (
            <button
              className="btn-secondary btn-sm flex items-center gap-1.5"
              disabled={markAllRead.isPending}
              onClick={() => markAllRead.mutate()}
            >
              <CheckCheck className="h-4 w-4" />
              Mark all read
            </button>
          )}
        </div>
      </div>

      <div className="card divide-y divide-surface-100 overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-sm text-surface-500">Loading…</div>
        ) : notifications.length === 0 ? (
          <div className="p-10 flex flex-col items-center gap-3 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-100">
              {showUnreadOnly ? <BellOff className="h-6 w-6 text-surface-400" /> : <Bell className="h-6 w-6 text-surface-400" />}
            </div>
            <p className="text-sm font-medium text-surface-700">
              {showUnreadOnly ? "No unread notifications" : "No notifications yet"}
            </p>
            <p className="text-xs text-surface-400 max-w-xs">
              Notifications appear here when inventories are verified, reports finish generating,
              milestones are due, or your team makes significant changes.
            </p>
          </div>
        ) : (
          notifications.map((n) => (
            <button
              key={n.NotificationId}
              className={[
                "w-full text-left flex items-start gap-4 px-5 py-4 transition-colors",
                n.IsRead ? "bg-white hover:bg-surface-50" : "bg-brand-50 hover:bg-brand-100/60",
              ].join(" ")}
              onClick={() => { if (!n.IsRead) markRead.mutate(n.NotificationId); }}
            >
              {/* Type icon */}
              <span className="mt-0.5 text-lg shrink-0 select-none" aria-hidden>
                {TYPE_ICONS[n.Type] ?? "🔔"}
              </span>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline justify-between gap-2">
                  <p className={`text-sm leading-snug ${n.IsRead ? "text-surface-700" : "font-semibold text-surface-900"}`}>
                    {n.Title}
                  </p>
                  <span className="shrink-0 text-xs text-surface-400">{timeAgo(n.CreatedAt)}</span>
                </div>
                {n.Body && (
                  <p className="mt-0.5 text-sm text-surface-500 line-clamp-2">{n.Body}</p>
                )}
                {n.RelatedModule && (
                  <p className="mt-1 text-xs text-surface-400 capitalize">
                    {n.RelatedModule.replace(/_/g, " ")}
                    {n.RelatedRecordId ? ` #${n.RelatedRecordId}` : ""}
                  </p>
                )}
              </div>

              {/* Unread dot */}
              {!n.IsRead && (
                <span className="mt-2 h-2 w-2 rounded-full bg-brand-500 shrink-0" aria-label="Unread" />
              )}
            </button>
          ))
        )}
      </div>
    </div>
  );
}

