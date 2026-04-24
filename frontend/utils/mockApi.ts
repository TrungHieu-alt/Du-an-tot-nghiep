
import { JobWithMatch, CandidateWithMatch, SearchState, SearchResponse, UserCV, JobRequirement, Job, Candidate } from '../types';
import api from '../lib/api';
import { calculateCandidateMatch, MOCK_REQUIREMENTS } from './matchingCandidates';

// --- Helpers ---

const formatSalary = (salary: any): string => {
  if (!salary) return "Thỏa thuận";
  if (typeof salary === 'string') return salary;
  if (typeof salary === 'object') {
    const min = salary.min;
    const max = salary.max;
    const currency = salary.currency || '';
    if (min !== undefined && max !== undefined) return `${min.toLocaleString()} - ${max.toLocaleString()} ${currency}`;
    if (min !== undefined) return `Từ ${min.toLocaleString()} ${currency}`;
    if (max !== undefined) return `Đến ${max.toLocaleString()} ${currency}`;
  }
  return "Thỏa thuận";
};

const formatTimeAgo = (dateInput: string | Date | undefined) => {
  if (!dateInput) return "Vừa xong";
  const date = new Date(dateInput);
  const now = new Date();
  const diff = (now.getTime() - date.getTime()) / 1000; // seconds
  
  if (diff < 60) return "Vừa xong";
  if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`;
  if (diff < 2592000) return `${Math.floor(diff / 86400)} ngày trước`;
  return date.toLocaleDateString('vi-VN');
};

// Helper to extract fields from RAG text preview
const extractFieldFromPreview = (text: string, label: string): string => {
  if (!text) return '';
  // Regex to look for "Label: Value" pattern, case insensitive, stopping at new line
  const regex = new RegExp(`${label}:\\s*([^\\n]+)`, 'i');
  const match = text.match(regex);
  return match ? match[1].trim() : '';
};

// --- API Functions ---

export const searchJobsApi = async (
  params: SearchState, 
  cvId?: string
): Promise<SearchResponse<JobWithMatch>> => {
  try {
    let rawItems: any[] = [];
    let meta = {
      page: params.page || 1,
      limit: 10,
      total: 0,
      totalPages: 0
    };
    
    // 1. MATCHING MODE: If a CV is selected, call the RAG endpoint
    if (cvId) {
      try {
        const matchParams = {
          page: params.page || 1,
          limit: 10,
          topK: 50, // Specific requirement
        };

        // Call the new RAG Match Endpoint
        const response = await api.get(`/rag/match-all-jobs-for-cv-doc/${cvId}`, { params: matchParams });
        const payload = response.data;

        // Check for matches array in the new response structure
        if (payload.matches && Array.isArray(payload.matches)) {
          rawItems = payload.matches;
          meta.total = Number(payload.totalItems || rawItems.length);
          meta.totalPages = Number(payload.totalPages || Math.ceil(meta.total / 10));

          // Map RAG Matching Response -> JobWithMatch
          const jobs: JobWithMatch[] = rawItems.map((match: any) => {
            const previewText = match.textPreview || '';
            
            // Extract details from text preview to populate UI card
            // Common patterns in the preview text: "Location: ...", "Salary: ...", "Seniority: ..."
            const extractedLocation = extractFieldFromPreview(previewText, 'Location');
            const extractedSeniority = extractFieldFromPreview(previewText, 'Seniority');
            const extractedDepartment = extractFieldFromPreview(previewText, 'Department');
            const extractedSalary = extractFieldFromPreview(previewText, 'Salary');
            
            // Try to extract skills from text if possible (e.g., "Skills: nodejs, javascript")
            const extractedSkillsStr = extractFieldFromPreview(previewText, 'Skills');
            const extractedSkills = extractedSkillsStr 
              ? extractedSkillsStr.split(',').map(s => s.trim()) 
              : [];

            return {
              id: match.jobId,
              title: match.jobTitle || "Công việc không tên",
              company: match.companyName || "Công ty ẩn danh",
              // Generate a consistent placeholder logo based on company name
              logo: `https://ui-avatars.com/api/?name=${encodeURIComponent(match.companyName || 'Job')}&background=random&color=fff`,
              
              salary: extractedSalary || "Thỏa thuận",
              location: extractedLocation || "Việt Nam",
              
              tags: extractedDepartment ? [extractedDepartment] : [],
              skills: extractedSkills,
              
              experienceLevel: extractedSeniority || "",
              type: "", // Not explicitly in top level RAG response usually
              postedAt: "Vừa xong", // RAG response doesn't usually have date, assume fresh
              
              description: previewText, // Use the full preview as description
              requirements: [],
              benefits: [],
              
              match: {
                score: match.score || 0, 
                matchedSkills: [], 
                reason: previewText // Use the AI generated preview as the explanation
              }
            };
          });

          return { data: jobs, meta };
        }
      } catch (error: any) {
        console.error("Error fetching matched jobs from RAG:", error);
        // Return empty on error to prevent crash
        return { data: [], meta: { page: 1, limit: 10, total: 0, totalPages: 0 } };
      }
    }

    // 2. STANDARD SEARCH MODE (No CV selected)
    const queryParams: any = {
      page: params.page || 1,
      limit: 10,
      search: params.q || undefined,
    };

    if (params.sort === 'oldest') {
      queryParams.sort = 'oldest';
    } else {
      queryParams.sort = 'latest';
    }

    if (params.filters) {
       if (params.filters.companyId && params.filters.companyId.length > 0) {
         queryParams.companyId = params.filters.companyId[0];
       }
       if (params.filters.userId && params.filters.userId.length > 0) {
         queryParams.userId = params.filters.userId[0];
       }
    }

    const response = await api.get('/jobs', { params: queryParams });
    const payload = response.data;

    rawItems = [];
    if (payload.items && Array.isArray(payload.items)) {
        rawItems = payload.items;
        meta = {
            page: Number(payload.page),
            limit: Number(payload.limit),
            total: Number(payload.total),
            totalPages: Number(payload.pages || Math.ceil(payload.total / payload.limit))
        };
    } else if (Array.isArray(payload)) {
        rawItems = payload;
        meta.total = rawItems.length;
        meta.totalPages = 1;
    } else if (payload.data && Array.isArray(payload.data)) {
        rawItems = payload.data;
        meta.total = payload.total || rawItems.length;
    }

    const jobs: JobWithMatch[] = rawItems.map((item: any) => {
       const skills = Array.isArray(item.skills)
         ? item.skills.map((s: any) => typeof s === 'string' ? s : s.name).filter(Boolean)
         : [];

       return {
         id: item._id || item.id,
         title: item.title || "Công việc không tên",
         company: item.companyName || "Công ty ẩn danh",
         logo: item.companyLogoUrl || `https://ui-avatars.com/api/?name=${encodeURIComponent(item.companyName || 'C')}&background=random`,
         salary: formatSalary(item.salary),
         location: item.companyLocation || item.location?.city || (typeof item.location === 'string' ? item.location : "Việt Nam"),
         tags: item.tags || [],
         skills: skills,
         experienceLevel: item.seniority || item.experienceLevel || "",
         type: Array.isArray(item.employmentType) ? item.employmentType.join(', ') : (item.employmentType || ""),
         postedAt: formatTimeAgo(item.createdAt || item.updatedAt),
         description: item.description,
         requirements: item.requirements || [],
         benefits: item.benefits || [],
         match: undefined 
       };
    });

    return { data: jobs, meta };

  } catch (error) {
    console.error("fetch jobs error", error);
    return { data: [], meta: { page: 1, limit: 10, total: 0, totalPages: 0 } };
  }
};


