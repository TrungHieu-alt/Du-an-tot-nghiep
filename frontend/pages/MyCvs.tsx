import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, FileText, Loader2, Pencil, Plus, Trash2, Upload } from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';
import { createCv, deleteCv, extractCvPdf, listMyCvs, updateCv } from '../src/api/normal';
import CvFormWizard, {
  createEmptyCvForm,
  cvFormFromExtractedCv,
  cvFormFromNormalCv,
  type CvFormState,
} from '../components/normal/CvFormWizard';
import type { NormalCv, NormalCvCreatePayload } from '../types';

const formatFileSize = (value: unknown): string => {
  const size = Number(value);
  if (!Number.isFinite(size) || size <= 0) return '';
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
};

const getOriginalName = (cv: NormalCv): string => {
  const value = cv.file?.originalname;
  return typeof value === 'string' ? value : '';
};

const getCity = (cv: NormalCv): string => {
  const value = cv.location?.city;
  return typeof value === 'string' ? value : '';
};

const formatDate = (value?: string): string => {
  if (!value) return 'Chưa rõ';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Chưa rõ' : date.toLocaleDateString('vi-VN');
};

const MyCvs: React.FC = () => {
  const { accessToken, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const showCreateForm = location.pathname === '/cv/new' || location.pathname === '/cvs/new';
  const showUploadForm = location.pathname === '/cv/upload' || location.pathname === '/cvs/upload';
  const [cvs, setCvs] = useState<NormalCv[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [extractWarnings, setExtractWarnings] = useState<string[]>([]);
  const [extractedText, setExtractedText] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<CvFormState>(createEmptyCvForm());
  const [editForm, setEditForm] = useState<CvFormState | null>(null);

  const load = async () => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    try {
      setCvs(await listMyCvs(accessToken));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không tải được danh sách CV.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [accessToken]);

  const submitManual = async (payload: NormalCvCreatePayload) => {
    if (!accessToken) return;
    setSaving(true);
    setError(null);
    try {
      await createCv(accessToken, payload);
      setForm(createEmptyCvForm());
      setExtractWarnings([]);
      setExtractedText('');
      setPdfFile(null);
      await load();
      navigate('/cvs');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không tạo được CV.');
    } finally {
      setSaving(false);
    }
  };

  const submitPdf = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!accessToken || !pdfFile) return;
    setExtracting(true);
    setError(null);
    setExtractWarnings([]);
    setExtractedText('');
    try {
      const result = await extractCvPdf(accessToken, pdfFile);
      setForm((current) => ({
        ...cvFormFromExtractedCv(result.cv as Record<string, unknown>),
        fullname: current.fullname || String(result.cv.fullname || ''),
      }));
      setExtractWarnings(result.warnings || []);
      setExtractedText(result.extractedText || '');
      navigate('/cvs/new');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không trích xuất được CV PDF.');
    } finally {
      setExtracting(false);
    }
  };

  const remove = async (cv: NormalCv) => {
    if (!accessToken) return;
    if (!window.confirm('Bạn chắc chắn muốn xóa CV này?')) return;
    await deleteCv(accessToken, cv.id);
    await load();
  };

  const beginEdit = (cv: NormalCv) => {
    setEditingId(cv.id);
    setEditForm(cvFormFromNormalCv(cv));
  };

  const saveEdit = async (payload: NormalCvCreatePayload) => {
    if (!accessToken || !editingId) return;
    setSaving(true);
    setError(null);
    try {
      await updateCv(accessToken, editingId, payload);
      setEditingId(null);
      setEditForm(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không cập nhật được CV.');
    } finally {
      setSaving(false);
    }
  };

  const toggleVisibility = async (cv: NormalCv) => {
    if (!accessToken) return;
    const isPublic = cv.status === 'published' && cv.visibility === 'public' && !cv.archived;
    await updateCv(accessToken, cv.id, {
      status: 'published',
      visibility: isPublic ? 'private' : 'public',
      archived: false,
    });
    await load();
  };

  if (!isAuthenticated) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-gray-900">Cần đăng nhập</h1>
        <Link to="/login" className="mt-4 inline-flex rounded-full bg-[#0F6FD6] px-5 py-2 text-sm font-semibold text-white">
          Đăng nhập
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex items-center gap-3">
          <FileText className="h-7 w-7 text-[#00A86B]" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">CV của tôi</h1>
            <p className="text-sm text-gray-500">Quản lý toàn bộ CV thuộc tài khoản hiện tại.</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/cvs/new" className="inline-flex items-center gap-2 rounded-full bg-[#0F6FD6] px-4 py-2 text-sm font-semibold text-white shadow-sm">
            <Plus className="h-4 w-4" />
            Tạo CV mới
          </Link>
          <Link to="/cvs/upload" className="inline-flex items-center gap-2 rounded-full bg-[#00A86B] px-4 py-2 text-sm font-semibold text-white shadow-sm">
            <Upload className="h-4 w-4" />
            Tải CV PDF lên
          </Link>
        </div>
      </div>

      {showCreateForm ? (
        <div className="mb-8">
          <CvFormWizard
            initialValue={form}
            saving={saving}
            onSubmit={submitManual}
            extractWarnings={extractWarnings}
            extractedText={extractedText}
            onCancel={() => navigate('/cvs')}
          />
        </div>
      ) : null}

      {showUploadForm ? (
        <form id="upload-cv" onSubmit={submitPdf} className="mb-8 rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
          <h2 className="mb-2 font-bold text-gray-900">Upload CV PDF để tự động điền</h2>
          <p className="mb-4 text-sm text-gray-500">
            Hệ thống chỉ trích xuất và điền vào form nháp. CV sẽ chưa được lưu cho đến khi bạn kiểm tra và bấm Tạo CV mới.
          </p>
          <div className="grid gap-3 md:grid-cols-2">
            <input value={form.fullname} onChange={(e) => setForm({ ...form, fullname: e.target.value })} placeholder="Họ tên nếu muốn lưu kèm" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input aria-label="Chọn CV PDF" type="file" accept="application/pdf,.pdf" onChange={(e) => setPdfFile(e.target.files?.[0] ?? null)} className="rounded-lg border border-dashed border-gray-300 bg-gray-50 px-3 py-6 text-sm" />
            <button disabled={extracting || !pdfFile} className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#00A86B] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60 md:col-span-2">
              {extracting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              {extracting ? 'Đang trích xuất...' : 'Trích xuất CV PDF'}
            </button>
          </div>
        </form>
      ) : null}

      {error && <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      {loading ? (
        <div className="py-10 text-center text-gray-500">Đang tải...</div>
      ) : (
        <>
          {cvs.length === 0 ? (
            <p className="mb-4 rounded-xl border border-dashed border-gray-200 bg-white px-4 py-3 text-sm text-gray-600">
              Bạn chưa có CV nào. Hãy tạo CV mới hoặc tải CV PDF lên.
            </p>
          ) : null}

          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
            <Link
              to="/cvs/new"
              aria-label="Tạo CV mới"
              className="flex min-h-[260px] flex-col items-center justify-center rounded-2xl border-2 border-dashed border-blue-200 bg-white p-6 text-center shadow-sm transition hover:-translate-y-0.5 hover:border-[#0F6FD6] hover:shadow-md"
            >
              <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-[#0F6FD6]">
                <Plus className="h-9 w-9" />
              </span>
              <span className="mt-4 text-base font-bold text-gray-900">Tạo CV mới</span>
              <span className="mt-2 text-sm text-gray-500">Tạo hồ sơ thủ công từ thông tin của bạn.</span>
              <span
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  navigate('/cvs/upload');
                }}
                role="button"
                tabIndex={0}
                className="mt-4 rounded-full bg-green-50 px-4 py-2 text-xs font-semibold text-[#00A86B]"
              >
                Tải PDF
              </span>
            </Link>

            {cvs.map((cv) => {
              const title = cv.fullname || getOriginalName(cv) || 'PDF CV';
              const isPublic = cv.visibility === 'public' && !cv.archived;
              return (
                <article
                  key={cv.id}
                  role="link"
                  tabIndex={0}
                  aria-label={`Mở CV ${title}`}
                  onClick={() => navigate(`/cvs/${cv.id}`)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') navigate(`/cvs/${cv.id}`);
                  }}
                  className="group flex min-h-[260px] cursor-pointer flex-col rounded-2xl border border-gray-100 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex min-w-0 gap-3">
                      {cv.avatar_url ? (
                        <img src={cv.avatar_url} alt="" className="h-12 w-12 rounded-xl object-cover" />
                      ) : null}
                      <div className="min-w-0">
                        <h2 className="line-clamp-2 text-base font-bold text-gray-900 group-hover:text-[#0F6FD6]">{title}</h2>
                        <p className="mt-1 line-clamp-2 text-sm text-gray-500">{cv.headline || cv.target_role || 'Chưa có vị trí mong muốn'}</p>
                        <p className="mt-1 text-xs text-gray-400">{getCity(cv) || 'Chưa có địa điểm'} · {(cv.employment_type || []).join(', ') || 'Chưa chọn hình thức'}</p>
                      </div>
                    </div>
                    <span className="shrink-0 rounded-xl bg-green-50 p-2 text-[#00A86B]">
                      <FileText className="h-5 w-5" />
                    </span>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2 text-xs">
                    <span className="rounded-full bg-gray-100 px-2 py-1">{cv.status}</span>
                    <span className="rounded-full bg-gray-100 px-2 py-1">{cv.visibility}</span>
                  </div>

                  {getOriginalName(cv) ? (
                    <div className="mt-4 rounded-xl bg-blue-50 p-3 text-xs text-blue-800">
                      <div className="line-clamp-1 font-semibold">{getOriginalName(cv)}</div>
                      <div>{formatFileSize(cv.file.size)} · {cv.file.uploaded_at ? formatDate(String(cv.file.uploaded_at)) : 'Chưa rõ ngày upload'}</div>
                    </div>
                  ) : null}

                  <div className="mt-auto pt-5">
                    <p className="mb-3 text-xs text-gray-500">Cập nhật: {formatDate(cv.updated_at || cv.created_at)}</p>
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={(event) => {
                          event.stopPropagation();
                          beginEdit(cv);
                        }}
                        className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-3 py-1.5 text-xs font-semibold text-gray-700"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                        Chỉnh sửa
                      </button>
                      <button
                        onClick={(event) => {
                          event.stopPropagation();
                          void toggleVisibility(cv);
                        }}
                        className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700"
                      >
                        {isPublic ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                        {isPublic ? 'Ẩn' : 'Hiện công khai'}
                      </button>
                      <button
                        onClick={(event) => {
                          event.stopPropagation();
                          void remove(cv);
                        }}
                        className="inline-flex items-center gap-1 rounded-full bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        Xóa
                      </button>
                    </div>
                  </div>

                  {editingId === cv.id && editForm ? (
                    <div
                      onClick={(event) => event.stopPropagation()}
                      className="mt-5 rounded-xl border border-blue-100 bg-blue-50/60 p-4"
                    >
                      <CvFormWizard
                        initialValue={editForm}
                        saving={saving}
                        onSubmit={saveEdit}
                        compact
                        onCancel={() => {
                          setEditingId(null);
                          setEditForm(null);
                        }}
                      />
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};

export default MyCvs;
