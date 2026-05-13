import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import {
  Briefcase,
  Loader2,
  Search,
  Sparkles,
  UserCircle,
  AlertCircle,
  FileSearch,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type {
  AnchorTypeV2,
  NormalCVSearchItem,
  NormalCVSearchParams,
  NormalJobSearchItem,
  NormalJobSearchParams,
} from '../types';
import { searchCvs, searchJobs } from '../src/api/normal';
import { useAuth } from '../contexts/AuthContext';
import V2SearchFilterPanel, {
  LOCATION_OPTIONS,
  type V2SearchFilters,
} from '../components/v2/V2SearchFilterPanel';
import V2SearchResultCard from '../components/v2/V2SearchResultCard';

const PAGE_LIMIT = 10;

const FILTER_KEYS: Array<keyof V2SearchFilters> = [
  'location',
  'industry',
  'employmentType',
  'experienceLevel',
  'salaryRange',
  'educationLevel',
  'workingModel',
  'sort',
  'skills',
  'yearsOfExperience',
  'expectedSalaryRange',
  'availability',
];

const parseType = (v: string | null, pathname: string): AnchorTypeV2 => {
  if (v === 'cv') return 'cv';
  if (v === 'job') return 'job';
  return pathname.startsWith('/cvs') ? 'cv' : 'job';
};

const salaryToRange = (value?: string): { min?: number; max?: number } => {
  switch (value) {
    case 'under_10m':
      return { max: 10_000_000 };
    case '10_20m':
      return { min: 10_000_000, max: 20_000_000 };
    case '20_30m':
      return { min: 20_000_000, max: 30_000_000 };
    case '30_50m':
      return { min: 30_000_000, max: 50_000_000 };
    case '50m_plus':
      return { min: 50_000_000 };
    default:
      return {};
  }
};

const hasActiveSearch = (q: string, filters: V2SearchFilters): boolean =>
  Boolean(q.trim()) || Object.values(filters).some((value) => Boolean(value));

const V2Search: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const { user } = useAuth();

  const urlQ = searchParams.get('q') ?? '';
  const urlType: AnchorTypeV2 = parseType(searchParams.get('type'), location.pathname);
  const urlPage = Math.max(1, Number(searchParams.get('page') ?? '1') || 1);

  const filtersFromUrl = useMemo<V2SearchFilters>(() => {
    const filters: V2SearchFilters = {};
    FILTER_KEYS.forEach((key) => {
      const value = searchParams.get(key);
      if (value) {
        filters[key] = value;
      }
    });
    return filters;
  }, [searchParams]);

  const [inputQ, setInputQ] = useState(urlQ);
  const [inputLocation, setInputLocation] = useState(filtersFromUrl.location ?? '');

  useEffect(() => setInputQ(urlQ), [urlQ]);
  useEffect(() => setInputLocation(filtersFromUrl.location ?? ''), [filtersFromUrl.location]);

  const [items, setItems] = useState<Array<NormalJobSearchItem | NormalCVSearchItem>>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isJobMode = urlType === 'job';
  const hasSearch = hasActiveSearch(urlQ, filtersFromUrl);
  const shouldFetch = true;

  useEffect(() => {
    if (!shouldFetch) {
      setItems([]);
      setTotal(0);
      setTotalPages(0);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    const salary = salaryToRange(filtersFromUrl.salaryRange);
    const expectedSalary = salaryToRange(filtersFromUrl.expectedSalaryRange);

    const promise =
      urlType === 'job'
        ? searchJobs({
            q: urlQ.trim() || undefined,
            location: filtersFromUrl.location,
            industry: filtersFromUrl.industry,
            employmentType: filtersFromUrl.employmentType,
            experienceLevel: filtersFromUrl.experienceLevel,
            salaryMin: salary.min,
            salaryMax: salary.max,
            educationLevel: filtersFromUrl.educationLevel,
            workingModel: filtersFromUrl.workingModel,
            skills: filtersFromUrl.skills,
            page: urlPage,
            limit: PAGE_LIMIT,
            sort: filtersFromUrl.sort ?? 'newest',
          } satisfies NormalJobSearchParams)
        : searchCvs({
            q: urlQ.trim() || undefined,
            location: filtersFromUrl.location,
            desiredIndustry: filtersFromUrl.industry,
            experienceLevel: filtersFromUrl.experienceLevel,
            yearsOfExperience: filtersFromUrl.yearsOfExperience,
            educationLevel: filtersFromUrl.educationLevel,
            expectedSalaryMin: expectedSalary.min,
            expectedSalaryMax: expectedSalary.max,
            workingModel: filtersFromUrl.workingModel,
            availability: filtersFromUrl.availability,
            skills: filtersFromUrl.skills,
            page: urlPage,
            limit: PAGE_LIMIT,
            sort: filtersFromUrl.sort ?? 'newest',
          } satisfies NormalCVSearchParams);

    promise
      .then((res) => {
        if (cancelled) return;
        setItems(res.items as Array<NormalJobSearchItem | NormalCVSearchItem>);
        setTotal(res.total);
        setTotalPages(res.totalPages);
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
  }, [urlQ, urlType, urlPage, filtersFromUrl, shouldFetch]);

  const updateUrl = useCallback(
    (
      patch: {
        q?: string;
        type?: AnchorTypeV2;
        page?: number;
      } & Partial<V2SearchFilters>,
      resetPage = true
    ) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);

        if (patch.q !== undefined) {
          if (patch.q) next.set('q', patch.q);
          else next.delete('q');
        }
        if (patch.type !== undefined) next.set('type', patch.type);

        FILTER_KEYS.forEach((key) => {
          if (Object.prototype.hasOwnProperty.call(patch, key)) {
            const value = patch[key];
            if (value) next.set(key, value);
            else next.delete(key);
          }
        });

        if (patch.page !== undefined) {
          if (patch.page > 1) next.set('page', String(patch.page));
          else next.delete('page');
        } else if (resetPage) {
          next.delete('page');
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
      location: inputLocation || undefined,
    });
  };

  const handleToggleType = (next: AnchorTypeV2) => {
    if (next === urlType) return;
    updateUrl({ type: next });
  };

  const handleFiltersChange = (next: V2SearchFilters) => {
    updateUrl(next);
  };

  const handlePageChange = (page: number) => {
    updateUrl({ page }, false);
  };

  return (
    <div className="bg-[#F5F7FC] min-h-screen pb-20">
      <div className="bg-white border-b border-gray-100 sticky top-20 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
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

          <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                value={inputQ}
                onChange={(e) => setInputQ(e.target.value)}
                placeholder={
                  isJobMode
                    ? 'Tên việc, công ty, kỹ năng, ngành nghề...'
                    : 'Tên ứng viên, vị trí, kỹ năng, kinh nghiệm...'
                }
                className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-full text-[15px] placeholder-gray-400 focus:outline-none focus:bg-white focus:border-[#0A65CC] focus:ring-2 focus:ring-[#0A65CC]/20"
              />
            </div>
            <div className="md:w-64">
              <select
                value={inputLocation}
                onChange={(event) => setInputLocation(event.target.value)}
                className="w-full rounded-full border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700 focus:border-[#0A65CC] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/20"
                aria-label="Khu vực"
              >
                <option value="">Khu vực</option>
                {LOCATION_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              className="px-6 py-3 rounded-full bg-[#0A65CC] text-white font-semibold text-sm hover:bg-[#085bb8] transition-colors whitespace-nowrap"
            >
              Tìm kiếm
            </button>
          </form>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-3">
          <V2SearchFilterPanel
            mode={urlType}
            filters={filtersFromUrl}
            onChange={handleFiltersChange}
          />
          <div className="mt-4 px-4 py-3 bg-amber-50 border border-amber-100 rounded-lg text-xs text-amber-800">
            <p className="font-semibold mb-1 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" /> Tìm kiếm thông thường
            </p>
            <p className="opacity-80">
              Bộ lọc dùng dữ liệu hiện có trong PostgreSQL. Các trường chưa có cột riêng như
              lương hoặc availability được giữ trong UI/API để chuẩn bị cho schema mở rộng.
            </p>
          </div>
        </div>

        <main className="lg:col-span-9">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <h1 className="text-lg font-bold text-gray-900">
              {hasSearch ? (
                <>
                  Tìm thấy <span className="text-[#0A65CC] tabular-nums">{total}</span> kết quả
                  {urlQ.trim() ? (
                    <>
                      {' '}
                      cho "<span className="text-gray-700">{urlQ.trim()}</span>"
                    </>
                  ) : null}
                </>
              ) : isJobMode ? (
                'Việc làm công khai'
              ) : (
                'CV công khai'
              )}
            </h1>
          </div>

          {loading && <RunningSpinner />}

          {error && !loading && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {!loading && !error && shouldFetch && total === 0 && (
            <EmptyState
              type={urlType}
              isRecruiter={user?.role === 'employer' || user?.role === 'admin'}
            />
          )}

          {!loading && !error && total > 0 && (
            <>
              <ResultsList type={urlType} items={items} />
              <Pagination
                page={urlPage}
                totalPages={totalPages}
                onPageChange={handlePageChange}
              />
            </>
          )}

          {!loading && !error && !shouldFetch && (
            <div className="text-center py-16 text-gray-400">
              <Search className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p className="text-sm">
                Gõ từ khóa hoặc chọn bộ lọc rồi bấm{' '}
                <strong className="text-gray-600">Tìm kiếm</strong>.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

const RunningSpinner: React.FC = () => (
  <div className="flex flex-col items-center justify-center py-16 text-gray-500">
    <Loader2 className="w-8 h-8 animate-spin text-[#0A65CC] mb-3" />
    <p className="text-sm">Đang tìm kiếm...</p>
  </div>
);

const EmptyState: React.FC<{ type: AnchorTypeV2; isRecruiter?: boolean }> = ({
  type,
  isRecruiter = false,
}) => (
  <div className="text-center py-16 border-2 border-dashed border-gray-200 rounded-xl">
    <FileSearch className="w-12 h-12 mx-auto mb-3 text-gray-300" />
    <p className="text-sm font-medium text-gray-700 mb-1">
      {type === 'job' ? 'No published public jobs found.' : 'Không tìm thấy CV phù hợp.'}
    </p>
    <p className="text-xs text-gray-500">
      {type === 'job' && isRecruiter
        ? 'Draft/private jobs are not shown in public search. Publish the job to make it searchable.'
        : 'Thử từ khóa rộng hơn hoặc bỏ bớt bộ lọc.'}
    </p>
  </div>
);

interface ResultsListProps {
  type: AnchorTypeV2;
  items: Array<NormalJobSearchItem | NormalCVSearchItem>;
}

const ResultsList: React.FC<ResultsListProps> = ({ type, items }) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
    {items.map((it) => (
      <V2SearchResultCard
        key={`${type}-${type === 'job' ? (it as NormalJobSearchItem).job_id : (it as NormalCVSearchItem).cv_id}`}
        item={it}
        type={type}
      />
    ))}
  </div>
);

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({ page, totalPages, onPageChange }) => {
  if (totalPages <= 1) return null;
  return (
    <div className="mt-6 flex items-center justify-center gap-3">
      <button
        type="button"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
        className="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 disabled:cursor-not-allowed disabled:opacity-50 hover:border-[#0A65CC] hover:text-[#0A65CC]"
      >
        <ChevronLeft className="h-4 w-4" />
        Trước
      </button>
      <span className="text-sm font-semibold text-gray-600">
        Trang {page} / {totalPages}
      </span>
      <button
        type="button"
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
        className="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 disabled:cursor-not-allowed disabled:opacity-50 hover:border-[#0A65CC] hover:text-[#0A65CC]"
      >
        Sau
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
};

export default V2Search;
