import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { resumesApi, ApiError } from "@/lib/api";
import { useFetch } from "@/lib/hooks";
import { LOCATION_LABELS, JOB_TYPE_LABELS, SENIORITY_LABELS, EDUCATION_LABELS, RESUME_STATUS_LABELS, LOCATIONS, JOB_TYPES, SENIORITIES, EDUCATIONS } from "@/lib/constants";
import PageHeader from "@/components/ui/PageHeader";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import FormField, { inputCls } from "@/components/ui/FormField";

export default function ResumeDetailPage() {
  const { resumeId } = useParams<{ resumeId: string }>();
  const { token } = useAuth();
  const navigate = useNavigate();
  const id = Number(resumeId);

  const { data: resume, loading, error, setData } = useFetch(
    () => (token ? resumesApi.get(id, token) : Promise.reject()),
    [id, token],
  );

  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});

  function startEdit() {
    if (!resume) return;
    setForm({
      title: resume.title, summary: resume.summary, experience: resume.experience,
      location: resume.location, job_type: resume.job_type,
      seniority: resume.seniority, education: resume.education,
      skills: resume.skills.join(", "),
    });
    setEditing(true);
  }

  async function saveEdit() {
    if (!token || !resume) return;
    setSaving(true); setActionError(null);
    try {
      const updated = await resumesApi.update(id, {
        ...form,
        skills: form.skills.split(",").map(s => s.trim()).filter(Boolean),
      }, token);
      setData(updated); setEditing(false);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.body.message : "Lỗi lưu.");
    } finally { setSaving(false); }
  }

  async function lifecycle(action: "activate" | "archive") {
    if (!token) return;
    setSaving(true); setActionError(null);
    try {
      const updated = action === "activate"
        ? await resumesApi.activate(id, token)
        : await resumesApi.archive(id, token);
      setData(updated);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.body.message : "Lỗi thao tác.");
    } finally { setSaving(false); }
  }

  if (loading) return <Spinner className="py-24" />;
  if (error) return <p className="p-6 text-sm text-red-500">{error}</p>;
  if (!resume) return null;

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title={resume.title}
        action={
          <div className="flex items-center gap-2">
            <Badge value={resume.status} label={RESUME_STATUS_LABELS[resume.status]} />
            {!editing && (
              <>
                {resume.status !== "active" && <button onClick={() => lifecycle("activate")} disabled={saving} className="rounded-md bg-green-600 px-3 py-1.5 text-xs text-white hover:bg-green-700 disabled:opacity-50">Kích hoạt</button>}
                {resume.status !== "archived" && <button onClick={() => lifecycle("archive")} disabled={saving} className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-50">Lưu trữ</button>}
                <button onClick={startEdit} className="rounded-md bg-slate-900 px-3 py-1.5 text-xs text-white hover:bg-slate-700">Chỉnh sửa</button>
              </>
            )}
            {editing && (
              <>
                <button onClick={saveEdit} disabled={saving} className="rounded-md bg-slate-900 px-3 py-1.5 text-xs text-white hover:bg-slate-700 disabled:opacity-50">{saving ? "Đang lưu..." : "Lưu"}</button>
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
              ["Địa điểm", LOCATION_LABELS[resume.location] ?? resume.location],
              ["Hình thức", JOB_TYPE_LABELS[resume.job_type] ?? resume.job_type],
              ["Cấp bậc", SENIORITY_LABELS[resume.seniority] ?? resume.seniority],
              ["Học vấn", EDUCATION_LABELS[resume.education] ?? resume.education],
              ["Kỹ năng", resume.skills.join(", ") || "—"],
            ] as [string, string][]).map(([k, v]) => (
              <div key={k}><dt className="text-xs font-medium text-slate-400 uppercase">{k}</dt><dd className="mt-0.5 text-sm text-slate-700">{v}</dd></div>
            ))}
            <div><dt className="text-xs font-medium text-slate-400 uppercase">Tóm tắt</dt><dd className="mt-0.5 whitespace-pre-wrap text-sm text-slate-700">{resume.summary || "—"}</dd></div>
            <div><dt className="text-xs font-medium text-slate-400 uppercase">Kinh nghiệm</dt><dd className="mt-0.5 whitespace-pre-wrap text-sm text-slate-700">{resume.experience || "—"}</dd></div>
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
            <FormField label="Tóm tắt"><textarea className={inputCls()} rows={3} value={form.summary} onChange={e => setForm(f => ({...f, summary: e.target.value}))} /></FormField>
            <FormField label="Kinh nghiệm"><textarea className={inputCls()} rows={4} value={form.experience} onChange={e => setForm(f => ({...f, experience: e.target.value}))} /></FormField>
          </div>
        )}
        <button onClick={() => navigate("/records")} className="mt-6 text-sm text-slate-400 hover:text-slate-600">← Quay lại</button>
      </div>
    </div>
  );
}
