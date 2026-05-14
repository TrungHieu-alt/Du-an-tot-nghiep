import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, FileText } from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';
import { listMyApplications } from '../src/api/normal';
import type { NormalApplication } from '../types';

const formatDate = (value?: string): string => {
  if (!value) return 'Chua ro';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Chua ro' : date.toLocaleDateString('vi-VN');
};

const MyApplications: React.FC = () => {
  const { accessToken, isAuthenticated } = useAuth();
  const [applications, setApplications] = useState<NormalApplication[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    listMyApplications(accessToken, { limit: 50 })
      .then((result) => setApplications(result.items))
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not load applications.'))
      .finally(() => setLoading(false));
  }, [accessToken]);

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
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex items-center gap-3">
        <Briefcase className="h-7 w-7 text-[#0F6FD6]" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Applications</h1>
          <p className="text-sm text-gray-500">Jobs submitted with your saved CVs.</p>
        </div>
      </div>

      {error ? <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
      {loading ? <div className="py-10 text-center text-gray-500">Loading applications...</div> : null}

      {!loading && applications.length === 0 ? (
        <p className="rounded-xl border border-dashed border-gray-200 bg-white px-4 py-3 text-sm text-gray-600">
          You have not submitted any applications yet.
        </p>
      ) : null}

      <div className="space-y-4">
        {applications.map((application) => (
          <article key={application.id} className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <Link to={`/job/${application.job.id}`} className="text-lg font-bold text-gray-900 hover:text-[#0F6FD6]">
                  {application.job.title}
                </Link>
                <p className="text-sm text-gray-500">{application.job.companyName || 'Company not provided'}</p>
                <p className="mt-2 inline-flex items-center gap-1 text-sm text-gray-700">
                  <FileText className="h-4 w-4" />
                  CV: {application.cv.fullname}
                  {application.cv.headline ? ` - ${application.cv.headline}` : ''}
                </p>
                {application.coverLetter ? (
                  <p className="mt-3 line-clamp-3 whitespace-pre-line text-sm text-gray-700">
                    {application.coverLetter}
                  </p>
                ) : null}
              </div>
              <div className="text-left sm:text-right">
                <span className="inline-flex rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-[#0F6FD6]">
                  {application.status}
                </span>
                <p className="mt-2 text-xs text-gray-500">Submitted {formatDate(application.createdAt)}</p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
};

export default MyApplications;
