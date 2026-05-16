import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { candidateProfileApi, ApiError } from "@/lib/api";
import FormField, { inputCls } from "@/components/ui/FormField";
import { LOCATIONS, LOCATION_LABELS } from "@/lib/constants";

export default function CandidateProfileSetupPage() {
  const { token, refreshMe } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [headline, setHeadline] = useState("");
  const [currentLocation, setCurrentLocation] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setError(null);
    setFieldErrors({});
    setSubmitting(true);
    try {
      await candidateProfileApi.upsert(
        { full_name: fullName, headline: headline || null, current_location: currentLocation || null },
        token,
      );
      await refreshMe();
      navigate("/jobs", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.body.fields) setFieldErrors(err.body.fields);
      else setError(err instanceof ApiError ? err.body.message : "Lỗi kết nối.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="mb-1 text-xl font-semibold text-slate-800">Hoàn tất hồ sơ cá nhân</h1>
        <p className="mb-6 text-sm text-slate-500">Tạo hồ sơ để bắt đầu tìm việc.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Họ và tên *" error={fieldErrors["body.full_name"]}>
            <input className={inputCls(fieldErrors["body.full_name"])} value={fullName} onChange={e => setFullName(e.target.value)} required placeholder="Nguyễn Văn A" />
          </FormField>
          <FormField label="Tiêu đề nghề nghiệp">
            <input className={inputCls()} value={headline} onChange={e => setHeadline(e.target.value)} placeholder="vd. Backend Developer" />
          </FormField>
          <FormField label="Địa điểm">
            <select className={inputCls()} value={currentLocation} onChange={e => setCurrentLocation(e.target.value)}>
              <option value="">-- Chọn địa điểm --</option>
              {LOCATIONS.map(l => <option key={l} value={l}>{LOCATION_LABELS[l]}</option>)}
            </select>
          </FormField>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={submitting} className="w-full rounded-md bg-slate-900 py-2.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60">
            {submitting ? "Đang lưu..." : "Tiếp tục"}
          </button>
        </form>
      </div>
    </div>
  );
}
