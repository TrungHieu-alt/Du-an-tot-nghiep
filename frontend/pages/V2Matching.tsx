import React, { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Sparkles, Info, AlertCircle, FileSearch, Clock, Filter as FilterIcon } from 'lucide-react';
import type {
  AnchorTypeV2,
  CVV2Detail,
  CVV2ListItem,
  JobV2Detail,
  JobV2ListItem,
  RunMatchingV2Response,
} from '../types';
import {
  getV2Cv,
  getV2Job,
  listV2Cvs,
  listV2Jobs,
  runV2MatchForCv,
  runV2MatchForJob,
} from '../src/api/v2';
import V2AnchorList from '../components/v2/V2AnchorList';
import V2MatchControls from '../components/v2/V2MatchControls';
import V2MatchResultCard from '../components/v2/V2MatchResultCard';

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

interface PageState {
  anchorType: AnchorTypeV2;
  selectedId: number | null;
  topK: number;
  minScore: number;
  isRunning: boolean;
  result: RunMatchingV2Response | null;
  runError: string | null;
}

type Action =
  | { type: 'SET_ANCHOR_TYPE'; payload: AnchorTypeV2 }
  | { type: 'SELECT'; payload: number }
  | { type: 'SET_TOP_K'; payload: number }
  | { type: 'SET_MIN_SCORE'; payload: number }
  | { type: 'RUN_START' }
  | { type: 'RUN_SUCCESS'; payload: RunMatchingV2Response }
  | { type: 'RUN_ERROR'; payload: string };

const initialState: PageState = {
  anchorType: 'job',
  selectedId: null,
  topK: 10,
  minScore: 0.7,
  isRunning: false,
  result: null,
  runError: null,
};

