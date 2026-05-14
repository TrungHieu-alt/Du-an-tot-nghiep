import api from '../../lib/api';
import { apiRoutes } from '../../lib/api-routes';
import type {
  NormalCVSearchItem,
  NormalCVSearchParams,
  CvExtractResponse,
  NormalCv,
  NormalCvCreatePayload,
  NormalCvUpdatePayload,
  NormalJob,
  NormalJobCreatePayload,
  NormalJobSearchItem,
  NormalJobSearchParams,
  NormalJobUpdatePayload,
  NormalSearchResponse,
} from '../../types';

const authHeaders = (token: string) => ({
  Authorization: `Bearer ${token}`,
});

const keyMapToCamel: Record<string, string> = {
  avatar_url: 'avatarUrl',
  preferred_name: 'preferredName',
  target_role: 'targetRole',
  occupation_group: 'occupationGroup',
  career_level: 'careerLevel',
  years_of_experience: 'yearsOfExperience',
  employment_type: 'employmentType',
  salary_expectation: 'salaryExpectation',
  normalized_name: 'normalizedName',
  tools_and_technologies: 'toolsAndTechnologies',
  domain_knowledge: 'domainKnowledge',
  company_id: 'companyId',
  company_name: 'companyName',
  company_logo_url: 'companyLogoUrl',
  company_website: 'companyWebsite',
  company_location: 'companyLocation',
  company_size: 'companySize',
  company_industry: 'companyIndustry',
  remote_type: 'remoteType',
  team_size: 'teamSize',
  nice_to_have: 'niceToHave',
  must_have_skills: 'mustHaveSkills',
  nice_to_have_skills: 'niceToHaveSkills',
  experience_years: 'experienceYears',
  education_level: 'educationLevel',
  required_education: 'requiredEducation',
  required_certifications: 'requiredCertifications',
  apply_url: 'applyUrl',
  apply_email: 'applyEmail',
  how_to_apply: 'howToApply',
  application_deadline: 'applicationDeadline',
  pre_screen_questions: 'preScreenQuestions',
  required_docs: 'requiredDocs',
  is_current: 'isCurrent',
  skills_used: 'skillsUsed',
  tools_used: 'toolsUsed',
  issue_date: 'issueDate',
  expiry_date: 'expiryDate',
  credential_url: 'credentialUrl',
  media_type: 'mediaType',
  uploaded_at: 'uploadedAt',
  archived: 'archived',
};

const keyMapToSnake = Object.fromEntries(
  Object.entries(keyMapToCamel).map(([snake, camel]) => [camel, snake])
) as Record<string, string>;

const mapKeys = (value: unknown, keyMap: Record<string, string>): unknown => {
  if (Array.isArray(value)) return value.map((item) => mapKeys(item, keyMap));
  if (value && typeof value === 'object' && !(value instanceof File) && !(value instanceof Date)) {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => [
        keyMap[key] ?? key,
        mapKeys(item, keyMap),
      ])
    );
  }
  return value;
};

const toCamelPayload = <T>(payload: T): T => mapKeys(payload, keyMapToCamel) as T;
const toSnakeResponse = <T>(payload: T): T => mapKeys(payload, keyMapToSnake) as T;

export async function searchJobs(
  params: NormalJobSearchParams
): Promise<NormalSearchResponse<NormalJobSearchItem>> {
  const response = await api.get<NormalSearchResponse<NormalJobSearchItem>>(
    apiRoutes.normalSearch.jobs(params)
  );
  return response.data;
}

export async function searchCvs(
  params: NormalCVSearchParams
): Promise<NormalSearchResponse<NormalCVSearchItem>> {
  const response = await api.get<NormalSearchResponse<NormalCVSearchItem>>(
    apiRoutes.normalSearch.cvs(params)
  );
  return response.data;
}

export async function createJob(token: string, payload: NormalJobCreatePayload): Promise<NormalJob> {
  const response = await api.post<NormalJob>(apiRoutes.job.create(), toCamelPayload(payload), {
    headers: authHeaders(token),
  });
  return toSnakeResponse(response.data);
}

export async function listMyJobs(token: string): Promise<NormalJob[]> {
  const response = await api.get<NormalJob[]>(apiRoutes.job.my(), {
    headers: authHeaders(token),
  });
  return toSnakeResponse(response.data);
}

export async function getJob(jobId: string, token?: string | null): Promise<NormalJob> {
  const response = await api.get<NormalJob>(apiRoutes.job.byId(jobId), {
    headers: token ? authHeaders(token) : undefined,
  });
  return toSnakeResponse(response.data);
}

export async function updateJob(
  token: string,
  jobId: string,
  payload: NormalJobUpdatePayload
): Promise<NormalJob> {
  const response = await api.put<NormalJob>(apiRoutes.job.byId(jobId), toCamelPayload(payload), {
    headers: authHeaders(token),
  });
  return toSnakeResponse(response.data);
}

export async function deleteJob(token: string, jobId: string): Promise<void> {
  await api.delete(apiRoutes.job.byId(jobId), {
    headers: authHeaders(token),
  });
}

export async function createCv(token: string, payload: NormalCvCreatePayload): Promise<NormalCv> {
  const response = await api.post<NormalCv>(apiRoutes.cv.create(), toCamelPayload(payload), {
    headers: authHeaders(token),
  });
  return toSnakeResponse(response.data);
}

export async function uploadCvPdf(
  token: string,
  file: File,
  fullname?: string
): Promise<NormalCv> {
  const form = new FormData();
  form.append('file', file);
  if (fullname) form.append('fullname', fullname);
  const response = await api.post<NormalCv>(apiRoutes.cv.upload(), form, {
    headers: {
      ...authHeaders(token),
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function extractCvPdf(token: string, file: File): Promise<CvExtractResponse> {
  const form = new FormData();
  form.append('file', file);
  const response = await api.post<CvExtractResponse>(apiRoutes.cv.extractPdf(), form, {
    headers: {
      ...authHeaders(token),
      'Content-Type': 'multipart/form-data',
    },
  });
  return toSnakeResponse(response.data);
}

export async function listMyCvs(token: string): Promise<NormalCv[]> {
  const response = await api.get<NormalCv[]>(apiRoutes.cv.my(), {
    headers: authHeaders(token),
  });
  return toSnakeResponse(response.data);
}

export async function getCv(token: string | null | undefined, cvId: string): Promise<NormalCv> {
  const response = await api.get<NormalCv>(apiRoutes.cv.byId(cvId), {
    headers: token ? authHeaders(token) : undefined,
  });
  return toSnakeResponse(response.data);
}

export async function updateCv(
  token: string,
  cvId: string,
  payload: NormalCvUpdatePayload
): Promise<NormalCv> {
  const response = await api.put<NormalCv>(apiRoutes.cv.byId(cvId), toCamelPayload(payload), {
    headers: authHeaders(token),
  });
  return toSnakeResponse(response.data);
}

export async function deleteCv(token: string, cvId: string): Promise<void> {
  await api.delete(apiRoutes.cv.byId(cvId), {
    headers: authHeaders(token),
  });
}
