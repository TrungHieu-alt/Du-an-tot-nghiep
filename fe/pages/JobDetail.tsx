
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  MapPin, DollarSign, Briefcase, Calendar, Building2, Globe, Clock, 
  CheckCircle2, Share2, Bookmark, ArrowLeft, AlertCircle, Edit, ExternalLink,
  Users, Mail, Phone, Printer, MonitorSmartphone, LayoutGrid, Sparkles, ChevronDown, BrainCircuit, Loader2
} from 'lucide-react';
import api from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import EditJobModal from '../components/modals/EditJobModal';
import { SkeletonList } from '../components/common/SkeletonLoader';

// --- Interfaces based on Backend JSON ---

interface JobSkill {
  _id?: string;
  name: string;
  level?: string;
}

interface RecruiterInfo {
  _id?: string;
  name: string;
  email: string;
  phone: string;
}

interface SalaryInfo {
  _id?: string;
  min?: number;
  max?: number;
  currency?: string;
}

interface JobDetailData {
  _id: string; // Internal ID
  id: string; // Alias for UI
  companyId: string;
  userId?: string; // Derived from createdBy
  
  // Core Info
  title: string;
  slug?: string;
  status: string;
  visibility?: string;
  
  // Company Info
  companyName: string;
  companyLogoUrl: string;
  companyWebsite: string;
  companyLocation: string; // Main display location
  department?: string;
  
  // Job Details
  employmentType: string[];
  seniority: string;
  teamSize?: number;
  experienceYears?: number;
  educationLevel?: string;
  remote: boolean;
  
  // Content
  description: string;
  responsibilities: string[];
  requirements: string[];
  niceToHave: string[];
  benefits: string[];
  
  // Complex Objects
  skills: JobSkill[];
  salary: SalaryInfo | null;
  recruiter?: RecruiterInfo;
  
  // Meta
  tags: string[];
  categories: string[];
  applyUrl?: string;
  applyEmail?: string;
  
  createdAt: string;
  updatedAt: string;
  
  // Original payload for editing
  raw: any; 
}

// Interface for Match Response
interface MatchAnalysisResult {
  jobId: string;
  cvId: string;
  totalPairs: number;
  finalOverallScoreDecimal: number;
  finalOverallScore: number;
  allPairs?: any[];
}

const JobDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [job, setJob] = useState<JobDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false); // Local state for bookmark

  // Match State
  const [myCvs, setMyCvs] = useState<any[]>([]);
  const [selectedCvId, setSelectedCvId] = useState<string>('');
  const [matchResult, setMatchResult] = useState<MatchAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Helper to format salary
  const formatSalary = (salary: SalaryInfo | null): string => {
    if (!salary) return "Thỏa thuận";
    const { min, max, currency = '' } = salary;
    
    if (min !== undefined && max !== undefined) return `${min.toLocaleString()} - ${max.toLocaleString()} ${currency}`;
    if (min !== undefined) return `Từ ${min.toLocaleString()} ${currency}`;
    if (max !== undefined) return `Đến ${max.toLocaleString()} ${currency}`;
    
    return "Thỏa thuận";
  };

  const fetchJob = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/jobs/${id}`);
      const payload = res.data;

      // Normalize data based on backend JSON
      const normalized: JobDetailData = {
        _id: payload._id,
        id: payload._id, // Map _id to id for easier usage
        companyId: payload.companyId,
        userId: payload.createdBy, // Mapping createdBy to userId for ownership check
        
        title: payload.title || 'Công việc không tên',
        slug: payload.slug,
        status: payload.status || 'published',
        
        companyName: payload.companyName || 'Công ty ẩn danh',
        companyLogoUrl: payload.companyLogoUrl || `https://ui-avatars.com/api/?name=${encodeURIComponent(payload.companyName || 'C')}&background=random`,
        companyWebsite: payload.companyWebsite || '',
        companyLocation: payload.companyLocation || (payload.location?.city) || 'Việt Nam',
        department: payload.department,
        
        employmentType: Array.isArray(payload.employmentType) ? payload.employmentType : [],
        seniority: payload.seniority || 'Not specified',
        teamSize: payload.teamSize,
        experienceYears: payload.experienceYears,
        educationLevel: payload.educationLevel,
        remote: !!payload.remote,
        
        description: payload.description || '',
        responsibilities: Array.isArray(payload.responsibilities) ? payload.responsibilities : [],
        requirements: Array.isArray(payload.requirements) ? payload.requirements : [],
        niceToHave: Array.isArray(payload.niceToHave) ? payload.niceToHave : [],
        benefits: Array.isArray(payload.benefits) ? payload.benefits : [],
        
        // Handle Skills (Array of Objects)
        skills: Array.isArray(payload.skills) ? payload.skills : [],
        
        // Handle Salary (Object or ID)
        salary: (typeof payload.salary === 'object' && payload.salary !== null) ? payload.salary : null,
        
        // Handle Recruiter
        recruiter: payload.recruiter,
        
        tags: Array.isArray(payload.tags) ? payload.tags : [],
        categories: Array.isArray(payload.categories) ? payload.categories : [],
        
        applyUrl: payload.applyUrl,
        applyEmail: payload.applyEmail,
        
        createdAt: payload.createdAt,
        updatedAt: payload.updatedAt,
        
        raw: payload
      };
      
      setJob(normalized);
    } catch (err: any) {
      console.error('Fetch Job Error:', err);
      setError(err.response?.data?.message || 'Không thể tải thông tin công việc.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchJob();
  }, [fetchJob]);

  // Fetch Candidate's CVs for Matching
  useEffect(() => {
    if (user) {
      const fetchMyCvs = async () => {
        try {
          const res = await api.get('/cv/user/me');
          const data = Array.isArray(res.data) ? res.data : (res.data?.data || []);
          setMyCvs(data);
        } catch (e) {
          console.error("Failed to fetch CVs for matching", e);
        }
      };
      fetchMyCvs();
    }
  }, [user]);

  // Check ownership
  const isOwner = user && job && (user.id === job.userId || user.id === job.raw?.createdBy);

  const handleUpdateJob = async (updatedData: any) => {
    setIsSaving(true);
    try {
      await api.put(`/jobs/${id}`, updatedData);
      await fetchJob();
      setIsEditModalOpen(false);
      alert('Cập nhật tin tuyển dụng thành công!');
    } catch (err: any) {
      console.error("Update failed", err);
      alert(err.response?.data?.message || 'Cập nhật thất bại.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteJob = async () => {
    try {
      await api.delete(`/jobs/${id}`);
      navigate('/jobs');
    } catch (err: any) {
      console.error("Delete failed", err);
      alert('Không thể xóa tin tuyển dụng. Vui lòng thử lại.');
    }
  };

  const handleApply = () => {
    if (job?.applyUrl) {
      window.open(job.applyUrl, '_blank');
    } else if (job?.applyEmail) {
      window.location.href = `mailto:${job.applyEmail}?subject=Ứng tuyển vị trí ${job.title}`;
    } else {
      alert('Vui lòng liên hệ trực tiếp nhà tuyển dụng.');
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    alert('Đã sao chép liên kết công việc!');
  };

  const toggleSave = () => {
    setIsSaved(!isSaved);
  };

  // --- Matching Logic ---
  const handleAnalyzeMatch = async (cvId: string) => {
    if (!cvId || !id) return;
    
    setSelectedCvId(cvId);
    setIsAnalyzing(true);
    setMatchResult(null);

    try {
      // Call RAG match endpoint: Match Job (id) against CV (cvId)
      // Note: The endpoint logic is symmetric, so order might depend on backend impl,
      // typically /match-job-cv-chunks/:jobId/:cvId
      const res = await api.get(`/rag/match-job-cv-chunks/${id}/${cvId}`);
      setMatchResult(res.data);
    } catch (error) {
      console.error("Match analysis failed", error);
      alert("Không thể phân tích mức độ phù hợp. Vui lòng thử lại sau.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getMatchEvaluation = (score: number) => {
    if (score >= 80) {
      return { text: "Cực kỳ phù hợp", color: "text-emerald-600 bg-emerald-50 border-emerald-200" };
    }
    if (score >= 50) {
      return { text: "Phù hợp trung bình", color: "text-amber-600 bg-amber-50 border-amber-200" };
    }
    return { text: "Cực kỳ không phù hợp", color: "text-red-600 bg-red-50 border-red-200" };
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('vi-VN');
  };

  // Helper to capitalize first letter
  const capitalize = (s: string) => s ? s.charAt(0).toUpperCase() + s.slice(1) : '';

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 pt-10 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto space-y-6">
           <div className="h-48 bg-white rounded-2xl animate-pulse"></div>
           <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="col-span-2 space-y-4">
                 <div className="h-96 bg-white rounded-2xl animate-pulse"></div>
              </div>
              <div className="h-96 bg-white rounded-2xl animate-pulse"></div>
           </div>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Không thể tải công việc</h2>
          <p className="text-gray-500 mb-6">{error || 'Công việc không tồn tại hoặc đã bị xóa.'}</p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => navigate('/jobs')} className="px-5 py-2.5 rounded-lg border border-gray-300 font-medium hover:bg-gray-50 transition-colors">
              Quay lại danh sách
            </button>
            <button onClick={fetchJob} className="px-5 py-2.5 rounded-lg bg-[#0A65CC] text-white font-medium hover:bg-blue-700 transition-colors">
              Thử lại
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F7FC] pt-8 pb-20 font-sans">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Navigation */}
        <div className="flex items-center justify-between mb-6">
          <Link to="/jobs" className="inline-flex items-center text-gray-500 hover:text-[#0A65CC] transition-colors font-medium text-sm">
            <ArrowLeft className="w-4 h-4 mr-1" /> Quay lại danh sách
          </Link>
          <div className="flex gap-2">
            {isOwner && (
               <button 
                 onClick={() => setIsEditModalOpen(true)}
                 className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg hover:border-[#0A65CC] hover:text-[#0A65CC] transition-all text-sm font-semibold shadow-sm"
               >
                 <Edit className="w-4 h-4" /> Quản lý tin
               </button>
            )}
            <button 
              onClick={handleShare}
              className="p-2 bg-white border border-gray-200 text-gray-500 rounded-lg hover:text-[#0A65CC] hover:border-[#0A65CC] transition-colors shadow-sm"
              title="Chia sẻ"
            >
              <Share2 className="w-5 h-5" />
            </button>
             <button 
              onClick={() => window.print()}
              className="p-2 bg-white border border-gray-200 text-gray-500 rounded-lg hover:text-[#0A65CC] hover:border-[#0A65CC] transition-colors shadow-sm hidden md:block"
              title="In"
            >
              <Printer className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Header Card */}
        <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-gray-100 mb-6">
           <div className="flex flex-col md:flex-row gap-6 md:items-start">
              <div className="flex-shrink-0">
                 <img 
                   src={job.companyLogoUrl} 
                   alt={job.companyName} 
                   className="w-20 h-20 md:w-28 md:h-28 rounded-xl object-contain border border-gray-100 shadow-sm p-2 bg-white"
                 />
              </div>
              <div className="flex-1 min-w-0">
                 <div className="flex flex-col md:flex-row md:justify-between gap-4">
                    <div>
                      <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2 leading-tight">{job.title}</h1>
                      <div className="flex items-center gap-2 mb-4 text-gray-600 font-medium">
                        <Building2 className="w-4 h-4" />
                        <span className="text-[#0A65CC]">{job.companyName}</span>
                        {job.remote && (
                          <span className="px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs font-bold ml-2 flex items-center gap-1">
                            <MonitorSmartphone className="w-3 h-3" /> Remote
                          </span>
                        )}
                      </div>
                      
                      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-500">
                         <div className="flex items-center gap-1.5">
                           <MapPin className="w-4 h-4 text-gray-400" />
                           {job.companyLocation}
                         </div>
                         <div className="flex items-center gap-1.5">
                           <Briefcase className="w-4 h-4 text-gray-400" />
                           {job.employmentType.map(capitalize).join(', ') || 'Full-time'}
                         </div>
                         <div className="flex items-center gap-1.5">
                           <Clock className="w-4 h-4 text-gray-400" />
                           {capitalize(job.seniority)}
                         </div>
                         <div className="flex items-center gap-1.5">
                           <Calendar className="w-4 h-4 text-gray-400" />
                           Đăng ngày: {formatDate(job.createdAt)}
                         </div>
                      </div>
                    </div>
                    
                    <div className="flex flex-col sm:flex-row gap-3 mt-2 md:mt-0">
                       <button 
                         onClick={handleApply}
                         className="flex items-center justify-center gap-2 px-8 py-3 bg-[#0A65CC] text-white font-bold rounded-lg hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/30 text-base"
                       >
                          Ứng tuyển ngay
                          <ExternalLink className="w-4 h-4" />
                       </button>
                       <button 
                         onClick={toggleSave}
                         className={`flex items-center justify-center gap-2 px-6 py-3 border rounded-lg font-bold transition-colors ${isSaved ? 'bg-blue-50 border-blue-200 text-[#0A65CC]' : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'}`}
                       >
                          <Bookmark className={`w-5 h-5 ${isSaved ? 'fill-current' : ''}`} />
                          {isSaved ? 'Đã lưu' : 'Lưu tin'}
                       </button>
                    </div>
                 </div>
              </div>
           </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Description */}
            <section className="bg-white rounded-xl p-6 md:p-8 shadow-sm border border-gray-100">
               <h3 className="text-lg font-bold text-gray-900 mb-4">Mô tả công việc</h3>
               <div className="text-gray-700 leading-relaxed whitespace-pre-line text-[15px]">
                 {job.description || <span className="italic text-gray-400">Chưa có mô tả chi tiết.</span>}
               </div>
            </section>

            {/* Responsibilities */}
            {job.responsibilities && job.responsibilities.length > 0 && (
              <section className="bg-white rounded-xl p-6 md:p-8 shadow-sm border border-gray-100">
                 <h3 className="text-lg font-bold text-gray-900 mb-4">Trách nhiệm chính</h3>
                 <ul className="space-y-3">
                   {job.responsibilities.map((item, idx) => (
                     <li key={idx} className="flex items-start gap-3 text-gray-700 text-[15px]">
                        <CheckCircle2 className="w-5 h-5 text-[#0A65CC] flex-shrink-0 mt-0.5" />
                        <span className="leading-relaxed">{item}</span>
                     </li>
                   ))}
                 </ul>
              </section>
            )}

            {/* Requirements */}
            {job.requirements && job.requirements.length > 0 && (
              <section className="bg-white rounded-xl p-6 md:p-8 shadow-sm border border-gray-100">
                 <h3 className="text-lg font-bold text-gray-900 mb-4">Yêu cầu công việc</h3>
                 <ul className="space-y-3">
                   {job.requirements.map((item, idx) => (
                     <li key={idx} className="flex items-start gap-3 text-gray-700 text-[15px]">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-2 flex-shrink-0" />
                        <span className="leading-relaxed">{item}</span>
                     </li>
                   ))}
                 </ul>
              </section>
            )}

            {/* Nice to Have */}
            {job.niceToHave && job.niceToHave.length > 0 && (
              <section className="bg-white rounded-xl p-6 md:p-8 shadow-sm border border-gray-100">
                 <h3 className="text-lg font-bold text-gray-900 mb-4">Điểm cộng (Nice-to-have)</h3>
                 <ul className="space-y-3">
                   {job.niceToHave.map((item, idx) => (
                     <li key={idx} className="flex items-start gap-3 text-gray-700 text-[15px]">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-400 mt-2 flex-shrink-0" />
                        <span className="leading-relaxed">{item}</span>
                     </li>
                   ))}
                 </ul>
              </section>
            )}
            
            {/* Tags */}
            {job.tags && job.tags.length > 0 && (
               <div className="pt-4">
                 <h4 className="text-sm font-bold text-gray-900 mb-3 uppercase tracking-wide">Từ khóa</h4>
                 <div className="flex flex-wrap gap-2">
                    {job.tags.map((tag, idx) => (
                      <span key={idx} className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm hover:bg-gray-200 transition-colors cursor-default border border-gray-200">
                        #{tag}
                      </span>
                    ))}
                 </div>
               </div>
            )}

          </div>

          {/* Right Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* --- AI Matching Card (New) --- */}
            {myCvs.length > 0 && (
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 ring-1 ring-blue-100 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-3 opacity-10">
                   <Sparkles className="w-16 h-16 text-blue-600" />
                </div>
                
                <h3 className="font-bold text-gray-900 mb-1 flex items-center gap-2 relative z-10">
                  <BrainCircuit className="w-5 h-5 text-[#0A65CC]" />
                  Đánh giá mức độ phù hợp
                </h3>
                <p className="text-xs text-gray-500 mb-4 relative z-10 italic">
                  Kết quả đánh giá tại đây sẽ chính xác hơn.
                </p>
                
                <div className="space-y-4 relative z-10">
                  <div className="relative">
                    <select 
                      className="w-full appearance-none bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg px-3 py-2.5 pr-8 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-[#0A65CC]"
                      value={selectedCvId}
                      onChange={(e) => handleAnalyzeMatch(e.target.value)}
                      disabled={isAnalyzing}
                    >
                      <option value="" disabled>Chọn CV để so sánh...</option>
                      {myCvs.map((cv) => (
                        <option key={cv._id || cv.id} value={cv._id || cv.id}>
                          {cv.fullname || cv.name || "CV không tên"}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                  </div>

                  {isAnalyzing && (
                    <div className="flex flex-col items-center justify-center py-4 text-gray-500">
                       <Loader2 className="w-8 h-8 animate-spin text-[#0A65CC] mb-2" />
                       <span className="text-xs font-medium">Đang phân tích dữ liệu...</span>
                    </div>
                  )}

                  {!isAnalyzing && matchResult && (
                    <div className="animate-in fade-in zoom-in duration-300">
                       <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-600">Điểm phù hợp:</span>
                          <span className="text-2xl font-bold text-[#0A65CC]">{matchResult.finalOverallScore}/100</span>
                       </div>
                       
                       <div className="w-full bg-gray-100 rounded-full h-2.5 mb-3 overflow-hidden">
                          <div 
                            className={`h-2.5 rounded-full transition-all duration-1000 ${
                              matchResult.finalOverallScore >= 80 ? 'bg-emerald-500' :
                              matchResult.finalOverallScore >= 50 ? 'bg-amber-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${matchResult.finalOverallScore}%` }}
                          ></div>
                       </div>

                       <div className={`text-center py-2 px-3 rounded-lg border text-sm font-bold ${getMatchEvaluation(matchResult.finalOverallScore).color}`}>
                          {getMatchEvaluation(matchResult.finalOverallScore).text}
                       </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Salary & Overview */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
               <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                 <LayoutGrid className="w-5 h-5 text-[#0A65CC]" />
                 Tổng quan
               </h3>
               
               <div className="space-y-4">
                  <div className="flex items-start gap-3">
                     <div className="p-2 bg-green-50 text-green-600 rounded-lg">
                       <DollarSign className="w-5 h-5" />
                     </div>
                     <div>
                       <p className="text-xs text-gray-500 font-semibold uppercase">Mức lương</p>
                       <p className="font-bold text-gray-900 text-lg">{formatSalary(job.salary)}</p>
                     </div>
                  </div>
                  
                  {job.experienceYears !== undefined && (
                     <div className="flex items-start gap-3">
                        <div className="p-2 bg-purple-50 text-purple-600 rounded-lg">
                          <Briefcase className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 font-semibold uppercase">Kinh nghiệm</p>
                          <p className="font-medium text-gray-900">{job.experienceYears} năm</p>
                        </div>
                     </div>
                  )}

                  {job.teamSize && (
                     <div className="flex items-start gap-3">
                        <div className="p-2 bg-orange-50 text-orange-600 rounded-lg">
                          <Users className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 font-semibold uppercase">Quy mô team</p>
                          <p className="font-medium text-gray-900">{job.teamSize} người</p>
                        </div>
                     </div>
                  )}

                  {job.department && (
                     <div className="flex items-start gap-3">
                        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                          <Building2 className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 font-semibold uppercase">Phòng ban</p>
                          <p className="font-medium text-gray-900">{job.department}</p>
                        </div>
                     </div>
                  )}
               </div>
            </div>

            {/* Benefits */}
            {job.benefits && job.benefits.length > 0 && (
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                 <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                   <CheckCircle2 className="w-5 h-5 text-[#0A65CC]" />
                   Quyền lợi
                 </h3>
                 <ul className="space-y-3">
                   {job.benefits.map((ben, idx) => (
                     <li key={idx} className="flex items-start gap-3 text-sm text-gray-700">
                        <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span>{ben}</span>
                     </li>
                   ))}
                 </ul>
              </div>
            )}

            {/* Skills */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
               <h3 className="font-bold text-gray-900 mb-4">Kỹ năng yêu cầu</h3>
               <div className="flex flex-col gap-2">
                 {job.skills.map((skill, idx) => (
                   <div key={idx} className="flex justify-between items-center text-sm p-2 bg-gray-50 rounded-lg border border-gray-100">
                     <span className="font-medium text-gray-700">{skill.name}</span>
                     {skill.level && (
                       <span className="text-xs bg-white text-gray-500 px-2 py-0.5 rounded border border-gray-200 capitalize">
                         {skill.level}
                       </span>
                     )}
                   </div>
                 ))}
                 {job.skills.length === 0 && <span className="text-gray-400 italic text-sm">Không yêu cầu kỹ năng cụ thể</span>}
               </div>
            </div>

            {/* Company Info */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
               <div className="flex items-center gap-3 mb-4">
                  <img src={job.companyLogoUrl} alt={job.companyName} className="w-12 h-12 rounded-lg object-contain border border-gray-100" />
                  <div>
                    <h3 className="font-bold text-gray-900 line-clamp-1">{job.companyName}</h3>
                    {job.companyWebsite && (
                      <a href={job.companyWebsite} target="_blank" rel="noopener noreferrer" className="text-sm text-[#0A65CC] hover:underline flex items-center gap-1">
                        Website <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
               </div>
               <button className="w-full py-2 bg-gray-50 text-gray-700 font-medium rounded-lg hover:bg-gray-100 transition-colors text-sm">
                 Xem trang công ty
               </button>
            </div>

            {/* Recruiter Contact (If available) */}
            {job.recruiter && (job.recruiter.name || job.recruiter.email) && (
               <div className="bg-gradient-to-br from-[#0A65CC] to-[#005bb5] rounded-xl p-6 text-white shadow-lg">
                  <h3 className="font-bold text-lg mb-4">Liên hệ tuyển dụng</h3>
                  <div className="space-y-3">
                     {job.recruiter.name && (
                       <div className="flex items-center gap-3">
                          <Users className="w-5 h-5 text-blue-200" />
                          <span className="font-medium">{job.recruiter.name}</span>
                       </div>
                     )}
                     {job.recruiter.email && (
                       <div className="flex items-center gap-3">
                          <Mail className="w-5 h-5 text-blue-200" />
                          <a href={`mailto:${job.recruiter.email}`} className="hover:underline">{job.recruiter.email}</a>
                       </div>
                     )}
                     {job.recruiter.phone && (
                       <div className="flex items-center gap-3">
                          <Phone className="w-5 h-5 text-blue-200" />
                          <span>{job.recruiter.phone}</span>
                       </div>
                     )}
                  </div>
               </div>
            )}

          </div>
        </div>
      </div>

      {/* Edit Modal */}
      {job && (
        <EditJobModal 
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          job={job.raw}
          onSave={handleUpdateJob}
          onDelete={handleDeleteJob}
          isSaving={isSaving}
        />
      )}
    </div>
  );
};

export default JobDetail;
