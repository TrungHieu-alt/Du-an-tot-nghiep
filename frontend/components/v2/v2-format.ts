/**
 * Display-label helpers for V2 enum slugs.
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
  ha_noi: 'Hà Nội',
  tp_hcm: 'TP. Hồ Chí Minh',
  da_nang: 'Đà Nẵng',
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
  lop_9: 'Lớp 9',
  lop_12: 'Lớp 12 / THPT',
  dai_hoc: 'Đại học',
  thac_si: 'Thạc sĩ',
  tien_si: 'Tiến sĩ',
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
  { value: 'ha_noi', label: LOCATION_LABELS.ha_noi },
  { value: 'tp_hcm', label: LOCATION_LABELS.tp_hcm },
  { value: 'da_nang', label: LOCATION_LABELS.da_nang },
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
