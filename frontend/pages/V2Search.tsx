import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Briefcase,
  Loader2,
  Search,
  Sparkles,
  UserCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  FileSearch,
} from 'lucide-react';
import type {
  AnchorTypeV2,
  CVSearchItem,
  JobSearchItem,
  JobTypeV2,
  LocationV2,
  SeniorityV2,
} from '../types';
import { searchV2Cvs, searchV2Jobs } from '../src/api/v2';
import V2LocationSelect from '../components/v2/V2LocationSelect';
import type { V2LocationValue } from '../components/v2/V2LocationSelect';
import V2SearchFilterPanel from '../components/v2/V2SearchFilterPanel';
import type { V2SearchFilters } from '../components/v2/V2SearchFilterPanel';
import V2SearchResultCard from '../components/v2/V2SearchResultCard';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SCORE_THRESHOLD = 0.2;
const TOP_K = 20;

// ---------------------------------------------------------------------------
// URL-param helpers
// ---------------------------------------------------------------------------

const isLocation = (v: string | null): v is LocationV2 =>
  v === 'ha_noi' || v === 'tp_hcm' || v === 'da_nang';

const isJobType = (v: string | null): v is JobTypeV2 =>
  v === 'remote' || v === 'fulltime' || v === 'parttime';

const isSeniority = (v: string | null): v is SeniorityV2 =>
  v === 'intern' || v === 'fresher' || v === 'junior' || v === 'mid' || v === 'senior' || v === 'lead';

