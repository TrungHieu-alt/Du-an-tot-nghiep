import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { applicationsApi, ApiError } from "@/lib/api";
import { useFetch } from "@/lib/hooks";
import { APP_STATUS_LABELS } from "@/lib/constants";
import PageHeader from "@/components/ui/PageHeader";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";

const NEXT_STATUSES: Record<string, string[]> = {
  submitted: ["shortlisted", "rejected"],
  shortlisted: ["hired", "rejected"],
  hired: [],
  rejected: [],
  withdrawn: [],
};

export default function RecruiterApplicationsPage() {
  const { token } = useAuth();
  const [actionError, setActionError] = useState<string | null>(null);
  const [acting, setActing] = useState(false);

  const { data, loading, reload } = useFetch(
    () => (token ? applicationsApi.list({}, token) : Promise.reject()),
    [token],
  );

  async function updateStatus(id: number, status: string) {
    if (!token) return;
    setActionError(null); setActing(true);
    try {
      await applicationsApi.updateStatus(id, status, token);
      reload();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.body.message : "Lỗi cập nhật.");
    } finally { setActing(false); }
  }

  const STATUS_LABEL: Record<string, string> = {
    shortlisted: "Đưa vào danh sách",
    hired: "Tuyển dụng",
    rejected: "Từ chối",
  };

  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Quản lý ứng tuyển" />
      {actionError && <p className="mx-6 mt-2 text-sm text-red-500">{actionError}</p>}
      <div className="flex-1 overflow-y-auto p-6">
        {loading && <Spinner className="py-16" />}
        {!loading && data?.items.length === 0 && (
          <EmptyState title="Chưa có đơn ứng tuyển" body="Đơn ứng tuyển sẽ xuất hiện khi ứng viên ứng tuyển vào các tin của bạn." />
        )}
        {!loading && (
          <div className="space-y-2">
            {data?.items.map(app => (
              <div key={app.application_id} className="rounded-lg border border-slate-200 bg-white px-4 py-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-700">Job #{app.job_id} · Ứng viên #{app.candidate_user_id}</p>
                    <p className="text-xs text-slate-400">Resume #{app.resume_id} · App #{app.application_id}</p>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap justify-end">
                    <Badge value={app.status} label={APP_STATUS_LABELS[app.status] ?? app.status} />
                    {NEXT_STATUSES[app.status]?.map(s => (
                      <button
                        key={s}
                        onClick={() => updateStatus(app.application_id, s)}
                        disabled={acting}
                        className="rounded-md border border-slate-300 px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-50"
                      >
                        {STATUS_LABEL[s] ?? s}
                      </button>
                    ))}
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
