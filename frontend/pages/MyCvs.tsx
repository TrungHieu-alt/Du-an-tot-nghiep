import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, FileText, Loader2, Pencil, Plus, Trash2, Upload } from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';
import { createCv, deleteCv, extractCvPdf, listMyCvs, updateCv } from '../src/api/normal';
import type { NormalCv } from '../types';

const splitCsv = (value: string): string[] =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

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

const getSkillCsv = (cv: NormalCv): string =>
  (cv.skills || [])
    .map((skill) => skill.name)
    .filter((name): name is string => typeof name === 'string' && Boolean(name.trim()))
    .join(', ');

const parseJsonArray = (value: string): Array<Record<string, unknown>> => {
  if (!value.trim()) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const stringifyJsonArray = (value: unknown): string =>
  Array.isArray(value) && value.length > 0 ? JSON.stringify(value, null, 2) : '';

const formatDate = (value?: string): string => {
  if (!value) return 'Chưa rõ';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Chưa rõ' : date.toLocaleDateString('vi-VN');
};

const emptyForm = {
  avatar_url: '',
  fullname: '',
  preferred_name: '',
  email: '',
  phone: '',
  city: '',
  state: '',
  country: 'VN',
  headline: '',
  target_role: '',
  employment_type: 'fulltime',
  salary_expectation: '',
  availability: '',
  skills: '',
  experiences: '',
  education: '',
  projects: '',
  certifications: '',
  languages: '',
  portfolio: '',
  references: '',
  tags: '',
  summary: '',
};

const formFromExtractedCv = (cv: Record<string, unknown>) => {
  const location = cv.location && typeof cv.location === 'object' ? cv.location as Record<string, unknown> : {};
  const skills = Array.isArray(cv.skills)
    ? cv.skills.map((skill) => typeof skill === 'object' && skill ? String((skill as Record<string, unknown>).name || '') : String(skill)).filter(Boolean).join(', ')
    : '';
  return {
    ...emptyForm,
    avatar_url: typeof cv.avatar_url === 'string' ? cv.avatar_url : '',
    fullname: typeof cv.fullname === 'string' ? cv.fullname : '',
    preferred_name: typeof cv.preferred_name === 'string' ? cv.preferred_name : '',
    email: typeof cv.email === 'string' ? cv.email : '',
    phone: typeof cv.phone === 'string' ? cv.phone : '',
    city: typeof location.city === 'string' ? location.city : '',
    state: typeof location.state === 'string' ? location.state : '',
    country: typeof location.country === 'string' ? location.country : 'VN',
    headline: typeof cv.headline === 'string' ? cv.headline : '',
    target_role: typeof cv.target_role === 'string' ? cv.target_role : '',
    employment_type: Array.isArray(cv.employment_type) ? cv.employment_type.join(', ') : '',
    salary_expectation: typeof cv.salary_expectation === 'string' ? cv.salary_expectation : '',
    availability: typeof cv.availability === 'string' ? cv.availability : '',
    skills,
    experiences: stringifyJsonArray(cv.experiences),
    education: stringifyJsonArray(cv.education),
    projects: stringifyJsonArray(cv.projects),
    certifications: stringifyJsonArray(cv.certifications),
    languages: stringifyJsonArray(cv.languages),
    portfolio: stringifyJsonArray(cv.portfolio),
    references: stringifyJsonArray(cv.references),
    tags: Array.isArray(cv.tags) ? cv.tags.join(', ') : '',
    summary: typeof cv.summary === 'string' ? cv.summary : '',
  };
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
  const [form, setForm] = useState(emptyForm);
  const [editForm, setEditForm] = useState(emptyForm);

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

  const submitManual = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!accessToken) return;
    setSaving(true);
    setError(null);
    try {
      await createCv(accessToken, {
        avatar_url: form.avatar_url || undefined,
        fullname: form.fullname,
        preferred_name: form.preferred_name || undefined,
        email: form.email || undefined,
        phone: form.phone || undefined,
        location: {
          city: form.city || undefined,
          state: form.state || undefined,
          country: form.country || undefined,
        },
        headline: form.headline || undefined,
        target_role: form.target_role || undefined,
        employment_type: splitCsv(form.employment_type),
        salary_expectation: form.salary_expectation || undefined,
        availability: form.availability || undefined,
        summary: form.summary || undefined,
        skills: splitCsv(form.skills).map((name) => ({ name })),
        experiences: parseJsonArray(form.experiences),
        education: parseJsonArray(form.education),
        projects: parseJsonArray(form.projects),
        certifications: parseJsonArray(form.certifications),
        languages: parseJsonArray(form.languages),
        portfolio: parseJsonArray(form.portfolio),
        references: parseJsonArray(form.references),
        tags: splitCsv(form.tags),
      });
      setForm(emptyForm);
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
        ...formFromExtractedCv(result.cv as Record<string, unknown>),
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
    setEditForm({
      avatar_url: cv.avatar_url || '',
      fullname: cv.fullname || '',
      preferred_name: cv.preferred_name || '',
      email: cv.email || '',
      phone: cv.phone || '',
      city: getCity(cv),
      state: typeof cv.location?.state === 'string' ? cv.location.state : '',
      country: typeof cv.location?.country === 'string' ? cv.location.country : 'VN',
      headline: cv.headline || '',
      target_role: cv.target_role || '',
      employment_type: (cv.employment_type || []).join(', '),
      salary_expectation: cv.salary_expectation || '',
      availability: cv.availability || '',
      skills: getSkillCsv(cv),
      experiences: stringifyJsonArray(cv.experiences),
      education: stringifyJsonArray(cv.education),
      projects: stringifyJsonArray(cv.projects),
      certifications: stringifyJsonArray(cv.certifications),
      languages: stringifyJsonArray(cv.languages),
      portfolio: stringifyJsonArray(cv.portfolio),
      references: stringifyJsonArray(cv.references),
      tags: (cv.tags || []).join(', '),
      summary: cv.summary || '',
    });
  };

  const saveEdit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!accessToken || !editingId) return;
    setSaving(true);
    setError(null);
    try {
      await updateCv(accessToken, editingId, {
        avatar_url: editForm.avatar_url || undefined,
        fullname: editForm.fullname,
        preferred_name: editForm.preferred_name || undefined,
        email: editForm.email || undefined,
        phone: editForm.phone || undefined,
        location: {
          city: editForm.city || undefined,
          state: editForm.state || undefined,
          country: editForm.country || undefined,
        },
        headline: editForm.headline || undefined,
        target_role: editForm.target_role || undefined,
        employment_type: splitCsv(editForm.employment_type),
        salary_expectation: editForm.salary_expectation || undefined,
        availability: editForm.availability || undefined,
        summary: editForm.summary || undefined,
        skills: splitCsv(editForm.skills).map((name) => ({ name })),
        experiences: parseJsonArray(editForm.experiences),
        education: parseJsonArray(editForm.education),
        projects: parseJsonArray(editForm.projects),
        certifications: parseJsonArray(editForm.certifications),
        languages: parseJsonArray(editForm.languages),
        portfolio: parseJsonArray(editForm.portfolio),
        references: parseJsonArray(editForm.references),
        tags: splitCsv(editForm.tags),
      });
      setEditingId(null);
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
        <form id="create-cv" onSubmit={submitManual} className="mb-8 rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
          <h2 className="mb-2 font-bold text-gray-900">Tạo CV mới</h2>
          {extractWarnings.length > 0 ? (
            <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              <p className="font-semibold">Cảnh báo trích xuất PDF</p>
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {extractWarnings.map((warning) => <li key={warning}>{warning}</li>)}
              </ul>
            </div>
          ) : null}
          {extractedText ? (
            <details className="mb-4 rounded-xl border border-gray-100 bg-gray-50 p-3 text-sm text-gray-600">
              <summary className="cursor-pointer font-semibold text-gray-800">Xem text đã trích xuất</summary>
              <pre className="mt-3 max-h-48 overflow-auto whitespace-pre-wrap text-xs">{extractedText}</pre>
            </details>
          ) : null}
          <div className="grid gap-3 md:grid-cols-2">
            <input value={form.avatar_url} onChange={(e) => setForm({ ...form, avatar_url: e.target.value })} placeholder="Avatar URL" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input required value={form.fullname} onChange={(e) => setForm({ ...form, fullname: e.target.value })} placeholder="Họ tên *" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.preferred_name} onChange={(e) => setForm({ ...form, preferred_name: e.target.value })} placeholder="Tên thường gọi" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.headline} onChange={(e) => setForm({ ...form, headline: e.target.value })} placeholder="Headline" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.target_role} onChange={(e) => setForm({ ...form, target_role: e.target.value })} placeholder="Vị trí mong muốn" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Email" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="Số điện thoại" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} placeholder="Thành phố" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} placeholder="Tỉnh/Bang" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} placeholder="Quốc gia" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.employment_type} onChange={(e) => setForm({ ...form, employment_type: e.target.value })} placeholder="Employment type: fulltime, contract..." className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.salary_expectation} onChange={(e) => setForm({ ...form, salary_expectation: e.target.value })} placeholder="Kỳ vọng lương" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.availability} onChange={(e) => setForm({ ...form, availability: e.target.value })} placeholder="Thời gian sẵn sàng" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} placeholder="Skills: Excel, Sales, English..." className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="Tags" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
            <textarea value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} placeholder="Tóm tắt kinh nghiệm" className="min-h-24 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
            <textarea value={form.experiences} onChange={(e) => setForm({ ...form, experiences: e.target.value })} placeholder='Experiences JSON array, ví dụ [{"title":"Sales Lead","company":"Demo"}]' className="min-h-24 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
            <textarea value={form.education} onChange={(e) => setForm({ ...form, education: e.target.value })} placeholder='Education JSON array, ví dụ [{"degree":"Bachelor","school":"Demo University"}]' className="min-h-24 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
            <textarea value={form.projects} onChange={(e) => setForm({ ...form, projects: e.target.value })} placeholder="Projects JSON array" className="min-h-20 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
            <textarea value={form.certifications} onChange={(e) => setForm({ ...form, certifications: e.target.value })} placeholder="Certifications JSON array" className="min-h-20 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
            <textarea value={form.languages} onChange={(e) => setForm({ ...form, languages: e.target.value })} placeholder='Languages JSON array, ví dụ [{"name":"English","level":"B2"}]' className="min-h-20 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
            <textarea value={form.portfolio} onChange={(e) => setForm({ ...form, portfolio: e.target.value })} placeholder="Portfolio JSON array" className="min-h-20 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
            <textarea value={form.references} onChange={(e) => setForm({ ...form, references: e.target.value })} placeholder="References JSON array" className="min-h-20 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
            <button disabled={saving} className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0F6FD6] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60 md:col-span-2">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Tạo CV mới
            </button>
          </div>
        </form>
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

                  {editingId === cv.id ? (
                    <form
                      onClick={(event) => event.stopPropagation()}
                      onSubmit={saveEdit}
                      className="mt-5 grid gap-3 rounded-xl border border-blue-100 bg-blue-50/60 p-4"
                    >
                      <h3 className="text-sm font-bold text-gray-900">Chỉnh sửa CV</h3>
                      <input required value={editForm.fullname} onChange={(e) => setEditForm({ ...editForm, fullname: e.target.value })} placeholder="Họ tên *" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <input value={editForm.target_role} onChange={(e) => setEditForm({ ...editForm, target_role: e.target.value })} placeholder="Vị trí mong muốn" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <input value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} placeholder="Email" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <input value={editForm.phone} onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })} placeholder="Số điện thoại" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <input value={editForm.city} onChange={(e) => setEditForm({ ...editForm, city: e.target.value })} placeholder="Thành phố" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <input value={editForm.skills} onChange={(e) => setEditForm({ ...editForm, skills: e.target.value })} placeholder="Skills" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <textarea value={editForm.summary} onChange={(e) => setEditForm({ ...editForm, summary: e.target.value })} placeholder="Tóm tắt" className="min-h-20 rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <div className="flex gap-2">
                        <button disabled={saving} className="rounded-full bg-[#0F6FD6] px-4 py-2 text-xs font-semibold text-white disabled:opacity-60">Lưu thay đổi</button>
                        <button type="button" onClick={() => setEditingId(null)} className="rounded-full bg-white px-4 py-2 text-xs font-semibold text-gray-700">Hủy</button>
                      </div>
                    </form>
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
