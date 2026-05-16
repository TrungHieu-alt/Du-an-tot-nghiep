import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { documentsApi, ApiError } from "@/lib/api";
import PageHeader from "@/components/ui/PageHeader";

export default function UploadPage() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ documentId: number; parseJobId: number } | null>(null);

  const docTypes = user?.role === "candidate"
    ? [{ value: "resume", label: "CV / Resume" }]
    : [{ value: "job_description", label: "Mô tả công việc (JD)" }];

  async function handleUpload() {
    if (!token || !file || !docType) return;
    setError(null); setUploading(true);
    try {
      const res = await documentsApi.upload(file, docType, token);
      setResult({ documentId: res.document.document_id, parseJobId: res.parse_job.parse_job_id });
    } catch (err) {
      setError(err instanceof ApiError ? err.body.message : "Lỗi tải lên.");
    } finally { setUploading(false); }
  }

  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Tải tệp lên" />
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-md space-y-4">
          {result ? (
            <div className="rounded-lg border border-green-200 bg-green-50 p-4">
              <p className="font-medium text-green-700">Tải lên thành công!</p>
              <p className="text-sm text-green-600">Document ID: {result.documentId} · Parse Job ID: {result.parseJobId}</p>
              <p className="mt-1 text-xs text-green-500">Hệ thống đang xử lý tệp. Kết quả sẽ được tạo tự động.</p>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => navigate("/records")}
                  className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700"
                >
                  {user?.role === "candidate" ? "Xem CV" : "Xem tin tuyển dụng"}
                </button>
                <button
                  onClick={() => { setResult(null); setFile(null); if (fileRef.current) fileRef.current.value = ""; }}
                  className="rounded-md border px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
                >
                  Tải thêm
                </button>
              </div>
            </div>
          ) : (
            <>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">Loại tài liệu *</label>
                <select
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                  value={docType}
                  onChange={e => setDocType(e.target.value)}
                >
                  <option value="">Chọn loại tài liệu...</option>
                  {docTypes.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">Tệp *</label>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={e => setFile(e.target.files?.[0] ?? null)}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-600 file:mr-3 file:rounded file:border-0 file:bg-slate-100 file:px-2 file:py-1 file:text-xs hover:bg-slate-50"
                />
                <p className="mt-1 text-xs text-slate-400">Hỗ trợ: PDF, DOC, DOCX, TXT</p>
              </div>

              {error && <p className="text-sm text-red-500">{error}</p>}

              <div className="flex gap-3">
                <button
                  onClick={handleUpload}
                  disabled={uploading || !file || !docType}
                  className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700 disabled:opacity-60"
                >
                  {uploading ? "Đang tải..." : "Tải lên"}
                </button>
                <button
                  type="button"
                  onClick={() => navigate("/records")}
                  className="rounded-md border px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
                >
                  Hủy
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