export const searchCandidatesApi = async (
  params: SearchState,
  reqId?: string
): Promise<SearchResponse<CandidateWithMatch>> => {
  try {
    let rawList: any[] = [];
    let meta = {
        page: params.page || 1,
        limit: 10,
        total: 0,
        totalPages: 0
    };

    // 1. MATCHING MODE: If Requirement ID is present
    if (reqId) {
      try {
        const matchParams = {
          page: params.page || 1,
          limit: 10,
          topK: 50 // New Requirement
        };
        
        // Call the new RAG Match Endpoint for Candidates
        const response = await api.get(`/rag/match-all-cvs-for-job-doc/${reqId}`, { params: matchParams });
        const payload = response.data;

        if (payload.matches && Array.isArray(payload.matches)) {
           rawList = payload.matches;
           meta.total = Number(payload.totalItems || rawList.length);
           meta.totalPages = Number(payload.totalPages || Math.ceil(meta.total / 10));

           const candidates: CandidateWithMatch[] = rawList.map((match: any) => {
             const textPreview = match.textPreview || '';
             
             // Extract helpers for preview text parsing
             const extract = (label: string) => {
                const regex = new RegExp(`${label}:\\s*([^\\n]+)`, 'i');
                const m = textPreview.match(regex);
                return m ? m[1].trim() : '';
             };

             const targetRole = extract('Target role');
             const skillsStr = extract('Skills');
             const skills = skillsStr 
                ? skillsStr.split(',').map((s:string) => s.trim()).filter(Boolean)
                : [];

             // Heuristic: Extract years like "2y", "5 năm" from the whole text or Skills section
             let yearsOfExperience = 0;
             const expMatch = textPreview.match(/(\d+)\s*(?:y|năm|year)/i);
             if (expMatch) {
               yearsOfExperience = parseInt(expMatch[1], 10);
             }

             // Heuristic: Level
             let experienceLevel = "Mid-Level";
             const lowerText = textPreview.toLowerCase();
             if (yearsOfExperience >= 5 || lowerText.includes('senior')) experienceLevel = "Senior";
             else if (yearsOfExperience <= 1 || lowerText.includes('fresher') || lowerText.includes('intern')) experienceLevel = "Junior";

             return {
               id: match.cvId,
               name: match.fullname || "Ứng viên",
               headline: targetRole || extract('Headline') || "Open to work",
               avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(match.fullname || 'U')}&background=random`,
               location: extract('Location') || "Việt Nam",
               skills: skills,
               experienceLevel: experienceLevel,
               yearsOfExperience: yearsOfExperience,
               availability: "Sẵn sàng",
               education: extract('Education'),
               match: {
                 score: match.score || 0,
                 matchedSkills: [],
                 reason: textPreview // Use preview as match reason
               }
             };
           });
           
           return { data: candidates, meta };
        }
      } catch (error: any) {
        console.warn("Candidate RAG matching endpoint failed, falling back to standard search", error);
        // Fallback proceeds below to standard search
      }
    }

    // 2. STANDARD SEARCH MODE (No Req selected or fallback)
    const queryParams: any = {
      page: params.page || 1,
      limit: 10,
      search: params.q || undefined,
    };

    if (params.sort === 'oldest') {
      queryParams.sort = 'oldest';
    } else {
      queryParams.sort = 'latest';
    }
    
    const response = await api.get('/cv', { params: queryParams });
    const payload = response.data;

    if (payload.items && Array.isArray(payload.items)) {
        rawList = payload.items;
        meta = {
            page: Number(payload.page),
            limit: Number(payload.limit),
            total: Number(payload.total),
            totalPages: Number(payload.pages || Math.ceil(payload.total / payload.limit))
        };
    } else if (Array.isArray(payload)) {
        rawList = payload;
        meta.total = rawList.length;
        meta.totalPages = 1;
    } else if (payload.data && Array.isArray(payload.data)) {
         rawList = payload.data;
         meta.total = payload.total || rawList.length;
    }

    let candidates: CandidateWithMatch[] = rawList.map((item: any) => {
       const skills = Array.isArray(item.skills)
         ? item.skills.map((s: any) => typeof s === 'string' ? s : s.name).filter(Boolean)
         : [];

       let yearsOfExperience = 0;
       if (typeof item.experienceYears === 'number') {
           yearsOfExperience = item.experienceYears;
       } else if (Array.isArray(item.experiences)) {
           yearsOfExperience = item.experiences.length > 0 ? item.experiences.length : 0;
       }

       let experienceLevel = item.experienceLevel || "Fresher";
       if (yearsOfExperience >= 5) experienceLevel = "Senior";
       else if (yearsOfExperience >= 2) experienceLevel = "Mid-Level";
       else if (yearsOfExperience >= 1) experienceLevel = "Junior";
       else if (yearsOfExperience === 0 && Array.isArray(item.employmentType) && item.employmentType.includes('Intern')) experienceLevel = "Intern";
       
       return {
         id: item._id || item.id,
         name: item.fullname || item.name || "Ứng viên",
         headline: item.headline || item.targetRole || "Open to work",
         avatar: item.avatarUrl || `https://ui-avatars.com/api/?name=${encodeURIComponent(item.fullname || 'User')}&background=random`,
         location: item.location?.city || (typeof item.location === 'string' ? item.location : "") || "Việt Nam",
         skills: skills,
         experienceLevel,
         yearsOfExperience,
         availability: item.availability || "Sẵn sàng",
         education: item.education?.[0]?.school
       };
    });

    // Client-side fallback matching if API didn't return match data but reqId exists
    // (This runs only if the API call in Step 1 failed or returned no items, but we got raw items from Step 2)
    if (reqId && !rawList.length && candidates.length) {
        let req = MOCK_REQUIREMENTS.find(r => r.id === reqId);
        if (!req) {
            try {
               const stored = JSON.parse(localStorage.getItem('demo_requirements') || '[]');
               req = stored.find((r: any) => r.id === reqId);
            } catch (e) {}
        }
        
        if (req) {
            candidates = candidates.map(c => {
               const match = calculateCandidateMatch(req!, c);
               return { ...c, match };
            });

            if (params.sort === 'relevance') {
                candidates.sort((a, b) => (b.match?.score || 0) - (a.match?.score || 0));
            }
        }
    }

    return {
      data: candidates,
      meta
    };

  } catch (error) {
    console.error("searchCandidatesApi failed:", error);
    return { data: [], meta: { page: 1, limit: 10, total: 0, totalPages: 0 } };
  }
};

export const createRequirement = async (req: JobRequirement): Promise<JobRequirement> => {
  const response = await api.post('/requirements', req);
  return response.data;
};

export const updateRequirement = async (id: string, payload: Partial<JobRequirement>): Promise<JobRequirement> => {
  const response = await api.put(`/requirements/${id}`, payload);
  return response.data;
};

export const deleteRequirement = async (id: string): Promise<boolean> => {
  const response = await api.delete(`/requirements/${id}`);
  return response.status === 200;
};

// --- User CV CRUD ---

export const createCv = async (cv: UserCV): Promise<UserCV> => {
  const response = await api.post('/cvs', cv);
  return response.data;
};

export const updateCv = async (id: string, payload: Partial<UserCV>): Promise<UserCV> => {
  const response = await api.put(`/cvs/${id}`, payload);
  return response.data;
};

export const deleteCv = async (id: string): Promise<boolean> => {
  const response = await api.delete(`/cvs/${id}`);
  return response.status === 200;
};

// --- Chatbot API ---
export const sendChatMessage = async (message: string): Promise<string> => {
  try {
    const response = await api.post('/rag/ask', { question: message });
    return response.data?.answer || "Tôi không tìm thấy câu trả lời phù hợp.";
  } catch (error) {
    console.error("Chatbot API error:", error);
    return "Xin lỗi, hệ thống đang gặp sự cố kết nối. Vui lòng thử lại sau.";
  }
};
