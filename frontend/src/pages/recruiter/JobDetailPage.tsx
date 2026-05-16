import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { jobsApi, ApiError } from "@/lib/api";
import { useFetch } from "@/lib/hooks";
import { LOCATION_LABELS, JOB_TYPE_LABELS, SENIORITY_LABELS, EDUCATION_LABELS, JOB_STATUS_LABELS, LOCATIONS, JOB_TYPES, SENIORITIES, EDUCATIONS } from "@/lib/constants";
import PageHeader from "@/components/ui/PageHeader";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import FormField, { inputCls } from "@/components/ui/FormField";

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const { token } = useAuth();
  const navigate = useNavigate();
  const id = Number(jobId);

  const { data: job, loading, error, setData } = useFetch(
    () => (token ? jobsApi.get(id, token) : Promise.reject()),
    [id, token],
  );

  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});

  function startEdit() {
    if (!job) return;
    setForm({ title: job.title, requirement: job.requirement, location: job.location, job_type: job.job_type, seniority: job.seniority, education: job.education, skills: job.skills.join(", ") });
    setEditing(true);
  }

  async function saveEdit() {
    if (!token || !job) return;
    setSaving(true); setActionError(null);
    try {
      const updated = await jobsApi.update(id, { ...form, skills: form.skills.split(",").map(s => s.trim()).filter(Boolean) }, token);
      setData(updated); setEditing(false);
    } catch (err) { setActionError(err instanceof ApiError ? err.body.message : "Lỗi lưu."); }
    finally { setSaving(false); }
  }

  async function lifecycle(action: "publish" | "close") {
    if (!token) return;
    setSaving(true); setActionError(null);
    try {
      const updated = action === "publish" ? await jobsApi.publish(id, token) : await jobsApi.close(id, token);
      setData(updated);
    } catch (err) { setActionError(err instanceof ApiError ? err.body.message : "Lỗi thao tác."); }
    finally { setSaving(false); }
  }

  if (loading) return <Spinner className="py-24" />;
  if (error) return <p className="p-6 text-sm text-red-500">{error}</p>;
  if (!job) return null;

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title={job.title}
        action={
          <div className="flex items-center gap-2">
            <Badge value={job.status} label={JOB_STATUS_LABELS[job.status]} />
            {!editing && (
              <>
                {job.status === "draft" && <button onClick={() => lifecycle("publish")} disabled={saving} className="rounded-md bg-blue-600 px-3 py-1.5 text-xs text-white hover:bg-blue-700 disabled:opacity-50">Đăng tuyển</button>}
                {job.status === "published" && <button onClick={() => lifecycle("close")} disabled={saving} className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-50">Đóng</button>}
                <button onClick={startEdit} className="rounded-md bg-slate-900 px-3 py-1.5 text-xs text-white hover:bg-slate-700">Chỉnh sửa</button>
              </>
            )}
            {editing && (
              <>
                <button onClick={saveEdit} disabled={saving} className="rounded-md bg-slate-900 px-3 py-1.5 text-xs text-white disabled:opacity-50">{saving ? "Đang lưu..." : "Lưu"}</button>
                <button onClick={() => setEditing(false)} className="rounded-md border px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50">Hủy</button>
              </>
            )}
          </div>
        }
      />
      {actionError && <p className="mx-6 mt-2 text-sm text-red-500">{actionError}</p>}
      <div className="flex-1 overflow-y-auto p-6">
        {!editing ? (
          <dl className="space-y-4">
            {([
              ["Địa điểm", LOCATION_LABELS[job.location] ?? job.location],
              ["Hình thức", JOB_TYPE_LABELS[job.job_type] ?? job.job_type],
              ["Cấp bậc", SENIORITY_LABELS[job.seniority] ?? job.seniority],
              ["Học vấn", EDUCATION_LABELS[job.education] ?? job.education],
              ["Kỹ năng", job.skills.join(", ") || "—"],
              ["Org ID", String(job.organization_id)],
            ] as [string, string][]).map(([k, v]) => (
              <div key={k}><dt className="text-xs font-medium uppercase text-slate-400">{k}</dt><dd className="mt-0.5 text-sm text-slate-700">{v}</dd></div>
            ))}
            <div><dt className="text-xs font-medium uppercase text-slate-400">Yêu cầu</dt><dd className="mt-0.5 whitespace-pre-wrap text-sm text-slate-700">{job.requirement || "—"}</dd></div>
          </dl>
        ) : (
          <div className="max-w-lg space-y-4">
            <FormField label="Tiêu đề"><input className={inputCls()} value={form.title} onChange={e => setForm(f => ({...f, title: e.target.value}))} /></FormField>
            <div className="grid grid-cols-2 gap-4">
              <FormField label="Địa điểm">
                <select className={inputCls()} value={form.location} onChange={e => setForm(f => ({...f, location: e.target.value}))}>
                  {LOCATIONS.map(l => <option key={l} value={l}>{LOCATION_LABELS[l]}</option>)}
                </select>
              </FormField>
              <FormField label="Hình thức">
                <select className={inputCls()} value={form.job_type} onChange={e => setForm(f => ({...f, job_type: e.target.value}))}>
                  {JOB_TYPES.map(t => <option key={t} value={t}>{JOB_TYPE_LABELS[t]}</option>)}
                </select>
              </FormField>
              <FormField label="Cấp bậc">
                <select className={inputCls()} value={form.seniority} onChange={e => setForm(f => ({...f, seniority: e.target.value}))}>
                  {SENIORITIES.map(s => <option key={s} value={s}>{SENIORITY_LABELS[s]}</option>)}
                </select>
              </FormField>
              <FormField label="Học vấn">
                <select className={inputCls()} value={form.education} onChange={e => setForm(f => ({...f, education: e.target.value}))}>
                  {EDUCATIONS.map(e => <option key={e} value={e}>{EDUCATION_LABELS[e]}</option>)}
                </select>
              </FormField>
            </div>
            <FormField label="Kỹ năng (phân cách bằng dấu phẩy)"><input className={inputCls()} value={form.skills} onChange={e => setForm(f => ({...f, skills: e.target.value}))} /></FormField>
            <FormField label="Yêu cầu công việc"><textarea className={inputCls()} rows={5} value={form.requirement} onChange={e => setForm(f => ({...f, requirement: e.target.value}))} /></FormField>
          </div>
        )}
        <button onClick={() => navigate("/records")} className="mt-6 text-sm text-slate-400 hover:text-slate-600">← Quay lại</button>
      </div>
    </div>
  );
}
