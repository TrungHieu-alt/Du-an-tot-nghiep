
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  MapPin, Mail, Phone, Calendar, Download, Share2, MessageCircle, 
  Edit, ArrowLeft, Building, GraduationCap, Globe, Award, Briefcase, 
  CheckCircle2, ExternalLink, Loader2, AlertCircle, Bookmark, DollarSign, Clock, Layout, Sparkles, ChevronDown, BrainCircuit
} from 'lucide-react';
import api from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import EditCvModal from '../components/modals/EditCvModal';
import { UserCV } from '../types';

// Types updated to match Backend Response
interface Experience {
  _id?: string;
  id?: string;
  title: string;
  company: string;
  companyWebsite?: string;
  location?: string;
  from?: string;
  to?: string;
  isCurrent?: boolean;
  employmentType?: string;
  responsibilities?: string[];
  achievements?: string[]; // Added
  tags?: string[]; // Added
}

interface Education {
  _id?: string;
  id?: string;
  school: string;
  degree: string;
  major: string;
  from?: string;
  to?: string;
  gpa?: string;
}

interface Project {
  _id?: string;
  id?: string;
  name: string;
  description?: string;
  role?: string;
  url?: string;
  techStack?: string[];
  metrics?: string[]; // Added
  from?: string;
  to?: string;
}

interface Certification {
  _id?: string;
  id?: string;
  name: string;
  issuer: string;
  issueDate: string;
  expiryDate?: string;
  credentialUrl?: string;
}

interface Language {
  _id?: string;
  name: string;
  level: string;
}

interface Skill {
  _id?: string;
  name: string;
  level?: string;
  category?: string; // Added
  years?: number; // Added
}

interface Location {
  _id?: string;
  city?: string;
  state?: string;
  country?: string;
}

interface CandidateDetailData {
  id: string;
  userId?: string;
  fullname: string;
  preferredName?: string;
  headline: string;
  email?: string;
  phone?: string;
  avatarUrl?: string;
  location: Location;
  summary?: string;
  
  // General Info
  targetRole?: string;
  salaryExpectation?: string;
  availability?: string;
  employmentType?: string[];

  skills: Skill[];
  experiences: Experience[];
  education: Education[];
  projects: Project[];
  certifications: Certification[];
  languages: Language[];
  portfolio: { type: string; url: string; description?: string }[];
  tags: string[];
  
