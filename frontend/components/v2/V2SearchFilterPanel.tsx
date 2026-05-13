import React from 'react';
import { X, Filter as FilterIcon } from 'lucide-react';

export type V2SearchMode = 'job' | 'cv';

export interface V2SearchFilters {
  location?: string;
  industry?: string;
  employmentType?: string;
  experienceLevel?: string;
  salaryRange?: string;
  educationLevel?: string;
  workingModel?: string;
  sort?: string;
  skills?: string;
  yearsOfExperience?: string;
  expectedSalaryRange?: string;
  availability?: string;
}

interface FilterOption {
  value: string;
  label: string;
}

interface V2SearchFilterPanelProps {
  mode: V2SearchMode;
  filters: V2SearchFilters;
  onChange: (next: V2SearchFilters) => void;
}

export const LOCATION_OPTIONS: FilterOption[] = [
  { value: 'ha_noi', label: 'Hà Nội' },
  { value: 'tp_hcm', label: 'TP. Hồ Chí Minh' },
  { value: 'da_nang', label: 'Đà Nẵng' },
  { value: 'can_tho', label: 'Cần Thơ' },
  { value: 'binh_duong', label: 'Bình Dương' },
  { value: 'dong_nai', label: 'Đồng Nai' },
  { value: 'hai_phong', label: 'Hải Phòng' },
  { value: 'remote', label: 'Remote' },
  { value: 'other', label: 'Other' },
];

export const INDUSTRY_OPTIONS: FilterOption[] = [
  { value: 'it_software', label: 'IT / Software' },
  { value: 'sales', label: 'Sales' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'accounting_finance', label: 'Accounting / Finance' },
  { value: 'human_resources', label: 'Human Resources' },
  { value: 'customer_service', label: 'Customer Service' },
  { value: 'education_training', label: 'Education / Training' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'construction', label: 'Construction' },
  { value: 'logistics_supply_chain', label: 'Logistics / Supply Chain' },
  { value: 'design_creative', label: 'Design / Creative' },
  { value: 'engineering', label: 'Engineering' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'hospitality_tourism', label: 'Hospitality / Tourism' },
  { value: 'administration_office', label: 'Administration / Office' },
  { value: 'legal', label: 'Legal' },
  { value: 'other', label: 'Other' },
];

const EMPLOYMENT_OPTIONS: FilterOption[] = [
  { value: 'fulltime', label: 'Full-time' },
  { value: 'parttime', label: 'Part-time' },
  { value: 'internship', label: 'Internship' },
  { value: 'contract', label: 'Contract' },
  { value: 'freelance', label: 'Freelance' },
  { value: 'remote', label: 'Remote' },
  { value: 'temporary', label: 'Temporary' },
];

const JOB_EXPERIENCE_OPTIONS: FilterOption[] = [
  { value: 'no_experience_required', label: 'No experience required' },
  { value: 'intern', label: 'Intern' },
  { value: 'entry_level', label: 'Entry-level' },
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid-level' },
  { value: 'senior', label: 'Senior' },
  { value: 'manager', label: 'Manager' },
  { value: 'director', label: 'Director' },
  { value: 'executive', label: 'Executive' },
];

const CV_EXPERIENCE_OPTIONS: FilterOption[] = [
  { value: 'no_experience', label: 'No experience' },
  { value: 'intern', label: 'Intern' },
  { value: 'entry_level', label: 'Entry-level' },
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid-level' },
  { value: 'senior', label: 'Senior' },
  { value: 'manager', label: 'Manager' },
  { value: 'director', label: 'Director' },
  { value: 'executive', label: 'Executive' },
];

const YEARS_OPTIONS: FilterOption[] = [
  { value: 'less_than_1', label: 'Less than 1 year' },
  { value: '1_2', label: '1 - 2 years' },
  { value: '2_5', label: '2 - 5 years' },
  { value: '5_10', label: '5 - 10 years' },
  { value: '10_plus', label: '10+ years' },
];

const SALARY_OPTIONS: FilterOption[] = [
  { value: 'any', label: 'Any' },
  { value: 'negotiable', label: 'Negotiable' },
  { value: 'under_10m', label: 'Under 10M' },
  { value: '10_20m', label: '10M - 20M' },
  { value: '20_30m', label: '20M - 30M' },
  { value: '30_50m', label: '30M - 50M' },
  { value: '50m_plus', label: '50M+' },
  { value: 'commission', label: 'Commission-based' },
];

const EXPECTED_SALARY_OPTIONS = SALARY_OPTIONS.filter((option) => option.value !== 'commission');

const EDUCATION_OPTIONS: FilterOption[] = [
  { value: 'no_requirement', label: 'No requirement' },
  { value: 'high_school', label: 'High school' },
  { value: 'vocational_college', label: 'Vocational / College' },
  { value: 'university', label: 'University' },
  { value: 'bachelor', label: 'Bachelor' },
  { value: 'master', label: 'Master' },
  { value: 'doctorate', label: 'Doctorate' },
  { value: 'other', label: 'Other' },
];

