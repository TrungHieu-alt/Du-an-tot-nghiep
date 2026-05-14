import React, { useMemo, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';

import type { NormalJob, NormalJobCreatePayload } from '../../types';
import {
  CURRENCY_OPTIONS,
  EDUCATION_LEVEL_OPTIONS,
  EMPLOYMENT_TYPE_OPTIONS,
  INDUSTRY_OPTIONS,
  JOB_STATUS_OPTIONS,
  OCCUPATION_GROUP_OPTIONS,
  PRE_SCREEN_QUESTION_TYPE_OPTIONS,
  REMOTE_TYPE_OPTIONS,
  SALARY_PERIOD_OPTIONS,
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
  { title: 'Basic job information', subtitle: 'Title, company, status, and visibility' },
  { title: 'Industry and location', subtitle: 'Role, remote type, employment, seniority' },
  { title: 'Job description', subtitle: 'Description and bullet lists' },
  { title: 'Skills and requirements', subtitle: 'General, must-have, nice-to-have skills' },
  { title: 'Education and screening', subtitle: 'Education, certifications, questions' },
  { title: 'Salary and application', subtitle: 'Compensation, recruiter, apply details' },
  { title: 'Review and save', subtitle: 'Tags, categories, final check' },
];

const makeKey = () => Math.random().toString(36).slice(2);
const isEmail = (value: string) => !value.trim() || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
const toNumber = (value: string): number | undefined => {
  if (!value.trim()) return undefined;
  const next = Number(value);
  return Number.isFinite(next) ? next : undefined;
};
const dateInput = (value: unknown): string => (typeof value === 'string' ? value.slice(0, 10) : '');
const deadlineValue = (value: string): string | undefined => value ? `${value}T23:59:00.000Z` : undefined;
const arrayFromUnknown = (value: unknown): string[] => Array.isArray(value) ? value.map(String).filter(Boolean) : [];
const clean = <T extends Record<string, unknown>>(value: T): T =>
  Object.fromEntries(Object.entries(value).filter(([, item]) => item !== undefined && item !== '')) as T;

export interface JobSkillForm {
  key: string;
  name: string;
  normalized_name: string;
  level: string;
  category: string;
  weight: string;
}

interface PreScreenQuestionForm {
  key: string;
  q: string;
  type: string;
  required: boolean;
  options: string[];
}

export interface JobFormState {
  company_id: string;
  title: string;
  slug: string;
  company_name: string;
  company_logo_url: string;
  company_website: string;
  company_location: string;
  company_size: string;
  company_industry: string;
  department: string;
  status: 'draft' | 'published' | 'closed' | 'unknown';
  visibility: 'public' | 'private' | 'unlisted' | 'unknown';
  industry: string;
  occupation_group: string;
  city: string;
  state: string;
  country: string;
  remote_type: string;
  remote: boolean;
  employment_type: string[];
  seniority: string;
  team_size: string;
  experience_years: string;
  description: string;
  responsibilities: string[];
  requirements: string[];
  nice_to_have: string[];
  skills: JobSkillForm[];
  must_have_skills: JobSkillForm[];
  nice_to_have_skills: JobSkillForm[];
  tools_and_technologies: string[];
  domain_knowledge: string[];
  education_level: string;
  required_education_level: string;
  required_education_major: string;
  required_certifications: string[];
  pre_screen_questions: PreScreenQuestionForm[];
  salary_min: string;
  salary_max: string;
  salary_currency: string;
  salary_period: string;
  benefits: string[];
  bonus: string;
  equity: string;
  apply_url: string;
  apply_email: string;
  recruiter_name: string;
  recruiter_email: string;
  recruiter_phone: string;
  how_to_apply: string;
  application_deadline: string;
  required_docs: string[];
  tags: string[];
  categories: string[];
  archived: boolean;
  version: string;
}

const emptySkill = (weight = ''): JobSkillForm => ({
  key: makeKey(),
  name: '',
  normalized_name: '',
  level: 'unknown',
  category: 'technical',
  weight,
});

const skillFromUnknown = (value: unknown, defaultWeight = ''): JobSkillForm => {
  const item = value && typeof value === 'object' ? value as Record<string, unknown> : { name: String(value || '') };
  const name = String(item.name || '');
  const normalized = normalizeSkillNameForForm(name);
  return {
    key: makeKey(),
    name,
    normalized_name: String(item.normalized_name || item.normalizedName || normalized.normalizedName || ''),
    level: String(item.level || 'unknown'),
    category: String(item.category || normalized.category || 'unknown'),
    weight: item.weight === undefined || item.weight === null ? defaultWeight : String(item.weight),
  };
};

const emptyQuestion = (): PreScreenQuestionForm => ({
  key: makeKey(),
  q: '',
  type: 'unknown',
  required: true,
  options: [],
});

const questionFromUnknown = (value: unknown): PreScreenQuestionForm => {
  const item = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  return {
    key: makeKey(),
    q: String(item.q || ''),
    type: String(item.type || 'unknown'),
    required: Boolean(item.required ?? true),
    options: arrayFromUnknown(item.options),
  };
};

export const createEmptyJobForm = (): JobFormState => ({
  company_id: '',
  title: '',
  slug: '',
  company_name: '',
  company_logo_url: '',
  company_website: '',
  company_location: '',
  company_size: '',
  company_industry: '',
  department: '',
  status: 'draft',
  visibility: 'private',
  industry: 'unknown',
  occupation_group: 'unknown',
  city: '',
  state: '',
  country: 'VN',
  remote_type: 'unknown',
  remote: false,
  employment_type: ['fulltime'],
  seniority: 'unknown',
  team_size: '',
  experience_years: '',
  description: '',
  responsibilities: [],
  requirements: [],
  nice_to_have: [],
  skills: [],
  must_have_skills: [],
  nice_to_have_skills: [],
  tools_and_technologies: [],
  domain_knowledge: [],
  education_level: 'unknown',
  required_education_level: 'unknown',
  required_education_major: '',
  required_certifications: [],
  pre_screen_questions: [],
  salary_min: '',
  salary_max: '',
  salary_currency: 'VND',
  salary_period: 'month',
  benefits: [],
  bonus: '',
  equity: '',
  apply_url: '',
  apply_email: '',
  recruiter_name: '',
  recruiter_email: '',
  recruiter_phone: '',
  how_to_apply: '',
  application_deadline: '',
  required_docs: [],
  tags: [],
  categories: [],
  archived: false,
  version: '1',
});

export const jobFormFromNormalJob = (job: NormalJob): JobFormState => {
  const location = job.location || {};
  const salary = job.salary || {};
  const recruiter = job.recruiter || {};
  const requiredEducation = job.required_education || {};
  return {
    ...createEmptyJobForm(),
    company_id: job.company_id || '',
    title: job.title || '',
    slug: job.slug || '',
    company_name: job.company_name || '',
    company_logo_url: job.company_logo_url || '',
    company_website: job.company_website || '',
    company_location: job.company_location || '',
    company_size: job.company_size || '',
    company_industry: job.company_industry || '',
    department: job.department || '',
    status: job.status || 'draft',
    visibility: job.visibility || 'private',
    industry: job.industry || 'unknown',
    occupation_group: job.occupation_group || 'unknown',
    city: typeof location.city === 'string' ? location.city : '',
    state: typeof location.state === 'string' ? location.state : '',
    country: typeof location.country === 'string' ? location.country : 'VN',
    remote_type: typeof location.remote_type === 'string' ? location.remote_type : 'unknown',
    remote: Boolean(job.remote),
    employment_type: job.employment_type && job.employment_type.length > 0 ? job.employment_type : ['unknown'],
    seniority: job.seniority || 'unknown',
    team_size: job.team_size === undefined || job.team_size === null ? '' : String(job.team_size),
    experience_years: job.experience_years === undefined || job.experience_years === null ? '' : String(job.experience_years),
    description: job.description || '',
    responsibilities: job.responsibilities || [],
    requirements: job.requirements || [],
    nice_to_have: job.nice_to_have || [],
    skills: (job.skills || []).map((item) => skillFromUnknown(item)),
    must_have_skills: (job.must_have_skills || []).map((item) => skillFromUnknown(item, '10')),
    nice_to_have_skills: (job.nice_to_have_skills || []).map((item) => skillFromUnknown(item, '5')),
    tools_and_technologies: job.tools_and_technologies || [],
    domain_knowledge: job.domain_knowledge || [],
    education_level: job.education_level || 'unknown',
    required_education_level: typeof requiredEducation.level === 'string' ? requiredEducation.level : 'unknown',
    required_education_major: typeof requiredEducation.major === 'string' ? requiredEducation.major : '',
    required_certifications: job.required_certifications || [],
    pre_screen_questions: (job.pre_screen_questions || []).map(questionFromUnknown),
    salary_min: salary.min === undefined || salary.min === null ? '' : String(salary.min),
    salary_max: salary.max === undefined || salary.max === null ? '' : String(salary.max),
    salary_currency: typeof salary.currency === 'string' ? salary.currency : 'VND',
    salary_period: typeof salary.period === 'string' ? salary.period : 'month',
    benefits: job.benefits || [],
    bonus: job.bonus || '',
    equity: job.equity || '',
    apply_url: job.apply_url || '',
    apply_email: job.apply_email || '',
    recruiter_name: typeof recruiter.name === 'string' ? recruiter.name : '',
    recruiter_email: typeof recruiter.email === 'string' ? recruiter.email : '',
    recruiter_phone: typeof recruiter.phone === 'string' ? recruiter.phone : '',
    how_to_apply: job.how_to_apply || '',
    application_deadline: dateInput(job.application_deadline),
    required_docs: job.required_docs || [],
    tags: job.tags || [],
    categories: job.categories || [],
    archived: Boolean(job.archived),
    version: typeof job.version === 'number' ? String(job.version) : '1',
  };
};

const skillPayload = (skills: JobSkillForm[], includeWeight: boolean) =>
  skills
    .filter((skill) => skill.name.trim())
    .map((skill) => {
      const normalized = normalizeSkillNameForForm(skill.name);
      return clean({
        name: skill.name.trim(),
        normalized_name: skill.normalized_name || normalized.normalizedName,
        level: skill.level || 'unknown',
        category: skill.category || normalized.category || 'unknown',
        weight: includeWeight ? (toNumber(skill.weight) ?? 1) : undefined,
      });
    });

export const jobPayloadFromForm = (form: JobFormState, mode: 'draft' | 'publish'): NormalJobCreatePayload => ({
  company_id: form.company_id || undefined,
  title: form.title.trim(),
  slug: form.slug || undefined,
  company_name: form.company_name || undefined,
  company_logo_url: form.company_logo_url || undefined,
  company_website: form.company_website || undefined,
  company_location: form.company_location || undefined,
  company_size: form.company_size || undefined,
  company_industry: form.company_industry || undefined,
  department: form.department || undefined,
  status: mode === 'draft' ? 'draft' : 'published',
  visibility: mode === 'draft' ? 'private' : form.visibility,
  industry: form.industry || 'unknown',
  occupation_group: form.occupation_group || 'unknown',
  location: clean({
    city: form.city || undefined,
    state: form.state || undefined,
    country: form.country || undefined,
    remote_type: form.remote_type || 'unknown',
  }),
  remote: form.remote_type === 'remote' || form.remote,
  employment_type: form.employment_type.length > 0 ? form.employment_type : ['unknown'],
  seniority: form.seniority || 'unknown',
  team_size: toNumber(form.team_size),
  experience_years: toNumber(form.experience_years),
  description: form.description || undefined,
  responsibilities: form.responsibilities,
  requirements: form.requirements,
  nice_to_have: form.nice_to_have,
  skills: skillPayload(form.skills, false),
  must_have_skills: skillPayload(form.must_have_skills, true),
  nice_to_have_skills: skillPayload(form.nice_to_have_skills, true),
  tools_and_technologies: form.tools_and_technologies,
  domain_knowledge: form.domain_knowledge,
  education_level: form.education_level || 'unknown',
  required_education: clean({
    level: form.required_education_level || 'unknown',
    major: form.required_education_major || undefined,
  }),
  required_certifications: form.required_certifications,
  pre_screen_questions: form.pre_screen_questions
    .filter((item) => item.q.trim())
    .map((item) => ({
      q: item.q.trim(),
      type: item.type || 'unknown',
      required: item.required,
      options: ['single-choice', 'multi-choice'].includes(item.type) ? item.options : [],
    })),
  salary: clean({
    min: toNumber(form.salary_min),
    max: toNumber(form.salary_max),
    currency: form.salary_currency || 'VND',
    period: form.salary_period || 'month',
  }),
  benefits: form.benefits,
  bonus: form.bonus || undefined,
  equity: form.equity || undefined,
  apply_url: form.apply_url || undefined,
  apply_email: form.apply_email || undefined,
  recruiter: clean({
    name: form.recruiter_name || undefined,
    email: form.recruiter_email || undefined,
    phone: form.recruiter_phone || undefined,
  }),
  how_to_apply: form.how_to_apply || undefined,
  application_deadline: deadlineValue(form.application_deadline),
  required_docs: form.required_docs,
  tags: form.tags,
  categories: form.categories,
  archived: form.archived,
  version: toNumber(form.version),
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

const TextAreaField: React.FC<{ label: string; value: string; onChange: (value: string) => void; helper?: string }> = ({ label, value, onChange, helper }) => (
  <Field label={label} helper={helper}>
    <textarea value={value} onChange={(event) => onChange(event.target.value)} rows={5} className={inputClass} />
  </Field>
);

function updateAt<T extends object>(items: T[], index: number, patch: Record<string, unknown>): T[] {
  return items.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } as T : item);
}

const RemoveButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <button type="button" onClick={onClick} className="inline-flex items-center gap-1 rounded-full bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600">
    <Trash2 className="h-3.5 w-3.5" />
    Remove
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

interface JobFormWizardProps {
  initialValue: JobFormState;
  saving: boolean;
  onSubmit: (payload: NormalJobCreatePayload, mode: 'draft' | 'publish') => Promise<void>;
  onCancel?: () => void;
  compact?: boolean;
}

export const JobFormWizard: React.FC<JobFormWizardProps> = ({ initialValue, saving, onSubmit, onCancel, compact = false }) => {
  const [form, setForm] = useState<JobFormState>(initialValue);
  const [currentStep, setCurrentStep] = useState(0);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const occupationOptions = useMemo(() => occupationOptionsForIndustry(form.industry), [form.industry]);
  const set = <K extends keyof JobFormState>(key: K, value: JobFormState[K]) => setForm((current) => ({ ...current, [key]: value }));

  const criticalErrors = () => {
    const next: Record<string, string> = {};
    if (!form.title.trim()) next.title = 'Job title is required.';
    if (!form.company_id.trim() && !form.company_name.trim()) next.company_name = 'Company name is required when company ID is empty.';
    if (!isEmail(form.apply_email)) next.apply_email = 'Please enter a valid apply email.';
    if (!isEmail(form.recruiter_email)) next.recruiter_email = 'Please enter a valid recruiter email.';
    return next;
  };
  const stepErrors = (step: number) => step === 0 || step === 5 ? criticalErrors() : {};
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
    await onSubmit(jobPayloadFromForm(form, mode), mode);
  };

  const renderSkills = (key: 'skills' | 'must_have_skills' | 'nice_to_have_skills', title: string, defaultWeight = '') => {
    const rows = form[key];
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="font-bold text-gray-900">{title}</h3>
            <p className="text-xs text-gray-500">Weight is saved as data only for downstream review.</p>
          </div>
          <AddButton onClick={() => set(key, [...rows, emptySkill(defaultWeight)] as JobFormState[typeof key])}>Add skill</AddButton>
        </div>
        {rows.length === 0 ? <EmptyState>No skills added yet.</EmptyState> : null}
        {rows.map((skill, index) => (
          <div key={skill.key} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
            <div className="mb-3 flex justify-end"><RemoveButton onClick={() => set(key, rows.filter((_, itemIndex) => itemIndex !== index) as JobFormState[typeof key])} /></div>
            <div className="grid gap-3 md:grid-cols-2">
              <TextField
                label="Skill name"
                value={skill.name}
                onChange={(value) => {
                  const normalized = normalizeSkillNameForForm(value);
                  set(key, updateAt(rows, index, {
                    name: value,
                    normalized_name: normalized.normalizedName,
                    category: skill.category === 'technical' || skill.category === 'unknown' ? normalized.category : skill.category,
                  }) as JobFormState[typeof key]);
                }}
              />
              <TextField label="Normalized name" value={skill.normalized_name} onChange={(value) => set(key, updateAt(rows, index, { normalized_name: value }) as JobFormState[typeof key])} />
              <SelectField label="Level" value={skill.level} options={SKILL_LEVEL_OPTIONS} onChange={(value) => set(key, updateAt(rows, index, { level: value }) as JobFormState[typeof key])} />
              <SelectField label="Category" value={skill.category} options={SKILL_CATEGORY_OPTIONS} onChange={(value) => set(key, updateAt(rows, index, { category: value }) as JobFormState[typeof key])} />
              {key !== 'skills' ? <TextField label="Weight" value={skill.weight} onChange={(value) => set(key, updateAt(rows, index, { weight: value }) as JobFormState[typeof key])} type="number" /> : null}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={compact ? 'space-y-4' : 'mx-auto max-w-6xl space-y-5'}>
      <div>
        <h2 className="text-2xl font-bold text-gray-900">{compact ? 'Edit Recruitment Request' : 'Create Recruitment Request'}</h2>
        <p className="mt-1 text-sm text-gray-500">Create normalized multi-industry job data for regular search and saving only.</p>
      </div>
      <Stepper steps={steps} currentStep={currentStep} />
      <section className={cardClass}>
        <div className="mb-5">
          <h3 className="text-lg font-bold text-gray-900">{steps[currentStep].title}</h3>
          <p className="text-sm text-gray-500">{steps[currentStep].subtitle}</p>
        </div>

        {currentStep === 0 ? (
          <div className="grid gap-4 md:grid-cols-2">
            <TextField label="Job title" value={form.title} onChange={(value) => set('title', value)} required error={errors.title} />
            <TextField label="Company ID" value={form.company_id} onChange={(value) => set('company_id', value)} helper="Optional if company name is provided." />
            <TextField label="Company name" value={form.company_name} onChange={(value) => set('company_name', value)} required={!form.company_id.trim()} error={errors.company_name} />
            <TextField label="Slug" value={form.slug} onChange={(value) => set('slug', value)} />
            <TextField label="Logo URL" value={form.company_logo_url} onChange={(value) => set('company_logo_url', value)} />
            <TextField label="Company website" value={form.company_website} onChange={(value) => set('company_website', value)} />
            <TextField label="Company location" value={form.company_location} onChange={(value) => set('company_location', value)} />
            <TextField label="Company size" value={form.company_size} onChange={(value) => set('company_size', value)} />
            <TextField label="Company industry" value={form.company_industry} onChange={(value) => set('company_industry', value)} />
            <TextField label="Department" value={form.department} onChange={(value) => set('department', value)} />
            <SelectField label="Status" value={form.status} options={JOB_STATUS_OPTIONS} onChange={(value) => set('status', value as JobFormState['status'])} helper="New records default to draft." />
            <SelectField label="Visibility" value={form.visibility} options={VISIBILITY_OPTIONS} onChange={(value) => set('visibility', value as JobFormState['visibility'])} helper="New records default to private." />
          </div>
        ) : null}

        {currentStep === 1 ? (
          <div className="grid gap-4 md:grid-cols-2">
            <SelectField label="Industry" value={form.industry} options={INDUSTRY_OPTIONS} onChange={(value) => {
              const allowed = occupationOptionsForIndustry(value).map((option) => option.value);
              setForm((current) => ({ ...current, industry: value, occupation_group: allowed.includes(current.occupation_group) ? current.occupation_group : 'unknown' }));
            }} />
            <SelectField label="Occupation group" value={form.occupation_group} options={occupationOptions} onChange={(value) => set('occupation_group', value)} />
            <TextField label="City" value={form.city} onChange={(value) => set('city', value)} />
            <TextField label="State" value={form.state} onChange={(value) => set('state', value)} />
            <TextField label="Country" value={form.country} onChange={(value) => set('country', value)} />
            <SelectField label="Remote type" value={form.remote_type} options={REMOTE_TYPE_OPTIONS} onChange={(value) => setForm((current) => ({ ...current, remote_type: value, remote: value === 'remote' ? true : current.remote }))} />
            <Field label="Remote flag">
              <label className="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-3 py-2 text-sm">
                <input type="checkbox" checked={form.remote || form.remote_type === 'remote'} onChange={(event) => set('remote', event.target.checked)} />
                Remote available
              </label>
            </Field>
            <MultiOptionField label="Employment type" values={form.employment_type} options={EMPLOYMENT_TYPE_OPTIONS} onChange={(value) => set('employment_type', value)} />
            <SelectField label="Seniority" value={form.seniority} options={SENIORITY_OPTIONS} onChange={(value) => set('seniority', value)} helper="Defaults to unknown, never junior." />
            <TextField label="Team size" value={form.team_size} onChange={(value) => set('team_size', value)} type="number" />
            <TextField label="Experience years" value={form.experience_years} onChange={(value) => set('experience_years', value)} type="number" />
          </div>
        ) : null}

        {currentStep === 2 ? (
          <div className="grid gap-4">
            <TextAreaField label="Description" value={form.description} onChange={(value) => set('description', value)} helper="Markdown-style plain text is supported." />
            <StringListEditor label="Responsibilities" values={form.responsibilities} onChange={(value) => set('responsibilities', value)} emptyText="No responsibilities added yet." />
            <StringListEditor label="Requirements" values={form.requirements} onChange={(value) => set('requirements', value)} emptyText="No requirements added yet." />
            <StringListEditor label="Nice-to-have" values={form.nice_to_have} onChange={(value) => set('nice_to_have', value)} emptyText="No nice-to-have items added yet." />
          </div>
        ) : null}

        {currentStep === 3 ? (
          <div className="space-y-7">
            {renderSkills('skills', 'General skills')}
            {renderSkills('must_have_skills', 'Must-have skills', '10')}
            {renderSkills('nice_to_have_skills', 'Nice-to-have skills', '5')}
            <div className="grid gap-4 md:grid-cols-2">
              <StringListEditor label="Tools and technologies" values={form.tools_and_technologies} onChange={(value) => set('tools_and_technologies', value)} emptyText="No tools added yet." />
              <StringListEditor label="Domain knowledge" values={form.domain_knowledge} onChange={(value) => set('domain_knowledge', value)} emptyText="No domain knowledge added yet." />
            </div>
          </div>
        ) : null}

        {currentStep === 4 ? (
          <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <SelectField label="Education level" value={form.education_level} options={EDUCATION_LEVEL_OPTIONS} onChange={(value) => setForm((current) => ({ ...current, education_level: value, required_education_level: value }))} />
              <SelectField label="Required education level" value={form.required_education_level} options={EDUCATION_LEVEL_OPTIONS} onChange={(value) => set('required_education_level', value)} />
              <TextField label="Required major" value={form.required_education_major} onChange={(value) => set('required_education_major', value)} />
              <StringListEditor label="Required certifications" values={form.required_certifications} onChange={(value) => set('required_certifications', value)} emptyText="No required certifications added yet." />
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-gray-900">Pre-screen questions</h3>
                  <p className="text-xs text-gray-500">Question type is saved as a normalized enum key.</p>
                </div>
                <AddButton onClick={() => set('pre_screen_questions', [...form.pre_screen_questions, emptyQuestion()])}>Add question</AddButton>
              </div>
              {form.pre_screen_questions.length === 0 ? <EmptyState>No screening questions added yet.</EmptyState> : null}
              {form.pre_screen_questions.map((question, index) => (
                <div key={question.key} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
                  <div className="mb-3 flex justify-end"><RemoveButton onClick={() => set('pre_screen_questions', form.pre_screen_questions.filter((_, itemIndex) => itemIndex !== index))} /></div>
                  <div className="grid gap-3 md:grid-cols-2">
                    <TextField label="Question" value={question.q} onChange={(value) => set('pre_screen_questions', updateAt(form.pre_screen_questions, index, { q: value }))} />
                    <SelectField label="Type" value={question.type} options={PRE_SCREEN_QUESTION_TYPE_OPTIONS} onChange={(value) => set('pre_screen_questions', updateAt(form.pre_screen_questions, index, { type: value, options: ['single-choice', 'multi-choice'].includes(value) ? question.options : [] }))} />
                    <Field label="Required">
                      <label className="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-3 py-2 text-sm">
                        <input type="checkbox" checked={question.required} onChange={(event) => set('pre_screen_questions', updateAt(form.pre_screen_questions, index, { required: event.target.checked }))} />
                        Candidate must answer
                      </label>
                    </Field>
                    {['single-choice', 'multi-choice'].includes(question.type) ? (
                      <StringListEditor label="Options" values={question.options} onChange={(value) => set('pre_screen_questions', updateAt(form.pre_screen_questions, index, { options: value }))} />
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {currentStep === 5 ? (
          <div className="grid gap-4 md:grid-cols-2">
            <TextField label="Salary min" value={form.salary_min} onChange={(value) => set('salary_min', value)} type="number" />
            <TextField label="Salary max" value={form.salary_max} onChange={(value) => set('salary_max', value)} type="number" />
            <SelectField label="Currency" value={form.salary_currency} options={CURRENCY_OPTIONS} onChange={(value) => set('salary_currency', value)} />
            <SelectField label="Period" value={form.salary_period} options={SALARY_PERIOD_OPTIONS} onChange={(value) => set('salary_period', value)} />
            <StringListEditor label="Benefits" values={form.benefits} onChange={(value) => set('benefits', value)} emptyText="No benefits added yet." />
            <StringListEditor label="Required documents" values={form.required_docs} onChange={(value) => set('required_docs', value)} emptyText="No required documents added yet." />
            <TextField label="Bonus" value={form.bonus} onChange={(value) => set('bonus', value)} />
            <TextField label="Equity" value={form.equity} onChange={(value) => set('equity', value)} />
            <TextField label="Apply URL" value={form.apply_url} onChange={(value) => set('apply_url', value)} />
            <TextField label="Apply email" value={form.apply_email} onChange={(value) => set('apply_email', value)} error={errors.apply_email} />
            <TextField label="Recruiter name" value={form.recruiter_name} onChange={(value) => set('recruiter_name', value)} />
            <TextField label="Recruiter email" value={form.recruiter_email} onChange={(value) => set('recruiter_email', value)} error={errors.recruiter_email} />
            <TextField label="Recruiter phone" value={form.recruiter_phone} onChange={(value) => set('recruiter_phone', value)} />
            <TextField label="How to apply" value={form.how_to_apply} onChange={(value) => set('how_to_apply', value)} />
            <TextField label="Application deadline" value={form.application_deadline} onChange={(value) => set('application_deadline', value)} type="date" />
          </div>
        ) : null}

        {currentStep === 6 ? (
          <div className="space-y-5">
            <div className="grid gap-3 md:grid-cols-3">
              <ReviewLine label="Job title" value={form.title} />
              <ReviewLine label="Company" value={form.company_name || form.company_id} />
              <ReviewLine label="Industry" value={optionLabel(INDUSTRY_OPTIONS, form.industry)} />
              <ReviewLine label="Occupation" value={optionLabel(OCCUPATION_GROUP_OPTIONS, form.occupation_group)} />
              <ReviewLine label="Location" value={[form.city, form.country].filter(Boolean).join(', ')} />
              <ReviewLine label="Remote type" value={optionLabel(REMOTE_TYPE_OPTIONS, form.remote_type)} />
              <ReviewLine label="Employment" value={form.employment_type.map((item) => optionLabel(EMPLOYMENT_TYPE_OPTIONS, item)).join(', ')} />
              <ReviewLine label="Seniority" value={optionLabel(SENIORITY_OPTIONS, form.seniority)} />
              <ReviewLine label="Skills" value={`${form.skills.length} general, ${form.must_have_skills.length} must-have, ${form.nice_to_have_skills.length} nice-to-have`} />
              <ReviewLine label="Salary" value={`${form.salary_min || '?'} - ${form.salary_max || '?'} ${form.salary_currency}/${form.salary_period}`} />
              <ReviewLine label="Application" value={form.apply_email || form.apply_url || form.how_to_apply} />
              <ReviewLine label="Screening" value={`${form.pre_screen_questions.length} questions`} />
              <ReviewLine label="Status" value={optionLabel(JOB_STATUS_OPTIONS, form.status)} />
              <ReviewLine label="Visibility" value={optionLabel(VISIBILITY_OPTIONS, form.visibility)} />
              <ReviewLine label="Archived" value={form.archived ? 'Yes' : 'No'} />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <StringListEditor label="Tags" values={form.tags} onChange={(value) => set('tags', value)} />
              <StringListEditor label="Categories" values={form.categories} onChange={(value) => set('categories', value)} />
              <TextField label="Version" value={form.version} onChange={(value) => set('version', value)} type="number" />
              <Field label="Archived">
                <label className="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-3 py-2 text-sm">
                  <input type="checkbox" checked={form.archived} onChange={(event) => set('archived', event.target.checked)} />
                  Archive this request
                </label>
              </Field>
            </div>
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

export default JobFormWizard;
