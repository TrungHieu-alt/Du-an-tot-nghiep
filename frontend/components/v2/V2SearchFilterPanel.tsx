import React, { useEffect, useMemo, useState } from 'react';
import { Check, Filter as FilterIcon, Search, X } from 'lucide-react';
import {
  CV_STATUS_OPTIONS,
  EDUCATION_LEVEL_OPTIONS,
  EMPLOYMENT_TYPE_OPTIONS,
  INDUSTRY_OPTIONS as NORMAL_INDUSTRY_OPTIONS,
  LANGUAGE_LEVEL_OPTIONS,
  OCCUPATION_GROUP_OPTIONS,
  REMOTE_TYPE_OPTIONS,
  SENIORITY_OPTIONS,
  occupationOptionsForIndustry,
  optionLabel,
} from '../../src/reference/normalEnums';

export type V2SearchMode = 'job' | 'cv';

export interface V2SearchFilters {
  location?: string;
  city?: string;
  country?: string;
  industry?: string;
  occupationGroup?: string;
  employmentType?: string;
  experienceLevel?: string;
  careerLevel?: string;
  salaryRange?: string;
  educationLevel?: string;
  educationMajor?: string;
  workingModel?: string;
  remoteType?: string;
  sort?: string;
  skills?: string;
  toolsAndTechnologies?: string;
  domainKnowledge?: string;
  yearsOfExperience?: string;
  yearsOfExperienceMin?: string;
  yearsOfExperienceMax?: string;
  availability?: string;
  certificationName?: string;
  languageName?: string;
  languageLevel?: string;
  status?: string;
  tags?: string;
}

interface FilterOption {
  value: string;
  label: string;
  industry?: string;
}

interface V2SearchFilterPanelProps {
  mode: V2SearchMode;
  keyword: string;
  filters: V2SearchFilters;
  onApply: (keyword: string, next: V2SearchFilters) => void;
  onClear: () => void;
}

export const INDUSTRY_OPTIONS: FilterOption[] = NORMAL_INDUSTRY_OPTIONS;

const EMPLOYMENT_OPTIONS: FilterOption[] = EMPLOYMENT_TYPE_OPTIONS;
const SENIORITY_FILTER_OPTIONS: FilterOption[] = SENIORITY_OPTIONS;
const EDUCATION_OPTIONS: FilterOption[] = EDUCATION_LEVEL_OPTIONS;
const WORKING_MODEL_OPTIONS: FilterOption[] = REMOTE_TYPE_OPTIONS;
const LANGUAGE_LEVEL_FILTER_OPTIONS: FilterOption[] = LANGUAGE_LEVEL_OPTIONS;
const STATUS_OPTIONS: FilterOption[] = CV_STATUS_OPTIONS;

const SALARY_OPTIONS: FilterOption[] = [
  { value: 'under_10m', label: 'Under 10M' },
  { value: '10_20m', label: '10M - 20M' },
  { value: '20_30m', label: '20M - 30M' },
  { value: '30_50m', label: '30M - 50M' },
  { value: '50m_plus', label: '50M+' },
];

const JOB_SORT_OPTIONS: FilterOption[] = [
  { value: 'createdAt_desc', label: 'Newest' },
  { value: 'createdAt_asc', label: 'Oldest' },
  { value: 'updatedAt_desc', label: 'Recently updated' },
  { value: 'updatedAt_asc', label: 'Least recently updated' },
  { value: 'salary_desc', label: 'Salary high to low' },
  { value: 'salary_asc', label: 'Salary low to high' },
  { value: 'views_desc', label: 'Most viewed' },
  { value: 'applicationsCount_desc', label: 'Most applications' },
  { value: 'applicationDeadline_asc', label: 'Deadline soonest' },
  { value: 'applicationDeadline_desc', label: 'Deadline latest' },
];

const CV_SORT_OPTIONS: FilterOption[] = [
  { value: 'createdAt_desc', label: 'Newest' },
  { value: 'createdAt_asc', label: 'Oldest' },
  { value: 'updatedAt_desc', label: 'Recently updated' },
  { value: 'updatedAt_asc', label: 'Least recently updated' },
  { value: 'yearsOfExperience_desc', label: 'Most experienced' },
  { value: 'yearsOfExperience_asc', label: 'Least experienced' },
  { value: 'fullname_asc', label: 'Name A-Z' },
  { value: 'fullname_desc', label: 'Name Z-A' },
];

