import React, { useEffect, useState } from 'react';
import {
  Briefcase,
  UserCircle,
  Search,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Sparkles,
  AlertCircle,
} from 'lucide-react';
import type {
  AnchorTypeV2,
  CVSearchItem,
  CVV2ListItem,
  JobSearchItem,
  JobV2ListItem,
} from '../../types';
import {
  listV2Cvs,
  listV2Jobs,
  searchV2Cvs,
  searchV2Jobs,
} from '../../src/api/v2';

const PAGE_SIZE = 10;
const SEARCH_TOP_K = 20;
const DEBOUNCE_MS = 300;

interface V2AnchorListProps {
  anchorType: AnchorTypeV2;
  selectedId: number | null;
  onAnchorTypeChange: (next: AnchorTypeV2) => void;
  onSelect: (id: number, type: AnchorTypeV2) => void;
}

interface BrowseSlice<T> {
  items: T[];
  total: number;
  offset: number;
  loading: boolean;
}

interface BrowseState {
  jobs: BrowseSlice<JobV2ListItem>;
  cvs: BrowseSlice<CVV2ListItem>;
}

interface SearchState {
  items: (JobSearchItem | CVSearchItem)[];
  loading: boolean;
  error: string | null;
}

const initialBrowse: BrowseState = {
  jobs: { items: [], total: 0, offset: 0, loading: false },
  cvs: { items: [], total: 0, offset: 0, loading: false },
};

const initialSearch: SearchState = {
  items: [],
  loading: false,
  error: null,
};

// ---------------------------------------------------------------------------
// Type guards & helpers
// ---------------------------------------------------------------------------

const itemId = (
  item: JobV2ListItem | CVV2ListItem | JobSearchItem | CVSearchItem
): number => ('job_id' in item ? item.job_id : item.cv_id);

