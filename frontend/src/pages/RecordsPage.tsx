import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { resumesApi, jobsApi } from "@/lib/api";
import { useFetch } from "@/lib/hooks";
import { RESUME_STATUS_LABELS, JOB_STATUS_LABELS, LOCATION_LABELS, SENIORITY_LABELS } from "@/lib/constants";
import PageHeader from "@/components/ui/PageHeader";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";

export default function RecordsPage() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const isCandidate = user?.role === "candidate";

  const resumes = useFetch(
    () => (isCandidate && token ? resumesApi.list(token) : Promise.resolve(null)),
    [token, isCandidate],
  );
  const jobs = useFetch(
    () => (!isCandidate && token ? jobsApi.list({}, token) : Promise.resolve(null)),
    [token, isCandidate],
  );

  const loading = isCandidate ? resumes.loading : jobs.loading;
  const error = isCandidate ? resumes.error : jobs.error;

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title={isCandidate ? "CV của tôi" : "Tin tuyển dụng"}
        action={
          <div className="flex gap-2">
            <button onClick={() => navigate(isCandidate ? "/records/resumes/new" : "/records/jobs/new")}
              className="rounded-md bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-700">
              {isCandidate ? "+ Tạo CV" : "+ Tạo tin"}
            </button>
            <button onClick={() => navigate("/documents/upload")}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50">
              Tải tệp
            </button>
          </div>
        }
      />
      <div className="flex-1 overflow-y-auto p-6">
        {loading && <Spinner className="py-16" />}
        {error && <p className="text-sm text-red-500">{error}</p>}
        {!loading && !error && isCandidate && (
          resumes.data?.items.length === 0
            ? <EmptyState title="Chưa có CV" body="Tải CV hoặc tạo CV thủ công để bắt đầu tìm việc." action={{ label: "Tạo CV", onClick: () => navigate("/records/resumes/new") }} />
            : <div className="space-y-2">
                {resumes.data?.items.map(r => (
                  <div key={r.resume_id} onClick={() => navigate(`/records/resumes/${r.resume_id}`)}
                    className="flex cursor-pointer items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 hover:border-slate-400">
                    <div>
                      <p className="font-medium text-slate-800">{r.title}</p>
                      <p className="text-xs text-slate-400">{LOCATION_LABELS[r.location] ?? r.location} · {SENIORITY_LABELS[r.seniority] ?? r.seniority}</p>
                    </div>
                    <Badge value={r.status} label={RESUME_STATUS_LABELS[r.status]} />
                  </div>
                ))}
              </div>
        )}
        {!loading && !error && !isCandidate && (
          jobs.data?.items.length === 0
            ? <EmptyState title="Chưa có tin tuyển dụng" body="Tạo tin tuyển dụng thủ công hoặc tải JD." action={{ label: "Tạo tin", onClick: () => navigate("/records/jobs/new") }} />
            : <div className="space-y-2">
                {jobs.data?.items.map(j => (
                  <div key={j.job_id} onClick={() => navigate(`/records/jobs/${j.job_id}`)}
                    className="flex cursor-pointer items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 hover:border-slate-400">
                    <div>
                      <p className="font-medium text-slate-800">{j.title}</p>
                      <p className="text-xs text-slate-400">{LOCATION_LABELS[j.location] ?? j.location} · {SENIORITY_LABELS[j.seniority] ?? j.seniority}</p>
                    </div>
                    <Badge value={j.status} label={JOB_STATUS_LABELS[j.status]} />
                  </div>
                ))}
              </div>
        )}
      </div>
    </div>
  );
}