  status?: string;
  createdAt?: string;
  updatedAt?: string;
  resumeUrl?: string;
  raw?: any;
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

const CandidateDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [candidate, setCandidate] = useState<CandidateDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Edit State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Match State
  const [myJobs, setMyJobs] = useState<any[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [matchResult, setMatchResult] = useState<MatchAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const fetchCandidate = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/cv/${id}`);
      const payload = res.data;

      // Normalize data based on provided JSON structure
      const normalized: CandidateDetailData = {
        id: payload._id || payload.id,
        userId: payload.createdBy || payload.userId, // Map createdBy to userId for ownership check
        fullname: payload.fullname || 'Ứng viên ẩn danh',
        preferredName: payload.preferredName,
        headline: payload.headline || payload.targetRole || 'Chưa có tiêu đề',
        email: payload.email,
        phone: payload.phone,
        avatarUrl: payload.avatarUrl,
        location: payload.location || {},
        summary: payload.summary,
        
        // General Info Mapping
        targetRole: payload.targetRole,
        salaryExpectation: payload.salaryExpectation,
        availability: payload.availability,
        employmentType: Array.isArray(payload.employmentType) ? payload.employmentType : [],

        skills: Array.isArray(payload.skills) ? payload.skills : [],
        experiences: Array.isArray(payload.experiences) ? payload.experiences : [],
        education: Array.isArray(payload.education) ? payload.education : [],
        projects: Array.isArray(payload.projects) ? payload.projects : [],
        certifications: Array.isArray(payload.certifications) ? payload.certifications : [],
        languages: Array.isArray(payload.languages) ? payload.languages : [],
        portfolio: Array.isArray(payload.portfolio) ? payload.portfolio : [],
        tags: Array.isArray(payload.tags) ? payload.tags : [],
        
        status: payload.status,
        createdAt: payload.createdAt,
        updatedAt: payload.updatedAt,
        resumeUrl: payload.resumeUrl || payload.cvFile,
        raw: payload // Store original payload for editing
      };
      
      setCandidate(normalized);
    } catch (err: any) {
      console.error('Fetch Candidate Error:', err);
      setError(err.response?.data?.message || 'Không thể tải thông tin ứng viên.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchCandidate();
  }, [fetchCandidate]);

  // Fetch Recruiter's Jobs for Matching
  useEffect(() => {
    if (user) {
      const fetchMyJobs = async () => {
        try {
          const res = await api.get('/jobs/user/me');
          const data = Array.isArray(res.data) ? res.data : (res.data?.data || res.data?.items || []);
          setMyJobs(data);
        } catch (e) {
          console.error("Failed to fetch jobs for matching", e);
        }
      };
      fetchMyJobs();
    }
  }, [user]);

  // Derived check for ownership
  const isOwner = user && candidate && (user.id === candidate.userId || user.id === candidate.raw?.user);

  const handleSaveCv = async (updatedData: any) => {
    setIsSaving(true);
    try {
      // API call to update
      await api.put(`/cv/${id}`, updatedData);
      
      // Refresh data
      await fetchCandidate();
      
      setIsEditModalOpen(false);
      alert('Cập nhật hồ sơ thành công!');
    } catch (err: any) {
      console.error("Update failed", err);
      alert(err.response?.data?.message || 'Cập nhật thất bại.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownload = () => {
    if (candidate?.resumeUrl) {
      window.open(candidate.resumeUrl, '_blank');
    } else {
      alert('Ứng viên chưa tải lên CV đính kèm.');
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    alert('Đã sao chép liên kết hồ sơ!');
  };

  // --- Matching Logic ---
  const handleAnalyzeMatch = async (jobId: string) => {
    if (!jobId || !id) return;
    
    setSelectedJobId(jobId);
    setIsAnalyzing(true);
    setMatchResult(null);

    try {
      // Call RAG match endpoint
      const res = await api.get(`/rag/match-job-cv-chunks/${jobId}/${id}`);
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

  // Helper to format dates
  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('vi-VN', { month: '2-digit', year: 'numeric' });
  };

  // Helper to construct UserCV for EditModal
  const getEditCvObject = (): UserCV => {
    if (!candidate) return {} as UserCV;
    return {
      id: candidate.id,
      name: candidate.fullname,
      title: candidate.headline,
      skills: candidate.skills.map(s => s.name),
      experienceLevel: 'Mid-Level', // Simplified fallback
      location: candidate.location.city || '',
      lastUpdated: candidate.updatedAt || '',
      ownerId: candidate.userId,
      details: candidate.raw // Pass full raw payload for pre-filling form
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 pt-20 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto space-y-6">
          <div className="h-40 bg-white rounded-2xl animate-pulse"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
             <div className="h-96 bg-white rounded-2xl animate-pulse"></div>
             <div className="col-span-2 h-96 bg-white rounded-2xl animate-pulse"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Không thể tải hồ sơ</h2>
          <p className="text-gray-500 mb-6">{error || 'Hồ sơ không tồn tại hoặc đã bị xóa.'}</p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => navigate('/candidates')} className="px-5 py-2.5 rounded-lg border border-gray-300 font-medium hover:bg-gray-50 transition-colors">
              Quay lại danh sách
            </button>
            <button onClick={fetchCandidate} className="px-5 py-2.5 rounded-lg bg-[#0A65CC] text-white font-medium hover:bg-blue-700 transition-colors">
              Thử lại
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F7FC] pt-8 pb-20 font-sans">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Navigation */}
        <div className="flex items-center justify-between mb-6">
          <Link to="/candidates" className="inline-flex items-center text-gray-500 hover:text-[#0A65CC] transition-colors font-medium text-sm">
            <ArrowLeft className="w-4 h-4 mr-1" /> Quay lại danh sách
          </Link>
          <div className="flex gap-2">
            {isOwner && (
               <button 
                 onClick={() => setIsEditModalOpen(true)}
                 className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg hover:border-[#0A65CC] hover:text-[#0A65CC] transition-all text-sm font-semibold shadow-sm"
               >
                 <Edit className="w-4 h-4" /> Chỉnh sửa hồ sơ
               </button>
            )}
            <button 
              onClick={handleShare}
              className="p-2 bg-white border border-gray-200 text-gray-500 rounded-lg hover:text-[#0A65CC] hover:border-[#0A65CC] transition-colors shadow-sm"
              title="Chia sẻ hồ sơ"
            >
              <Share2 className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Header Card */}
        <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-gray-100 mb-6">
           <div className="flex flex-col md:flex-row gap-6 md:items-start">
              <div className="flex-shrink-0">
                 <img 
                   src={candidate.avatarUrl || `https://ui-avatars.com/api/?name=${encodeURIComponent(candidate.fullname)}&background=random&size=200`} 
                   alt={candidate.fullname} 
                   className="w-24 h-24 md:w-32 md:h-32 rounded-full object-cover border-4 border-gray-50 shadow-md"
                 />
              </div>
              <div className="flex-1 min-w-0">
                 <div className="flex flex-col md:flex-row md:justify-between gap-4">
                    <div>
                      <div className="flex items-baseline gap-2 mb-1">
                        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{candidate.fullname}</h1>
                        {candidate.preferredName && (
                          <span className="text-gray-500 text-sm">({candidate.preferredName})</span>
                        )}
                      </div>
                      <p className="text-lg text-[#0A65CC] font-medium mb-3">{candidate.headline}</p>
                      
                      <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                         {candidate.location.city && (
                           <div className="flex items-center gap-1.5">
                             <MapPin className="w-4 h-4 text-gray-400" />
                             {candidate.location.city} {candidate.location.country ? `, ${candidate.location.country}` : ''}
                           </div>
                         )}
                         {candidate.email && (
                           <div className="flex items-center gap-1.5">
                             <Mail className="w-4 h-4 text-gray-400" />
                             {candidate.email}
                           </div>
                         )}
                         {candidate.phone && (
                           <div className="flex items-center gap-1.5">
                             <Phone className="w-4 h-4 text-gray-400" />
                             {candidate.phone}
                           </div>
                         )}
                         <div className="flex items-center gap-1.5 text-gray-500">
                             <Calendar className="w-4 h-4 text-gray-400" />
                             Cập nhật: {formatDate(candidate.updatedAt)}
                         </div>
                      </div>
                    </div>
                    
                    <div className="flex flex-col sm:flex-row gap-3 mt-2 md:mt-0">
                       <button className="flex items-center justify-center gap-2 px-6 py-2.5 bg-[#0A65CC] text-white font-bold rounded-lg hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/30">
                          <MessageCircle className="w-5 h-5" />
                          Gửi tin nhắn
                       </button>
                       <button 
                         onClick={handleDownload}
                         className="flex items-center justify-center gap-2 px-6 py-2.5 bg-white border border-gray-200 text-gray-700 font-bold rounded-lg hover:bg-gray-50 transition-colors"
                         disabled={!candidate.resumeUrl}
                         title={!candidate.resumeUrl ? "Không có CV đính kèm" : ""}
                       >
                          <Download className="w-5 h-5" />
                          Tải CV
                       </button>
                    </div>
                 </div>
              </div>
           </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* --- AI Matching Card (New) --- */}
            {myJobs.length > 0 && (
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
                      value={selectedJobId}
                      onChange={(e) => handleAnalyzeMatch(e.target.value)}
                      disabled={isAnalyzing}
                    >
                      <option value="" disabled>Chọn công việc để so sánh...</option>
                      {myJobs.map((job) => (
                        <option key={job._id || job.id} value={job._id || job.id}>
                          {job.title}
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

            {/* General Info Card */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                 <Layout className="w-5 h-5 text-[#0A65CC]" />
                 Thông tin chung
                </h3>
                <div className="space-y-4">
                  {candidate.targetRole && (
                    <div className="flex items-start gap-3">
                      <Briefcase className="w-4 h-4 text-gray-400 mt-1" />
                      <div>
                        <p className="text-xs text-gray-500 font-medium uppercase">Vị trí mong muốn</p>
                        <p className="text-sm font-semibold text-gray-900">{candidate.targetRole}</p>
                      </div>
                    </div>
                  )}
                  {candidate.salaryExpectation && (
                     <div className="flex items-start gap-3">
                      <DollarSign className="w-4 h-4 text-gray-400 mt-1" />
                      <div>
                        <p className="text-xs text-gray-500 font-medium uppercase">Mức lương mong muốn</p>
                        <p className="text-sm font-semibold text-gray-900">{candidate.salaryExpectation}</p>
                      </div>
                    </div>
                  )}
                   {candidate.availability && (
                     <div className="flex items-start gap-3">
                      <Clock className="w-4 h-4 text-gray-400 mt-1" />
                      <div>
                        <p className="text-xs text-gray-500 font-medium uppercase">Sẵn sàng làm việc</p>
                        <p className="text-sm font-semibold text-gray-900">{candidate.availability}</p>
                      </div>
                    </div>
                  )}
                  {candidate.employmentType && candidate.employmentType.length > 0 && (
                     <div className="flex items-start gap-3">
                      <Building className="w-4 h-4 text-gray-400 mt-1" />
                      <div>
                        <p className="text-xs text-gray-500 font-medium uppercase">Loại hình</p>
                        <p className="text-sm font-semibold text-gray-900">{candidate.employmentType.join(', ')}</p>
                      </div>
                    </div>
                  )}
                </div>
            </div>

            {/* Skills */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
               <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                 <Award className="w-5 h-5 text-[#0A65CC]" />
                 Kỹ năng
               </h3>
               <div className="flex flex-wrap gap-2">
                 {candidate.skills.map((skill, idx) => (
                   <div key={idx} className="bg-gray-50 text-gray-700 px-3 py-2 rounded-lg text-sm border border-gray-100 w-full hover:border-blue-200 transition-colors">
                     <div className="flex justify-between items-center mb-1">
                        <span className="font-semibold">{skill.name}</span>
                        {skill.level && <span className="text-xs bg-white border border-gray-200 px-1.5 py-0.5 rounded">{skill.level}</span>}
                     </div>
                     <div className="flex gap-2 text-xs text-gray-500">
                        {skill.category && <span>{skill.category}</span>}
                        {skill.category && skill.years && <span>•</span>}
                        {skill.years && <span>{skill.years} năm</span>}
                     </div>
                   </div>
                 ))}
                 {candidate.skills.length === 0 && <p className="text-sm text-gray-400 italic">Chưa cập nhật kỹ năng</p>}
               </div>
            </div>

            {/* Languages */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
               <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                 <Globe className="w-5 h-5 text-[#0A65CC]" />
                 Ngôn ngữ
               </h3>
               <div className="space-y-3">
                 {candidate.languages.map((lang, idx) => (
                   <div key={idx} className="flex justify-between items-center text-sm">
                     <span className="font-medium text-gray-700">{lang.name}</span>
                     <span className="text-gray-500 bg-gray-50 px-2 py-0.5 rounded">{lang.level}</span>
                   </div>
                 ))}
                 {candidate.languages.length === 0 && <p className="text-sm text-gray-400 italic">Chưa cập nhật ngôn ngữ</p>}
               </div>
            </div>

            {/* Tags */}
            {candidate.tags && candidate.tags.length > 0 && (
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Bookmark className="w-5 h-5 text-[#0A65CC]" />
                  Tags
                </h3>
                <div className="flex flex-wrap gap-2">
                  {candidate.tags.map((tag, idx) => (
                    <span key={idx} className="text-xs font-medium bg-blue-50 text-blue-600 px-2.5 py-1 rounded-full">
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Status Metadata */}
            <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
               <div className="flex justify-between items-center text-sm mb-2">
                  <span className="text-gray-500">Trạng thái hồ sơ</span>
                  <span className={`font-semibold px-2 py-0.5 rounded ${candidate.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'}`}>
                    {candidate.status === 'published' ? 'Công khai' : 'Nháp/Riêng tư'}
                  </span>
               </div>
               <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-500">ID Hồ sơ</span>
                  <span className="font-mono text-gray-700">#{candidate.id.slice(-6).toUpperCase()}</span>
               </div>
            </div>

          </div>

          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Summary */}
            <section className="bg-white rounded-xl p-6 md:p-8 shadow-sm border border-gray-100">
               <h3 className="text-lg font-bold text-gray-900 mb-4">Giới thiệu</h3>
               <p className="text-gray-600 leading-relaxed whitespace-pre-line">
                 {candidate.summary || <span className="italic text-gray-400">Chưa có thông tin giới thiệu.</span>}
               </p>
            </section>

            {/* Experience */}
            <section className="bg-white rounded-xl p-6 md:p-8 shadow-sm border border-gray-100">
               <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
                 <Briefcase className="w-5 h-5 text-[#0A65CC]" />
                 Kinh nghiệm làm việc
               </h3>
               
               <div className="space-y-8 relative before:absolute before:left-[21px] before:top-2 before:bottom-2 before:w-[2px] before:bg-gray-100">
                  {candidate.experiences.map((exp, idx) => (
                    <div key={idx} className="relative pl-10 md:pl-12 group">
                       <div className="absolute left-[13px] top-1.5 w-[18px] h-[18px] rounded-full border-4 border-white bg-gray-300 group-hover:bg-[#0A65CC] transition-colors shadow-sm"></div>
                       <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-2">
                          <div>
                            <h4 className="font-bold text-gray-900 text-lg">{exp.title}</h4>
                            <div className="flex items-center gap-2 text-[#0A65CC] font-medium">
                               <span>{exp.company}</span>
                               {exp.employmentType && <span className="text-xs bg-blue-50 px-2 py-0.5 rounded-full text-blue-600">{exp.employmentType}</span>}
                            </div>
                          </div>
                          <span className="text-sm text-gray-500 bg-gray-50 px-3 py-1 rounded-full mt-1 sm:mt-0 w-fit">
                             {formatDate(exp.from)} - {exp.isCurrent ? 'Hiện tại' : formatDate(exp.to)}
                          </span>
                       </div>
                       
                       {exp.location && <p className="text-sm text-gray-400 mb-3 flex items-center gap-1"><MapPin className="w-3 h-3"/> {exp.location}</p>}
                       
                       {/* Responsibilities */}
                       {exp.responsibilities && exp.responsibilities.length > 0 && (
                         <ul className="space-y-1.5 mt-3 mb-3">
                           {exp.responsibilities.map((resp, rIdx) => (
                             <li key={rIdx} className="text-gray-600 text-sm flex items-start gap-2">
                                <span className="mt-1.5 w-1.5 h-1.5 bg-gray-400 rounded-full flex-shrink-0"></span>
                                <span className="leading-relaxed">{resp}</span>
                             </li>
                           ))}
                         </ul>
                       )}

                       {/* Achievements */}
                       {exp.achievements && exp.achievements.length > 0 && (
                          <div className="mt-3 bg-green-50 p-3 rounded-lg border border-green-100">
                             <h5 className="text-xs font-bold text-green-800 uppercase mb-2">Thành tựu</h5>
                             <ul className="space-y-1">
                                {exp.achievements.map((ach, aIdx) => (
                                    <li key={aIdx} className="text-green-700 text-sm flex items-start gap-2">
                                        <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                                        <span>{ach}</span>
                                    </li>
                                ))}
                             </ul>
                          </div>
                       )}

                       {/* Tech Tags */}
                       {exp.tags && exp.tags.length > 0 && (
                          <div className="flex flex-wrap gap-2 mt-3">
                             {exp.tags.map((tag, tIdx) => (
                                <span key={tIdx} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">#{tag}</span>
                             ))}
                          </div>
                       )}
                    </div>
                  ))}
                  {candidate.experiences.length === 0 && <p className="pl-10 text-gray-400 italic">Chưa cập nhật kinh nghiệm.</p>}
               </div>
            </section>

            {/* Education */}
            <section className="bg-white rounded-xl p-6 md:p-8 shadow-sm border border-gray-100">
               <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
                 <GraduationCap className="w-5 h-5 text-[#0A65CC]" />
                 Học vấn
               </h3>
               <div className="space-y-6">
                 {candidate.education.map((edu, idx) => (
                   <div key={idx} className="flex gap-4 group">
                      <div className="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center text-[#0A65CC] flex-shrink-0">
                        <Building className="w-6 h-6" />
                      </div>
                      <div className="flex-1">
                         <div className="flex justify-between items-start">
                            <div>
                               <h4 className="font-bold text-gray-900">{edu.school}</h4>
                               <p className="text-gray-600">{edu.degree} - {edu.major}</p>
                            </div>
                            <span className="text-sm text-gray-500 italic whitespace-nowrap">
                              {edu.from ? new Date(edu.from).getFullYear() : ''} - {edu.to ? new Date(edu.to).getFullYear() : 'Present'}
                            </span>
                         </div>
                         {edu.gpa && <p className="text-sm text-gray-500 mt-1">GPA: {edu.gpa}</p>}
                      </div>
                   </div>
                 ))}
                 {candidate.education.length === 0 && <p className="text-gray-400 italic">Chưa cập nhật học vấn.</p>}
               </div>
            </section>

            {/* Projects */}
            <section className="bg-white rounded-xl p-6 md:p-8 shadow-sm border border-gray-100">
               <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
                 <CheckCircle2 className="w-5 h-5 text-[#0A65CC]" />
                 Dự án nổi bật
               </h3>
               <div className="grid gap-4">
                 {candidate.projects.map((proj, idx) => (
                   <div key={idx} className="border border-gray-100 rounded-xl p-5 hover:border-blue-200 transition-colors bg-gray-50/30">
                      <div className="flex justify-between items-start mb-2">
                         <h4 className="font-bold text-gray-900 text-lg">{proj.name}</h4>
                         {proj.url && (
                           <a href={proj.url} target="_blank" rel="noopener noreferrer" className="text-[#0A65CC] hover:underline flex items-center gap-1 text-sm">
                             Demo <ExternalLink className="w-3 h-3" />
                           </a>
                         )}
                      </div>
                      <p className="text-sm text-gray-500 mb-3 italic">{proj.role} • {formatDate(proj.from)} - {formatDate(proj.to)}</p>
                      
                      <p className="text-gray-600 text-sm mb-3">{proj.description}</p>
                      
                      {/* Project Metrics */}
                      {proj.metrics && proj.metrics.length > 0 && (
                        <div className="mb-3">
                           <ul className="list-disc pl-4 space-y-1">
                              {proj.metrics.map((m, mIdx) => (
                                 <li key={mIdx} className="text-xs text-green-700 font-medium">{m}</li>
                              ))}
                           </ul>
                        </div>
                      )}

                      {/* Tech Stack */}
                      {proj.techStack && (
                        <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-200/50">
                          {proj.techStack.map((tech, tIdx) => (
                            <span key={tIdx} className="text-xs px-2 py-0.5 bg-white border border-gray-200 rounded text-gray-600 font-medium">
                              {tech}
                            </span>
                          ))}
                        </div>
                      )}
                   </div>
                 ))}
                 {candidate.projects.length === 0 && <p className="text-gray-400 italic">Chưa cập nhật dự án.</p>}
               </div>
            </section>

          </div>
        </div>
      </div>

      {/* Edit Modal */}
      {candidate && (
        <EditCvModal 
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          cv={getEditCvObject()}
          onSave={handleSaveCv}
          onDelete={() => {}} 
          isSaving={isSaving}
        />
      )}
    </div>
  );
};

export default CandidateDetail;
