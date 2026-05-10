import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Award,
  Briefcase,
  FileSearch,
  GraduationCap,
  Loader2,
  MapPin,
  Play,
  Tag,
} from 'lucide-react';
import type { JobV2Detail } from '../types';
import { getV2Job } from '../src/api/v2';
import {
  formatEducationV2,
  formatJobTypeV2,
  formatLocationV2,
  formatSeniorityV2,
} from '../components/v2/v2-format';

type LoadState =
  | { status: 'loading' }
  | { status: 'ok'; data: JobV2Detail }
  | { status: 'not_found' }
  | { status: 'error'; message: string };

const parseId = (raw: string | undefined): number | null => {
  if (!raw) return null;
  const n = Number(raw);
  if (!Number.isFinite(n) || n <= 0 || !Number.isInteger(n)) return null;
  return n;
};

const errorStatus = (err: unknown): number | undefined => {
  if (err && typeof err === 'object' && 'response' in err) {
    const r = (err as { response?: { status?: number } }).response;
    return r?.status;
  }
  return undefined;
};

const V2JobDetail: React.FC = () => {
  const { id: rawId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const id = parseId(rawId);

  const [state, setState] = useState<LoadState>({ status: 'loading' });

  useEffect(() => {
    if (id === null) {
      setState({ status: 'not_found' });
      return;
    }
    let cancelled = false;
    setState({ status: 'loading' });
    getV2Job(id)
      .then((data) => {
        if (cancelled) return;
        setState({ status: 'ok', data });
      })
      .catch((err) => {
        if (cancelled) return;
        if (errorStatus(err) === 404) {
          setState({ status: 'not_found' });
        } else {
          setState({
            status: 'error',
            message: err instanceof Error ? err.message : 'Đã có lỗi xảy ra.',
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  // ---------------- Render branches ----------------

  if (state.status === 'loading') {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 flex flex-col items-center text-gray-400">
        <Loader2 className="w-8 h-8 animate-spin mb-3" />
        <p className="text-sm">Đang tải chi tiết job…</p>
      </div>
    );
  }

  if (state.status === 'not_found') {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <FileSearch className="w-14 h-14 mx-auto text-gray-300 mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">Không tìm thấy job</h1>
        <p className="text-sm text-gray-500 mb-6">
          Job với ID <span className="font-mono">{rawId}</span> không tồn tại trong V2 catalog.
        </p>
        <Link
          to="/v2/search?type=job"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#0A65CC] text-white font-semibold text-sm hover:bg-[#085bb8] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Quay lại tìm kiếm
        </Link>
      </div>
    );
  }

  if (state.status === 'error') {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <p className="text-sm text-red-600">{state.message}</p>
      </div>
    );
  }

  const job = state.data;

  return (
    <div className="bg-[#F5F7FC] min-h-screen pb-20">
      {/* Hero */}
      <section className="bg-gradient-to-r from-[#0A65CC] to-[#00B14F] text-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-1.5 text-blue-50 hover:text-white text-sm mb-5 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Quay lại
          </button>
          <div className="flex items-center gap-2 text-blue-50 text-xs font-mono mb-2">
            <Briefcase className="w-3.5 h-3.5" />
            <span>JOB · #{job.job_id}</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-4 leading-tight">
            {job.title}
          </h1>
          <div className="flex flex-wrap gap-2 text-sm">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-sm">
              <MapPin className="w-3.5 h-3.5" /> {formatLocationV2(job.location)}
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-sm">
              <Briefcase className="w-3.5 h-3.5" /> {formatJobTypeV2(job.job_type)}
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-sm">
              <Award className="w-3.5 h-3.5" /> {formatSeniorityV2(job.seniority)}
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-sm">
              <GraduationCap className="w-3.5 h-3.5" /> {formatEducationV2(job.education)}
            </span>
          </div>
        </div>
      </section>

      {/* Body */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Skills */}
          <Card title="Skills yêu cầu" icon={<Tag className="w-4 h-4" />}>
            {job.skills.length === 0 ? (
              <p className="text-sm text-gray-400 italic">Chưa có thông tin.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {job.skills.map((s) => (
                  <span
                    key={s}
                    className="inline-flex px-3 py-1 rounded-md bg-blue-50 text-[#0A65CC] text-sm font-medium"
                  >
                    {s}
                  </span>
                ))}
              </div>
            )}
          </Card>

          {/* Requirement */}
          <Card title="Mô tả yêu cầu" icon={<FileSearch className="w-4 h-4" />}>
            {job.requirement ? (
              <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                {job.requirement}
              </p>
            ) : (
              <p className="text-sm text-gray-400 italic">Chưa có mô tả.</p>
            )}
          </Card>

          {/* Required certifications */}
          <Card
            title="Chứng chỉ yêu cầu"
            icon={<Award className="w-4 h-4" />}
          >
            {job.required_certifications.length === 0 ? (
              <p className="text-sm text-gray-400 italic">Không yêu cầu chứng chỉ cụ thể.</p>
            ) : (
              <ul className="space-y-1.5 text-sm text-gray-700">
                {job.required_certifications.map((c) => (
                  <li key={c} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#00B14F]" />
                    {c}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        {/* Action panel — sticky */}
        <aside className="lg:col-span-1">
          <div className="lg:sticky lg:top-24 space-y-4">
            <div className="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
              <p className="text-xs uppercase tracking-wide text-gray-500 mb-2">
                Matching V2
              </p>
              <p className="text-sm text-gray-700 mb-4">
                Tìm các CV phù hợp nhất với job này dùng pipeline pgvector.
              </p>
              <Link
                to={`/v2/matching?anchor=job&id=${job.job_id}`}
                className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-[#0A65CC] to-[#00B14F] shadow-md shadow-blue-500/20 hover:shadow-lg transition-all duration-300 transform hover:-translate-y-0.5"
              >
                <Play className="w-4 h-4" /> Run Matching V2
              </Link>
              <Link
                to="/v2/search?type=job"
                className="mt-2 w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl font-medium text-gray-600 hover:bg-gray-50 transition-colors text-sm"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Quay lại tìm kiếm
              </Link>
            </div>

            <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 text-xs text-amber-800">
              <p className="font-semibold mb-1">V2 prototype</p>
              <p className="opacity-80">
                Dữ liệu đến từ Postgres + pgvector. Run Matching trả top 10 CV theo cosine
                similarity blend title+skills, thêm filter cứng location/job_type/seniority.
              </p>
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Local Card subcomponent — keeps page layout consistent without a new file.
// ---------------------------------------------------------------------------

const Card: React.FC<{
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}> = ({ title, icon, children }) => (
  <div className="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
    <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2 mb-3">
      {icon}
      {title}
    </h2>
    {children}
  </div>
);

export default V2JobDetail;
