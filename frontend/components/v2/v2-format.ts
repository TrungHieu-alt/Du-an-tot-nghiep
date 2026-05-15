/**
 * Display-label helpers for V2 contract values.
 *
 * Source of truth for the underlying enum values: backend CHECK constraints
 * in backend/db_v2/orm_models.py. Keep these maps in sync if a new enum
 * value is added at the database layer.
 */

import type {
  EducationV2,
  JobTypeV2,
  LocationV2,
  SeniorityV2,
} from '../../types';

const LOCATION_LABELS: Record<LocationV2, string> = {
  'Hà Nội': 'Hà Nội',
  'TP. Hồ Chí Minh': 'TP. Hồ Chí Minh',
  'Đà Nẵng': 'Đà Nẵng',
};

const JOB_TYPE_LABELS: Record<JobTypeV2, string> = {
  remote: 'Remote',
  fulltime: 'Full-time',
  parttime: 'Part-time',
};

const SENIORITY_LABELS: Record<SeniorityV2, string> = {
  intern: 'Intern',
  fresher: 'Fresher',
  junior: 'Junior',
  mid: 'Mid-Level',
  senior: 'Senior',
  lead: 'Lead',
};

const EDUCATION_LABELS: Record<EducationV2, string> = {
  high_school: 'THPT',
  bachelor: 'Đại học',
  master: 'Thạc sĩ',
  phd: 'Tiến sĩ',
};

export const formatLocationV2 = (loc: LocationV2): string =>
  LOCATION_LABELS[loc] ?? String(loc);

export const formatJobTypeV2 = (t: JobTypeV2): string =>
  JOB_TYPE_LABELS[t] ?? String(t);

export const formatSeniorityV2 = (s: SeniorityV2): string =>
  SENIORITY_LABELS[s] ?? String(s);

export const formatEducationV2 = (e: EducationV2): string =>
  EDUCATION_LABELS[e] ?? String(e);

export const LOCATION_OPTIONS: Array<{ value: LocationV2; label: string }> = [
  { value: 'Hà Nội', label: LOCATION_LABELS['Hà Nội'] },
  { value: 'TP. Hồ Chí Minh', label: LOCATION_LABELS['TP. Hồ Chí Minh'] },
  { value: 'Đà Nẵng', label: LOCATION_LABELS['Đà Nẵng'] },
];

export const JOB_TYPE_OPTIONS: Array<{ value: JobTypeV2; label: string }> = [
  { value: 'remote', label: JOB_TYPE_LABELS.remote },
  { value: 'fulltime', label: JOB_TYPE_LABELS.fulltime },
  { value: 'parttime', label: JOB_TYPE_LABELS.parttime },
];

export const SENIORITY_OPTIONS: Array<{ value: SeniorityV2; label: string }> = [
  { value: 'intern', label: SENIORITY_LABELS.intern },
  { value: 'fresher', label: SENIORITY_LABELS.fresher },
  { value: 'junior', label: SENIORITY_LABELS.junior },
  { value: 'mid', label: SENIORITY_LABELS.mid },
  { value: 'senior', label: SENIORITY_LABELS.senior },
  { value: 'lead', label: SENIORITY_LABELS.lead },
];
