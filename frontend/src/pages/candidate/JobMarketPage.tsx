import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { jobsApi, resumesApi, applicationsApi, matchingApi, ApiError, type JobSummary, type ResumeSummary } from "@/lib/api";
import { useFetch } from "@/lib/hooks";
import { LOCATION_LABELS, SENIORITY_LABELS, JOB_TYPE_LABELS } from "@/lib/constants";
import PageHeader from "@/components/ui/PageHeader";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";

export default function JobMarketPage() {
  const { token } = useAuth();
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<JobSummary[] | null>(null);
  const [selectedJob, setSelectedJob] = useState<JobSummary | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applying, setApplying] = useState(false);
  const [appliedIds, setAppliedIds] = useState<Set<number>>(new Set());
  const [matchResult, setMatchResult] = useState<{ score: number; reasoning?: string } | null>(null);
  const [matchLoading, setMatchLoading] = useState(false);

  const { data: jobs, loading } = useFetch(
    () => (token ? jobsApi.list({ status: "published" }, token) : Promise.reject()),
    [token],
  );

  const { data: myResumes } = useFetch(
    () => (token ? resumesApi.list(token) : Promise.reject()),
    [token],
  );

  const activeResume = myResumes?.items.find(r => r.status === "active");

  async function search() {
    if (!token || !query.trim()) { setSearchResults(null); return; }
    setSearching(true);
    try {
      const res = await jobsApi.list({ q: query, status: "published" }, token);
      setSearchResults(res.items);
    } catch { setSearchResults([]); }
    finally { setSearching(false); }
  }

  async function runMatch(job: JobSummary) {
    if (!token || !activeResume) return;
    setMatchLoading(true); setMatchResult(null);
    try {
      const res = await matchingApi.runForJob(job.job_id, { resume_id: activeResume.resume_id }, token);
      const top = res.items[0];
      if (top) setMatchResult({ score: top.score, reasoning: top.reasoning });
    } catch { /* ignore */ }
    finally { setMatchLoading(false); }
  }

  async function applyToJob() {
    if (!token || !selectedJob || !activeResume) return;
    setApplyError(null); setApplying(true);
    try {
      await applicationsApi.create(selectedJob.job_id, activeResume.resume_id, token);
      setAppliedIds(s => new Set(s).add(selectedJob.job_id));
      setSelectedJob(null); setMatchResult(null);
    } catch (err) {
      setApplyError(err instanceof ApiError ? err.body.message : "Lỗi ứng tuyển.");
    } finally { setApplying(false); }
  }

  function openJob(job: JobSummary) {
    setSelectedJob(job); setMatchResult(null); setApplyError(null);
    runMatch(job);
  }

  const displayed = searchResults ?? jobs?.items ?? [];

  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Thị trường việc làm" />
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mb-4 flex gap-2">
          <input
            className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            placeholder="Tìm kiếm công việc..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && search()}
          />
          <button onClick={search} disabled={searching} className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700 disabled:opacity-50">
            {searching ? "..." : "Tìm"}
          </button>
          {searchResults !== null && (
            <button onClick={() => { setSearchResults(null); setQuery(""); }} className="rounded-md border px-3 py-2 text-sm text-slate-500 hover:bg-slate-50">Xóa</button>
          )}
        </div>

        {!activeResume && (
          <p className="mb-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
            Bạn cần kích hoạt một CV để ứng tuyển công việc.
          </p>
        )}

        {loading && <Spinner className="py-16" />}
        {!loading && displayed.length === 0 && (
          <EmptyState title="Không có công việc" body="Chưa có tin tuyển dụng phù hợp." />
        )}

        <div className="space-y-2">
          {displayed.map(job => (
            <div
              key={job.job_id}
              onClick={() => openJob(job)}
              className={`flex cursor-pointer items-center justify-between rounded-lg border bg-white px-4 py-3 hover:border-slate-400 ${selectedJob?.job_id === job.job_id ? "border-slate-500" : "border-slate-200"}`}
            >
              <div>
                <p className="font-medium text-slate-800">{job.title}</p>
                <p className="text-xs text-slate-400">
                  {LOCATION_LABELS[job.location] ?? job.location} · {SENIORITY_LABELS[job.seniority] ?? job.seniority} · {JOB_TYPE_LABELS[job.job_type] ?? job.job_type}
                </p>
                {job.skills.length > 0 && (
                  <p className="mt-1 text-xs text-slate-500">{job.skills.slice(0, 4).join(", ")}{job.skills.length > 4 ? "..." : ""}</p>
                )}
              </div>
              <div className="flex flex-col items-end gap-1">
                {appliedIds.has(job.job_id) && <span className="text-xs text-green-600 font-medium">Đã ứng tuyển</span>}
              </div>
            </div>
          ))}
        </div>

        {selectedJob && (
          <div className="mt-6 rounded-lg border border-slate-300 bg-white p-5">
            <div className="mb-3 flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-slate-800">{selectedJob.title}</h2>
                <p className="text-sm text-slate-500">
                  {LOCATION_LABELS[selectedJob.location]} · {SENIORITY_LABELS[selectedJob.seniority]} · {JOB_TYPE_LABELS[selectedJob.job_type]}
                </p>
              </div>
              <Badge value={selectedJob.status} label="Đang tuyển" />
            </div>

            {selectedJob.skills.length > 0 && (
              <p className="mb-2 text-sm text-slate-600"><span className="font-medium">Kỹ năng:</span> {selectedJob.skills.join(", ")}</p>
            )}
            {selectedJob.requirement && (
              <p className="mb-3 whitespace-pre-wrap text-sm text-slate-700">{selectedJob.requirement}</p>
            )}

            {matchLoading && <p className="mb-2 text-xs text-slate-400">Đang tính điểm phù hợp...</p>}
            {matchResult && (
              <div className="mb-3 rounded-md bg-blue-50 px-3 py-2 text-sm">
                <span className="font-medium text-blue-700">Độ phù hợp: {Math.round(matchResult.score * 100)}%</span>
                {matchResult.reasoning && <p className="mt-1 text-xs text-blue-600">{matchResult.reasoning}</p>}
              </div>
            )}

            {applyError && <p className="mb-2 text-sm text-red-500">{applyError}</p>}

            <div className="flex gap-2">
              {!appliedIds.has(selectedJob.job_id) ? (
                <button
                  onClick={applyToJob}
                  disabled={applying || !activeResume}
                  className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700 disabled:opacity-50"
                >
                  {applying ? "Đang ứng tuyển..." : "Ứng tuyển"}
                </button>
              ) : (
                <span className="rounded-md bg-green-100 px-4 py-2 text-sm text-green-700 font-medium">Đã ứng tuyển</span>
              )}
              <button onClick={() => setSelectedJob(null)} className="rounded-md border px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">Đóng</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
