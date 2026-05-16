import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { recruiterProfileApi, organizationsApi, ApiError, type Organization } from "@/lib/api";
import FormField, { inputCls } from "@/components/ui/FormField";

export default function RecruiterProfileSetupPage() {
  const { token, refreshMe } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [title, setTitle] = useState("");
  const [orgQuery, setOrgQuery] = useState("");
  const [orgResults, setOrgResults] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [searching, setSearching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function searchOrg() {
    if (!token || !orgQuery.trim()) return;
    setSearching(true);
    try {
      const res = await organizationsApi.search(orgQuery, token);
      setOrgResults(res.items);
    } catch {
      setOrgResults([]);
    } finally {
      setSearching(false);
    }
  }

  async function createAndSelectOrg() {
    if (!token || !orgQuery.trim()) return;
    try {
      const org = await organizationsApi.create(orgQuery.trim(), token);
      setSelectedOrg(org);
      setOrgResults([]);
    } catch (err) {
      setError(err instanceof ApiError ? err.body.message : "Không thể tạo tổ chức.");
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token || !selectedOrg) { setError("Vui lòng chọn tổ chức."); return; }
    setError(null); setFieldErrors({});
    setSubmitting(true);
    try {
      await recruiterProfileApi.upsert(
        { organization_id: selectedOrg.organization_id, full_name: fullName, title: title || null },
        token,
      );
      await refreshMe();
      navigate("/talent", { replace: true });
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
        <h1 className="mb-1 text-xl font-semibold text-slate-800">Hoàn tất hồ sơ nhà tuyển dụng</h1>
        <p className="mb-6 text-sm text-slate-500">Chọn tổ chức để bắt đầu đăng tin tuyển dụng.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Org search */}
          <FormField label="Tổ chức *">
            {selectedOrg ? (
              <div className="flex items-center justify-between rounded-md border border-slate-300 px-3 py-2">
                <span className="text-sm font-medium">{selectedOrg.name}</span>
                <button type="button" onClick={() => setSelectedOrg(null)} className="text-xs text-slate-400 hover:text-red-500">Đổi</button>
              </div>
            ) : (
              <div className="space-y-1">
                <div className="flex gap-2">
                  <input className={inputCls()} value={orgQuery} onChange={e => setOrgQuery(e.target.value)} placeholder="Tìm tên tổ chức..." />
                  <button type="button" onClick={searchOrg} disabled={searching} className="rounded-md bg-slate-100 px-3 text-sm hover:bg-slate-200 disabled:opacity-50">
                    {searching ? "..." : "Tìm"}
                  </button>
                </div>
                {orgResults.length > 0 && (
                  <div className="rounded-md border border-slate-200 bg-white shadow-sm">
                    {orgResults.map(o => (
                      <button key={o.organization_id} type="button" onClick={() => { setSelectedOrg(o); setOrgResults([]); }}
                        className="flex w-full items-center px-3 py-2 text-left text-sm hover:bg-slate-50">
                        {o.name}
                      </button>
                    ))}
                  </div>
                )}
                {orgQuery.trim() && (
                  <button type="button" onClick={createAndSelectOrg} className="text-xs text-blue-600 hover:underline">
                    + Tạo mới "{orgQuery}"
                  </button>
                )}
              </div>
            )}
          </FormField>
          <FormField label="Họ và tên *" error={fieldErrors["body.full_name"]}>
            <input className={inputCls(fieldErrors["body.full_name"])} value={fullName} onChange={e => setFullName(e.target.value)} required placeholder="Nguyễn Thị B" />
          </FormField>
          <FormField label="Chức danh">
            <input className={inputCls()} value={title} onChange={e => setTitle(e.target.value)} placeholder="vd. HR Manager" />
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
