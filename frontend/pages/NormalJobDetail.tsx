import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Briefcase, FileText, MapPin, Users } from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';
import {
  createApplication,
  getJob,
  listJobApplications,
  listMyApplications,
  listMyCvs,
  updateApplicationStatus,
} from '../src/api/normal';
import type {
  NormalApplication,
  NormalApplicationStatus,
  NormalCv,
  NormalJob,
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
  if (!value) return 'Chua ro';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Chua ro' : date.toLocaleDateString('vi-VN');
};

const errorMessage = (err: unknown, fallback: string): string => {
  const responseDetail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof responseDetail === 'string') return responseDetail;
  return err instanceof Error ? err.message : fallback;
};

const NormalJobDetail: React.FC = () => {
  const { id } = useParams();
  const { accessToken, isAuthenticated, user } = useAuth();
  const [job, setJob] = useState<NormalJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cvs, setCvs] = useState<NormalCv[]>([]);
  const [applyOpen, setApplyOpen] = useState(false);
  const [selectedCvId, setSelectedCvId] = useState('');
  const [coverLetter, setCoverLetter] = useState('');
  const [applyLoading, setApplyLoading] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applySuccess, setApplySuccess] = useState<string | null>(null);
  const [alreadyApplied, setAlreadyApplied] = useState(false);
  const [applicants, setApplicants] = useState<NormalApplication[]>([]);
  const [applicantsOpen, setApplicantsOpen] = useState(false);
  const [applicantsLoading, setApplicantsLoading] = useState(false);
  const [applicantsError, setApplicantsError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getJob(id, accessToken)
      .then(setJob)
      .catch((err) => setError(err instanceof Error ? err.message : 'Không tải được job.'));
  }, [id, accessToken]);

  const isOwner = Boolean(job && user && job.created_by === user.id);

  useEffect(() => {
    if (!accessToken || !job || isOwner) return;
    listMyApplications(accessToken, { limit: 50 })
      .then((result) => {
        setAlreadyApplied(result.items.some((application) => application.jobId === job.id));
      })
      .catch(() => {
        setAlreadyApplied(false);
      });
  }, [accessToken, job, isOwner]);

  const openApply = async () => {
    setApplyOpen(true);
    setApplyError(null);
    setApplySuccess(null);
    if (!accessToken) {
      setApplyError('Please log in before applying.');
      return;
    }
    setApplyLoading(true);
    try {
      const myCvs = await listMyCvs(accessToken);
      setCvs(myCvs);
      if (!selectedCvId && myCvs.length > 0) {
        setSelectedCvId(myCvs[0].id);
      }
    } catch (err) {
      setApplyError(errorMessage(err, 'Could not load your CVs.'));
    } finally {
      setApplyLoading(false);
    }
  };

  const submitApplication = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!job || !accessToken || !selectedCvId) return;
    setApplyLoading(true);
    setApplyError(null);
    setApplySuccess(null);
    try {
      await createApplication(accessToken, {
        jobId: job.id,
        cvId: selectedCvId,
        coverLetter: coverLetter.trim() || undefined,
      });
      setAlreadyApplied(true);
      setApplyOpen(false);
      setApplySuccess('Application submitted.');
      setJob({ ...job, applications_count: Number(job.applications_count || 0) + 1 });
    } catch (err) {
      setApplyError(errorMessage(err, 'Could not submit application.'));
    } finally {
      setApplyLoading(false);
    }
  };

  const loadApplicants = async () => {
    if (!job || !accessToken) return;
    setApplicantsOpen(true);
    setApplicantsLoading(true);
    setApplicantsError(null);
    try {
      const result = await listJobApplications(accessToken, job.id, { limit: 50 });
      setApplicants(result.items);
    } catch (err) {
      setApplicantsError(errorMessage(err, 'Could not load applicants.'));
    } finally {
      setApplicantsLoading(false);
    }
  };

  const changeStatus = async (applicationId: string, nextStatus: NormalApplicationStatus) => {
    if (!accessToken) return;
    const updated = await updateApplicationStatus(accessToken, applicationId, nextStatus);
    setApplicants((current) =>
      current.map((application) => application.id === applicationId ? updated : application)
    );
  };

  if (error) return <div className="mx-auto max-w-3xl px-4 py-16 text-red-600">{error}</div>;
  if (!job) return <div className="mx-auto max-w-3xl px-4 py-16 text-gray-500">Đang tải...</div>;

  const location = job.location?.city || job.location?.remote_type || '';

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <Link to="/jobs/search" className="text-sm font-semibold text-[#0F6FD6]">Quay lại tìm việc</Link>
      <article className="mt-4 rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-blue-50 p-3 text-[#0F6FD6]">
            <Briefcase className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
            <p className="mt-2 text-gray-600">{job.company_name || 'Chưa có tên công ty'} · {job.company_industry || 'Chưa có ngành'}</p>
            {location ? (
              <p className="mt-2 inline-flex items-center gap-1 text-sm text-gray-500">
                <MapPin className="h-4 w-4" /> {String(location)}
              </p>
            ) : null}
          </div>
        </div>
        {job.description ? <p className="mt-6 whitespace-pre-line text-gray-700">{job.description}</p> : null}
        {job.requirements.length > 0 && (
          <section className="mt-6">
            <h2 className="font-bold text-gray-900">Yêu cầu</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
              {job.requirements.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </section>
        )}
        {job.skills.length > 0 && (
          <div className="mt-6 flex flex-wrap gap-2">
            {job.skills.map((skill) => (
              <span key={String(skill.name)} className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-[#0F6FD6]">
                {String(skill.name)}
              </span>
            ))}
          </div>
        )}
        <section className="mt-8 border-t border-gray-100 pt-6">
          {isOwner ? (
            <div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="font-bold text-gray-900">Applicants</h2>
                  <p className="text-sm text-gray-500">
                    {Number(job.applications_count || 0)} submitted applications
                  </p>
                </div>
                <button
                  type="button"
                  onClick={loadApplicants}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0F6FD6] px-4 py-2 text-sm font-semibold text-white"
                >
                  <Users className="h-4 w-4" />
                  View applicants
                </button>
              </div>
              {applicantsOpen ? (
                <div className="mt-5 space-y-4">
                  {applicantsLoading ? <p className="text-sm text-gray-500">Loading applicants...</p> : null}
                  {applicantsError ? <p className="text-sm text-red-600">{applicantsError}</p> : null}
                  {!applicantsLoading && applicants.length === 0 ? (
                    <p className="text-sm text-gray-500">No applications yet.</p>
                  ) : null}
                  {applicants.map((application) => (
                    <article key={application.id} className="border-t border-gray-100 pt-4">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-900">{application.cv.fullname}</h3>
                          {application.cv.headline ? (
                            <p className="text-sm text-gray-600">{application.cv.headline}</p>
                          ) : null}
                          <p className="text-xs text-gray-500">
                            Submitted {formatDate(application.createdAt)}
                          </p>
                          {application.coverLetter ? (
                            <p className="mt-2 whitespace-pre-line text-sm text-gray-700">{application.coverLetter}</p>
                          ) : null}
                        </div>
                        <label className="text-sm font-medium text-gray-700">
                          Status
                          <select
                            value={application.status}
                            onChange={(event) =>
                              void changeStatus(application.id, event.target.value as NormalApplicationStatus)
                            }
                            className="mt-1 block rounded-lg border border-gray-200 px-3 py-2 text-sm"
                            aria-label={`Application status for ${application.cv.fullname}`}
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
              ) : null}
            </div>
          ) : (
            <div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="font-bold text-gray-900">Apply</h2>
                  <p className="text-sm text-gray-500">Submit one of your saved CVs for this job.</p>
                </div>
                {isAuthenticated ? (
                  <button
                    type="button"
                    onClick={openApply}
                    disabled={alreadyApplied}
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#00A86B] px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <FileText className="h-4 w-4" />
                    {alreadyApplied ? 'Already applied' : 'Apply with CV'}
                  </button>
                ) : (
                  <Link to="/login" className="inline-flex items-center justify-center rounded-lg bg-[#0F6FD6] px-4 py-2 text-sm font-semibold text-white">
                    Log in to apply
                  </Link>
                )}
              </div>
              {applySuccess ? <p className="mt-3 text-sm text-green-700">{applySuccess}</p> : null}
              {applyOpen ? (
                <form onSubmit={submitApplication} className="mt-5 space-y-4">
                  {applyLoading ? <p className="text-sm text-gray-500">Loading...</p> : null}
                  {applyError ? <p className="text-sm text-red-600">{applyError}</p> : null}
                  {!applyLoading && cvs.length === 0 ? (
                    <p className="text-sm text-gray-600">No CV available. Create a CV before applying.</p>
                  ) : null}
                  {cvs.length > 0 ? (
                    <fieldset>
                      <legend className="text-sm font-semibold text-gray-900">Select CV</legend>
                      <div className="mt-2 space-y-2">
                        {cvs.map((cv) => (
                          <label key={cv.id} className="flex gap-3 rounded-lg border border-gray-200 px-3 py-2 text-sm">
                            <input
                              type="radio"
                              name="cvId"
                              value={cv.id}
                              checked={selectedCvId === cv.id}
                              onChange={() => setSelectedCvId(cv.id)}
                            />
                            <span>
                              <span className="font-semibold text-gray-900">{cv.fullname}</span>
                              {cv.headline ? <span className="block text-gray-500">{cv.headline}</span> : null}
                            </span>
                          </label>
                        ))}
                      </div>
                    </fieldset>
                  ) : null}
                  <div>
                    <label htmlFor="cover-letter" className="text-sm font-semibold text-gray-900">Cover letter</label>
                    <textarea
                      id="cover-letter"
                      value={coverLetter}
                      onChange={(event) => setCoverLetter(event.target.value)}
                      rows={4}
                      className="mt-2 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={!selectedCvId || applyLoading}
                    className="rounded-lg bg-[#00A86B] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                  >
                    Submit application
                  </button>
                </form>
              ) : null}
            </div>
          )}
        </section>
      </article>
    </div>
  );
};

export default NormalJobDetail;
