export interface NormalOption {
  value: string;
  label: string;
  industry?: string;
}

export const INDUSTRY_OPTIONS: NormalOption[] = [
  { value: 'information_technology', label: 'Information Technology' },
  { value: 'accounting_finance', label: 'Accounting & Finance' },
  { value: 'sales', label: 'Sales' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'human_resources', label: 'Human Resources' },
  { value: 'education', label: 'Education' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'engineering_construction', label: 'Engineering & Construction' },
  { value: 'design_creative', label: 'Design & Creative' },
  { value: 'customer_service', label: 'Customer Service' },
  { value: 'operations', label: 'Operations' },
  { value: 'logistics_supply_chain', label: 'Logistics & Supply Chain' },
  { value: 'hospitality_tourism', label: 'Hospitality & Tourism' },
  { value: 'legal', label: 'Legal' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'retail', label: 'Retail' },
  { value: 'other', label: 'Other' },
  { value: 'unknown', label: 'Unknown' },
];

export const OCCUPATION_GROUP_OPTIONS: NormalOption[] = [
  { value: 'software_engineering', label: 'Software Engineering', industry: 'information_technology' },
  { value: 'data_ai', label: 'Data & AI', industry: 'information_technology' },
  { value: 'it_support', label: 'IT Support', industry: 'information_technology' },
  { value: 'cybersecurity', label: 'Cybersecurity', industry: 'information_technology' },
  { value: 'devops_cloud', label: 'DevOps & Cloud', industry: 'information_technology' },
  { value: 'accountant', label: 'Accountant', industry: 'accounting_finance' },
  { value: 'auditor', label: 'Auditor', industry: 'accounting_finance' },
  { value: 'financial_analyst', label: 'Financial Analyst', industry: 'accounting_finance' },
  { value: 'tax_specialist', label: 'Tax Specialist', industry: 'accounting_finance' },
  { value: 'sales_executive', label: 'Sales Executive', industry: 'sales' },
  { value: 'business_development', label: 'Business Development', industry: 'sales' },
  { value: 'account_manager', label: 'Account Manager', industry: 'sales' },
  { value: 'digital_marketing', label: 'Digital Marketing', industry: 'marketing' },
  { value: 'content_marketing', label: 'Content Marketing', industry: 'marketing' },
  { value: 'seo_sem', label: 'SEO / SEM', industry: 'marketing' },
  { value: 'brand_marketing', label: 'Brand Marketing', industry: 'marketing' },
  { value: 'hr_recruitment', label: 'HR & Recruitment', industry: 'human_resources' },
  { value: 'compensation_benefits', label: 'Compensation & Benefits', industry: 'human_resources' },
  { value: 'training_development', label: 'Training & Development', industry: 'human_resources' },
  { value: 'teacher', label: 'Teacher', industry: 'education' },
  { value: 'lecturer', label: 'Lecturer', industry: 'education' },
  { value: 'academic_advisor', label: 'Academic Advisor', industry: 'education' },
  { value: 'doctor', label: 'Doctor', industry: 'healthcare' },
  { value: 'nurse', label: 'Nurse', industry: 'healthcare' },
  { value: 'pharmacist', label: 'Pharmacist', industry: 'healthcare' },
  { value: 'medical_technician', label: 'Medical Technician', industry: 'healthcare' },
  { value: 'civil_engineer', label: 'Civil Engineer', industry: 'engineering_construction' },
  { value: 'mechanical_engineer', label: 'Mechanical Engineer', industry: 'engineering_construction' },
  { value: 'electrical_engineer', label: 'Electrical Engineer', industry: 'engineering_construction' },
  { value: 'architect', label: 'Architect', industry: 'engineering_construction' },
  { value: 'graphic_designer', label: 'Graphic Designer', industry: 'design_creative' },
  { value: 'ui_ux_designer', label: 'UI/UX Designer', industry: 'design_creative' },
  { value: 'video_editor', label: 'Video Editor', industry: 'design_creative' },
  { value: 'customer_support', label: 'Customer Support', industry: 'customer_service' },
  { value: 'call_center_agent', label: 'Call Center Agent', industry: 'customer_service' },
  { value: 'operations_staff', label: 'Operations Staff', industry: 'operations' },
  { value: 'operations_manager', label: 'Operations Manager', industry: 'operations' },
  { value: 'logistics_staff', label: 'Logistics Staff', industry: 'logistics_supply_chain' },
  { value: 'warehouse_staff', label: 'Warehouse Staff', industry: 'logistics_supply_chain' },
  { value: 'supply_chain_planner', label: 'Supply Chain Planner', industry: 'logistics_supply_chain' },
  { value: 'hotel_staff', label: 'Hotel Staff', industry: 'hospitality_tourism' },
  { value: 'tour_guide', label: 'Tour Guide', industry: 'hospitality_tourism' },
  { value: 'restaurant_staff', label: 'Restaurant Staff', industry: 'hospitality_tourism' },
  { value: 'legal_staff', label: 'Legal Staff', industry: 'legal' },
  { value: 'lawyer', label: 'Lawyer', industry: 'legal' },
  { value: 'compliance_officer', label: 'Compliance Officer', industry: 'legal' },
  { value: 'production_worker', label: 'Production Worker', industry: 'manufacturing' },
  { value: 'quality_control', label: 'Quality Control', industry: 'manufacturing' },
  { value: 'production_manager', label: 'Production Manager', industry: 'manufacturing' },
  { value: 'retail_staff', label: 'Retail Staff', industry: 'retail' },
  { value: 'store_manager', label: 'Store Manager', industry: 'retail' },
  { value: 'other', label: 'Other', industry: 'other' },
  { value: 'unknown', label: 'Unknown', industry: 'unknown' },
];

