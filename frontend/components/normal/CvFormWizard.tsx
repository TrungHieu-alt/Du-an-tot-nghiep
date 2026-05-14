import React, { useMemo, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';

import type { NormalCv, NormalCvCreatePayload } from '../../types';
import {
  CV_STATUS_OPTIONS,
  EDUCATION_LEVEL_OPTIONS,
  EMPLOYMENT_TYPE_OPTIONS,
  INDUSTRY_OPTIONS,
  LANGUAGE_LEVEL_OPTIONS,
  OCCUPATION_GROUP_OPTIONS,
  PORTFOLIO_MEDIA_TYPE_OPTIONS,
  SENIORITY_OPTIONS,
  SKILL_CATEGORY_OPTIONS,
  SKILL_LEVEL_OPTIONS,
  VISIBILITY_OPTIONS,
  normalizeSkillNameForForm,
  occupationOptionsForIndustry,
  optionLabel,
} from '../../src/reference/normalEnums';
import {
  EmptyState,
  Field,
  MultiOptionField,
  SelectField,
  Stepper,
  StringListEditor,
  WizardActions,
  cardClass,
  inputClass,
  type FormStep,
} from './FormPrimitives';

const steps: FormStep[] = [
  { title: 'Basic information', subtitle: 'Identity, contact, and profile summary' },
  { title: 'Career target', subtitle: 'Industry, level, role, and availability' },
  { title: 'Skills and tools', subtitle: 'Normalized skills, tools, and domains' },
  { title: 'Experience', subtitle: 'Work history, responsibilities, achievements' },
  { title: 'Education', subtitle: 'Education and certifications' },
  { title: 'Optional profile', subtitle: 'Projects, languages, portfolio, references' },
  { title: 'Review and save', subtitle: 'Check normalized values before saving' },
];

const makeKey = () => Math.random().toString(36).slice(2);
const isEmail = (value: string) => !value.trim() || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
const isPhone = (value: string) => !value.trim() || /^[0-9+()\-\s.]{7,20}$/.test(value.trim());
const toNumber = (value: string): number | undefined => {
  if (!value.trim()) return undefined;
  const next = Number(value);
  return Number.isFinite(next) ? next : undefined;
};
const dateInput = (value: unknown): string => (typeof value === 'string' ? value.slice(0, 10) : '');
const dateTimeOrUndefined = (value: string): string | undefined => value ? `${value}T00:00:00.000Z` : undefined;
const arrayFromUnknown = (value: unknown): string[] => Array.isArray(value) ? value.map(String).filter(Boolean) : [];
const clean = <T extends Record<string, unknown>>(value: T): T =>
  Object.fromEntries(Object.entries(value).filter(([, item]) => item !== undefined && item !== '')) as T;

export interface CvSkillForm {
  key: string;
  name: string;
  normalized_name: string;
  level: string;
  category: string;
  years: string;
}

interface CvExperienceForm {
  key: string;
  id: string;
  title: string;
  company: string;
  company_website: string;
  location: string;
  from: string;
  to: string;
  is_current: boolean;
  employment_type: string;
  team_size: string;
  responsibilities: string[];
  achievements: string[];
  skills_used: string[];
  tools_used: string[];
  tags: string[];
}

interface CvEducationForm {
  key: string;
  degree: string;
  level: string;
  major: string;
  school: string;
  from: string;
  to: string;
  gpa: string;
}

interface CvProjectForm {
  key: string;
  name: string;
  description: string;
  role: string;
  from: string;
  to: string;
  tools: string[];
  skills_used: string[];
  outcomes: string[];
  url: string;
  metrics: string[];
}

interface CvCertificationForm {
  key: string;
  name: string;
  issuer: string;
  issue_date: string;
  expiry_date: string;
  credential_url: string;
}

interface CvLanguageForm {
  key: string;
  name: string;
  level: string;
}

interface CvPortfolioForm {
  key: string;
  media_type: string;
  url: string;
  description: string;
}

interface CvReferenceForm {
  key: string;
  name: string;
  relation: string;
  contact: string;
  note: string;
}

export interface CvFormState {
  avatar_url: string;
  fullname: string;
  preferred_name: string;
  email: string;
  phone: string;
  city: string;
  state: string;
  country: string;
  headline: string;
  summary: string;
  industry: string;
  occupation_group: string;
  career_level: string;
  years_of_experience: string;
  target_role: string;
  employment_type: string[];
  salary_expectation: string;
  availability: string;
  skills: CvSkillForm[];
  tools_and_technologies: string[];
  domain_knowledge: string[];
  experiences: CvExperienceForm[];
  education: CvEducationForm[];
  projects: CvProjectForm[];
  certifications: CvCertificationForm[];
  languages: CvLanguageForm[];
  portfolio: CvPortfolioForm[];
  references: CvReferenceForm[];
  status: string;
  visibility: 'public' | 'private' | 'unlisted' | 'unknown';
  tags: string[];
}

const emptySkill = (name = ''): CvSkillForm => {
  const normalized = normalizeSkillNameForForm(name);
  return {
    key: makeKey(),
    name,
    normalized_name: name ? normalized.normalizedName : '',
    level: 'unknown',
    category: name ? normalized.category : 'technical',
    years: '',
  };
};

const emptyExperience = (): CvExperienceForm => ({
  key: makeKey(),
  id: '',
  title: '',
  company: '',
  company_website: '',
  location: '',
  from: '',
  to: '',
  is_current: false,
  employment_type: 'unknown',
  team_size: '',
  responsibilities: [],
  achievements: [],
  skills_used: [],
  tools_used: [],
  tags: [],
});

const emptyEducation = (): CvEducationForm => ({
  key: makeKey(),
  degree: '',
  level: 'unknown',
  major: '',
  school: '',
  from: '',
  to: '',
  gpa: '',
});

const emptyProject = (): CvProjectForm => ({
  key: makeKey(),
  name: '',
  description: '',
  role: '',
  from: '',
  to: '',
  tools: [],
  skills_used: [],
  outcomes: [],
  url: '',
  metrics: [],
});

const emptyCertification = (): CvCertificationForm => ({
  key: makeKey(),
  name: '',
  issuer: '',
  issue_date: '',
  expiry_date: '',
  credential_url: '',
});

const emptyLanguage = (): CvLanguageForm => ({ key: makeKey(), name: '', level: 'unknown' });
const emptyPortfolio = (): CvPortfolioForm => ({ key: makeKey(), media_type: 'other', url: '', description: '' });
const emptyReference = (): CvReferenceForm => ({ key: makeKey(), name: '', relation: '', contact: '', note: '' });

export const createEmptyCvForm = (): CvFormState => ({
  avatar_url: '',
  fullname: '',
  preferred_name: '',
  email: '',
  phone: '',
  city: '',
  state: '',
  country: 'VN',
  headline: '',
  summary: '',
  industry: 'unknown',
  occupation_group: 'unknown',
  career_level: 'unknown',
  years_of_experience: '',
  target_role: '',
  employment_type: ['fulltime'],
  salary_expectation: '',
  availability: '',
  skills: [],
  tools_and_technologies: [],
  domain_knowledge: [],
  experiences: [],
  education: [],
  projects: [],
  certifications: [],
  languages: [],
  portfolio: [],
  references: [],
  status: 'draft',
  visibility: 'private',
  tags: [],
});

const skillFromUnknown = (skill: unknown): CvSkillForm => {
  const item = skill && typeof skill === 'object' ? skill as Record<string, unknown> : { name: String(skill || '') };
  const name = String(item.name || '');
  const normalized = normalizeSkillNameForForm(name);
  return {
    key: makeKey(),
    name,
    normalized_name: String(item.normalized_name || item.normalizedName || normalized.normalizedName || ''),
    level: String(item.level || 'unknown'),
    category: String(item.category || normalized.category || 'unknown'),
    years: item.years === undefined || item.years === null ? '' : String(item.years),
  };
};

export const cvFormFromExtractedCv = (cv: Record<string, unknown>): CvFormState => {
  const location = cv.location && typeof cv.location === 'object' ? cv.location as Record<string, unknown> : {};
  return {
    ...createEmptyCvForm(),
    avatar_url: typeof cv.avatar_url === 'string' ? cv.avatar_url : '',
    fullname: typeof cv.fullname === 'string' ? cv.fullname : '',
    preferred_name: typeof cv.preferred_name === 'string' ? cv.preferred_name : '',
    email: typeof cv.email === 'string' ? cv.email : '',
    phone: typeof cv.phone === 'string' ? cv.phone : '',
    city: typeof location.city === 'string' ? location.city : '',
    state: typeof location.state === 'string' ? location.state : '',
    country: typeof location.country === 'string' ? location.country : 'VN',
    headline: typeof cv.headline === 'string' ? cv.headline : '',
    summary: typeof cv.summary === 'string' ? cv.summary : '',
    industry: typeof cv.industry === 'string' ? cv.industry : 'unknown',
    occupation_group: typeof cv.occupation_group === 'string' ? cv.occupation_group : 'unknown',
    career_level: typeof cv.career_level === 'string' ? cv.career_level : 'unknown',
    years_of_experience: typeof cv.years_of_experience === 'number' ? String(cv.years_of_experience) : '',
    target_role: typeof cv.target_role === 'string' ? cv.target_role : '',
    employment_type: Array.isArray(cv.employment_type) && cv.employment_type.length > 0 ? cv.employment_type.map(String) : ['unknown'],
    salary_expectation: typeof cv.salary_expectation === 'string' ? cv.salary_expectation : '',
    availability: typeof cv.availability === 'string' ? cv.availability : '',
    skills: Array.isArray(cv.skills) ? cv.skills.map(skillFromUnknown).filter((skill) => skill.name) : [],
    tools_and_technologies: arrayFromUnknown(cv.tools_and_technologies),
    domain_knowledge: arrayFromUnknown(cv.domain_knowledge),
    experiences: Array.isArray(cv.experiences) ? cv.experiences.map((item) => experienceFromUnknown(item)) : [],
    education: Array.isArray(cv.education) ? cv.education.map((item) => educationFromUnknown(item)) : [],
    projects: Array.isArray(cv.projects) ? cv.projects.map((item) => projectFromUnknown(item)) : [],
    certifications: Array.isArray(cv.certifications) ? cv.certifications.map((item) => certificationFromUnknown(item)) : [],
    languages: Array.isArray(cv.languages) ? cv.languages.map((item) => languageFromUnknown(item)) : [],
    portfolio: Array.isArray(cv.portfolio) ? cv.portfolio.map((item) => portfolioFromUnknown(item)) : [],
    references: Array.isArray(cv.references) ? cv.references.map((item) => referenceFromUnknown(item)) : [],
    status: typeof cv.status === 'string' ? cv.status : 'draft',
    visibility: (typeof cv.visibility === 'string' ? cv.visibility : 'private') as CvFormState['visibility'],
    tags: arrayFromUnknown(cv.tags),
  };
};

export const cvFormFromNormalCv = (cv: NormalCv): CvFormState => cvFormFromExtractedCv(cv as unknown as Record<string, unknown>);

const experienceFromUnknown = (value: unknown): CvExperienceForm => {
  const item = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  return {
    ...emptyExperience(),
    id: String(item.id || ''),
    title: String(item.title || ''),
    company: String(item.company || ''),
    company_website: String(item.company_website || item.companyWebsite || ''),
    location: String(item.location || ''),
    from: dateInput(item.from),
    to: dateInput(item.to),
    is_current: Boolean(item.is_current ?? item.isCurrent),
    employment_type: String(item.employment_type || item.employmentType || 'unknown'),
    team_size: item.team_size === undefined && item.teamSize === undefined ? '' : String(item.team_size ?? item.teamSize),
    responsibilities: arrayFromUnknown(item.responsibilities),
    achievements: arrayFromUnknown(item.achievements),
    skills_used: arrayFromUnknown(item.skills_used ?? item.skillsUsed),
    tools_used: arrayFromUnknown(item.tools_used ?? item.toolsUsed),
    tags: arrayFromUnknown(item.tags),
  };
};

const educationFromUnknown = (value: unknown): CvEducationForm => {
  const item = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  return {
    ...emptyEducation(),
    degree: String(item.degree || ''),
    level: String(item.level || 'unknown'),
    major: String(item.major || ''),
    school: String(item.school || ''),
    from: dateInput(item.from),
    to: dateInput(item.to),
    gpa: String(item.gpa || ''),
  };
};

const projectFromUnknown = (value: unknown): CvProjectForm => {
  const item = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  return {
    ...emptyProject(),
    name: String(item.name || ''),
    description: String(item.description || ''),
    role: String(item.role || ''),
    from: dateInput(item.from),
    to: dateInput(item.to),
    tools: arrayFromUnknown(item.tools),
    skills_used: arrayFromUnknown(item.skills_used ?? item.skillsUsed),
    outcomes: arrayFromUnknown(item.outcomes),
    url: String(item.url || ''),
    metrics: arrayFromUnknown(item.metrics),
  };
};

const certificationFromUnknown = (value: unknown): CvCertificationForm => {
  const item = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  return {
    ...emptyCertification(),
    name: String(item.name || ''),
    issuer: String(item.issuer || ''),
    issue_date: dateInput(item.issue_date ?? item.issueDate),
    expiry_date: dateInput(item.expiry_date ?? item.expiryDate),
    credential_url: String(item.credential_url || item.credentialUrl || ''),
  };
};

const languageFromUnknown = (value: unknown): CvLanguageForm => {
  const item = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  return { key: makeKey(), name: String(item.name || ''), level: String(item.level || 'unknown') };
};

const portfolioFromUnknown = (value: unknown): CvPortfolioForm => {
  const item = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  return {
    key: makeKey(),
    media_type: String(item.media_type || item.mediaType || 'other'),
    url: String(item.url || ''),
    description: String(item.description || ''),
  };
};

const referenceFromUnknown = (value: unknown): CvReferenceForm => {
  const item = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  return {
    key: makeKey(),
    name: String(item.name || ''),
    relation: String(item.relation || ''),
    contact: String(item.contact || ''),
    note: String(item.note || ''),
  };
};

const hasAny = (values: Array<string | number | boolean | string[]>) =>
  values.some((value) => Array.isArray(value) ? value.length > 0 : Boolean(String(value || '').trim()));

export const cvPayloadFromForm = (form: CvFormState, mode: 'draft' | 'publish'): NormalCvCreatePayload => ({
  avatar_url: form.avatar_url || undefined,
  fullname: form.fullname.trim(),
  preferred_name: form.preferred_name || undefined,
  email: form.email || undefined,
  phone: form.phone || undefined,
  location: clean({
    city: form.city || undefined,
    state: form.state || undefined,
    country: form.country || undefined,
  }),
  headline: form.headline || undefined,
  summary: form.summary || undefined,
  industry: form.industry || 'unknown',
  occupation_group: form.occupation_group || 'unknown',
  career_level: form.career_level || 'unknown',
  years_of_experience: toNumber(form.years_of_experience),
  target_role: form.target_role || undefined,
  employment_type: form.employment_type.length > 0 ? form.employment_type : ['unknown'],
  salary_expectation: form.salary_expectation || undefined,
  availability: form.availability || undefined,
  skills: form.skills
    .filter((skill) => skill.name.trim())
    .map((skill) => {
      const normalized = normalizeSkillNameForForm(skill.name);
      return clean({
        name: skill.name.trim(),
        normalized_name: skill.normalized_name || normalized.normalizedName,
        level: skill.level || 'unknown',
        category: skill.category || normalized.category || 'unknown',
        years: toNumber(skill.years),
      });
    }),
  tools_and_technologies: form.tools_and_technologies,
  domain_knowledge: form.domain_knowledge,
  experiences: form.experiences
    .filter((item) => hasAny([item.title, item.company, item.responsibilities, item.achievements]))
    .map((item) => clean({
      id: item.id || undefined,
      title: item.title || undefined,
      company: item.company || undefined,
      company_website: item.company_website || undefined,
      location: item.location || undefined,
      from: dateTimeOrUndefined(item.from),
      to: item.is_current ? undefined : dateTimeOrUndefined(item.to),
      is_current: item.is_current,
      employment_type: item.employment_type || 'unknown',
      team_size: toNumber(item.team_size),
      responsibilities: item.responsibilities,
      achievements: item.achievements,
      skills_used: item.skills_used,
      tools_used: item.tools_used,
      tags: item.tags,
    })),
  education: form.education
    .filter((item) => hasAny([item.degree, item.school, item.major]))
    .map((item) => clean({
      degree: item.degree || undefined,
      level: item.level || 'unknown',
      major: item.major || undefined,
      school: item.school || undefined,
      from: dateTimeOrUndefined(item.from),
      to: dateTimeOrUndefined(item.to),
      gpa: item.gpa || undefined,
    })),
  projects: form.projects
    .filter((item) => hasAny([item.name, item.description, item.tools, item.skills_used]))
    .map((item) => clean({
      name: item.name || undefined,
      description: item.description || undefined,
      role: item.role || undefined,
      from: dateTimeOrUndefined(item.from),
      to: dateTimeOrUndefined(item.to),
      tools: item.tools,
      skills_used: item.skills_used,
      outcomes: item.outcomes,
      url: item.url || undefined,
      metrics: item.metrics,
    })),
  certifications: form.certifications
    .filter((item) => hasAny([item.name, item.issuer]))
    .map((item) => clean({
      name: item.name || undefined,
      issuer: item.issuer || undefined,
      issue_date: dateTimeOrUndefined(item.issue_date),
      expiry_date: dateTimeOrUndefined(item.expiry_date),
      credential_url: item.credential_url || undefined,
    })),
  languages: form.languages
    .filter((item) => item.name.trim())
    .map((item) => ({ name: item.name.trim(), level: item.level || 'unknown' })),
  portfolio: form.portfolio
    .filter((item) => hasAny([item.url, item.description]))
    .map((item) => clean({
      media_type: item.media_type || 'other',
      url: item.url || undefined,
      description: item.description || undefined,
    })),
  references: form.references
    .filter((item) => hasAny([item.name, item.contact, item.note]))
    .map((item) => clean({
      name: item.name || undefined,
      relation: item.relation || undefined,
      contact: item.contact || undefined,
      note: item.note || undefined,
    })),
  status: mode === 'publish' ? 'published' : 'draft',
  visibility: mode === 'publish' ? form.visibility : 'private',
  tags: form.tags,
});

const TextField: React.FC<{
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  helper?: string;
  error?: string;
  type?: string;
}> = ({ label, value, onChange, required, helper, error, type = 'text' }) => (
  <Field label={label} required={required} helper={helper} error={error}>
    <input value={value} onChange={(event) => onChange(event.target.value)} type={type} className={inputClass} />
  </Field>
);

const TextAreaField: React.FC<{
  label: string;
  value: string;
  onChange: (value: string) => void;
  helper?: string;
  rows?: number;
}> = ({ label, value, onChange, helper, rows = 4 }) => (
  <Field label={label} helper={helper}>
    <textarea value={value} onChange={(event) => onChange(event.target.value)} rows={rows} className={inputClass} />
  </Field>
);

function updateAt<T extends object>(items: T[], index: number, patch: Record<string, unknown>): T[] {
  return items.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } as T : item);
}

