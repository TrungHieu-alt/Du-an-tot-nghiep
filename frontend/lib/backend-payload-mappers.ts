type CandidateResumeRequestPayload = {
  title: string;
  location?: string;
  experience?: string;
  skills: string[];
  summary?: string;
  full_text?: string;
  is_main: boolean;
};

type JobPostRequestPayload = {
  title: string;
  role: string;
  location: string;
  job_type: string;
  experience_level: string;
  skills: string[];
  salary_min?: number;
  salary_max?: number;
  full_text?: string;
};

const asText = (value: unknown): string | undefined => {
  if (typeof value !== 'string') return undefined;
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
};

const asStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (typeof item === 'string') return item.trim();
      if (item && typeof item === 'object' && typeof (item as any).name === 'string') {
        return (item as any).name.trim();
      }
      return '';
    })
    .filter(Boolean);
};

const parseSalaryRange = (
  value: unknown
): { salary_min?: number; salary_max?: number } => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return { salary_min: value, salary_max: value };
  }

  if (typeof value !== 'string') return {};
  const normalized = value.replace(/[, ]+/g, '');
  const rangeMatch = normalized.match(/(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)/);
  if (rangeMatch) {
    const min = Number(rangeMatch[1]);
    const max = Number(rangeMatch[2]);
    return {
      salary_min: Number.isFinite(min) ? min : undefined,
      salary_max: Number.isFinite(max) ? max : undefined,
    };
  }

  const singleMatch = normalized.match(/(\d+(?:\.\d+)?)/);
  if (!singleMatch) return {};
  const salary = Number(singleMatch[1]);
  if (!Number.isFinite(salary)) return {};
  return { salary_min: salary, salary_max: salary };
};

const toLines = (value: unknown): string[] => {
  if (typeof value !== 'string') return [];
  return value
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*[-*]\s*/, '').trim())
    .filter(Boolean);
};

export const toCandidateResumeUpdatePayload = (
  formData: any,
  fallback?: any
): CandidateResumeRequestPayload => {
  const title = asText(formData?.headline) || asText(formData?.title) || asText(fallback?.title) || 'Untitled CV';

  const location =
    asText(formData?.location?.city) ||
    asText(formData?.location) ||
    asText(fallback?.location?.city) ||
    asText(fallback?.location);

  const summary = asText(formData?.summary) || asText(formData?.full_text) || asText(fallback?.summary);

  const experience =
    asText(formData?.experience) ||
    toLines(formData?.criteria).join('\n') ||
    asText(fallback?.experience);

  const skillsFromForm = asStringArray(formData?.skills);
  const skills = skillsFromForm.length ? skillsFromForm : asStringArray(fallback?.skills);

  const full_text =
    asText(formData?.full_text) ||
    [summary, experience].filter(Boolean).join('\n\n') ||
    asText(fallback?.full_text);

  return {
    title,
    location,
    experience,
    skills,
    summary,
    full_text,
    is_main: Boolean(formData?.is_main ?? fallback?.is_main),
  };
};

export const toJobPostUpdatePayload = (
  formData: any,
  fallback?: any
): JobPostRequestPayload => {
  const title = asText(formData?.title) || asText(fallback?.title) || 'Untitled Job';
  const role =
    asText(formData?.role) ||
    asText(formData?.targetRole) ||
    asText(fallback?.role) ||
    title;
  const location =
    asText(formData?.location?.city) ||
    asText(formData?.location) ||
    asText(fallback?.location?.city) ||
    asText(fallback?.location) ||
    'Remote';
  const job_type =
    asText(formData?.job_type) ||
    (Array.isArray(formData?.employmentType) && formData.employmentType.length
      ? asText(formData.employmentType[0])
      : undefined) ||
    asText(fallback?.job_type) ||
    'Full-time';
  const experience_level =
    asText(formData?.experience_level) ||
    asText(formData?.experienceLevel) ||
    asText(formData?.seniority) ||
    asText(fallback?.experience_level) ||
    'Mid-Level';
  const skillsFromForm = asStringArray(formData?.skills);
  const skills = skillsFromForm.length ? skillsFromForm : asStringArray(fallback?.skills);
  const salary = {
    salary_min:
      typeof formData?.salary_min === 'number' ? formData.salary_min : undefined,
    salary_max:
      typeof formData?.salary_max === 'number' ? formData.salary_max : undefined,
  };
  const salaryFromRange =
    salary.salary_min === undefined && salary.salary_max === undefined
      ? parseSalaryRange(formData?.salaryRange)
      : salary;

  const requirements = toLines(formData?.requirements || formData?.criteria);
  const fullTextFallback = asText(fallback?.full_text);
  const full_text =
    asText(formData?.full_text) ||
    [asText(formData?.description), requirements.join('\n')].filter(Boolean).join('\n\n') ||
    fullTextFallback;

  return {
    title,
    role,
    location,
    job_type,
    experience_level,
    skills,
    salary_min:
      salaryFromRange.salary_min ??
      (typeof fallback?.salary_min === 'number' ? fallback.salary_min : undefined),
    salary_max:
      salaryFromRange.salary_max ??
      (typeof fallback?.salary_max === 'number' ? fallback.salary_max : undefined),
    full_text,
  };
};
