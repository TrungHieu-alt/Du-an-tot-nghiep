import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { applicationsApi, invitesApi, ApiError } from "@/lib/api";
import { useFetch } from "@/lib/hooks";
import { APP_STATUS_LABELS, INVITE_STATUS_LABELS } from "@/lib/constants";
import PageHeader from "@/components/ui/PageHeader";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";

type Tab = "applications" | "invites";

export default function MyActivityPage() {
  const { token } = useAuth();
  const [tab, setTab] = useState<Tab>("applications");
  const [actionError, setActionError] = useState<string | null>(null);
  const [acting, setActing] = useState(false);

  const { data: applications, loading: appsLoading, reload: reloadApps } = useFetch(
    () => (token ? applicationsApi.list({}, token) : Promise.reject()),
    [token],
  );

  const { data: invites, loading: invitesLoading, reload: reloadInvites } = useFetch(
    () => (token ? invitesApi.list({}, token) : Promise.reject()),
    [token],
  );

  async function withdrawApplication(id: number) {
    if (!token) return;
    setActionError(null); setActing(true);
    try {
      await applicationsApi.updateStatus(id, "withdrawn", token);
      reloadApps();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.body.message : "Lỗi thao tác.");
    } finally { setActing(false); }
  }

  async function respondInvite(id: number, action: "accept" | "reject") {
    if (!token) return;
    setActionError(null); setActing(true);
    try {
      if (action === "accept") await invitesApi.accept(id, token);
      else await invitesApi.reject(id, token);
      reloadInvites();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.body.message : "Lỗi thao tác.");
    } finally { setActing(false); }
  }

  const loading = tab === "applications" ? appsLoading : invitesLoading;

  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Hoạt động của tôi" />
      <div className="border-b border-slate-200 px-6">
        <div className="flex gap-4">
          {(["applications", "invites"] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${tab === t ? "border-slate-800 text-slate-800" : "border-transparent text-slate-400 hover:text-slate-600"}`}
            >
              {t === "applications" ? "Đơn ứng tuyển" : "Lời mời"}
            </button>
          ))}
        </div>
      </div>

      {actionError && <p className="mx-6 mt-2 text-sm text-red-500">{actionError}</p>}

      <div className="flex-1 overflow-y-auto p-6">
        {loading && <Spinner className="py-16" />}

        {!loading && tab === "applications" && (
          applications?.items.length === 0
            ? <EmptyState title="Chưa có đơn ứng tuyển" body="Ứng tuyển công việc trong Thị trường việc làm." />
            : <div className="space-y-2">
                {applications?.items.map(app => (
                  <div key={app.application_id} className="rounded-lg border border-slate-200 bg-white px-4 py-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-700">Job #{app.job_id}</p>
                        <p className="text-xs text-slate-400">Resume #{app.resume_id} · App #{app.application_id}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge value={app.status} label={APP_STATUS_LABELS[app.status] ?? app.status} />
                        {app.status === "submitted" && (
                          <button
                            onClick={() => withdrawApplication(app.application_id)}
                            disabled={acting}
                            className="text-xs text-red-500 hover:text-red-700 disabled:opacity-50"
                          >
                            Rút đơn
                          </button>
                        )}
                      </div>
                    </div>
                    {app.events.length > 0 && (
                      <p className="mt-1 text-xs text-slate-400">
                        Cập nhật: {app.events[app.events.length - 1].to_status ?? app.status}
                      </p>
                    )}
                  </div>
                ))}
              </div>
        )}

        {!loading && tab === "invites" && (
          invites?.items.length === 0
            ? <EmptyState title="Chưa có lời mời" body="Nhà tuyển dụng sẽ mời bạn khi CV phù hợp." />
            : <div className="space-y-2">
                {invites?.items.map(inv => (
                  <div key={inv.invite_id} className="rounded-lg border border-slate-200 bg-white px-4 py-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-700">Job #{inv.job_id}</p>
                        <p className="text-xs text-slate-400">Resume #{inv.resume_id}</p>
                        {inv.message && <p className="mt-1 text-xs text-slate-500 italic">"{inv.message}"</p>}
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge value={inv.status} label={INVITE_STATUS_LABELS[inv.status] ?? inv.status} />
                        {inv.status === "pending" && (
                          <>
                            <button onClick={() => respondInvite(inv.invite_id, "accept")} disabled={acting} className="rounded-md bg-green-600 px-2.5 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-50">Chấp nhận</button>
                            <button onClick={() => respondInvite(inv.invite_id, "reject")} disabled={acting} className="rounded-md border border-slate-300 px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-50">Từ chối</button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
        )}
      </div>
    </div>
  );
}