const reducer = (s: PageState, a: Action): PageState => {
  switch (a.type) {
    case 'SET_ANCHOR_TYPE':
      // Clear selection + result when switching tab
      return { ...s, anchorType: a.payload, selectedId: null, result: null, runError: null };
    case 'SELECT':
      return { ...s, selectedId: a.payload, result: null, runError: null };
    case 'SET_TOP_K':
      return { ...s, topK: a.payload };
    case 'SET_MIN_SCORE':
      return { ...s, minScore: a.payload };
    case 'RUN_START':
      return { ...s, isRunning: true, runError: null };
    case 'RUN_SUCCESS':
      return { ...s, isRunning: false, result: a.payload, runError: null };
    case 'RUN_ERROR':
      return { ...s, isRunning: false, runError: a.payload };
    default:
      return s;
  }
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const errorToString = (err: unknown): string => {
  if (err instanceof Error) return err.message;
  if (typeof err === 'string') return err;
  return 'Đã có lỗi xảy ra. Vui lòng thử lại.';
};

const SENIORITY_ORDER: Record<string, number> = {
  intern: 0, fresher: 1, junior: 2, mid: 3, senior: 4, lead: 5,
};
const formatSeniority = (s: string) => s.toUpperCase();

// Strict URL param parsers — reject malformed deep-links rather than guess.
const parseAnchorParam = (raw: string | null): AnchorTypeV2 | null =>
  raw === 'job' || raw === 'cv' ? raw : null;

const parseIdParam = (raw: string | null): number | null => {
  if (!raw) return null;
  const n = Number(raw);
  if (!Number.isFinite(n) || !Number.isInteger(n) || n <= 0) return null;
  return n;
};

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const V2Matching: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [state, dispatch] = useReducer(reducer, initialState);
  const { anchorType, selectedId, topK, minScore, isRunning, result, runError } = state;

  // ---------------- Deep-link: hydrate state from URL on mount ----------------
  //
  // Reads ?anchor=job|cv&id=<int>. Invalid combinations (missing/non-positive
  // id, unknown anchor) are silently ignored — page falls back to default state.
  // We dispatch only the deltas needed; SET_ANCHOR_TYPE clears selection so we
  // run it BEFORE SELECT to avoid wiping a freshly hydrated id.
  const hydratedRef = useRef(false);
  useEffect(() => {
    if (hydratedRef.current) return;
    hydratedRef.current = true;

    const anchor = parseAnchorParam(searchParams.get('anchor'));
    const id = parseIdParam(searchParams.get('id'));
    if (anchor === null || id === null) return;

    if (anchor !== state.anchorType) {
      dispatch({ type: 'SET_ANCHOR_TYPE', payload: anchor });
    }
    dispatch({ type: 'SELECT', payload: id });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---------------- State → URL sync ----------------
  //
  // After hydration, mirror anchorType/selectedId back into URL using replace
  // (so the address bar stays canonical for share/bookmark, without polluting
  // browser history). We compare strings to skip no-op writes that would
  // otherwise re-render router consumers.
  useEffect(() => {
    if (!hydratedRef.current) return;
    const next = new URLSearchParams(searchParams);
    next.set('anchor', anchorType);
    if (selectedId !== null) next.set('id', String(selectedId));
    else next.delete('id');
    if (next.toString() !== searchParams.toString()) {
      setSearchParams(next, { replace: true });
    }
  }, [anchorType, selectedId, searchParams, setSearchParams]);

  // Anchor detail (memoized fetch by selectedId+type)
  const [anchorDetail, setAnchorDetail] = useState<JobV2Detail | CVV2Detail | null>(null);
  const [anchorLoading, setAnchorLoading] = useState(false);

  useEffect(() => {
    if (selectedId === null) {
      setAnchorDetail(null);
      return;
    }
    let cancelled = false;
    setAnchorLoading(true);
    const promise = anchorType === 'job' ? getV2Job(selectedId) : getV2Cv(selectedId);
    promise
      .then((d) => {
        if (cancelled) return;
        setAnchorDetail(d);
        setAnchorLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setAnchorDetail(null);
        setAnchorLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId, anchorType]);

  // Opposite-side title cache for results display.
  // When anchor is a job, we need CV titles; vice versa.
  const [oppositeTitles, setOppositeTitles] = useState<Map<number, string>>(new Map());

  useEffect(() => {
    if (!result || result.matches.length === 0) return;
    let cancelled = false;
    const fetcher = anchorType === 'job'
      ? () => listV2Cvs({ limit: 200, offset: 0 }).then((r) => r.items.map((i: CVV2ListItem) => [i.cv_id, i.title] as const))
      : () => listV2Jobs({ limit: 200, offset: 0 }).then((r) => r.items.map((i: JobV2ListItem) => [i.job_id, i.title] as const));
    fetcher()
      .then((pairs) => {
        if (cancelled) return;
        setOppositeTitles(new Map(pairs));
      })
      .catch(() => {
        // global toast via axios interceptor
      });
    return () => {
      cancelled = true;
    };
  }, [result, anchorType]);

  // Handlers
  const handleAnchorTypeChange = useCallback((next: AnchorTypeV2) => {
    dispatch({ type: 'SET_ANCHOR_TYPE', payload: next });
  }, []);
  const handleSelect = useCallback((id: number) => {
    dispatch({ type: 'SELECT', payload: id });
  }, []);
  const handleTopK = useCallback((n: number) => dispatch({ type: 'SET_TOP_K', payload: n }), []);
  const handleMinScore = useCallback((n: number) => dispatch({ type: 'SET_MIN_SCORE', payload: n }), []);

  const handleRun = useCallback(async () => {
    if (selectedId === null) return;
    dispatch({ type: 'RUN_START' });
    try {
      const body = { top_k: topK, min_score: minScore };
      const res = anchorType === 'job'
        ? await runV2MatchForJob(selectedId, body)
        : await runV2MatchForCv(selectedId, body);
      dispatch({ type: 'RUN_SUCCESS', payload: res });
    } catch (err) {
      dispatch({ type: 'RUN_ERROR', payload: errorToString(err) });
    }
  }, [anchorType, selectedId, topK, minScore]);

  const isJobAnchor = anchorType === 'job';
  const detailSkills = anchorDetail?.skills ?? [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Page header */}
      <div className="mb-6 flex items-start justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#0A65CC]" />
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">
              V2 Matching
            </h1>
            <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide rounded-full bg-amber-100 text-amber-700">
              prototype · beta
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Postgres + pgvector pipeline. Sync, no persistence. Anchor a job or a CV, tune top_k / min_score, run.
          </p>
        </div>
      </div>

      {/* Three-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 min-h-[calc(100vh-220px)]">
        {/* Left — anchor list */}
        <div className="lg:col-span-3 min-h-[500px]">
          <V2AnchorList
            anchorType={anchorType}
            selectedId={selectedId}
            onAnchorTypeChange={handleAnchorTypeChange}
            onSelect={handleSelect}
          />
        </div>

        {/* Center — preview + controls */}
        <div className="lg:col-span-4">
          <div className="bg-white border border-gray-100 rounded-xl shadow-sm p-5 space-y-5 h-full">
            <div>
              <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2">
                <Info className="w-4 h-4" /> Anchor preview
              </h2>
              {selectedId === null ? (
                <div className="mt-4 text-sm text-gray-400 py-10 text-center border-2 border-dashed border-gray-200 rounded-lg">
                  Chọn một {isJobAnchor ? 'Job' : 'CV'} ở cột trái để bắt đầu.
                </div>
              ) : anchorLoading || !anchorDetail ? (
                <div className="mt-4 text-sm text-gray-400 py-10 text-center">
                  Đang tải chi tiết…
                </div>
              ) : (
                <div className="mt-3 space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs text-gray-400 font-mono">
                      #{isJobAnchor ? (anchorDetail as JobV2Detail).job_id : (anchorDetail as CVV2Detail).cv_id}
                    </span>
                    <span className="text-[10px] uppercase tracking-wide text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                      {formatSeniority(anchorDetail.seniority)}
                    </span>
                  </div>
                  <p className="text-base font-semibold text-gray-900">{anchorDetail.title}</p>
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-md font-medium">
                      📍 {anchorDetail.location}
                    </span>
                    <span className="px-2 py-1 bg-green-50 text-green-700 rounded-md font-medium">
                      {anchorDetail.job_type}
                    </span>
                    <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded-md font-medium">
                      🎓 {anchorDetail.education}
                    </span>
                  </div>
                  {detailSkills.length > 0 && (
                    <div>
                      <p className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">Skills</p>
                      <div className="flex flex-wrap gap-1.5">
                        {detailSkills.map((s) => (
                          <span key={s} className="text-xs px-2 py-0.5 bg-gray-100 rounded text-gray-700">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4 flex items-center gap-2">
                <FilterIcon className="w-4 h-4" /> Match controls
              </h2>
              <V2MatchControls
                topK={topK}
                minScore={minScore}
                isRunning={isRunning}
                disabled={selectedId === null}
                onTopKChange={handleTopK}
                onMinScoreChange={handleMinScore}
                onRun={handleRun}
              />
              {runError && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2 text-xs text-red-700">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{runError}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right — results */}
        <div className="lg:col-span-5">
          <div className="bg-white border border-gray-100 rounded-xl shadow-sm h-full flex flex-col">
            {/* Header */}
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#00B14F]" /> Results
              </h2>
              {result && (
                <span className="text-xs text-gray-500">
                  Anchor: <span className="font-mono">#{result.anchor_id}</span>
                </span>
              )}
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-5">
              {!result && !isRunning && (
                <EmptyResults selectedId={selectedId} />
              )}

              {isRunning && <RunningSpinner />}

              {result && !isRunning && (
                <ResultsBody
                  result={result}
                  anchorType={anchorType}
                  oppositeTitles={oppositeTitles}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Sub-components (kept in-file; total lines under 300)
// ---------------------------------------------------------------------------

const EmptyResults: React.FC<{ selectedId: number | null }> = ({ selectedId }) => (
  <div className="text-center py-16 text-gray-400">
    <FileSearch className="w-12 h-12 mx-auto mb-3 opacity-40" />
    <p className="text-sm">
      {selectedId === null
        ? 'Chọn anchor và bấm Run để xem kết quả.'
        : 'Sẵn sàng. Bấm Run Matching V2 để chạy.'}
    </p>
  </div>
);

const RunningSpinner: React.FC = () => (
  <div className="flex flex-col items-center justify-center py-16 text-gray-500">
    <div className="relative">
      <div className="w-12 h-12 rounded-full border-4 border-blue-100 border-t-[#0A65CC] animate-spin" />
    </div>
    <p className="mt-4 text-sm">Đang chạy matching…</p>
  </div>
);

const StatPill: React.FC<{ label: string; value: string | number; accent?: string }> = ({
  label, value, accent,
}) => (
  <div className="px-3 py-2 bg-gray-50 rounded-lg border border-gray-100">
    <p className="text-[10px] uppercase tracking-wide text-gray-500">{label}</p>
    <p className={`mt-0.5 text-sm font-bold tabular-nums ${accent ?? 'text-gray-900'}`}>{value}</p>
  </div>
);

interface ResultsBodyProps {
  result: RunMatchingV2Response;
  anchorType: AnchorTypeV2;
  oppositeTitles: Map<number, string>;
}

const ResultsBody: React.FC<ResultsBodyProps> = ({ result, anchorType, oppositeTitles }) => {
  return (
    <div className="space-y-5">
      {/* Stats banner */}
      <div className="grid grid-cols-3 gap-2">
        <StatPill label="Candidates" value={result.total_candidates} />
        <StatPill label="After filter" value={result.total_after_filter} accent="text-amber-600" />
        <StatPill label="Returned" value={result.total_returned} accent="text-[#00B14F]" />
      </div>

      {/* Runtime breakdown */}
      <div className="px-3 py-2 bg-blue-50/60 border border-blue-100 rounded-lg flex items-center gap-3 flex-wrap text-xs text-gray-600">
        <Clock className="w-3.5 h-3.5 text-[#0A65CC]" />
        <span>total <strong className="text-gray-900 tabular-nums">{result.runtime_ms_total}ms</strong></span>
        <span>· filter <span className="tabular-nums">{result.runtime_ms_filter}ms</span></span>
        <span>· scoring <span className="tabular-nums">{result.runtime_ms_scoring}ms</span></span>
        <span>· sort <span className="tabular-nums">{result.runtime_ms_sort}ms</span></span>
      </div>

      {/* List of matches */}
      {result.total_returned === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-xl">
          <FileSearch className="w-10 h-10 mx-auto mb-2 text-gray-300" />
          <p className="text-sm font-medium text-gray-600">No matches above min_score</p>
          <p className="mt-1 text-xs text-gray-400">
            Thử giảm <code>min_score</code> hoặc đổi anchor.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {result.matches.map((m) => {
            const oppositeId = anchorType === 'job' ? m.cv_id : m.job_id;
            return (
              <V2MatchResultCard
                key={`${m.rank}-${m.cv_id}-${m.job_id}`}
                match={m}
                anchorType={anchorType}
                oppositeTitle={oppositeTitles.get(oppositeId)}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};

export default V2Matching;
