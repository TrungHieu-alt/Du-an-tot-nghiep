import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Briefcase, Eye, EyeOff, Loader2, Pencil, Plus, Trash2, XCircle } from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';
import { createJob, deleteJob, listMyJobs, updateJob } from '../src/api/normal';
import type { NormalJob } from '../types';

const splitCsv = (value: string): string[] =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

const formatDate = (value?: string): string => {
  if (!value) return 'Chưa rõ';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Chưa rõ' : date.toLocaleDateString('vi-VN');
};

const getCity = (job: NormalJob): string => {
  const value = job.location?.city;
  return typeof value === 'string' ? value : '';
};

const getSkillCsv = (job: NormalJob): string =>
  (job.skills || [])
    .map((skill) => skill.name)
    .filter((name): name is string => typeof name === 'string' && Boolean(name.trim()))
    .join(', ');

const salarySummary = (job: NormalJob): string => {
  const min = job.salary?.min;
  const max = job.salary?.max;
  const currency = typeof job.salary?.currency === 'string' ? job.salary.currency : '';
  if (min === undefined && max === undefined) return 'Chưa công khai';
  return `${min ?? '?'} - ${max ?? '?'} ${currency}`.trim();
};

const parseNumber = (value: string): number | undefined => {
  if (!value.trim()) return undefined;
  const number = Number(value);
  return Number.isFinite(number) ? number : undefined;
};

const emptyForm = {
  company_id: '',
  title: '',
  slug: '',
  company_name: '',
  company_logo_url: '',
  company_website: '',
  company_location: '',
  company_size: '',
  company_industry: '',
  department: '',
  city: '',
  state: '',
  country: 'VN',
  remote_type: 'onsite',
  employment_type: 'fulltime',
  seniority: 'junior',
  team_size: '',
  status: 'published',
  visibility: 'public',
  skills: '',
  responsibilities: '',
  requirements: '',
  nice_to_have: '',
  experience_years: '',
  education_level: '',
  salary_min: '',
  salary_max: '',
  salary_currency: 'VND',
  salary_period: 'month',
  benefits: '',
  bonus: '',
  equity: '',
  apply_url: '',
  apply_email: '',
  recruiter_name: '',
  recruiter_email: '',
  recruiter_phone: '',
  how_to_apply: '',
  application_deadline: '',
  categories: '',
  tags: '',
  required_docs: '',
  description: '',
};

