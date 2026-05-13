import React from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, MapPin, Award, ArrowUpRight } from 'lucide-react';
import type { NormalCVSearchItem, NormalJobSearchItem } from '../../types';
import {
  formatJobTypeV2,
  formatLocationV2,
  formatSeniorityV2,
} from './v2-format';

interface V2SearchResultCardProps {
  item: NormalJobSearchItem | NormalCVSearchItem;
  type: 'job' | 'cv';
}

const MAX_VISIBLE_SKILLS = 6;

const V2SearchResultCard: React.FC<V2SearchResultCardProps> = ({
  item,
  type,
}) => {
  const id = type === 'job' ? (item as NormalJobSearchItem).job_id : (item as NormalCVSearchItem).cv_id;
  const targetUrl = type === 'job' ? `/job/${id}` : `/cv/${id}`;

  const visibleSkills = item.skills.slice(0, MAX_VISIBLE_SKILLS);
  const hiddenCount = item.skills.length - visibleSkills.length;
  const formatLocation = (value: string) => {
    if (value === 'ha_noi' || value === 'tp_hcm' || value === 'da_nang') {
      return formatLocationV2(value);
    }
    return value;
  };
  const formatJobType = (value: string) => {
    if (value === 'remote' || value === 'fulltime' || value === 'parttime') {
      return formatJobTypeV2(value);
    }
    return value;
  };
  const formatSeniority = (value: string) => {
    if (
      value === 'intern' ||
      value === 'fresher' ||
      value === 'junior' ||
      value === 'mid' ||
      value === 'senior' ||
      value === 'lead'
    ) {
      return formatSeniorityV2(value);
    }
    return value;
  };

  return (
    <Link
      to={targetUrl}
      className="group block bg-white border border-gray-100 rounded-xl shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5"
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
        </div>

        {/* Enum chips */}
        <div className="mt-3 flex flex-wrap gap-1.5 text-xs">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-gray-50 text-gray-700 font-medium">
            <MapPin className="w-3 h-3" /> {formatLocation(item.location)}
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-gray-50 text-gray-700 font-medium">
            <Briefcase className="w-3 h-3" /> {formatJobType(item.job_type)}
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-gray-50 text-gray-700 font-medium">
            <Award className="w-3 h-3" /> {formatSeniority(item.seniority)}
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
