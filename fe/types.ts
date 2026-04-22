

export interface Job {
  id: number;
  title: string;
  company: string;
  logo: string;
  salary: string;
  location: string;
  tags: string[]; // Used for matching keywords
  skills?: string[]; // Specific technical skills for matching
  experienceLevel?: string; // e.g., "Junior", "Senior"
  type?: string; // Full-time, Remote, etc.
  postedAt?: string;
  description?: string;
  requirements?: string[];
  benefits?: string[];
}

export interface Category {
  id: number;
  name: string;
  count: number;
  iconName: string;
}

export interface Company {
  id: number;
  name: string;
  logo: string;
  openPositions: number;
}

export interface Testimonial {
  id: number;
  name: string;
  role: string;
  avatar: string;
  content: string;
}

export interface UserCV {
  id: string;
  name: string;
  title: string;
  skills: string[];
  experienceLevel: string;
  location: string;
  lastUpdated: string;
  ownerId?: string;
  details?: any;
}

export interface MatchResult {
  score: number; // 0-100
  matchedSkills: string[];
  reason: string;
}

export interface JobWithMatch extends Job {
  match?: MatchResult;
}

// --- Recruiter Flow Types ---

export interface JobRequirement {
  id: string;
  title: string;
  skills: string[];
  experienceLevel: string;
  location: string;
  createdAt: string;
  openPositions: number;
  // Visual props for the UI
  criteriaList: string[]; // e.g. ["React, TypeScript", "3+ năm kinh nghiệm", "Hà Nội"]
  iconType: 'Code' | 'Megaphone' | 'Server' | 'PenTool'; 
  color: string; // Tailwind color class for bg, e.g. "bg-blue-500"
  ownerId?: string; // ID of the user who created this requirement
}

export interface Candidate {
  id: string;
  name: string;
  headline: string; // e.g. "Senior React Developer"
  avatar: string;
  location: string;
  skills: string[];
  experienceLevel: string; // e.g. "Senior", "Junior"
  yearsOfExperience: number;
  availability: string; // e.g. "Immediate", "2 weeks"
  education?: string;
}

export interface CandidateMatchResult {
  score: number;
  matchedSkills: string[];
  reason: string;
  detailScores?: {
    skills: number;
    experience: number;
    title: number;
    location: number;
    other: number;
  };
}

export interface CandidateWithMatch extends Candidate {
  match?: CandidateMatchResult;
}

// --- Search & Filter Types ---

export type ViewMode = 'grid' | 'list';
export type SortOption = 
  | 'relevance' 
  | 'newest' 
  | 'oldest' 
  | 'salary_high' 
  | 'salary_low'
  | 'exp_high' // Experience High to Low
  | 'exp_low'; // Experience Low to High

export interface FilterOption {
  label: string;
  value: string;
  count?: number;
}

export interface FilterGroup {
  id: string; // key for the filter, e.g. 'level', 'type'
  title: string;
  options: FilterOption[];
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface SearchResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface SearchState {
  q: string;
  location: string;
  filters: Record<string, string[]>;
  sort: SortOption;
  page: number;
}

// --- Auth Types ---

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role?: 'candidate' | 'recruiter' | 'admin';
  
  // Personal Info
  phone?: string;
  gender?: 'Male' | 'Female' | 'Other';
  birthday?: string;
  
  // Career Info
  currentPosition?: string;
  experienceLevel?: string;
  skills?: string[]; // For profile skills tags
  preferredLocation?: string;
  salaryRange?: string;
}

export interface AuthResponse {
  accessToken: string;
  user: User;
}

// --- DTOs ---

export interface CreateCvDto {
//  userId?: string;
  fullname: string;
  preferredName?: string;
  email?: string;
  phone?: string;
  headline?: string;
  avatarUrl?: string;
  location?: {
    city?: string;
    state?: string;
    country?: string;
  };
  summary?: string;
  targetRole?: string;
  salaryExpectation?: string;
  availability?: string;
  employmentType?: string[];
  skills?: {
    name: string;
    level?: string;
    category?: string;
    years?: number;
  }[];
  experiences?: {
    id?: string;
    title: string;
    company: string;
    companyWebsite?: string;
    location?: string;
    from?: string;
    to?: string;
    isCurrent?: boolean;
    employmentType?: string;
    teamSize?: number;
    responsibilities?: string[];
    achievements?: string[];
    tags?: string[];
  }[];
  education?: {
    school: string;
    degree: string;
    major: string;
    from?: string;
    to?: string;
    gpa?: string;
  }[];
  projects?: {
    name: string;
    description?: string;
    role?: string;
    from?: string;
    to?: string;
    techStack?: string[];
    url?: string;
    metrics?: string[];
  }[];
  certifications?: {
    name: string;
    issuer: string;
    issueDate: string;
    expiryDate?: string;
    credentialUrl?: string;
  }[];
  languages?: {
    name: string;
    level: string;
  }[];
  portfolio?: {
    type: string;
    url: string;
    description?: string;
  }[];
  references?: {
    name: string;
    relation?: string;
    contact?: string;
    note?: string;
  }[];
  tags?: string[];
}