import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { resumesApi, jobsApi, invitesApi, matchingApi, ApiError, type ResumeSummary, type JobSummary } from "@/lib/api";
import { useFetch } from "@/lib/hooks";
import { LOCATION_LABELS, SENIORITY_LABELS, JOB_TYPE_LABELS } from "@/lib/constants";
import PageHeader from "@/components/ui/PageHeader";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";

export default function TalentMarketPage() {
  const { token } = useAuth();
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<ResumeSummary[] | null>(null);
  const [selectedResume, setSelectedResume] = useState<ResumeSummary | null>(null);
  const [inviteMessage, setInviteMessage] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [invitedIds, setInvitedIds] = useState<Set<number>>(new Set());
  const [matchResult, setMatchResult] = useState<{ score: number; reasoning?: string } | null>(null);
  const [matchLoading, setMatchLoading] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);

  const { data: jobs } = useFetch(
    () => (token ? jobsApi.list({ status: "published" }, token) : Promise.reject()),
    [token],
  );

  const { data: resumes, loading } = useFetch(
    () => (token ? resumesApi.list(token) : Promise.reject()),
    [token],
  );

  async function search() {
    if (!token || !query.trim()) { setSearchResults(null); return; }
    setSearching(true);
    try {
      const res = await resumesApi.list(token);
      const filtered = res.items.filter(r =>
        r.title.toLowerCase().includes(query.toLowerCase()) ||
        r.skills.some(s => s.toLowerCase().includes(query.toLowerCase()))
      );
      setSearchResults(filtered);
    } catch { setSearchResults([]); }
    finally { setSearching(false); }
  }

  async function runMatch(resume: ResumeSummary, jobId: number) {
    if (!token) return;
    setMatchLoading(true); setMatchResult(null);
    try {
      const res = await matchingApi.runForResume(resume.resume_id, { job_id: jobId }, token);
      const top = res.items[0];
      if (top) setMatchResult({ score: top.score, reasoning: top.reasoning });
    } catch { /* ignore */ }
    finally { setMatchLoading(false); }
  }

  function openResume(resume: ResumeSummary) {
    setSelectedResume(resume); setMatchResult(null); setInviteError(null); setInviteMessage("");
    if (selectedJobId) runMatch(resume, selectedJobId);
  }

  async function sendInvite() {
    if (!token || !selectedResume || !selectedJobId) return;
    setInviteError(null); setInviting(true);
    try {
      await invitesApi.create(selectedJobId, selectedResume.resume_id, inviteMessage || null, token);
      setInvitedIds(s => new Set(s).add(selectedResume.resume_id));
      setSelectedResume(null);
    } catch (err) {
      setInviteError(err instanceof ApiError ? err.body.message : "Lỗi mời ứng viên.");
    } finally { setInviting(false); }
  }

  const displayed = searchResults ?? resumes?.items.filter(r => r.status === "active") ?? [];
  const publishedJobs = jobs?.items.filter((j: JobSummary) => j.status === "published") ?? [];

  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Thị trường ứng viên" />
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mb-4 flex gap-2">
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            value={selectedJobId ?? ""}
            onChange={e => { setSelectedJobId(Number(e.target.value) || null); setMatchResult(null); }}
          >
            <option value="">Chọn tin tuyển dụng để match...</option>
            {publishedJobs.map((j: JobSummary) => (
              <option key={j.job_id} value={j.job_id}>{j.title}</option>
            ))}
          </select>
        </div>

        <div className="mb-4 flex gap-2">
          <input
            className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            placeholder="Tìm ứng viên theo kỹ năng hoặc tiêu đề..."
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

        {loading && <Spinner className="py-16" />}
        {!loading && displayed.length === 0 && (
          <EmptyState title="Không có ứng viên" body="Chưa có CV đang hoạt động trong hệ thống." />
        )}

        <div className="space-y-2">
          {displayed.map(r => (
            <div
              key={r.resume_id}
              onClick={() => openResume(r)}
              className={`flex cursor-pointer items-center justify-between rounded-lg border bg-white px-4 py-3 hover:border-slate-400 ${selectedResume?.resume_id === r.resume_id ? "border-slate-500" : "border-slate-200"}`}
            >
              <div>
                <p className="font-medium text-slate-800">{r.title}</p>
                <p className="text-xs text-slate-400">
                  {LOCATION_LABELS[r.location] ?? r.location} · {SENIORITY_LABELS[r.seniority] ?? r.seniority} · {JOB_TYPE_LABELS[r.job_type] ?? r.job_type}
                </p>
                {r.skills.length > 0 && (
                  <p className="mt-1 text-xs text-slate-500">{r.skills.slice(0, 4).join(", ")}{r.skills.length > 4 ? "..." : ""}</p>
                )}
              </div>
              {invitedIds.has(r.resume_id) && <span className="text-xs text-green-600 font-medium">Đã mời</span>}
            </div>
          ))}
        </div>

        {selectedResume && (
          <div className="mt-6 rounded-lg border border-slate-300 bg-white p-5">
            <div className="mb-3">
              <h2 className="font-semibold text-slate-800">{selectedResume.title}</h2>
              <p className="text-sm text-slate-500">
                {LOCATION_LABELS[selectedResume.location]} · {SENIORITY_LABELS[selectedResume.seniority]} · {JOB_TYPE_LABELS[selectedResume.job_type]}
              </p>
              {selectedResume.skills.length > 0 && (
                <p className="mt-1 text-sm text-slate-600"><span className="font-medium">Kỹ năng:</span> {selectedResume.skills.join(", ")}</p>
              )}
            </div>

            {matchLoading && <p className="mb-2 text-xs text-slate-400">Đang tính điểm phù hợp...</p>}
            {matchResult && (
              <div className="mb-3 rounded-md bg-blue-50 px-3 py-2 text-sm">
                <span className="font-medium text-blue-700">Độ phù hợp: {Math.round(matchResult.score * 100)}%</span>
                {matchResult.reasoning && <p className="mt-1 text-xs text-blue-600">{matchResult.reasoning}</p>}
              </div>
            )}

            {!invitedIds.has(selectedResume.resume_id) && (
              <div className="mb-3">
                <textarea
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                  rows={2}
                  placeholder="Lời nhắn (tùy chọn)..."
                  value={inviteMessage}
                  onChange={e => setInviteMessage(e.target.value)}
                />
              </div>
            )}

            {inviteError && <p className="mb-2 text-sm text-red-500">{inviteError}</p>}

            <div className="flex gap-2">
              {!invitedIds.has(selectedResume.resume_id) ? (
                <button
                  onClick={sendInvite}
                  disabled={inviting || !selectedJobId}
                  title={!selectedJobId ? "Chọn tin tuyển dụng trước" : undefined}
                  className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700 disabled:opacity-50"
                >
                  {inviting ? "Đang gửi..." : "Mời ứng tuyển"}
                </button>
              ) : (
                <span className="rounded-md bg-green-100 px-4 py-2 text-sm text-green-700 font-medium">Đã mời</span>
              )}
              <button onClick={() => setSelectedResume(null)} className="rounded-md border px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">Đóng</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