export const splitFilterValues = (value?: string): string[] =>
  (value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

const joinFilterValues = (values: string[]): string | undefined => {
  const unique = Array.from(new Set(values.filter(Boolean)));
  return unique.length > 0 ? unique.join(',') : undefined;
};

const toggleValue = (current: string | undefined, value: string): string | undefined => {
  const values = splitFilterValues(current);
  const next = values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
  return joinFilterValues(next);
};

const hasAnyFilters = (keyword: string, filters: V2SearchFilters): boolean =>
  Boolean(keyword.trim()) || Object.values(filters).some((value) => Boolean(value));

const fieldIdFromLabel = (label: string): string =>
  `normal-filter-${label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')}`;

const Section: React.FC<{
  title: string;
  description?: string;
  children: React.ReactNode;
}> = ({ title, description, children }) => (
  <section className="rounded-xl border border-gray-100 bg-gray-50/60 p-4">
    <div className="mb-3">
      <h4 className="text-sm font-bold text-gray-900">{title}</h4>
      {description ? <p className="mt-1 text-xs text-gray-500">{description}</p> : null}
    </div>
    <div className="space-y-3">{children}</div>
  </section>
);

const Field: React.FC<{
  id: string;
  label: string;
  children: React.ReactNode;
  helper?: string;
  helperId?: string;
}> = ({ id, label, children, helper, helperId }) => (
  <div className="block">
    <label htmlFor={id} className="mb-1 block text-xs font-semibold text-gray-700">
      {label}
    </label>
    {children}
    {helper ? (
      <span id={helperId} className="mt-1 block text-[11px] leading-4 text-gray-500">
        {helper}
      </span>
    ) : null}
  </div>
);

const inputClass =
  'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:border-[#0A65CC] focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/15';

const TextInput: React.FC<{
  id?: string;
  label: string;
  value?: string;
  placeholder?: string;
  helper?: string;
  type?: string;
  min?: number;
  onChange: (value?: string) => void;
}> = ({ id, label, value, placeholder, helper, type = 'text', min, onChange }) => {
  const inputId = id ?? fieldIdFromLabel(label);
  const helperId = helper ? `${inputId}-helper` : undefined;
  return (
    <Field id={inputId} label={label} helper={helper} helperId={helperId}>
      <input
        id={inputId}
        type={type}
        min={min}
        value={value ?? ''}
        placeholder={placeholder}
        aria-describedby={helperId}
        onChange={(event) => onChange(event.target.value || undefined)}
        className={inputClass}
      />
    </Field>
  );
};

const SelectInput: React.FC<{
  id?: string;
  label: string;
  value?: string;
  options: FilterOption[];
  placeholder?: string;
  helper?: string;
  disabled?: boolean;
  onChange: (value?: string) => void;
}> = ({ id, label, value, options, placeholder = 'Any', helper, disabled, onChange }) => {
  const selectId = id ?? fieldIdFromLabel(label);
  const helperId = helper ? `${selectId}-helper` : undefined;
  return (
    <Field id={selectId} label={label} helper={helper} helperId={helperId}>
      <select
        id={selectId}
        value={value ?? ''}
        disabled={disabled}
        aria-describedby={helperId}
        onChange={(event) => onChange(event.target.value || undefined)}
        className={`${inputClass} disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400`}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </Field>
  );
};

const MultiChipField: React.FC<{
  label: string;
  value?: string;
  options: FilterOption[];
  helper?: string;
  onChange: (value?: string) => void;
}> = ({ label, value, options, helper, onChange }) => {
  const selected = splitFilterValues(value);
  const groupId = fieldIdFromLabel(label);
  const helperId = helper ? `${groupId}-helper` : undefined;
  return (
    <fieldset aria-describedby={helperId}>
      <legend className="mb-1 block text-xs font-semibold text-gray-700">{label}</legend>
      <div className="flex flex-wrap gap-1.5">
        {options.map((option) => {
          const active = selected.includes(option.value);
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => onChange(toggleValue(value, option.value))}
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
                active
                  ? 'bg-[#0A65CC] text-white shadow-sm'
                  : 'border border-gray-200 bg-white text-gray-700 hover:border-[#0A65CC] hover:text-[#0A65CC]'
              }`}
            >
              {active ? <Check className="h-3 w-3" /> : null}
              {option.label}
            </button>
          );
        })}
      </div>
      {helper ? (
        <span id={helperId} className="mt-1 block text-[11px] leading-4 text-gray-500">
          {helper}
        </span>
      ) : null}
    </fieldset>
  );
};

const ActiveChip: React.FC<{
  label: string;
  onRemove: () => void;
}> = ({ label, onRemove }) => (
  <button
    type="button"
    onClick={onRemove}
    className="inline-flex items-center gap-1 rounded-full border border-blue-100 bg-blue-50 px-2.5 py-1 text-xs font-semibold text-[#0A65CC] hover:border-blue-200 hover:bg-white"
  >
    {label}
    <X className="h-3 w-3" />
  </button>
);

const normalizeYears = (draft: V2SearchFilters): V2SearchFilters => {
  const min = draft.yearsOfExperienceMin ? Number(draft.yearsOfExperienceMin) : undefined;
  const max = draft.yearsOfExperienceMax ? Number(draft.yearsOfExperienceMax) : undefined;
  if (min !== undefined && min < 0) return { ...draft, yearsOfExperienceMin: '0' };
  if (max !== undefined && max < 0) return { ...draft, yearsOfExperienceMax: '0' };
  if (min !== undefined && max !== undefined && max < min) {
    return { ...draft, yearsOfExperienceMax: String(min) };
  }
  return draft;
};

const V2SearchFilterPanel: React.FC<V2SearchFilterPanelProps> = ({
  mode,
  keyword,
  filters,
  onApply,
  onClear,
}) => {
  const [draftKeyword, setDraftKeyword] = useState(keyword);
  const [draft, setDraft] = useState<V2SearchFilters>(filters);
  const isJob = mode === 'job';

  useEffect(() => setDraftKeyword(keyword), [keyword]);
  useEffect(() => setDraft(filters), [filters]);

  const occupationOptions = useMemo(() => {
    if (!draft.industry) return OCCUPATION_GROUP_OPTIONS;
    return occupationOptionsForIndustry(draft.industry);
  }, [draft.industry]);

  const setKey = <K extends keyof V2SearchFilters>(key: K, value: V2SearchFilters[K] | undefined) => {
    setDraft((current) => {
      const next = { ...current, [key]: value };
      if (key === 'industry') {
        const allowedOccupations = value ? occupationOptionsForIndustry(String(value)).map((option) => option.value) : [];
        if (next.occupationGroup && value && !allowedOccupations.includes(next.occupationGroup)) {
          next.occupationGroup = undefined;
        }
      }
      return next;
    });
  };

  const applyDraft = () => onApply(draftKeyword.trim(), normalizeYears(draft));
  const clearAll = () => {
    setDraftKeyword('');
    setDraft({});
    onClear();
  };

  const hasAny = hasAnyFilters(keyword, filters);

  const removeFilter = (key: keyof V2SearchFilters, value?: string) => {
    if (value) {
      onApply(keyword, { ...filters, [key]: joinFilterValues(splitFilterValues(filters[key]).filter((item) => item !== value)) });
      return;
    }
    onApply(keyword, { ...filters, [key]: undefined });
  };

  const activeChips = () => {
    const chips: React.ReactNode[] = [];
    if (keyword.trim()) {
      chips.push(<ActiveChip key="q" label={`Keyword: ${keyword.trim()}`} onRemove={() => onApply('', filters)} />);
    }
    const pushSingle = (key: keyof V2SearchFilters, label: string, options?: FilterOption[]) => {
      const value = filters[key];
      if (!value) return;
      const display = options ? optionLabel(options, value) : value;
      chips.push(<ActiveChip key={key} label={`${label}: ${display}`} onRemove={() => removeFilter(key)} />);
    };
    const pushMulti = (key: keyof V2SearchFilters, label: string, options?: FilterOption[]) => {
      splitFilterValues(filters[key]).forEach((value) => {
        const display = options ? optionLabel(options, value) : value;
        chips.push(
          <ActiveChip
            key={`${key}-${value}`}
            label={`${label}: ${display}`}
            onRemove={() => removeFilter(key, value)}
          />
        );
      });
    };

    pushSingle('industry', 'Industry', INDUSTRY_OPTIONS);
    pushSingle('occupationGroup', 'Occupation', OCCUPATION_GROUP_OPTIONS);
    pushMulti(isJob ? 'experienceLevel' : 'careerLevel', isJob ? 'Seniority' : 'Career level', SENIORITY_FILTER_OPTIONS);
    pushMulti('employmentType', 'Employment', EMPLOYMENT_OPTIONS);
    pushSingle('city', 'City');
    pushSingle('location', 'Location');
    pushSingle('country', 'Country');
    pushMulti('educationLevel', 'Education', EDUCATION_OPTIONS);
    pushSingle('educationMajor', 'Major');
    pushMulti('skills', 'Skill');
    pushMulti('toolsAndTechnologies', 'Tool');
    pushMulti('domainKnowledge', 'Domain');
    pushMulti('certificationName', 'Certification');
    pushSingle('languageName', 'Language');
    pushSingle('languageLevel', 'Language level', LANGUAGE_LEVEL_FILTER_OPTIONS);
    pushSingle('status', 'Status', STATUS_OPTIONS);
    pushMulti('tags', 'Tag');
    pushSingle('sort', 'Sort', isJob ? JOB_SORT_OPTIONS : CV_SORT_OPTIONS);
    return chips;
  };

  return (
    <aside className="space-y-4 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="flex items-center gap-2 text-base font-bold text-gray-900">
            <FilterIcon className="h-4 w-4 text-[#0A65CC]" /> Bộ lọc
          </h3>
          <p className="mt-1 text-xs text-gray-500">
            {isJob ? 'Normal job search filters.' : 'Normalized candidate filters for normal CV search.'}
          </p>
        </div>
        {hasAny ? (
          <button
            type="button"
            onClick={clearAll}
            className="inline-flex items-center gap-1 rounded-full border border-gray-200 px-2.5 py-1 text-xs font-semibold text-gray-600 hover:border-red-200 hover:text-red-600"
          >
            <X className="h-3 w-3" /> Clear
          </button>
        ) : null}
      </div>

      <Section title="Keyword" description="Search normal PostgreSQL CV/Job fields.">
        <div className="relative">
          <label htmlFor="normal-filter-keyword" className="sr-only">
            Keyword
          </label>
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            id="normal-filter-keyword"
            value={draftKeyword}
            onChange={(event) => setDraftKeyword(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') applyDraft();
            }}
            placeholder={isJob ? 'React developer, company, requirement...' : 'Python FastAPI, candidate, project...'}
            className={`${inputClass} pl-9`}
          />
        </div>
      </Section>

      <Section title="Industry & role">
        <SelectInput
          label="Industry"
          value={draft.industry}
          options={INDUSTRY_OPTIONS}
          placeholder="Any industry"
          onChange={(value) => setKey('industry', value)}
        />
        <SelectInput
          label="Occupation group"
          value={draft.occupationGroup}
          options={occupationOptions}
          placeholder={draft.industry ? 'Any occupation group' : 'All occupation groups'}
          helper={draft.industry ? 'Options are scoped to the selected industry.' : 'Select an industry to narrow this list.'}
          onChange={(value) => setKey('occupationGroup', value)}
        />
      </Section>

      <Section title="Experience & employment">
        {isJob ? (
          <SelectInput
            label="Seniority"
            value={draft.experienceLevel}
            options={SENIORITY_FILTER_OPTIONS}
            placeholder="Any seniority"
            onChange={(value) => setKey('experienceLevel', value)}
          />
        ) : (
          <MultiChipField
            label="Career level"
            value={draft.careerLevel}
            options={SENIORITY_FILTER_OPTIONS}
            helper="Uses normalized career level keys such as junior, middle, senior, or unknown."
            onChange={(value) => setKey('careerLevel', value)}
          />
        )}
        {!isJob ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <TextInput
              label="Years min"
              type="number"
              min={0}
              value={draft.yearsOfExperienceMin}
              onChange={(value) => setKey('yearsOfExperienceMin', value)}
            />
            <TextInput
              label="Years max"
              type="number"
              min={0}
              value={draft.yearsOfExperienceMax}
              helper="Max is adjusted to min if it is lower."
              onChange={(value) => setKey('yearsOfExperienceMax', value)}
            />
          </div>
        ) : null}
        <MultiChipField
          label="Employment type"
          value={draft.employmentType}
          options={EMPLOYMENT_OPTIONS}
          onChange={(value) => setKey('employmentType', value)}
        />
      </Section>

      <Section title="Skills & tools">
        <TextInput
          id="skills-input"
          label="Skills"
          value={draft.skills}
          placeholder="ReactJS, Postgres, MS Excel"
          helper={isJob ? 'Comma-separated skills.' : 'Aliases are normalized before searching: ReactJS -> react, Postgres -> postgresql.'}
          onChange={(value) => setKey('skills', value)}
        />
        {!isJob ? (
          <>
            <TextInput
              id="tools-and-technologies-input"
              label="Tools and technologies"
              value={draft.toolsAndTechnologies}
              placeholder="FastAPI, Excel, AutoCAD"
              helper="Comma-separated values."
              onChange={(value) => setKey('toolsAndTechnologies', value)}
            />
            <TextInput
              id="domain-knowledge-input"
              label="Domain knowledge"
              value={draft.domainKnowledge}
              placeholder="accounting, tax, healthcare"
              helper="Comma-separated values."
              onChange={(value) => setKey('domainKnowledge', value)}
            />
          </>
        ) : null}
      </Section>

      {!isJob ? (
        <Section title="Education & languages">
          <MultiChipField
            label="Education level"
            value={draft.educationLevel}
            options={EDUCATION_OPTIONS}
            onChange={(value) => setKey('educationLevel', value)}
          />
          <TextInput
            label="Education major"
            value={draft.educationMajor}
            placeholder="Computer Science"
            onChange={(value) => setKey('educationMajor', value)}
          />
          <TextInput
            label="Certifications"
            value={draft.certificationName}
            placeholder="AWS, CPA"
            helper="Comma-separated certification names."
            onChange={(value) => setKey('certificationName', value)}
          />
          <div className="grid gap-3 sm:grid-cols-2">
            <TextInput
              label="Language name"
              value={draft.languageName}
              placeholder="English"
              onChange={(value) => setKey('languageName', value)}
            />
            <SelectInput
              label="Language level"
              value={draft.languageLevel}
              options={LANGUAGE_LEVEL_FILTER_OPTIONS}
              placeholder="Any level"
              onChange={(value) => setKey('languageLevel', value)}
            />
          </div>
        </Section>
      ) : (
        <Section title="Education & location">
          <SelectInput
            label="Education level"
            value={draft.educationLevel}
            options={EDUCATION_OPTIONS}
            placeholder="Any education level"
            onChange={(value) => setKey('educationLevel', value)}
          />
          <SelectInput
            label="Working model"
            value={draft.workingModel}
            options={WORKING_MODEL_OPTIONS}
            placeholder="Any model"
            onChange={(value) => setKey('workingModel', value)}
          />
        </Section>
      )}

      <Section title={isJob ? 'Location & status' : 'Location & status'}>
        <div className="grid gap-3 sm:grid-cols-2">
          <TextInput
            label="City"
            value={draft.city ?? draft.location}
            placeholder="Hà Nội"
            onChange={(value) => {
              setKey('city', value);
              setKey('location', undefined);
            }}
          />
          <TextInput
            label="Country"
            value={draft.country}
            placeholder="Việt Nam"
            onChange={(value) => setKey('country', value)}
          />
        </div>
        {!isJob ? (
          <>
            <SelectInput
              label="Status"
              value={draft.status}
              options={STATUS_OPTIONS}
              placeholder="Published public CVs"
              helper="Public search still only returns published public CVs."
              onChange={(value) => setKey('status', value)}
            />
            <TextInput
              id="tags-input"
              label="Tags"
              value={draft.tags}
              placeholder="backend, remote"
              helper="Comma-separated tags."
              onChange={(value) => setKey('tags', value)}
            />
          </>
        ) : null}
      </Section>

      {!isJob ? null : (
        <Section title="Job-specific">
          <SelectInput
            label="Salary range"
            value={draft.salaryRange}
            options={SALARY_OPTIONS}
            placeholder="Any salary"
            onChange={(value) => setKey('salaryRange', value)}
          />
          <SelectInput
            label="Sort"
            value={draft.sort}
            options={JOB_SORT_OPTIONS}
            placeholder="Default sort"
            onChange={(value) => setKey('sort', value)}
          />
        </Section>
      )}

      {!isJob ? (
        <Section title="Sort">
          <SelectInput
            label="Sort results"
            value={draft.sort}
            options={CV_SORT_OPTIONS}
            placeholder="Default sort"
            onChange={(value) => setKey('sort', value)}
          />
        </Section>
      ) : null}

      {hasAny ? (
        <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-3">
          <div className="mb-2 text-xs font-bold uppercase tracking-wide text-[#0A65CC]">Active filters</div>
          <div className="flex flex-wrap gap-1.5">{activeChips()}</div>
        </div>
      ) : null}

      <div className="sticky bottom-3 flex gap-2 rounded-xl border border-gray-100 bg-white/95 p-2 shadow-lg shadow-gray-900/5 backdrop-blur">
        <button
          type="button"
          onClick={applyDraft}
          className="flex-1 rounded-lg bg-[#0A65CC] px-4 py-2 text-sm font-bold text-white hover:bg-[#085bb8]"
        >
          Apply filters
        </button>
        <button
          type="button"
          onClick={clearAll}
          className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-bold text-gray-700 hover:border-red-200 hover:text-red-600"
        >
          Clear
        </button>
      </div>
    </aside>
  );
};

export default V2SearchFilterPanel;
