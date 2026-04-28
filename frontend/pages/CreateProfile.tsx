
import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { FileText, Edit3, ArrowLeft, Loader2 } from 'lucide-react';
import ProfileForm from '../components/profile/ProfileForm';
import BdfUploadParser from '../components/profile/BdfUploadParser';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';
import { apiRoutes } from '../lib/api-routes';
import { getCurrentUserId } from '../lib/auth-session';
import { toCandidateResumeUpdatePayload, toJobPostUpdatePayload } from '../lib/backend-payload-mappers';

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
  const [requiresParsedCvConfirmation, setRequiresParsedCvConfirmation] = useState(false);
  const [parsedCvId, setParsedCvId] = useState<string | null>(null);

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
            let submitResult = resultData;
            let newCvId = resultData._id || resultData.id || resultData.cv_id;

            if (requiresParsedCvConfirmation || !newCvId) {
              const userId = user?.id || getCurrentUserId();
              if (!userId) {
                throw new Error('Vui lòng đăng nhập để lưu hồ sơ.');
              }

              const mappedData = toCandidateResumeUpdatePayload(
                resultData,
                prefilledData || undefined
              );
              const response = parsedCvId
                ? await api.put(apiRoutes.cv.byId(parsedCvId), mappedData)
                : await api.post(apiRoutes.cv.create(userId), mappedData);

              submitResult = response.data;
              newCvId = submitResult?._id || submitResult?.id || submitResult?.cv_id || parsedCvId;
            }
            
            // Save to localStorage for demo persistence
            try {
                const existingStr = localStorage.getItem('demo_cvs');
                const existing = existingStr ? JSON.parse(existingStr) : [];
                const safeCv = safeDeepClone(submitResult);
                localStorage.setItem('demo_cvs', JSON.stringify([safeCv, ...existing]));
            } catch (e) {
                console.error("Failed to save CV to local storage", e);
            }

            setRequiresParsedCvConfirmation(false);
            setParsedCvId(null);
            console.log("Redirecting to jobs with CV:", newCvId);
            if (newCvId) {
                // FORCE REDIRECT
                navigate(`/jobs?cv=${newCvId}`);
            } else {
                navigate(`/jobs?manual=true`);
            }

        } else {
            // --- RECRUITER FLOW ---
            let submitResult = resultData;
            let newReqId = resultData._id || resultData.id || resultData.job_id;

            if (!newReqId) {
              const recruiterId = user?.id || getCurrentUserId();
              if (!recruiterId) {
                throw new Error('Vui lòng đăng nhập để tạo yêu cầu tuyển dụng.');
              }

              const mappedData = toJobPostUpdatePayload(resultData, prefilledData || undefined);
              const response = await api.post(apiRoutes.jobs.create(recruiterId), mappedData);
              submitResult = response.data;
              newReqId = submitResult?._id || submitResult?.id || submitResult?.job_id;
            }
            
            try {
                const existingStr = localStorage.getItem('demo_requirements');
                const existing = existingStr ? JSON.parse(existingStr) : [];
                const safeReq = safeDeepClone(submitResult);
                localStorage.setItem('demo_requirements', JSON.stringify([safeReq, ...existing]));
            } catch (e) {
                console.error("Failed to save requirement to local storage", e);
            }
            
            navigate(newReqId ? `/candidates?req=${newReqId}` : '/candidates');
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
        if (isCandidateMode) {
            const uploadedCvId = data?._id || data?.id || data?.cv_id || null;
            setParsedCvId(uploadedCvId ? String(uploadedCvId) : null);
            setPrefilledData(data);
            setRequiresParsedCvConfirmation(true);
            setActiveTab('manual');
            setIsSubmitting(false);
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
        console.error("Parse handling failed, fallback to manual review", error);
        setPrefilledData(data); // Try to fill whatever we got
        setRequiresParsedCvConfirmation(isCandidateMode);
        setActiveTab('manual');
        setIsSubmitting(false);
        alert("Không thể xử lý tài liệu tự động. Vui lòng kiểm tra và lưu lại trước khi tìm kiếm.");
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
                isEditMode={true}
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
                    <BdfUploadParser mode={isCandidateMode ? 'cv' : 'jd'} onParseComplete={handleParseComplete} />
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