export const SENIORITY_OPTIONS: NormalOption[] = [
  { value: 'intern', label: 'Intern' },
  { value: 'fresher', label: 'Fresher' },
  { value: 'junior', label: 'Junior' },
  { value: 'middle', label: 'Middle' },
  { value: 'senior', label: 'Senior' },
  { value: 'lead', label: 'Lead' },
  { value: 'manager', label: 'Manager' },
  { value: 'director', label: 'Director' },
  { value: 'unknown', label: 'Unknown' },
];

export const EMPLOYMENT_TYPE_OPTIONS: NormalOption[] = [
  { value: 'fulltime', label: 'Full-time' },
  { value: 'parttime', label: 'Part-time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
  { value: 'freelance', label: 'Freelance' },
  { value: 'temporary', label: 'Temporary' },
  { value: 'unknown', label: 'Unknown' },
];

export const REMOTE_TYPE_OPTIONS: NormalOption[] = [
  { value: 'onsite', label: 'On-site' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'remote', label: 'Remote' },
  { value: 'unknown', label: 'Unknown' },
];

export const EDUCATION_LEVEL_OPTIONS: NormalOption[] = [
  { value: 'high_school', label: 'High School' },
  { value: 'vocational', label: 'Vocational' },
  { value: 'associate', label: 'Associate' },
  { value: 'bachelor', label: 'Bachelor' },
  { value: 'master', label: 'Master' },
  { value: 'phd', label: 'PhD' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'unknown', label: 'Unknown' },
];

export const CV_STATUS_OPTIONS: NormalOption[] = [
  { value: 'draft', label: 'Draft' },
  { value: 'published', label: 'Published' },
  { value: 'archived', label: 'Archived' },
  { value: 'unknown', label: 'Unknown' },
];

export const JOB_STATUS_OPTIONS: NormalOption[] = [
  { value: 'draft', label: 'Draft' },
  { value: 'published', label: 'Published' },
  { value: 'closed', label: 'Closed' },
  { value: 'unknown', label: 'Unknown' },
];

export const VISIBILITY_OPTIONS: NormalOption[] = [
  { value: 'private', label: 'Private' },
  { value: 'public', label: 'Public' },
  { value: 'unlisted', label: 'Unlisted' },
  { value: 'unknown', label: 'Unknown' },
];

export const SALARY_PERIOD_OPTIONS: NormalOption[] = [
  { value: 'hour', label: 'Per Hour' },
  { value: 'day', label: 'Per Day' },
  { value: 'month', label: 'Per Month' },
  { value: 'year', label: 'Per Year' },
  { value: 'project', label: 'Per Project' },
  { value: 'unknown', label: 'Unknown' },
];

export const CURRENCY_OPTIONS: NormalOption[] = [
  { value: 'VND', label: 'VND' },
  { value: 'USD', label: 'USD' },
  { value: 'EUR', label: 'EUR' },
  { value: 'JPY', label: 'JPY' },
  { value: 'KRW', label: 'KRW' },
  { value: 'unknown', label: 'Unknown' },
];

export const SKILL_LEVEL_OPTIONS: NormalOption[] = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
  { value: 'expert', label: 'Expert' },
  { value: 'unknown', label: 'Unknown' },
];