const itemScore = (
  item: JobV2ListItem | CVV2ListItem | JobSearchItem | CVSearchItem
): number | null => ('score' in item ? item.score : null);

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const V2AnchorList: React.FC<V2AnchorListProps> = ({
  anchorType,
  selectedId,
  onAnchorTypeChange,
  onSelect,
}) => {
  // ---------------- Browse state (paginated catalog) ----------------
  const [browse, setBrowse] = useState<BrowseState>(initialBrowse);

  // ---------------- Search state ----------------
  const [searchInput, setSearchInput] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');
  const [searchState, setSearchState] = useState<SearchState>(initialSearch);

  const mode: 'browse' | 'search' = debouncedQ.trim() === '' ? 'browse' : 'search';

  // ---------------- Debounce input ----------------
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQ(searchInput), DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // ---------------- Browse fetch: jobs ----------------
  useEffect(() => {
    let cancelled = false;
    setBrowse((s) => ({ ...s, jobs: { ...s.jobs, loading: true } }));
    listV2Jobs({ limit: PAGE_SIZE, offset: browse.jobs.offset })
      .then((res) => {
        if (cancelled) return;
        setBrowse((s) => ({
          ...s,
          jobs: { items: res.items, total: res.total, offset: s.jobs.offset, loading: false },
        }));
      })
      .catch(() => {
        if (cancelled) return;
        setBrowse((s) => ({ ...s, jobs: { ...s.jobs, loading: false } }));
      });
    return () => {
      cancelled = true;
    };
  }, [browse.jobs.offset]);

  // ---------------- Browse fetch: cvs ----------------
  useEffect(() => {
    let cancelled = false;
    setBrowse((s) => ({ ...s, cvs: { ...s.cvs, loading: true } }));
    listV2Cvs({ limit: PAGE_SIZE, offset: browse.cvs.offset })
      .then((res) => {
        if (cancelled) return;
        setBrowse((s) => ({
          ...s,
          cvs: { items: res.items, total: res.total, offset: s.cvs.offset, loading: false },
        }));
      })
      .catch(() => {
        if (cancelled) return;
        setBrowse((s) => ({ ...s, cvs: { ...s.cvs, loading: false } }));
      });
    return () => {
      cancelled = true;
    };
  }, [browse.cvs.offset]);

  // ---------------- Search fetch (re-runs on debounced q OR anchor type) ----------------
  useEffect(() => {
    const q = debouncedQ.trim();
    if (q === '') {
      // Browse mode → clear any stale search state.
      setSearchState(initialSearch);
      return;
    }
    let cancelled = false;
    setSearchState((s) => ({ ...s, loading: true, error: null }));
    const fetcher = anchorType === 'job' ? searchV2Jobs : searchV2Cvs;
    fetcher({ q, top_k: SEARCH_TOP_K })
      .then((res) => {
        if (cancelled) return;
        setSearchState({ items: res.items, loading: false, error: null });
      })
      .catch((err) => {
        if (cancelled) return;
        setSearchState({
          items: [],
          loading: false,
          error: err instanceof Error ? err.message : 'Không tìm kiếm được, thử lại sau.',
        });
      });
    return () => {
      cancelled = true;
    };
  }, [debouncedQ, anchorType]);

  // ---------------- Derived view-model ----------------

  const browseSlice: BrowseSlice<JobV2ListItem | CVV2ListItem> =
    anchorType === 'job' ? browse.jobs : browse.cvs;
  const totalPages = Math.max(1, Math.ceil(browseSlice.total / PAGE_SIZE));
  const currentPage = Math.floor(browseSlice.offset / PAGE_SIZE) + 1;

  const displayItems: (JobV2ListItem | CVV2ListItem | JobSearchItem | CVSearchItem)[] =
    mode === 'search' ? searchState.items : browseSlice.items;
  const isLoading =
    mode === 'search' ? searchState.loading : browseSlice.loading;

  // ---------------- Handlers ----------------

  const handlePage = (delta: number) => {
    setBrowse((s) => {
      const key = anchorType === 'job' ? 'jobs' : 'cvs';
      const cur = s[key];
      const nextOffset = Math.max(
        0,
        Math.min(cur.offset + delta * PAGE_SIZE, (totalPages - 1) * PAGE_SIZE)
      );
      return { ...s, [key]: { ...cur, offset: nextOffset } };
    });
  };

  // ---------------- Render ----------------

  return (
    <div className="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden flex flex-col h-full">
      {/* Tabs */}
      <div className="flex border-b border-gray-100">
        <button
          type="button"
          onClick={() => onAnchorTypeChange('job')}
          className={`flex-1 px-4 py-3 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${
            anchorType === 'job'
              ? 'text-[#0A65CC] border-b-2 border-[#0A65CC] bg-blue-50/40'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <Briefcase className="w-4 h-4" /> By Job
        </button>
        <button
          type="button"
          onClick={() => onAnchorTypeChange('cv')}
          className={`flex-1 px-4 py-3 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${
            anchorType === 'cv'
              ? 'text-[#00B14F] border-b-2 border-[#00B14F] bg-green-50/40'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <UserCircle className="w-4 h-4" /> By CV
        </button>
      </div>

      {/* Search input */}
      <div className="p-3 border-b border-gray-100">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder={`Tìm theo tiêu đề / skill (${anchorType === 'job' ? 'jobs' : 'CVs'})…`}
            className="w-full pl-9 pr-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-[#0A65CC]/20 focus:border-[#0A65CC]/30"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-12 text-gray-400">
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
            <span className="text-sm">
              {mode === 'search' ? 'Đang tìm…' : 'Đang tải…'}
            </span>
          </div>
        ) : mode === 'search' && searchState.error ? (
          <div className="flex items-start gap-2 m-3 p-3 bg-red-50 border border-red-100 rounded-lg text-xs text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{searchState.error}</span>
          </div>
        ) : displayItems.length === 0 ? (
          <div className="text-center text-sm text-gray-400 py-12 px-4">
            {mode === 'search'
              ? `Không tìm thấy ${anchorType === 'job' ? 'job' : 'CV'} nào khớp với "${debouncedQ.trim()}".`
              : 'Không có kết quả.'}
          </div>
        ) : (
          <ul className="divide-y divide-gray-50">
            {displayItems.map((item) => {
              const id = itemId(item);
              const score = itemScore(item);
              const isSelected = selectedId === id;
              return (
                <li key={id}>
                  <button
                    type="button"
                    onClick={() => onSelect(id, anchorType)}
                    className={`w-full text-left px-4 py-3 transition-colors ${
                      isSelected
                        ? 'bg-blue-50 border-l-4 border-[#0A65CC]'
                        : 'hover:bg-gray-50 border-l-4 border-transparent'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs text-gray-400 font-mono">#{id}</span>
                      <div className="flex items-center gap-1.5">
                        {score !== null && (
                          <span
                            className="text-[10px] font-bold tabular-nums px-1.5 py-0.5 rounded bg-blue-50 text-[#0A65CC]"
                            aria-label={`Score ${Math.round(score * 100)}%`}
                          >
                            {Math.round(score * 100)}%
                          </span>
                        )}
                        <span className="text-[10px] uppercase tracking-wide text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                          {item.seniority}
                        </span>
                      </div>
                    </div>
                    <p
                      className={`mt-1 text-sm font-semibold line-clamp-2 ${
                        isSelected ? 'text-[#0A65CC]' : 'text-gray-900'
                      }`}
                    >
                      {item.title}
                    </p>
                    <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500">
                      <span>{item.location}</span>
                      <span>·</span>
                      <span>{item.job_type}</span>
                    </div>
                    {item.skills.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {item.skills.slice(0, 4).map((s) => (
                          <span
                            key={s}
                            className="text-[10px] px-1.5 py-0.5 bg-gray-100 rounded text-gray-600"
                          >
                            {s}
                          </span>
                        ))}
                        {item.skills.length > 4 && (
                          <span className="text-[10px] text-gray-400">
                            +{item.skills.length - 4}
                          </span>
                        )}
                      </div>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* Footer — paginate browse, count for search */}
      <div className="flex items-center justify-between px-3 py-2 border-t border-gray-100 text-xs text-gray-500">
        {mode === 'search' ? (
          <span className="flex items-center gap-1.5">
            <Sparkles className="w-3 h-3 text-[#0A65CC]" />
            {searchState.loading
              ? '…'
              : `${searchState.items.length} kết quả · semantic search`}
          </span>
        ) : (
          <>
            <span>
              Trang {currentPage}/{totalPages} · {browseSlice.total}{' '}
              {anchorType === 'job' ? 'jobs' : 'CVs'}
            </span>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => handlePage(-1)}
                disabled={currentPage <= 1 || browseSlice.loading}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
                aria-label="Previous page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => handlePage(1)}
                disabled={currentPage >= totalPages || browseSlice.loading}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
                aria-label="Next page"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default V2AnchorList;