const WORKING_MODEL_OPTIONS: FilterOption[] = [
  { value: 'onsite', label: 'On-site' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'remote', label: 'Remote' },
];

const AVAILABILITY_OPTIONS: FilterOption[] = [
  { value: 'immediately', label: 'Immediately' },
  { value: 'within_1_week', label: 'Within 1 week' },
  { value: 'within_1_month', label: 'Within 1 month' },
  { value: 'negotiable', label: 'Negotiable' },
];

const JOB_SORT_OPTIONS: FilterOption[] = [
  { value: 'newest', label: 'Newest' },
  { value: 'oldest', label: 'Oldest' },
  { value: 'most_relevant', label: 'Most relevant' },
  { value: 'salary_high_to_low', label: 'Salary high to low' },
  { value: 'salary_low_to_high', label: 'Salary low to high' },
];

const CV_SORT_OPTIONS: FilterOption[] = [
  { value: 'newest', label: 'Newest' },
  { value: 'oldest', label: 'Oldest' },
  { value: 'most_relevant', label: 'Most relevant' },
  { value: 'most_experienced', label: 'Most experienced' },
];

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

const SelectGroup: React.FC<{
  title: string;
  value?: string;
  options: FilterOption[];
  onChange: (value?: string) => void;
}> = ({ title, value, options, onChange }) => (
  <Group title={title}>
    {options.map((option) => (
      <Chip
        key={option.value}
        active={value === option.value}
        onClick={() => onChange(value === option.value ? undefined : option.value)}
      >
        {option.label}
      </Chip>
    ))}
  </Group>
);

const V2SearchFilterPanel: React.FC<V2SearchFilterPanelProps> = ({
  mode,
  filters,
  onChange,
}) => {
  const hasAny = Object.values(filters).some((value) => Boolean(value));

  const setKey = <K extends keyof V2SearchFilters>(
    key: K,
    value: V2SearchFilters[K] | undefined
  ) => {
    onChange({
      ...filters,
      [key]: value,
    });
  };

  const clearAll = () => onChange({});
  const isJob = mode === 'job';

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

      <SelectGroup
        title="Khu vực"
        value={filters.location}
        options={LOCATION_OPTIONS}
        onChange={(value) => setKey('location', value)}
      />

      <SelectGroup
        title={isJob ? 'Ngành nghề / Danh mục' : 'Ngành mong muốn'}
        value={filters.industry}
        options={INDUSTRY_OPTIONS}
        onChange={(value) => setKey('industry', value)}
      />

      {isJob && (
        <SelectGroup
          title="Hình thức làm việc"
          value={filters.employmentType}
          options={EMPLOYMENT_OPTIONS}
          onChange={(value) => setKey('employmentType', value)}
        />
      )}

      <SelectGroup
        title="Cấp kinh nghiệm"
        value={filters.experienceLevel}
        options={isJob ? JOB_EXPERIENCE_OPTIONS : CV_EXPERIENCE_OPTIONS}
        onChange={(value) => setKey('experienceLevel', value)}
      />

      {!isJob && (
        <SelectGroup
          title="Số năm kinh nghiệm"
          value={filters.yearsOfExperience}
          options={YEARS_OPTIONS}
          onChange={(value) => setKey('yearsOfExperience', value)}
        />
      )}

      <SelectGroup
        title={isJob ? 'Mức lương' : 'Lương kỳ vọng'}
        value={isJob ? filters.salaryRange : filters.expectedSalaryRange}
        options={isJob ? SALARY_OPTIONS : EXPECTED_SALARY_OPTIONS}
        onChange={(value) =>
          setKey(isJob ? 'salaryRange' : 'expectedSalaryRange', value)
        }
      />

      <SelectGroup
        title={isJob ? 'Yêu cầu học vấn' : 'Trình độ học vấn'}
        value={filters.educationLevel}
        options={EDUCATION_OPTIONS}
        onChange={(value) => setKey('educationLevel', value)}
      />

      <SelectGroup
        title={isJob ? 'Mô hình làm việc' : 'Mong muốn làm việc'}
        value={filters.workingModel}
        options={WORKING_MODEL_OPTIONS}
        onChange={(value) => setKey('workingModel', value)}
      />

      {!isJob && (
        <SelectGroup
          title="Sẵn sàng nhận việc"
          value={filters.availability}
          options={AVAILABILITY_OPTIONS}
          onChange={(value) => setKey('availability', value)}
        />
      )}

      <Group title="Kỹ năng / Từ khóa">
        <input
          type="text"
          value={filters.skills ?? ''}
          onChange={(event) => setKey('skills', event.target.value || undefined)}
          placeholder="Excel, Sales, English, React..."
          className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 placeholder-gray-400 focus:border-[#0A65CC] focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/15"
        />
      </Group>

      <SelectGroup
        title="Sắp xếp"
        value={filters.sort}
        options={isJob ? JOB_SORT_OPTIONS : CV_SORT_OPTIONS}
        onChange={(value) => setKey('sort', value)}
      />
    </aside>
  );
};

export default V2SearchFilterPanel;
