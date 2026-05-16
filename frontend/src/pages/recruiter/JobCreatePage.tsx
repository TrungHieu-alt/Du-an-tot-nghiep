import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { jobsApi, ApiError } from "@/lib/api";
import { LOCATIONS, LOCATION_LABELS, JOB_TYPES, JOB_TYPE_LABELS, SENIORITIES, SENIORITY_LABELS, EDUCATIONS, EDUCATION_LABELS } from "@/lib/constants";
import PageHeader from "@/components/ui/PageHeader";
import FormField, { inputCls } from "@/components/ui/FormField";

export default function JobCreatePage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ title: "", location: "ha_noi", job_type: "fulltime", seniority: "mid", education: "dai_hoc", skills: "", requirement: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setError(null); setSubmitting(true);
    try {
      const res = await jobsApi.create({ ...form, skills: form.skills.split(",").map(s => s.trim()).filter(Boolean) }, token);
      navigate(`/records/jobs/${res.job_id}`, { replace: true });
    } catch (err) { setError(err instanceof ApiError ? err.body.message : "Lỗi tạo tin."); }
    finally { setSubmitting(false); }
  }

  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Tạo tin tuyển dụng" />
      <div className="flex-1 overflow-y-auto p-6">
        <form onSubmit={handleSubmit} className="max-w-lg space-y-4">
          <FormField label="Tiêu đề *"><input className={inputCls()} value={form.title} onChange={set("title")} required placeholder="vd. Senior Backend Engineer" /></FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Địa điểm *"><select className={inputCls()} value={form.location} onChange={set("location")}>{LOCATIONS.map(l => <option key={l} value={l}>{LOCATION_LABELS[l]}</option>)}</select></FormField>
            <FormField label="Hình thức *"><select className={inputCls()} value={form.job_type} onChange={set("job_type")}>{JOB_TYPES.map(t => <option key={t} value={t}>{JOB_TYPE_LABELS[t]}</option>)}</select></FormField>
            <FormField label="Cấp bậc *"><select className={inputCls()} value={form.seniority} onChange={set("seniority")}>{SENIORITIES.map(s => <option key={s} value={s}>{SENIORITY_LABELS[s]}</option>)}</select></FormField>
            <FormField label="Học vấn *"><select className={inputCls()} value={form.education} onChange={set("education")}>{EDUCATIONS.map(e => <option key={e} value={e}>{EDUCATION_LABELS[e]}</option>)}</select></FormField>
          </div>
          <FormField label="Kỹ năng (phân cách bằng dấu phẩy)"><input className={inputCls()} value={form.skills} onChange={set("skills")} placeholder="python, fastapi, sql" /></FormField>
          <FormField label="Yêu cầu công việc"><textarea className={inputCls()} rows={5} value={form.requirement} onChange={set("requirement")} /></FormField>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-3">
            <button type="submit" disabled={submitting} className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700 disabled:opacity-60">{submitting ? "Đang tạo..." : "Tạo tin"}</button>
            <button type="button" onClick={() => navigate("/records")} className="rounded-md border px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">Hủy</button>
          </div>
        </form>
      </div>
    </div>
  );
}
