import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Briefcase, MapPin } from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';
import { getJob } from '../src/api/normal';
import type { NormalJob } from '../types';

const NormalJobDetail: React.FC = () => {
  const { id } = useParams();
  const { accessToken } = useAuth();
  const [job, setJob] = useState<NormalJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getJob(id, accessToken)
      .then(setJob)
      .catch((err) => setError(err instanceof Error ? err.message : 'Không tải được job.'));
  }, [id, accessToken]);

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
      </article>
    </div>
  );
};

export default NormalJobDetail;
