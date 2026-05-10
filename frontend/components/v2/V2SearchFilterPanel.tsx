import React from 'react';
import { X, Filter as FilterIcon } from 'lucide-react';
import type {
  JobTypeV2,
  LocationV2,
  SeniorityV2,
} from '../../types';
import {
  JOB_TYPE_OPTIONS,
  LOCATION_OPTIONS,
  SENIORITY_OPTIONS,
} from './v2-format';

export interface V2SearchFilters {
  location?: LocationV2;
  job_type?: JobTypeV2;
  seniority?: SeniorityV2;
}

interface V2SearchFilterPanelProps {
  filters: V2SearchFilters;
  onChange: (next: V2SearchFilters) => void;
  /** When true, the panel hides the location group (e.g. when searching CVs
   *  where the home doesn't pre-fill location). Optional. */
  hideLocation?: boolean;
}

const Group: React.FC<{
  title: string;
  children: React.ReactNode;
}> = ({ title, children }) => (
  <div className="space-y-2">
    <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</h4>
    <div className="flex flex-wrap gap-1.5">{children}</div>
  </div>
);

const Chip: React.FC<{
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}> = ({ active, onClick, children }) => (
  <button
    type="button"
    onClick={onClick}
    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
      active
        ? 'bg-[#0A65CC] text-white shadow-sm'
        : 'bg-white border border-gray-200 text-gray-700 hover:border-[#0A65CC] hover:text-[#0A65CC]'
    }`}
  >
    {children}
  </button>
);

const V2SearchFilterPanel: React.FC<V2SearchFilterPanelProps> = ({
  filters,
  onChange,
  hideLocation = false,
}) => {
  const hasAny =
    Boolean(filters.location) || Boolean(filters.job_type) || Boolean(filters.seniority);

  const setKey = <K extends keyof V2SearchFilters>(
    key: K,
    value: V2SearchFilters[K] | undefined
  ) => {
    // Toggle: clicking the active chip clears it.
    onChange({
      ...filters,
      [key]: filters[key] === value ? undefined : value,
    });
  };

  const clearAll = () => onChange({});

  return (
    <aside className="bg-white border border-gray-100 rounded-xl shadow-sm p-5 space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
          <FilterIcon className="w-4 h-4 text-[#0A65CC]" /> Bộ lọc
        </h3>
        {hasAny && (
          <button
            type="button"
            onClick={clearAll}
            className="text-xs text-gray-500 hover:text-red-500 inline-flex items-center gap-1"
          >
            <X className="w-3 h-3" /> Xóa tất cả
          </button>
        )}
      </div>

      {!hideLocation && (
        <Group title="Khu vực">
          {LOCATION_OPTIONS.map((opt) => (
            <Chip
              key={opt.value}
              active={filters.location === opt.value}
              onClick={() => setKey('location', opt.value)}
            >
              {opt.label}
            </Chip>
          ))}
        </Group>
      )}

      <Group title="Hình thức">
        {JOB_TYPE_OPTIONS.map((opt) => (
          <Chip
            key={opt.value}
            active={filters.job_type === opt.value}
            onClick={() => setKey('job_type', opt.value)}
          >
            {opt.label}
          </Chip>
        ))}
      </Group>

      <Group title="Cấp bậc">
        {SENIORITY_OPTIONS.map((opt) => (
          <Chip
            key={opt.value}
            active={filters.seniority === opt.value}
            onClick={() => setKey('seniority', opt.value)}
          >
            {opt.label}
          </Chip>
        ))}
      </Group>
    </aside>
  );
};

export default V2SearchFilterPanel;
