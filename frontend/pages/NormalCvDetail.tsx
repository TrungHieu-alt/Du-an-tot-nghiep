import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { FileText } from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';
import { getCv } from '../src/api/normal';
import type { NormalCv } from '../types';

const getOriginalName = (cv: NormalCv): string => {
  const value = cv.file?.originalname;
  return typeof value === 'string' ? value : '';
};

const NormalCvDetail: React.FC = () => {
  const { id } = useParams();
  const { accessToken, isAuthenticated } = useAuth();
  const [cv, setCv] = useState<NormalCv | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getCv(accessToken, id)
      .then(setCv)
      .catch((err) => setError(err instanceof Error ? err.message : 'Không tải được CV.'));
  }, [id, accessToken]);

  if (error) return <div className="mx-auto max-w-3xl px-4 py-16 text-red-600">{error}</div>;
  if (!cv) return <div className="mx-auto max-w-3xl px-4 py-16 text-gray-500">Đang tải...</div>;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <Link to={isAuthenticated ? '/cvs' : '/cvs/search'} className="text-sm font-semibold text-[#0F6FD6]">
        {isAuthenticated ? 'Quay lại CV của tôi' : 'Quay lại tìm CV'}
      </Link>
      <article className="mt-4 rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-emerald-50 p-3 text-[#00A86B]">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{cv.fullname || getOriginalName(cv) || 'PDF CV'}</h1>
            <p className="mt-2 text-gray-600">{cv.target_role || cv.headline || 'Chưa có vị trí mong muốn'}</p>
          </div>
        </div>
        {cv.summary ? <p className="mt-6 whitespace-pre-line text-gray-700">{cv.summary}</p> : null}
        {getOriginalName(cv) ? (
          <div className="mt-6 rounded-lg bg-blue-50 p-4 text-sm text-blue-800">
            PDF: {getOriginalName(cv)}
          </div>
        ) : null}
        {cv.skills.length > 0 && (
          <div className="mt-6 flex flex-wrap gap-2">
            {cv.skills.map((skill) => (
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

export default NormalCvDetail;
