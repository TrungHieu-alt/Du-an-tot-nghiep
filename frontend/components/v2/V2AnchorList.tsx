import React, { useEffect, useMemo, useState } from 'react';
import { Briefcase, UserCircle, Search, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import type {
  AnchorTypeV2,
  CVV2ListItem,
  JobV2ListItem,
} from '../../types';
import { listV2Cvs, listV2Jobs } from '../../src/api/v2';

const PAGE_SIZE = 10;

interface V2AnchorListProps {
  anchorType: AnchorTypeV2;
  selectedId: number | null;
  onAnchorTypeChange: (next: AnchorTypeV2) => void;
  onSelect: (id: number, type: AnchorTypeV2) => void;
}

interface ListState {
  jobs: { items: JobV2ListItem[]; total: number; offset: number; loading: boolean };
  cvs: { items: CVV2ListItem[]; total: number; offset: number; loading: boolean };
}

const initialState: ListState = {
  jobs: { items: [], total: 0, offset: 0, loading: false },
  cvs: { items: [], total: 0, offset: 0, loading: false },
};

const V2AnchorList: React.FC<V2AnchorListProps> = ({
  anchorType,
  selectedId,
  onAnchorTypeChange,
  onSelect,
}) => {
  const [state, setState] = useState<ListState>(initialState);
  const [search, setSearch] = useState('');

  // Fetch jobs
  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, jobs: { ...s.jobs, loading: true } }));
    listV2Jobs({ limit: PAGE_SIZE, offset: state.jobs.offset })
      .then((res) => {
        if (cancelled) return;
        setState((s) => ({
          ...s,
          jobs: { items: res.items, total: res.total, offset: s.jobs.offset, loading: false },
        }));
      })
      .catch(() => {
        if (cancelled) return;
        setState((s) => ({ ...s, jobs: { ...s.jobs, loading: false } }));
      });
    return () => {
      cancelled = true;
    };
  }, [state.jobs.offset]);

  // Fetch cvs
  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, cvs: { ...s.cvs, loading: true } }));
    listV2Cvs({ limit: PAGE_SIZE, offset: state.cvs.offset })
      .then((res) => {
        if (cancelled) return;
        setState((s) => ({
          ...s,
          cvs: { items: res.items, total: res.total, offset: s.cvs.offset, loading: false },
        }));
      })
      .catch(() => {
        if (cancelled) return;
        setState((s) => ({ ...s, cvs: { ...s.cvs, loading: false } }));
      });
    return () => {
      cancelled = true;
    };
  }, [state.cvs.offset]);

  const current = anchorType === 'job' ? state.jobs : state.cvs;
  const totalPages = Math.max(1, Math.ceil(current.total / PAGE_SIZE));
  const currentPage = Math.floor(current.offset / PAGE_SIZE) + 1;

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return current.items;
    return current.items.filter((item) => {
      const title = item.title.toLowerCase();
      const skills = item.skills.join(' ').toLowerCase();
      return title.includes(q) || skills.includes(q);
    });
  }, [search, current.items]);

  const handlePage = (delta: number) => {
    setState((s) => {
      const key = anchorType === 'job' ? 'jobs' : 'cvs';
      const cur = s[key];
      const nextOffset = Math.max(0, Math.min(cur.offset + delta * PAGE_SIZE, (totalPages - 1) * PAGE_SIZE));
      return { ...s, [key]: { ...cur, offset: nextOffset } };
    });
  };

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

      {/* Search */}
      <div className="p-3 border-b border-gray-100">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Tìm theo tiêu đề / skill (${anchorType === 'job' ? 'jobs' : 'CVs'})…`}
            className="w-full pl-9 pr-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-[#0A65CC]/20 focus:border-[#0A65CC]/30"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {current.loading ? (
          <div className="flex items-center justify-center py-12 text-gray-400">
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
            <span className="text-sm">Đang tải…</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center text-sm text-gray-400 py-12">
            Không có kết quả.
          </div>
        ) : (
          <ul className="divide-y divide-gray-50">
            {filtered.map((item) => {
              const id = anchorType === 'job' ? (item as JobV2ListItem).job_id : (item as CVV2ListItem).cv_id;
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
                      <span className="text-[10px] uppercase tracking-wide text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                        {item.seniority}
                      </span>
                    </div>
                    <p className={`mt-1 text-sm font-semibold line-clamp-2 ${isSelected ? 'text-[#0A65CC]' : 'text-gray-900'}`}>
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
                          <span key={s} className="text-[10px] px-1.5 py-0.5 bg-gray-100 rounded text-gray-600">
                            {s}
                          </span>
                        ))}
                        {item.skills.length > 4 && (
                          <span className="text-[10px] text-gray-400">+{item.skills.length - 4}</span>
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

      {/* Pagination */}
      <div className="flex items-center justify-between px-3 py-2 border-t border-gray-100 text-xs text-gray-500">
        <span>
          Trang {currentPage}/{totalPages} · {current.total} {anchorType === 'job' ? 'jobs' : 'CVs'}
        </span>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => handlePage(-1)}
            disabled={currentPage <= 1 || current.loading}
            className="p-1 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Previous page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => handlePage(1)}
            disabled={currentPage >= totalPages || current.loading}
            className="p-1 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Next page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default V2AnchorList;