const parseType = (v: string | null): AnchorTypeV2 => (v === 'cv' ? 'cv' : 'job');

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const V2Search: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Derive request from URL params (the URL is the single source of truth).
  const urlQ = searchParams.get('q') ?? '';
  const urlType: AnchorTypeV2 = parseType(searchParams.get('type'));
  const urlLocation: LocationV2 | undefined = isLocation(searchParams.get('location'))
    ? (searchParams.get('location') as LocationV2)
    : undefined;
  const urlJobType: JobTypeV2 | undefined = isJobType(searchParams.get('job_type'))
    ? (searchParams.get('job_type') as JobTypeV2)
    : undefined;
  const urlSeniority: SeniorityV2 | undefined = isSeniority(searchParams.get('seniority'))
    ? (searchParams.get('seniority') as SeniorityV2)
    : undefined;

  // Local input draft so the user can type without spamming navigation.
  const [inputQ, setInputQ] = useState(urlQ);
  const [inputLocation, setInputLocation] = useState<V2LocationValue>(urlLocation ?? '');
  // Sync drafts with URL when URL changes (e.g. back/forward).
  useEffect(() => setInputQ(urlQ), [urlQ]);
  useEffect(() => setInputLocation(urlLocation ?? ''), [urlLocation]);

  // Results
  const [items, setItems] = useState<JobSearchItem[] | CVSearchItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showLowScore, setShowLowScore] = useState(false);

  // Trigger fetch on URL changes.
  useEffect(() => {
    if (!urlQ.trim()) {
      // Empty query → clear results, no API call.
      setItems([]);
      setTotal(0);
      setLoading(false);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    setShowLowScore(false);
    const body = {
      q: urlQ.trim(),
      top_k: TOP_K,
      location: urlLocation,
      job_type: urlJobType,
      seniority: urlSeniority,
    };
    const promise = urlType === 'job' ? searchV2Jobs(body) : searchV2Cvs(body);
    promise
      .then((res) => {
        if (cancelled) return;
        setItems(res.items as JobSearchItem[] | CVSearchItem[]);
        setTotal(res.total);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Lỗi khi tìm kiếm.');
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [urlQ, urlType, urlLocation, urlJobType, urlSeniority]);

  // ---------------- Update URL helpers ----------------

  const updateUrl = useCallback(
    (
      patch: {
        q?: string;
        type?: AnchorTypeV2;
        location?: LocationV2 | '';
        job_type?: JobTypeV2 | '';
        seniority?: SeniorityV2 | '';
      }
    ) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (patch.q !== undefined) {
          if (patch.q) next.set('q', patch.q);
          else next.delete('q');
        }
        if (patch.type !== undefined) next.set('type', patch.type);
        if (patch.location !== undefined) {
          if (patch.location) next.set('location', patch.location);
          else next.delete('location');
        }
        if (patch.job_type !== undefined) {
          if (patch.job_type) next.set('job_type', patch.job_type);
          else next.delete('job_type');
        }
        if (patch.seniority !== undefined) {
          if (patch.seniority) next.set('seniority', patch.seniority);
          else next.delete('seniority');
        }
        return next;
      });
    },
    [setSearchParams]
  );

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    updateUrl({
      q: inputQ.trim(),
      type: urlType,
      location: urlType === 'job' ? inputLocation : '',
    });
  };

  const handleToggleType = (next: AnchorTypeV2) => {
    if (next === urlType) return;
    updateUrl({ type: next });
  };

  const handleFiltersChange = (next: V2SearchFilters) => {
    updateUrl({
      location: next.location ?? '',
      job_type: next.job_type ?? '',
      seniority: next.seniority ?? '',
    });
  };

  // ---------------- Score split ----------------

  const { highScore, lowScore } = useMemo(() => {
    const high: typeof items = [];
    const low: typeof items = [];
    items.forEach((it) => {
      if (it.score >= SCORE_THRESHOLD) high.push(it as never);
      else low.push(it as never);
    });
    return { highScore: high, lowScore: low };
  }, [items]);

  const filtersForPanel: V2SearchFilters = {
    location: urlLocation,
    job_type: urlJobType,
    seniority: urlSeniority,
  };
  const isJobMode = urlType === 'job';

  return (
    <div className="bg-[#F5F7FC] min-h-screen pb-20">
      {/* Sticky top search bar */}
      <div className="bg-white border-b border-gray-100 sticky top-20 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          {/* Toggle Job/CV */}
          <div className="flex items-center gap-2 mb-3">
            <button
              type="button"
              onClick={() => handleToggleType('job')}
              className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-semibold transition-colors ${
                isJobMode
                  ? 'bg-[#0A65CC] text-white shadow-sm'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Briefcase className="w-4 h-4" /> Tìm Job
            </button>
            <button
              type="button"
              onClick={() => handleToggleType('cv')}
              className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-semibold transition-colors ${
                !isJobMode
                  ? 'bg-[#00B14F] text-white shadow-sm'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <UserCircle className="w-4 h-4" /> Tìm CV
            </button>
          </div>

          {/* Search row */}
          <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                value={inputQ}
                onChange={(e) => setInputQ(e.target.value)}
                placeholder={
                  isJobMode
                    ? 'Tên công việc, kỹ năng, level…'
                    : 'Vị trí, kỹ năng ứng viên cần tìm…'
                }
                className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-full text-[15px] placeholder-gray-400 focus:outline-none focus:bg-white focus:border-[#0A65CC] focus:ring-2 focus:ring-[#0A65CC]/20"
              />
            </div>
            {isJobMode && (
              <div className="md:w-64">
                <V2LocationSelect
                  value={inputLocation}
                  onChange={(v) => setInputLocation(v)}
                  placeholder="Khu vực"
                />
              </div>
            )}
            <button
              type="submit"
              className="px-6 py-3 rounded-full bg-[#0A65CC] text-white font-semibold text-sm hover:bg-[#085bb8] transition-colors whitespace-nowrap"
            >
              Tìm kiếm
            </button>
          </form>
        </div>
      </div>

      {/* Body */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-3">
          <V2SearchFilterPanel
            filters={filtersForPanel}
            onChange={handleFiltersChange}
          />
          <div className="mt-4 px-4 py-3 bg-amber-50 border border-amber-100 rounded-lg text-xs text-amber-800">
            <p className="font-semibold mb-1 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" /> V2 prototype
            </p>
            <p className="opacity-80">
              Hiện có 6 jobs và 36 CVs trong seed. Hash-based embedder so khớp theo từ
              (token-only). Thử các từ khóa: "backend", "frontend", "devops", "python".
            </p>
          </div>
        </div>

        {/* Results */}
        <main className="lg:col-span-9">
          {/* Header */}
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <h1 className="text-lg font-bold text-gray-900">
              {urlQ.trim() ? (
                <>
                  Tìm thấy <span className="text-[#0A65CC] tabular-nums">{total}</span> kết quả
                  cho "<span className="text-gray-700">{urlQ.trim()}</span>"
                </>
              ) : (
                'Nhập từ khóa để bắt đầu'
              )}
            </h1>
          </div>

          {/* States */}
          {loading && <RunningSpinner />}

          {error && !loading && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {!loading && !error && urlQ.trim() && total === 0 && (
            <EmptyState type={urlType} />
          )}

          {!loading && !error && total > 0 && (
            <ResultsList
              type={urlType}
              highScore={highScore}
              lowScore={lowScore}
              showLowScore={showLowScore}
              onToggleLow={() => setShowLowScore((s) => !s)}
            />
          )}

          {/* Initial empty (no query yet) */}
          {!loading && !error && !urlQ.trim() && (
            <div className="text-center py-16 text-gray-400">
              <Search className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p className="text-sm">
                Gõ vài từ khóa rồi bấm <strong className="text-gray-600">Tìm kiếm</strong>.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const RunningSpinner: React.FC = () => (
  <div className="flex flex-col items-center justify-center py-16 text-gray-500">
    <Loader2 className="w-8 h-8 animate-spin text-[#0A65CC] mb-3" />
    <p className="text-sm">Đang tìm kiếm…</p>
  </div>
);

const EmptyState: React.FC<{ type: AnchorTypeV2 }> = ({ type }) => (
  <div className="text-center py-16 border-2 border-dashed border-gray-200 rounded-xl">
    <FileSearch className="w-12 h-12 mx-auto mb-3 text-gray-300" />
    <p className="text-sm font-medium text-gray-700 mb-1">
      Không tìm thấy {type === 'job' ? 'job' : 'CV'} phù hợp.
    </p>
    <p className="text-xs text-gray-500">
      V2 prototype hiện có {type === 'job' ? '6 jobs' : '36 CVs'}. Thử từ khóa khác hoặc bỏ
      bớt filter.
    </p>
  </div>
);

interface ResultsListProps {
  type: AnchorTypeV2;
  highScore: (JobSearchItem | CVSearchItem)[];
  lowScore: (JobSearchItem | CVSearchItem)[];
  showLowScore: boolean;
  onToggleLow: () => void;
}

const ResultsList: React.FC<ResultsListProps> = ({
  type,
  highScore,
  lowScore,
  showLowScore,
  onToggleLow,
}) => {
  const noHigh = highScore.length === 0;
  return (
    <div className="space-y-4">
      {/* High-score list */}
      {!noHigh && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {highScore.map((it) => (
            <V2SearchResultCard
              key={`${type}-${type === 'job' ? (it as JobSearchItem).job_id : (it as CVSearchItem).cv_id}`}
              item={it}
              type={type}
            />
          ))}
        </div>
      )}

      {/* Low-score: auto-expanded if no high; otherwise collapsible */}
      {lowScore.length > 0 && (
        <div>
          {noHigh ? (
            <div className="mb-3 p-3 bg-amber-50 border border-amber-100 rounded-lg text-xs text-amber-800">
              Không có kết quả phù hợp cao. Hiển thị các kết quả gần đúng nhất:
            </div>
          ) : (
            <button
              type="button"
              onClick={onToggleLow}
              className="w-full mb-3 px-4 py-2 rounded-lg bg-gray-50 hover:bg-gray-100 text-sm text-gray-600 inline-flex items-center justify-between transition-colors"
            >
              <span>
                Xem thêm <strong className="text-gray-900">{lowScore.length}</strong> kết quả
                ít liên quan (score &lt; 20%)
              </span>
              {showLowScore ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          )}

          {(noHigh || showLowScore) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {lowScore.map((it) => (
                <V2SearchResultCard
                  key={`${type}-${type === 'job' ? (it as JobSearchItem).job_id : (it as CVSearchItem).cv_id}`}
                  item={it}
                  type={type}
                  lowScore
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default V2Search;
