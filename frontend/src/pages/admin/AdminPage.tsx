import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { adminApi, ApiError, type UserSummary } from "@/lib/api";
import { useFetch } from "@/lib/hooks";
import PageHeader from "@/components/ui/PageHeader";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import Pagination from "@/components/ui/Pagination";

type Tab = "users" | "documents" | "applications";

const PAGE_LIMIT = 20;

export default function AdminPage() {
  const { token, user: me } = useAuth();
  const [tab, setTab] = useState<Tab>("users");
  const [usersOffset, setUsersOffset] = useState(0);
  const [docsOffset, setDocsOffset] = useState(0);
  const [appsOffset, setAppsOffset] = useState(0);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actingUserId, setActingUserId] = useState<number | null>(null);

  const { data: users, loading: usersLoading, reload: reloadUsers } = useFetch(
    () => (token ? adminApi.users({ limit: String(PAGE_LIMIT), offset: String(usersOffset) }, token) : Promise.reject()),
    [token, usersOffset],
  );

  const { data: documents, loading: docsLoading, reload: reloadDocs } = useFetch(
    () => (token ? adminApi.documents({ limit: String(PAGE_LIMIT), offset: String(docsOffset) }, token) : Promise.reject()),
    [token, docsOffset],
  );

  const { data: applications, loading: appsLoading, reload: reloadApps } = useFetch(
    () => (token ? adminApi.applications({ limit: String(PAGE_LIMIT), offset: String(appsOffset) }, token) : Promise.reject()),
    [token, appsOffset],
  );

  const loading = tab === "users" ? usersLoading : tab === "documents" ? docsLoading : appsLoading;

  async function toggleUserStatus(u: UserSummary) {
    if (!token) return;
    const newStatus = u.status === "active" ? "disabled" : "active";
    const action = newStatus === "disabled" ? "khóa" : "mở khóa";
    if (!confirm(`Bạn có chắc muốn ${action} người dùng ${u.email}?`)) return;
    setActionError(null); setActingUserId(u.user_id);
    try {
      await adminApi.updateUser(u.user_id, newStatus, token);
      reloadUsers();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.body.message : `Không thể ${action} người dùng.`);
    } finally { setActingUserId(null); }
  }

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
          <>
            {actionError && (
              <p className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{actionError}</p>
            )}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs font-medium uppercase text-slate-400">
                    <th className="pb-2 pr-4">ID</th>
                    <th className="pb-2 pr-4">Email</th>
                    <th className="pb-2 pr-4">Vai trò</th>
                    <th className="pb-2 pr-4">Trạng thái</th>
                    <th className="pb-2 pr-4">Ngày tạo</th>
                    <th className="pb-2">Hành động</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {users?.items.map((u: UserSummary) => {
                    const isSelf = me?.user_id === u.user_id;
                    const acting = actingUserId === u.user_id;
                    return (
                      <tr key={u.user_id} className="hover:bg-slate-50">
                        <td className="py-2 pr-4 text-slate-500">{u.user_id}</td>
                        <td className="py-2 pr-4 text-slate-700">{u.email}{isSelf && <span className="ml-1 text-xs text-slate-400">(bạn)</span>}</td>
                        <td className="py-2 pr-4 capitalize text-slate-600">{u.role}</td>
                        <td className="py-2 pr-4"><Badge value={u.status} label={u.status === "active" ? "Hoạt động" : u.status === "disabled" ? "Bị khóa" : u.status} /></td>
                        <td className="py-2 pr-4 text-slate-400 text-xs">{new Date(u.created_at).toLocaleDateString("vi-VN")}</td>
                        <td className="py-2">
                          {isSelf ? (
                            <span className="text-xs text-slate-400">—</span>
                          ) : (
                            <button
                              onClick={() => toggleUserStatus(u)}
                              disabled={acting}
                              className={`rounded-md border px-2 py-1 text-xs font-medium disabled:opacity-50 ${u.status === "active" ? "border-red-300 text-red-700 hover:bg-red-50" : "border-green-300 text-green-700 hover:bg-green-50"}`}
                            >
                              {acting ? "..." : u.status === "active" ? "Khóa" : "Mở khóa"}
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {users && (
              <Pagination
                className="mt-4"
                total={users.total}
                limit={users.limit}
                offset={users.offset}
                onChange={o => { setUsersOffset(o); reloadUsers(); }}
              />
            )}
          </>
        )}

        {!loading && tab === "documents" && (
          <>
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
            </div>
            {documents && (
              <Pagination
                className="mt-4"
                total={documents.total}
                limit={documents.limit}
                offset={documents.offset}
                onChange={o => { setDocsOffset(o); reloadDocs(); }}
              />
            )}
          </>
        )}

        {!loading && tab === "applications" && (
          <>
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
            </div>
            {applications && (
              <Pagination
                className="mt-4"
                total={applications.total}
                limit={applications.limit}
                offset={applications.offset}
                onChange={o => { setAppsOffset(o); reloadApps(); }}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
