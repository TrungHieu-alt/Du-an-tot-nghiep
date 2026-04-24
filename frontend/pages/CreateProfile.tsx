
import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { FileText, Edit3, ArrowLeft, Loader2 } from 'lucide-react';
import ProfileForm from '../components/profile/ProfileForm';
import BdfUploadParser from '../components/profile/BdfUploadParser';
import { CreateCvDto } from '../types';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';

// Local safe clone to ensure localStorage writes don't crash on cycles
const safeDeepClone = (obj: any, seen = new WeakSet()): any => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj);
  
  if (seen.has(obj)) return undefined;
  seen.add(obj);

  if (Array.isArray(obj)) {
    return obj.map(v => safeDeepClone(v, seen)).filter(v => v !== undefined);
  }

  const res: any = {};
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const val = safeDeepClone(obj[key], seen);
      if (val !== undefined) res[key] = val;
    }
  }
  return res;
};

const CreateProfile: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  
  const type = searchParams.get('type');
  const isCandidateMode = type === 'cv';
  
  const [activeTab, setActiveTab] = useState<'manual' | 'upload'>('manual');
  const [prefilledData, setPrefilledData] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Set default user data if available
  React.useEffect(() => {
    if (isCandidateMode && user && !prefilledData) {
      setPrefilledData({
        userId: user.id,
        fullname: user.name,
        email: user.email,
        phone: user.phone,
        location: { city: user.preferredLocation },
        skills: user.skills?.map(s => ({ name: s, level: 'Intermediate', years: 1 }))
      });
    }
  }, [user, isCandidateMode, prefilledData]);

  const handleFormSubmit = async (resultData: any) => {
    setIsSubmitting(true);
    
    try {
        if (isCandidateMode) {
            // --- CANDIDATE FLOW ---
            const newCvId = resultData._id || resultData.id;
            
            // Save to localStorage for demo persistence
            try {
                const existingStr = localStorage.getItem('demo_cvs');
                const existing = existingStr ? JSON.parse(existingStr) : [];
                const safeCv = safeDeepClone(resultData);
                localStorage.setItem('demo_cvs', JSON.stringify([safeCv, ...existing]));
            } catch (e) {
                console.error("Failed to save CV to local storage", e);
            }

            console.log("Redirecting to jobs with CV:", newCvId);
            if (newCvId) {
                // FORCE REDIRECT
                navigate(`/jobs?cv=${newCvId}`);
            } else {
                navigate(`/jobs?manual=true`);
            }

        } else {
            // --- RECRUITER FLOW ---
            const newReqId = resultData._id || resultData.id || `req_${Date.now()}`;
            
            try {
                const existingStr = localStorage.getItem('demo_requirements');
                const existing = existingStr ? JSON.parse(existingStr) : [];
                const safeReq = safeDeepClone(resultData);
                localStorage.setItem('demo_requirements', JSON.stringify([safeReq, ...existing]));
            } catch (e) {
                console.error("Failed to save requirement to local storage", e);
            }
            
            navigate(`/candidates?req=${newReqId}`);
        }
    } catch (err) {
        console.error("Error during navigation logic", err);
        setIsSubmitting(false);
        alert("Có lỗi xảy ra khi chuyển hướng.");
    }
  };

  const handleParseComplete = async (data: any) => {
    setIsSubmitting(true); // Start loading UI immediately

    try {
        // 1. CASE A: Backend already created the CV (ID exists)
        if (data._id || data.id) {
            console.log("Upload returned existing ID, redirecting...");
            await handleFormSubmit(data);
            return;
        }

        // 2. CASE B: Need to create CV from parsed text
        if (isCandidateMode) {
            // Construct payload with safe defaults to ensure API success
            const mappedData: Partial<CreateCvDto> = {
                fullname: data.fullname || user?.name || "Hồ sơ của tôi", // Fallback mandatory field
                email: data.email || user?.email,
                phone: data.phone || user?.phone,
                headline: data.headline || data.targetRole || "Open to work",
                summary: data.summary,
                location: {
                    city: data.location?.city || (typeof data.location === 'string' ? data.location : '') || '',
                    state: data.location?.state || '',
                    country: data.location?.country || ''
                },
                targetRole: data.targetRole,
                skills: Array.isArray(data.skills) ? data.skills : [],
                experiences: Array.isArray(data.experiences) ? data.experiences : [],
                education: Array.isArray(data.education) ? data.education : [],
                projects: Array.isArray(data.projects) ? data.projects : [],
                certifications: Array.isArray(data.certifications) ? data.certifications : [],
                languages: Array.isArray(data.languages) ? data.languages : [],
                tags: data.tags || [],
                employmentType: Array.isArray(data.employmentType) ? data.employmentType : []
            };

            console.log("Auto-creating CV with data:", mappedData);
            
            // Call API to create
            const res = await api.post('/cv', mappedData);
            
            // Redirect immediately with new data
            if (res.data && (res.data._id || res.data.id)) {
                await handleFormSubmit(res.data);
            } else {
                throw new Error("API succeeded but returned no ID");
            }

        } else {
            // Recruiter Mode: Just fill form (standard behavior)
            setPrefilledData({
                title: data.title,
                skills: data.skills,
                experienceLevel: data.experienceLevel,
                location: data.location,
                criteria: data.criteria || (data.skills ? `- ${data.skills}` : '')
            });
            setActiveTab('manual');
            setIsSubmitting(false);
        }
    } catch (error) {
        console.error("Auto-save failed, fallback to manual review", error);
        // Only on CRITICAL failure do we show the form
        setPrefilledData(data); // Try to fill whatever we got
        setActiveTab('manual');
        setIsSubmitting(false);
        alert("Không thể tự động tạo hồ sơ. Vui lòng kiểm tra lại thông tin.");
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F7FC] py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button 
            onClick={() => navigate(-1)} 
            className="flex items-center text-gray-500 hover:text-[#0A65CC] transition-colors mb-4 text-sm font-semibold"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Quay lại
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            {isCandidateMode ? "Tạo hồ sơ ứng viên mới" : "Tạo yêu cầu tuyển dụng mới"}
          </h1>
          <p className="text-gray-500 mt-2">
            {isCandidateMode 
              ? "Cập nhật thông tin để chúng tôi giúp bạn tìm kiếm công việc phù hợp nhất." 
              : "Thiết lập tiêu chí để tìm kiếm ứng viên phù hợp nhất cho doanh nghiệp của bạn."}
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-[24px] shadow-sm border border-gray-100 overflow-hidden">
          
          {/* Tabs */}
          <div className="flex border-b border-gray-100">
            <button
              onClick={() => setActiveTab('manual')}
              className={`flex-1 py-5 text-center font-semibold text-sm flex items-center justify-center gap-2 transition-colors relative
                ${activeTab === 'manual' ? 'text-[#0A65CC] bg-blue-50/30' : 'text-gray-500 hover:bg-gray-50'}
              `}
            >
              <Edit3 className="w-4 h-4" />
              Nhập thủ công
              {activeTab === 'manual' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#0A65CC]" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`flex-1 py-5 text-center font-semibold text-sm flex items-center justify-center gap-2 transition-colors relative
                ${activeTab === 'upload' ? 'text-[#0A65CC] bg-blue-50/30' : 'text-gray-500 hover:bg-gray-50'}
              `}
            >
              <FileText className="w-4 h-4" />
              Tải lên {isCandidateMode ? 'CV' : 'BDF / JD'}
              {activeTab === 'upload' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#0A65CC]" />
              )}
            </button>
          </div>

          {/* Content Area */}
          <div className="p-8">
            {activeTab === 'manual' ? (
              <ProfileForm 
                initialData={prefilledData} 
                onSubmit={handleFormSubmit}
                isSubmitting={isSubmitting}
                mode={isCandidateMode ? 'candidate' : 'recruiter'}
              />
            ) : (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="mb-6 text-center max-w-lg mx-auto">
                  <h3 className="text-lg font-bold text-gray-900 mb-2">Tự động điền từ tài liệu</h3>
                  <p className="text-gray-500 text-sm">
                    {isCandidateMode 
                      ? "Tải lên CV (PDF/Word) để hệ thống tự động trích xuất kỹ năng và kinh nghiệm của bạn."
                      : "Tải lên bản mô tả công việc (JD) hoặc hồ sơ yêu cầu (BDF) để hệ thống tự động trích xuất thông tin."}
                  </p>
                </div>
                
                {isSubmitting ? (
                    <div className="flex flex-col items-center justify-center py-12">
                        <Loader2 className="w-12 h-12 text-[#0A65CC] animate-spin mb-4" />
                        <p className="text-[#0A65CC] font-medium text-lg">Đang tạo hồ sơ và chuyển hướng...</p>
                        <p className="text-gray-500 text-sm mt-2">Vui lòng đợi trong giây lát</p>
                    </div>
                ) : (
                    <BdfUploadParser onParseComplete={handleParseComplete} />
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateProfile;
