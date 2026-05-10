import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Award } from 'lucide-react';
import type { AnchorTypeV2, MatchItemV2 } from '../../types';
import V2ScoreBars from './V2ScoreBars';

interface V2MatchResultCardProps {
  match: MatchItemV2;
  anchorType: AnchorTypeV2;
  oppositeTitle?: string;
}

const clamp = (v: number) => Math.max(0, Math.min(1, v));

const V2MatchResultCard: React.FC<V2MatchResultCardProps> = ({
  match,
  anchorType,
  oppositeTitle,
}) => {
  const [open, setOpen] = useState(false);
  const oppositeId = anchorType === 'job' ? match.cv_id : match.job_id;
  const oppositeLabel = anchorType === 'job' ? 'CV' : 'Job';
  const finalPct = Math.round(clamp(match.final_score) * 100);

  // Pick rank badge color
  const rankBg =
    match.rank === 1
      ? 'bg-amber-400 text-white'
      : match.rank === 2
        ? 'bg-gray-300 text-gray-800'
        : match.rank === 3
          ? 'bg-orange-300 text-orange-900'
          : 'bg-gray-100 text-gray-600';

  return (
    <div className="bg-white border border-gray-100 rounded-xl shadow-sm hover:shadow-md transition-shadow">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div
            className={`flex-shrink-0 w-9 h-9 rounded-full font-bold flex items-center justify-center text-sm ${rankBg}`}
            aria-label={`Rank ${match.rank}`}
          >
            {match.rank}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="font-medium uppercase tracking-wide">{oppositeLabel}</span>
              <span className="font-mono">#{oppositeId}</span>
            </div>
            <p className="mt-0.5 text-sm font-semibold text-gray-900 truncate">
              {oppositeTitle ?? <span className="text-gray-400 italic">(loading title…)</span>}
            </p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Award className="w-3.5 h-3.5" />
              <span>final</span>
            </div>
            <div className="text-xl font-bold text-[#0A65CC] tabular-nums leading-none mt-1">
              {finalPct}%
            </div>
          </div>
        </div>

        {/* Final score bar */}
        <div className="mt-3 h-2 w-full bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#0A65CC] to-[#00B14F] transition-all duration-500"
            style={{ width: `${finalPct}%` }}
          />
        </div>

        {/* Sub-scores */}
        <div className="mt-4">
          <V2ScoreBars
            titleScore={match.title_score}
            skillsScore={match.skills_score}
            reqExpScore={match.req_exp_score}
            reqSummaryScore={match.req_summary_score}
          />
        </div>

        {/* Reasoning toggle */}
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="mt-4 w-full flex items-center justify-between text-xs font-medium text-gray-500 hover:text-[#0A65CC] transition-colors"
          aria-expanded={open}
        >
          <span>{open ? 'Ẩn lý do' : 'Xem lý do'}</span>
          {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        {open && (
          <div className="mt-2 p-3 bg-gray-50 rounded-lg text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">
            {match.reasoning || <span className="text-gray-400 italic">(không có lý do)</span>}
          </div>
        )}
      </div>
    </div>
  );
};

export default V2MatchResultCard;
