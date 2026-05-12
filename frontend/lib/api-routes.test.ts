import { describe, expect, it } from 'vitest';
import { apiRoutes } from './api-routes';

describe('apiRoutes', () => {
  it('exposes only auth, system and v2 route builders', () => {
    expect(Object.keys(apiRoutes).sort()).toEqual(['auth', 'system', 'v2']);
  });

  describe('auth', () => {
    it('returns canonical auth endpoints', () => {
      expect(apiRoutes.auth.register()).toBe('/auth/register');
      expect(apiRoutes.auth.login()).toBe('/auth/login');
      expect(apiRoutes.auth.me()).toBe('/auth/me');
    });
  });

  describe('v2 catalog', () => {
    it('jobs() omits query string when no params given', () => {
      expect(apiRoutes.v2.catalog.jobs()).toBe('/v2/prototype/catalog/jobs');
      expect(apiRoutes.v2.catalog.jobs({})).toBe('/v2/prototype/catalog/jobs');
    });

    it('jobs() emits limit and offset', () => {
      expect(apiRoutes.v2.catalog.jobs({ limit: 25, offset: 50 })).toBe(
        '/v2/prototype/catalog/jobs?limit=25&offset=50'
      );
    });

    it('jobs() supports partial pagination', () => {
      expect(apiRoutes.v2.catalog.jobs({ limit: 10 })).toBe(
        '/v2/prototype/catalog/jobs?limit=10'
      );
      expect(apiRoutes.v2.catalog.jobs({ offset: 5 })).toBe(
        '/v2/prototype/catalog/jobs?offset=5'
      );
    });

    it('jobs() preserves explicit zero offset', () => {
      expect(apiRoutes.v2.catalog.jobs({ limit: 10, offset: 0 })).toBe(
        '/v2/prototype/catalog/jobs?limit=10&offset=0'
      );
    });

    it('cvs() mirrors jobs() behaviour', () => {
      expect(apiRoutes.v2.catalog.cvs()).toBe('/v2/prototype/catalog/cvs');
      expect(apiRoutes.v2.catalog.cvs({ limit: 5, offset: 0 })).toBe(
        '/v2/prototype/catalog/cvs?limit=5&offset=0'
      );
    });

    it('detail builders encode integer IDs', () => {
      expect(apiRoutes.v2.catalog.jobById(4001)).toBe(
        '/v2/prototype/catalog/jobs/4001'
      );
      expect(apiRoutes.v2.catalog.cvById(3001)).toBe(
        '/v2/prototype/catalog/cvs/3001'
      );
    });
  });

  describe('v2 catalog search', () => {
    it('searchJobs returns the canonical search endpoint', () => {
      expect(apiRoutes.v2.catalog.searchJobs()).toBe(
        '/v2/prototype/catalog/jobs/search'
      );
    });

    it('searchCvs returns the canonical search endpoint', () => {
      expect(apiRoutes.v2.catalog.searchCvs()).toBe(
        '/v2/prototype/catalog/cvs/search'
      );
    });
  });

  describe('v2 matching', () => {
    it('runForJob points to the prototype job endpoint', () => {
      expect(apiRoutes.v2.matching.runForJob(4001)).toBe(
        '/v2/prototype/matching/job/4001/run'
      );
    });

    it('runForCv points to the prototype cv endpoint', () => {
      expect(apiRoutes.v2.matching.runForCv(3001)).toBe(
        '/v2/prototype/matching/cv/3001/run'
      );
    });
  });
});
