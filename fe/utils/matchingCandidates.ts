
import { Candidate, JobRequirement, CandidateMatchResult } from '../types';

/**
 * Client-side demo matching algorithm for candidates.
 * Weights:
 * - Skills overlap: 55%
 * - Experience level: 15%
 * - Title similarity: 10%
 * - Location: 10%
 * - Other (Availability/Keywords): 10%
 */
export const calculateCandidateMatch = (req: JobRequirement, candidate: Candidate): CandidateMatchResult => {
  const weights = {
    skills: 55,
    experience: 15,
    title: 10,
    location: 10,
    other: 10
  };

  let totalScore = 0;
  const detailScores = { skills: 0, experience: 0, title: 0, location: 0, other: 0 };

  // 1. Skills Overlap (55%)
  const reqSkills = req.skills.map(s => s.toLowerCase());
  const candSkills = candidate.skills.map(s => s.toLowerCase());
  const matchedSkills = reqSkills.filter(s => candSkills.includes(s));
  
  if (reqSkills.length > 0) {
    const skillRatio = matchedSkills.length / reqSkills.length;
    detailScores.skills = skillRatio * weights.skills;
  } else {
    detailScores.skills = weights.skills * 0.5; // Fallback
  }
  totalScore += detailScores.skills;

  // 2. Experience Level (15%)
  if (req.experienceLevel === candidate.experienceLevel) {
    detailScores.experience = weights.experience;
  } else if (req.experienceLevel === 'Junior' && candidate.experienceLevel === 'Senior') {
    detailScores.experience = weights.experience; 
  } else if (req.experienceLevel === 'Mid-Level' && candidate.experienceLevel === 'Senior') {
     detailScores.experience = weights.experience;
  } else {
    detailScores.experience = 0;
  }
  totalScore += detailScores.experience;

  // 3. Title Similarity (10%)
  const reqTitle = req.title.toLowerCase();
  const candHeadline = candidate.headline.toLowerCase();
  if (candHeadline.includes(reqTitle) || reqTitle.includes(candHeadline)) {
    detailScores.title = weights.title;
  }
  totalScore += detailScores.title;

  // 4. Location (10%)
  if (req.location.includes(candidate.location) || candidate.location.includes(req.location) || candidate.location === 'Remote') {
    detailScores.location = weights.location;
  }
  totalScore += detailScores.location;

  // 5. Other / Availability (10%)
  if (candidate.availability === 'Immediate') {
    detailScores.other = weights.other;
  } else {
    detailScores.other = weights.other / 2;
  }
  totalScore += detailScores.other;

  // Generate Human Readable Reason
  let reason = "";
  if (matchedSkills.length >= 3) {
    reason = `Skills matched: ${matchedSkills.slice(0, 3).join(', ')}`;
  } else if (detailScores.title > 0) {
    reason = `Title matched: ${candidate.headline}`;
  } else if (detailScores.experience > 0) {
    reason = `Experience level matched: ${candidate.experienceLevel}`;
  } else {
    reason = "General profile match";
  }

  return {
    score: Math.min(Math.round(totalScore), 100),
    matchedSkills: reqSkills.filter(s => candSkills.includes(s)), 
    reason,
    detailScores
  };
};

// --- Mock Data Enriched for UI ---

export const MOCK_REQUIREMENTS: JobRequirement[] = [
  {
    id: 'req_1',
    title: 'Frontend React Developer',
    skills: ['React', 'TypeScript', 'Tailwind CSS', 'Redux'],
    experienceLevel: 'Senior',
    location: 'Hà Nội',
    createdAt: '2 days ago',
    openPositions: 2,
    iconType: 'Code',
    color: 'bg-blue-500',
    criteriaList: [
      "React, TypeScript, Tailwind",
      "3+ năm kinh nghiệm",
      "Hà Nội hoặc Remote",
      "Lương $1500 - $2500",
      "Full-time"
    ]
  },
  {
    id: 'req_2',
    title: 'Marketing Executive',
    skills: ['Social Media', 'Content Writing', 'English', 'SEO'],
    experienceLevel: 'Junior',
    location: 'Hồ Chí Minh',
    createdAt: '1 week ago',
    openPositions: 1,
    iconType: 'Megaphone',
    color: 'bg-rose-500',
    criteriaList: [
      "Content Writing, SEO, Social",
      "1+ năm kinh nghiệm",
      "Hồ Chí Minh",
      "Lương 12 - 18 triệu",
      "Full-time"
    ]
  },
  {
    id: 'req_3',
    title: 'Backend Engineer',
    skills: ['Node.js', 'MongoDB', 'Docker', 'AWS'],
    experienceLevel: 'Mid-Level',
    location: 'Remote',
    createdAt: '3 days ago',
    openPositions: 3,
    iconType: 'Server',
    color: 'bg-indigo-500',
    criteriaList: [
      "Node.js, MongoDB, AWS",
      "2+ năm kinh nghiệm",
      "Remote",
      "Lương $2000+",
      "Contract / Full-time"
    ]
  },
  {
    id: 'req_4',
    title: 'UI/UX Designer',
    skills: ['Figma', 'Adobe XD', 'User Research'],
    experienceLevel: 'Mid-Level',
    location: 'Hà Nội',
    createdAt: '5 days ago',
    openPositions: 1,
    iconType: 'PenTool',
    color: 'bg-purple-500',
    criteriaList: [
      "Figma, Adobe Suite",
      "Portfolio bắt buộc",
      "Hà Nội",
      "Lương 15 - 25 triệu",
      "Full-time"
    ]
  }
];

export const MOCK_CANDIDATES: Candidate[] = [
  {
    id: 'c_1',
    name: 'Nguyễn Văn A',
    headline: 'Senior Frontend Developer',
    avatar: 'https://images.unsplash.com/photo-1599566150163-29194dcaad36?w=100&h=100&fit=crop',
    location: 'Hà Nội',
    skills: ['React', 'TypeScript', 'Tailwind CSS', 'Redux', 'Next.js'],
    experienceLevel: 'Senior',
    yearsOfExperience: 5,
    availability: 'Immediate'
  },
  {
    id: 'c_2',
    name: 'Trần Thị B',
    headline: 'Marketing Specialist',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop',
    location: 'Hồ Chí Minh',
    skills: ['Social Media', 'Content Writing', 'SEO', 'Canva'],
    experienceLevel: 'Junior',
    yearsOfExperience: 2,
    availability: '2 weeks'
  },
  {
    id: 'c_3',
    name: 'Le Van C',
    headline: 'Full Stack Developer',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop',
    location: 'Đà Nẵng',
    skills: ['React', 'Node.js', 'MongoDB', 'Express'],
    experienceLevel: 'Mid-Level',
    yearsOfExperience: 3,
    availability: '1 month'
  },
  {
    id: 'c_4',
    name: 'Pham D',
    headline: 'Senior React Native Dev',
    avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop',
    location: 'Remote',
    skills: ['React', 'React Native', 'JavaScript', 'TypeScript'],
    experienceLevel: 'Senior',
    yearsOfExperience: 6,
    availability: 'Immediate'
  }
];