import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { adminApi, type UserSummary } from "@/lib/api";
import { useFetch } from "@/lib/hooks";
import PageHeader from "@/components/ui/PageHeader";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";

type Tab = "users" | "documents" | "applications";

export default function AdminPage() {
  const { token } = useAuth();
  const [tab, setTab] = useState<Tab>("users");

  const { data: users, loading: usersLoading } = useFetch(
    () => (token ? adminApi.users({}, token) : Promise.reject()),
    [token],
  );

  const { data: documents, loading: docsLoading } = useFetch(
    () => (token ? adminApi.documents({}, token) : Promise.reject()),
    [token],
  );

  const { data: applications, loading: appsLoading } = useFetch(
    () => (token ? adminApi.applications({}, token) : Promise.reject()),
    [token],
  );

  const loading = tab === "users" ? usersLoading : tab === "documents" ? docsLoading : appsLoading;

  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Giám sát hệ thống" />
      <div className="border-b border-slate-200 px-6">
        <div className="flex gap-4">
          {(["users", "documents", "applications"] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${tab === t ? "border-slate-800 text-slate-800" : "border-transparent text-slate-400 hover:text-slate-600"}`}
            >
              {t === "users" ? "Người dùng" : t === "documents" ? "Tài liệu" : "Ứng tuyển"}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {loading && <Spinner className="py-16" />}

        {!loading && tab === "users" && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs font-medium uppercase text-slate-400">
                  <th className="pb-2 pr-4">ID</th>
                  <th className="pb-2 pr-4">Email</th>
                  <th className="pb-2 pr-4">Vai trò</th>
                  <th className="pb-2 pr-4">Trạng thái</th>
                  <th className="pb-2">Ngày tạo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users?.items.map((u: UserSummary) => (
                  <tr key={u.user_id} className="hover:bg-slate-50">
                    <td className="py-2 pr-4 text-slate-500">{u.user_id}</td>
                    <td className="py-2 pr-4 text-slate-700">{u.email}</td>
                    <td className="py-2 pr-4 capitalize text-slate-600">{u.role}</td>
                    <td className="py-2 pr-4"><Badge value={u.status} label={u.status === "active" ? "Hoạt động" : "Bị khóa"} /></td>
                    <td className="py-2 text-slate-400 text-xs">{new Date(u.created_at).toLocaleDateString("vi-VN")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {users && <p className="mt-2 text-xs text-slate-400">Tổng: {users.total} người dùng</p>}
          </div>
        )}

        {!loading && tab === "documents" && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs font-medium uppercase text-slate-400">
                  <th className="pb-2 pr-4">ID</th>
                  <th className="pb-2 pr-4">Tên file</th>
                  <th className="pb-2 pr-4">Loại</th>
                  <th className="pb-2 pr-4">Owner</th>
                  <th className="pb-2">Ngày tạo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents?.items.map(d => (
                  <tr key={d.document_id} className="hover:bg-slate-50">
                    <td className="py-2 pr-4 text-slate-500">{d.document_id}</td>
                    <td className="py-2 pr-4 text-slate-700">{d.filename}</td>
                    <td className="py-2 pr-4 text-slate-600">{d.document_type}</td>
                    <td className="py-2 pr-4 text-slate-500">#{d.owner_user_id}</td>
                    <td className="py-2 text-slate-400 text-xs">{new Date(d.created_at).toLocaleDateString("vi-VN")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {documents && <p className="mt-2 text-xs text-slate-400">Tổng: {documents.total} tài liệu</p>}
          </div>
        )}

        {!loading && tab === "applications" && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs font-medium uppercase text-slate-400">
                  <th className="pb-2 pr-4">App ID</th>
                  <th className="pb-2 pr-4">Job ID</th>
                  <th className="pb-2 pr-4">Ứng viên</th>
                  <th className="pb-2">Trạng thái</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {applications?.items.map(a => (
                  <tr key={a.application_id} className="hover:bg-slate-50">
                    <td className="py-2 pr-4 text-slate-500">{a.application_id}</td>
                    <td className="py-2 pr-4 text-slate-600">#{a.job_id}</td>
                    <td className="py-2 pr-4 text-slate-600">#{a.candidate_user_id}</td>
                    <td className="py-2"><Badge value={a.status} label={a.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {applications && <p className="mt-2 text-xs text-slate-400">Tổng: {applications.total} đơn ứng tuyển</p>}
          </div>
        )}
      </div>
    </div>
  );
}