export const SKILL_CATEGORY_OPTIONS: NormalOption[] = [
  { value: 'technical', label: 'Technical Skill' },
  { value: 'professional', label: 'Professional Skill' },
  { value: 'soft_skill', label: 'Soft Skill' },
  { value: 'language', label: 'Language' },
  { value: 'tool', label: 'Tool' },
  { value: 'domain_knowledge', label: 'Domain Knowledge' },
  { value: 'certification', label: 'Certification' },
  { value: 'management', label: 'Management' },
  { value: 'unknown', label: 'Unknown' },
];

export const LANGUAGE_LEVEL_OPTIONS: NormalOption[] = [
  { value: 'basic', label: 'Basic' },
  { value: 'conversational', label: 'Conversational' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'proficient', label: 'Proficient' },
  { value: 'fluent', label: 'Fluent' },
  { value: 'native', label: 'Native' },
  { value: 'unknown', label: 'Unknown' },
];

export const PRE_SCREEN_QUESTION_TYPE_OPTIONS: NormalOption[] = [
  { value: 'text', label: 'Text' },
  { value: 'number', label: 'Number' },
  { value: 'single-choice', label: 'Single Choice' },
  { value: 'multi-choice', label: 'Multiple Choice' },
  { value: 'unknown', label: 'Unknown' },
];

export const PORTFOLIO_MEDIA_TYPE_OPTIONS: NormalOption[] = [
  { value: 'website', label: 'Website' },
  { value: 'github', label: 'GitHub' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'behance', label: 'Behance' },
  { value: 'dribbble', label: 'Dribbble' },
  { value: 'youtube', label: 'YouTube' },
  { value: 'document', label: 'Document' },
  { value: 'image', label: 'Image' },
  { value: 'video', label: 'Video' },
  { value: 'other', label: 'Other' },
  { value: 'unknown', label: 'Unknown' },
];

export const optionLabel = (options: NormalOption[], value?: string | null): string => {
  if (!value) return 'Unknown';
  return options.find((option) => option.value === value)?.label ?? value;
};

export const occupationOptionsForIndustry = (industry: string): NormalOption[] => {
  const scoped = OCCUPATION_GROUP_OPTIONS.filter((option) => option.industry === industry);
  const unknown = OCCUPATION_GROUP_OPTIONS.find((option) => option.value === 'unknown');
  if (industry === 'unknown' || scoped.length === 0) return unknown ? [unknown] : [];
  return unknown ? [...scoped, unknown] : scoped;
};

const normalizeText = (value: string): string =>
  value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();

export const slugifySkillName = (value: string): string => {
  const normalized = normalizeText(value)
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
  return normalized || 'unknown';
};