const MyJobs: React.FC = () => {
  const { accessToken, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const showCreateForm = location.pathname === '/job/new' || location.pathname === '/employer/requests/new';
  const [jobs, setJobs] = useState<NormalJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [editForm, setEditForm] = useState(emptyForm);

  const load = async () => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    try {
      setJobs(await listMyJobs(accessToken));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không tải được danh sách yêu cầu tuyển dụng.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [accessToken]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!accessToken) return;
    setSaving(true);
    setError(null);
    try {
      await createJob(accessToken, {
        company_id: form.company_id || undefined,
        title: form.title,
        slug: form.slug || undefined,
        company_name: form.company_name || undefined,
        company_logo_url: form.company_logo_url || undefined,
        company_website: form.company_website || undefined,
        company_location: form.company_location || undefined,
        company_size: form.company_size || undefined,
        company_industry: form.company_industry || undefined,
        department: form.department || undefined,
        location: {
          city: form.city || undefined,
          state: form.state || undefined,
          country: form.country || undefined,
          remote_type: form.remote_type || undefined,
        },
        employment_type: [form.employment_type],
        seniority: form.seniority,
        team_size: parseNumber(form.team_size),
        status: form.status as 'draft' | 'published' | 'closed',
        visibility: form.visibility as 'public' | 'private' | 'unlisted',
        skills: splitCsv(form.skills).map((name) => ({ name })),
        responsibilities: splitCsv(form.responsibilities),
        requirements: splitCsv(form.requirements),
        nice_to_have: splitCsv(form.nice_to_have),
        experience_years: parseNumber(form.experience_years),
        education_level: form.education_level || undefined,
        salary: {
          min: parseNumber(form.salary_min),
          max: parseNumber(form.salary_max),
          currency: form.salary_currency || undefined,
          period: form.salary_period || undefined,
        },
        benefits: splitCsv(form.benefits),
        bonus: form.bonus || undefined,
        equity: form.equity || undefined,
        apply_url: form.apply_url || undefined,
        apply_email: form.apply_email || undefined,
        recruiter: {
          name: form.recruiter_name || undefined,
          email: form.recruiter_email || undefined,
          phone: form.recruiter_phone || undefined,
        },
        how_to_apply: form.how_to_apply || undefined,
        application_deadline: form.application_deadline || undefined,
        categories: splitCsv(form.categories),
        tags: splitCsv(form.tags),
        remote: form.remote_type === 'remote',
        required_docs: splitCsv(form.required_docs),
        description: form.description || undefined,
      });
      setForm(emptyForm);
      await load();
      navigate('/employer/requests');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không tạo được yêu cầu tuyển dụng.');
    } finally {
      setSaving(false);
    }
  };

  const beginEdit = (job: NormalJob) => {
    setEditingId(job.id);
    setEditForm({
      company_id: job.company_id || '',
      title: job.title || '',
      slug: job.slug || '',
      company_name: job.company_name || '',
      company_logo_url: job.company_logo_url || '',
      company_website: job.company_website || '',
      company_location: job.company_location || '',
      company_size: job.company_size || '',
      company_industry: job.company_industry || '',
      department: job.department || '',
      city: getCity(job),
      state: typeof job.location?.state === 'string' ? job.location.state : '',
      country: typeof job.location?.country === 'string' ? job.location.country : 'VN',
      remote_type: typeof job.location?.remote_type === 'string' ? job.location.remote_type : 'onsite',
      employment_type: job.employment_type?.[0] || 'fulltime',
      seniority: job.seniority || 'junior',
      team_size: job.team_size ? String(job.team_size) : '',
      status: job.status || 'published',
      visibility: job.visibility || 'public',
      skills: getSkillCsv(job),
      responsibilities: (job.responsibilities || []).join(', '),
      requirements: (job.requirements || []).join(', '),
      nice_to_have: (job.nice_to_have || []).join(', '),
      experience_years: job.experience_years !== undefined && job.experience_years !== null ? String(job.experience_years) : '',
      education_level: job.education_level || '',
      salary_min: job.salary?.min !== undefined ? String(job.salary.min) : '',
      salary_max: job.salary?.max !== undefined ? String(job.salary.max) : '',
      salary_currency: typeof job.salary?.currency === 'string' ? job.salary.currency : 'VND',
      salary_period: typeof job.salary?.period === 'string' ? job.salary.period : 'month',
      benefits: (job.benefits || []).join(', '),
      bonus: job.bonus || '',
      equity: job.equity || '',
      apply_url: job.apply_url || '',
      apply_email: job.apply_email || '',
      recruiter_name: typeof job.recruiter?.name === 'string' ? job.recruiter.name : '',
      recruiter_email: typeof job.recruiter?.email === 'string' ? job.recruiter.email : '',
      recruiter_phone: typeof job.recruiter?.phone === 'string' ? job.recruiter.phone : '',
      how_to_apply: job.how_to_apply || '',
      application_deadline: job.application_deadline || '',
      categories: (job.categories || []).join(', '),
      tags: (job.tags || []).join(', '),
      required_docs: (job.required_docs || []).join(', '),
      description: job.description || '',
    });
  };

  const saveEdit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!accessToken || !editingId) return;
    setSaving(true);
    setError(null);
    try {
      await updateJob(accessToken, editingId, {
        company_id: editForm.company_id || undefined,
        title: editForm.title,
        slug: editForm.slug || undefined,
        company_name: editForm.company_name || undefined,
        company_logo_url: editForm.company_logo_url || undefined,
        company_website: editForm.company_website || undefined,
        company_location: editForm.company_location || undefined,
        company_size: editForm.company_size || undefined,
        company_industry: editForm.company_industry || undefined,
        department: editForm.department || undefined,
        location: {
          city: editForm.city || undefined,
          state: editForm.state || undefined,
          country: editForm.country || undefined,
          remote_type: editForm.remote_type || undefined,
        },
        employment_type: [editForm.employment_type],
        seniority: editForm.seniority,
        team_size: parseNumber(editForm.team_size),
        status: editForm.status as 'draft' | 'published' | 'closed',
        visibility: editForm.visibility as 'public' | 'private' | 'unlisted',
        skills: splitCsv(editForm.skills).map((name) => ({ name })),
        responsibilities: splitCsv(editForm.responsibilities),
        requirements: splitCsv(editForm.requirements),
        nice_to_have: splitCsv(editForm.nice_to_have),
        experience_years: parseNumber(editForm.experience_years),
        education_level: editForm.education_level || undefined,
        salary: {
          min: parseNumber(editForm.salary_min),
          max: parseNumber(editForm.salary_max),
          currency: editForm.salary_currency || undefined,
          period: editForm.salary_period || undefined,
        },
        benefits: splitCsv(editForm.benefits),
        bonus: editForm.bonus || undefined,
        equity: editForm.equity || undefined,
        apply_url: editForm.apply_url || undefined,
        apply_email: editForm.apply_email || undefined,
        recruiter: {
          name: editForm.recruiter_name || undefined,
          email: editForm.recruiter_email || undefined,
          phone: editForm.recruiter_phone || undefined,
        },
        how_to_apply: editForm.how_to_apply || undefined,
        application_deadline: editForm.application_deadline || undefined,
        categories: splitCsv(editForm.categories),
        tags: splitCsv(editForm.tags),
        remote: editForm.remote_type === 'remote',
        required_docs: splitCsv(editForm.required_docs),
        description: editForm.description || undefined,
      });
      setEditingId(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không cập nhật được yêu cầu tuyển dụng.');
    } finally {
      setSaving(false);
    }
  };

  const toggleVisibility = async (job: NormalJob) => {
    if (!accessToken) return;
    const isPublic = job.status === 'published' && job.visibility === 'public' && !job.archived;
    await updateJob(accessToken, job.id, {
      status: 'published',
      visibility: isPublic ? 'private' : 'public',
      archived: false,
    });
    await load();
  };

  const closeJob = async (job: NormalJob) => {
    if (!accessToken) return;
    await updateJob(accessToken, job.id, {
      status: 'closed',
      archived: false,
    });
    await load();
  };

  const remove = async (job: NormalJob) => {
    if (!accessToken) return;
    if (!window.confirm('Bạn chắc chắn muốn xóa yêu cầu tuyển dụng này?')) return;
    await deleteJob(accessToken, job.id);
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
          <Briefcase className="h-7 w-7 text-[#0F6FD6]" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Yêu cầu tuyển dụng của tôi</h1>
            <p className="text-sm text-gray-500">Quản lý các yêu cầu tuyển dụng normal search thuộc tài khoản hiện tại.</p>
            <p className="mt-1 text-xs text-amber-700">Draft/private jobs are not shown in public search. Publish the job to make it searchable.</p>
          </div>
        </div>
        <Link to="/employer/requests/new" className="inline-flex items-center gap-2 rounded-full bg-[#0F6FD6] px-4 py-2 text-sm font-semibold text-white shadow-sm">
          <Plus className="h-4 w-4" />
          Tạo yêu cầu tuyển dụng mới
        </Link>
      </div>

      {showCreateForm ? (
        <form onSubmit={submit} className="mb-8 grid gap-4 rounded-2xl border border-gray-100 bg-white p-5 shadow-sm md:grid-cols-2">
          <h2 className="font-bold text-gray-900 md:col-span-2">Tạo yêu cầu tuyển dụng mới</h2>
          <input value={form.company_id} onChange={(e) => setForm({ ...form, company_id: e.target.value })} placeholder="Company ID" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Tiêu đề job *" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} placeholder="Slug" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} placeholder="Tên công ty" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.company_logo_url} onChange={(e) => setForm({ ...form, company_logo_url: e.target.value })} placeholder="Logo URL" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.company_website} onChange={(e) => setForm({ ...form, company_website: e.target.value })} placeholder="Website công ty" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.company_location} onChange={(e) => setForm({ ...form, company_location: e.target.value })} placeholder="Địa chỉ công ty" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.company_size} onChange={(e) => setForm({ ...form, company_size: e.target.value })} placeholder="Quy mô công ty" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.company_industry} onChange={(e) => setForm({ ...form, company_industry: e.target.value })} placeholder="Ngành nghề" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} placeholder="Phòng ban" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} placeholder="Thành phố" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} placeholder="Tỉnh/Bang" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} placeholder="Quốc gia" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <select value={form.remote_type} onChange={(e) => setForm({ ...form, remote_type: e.target.value })} className="rounded-lg border border-gray-200 px-3 py-2 text-sm">
            <option value="onsite">On-site</option>
            <option value="hybrid">Hybrid</option>
            <option value="remote">Remote</option>
          </select>
          <select value={form.employment_type} onChange={(e) => setForm({ ...form, employment_type: e.target.value })} className="rounded-lg border border-gray-200 px-3 py-2 text-sm">
            <option value="fulltime">Full-time</option>
            <option value="parttime">Part-time</option>
            <option value="internship">Internship</option>
            <option value="contract">Contract</option>
            <option value="freelance">Freelance</option>
          </select>
          <select value={form.seniority} onChange={(e) => setForm({ ...form, seniority: e.target.value })} className="rounded-lg border border-gray-200 px-3 py-2 text-sm">
            <option value="intern">Intern</option>
            <option value="entry_level">Entry-level</option>
            <option value="junior">Junior</option>
            <option value="mid">Mid-level</option>
            <option value="senior">Senior</option>
            <option value="manager">Manager</option>
          </select>
          <input value={form.team_size} onChange={(e) => setForm({ ...form, team_size: e.target.value })} placeholder="Team size" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="rounded-lg border border-gray-200 px-3 py-2 text-sm">
            <option value="published">Published</option>
            <option value="draft">Draft</option>
            <option value="closed">Closed</option>
          </select>
          <select value={form.visibility} onChange={(e) => setForm({ ...form, visibility: e.target.value })} className="rounded-lg border border-gray-200 px-3 py-2 text-sm">
            <option value="public">Public</option>
            <option value="private">Private</option>
            <option value="unlisted">Unlisted</option>
          </select>
          <input value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} placeholder="Skills: Excel, Sales, React..." className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.experience_years} onChange={(e) => setForm({ ...form, experience_years: e.target.value })} placeholder="Số năm kinh nghiệm" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.education_level} onChange={(e) => setForm({ ...form, education_level: e.target.value })} placeholder="Trình độ học vấn" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.salary_min} onChange={(e) => setForm({ ...form, salary_min: e.target.value })} placeholder="Lương min" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.salary_max} onChange={(e) => setForm({ ...form, salary_max: e.target.value })} placeholder="Lương max" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.salary_currency} onChange={(e) => setForm({ ...form, salary_currency: e.target.value })} placeholder="Currency" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.salary_period} onChange={(e) => setForm({ ...form, salary_period: e.target.value })} placeholder="Period" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.categories} onChange={(e) => setForm({ ...form, categories: e.target.value })} placeholder="Categories" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="Tags" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.benefits} onChange={(e) => setForm({ ...form, benefits: e.target.value })} placeholder="Benefits" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.bonus} onChange={(e) => setForm({ ...form, bonus: e.target.value })} placeholder="Bonus" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.equity} onChange={(e) => setForm({ ...form, equity: e.target.value })} placeholder="Equity" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.apply_url} onChange={(e) => setForm({ ...form, apply_url: e.target.value })} placeholder="Apply URL" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.apply_email} onChange={(e) => setForm({ ...form, apply_email: e.target.value })} placeholder="Apply email" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.recruiter_name} onChange={(e) => setForm({ ...form, recruiter_name: e.target.value })} placeholder="Tên recruiter" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.recruiter_email} onChange={(e) => setForm({ ...form, recruiter_email: e.target.value })} placeholder="Email recruiter" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.recruiter_phone} onChange={(e) => setForm({ ...form, recruiter_phone: e.target.value })} placeholder="Phone recruiter" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.how_to_apply} onChange={(e) => setForm({ ...form, how_to_apply: e.target.value })} placeholder="Cách ứng tuyển" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input type="datetime-local" value={form.application_deadline} onChange={(e) => setForm({ ...form, application_deadline: e.target.value })} className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <input value={form.required_docs} onChange={(e) => setForm({ ...form, required_docs: e.target.value })} placeholder="Required docs" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
          <textarea value={form.responsibilities} onChange={(e) => setForm({ ...form, responsibilities: e.target.value })} placeholder="Responsibilities, phân tách bằng dấu phẩy" className="min-h-20 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
          <textarea value={form.requirements} onChange={(e) => setForm({ ...form, requirements: e.target.value })} placeholder="Requirements, phân tách bằng dấu phẩy" className="min-h-20 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
          <textarea value={form.nice_to_have} onChange={(e) => setForm({ ...form, nice_to_have: e.target.value })} placeholder="Nice to have, phân tách bằng dấu phẩy" className="min-h-20 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
          <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Mô tả" className="min-h-24 rounded-lg border border-gray-200 px-3 py-2 text-sm md:col-span-2" />
          <button disabled={saving} className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0F6FD6] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60 md:col-span-2">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Tạo yêu cầu tuyển dụng mới
          </button>
        </form>
      ) : null}

      {error && <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      {loading ? (
        <div className="py-10 text-center text-gray-500">Đang tải...</div>
      ) : (
        <>
          {jobs.length === 0 ? (
            <p className="mb-4 rounded-xl border border-dashed border-gray-200 bg-white px-4 py-3 text-sm text-gray-600">
              Bạn chưa có yêu cầu tuyển dụng nào. Hãy tạo yêu cầu mới.
            </p>
          ) : null}

          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
            <Link
              to="/employer/requests/new"
              aria-label="Tạo yêu cầu tuyển dụng mới"
              className="flex min-h-[260px] flex-col items-center justify-center rounded-2xl border-2 border-dashed border-blue-200 bg-white p-6 text-center shadow-sm transition hover:-translate-y-0.5 hover:border-[#0F6FD6] hover:shadow-md"
            >
              <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-[#0F6FD6]">
                <Plus className="h-9 w-9" />
              </span>
              <span className="mt-4 text-base font-bold text-gray-900">Tạo yêu cầu tuyển dụng mới</span>
              <span className="mt-2 text-sm text-gray-500">Đăng yêu cầu tuyển dụng cho normal search.</span>
            </Link>

            {jobs.map((job) => {
              const isPublic = job.status === 'published' && job.visibility === 'public' && !job.archived;
              const applicationsCount = Number(job.applications_count ?? 0);
              return (
                <article
                  key={job.id}
                  role="link"
                  tabIndex={0}
                  aria-label={`Mở yêu cầu tuyển dụng ${job.title}`}
                  onClick={() => navigate(`/employer/requests/${job.id}`)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') navigate(`/employer/requests/${job.id}`);
                  }}
                  className="group flex min-h-[260px] cursor-pointer flex-col rounded-2xl border border-gray-100 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex min-w-0 gap-3">
                      {job.company_logo_url ? (
                        <img src={job.company_logo_url} alt="" className="h-12 w-12 rounded-xl object-cover" />
                      ) : null}
                      <div className="min-w-0">
                        <h2 className="line-clamp-2 text-base font-bold text-gray-900 group-hover:text-[#0F6FD6]">{job.title}</h2>
                        <p className="mt-1 line-clamp-2 text-sm text-gray-500">{job.company_name || 'Chưa có công ty'} · {job.company_industry || 'Chưa có ngành'}</p>
                        <p className="mt-1 text-xs text-gray-400">{job.company_location || getCity(job) || 'Chưa có địa điểm'} · {(job.employment_type || []).join(', ') || 'Chưa chọn hình thức'}</p>
                      </div>
                    </div>
                    <span className="shrink-0 rounded-xl bg-blue-50 p-2 text-[#0F6FD6]">
                      <Briefcase className="h-5 w-5" />
                    </span>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2 text-xs">
                    <span className="rounded-full bg-gray-100 px-2 py-1">{job.status}</span>
                    <span className="rounded-full bg-gray-100 px-2 py-1">{job.visibility}</span>
                    <span className="rounded-full bg-gray-100 px-2 py-1">{job.archived ? 'archived' : 'active'}</span>
                  </div>

                  <div className="mt-4 rounded-xl bg-gray-50 p-3 text-xs text-gray-600">
                    <div>
                      Lương: {salarySummary(job)}
                    </div>
                    <div>Ứng tuyển: {Number.isFinite(applicationsCount) ? applicationsCount : 0}</div>
                    <div>Cập nhật: {formatDate(job.updated_at || job.created_at)}</div>
                  </div>

                  <div className="mt-auto pt-5">
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={(event) => {
                          event.stopPropagation();
                          beginEdit(job);
                        }}
                        className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-3 py-1.5 text-xs font-semibold text-gray-700"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                        Chỉnh sửa
                      </button>
                      <button
                        onClick={(event) => {
                          event.stopPropagation();
                          void toggleVisibility(job);
                        }}
                        className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700"
                      >
                        {isPublic ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                        {isPublic ? 'Ẩn' : 'Hiện công khai'}
                      </button>
                      <button
                        onClick={(event) => {
                          event.stopPropagation();
                          void closeJob(job);
                        }}
                        className="inline-flex items-center gap-1 rounded-full bg-orange-50 px-3 py-1.5 text-xs font-semibold text-orange-700"
                      >
                        <XCircle className="h-3.5 w-3.5" />
                        Đóng tuyển
                      </button>
                      <button
                        onClick={(event) => {
                          event.stopPropagation();
                          void remove(job);
                        }}
                        className="inline-flex items-center gap-1 rounded-full bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        Xóa
                      </button>
                    </div>
                  </div>

                  {editingId === job.id ? (
                    <form
                      onClick={(event) => event.stopPropagation()}
                      onSubmit={saveEdit}
                      className="mt-5 grid gap-3 rounded-xl border border-blue-100 bg-blue-50/60 p-4"
                    >
                      <h3 className="text-sm font-bold text-gray-900">Chỉnh sửa yêu cầu tuyển dụng</h3>
                      <input required value={editForm.title} onChange={(e) => setEditForm({ ...editForm, title: e.target.value })} placeholder="Tiêu đề job *" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <input value={editForm.company_name} onChange={(e) => setEditForm({ ...editForm, company_name: e.target.value })} placeholder="Tên công ty" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <input value={editForm.company_industry} onChange={(e) => setEditForm({ ...editForm, company_industry: e.target.value })} placeholder="Ngành nghề" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <input value={editForm.city} onChange={(e) => setEditForm({ ...editForm, city: e.target.value })} placeholder="Thành phố" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <input value={editForm.skills} onChange={(e) => setEditForm({ ...editForm, skills: e.target.value })} placeholder="Skills" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <input value={editForm.categories} onChange={(e) => setEditForm({ ...editForm, categories: e.target.value })} placeholder="Categories" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <input value={editForm.tags} onChange={(e) => setEditForm({ ...editForm, tags: e.target.value })} placeholder="Tags" className="rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                      <textarea value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} placeholder="Mô tả" className="min-h-20 rounded-lg border border-gray-200 px-3 py-2 text-sm" />
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

export default MyJobs;