const RemoveButton: React.FC<{ onClick: () => void; label?: string }> = ({ onClick, label = 'Remove' }) => (
  <button type="button" onClick={onClick} className="inline-flex items-center gap-1 rounded-full bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600">
    <Trash2 className="h-3.5 w-3.5" />
    {label}
  </button>
);

const AddButton: React.FC<{ onClick: () => void; children: React.ReactNode }> = ({ onClick, children }) => (
  <button type="button" onClick={onClick} className="inline-flex items-center gap-2 rounded-xl border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-semibold text-[#0F6FD6]">
    <Plus className="h-4 w-4" />
    {children}
  </button>
);

const ReviewLine: React.FC<{ label: string; value?: React.ReactNode }> = ({ label, value }) => (
  <div className="rounded-xl bg-gray-50 p-3">
    <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</dt>
    <dd className="mt-1 text-sm font-semibold text-gray-900">{value || 'Not provided'}</dd>
  </div>
);

interface CvFormWizardProps {
  initialValue: CvFormState;
  saving: boolean;
  onSubmit: (payload: NormalCvCreatePayload, mode: 'draft' | 'publish') => Promise<void>;
  onCancel?: () => void;
  extractWarnings?: string[];
  extractedText?: string;
  compact?: boolean;
}

export const CvFormWizard: React.FC<CvFormWizardProps> = ({
  initialValue,
  saving,
  onSubmit,
  onCancel,
  extractWarnings = [],
  extractedText = '',
  compact = false,
}) => {
  const [form, setForm] = useState<CvFormState>(initialValue);
  const [currentStep, setCurrentStep] = useState(0);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const occupationOptions = useMemo(() => occupationOptionsForIndustry(form.industry), [form.industry]);

  const set = <K extends keyof CvFormState>(key: K, value: CvFormState[K]) => setForm((current) => ({ ...current, [key]: value }));
  const criticalErrors = () => {
    const next: Record<string, string> = {};
    if (!form.fullname.trim()) next.fullname = 'Full name is required.';
    if (!isEmail(form.email)) next.email = 'Please enter a valid email.';
    if (!isPhone(form.phone)) next.phone = 'Please enter a valid phone number.';
    return next;
  };
  const stepErrors = (step: number) => (step === 0 ? criticalErrors() : {});
  const nextDisabled = Object.keys(stepErrors(currentStep)).length > 0;

  const goNext = () => {
    const next = stepErrors(currentStep);
    setErrors(next);
    if (Object.keys(next).length === 0) setCurrentStep((step) => Math.min(step + 1, steps.length - 1));
  };

  const submit = async (mode: 'draft' | 'publish') => {
    const next = criticalErrors();
    setErrors(next);
    if (Object.keys(next).length > 0) {
      setCurrentStep(0);
      return;
    }
    await onSubmit(cvPayloadFromForm(form, mode), mode);
  };

  const skillSection = (
    <div className="space-y-4">
      {form.skills.length === 0 ? <EmptyState>No skills added yet. Add your first skill.</EmptyState> : null}
      {form.skills.map((skill, index) => (
        <div key={skill.key} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <h3 className="font-bold text-gray-900">Skill {index + 1}</h3>
              <p className="text-xs text-gray-500">Original name is displayed; normalizedName is saved for search.</p>
            </div>
            <RemoveButton onClick={() => set('skills', form.skills.filter((_, itemIndex) => itemIndex !== index))} />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <TextField
              label="Skill name"
              value={skill.name}
              onChange={(value) => {
                const normalized = normalizeSkillNameForForm(value);
                set('skills', updateAt(form.skills, index, {
                  name: value,
                  normalized_name: normalized.normalizedName,
                  category: skill.category === 'technical' || skill.category === 'unknown' ? normalized.category : skill.category,
                }));
              }}
            />
            <TextField label="Normalized name" value={skill.normalized_name} onChange={(value) => set('skills', updateAt(form.skills, index, { normalized_name: value }))} />
            <SelectField label="Level" value={skill.level} options={SKILL_LEVEL_OPTIONS} onChange={(value) => set('skills', updateAt(form.skills, index, { level: value }))} />
            <SelectField label="Category" value={skill.category} options={SKILL_CATEGORY_OPTIONS} onChange={(value) => set('skills', updateAt(form.skills, index, { category: value }))} />
            <TextField label="Years" value={skill.years} onChange={(value) => set('skills', updateAt(form.skills, index, { years: value }))} type="number" />
          </div>
        </div>
      ))}
      <AddButton onClick={() => set('skills', [...form.skills, emptySkill()])}>Add skill</AddButton>
    </div>
  );

  return (
    <div className={compact ? 'space-y-4' : 'mx-auto max-w-6xl space-y-5'}>
      <div>
        <h2 className="text-2xl font-bold text-gray-900">{compact ? 'Edit CV' : 'Create CV'}</h2>
        <p className="mt-1 text-sm text-gray-500">Build a normalized multi-industry CV. Enum values are saved as keys only.</p>
      </div>
      <Stepper steps={steps} currentStep={currentStep} />

      {extractWarnings.length > 0 ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          <p className="font-semibold">PDF extraction warnings</p>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {extractWarnings.map((warning) => <li key={warning}>{warning}</li>)}
          </ul>
        </div>
      ) : null}
      {extractedText ? (
        <details className="rounded-xl border border-gray-100 bg-gray-50 p-3 text-sm text-gray-600">
          <summary className="cursor-pointer font-semibold text-gray-800">View extracted text</summary>
          <pre className="mt-3 max-h-48 overflow-auto whitespace-pre-wrap text-xs">{extractedText}</pre>
        </details>
      ) : null}

      <section className={cardClass}>
        <div className="mb-5">
          <h3 className="text-lg font-bold text-gray-900">{steps[currentStep].title}</h3>
          <p className="text-sm text-gray-500">{steps[currentStep].subtitle}</p>
        </div>

        {currentStep === 0 ? (
          <div className="grid gap-4 lg:grid-cols-[180px_minmax(0,1fr)]">
            <div className="flex flex-col items-center rounded-2xl bg-gray-50 p-4 text-center">
              {form.avatar_url ? (
                <img src={form.avatar_url} alt="" className="h-24 w-24 rounded-2xl object-cover" />
              ) : (
                <div className="flex h-24 w-24 items-center justify-center rounded-2xl bg-white text-sm font-semibold text-gray-400">Avatar</div>
              )}
              <p className="mt-3 text-xs text-gray-500">Paste an image URL to preview avatar.</p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <TextField label="Avatar URL" value={form.avatar_url} onChange={(value) => set('avatar_url', value)} />
              <TextField label="Full name" value={form.fullname} onChange={(value) => set('fullname', value)} required error={errors.fullname} />
              <TextField label="Preferred name" value={form.preferred_name} onChange={(value) => set('preferred_name', value)} />
              <TextField label="Email" value={form.email} onChange={(value) => set('email', value)} error={errors.email} />
              <TextField label="Phone" value={form.phone} onChange={(value) => set('phone', value)} error={errors.phone} />
              <TextField label="City" value={form.city} onChange={(value) => set('city', value)} />
              <TextField label="State" value={form.state} onChange={(value) => set('state', value)} />
              <TextField label="Country" value={form.country} onChange={(value) => set('country', value)} />
              <TextField label="Headline" value={form.headline} onChange={(value) => set('headline', value)} helper="A short role headline, for example: Senior Accountant or Frontend Developer." />
              <TextAreaField label="Summary" value={form.summary} onChange={(value) => set('summary', value)} helper="Keep it concise and outcome-focused." />
            </div>
          </div>
        ) : null}

        {currentStep === 1 ? (
          <div className="grid gap-4 md:grid-cols-2">
            <SelectField label="Industry" value={form.industry} options={INDUSTRY_OPTIONS} onChange={(value) => {
              const allowed = occupationOptionsForIndustry(value).map((option) => option.value);
              setForm((current) => ({ ...current, industry: value, occupation_group: allowed.includes(current.occupation_group) ? current.occupation_group : 'unknown' }));
            }} helper="Used for multi-industry search filters." />
            <SelectField label="Occupation group" value={form.occupation_group} options={occupationOptions} onChange={(value) => set('occupation_group', value)} />
            <SelectField label="Career level" value={form.career_level} options={SENIORITY_OPTIONS} onChange={(value) => set('career_level', value)} helper="Defaults to unknown, never junior." />
            <TextField label="Years of experience" value={form.years_of_experience} onChange={(value) => set('years_of_experience', value)} type="number" />
            <TextField label="Target role" value={form.target_role} onChange={(value) => set('target_role', value)} />
            <MultiOptionField label="Employment type" values={form.employment_type} options={EMPLOYMENT_TYPE_OPTIONS} onChange={(value) => set('employment_type', value)} />
            <TextField label="Salary expectation" value={form.salary_expectation} onChange={(value) => set('salary_expectation', value)} />
            <TextField label="Availability" value={form.availability} onChange={(value) => set('availability', value)} />
          </div>
        ) : null}

        {currentStep === 2 ? (
          <div className="space-y-6">
            {skillSection}
            <div className="grid gap-4 md:grid-cols-2">
              <StringListEditor label="Tools and technologies" values={form.tools_and_technologies} onChange={(value) => set('tools_and_technologies', value)} placeholder="Excel, Figma, FastAPI..." emptyText="No tools added yet." />
              <StringListEditor label="Domain knowledge" values={form.domain_knowledge} onChange={(value) => set('domain_knowledge', value)} placeholder="Tax, retail, healthcare..." emptyText="No domain knowledge added yet." />
            </div>
          </div>
        ) : null}

        {currentStep === 3 ? (
          <div className="space-y-4">
            {form.experiences.length === 0 ? <EmptyState>No experience added yet.</EmptyState> : null}
            {form.experiences.map((item, index) => (
              <div key={item.key} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="font-bold text-gray-900">Experience {index + 1}</h3>
                  <RemoveButton onClick={() => set('experiences', form.experiences.filter((_, itemIndex) => itemIndex !== index))} />
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <TextField label="Title" value={item.title} onChange={(value) => set('experiences', updateAt(form.experiences, index, { title: value }))} />
                  <TextField label="Company" value={item.company} onChange={(value) => set('experiences', updateAt(form.experiences, index, { company: value }))} />
                  <TextField label="Company website" value={item.company_website} onChange={(value) => set('experiences', updateAt(form.experiences, index, { company_website: value }))} />
                  <TextField label="Location" value={item.location} onChange={(value) => set('experiences', updateAt(form.experiences, index, { location: value }))} />
                  <TextField label="From" value={item.from} onChange={(value) => set('experiences', updateAt(form.experiences, index, { from: value }))} type="date" />
                  {!item.is_current ? <TextField label="To" value={item.to} onChange={(value) => set('experiences', updateAt(form.experiences, index, { to: value }))} type="date" /> : null}
                  <Field label="Current role">
                    <label className="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-3 py-2 text-sm">
                      <input type="checkbox" checked={item.is_current} onChange={(event) => set('experiences', updateAt(form.experiences, index, { is_current: event.target.checked, to: event.target.checked ? '' : item.to }))} />
                      I currently work here
                    </label>
                  </Field>
                  <SelectField label="Employment type" value={item.employment_type} options={EMPLOYMENT_TYPE_OPTIONS} onChange={(value) => set('experiences', updateAt(form.experiences, index, { employment_type: value }))} />
                  <TextField label="Team size" value={item.team_size} onChange={(value) => set('experiences', updateAt(form.experiences, index, { team_size: value }))} type="number" />
                  <StringListEditor label="Responsibilities" values={item.responsibilities} onChange={(value) => set('experiences', updateAt(form.experiences, index, { responsibilities: value }))} emptyText="No responsibilities added yet." />
                  <StringListEditor label="Achievements" values={item.achievements} onChange={(value) => set('experiences', updateAt(form.experiences, index, { achievements: value }))} emptyText="No achievements added yet." />
                  <StringListEditor label="Skills used" values={item.skills_used} onChange={(value) => set('experiences', updateAt(form.experiences, index, { skills_used: value }))} />
                  <StringListEditor label="Tools used" values={item.tools_used} onChange={(value) => set('experiences', updateAt(form.experiences, index, { tools_used: value }))} />
                  <StringListEditor label="Tags" values={item.tags} onChange={(value) => set('experiences', updateAt(form.experiences, index, { tags: value }))} />
                </div>
              </div>
            ))}
            <AddButton onClick={() => set('experiences', [...form.experiences, emptyExperience()])}>Add experience</AddButton>
          </div>
        ) : null}

        {currentStep === 4 ? (
          <div className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-gray-900">Education</h3>
                <AddButton onClick={() => set('education', [...form.education, emptyEducation()])}>Add education</AddButton>
              </div>
              {form.education.length === 0 ? <EmptyState>No education added yet.</EmptyState> : null}
              {form.education.map((item, index) => (
                <div key={item.key} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
                  <div className="mb-3 flex justify-end"><RemoveButton onClick={() => set('education', form.education.filter((_, itemIndex) => itemIndex !== index))} /></div>
                  <div className="grid gap-3 md:grid-cols-2">
                    <TextField label="Degree" value={item.degree} onChange={(value) => set('education', updateAt(form.education, index, { degree: value }))} />
                    <SelectField label="Level" value={item.level} options={EDUCATION_LEVEL_OPTIONS} onChange={(value) => set('education', updateAt(form.education, index, { level: value }))} />
                    <TextField label="Major" value={item.major} onChange={(value) => set('education', updateAt(form.education, index, { major: value }))} />
                    <TextField label="School" value={item.school} onChange={(value) => set('education', updateAt(form.education, index, { school: value }))} />
                    <TextField label="From" value={item.from} onChange={(value) => set('education', updateAt(form.education, index, { from: value }))} type="date" />
                    <TextField label="To" value={item.to} onChange={(value) => set('education', updateAt(form.education, index, { to: value }))} type="date" />
                    <TextField label="GPA" value={item.gpa} onChange={(value) => set('education', updateAt(form.education, index, { gpa: value }))} />
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-gray-900">Certifications</h3>
                <AddButton onClick={() => set('certifications', [...form.certifications, emptyCertification()])}>Add certification</AddButton>
              </div>
              {form.certifications.length === 0 ? <EmptyState>No certification added yet.</EmptyState> : null}
              {form.certifications.map((item, index) => (
                <div key={item.key} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
                  <div className="mb-3 flex justify-end"><RemoveButton onClick={() => set('certifications', form.certifications.filter((_, itemIndex) => itemIndex !== index))} /></div>
                  <div className="grid gap-3 md:grid-cols-2">
                    <TextField label="Name" value={item.name} onChange={(value) => set('certifications', updateAt(form.certifications, index, { name: value }))} />
                    <TextField label="Issuer" value={item.issuer} onChange={(value) => set('certifications', updateAt(form.certifications, index, { issuer: value }))} />
                    <TextField label="Issue date" value={item.issue_date} onChange={(value) => set('certifications', updateAt(form.certifications, index, { issue_date: value }))} type="date" />
                    <TextField label="Expiry date" value={item.expiry_date} onChange={(value) => set('certifications', updateAt(form.certifications, index, { expiry_date: value }))} type="date" />
                    <TextField label="Credential URL" value={item.credential_url} onChange={(value) => set('certifications', updateAt(form.certifications, index, { credential_url: value }))} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {currentStep === 5 ? (
          <div className="space-y-5">
            <details open className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
              <summary className="cursor-pointer font-bold text-gray-900">Projects</summary>
              <div className="mt-4 space-y-4">
                {form.projects.length === 0 ? <EmptyState>No projects added yet.</EmptyState> : null}
                {form.projects.map((item, index) => (
                  <div key={item.key} className="rounded-xl bg-white p-4">
                    <div className="mb-3 flex justify-end"><RemoveButton onClick={() => set('projects', form.projects.filter((_, itemIndex) => itemIndex !== index))} /></div>
                    <div className="grid gap-3 md:grid-cols-2">
                      <TextField label="Name" value={item.name} onChange={(value) => set('projects', updateAt(form.projects, index, { name: value }))} />
                      <TextField label="Role" value={item.role} onChange={(value) => set('projects', updateAt(form.projects, index, { role: value }))} />
                      <TextField label="From" value={item.from} onChange={(value) => set('projects', updateAt(form.projects, index, { from: value }))} type="date" />
                      <TextField label="To" value={item.to} onChange={(value) => set('projects', updateAt(form.projects, index, { to: value }))} type="date" />
                      <TextField label="URL" value={item.url} onChange={(value) => set('projects', updateAt(form.projects, index, { url: value }))} />
                      <TextAreaField label="Description" value={item.description} onChange={(value) => set('projects', updateAt(form.projects, index, { description: value }))} />
                      <StringListEditor label="Tools" values={item.tools} onChange={(value) => set('projects', updateAt(form.projects, index, { tools: value }))} />
                      <StringListEditor label="Skills used" values={item.skills_used} onChange={(value) => set('projects', updateAt(form.projects, index, { skills_used: value }))} />
                      <StringListEditor label="Outcomes" values={item.outcomes} onChange={(value) => set('projects', updateAt(form.projects, index, { outcomes: value }))} />
                      <StringListEditor label="Metrics" values={item.metrics} onChange={(value) => set('projects', updateAt(form.projects, index, { metrics: value }))} />
                    </div>
                  </div>
                ))}
                <AddButton onClick={() => set('projects', [...form.projects, emptyProject()])}>Add project</AddButton>
              </div>
            </details>

            <details open className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
              <summary className="cursor-pointer font-bold text-gray-900">Languages, portfolio, references</summary>
              <div className="mt-4 grid gap-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between"><h4 className="font-semibold text-gray-900">Languages</h4><AddButton onClick={() => set('languages', [...form.languages, emptyLanguage()])}>Add language</AddButton></div>
                  {form.languages.length === 0 ? <EmptyState>No languages added yet.</EmptyState> : null}
                  {form.languages.map((item, index) => (
                    <div key={item.key} className="grid gap-3 rounded-xl bg-white p-3 md:grid-cols-[1fr_1fr_auto]">
                      <TextField label="Name" value={item.name} onChange={(value) => set('languages', updateAt(form.languages, index, { name: value }))} />
                      <SelectField label="Level" value={item.level} options={LANGUAGE_LEVEL_OPTIONS} onChange={(value) => set('languages', updateAt(form.languages, index, { level: value }))} />
                      <div className="self-end"><RemoveButton onClick={() => set('languages', form.languages.filter((_, itemIndex) => itemIndex !== index))} /></div>
                    </div>
                  ))}
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between"><h4 className="font-semibold text-gray-900">Portfolio</h4><AddButton onClick={() => set('portfolio', [...form.portfolio, emptyPortfolio()])}>Add portfolio</AddButton></div>
                  {form.portfolio.length === 0 ? <EmptyState>No portfolio links added yet.</EmptyState> : null}
                  {form.portfolio.map((item, index) => (
                    <div key={item.key} className="grid gap-3 rounded-xl bg-white p-3 md:grid-cols-2">
                      <SelectField label="Media type" value={item.media_type} options={PORTFOLIO_MEDIA_TYPE_OPTIONS} onChange={(value) => set('portfolio', updateAt(form.portfolio, index, { media_type: value }))} />
                      <TextField label="URL" value={item.url} onChange={(value) => set('portfolio', updateAt(form.portfolio, index, { url: value }))} />
                      <TextAreaField label="Description" value={item.description} onChange={(value) => set('portfolio', updateAt(form.portfolio, index, { description: value }))} />
                      <div className="self-end"><RemoveButton onClick={() => set('portfolio', form.portfolio.filter((_, itemIndex) => itemIndex !== index))} /></div>
                    </div>
                  ))}
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between"><h4 className="font-semibold text-gray-900">References</h4><AddButton onClick={() => set('references', [...form.references, emptyReference()])}>Add reference</AddButton></div>
                  {form.references.length === 0 ? <EmptyState>No references added yet.</EmptyState> : null}
                  {form.references.map((item, index) => (
                    <div key={item.key} className="grid gap-3 rounded-xl bg-white p-3 md:grid-cols-2">
                      <TextField label="Name" value={item.name} onChange={(value) => set('references', updateAt(form.references, index, { name: value }))} />
                      <TextField label="Relation" value={item.relation} onChange={(value) => set('references', updateAt(form.references, index, { relation: value }))} />
                      <TextField label="Contact" value={item.contact} onChange={(value) => set('references', updateAt(form.references, index, { contact: value }))} />
                      <TextField label="Note" value={item.note} onChange={(value) => set('references', updateAt(form.references, index, { note: value }))} />
                      <div className="md:col-span-2"><RemoveButton onClick={() => set('references', form.references.filter((_, itemIndex) => itemIndex !== index))} /></div>
                    </div>
                  ))}
                </div>
              </div>
            </details>
          </div>
        ) : null}

        {currentStep === 6 ? (
          <div className="space-y-5">
            <div className="grid gap-3 md:grid-cols-3">
              <ReviewLine label="Full name" value={form.fullname} />
              <ReviewLine label="Target role" value={form.target_role || form.headline} />
              <ReviewLine label="Industry" value={optionLabel(INDUSTRY_OPTIONS, form.industry)} />
              <ReviewLine label="Occupation" value={optionLabel(OCCUPATION_GROUP_OPTIONS, form.occupation_group)} />
              <ReviewLine label="Career level" value={optionLabel(SENIORITY_OPTIONS, form.career_level)} />
              <ReviewLine label="Employment type" value={form.employment_type.map((item) => optionLabel(EMPLOYMENT_TYPE_OPTIONS, item)).join(', ')} />
              <ReviewLine label="Skills" value={form.skills.map((skill) => `${skill.name || 'Unnamed'} (${skill.normalized_name || normalizeSkillNameForForm(skill.name).normalizedName})`).join(', ')} />
              <ReviewLine label="Experience" value={`${form.experiences.length} entries`} />
              <ReviewLine label="Education" value={`${form.education.length} entries`} />
              <ReviewLine label="Projects" value={`${form.projects.length} entries`} />
              <ReviewLine label="Languages" value={form.languages.map((item) => `${item.name} ${item.level}`).join(', ')} />
              <ReviewLine label="Portfolio" value={`${form.portfolio.length} links`} />
              <ReviewLine label="References" value={`${form.references.length} entries`} />
              <ReviewLine label="Status" value={optionLabel(CV_STATUS_OPTIONS, form.status)} />
              <ReviewLine label="Tags" value={form.tags.join(', ')} />
            </div>
            <SelectField label="Save visibility" value={form.visibility} options={VISIBILITY_OPTIONS} onChange={(value) => set('visibility', value as CvFormState['visibility'])} helper="Draft saves remain private. Publish uses this visibility value." />
            <StringListEditor label="Tags" values={form.tags} onChange={(value) => set('tags', value)} />
          </div>
        ) : null}
      </section>

      <WizardActions
        currentStep={currentStep}
        totalSteps={steps.length}
        saving={saving}
        nextDisabled={nextDisabled}
        onBack={() => currentStep === 0 && onCancel ? onCancel() : setCurrentStep((step) => Math.max(0, step - 1))}
        onNext={goNext}
        onSaveDraft={() => void submit('draft')}
        onPublish={() => void submit('publish')}
      />
    </div>
  );
};

export default CvFormWizard;
