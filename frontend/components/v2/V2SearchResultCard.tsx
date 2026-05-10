import React from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, MapPin, Award, ArrowUpRight } from 'lucide-react';
import type { CVSearchItem, JobSearchItem } from '../../types';
import {
  formatJobTypeV2,
  formatLocationV2,
  formatSeniorityV2,
} from './v2-format';

interface V2SearchResultCardProps {
  item: JobSearchItem | CVSearchItem;
  type: 'job' | 'cv';
  /** When true the card is rendered in a muted "low score" variant. */
  lowScore?: boolean;
}

const MAX_VISIBLE_SKILLS = 6;

const V2SearchResultCard: React.FC<V2SearchResultCardProps> = ({
  item,
  type,
  lowScore = false,
}) => {
  const id = type === 'job' ? (item as JobSearchItem).job_id : (item as CVSearchItem).cv_id;
  const targetUrl = type === 'job' ? `/v2/jobs/${id}` : `/v2/cvs/${id}`;
  const pct = Math.round(Math.max(0, Math.min(1, item.score)) * 100);

  const visibleSkills = item.skills.slice(0, MAX_VISIBLE_SKILLS);
  const hiddenCount = item.skills.length - visibleSkills.length;

  return (
    <Link
      to={targetUrl}
      className={`group block bg-white border rounded-xl shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 ${
        lowScore
          ? 'border-gray-100 opacity-70 hover:opacity-100'
          : 'border-gray-100'
      }`}
    >
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 text-xs text-gray-400 font-mono mb-1">
              <span className="uppercase tracking-wide">{type}</span>
              <span>·</span>
              <span>#{id}</span>
            </div>
            <h3 className="text-base font-semibold text-gray-900 group-hover:text-[#0A65CC] transition-colors line-clamp-2">
              {item.title}
            </h3>
          </div>

          {/* Score badge */}
          <div
            className={`flex-shrink-0 flex flex-col items-center justify-center px-3 py-2 rounded-lg ${
              lowScore
                ? 'bg-gray-50 text-gray-400'
                : 'bg-blue-50 text-[#0A65CC]'
            }`}
            aria-label={`Score ${pct}%`}
          >
            <span className="text-base font-bold tabular-nums leading-none">{pct}%</span>
            <span className="text-[9px] uppercase tracking-wide mt-0.5">match</span>
          </div>
        </div>

        {/* Enum chips */}
        <div className="mt-3 flex flex-wrap gap-1.5 text-xs">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-gray-50 text-gray-700 font-medium">
            <MapPin className="w-3 h-3" /> {formatLocationV2(item.location)}
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-gray-50 text-gray-700 font-medium">
            <Briefcase className="w-3 h-3" /> {formatJobTypeV2(item.job_type)}
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-gray-50 text-gray-700 font-medium">
            <Award className="w-3 h-3" /> {formatSeniorityV2(item.seniority)}
          </span>
        </div>

        {/* Skills */}
        {visibleSkills.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {visibleSkills.map((s) => (
              <span
                key={s}
                className="text-[11px] px-2 py-0.5 rounded bg-blue-50/60 text-[#0A65CC] font-medium"
              >
                {s}
              </span>
            ))}
            {hiddenCount > 0 && (
              <span className="text-[11px] px-2 py-0.5 rounded bg-gray-100 text-gray-500">
                +{hiddenCount} more
              </span>
            )}
          </div>
        )}

        {/* Footer hint */}
        <div className="mt-4 flex items-center justify-end text-xs text-gray-400 group-hover:text-[#0A65CC] transition-colors">
          <span>Xem chi tiết</span>
          <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
        </div>
      </div>
    </Link>
  );
};

export default V2SearchResultCard;
