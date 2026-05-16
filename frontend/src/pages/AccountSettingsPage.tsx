import { useState, type FormEvent } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { candidateProfileApi, recruiterProfileApi, ApiError } from "@/lib/api";
import { LOCATIONS, LOCATION_LABELS } from "@/lib/constants";
import PageHeader from "@/components/ui/PageHeader";
import FormField, { inputCls } from "@/components/ui/FormField";

export default function AccountSettingsPage() {
  const { user, token, refreshMe, logout } = useAuth();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [fullName, setFullName] = useState(user?.role === "candidate" ? "" : "");
  const [headline, setHeadline] = useState("");
  const [currentLocation, setCurrentLocation] = useState("ha_noi");
  const [titleField, setTitleField] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token || !user) return;
    setError(null); setSaving(true); setSuccess(false);
    try {
      if (user.role === "candidate") {
        await candidateProfileApi.upsert({ full_name: fullName, headline, current_location: currentLocation }, token);
      } else if (user.role === "recruiter") {
        await recruiterProfileApi.upsert({ full_name: fullName, title: titleField || null }, token);
      }
      await refreshMe();
      setSuccess(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.body.message : "Lỗi lưu.");
    } finally { setSaving(false); }
  }

  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Cài đặt tài khoản" />
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-md space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="mb-1 text-sm font-medium text-slate-700">Thông tin tài khoản</h2>
            <p className="text-sm text-slate-500">{user?.email}</p>
            <p className="text-xs text-slate-400 capitalize">{user?.role} · {user?.status}</p>
          </div>

          {user?.role !== "admin" && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <FormField label="Họ và tên">
                <input className={inputCls()} value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Nguyễn Văn A" />
              </FormField>
              {user?.role === "candidate" && (
                <>
                  <FormField label="Tiêu đề nghề nghiệp">
                    <input className={inputCls()} value={headline} onChange={e => setHeadline(e.target.value)} placeholder="vd. Senior Backend Developer" />
                  </FormField>
                  <FormField label="Địa điểm">
                    <select className={inputCls()} value={currentLocation} onChange={e => setCurrentLocation(e.target.value)}>
                      {LOCATIONS.map(l => <option key={l} value={l}>{LOCATION_LABELS[l]}</option>)}
                    </select>
                  </FormField>
                </>
              )}
              {user?.role === "recruiter" && (
                <FormField label="Chức danh">
                  <input className={inputCls()} value={titleField} onChange={e => setTitleField(e.target.value)} placeholder="vd. HR Manager" />
                </FormField>
              )}
              {error && <p className="text-sm text-red-500">{error}</p>}
              {success && <p className="text-sm text-green-600">Đã lưu thành công.</p>}
              <button type="submit" disabled={saving} className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700 disabled:opacity-60">
                {saving ? "Đang lưu..." : "Lưu thay đổi"}
              </button>
            </form>
          )}

          <div className="border-t border-slate-200 pt-4">
            <button onClick={logout} className="text-sm text-red-500 hover:text-red-700">Đăng xuất</button>
          </div>
        </div>
      </div>
    </div>
  );
}
