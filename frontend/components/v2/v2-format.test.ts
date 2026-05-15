import { describe, expect, it } from 'vitest';
import {
  JOB_TYPE_OPTIONS,
  LOCATION_OPTIONS,
  SENIORITY_OPTIONS,
  formatEducationV2,
  formatJobTypeV2,
  formatLocationV2,
  formatSeniorityV2,
} from './v2-format';

describe('v2-format', () => {
  describe('formatLocationV2', () => {
    it('maps each location value to a Vietnamese label', () => {
      expect(formatLocationV2('Hà Nội')).toBe('Hà Nội');
      expect(formatLocationV2('TP. Hồ Chí Minh')).toBe('TP. Hồ Chí Minh');
      expect(formatLocationV2('Đà Nẵng')).toBe('Đà Nẵng');
    });
  });

  describe('formatJobTypeV2', () => {
    it('maps each job type value to a label', () => {
      expect(formatJobTypeV2('remote')).toBe('Remote');
      expect(formatJobTypeV2('fulltime')).toBe('Full-time');
      expect(formatJobTypeV2('parttime')).toBe('Part-time');
    });
  });

  describe('formatSeniorityV2', () => {
    it('covers all six seniority levels', () => {
      expect(formatSeniorityV2('intern')).toBe('Intern');
      expect(formatSeniorityV2('fresher')).toBe('Fresher');
      expect(formatSeniorityV2('junior')).toBe('Junior');
      expect(formatSeniorityV2('mid')).toBe('Mid-Level');
      expect(formatSeniorityV2('senior')).toBe('Senior');
      expect(formatSeniorityV2('lead')).toBe('Lead');
    });
  });

  describe('formatEducationV2', () => {
    it('maps the four education levels', () => {
      expect(formatEducationV2('high_school')).toBe('THPT');
      expect(formatEducationV2('bachelor')).toBe('Đại học');
      expect(formatEducationV2('master')).toBe('Thạc sĩ');
      expect(formatEducationV2('phd')).toBe('Tiến sĩ');
    });
  });

  describe('option lists', () => {
    it('LOCATION_OPTIONS has 3 entries with value+label', () => {
      expect(LOCATION_OPTIONS).toHaveLength(3);
      LOCATION_OPTIONS.forEach((o) => {
        expect(o).toHaveProperty('value');
        expect(o).toHaveProperty('label');
      });
    });

    it('JOB_TYPE_OPTIONS has 3 entries', () => {
      expect(JOB_TYPE_OPTIONS).toHaveLength(3);
    });

    it('SENIORITY_OPTIONS has 6 entries in canonical order', () => {
      expect(SENIORITY_OPTIONS.map((o) => o.value)).toEqual([
        'intern',
        'fresher',
        'junior',
        'mid',
        'senior',
        'lead',
      ]);
    });
  });
});
