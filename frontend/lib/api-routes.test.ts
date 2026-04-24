import { describe, expect, it } from 'vitest';
import { apiRoutes } from './api-routes';

describe('apiRoutes', () => {
  it('builds canonical routes for core domains', () => {
    expect(apiRoutes.users.login()).toBe('/users/login');
    expect(apiRoutes.users.byId(12)).toBe('/users/12');
    expect(apiRoutes.cv.create('99')).toBe('/cv/create/99');
    expect(apiRoutes.jobs.byRecruiter('7')).toBe('/jobs/recruiter/7');
    const route = apiRoutes.jobs.matchCvDetail('101', '202');
    expect(route).toContain('/jobs/match/101/');
    expect(route).toContain('/202');
  });
});
