import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Briefcase, Eye, EyeOff, Pencil, Plus, Trash2, Users, XCircle } from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';
import {
  createJob,
  deleteJob,
  listJobApplications,
  listMyJobs,
  updateApplicationStatus,
  updateJob,
} from '../src/api/normal';
import JobFormWizard, {
  createEmptyJobForm,
  jobFormFromNormalJob,
  type JobFormState,
} from '../components/normal/JobFormWizard';
import type {
  NormalApplication,
  NormalApplicationStatus,
  NormalJob,
  NormalJobCreatePayload,
} from '../types';

const APPLICATION_STATUSES: NormalApplicationStatus[] = [
  'submitted',
  'reviewing',
  'shortlisted',
  'rejected',
  'accepted',
  'withdrawn',
];

const formatDate = (value?: string): string => {
  if (!value) return 'Chưa rõ';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Chưa rõ' : date.toLocaleDateString('vi-VN');
};

const getCity = (job: NormalJob): string => {
  const value = job.location?.city;
  return typeof value === 'string' ? value : '';
};

const salarySummary = (job: NormalJob): string => {
  const min = job.salary?.min;
  const max = job.salary?.max;
  const currency = typeof job.salary?.currency === 'string' ? job.salary.currency : '';
  if (min === undefined && max === undefined) return 'Chưa công khai';
  return `${min ?? '?'} - ${max ?? '?'} ${currency}`.trim();
};

const errorMessage = (err: unknown, fallback: string): string => {
  const responseDetail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof responseDetail === 'string') return responseDetail;
  return err instanceof Error ? err.message : fallback;
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
  const [form, setForm] = useState<JobFormState>(createEmptyJobForm());
  const [editForm, setEditForm] = useState<JobFormState | null>(null);
  const [applicantsJobId, setApplicantsJobId] = useState<string | null>(null);
  const [applicants, setApplicants] = useState<NormalApplication[]>([]);
  const [applicantsLoading, setApplicantsLoading] = useState(false);
  const [applicantsError, setApplicantsError] = useState<string | null>(null);

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

  const submit = async (payload: NormalJobCreatePayload) => {
    if (!accessToken) return;
    setSaving(true);
    setError(null);
    try {
      await createJob(accessToken, payload);
      setForm(createEmptyJobForm());
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
    setEditForm(jobFormFromNormalJob(job));
  };

  const saveEdit = async (payload: NormalJobCreatePayload) => {
    if (!accessToken || !editingId) return;
    setSaving(true);
    setError(null);
    try {
      await updateJob(accessToken, editingId, payload);
      setEditingId(null);
      setEditForm(null);
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

  const viewApplicants = async (job: NormalJob) => {
    if (!accessToken) return;
    if (applicantsJobId === job.id) {
      setApplicantsJobId(null);
      setApplicants([]);
      return;
    }
    setApplicantsJobId(job.id);
    setApplicants([]);
    setApplicantsLoading(true);
    setApplicantsError(null);
    try {
      const result = await listJobApplications(accessToken, job.id, { limit: 50 });
      setApplicants(result.items);
    } catch (err) {
      setApplicantsError(errorMessage(err, 'Không tải được danh sách ứng viên.'));
    } finally {
      setApplicantsLoading(false);
    }
  };

  const changeApplicationStatus = async (
    applicationId: string,
    nextStatus: NormalApplicationStatus
  ) => {
    if (!accessToken) return;
    const updated = await updateApplicationStatus(accessToken, applicationId, nextStatus);
    setApplicants((current) =>
      current.map((application) => application.id === applicationId ? updated : application)
    );
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
        <div className="mb-8">
          <JobFormWizard initialValue={form} saving={saving} onSubmit={submit} onCancel={() => navigate('/employer/requests')} />
        </div>
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
	                          void viewApplicants(job);
	                        }}
	                        className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-3 py-1.5 text-xs font-semibold text-[#0F6FD6]"
	                      >
	                        <Users className="h-3.5 w-3.5" />
	                        View applicants
	                      </button>
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

                  {editingId === job.id && editForm ? (
                    <div
                      onClick={(event) => event.stopPropagation()}
                      className="mt-5 rounded-xl border border-blue-100 bg-blue-50/60 p-4"
                    >
                      <JobFormWizard
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

	                  {applicantsJobId === job.id ? (
	                    <div
	                      onClick={(event) => event.stopPropagation()}
	                      className="mt-5 border-t border-gray-100 pt-4"
	                    >
	                      <h3 className="text-sm font-bold text-gray-900">Applicants</h3>
	                      {applicantsLoading ? <p className="mt-2 text-sm text-gray-500">Loading applicants...</p> : null}
	                      {applicantsError ? <p className="mt-2 text-sm text-red-600">{applicantsError}</p> : null}
	                      {!applicantsLoading && applicants.length === 0 ? (
	                        <p className="mt-2 text-sm text-gray-500">No applications yet.</p>
	                      ) : null}
	                      <div className="mt-3 space-y-3">
	                        {applicants.map((application) => (
	                          <article key={application.id} className="border-t border-gray-100 pt-3">
	                            <div className="flex flex-col gap-2">
	                              <div>
	                                <p className="font-semibold text-gray-900">{application.cv.fullname}</p>
	                                {application.cv.headline ? (
	                                  <p className="text-sm text-gray-600">{application.cv.headline}</p>
	                                ) : null}
	                                <p className="text-xs text-gray-500">
	                                  Submitted {formatDate(application.createdAt)}
	                                </p>
	                                {application.coverLetter ? (
	                                  <p className="mt-1 line-clamp-3 text-sm text-gray-700">{application.coverLetter}</p>
	                                ) : null}
	                              </div>
	                              <label className="text-xs font-semibold text-gray-700">
	                                Status
	                                <select
	                                  value={application.status}
	                                  onChange={(event) =>
	                                    void changeApplicationStatus(
	                                      application.id,
	                                      event.target.value as NormalApplicationStatus
	                                    )
	                                  }
	                                  aria-label={`Application status for ${application.cv.fullname}`}
	                                  className="mt-1 block w-full rounded-lg border border-gray-200 px-2 py-1.5 text-sm"
	                                >
	                                  {APPLICATION_STATUSES.map((statusValue) => (
	                                    <option key={statusValue} value={statusValue}>{statusValue}</option>
	                                  ))}
	                                </select>
	                              </label>
	                            </div>
	                          </article>
	                        ))}
	                      </div>
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

export default MyJobs;
