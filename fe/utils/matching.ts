
import { Job, UserCV, MatchResult } from '../types';

/**
 * Client-side demo implementation of weighted matching.
 * Weights: Skills 50%, Title 20%, Experience 15%, Location 10%, Keywords 5%
 */
export const calculateMatch = (job: Job, cv: UserCV): MatchResult => {
  if (!cv) {
    return {
      score: 0,
      matchedSkills: [],
      reason: 'Missing CV data'
    };
  }

  let score = 0;
  const weights = {
    skills: 50,
    title: 20,
    experience: 15,
    location: 10,
    tags: 5
  };

  // Safe accessors for CV properties which might be undefined from API
  const cvSkillsRaw = cv.skills || [];
  const cvSkills = Array.isArray(cvSkillsRaw) 
    ? cvSkillsRaw.map(s => typeof s === 'string' ? s.toLowerCase() : '')
    : [];
  
  const cvTitle = (cv.title || '').toLowerCase();
  const cvLocation = (cv.location || '');
  const cvExpLevel = (cv.experienceLevel || '');

  // 1. Skill Matching (50%)
  // Normalize skills to lowercase for comparison
  const jobSkills = (job.skills || []).map(s => s.toLowerCase());
  
  const matchedSkills = jobSkills.filter(skill => cvSkills.includes(skill));
  
  if (jobSkills.length > 0) {
    const skillMatchRatio = matchedSkills.length / jobSkills.length;
    score += skillMatchRatio * weights.skills;
  } else {
    // If job has no specific skills listed, give partial credit if title matches
    score += weights.skills * 0.5; 
  }

  // 2. Title Fuzzy Match (20%)
  const jobTitle = job.title.toLowerCase();
  
  if (cvTitle && (jobTitle.includes(cvTitle) || cvTitle.includes(jobTitle))) {
    score += weights.title;
  }

  // 3. Experience Match (15%)
  // Simple equality check for demo
  if (job.experienceLevel === cvExpLevel) {
    score += weights.experience;
  }

  // 4. Location Match (10%)
  if (cvLocation && (job.location.includes(cvLocation) || cvLocation.includes(job.location))) {
    score += weights.location;
  }

  // 5. Tag/Keyword Match (5%)
  const jobTags = (job.tags || []).map(t => t.toLowerCase());
  const matchedTags = jobTags.filter(t => cvSkills.includes(t) || cvTitle.includes(t));
  if (matchedTags.length > 0) {
    score += weights.tags;
  }

  return {
    score: Math.min(Math.round(score), 100),
    matchedSkills: matchedSkills,
    reason: matchedSkills.length > 0 
      ? `Phù hợp ${matchedSkills.length} kỹ năng: ${matchedSkills.slice(0, 3).join(', ')}${matchedSkills.length > 3 ? '...' : ''}`
      : 'Phù hợp dựa trên hồ sơ tổng quát'
  };
};

// Mock CV Data for the demo (Fallback)
export const MOCK_CVS: UserCV[] = [
  {
    id: 'cv_1',
    name: 'Frontend Developer CV',
    title: 'Frontend Developer',
    skills: ['React', 'TypeScript', 'Tailwind', 'HTML', 'CSS', 'JavaScript'],
    experienceLevel: 'Senior',
    location: 'Hà Nội',
    lastUpdated: '2 ngày trước'
  },
  {
    id: 'cv_2',
    name: 'Marketing Profile',
    title: 'Marketing Manager',
    skills: ['SEO', 'Content Marketing', 'Google Ads', 'Social Media'],
    experienceLevel: 'Mid-Level',
    location: 'Hồ Chí Minh',
    lastUpdated: '1 tuần trước'
  },
  {
    id: 'cv_3',
    name: 'Fresher IT',
    title: 'Intern Developer',
    skills: ['Java', 'Basic HTML'],
    experienceLevel: 'Junior',
    location: 'Đà Nẵng',
    lastUpdated: 'Vừa xong'
  }
];