const SKILL_ALIASES: Array<{ normalizedName: string; aliases: string[]; category: string }> = [
  { normalizedName: 'react', aliases: ['React', 'ReactJS', 'React.js', 'reactjs', 'react.js'], category: 'technical' },
  { normalizedName: 'nodejs', aliases: ['Node', 'Node.js', 'NodeJS', 'nodejs', 'node.js'], category: 'technical' },
  { normalizedName: 'python', aliases: ['Python', 'python'], category: 'technical' },
  { normalizedName: 'fastapi', aliases: ['FastAPI', 'Fast API', 'fastapi'], category: 'technical' },
  { normalizedName: 'postgresql', aliases: ['PostgreSQL', 'Postgres', 'postgres', 'postgresql'], category: 'technical' },
  { normalizedName: 'mongodb', aliases: ['MongoDB', 'Mongo', 'mongo'], category: 'technical' },
  { normalizedName: 'excel', aliases: ['Excel', 'Microsoft Excel', 'MS Excel'], category: 'tool' },
  { normalizedName: 'word', aliases: ['Word', 'Microsoft Word', 'MS Word'], category: 'tool' },
  { normalizedName: 'powerpoint', aliases: ['PowerPoint', 'Microsoft PowerPoint', 'MS PowerPoint'], category: 'tool' },
  { normalizedName: 'misa', aliases: ['MISA', 'Misa', 'MISA Accounting'], category: 'tool' },
  { normalizedName: 'sap', aliases: ['SAP', 'SAP ERP'], category: 'tool' },
  { normalizedName: 'tax_declaration', aliases: ['Tax Declaration', 'Tax Filing', 'Tax Reporting', 'Kê khai thuế', 'Khai thuế'], category: 'professional' },
  { normalizedName: 'financial_reporting', aliases: ['Financial Reporting', 'Báo cáo tài chính', 'Lập báo cáo tài chính'], category: 'professional' },
  { normalizedName: 'photoshop', aliases: ['Photoshop', 'Adobe Photoshop', 'PTS'], category: 'tool' },
  { normalizedName: 'illustrator', aliases: ['Illustrator', 'Adobe Illustrator', 'AI'], category: 'tool' },
  { normalizedName: 'figma', aliases: ['Figma', 'figma'], category: 'tool' },
  { normalizedName: 'autocad', aliases: ['AutoCAD', 'Auto CAD', 'autocad'], category: 'tool' },
  { normalizedName: 'revit', aliases: ['Revit', 'Autodesk Revit'], category: 'tool' },
  { normalizedName: 'google_ads', aliases: ['Google Ads', 'Google Adwords', 'AdWords'], category: 'tool' },
  { normalizedName: 'meta_ads', aliases: ['Meta Ads', 'Facebook Ads', 'Facebook Advertising'], category: 'tool' },
  { normalizedName: 'seo', aliases: ['SEO', 'Search Engine Optimization', 'Tối ưu công cụ tìm kiếm'], category: 'professional' },
  { normalizedName: 'sales', aliases: ['Sales', 'Telesales', 'Selling', 'Bán hàng'], category: 'professional' },
  { normalizedName: 'customer_service', aliases: ['Customer Service', 'Customer Support', 'Chăm sóc khách hàng', 'CSKH'], category: 'professional' },
  { normalizedName: 'recruitment', aliases: ['Recruitment', 'Hiring', 'Talent Acquisition', 'Tuyển dụng'], category: 'professional' },
  { normalizedName: 'communication', aliases: ['Communication', 'Giao tiếp', 'Communication Skill'], category: 'soft_skill' },
  { normalizedName: 'teamwork', aliases: ['Teamwork', 'Team Work', 'Làm việc nhóm'], category: 'soft_skill' },
  { normalizedName: 'leadership', aliases: ['Leadership', 'Team Leadership', 'Lãnh đạo nhóm'], category: 'management' },
];

export const normalizeSkillNameForForm = (name: string): { normalizedName: string; category: string } => {
  const key = normalizeText(name);
  const alias = SKILL_ALIASES.find((item) => item.aliases.some((candidate) => normalizeText(candidate) === key));
  if (alias) return { normalizedName: alias.normalizedName, category: alias.category };
  return { normalizedName: slugifySkillName(name), category: 'unknown' };
};
