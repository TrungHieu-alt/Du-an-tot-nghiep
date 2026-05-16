import { useAuth } from "@/contexts/AuthContext";
import { notificationsApi, ApiError } from "@/lib/api";
import { useFetch } from "@/lib/hooks";
import PageHeader from "@/components/ui/PageHeader";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import { useState } from "react";

export default function NotificationsPage() {
  const { token } = useAuth();
  const [markingAll, setMarkingAll] = useState(false);

  const { data, loading, reload } = useFetch(
    () => (token ? notificationsApi.list(token) : Promise.reject()),
    [token],
  );

  async function markAll() {
    if (!token) return;
    setMarkingAll(true);
    try {
      await notificationsApi.markAllRead(token);
      reload();
    } catch { /* ignore */ }
    finally { setMarkingAll(false); }
  }

  async function markOne(id: number) {
    if (!token) return;
    try {
      await notificationsApi.markRead(id, token);
      reload();
    } catch { /* ignore */ }
  }

  const unreadCount = data?.items.filter(n => n.status === "unread").length ?? 0;

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Thông báo"
        action={
          unreadCount > 0
            ? <button onClick={markAll} disabled={markingAll} className="rounded-md border px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-50">
                Đánh dấu tất cả đã đọc
              </button>
            : undefined
        }
      />
      <div className="flex-1 overflow-y-auto p-6">
        {loading && <Spinner className="py-16" />}
        {!loading && data?.items.length === 0 && (
          <EmptyState title="Chưa có thông báo" body="Thông báo sẽ xuất hiện khi có hoạt động mới." />
        )}
        {!loading && (
          <div className="space-y-2">
            {data?.items.map(n => (
              <div
                key={n.notification_id}
                onClick={() => n.status === "unread" && markOne(n.notification_id)}
                className={`cursor-pointer rounded-lg border px-4 py-3 ${n.status === "unread" ? "border-blue-200 bg-blue-50" : "border-slate-200 bg-white"}`}
              >
                <p className={`text-sm font-medium ${n.status === "unread" ? "text-slate-800" : "text-slate-600"}`}>{n.title}</p>
                <p className="text-xs text-slate-500">{n.body}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
