
import React, { useState, useMemo } from 'react';
import { X, Trash2, UploadCloud, Edit3, AlertCircle, Loader2 } from 'lucide-react';
import ProfileForm from '../profile/ProfileForm';
import BdfUploadParser from '../profile/BdfUploadParser';
import ConfirmDialog from '../common/ConfirmDialog';
import { UserCV } from '../../types';

interface EditCvModalProps {
  isOpen: boolean;
  onClose: () => void;
  cv: UserCV;
  onSave: (updatedData: any) => void;
  onDelete: (cv: UserCV) => void;
  isSaving: boolean;
  isLoading?: boolean;
}

// Local helper for robust deep cloning with cycle detection
const safeDeepClone = (obj: any, seen = new WeakSet()): any => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj);
  
  if (seen.has(obj)) return undefined; // Break cycle
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

const EditCvModal: React.FC<EditCvModalProps> = ({ 
  isOpen, onClose, cv, onSave, onDelete, isSaving, isLoading 
}) => {
  const [activeTab, setActiveTab] = useState<'manual' | 'upload'>('manual');
  const [formData, setFormData] = useState<any>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  if (!isOpen) return null;

  // Memoize initial data to prevent form resetting on re-renders
  // Use safeDeepClone to ensure no reference cycles passed to form state
  const initialFormData = useMemo(() => {
    // 1. Prefer details fetched from backend (if available)
    if (cv.details) {
        return safeDeepClone(cv.details);
    }
    
    // 2. Fallback to uploaded parsed data
    if (formData) return formData;
    
    // 3. Fallback to basic info from list view
    return {
      fullname: cv.name || '',
      headline: cv.title || '',
      skills: Array.isArray(cv.skills) 
        ? cv.skills.map(s => (typeof s === 'string' ? { name: s, level: 'Intermediate' } : s)) 
        : [],
      location: { city: cv.location || '' },
      experienceLevel: cv.experienceLevel || '',
    };
  }, [cv, formData]);

  const handleParseComplete = (data: any) => {
    setFormData({
      title: data.title,
      skills: data.skills,
      experienceLevel: data.experienceLevel,
      location: data.location,
      salaryRange: data.salaryRange || '',
      criteria: data.criteria || ''
    });
    setActiveTab('manual');
  };

  const handleConfirmDelete = () => {
    setShowDeleteConfirm(false);
    onDelete(cv);
    onClose();
  };

  return (
    <div 
      className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200 pointer-events-auto"
      role="dialog"
      aria-modal="true"
      onClick={onClose} // Backdrop close handler
    >
      <div 
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 duration-300 pointer-events-auto cursor-default"
        onClick={(e) => e.stopPropagation()} // Prevent bubbling to backdrop
      >
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50">
          <h3 className="text-lg font-bold text-gray-900">Chỉnh sửa hồ sơ</h3>
          <button 
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs - Only show if not loading */}
        {!isLoading && (
          <div className="flex border-b border-gray-100 bg-white">
            <button
              onClick={() => setActiveTab('manual')}
              className={`flex-1 py-4 text-center font-semibold text-sm flex items-center justify-center gap-2 transition-colors relative
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
              className={`flex-1 py-4 text-center font-semibold text-sm flex items-center justify-center gap-2 transition-colors relative
                ${activeTab === 'upload' ? 'text-[#0A65CC] bg-blue-50/30' : 'text-gray-500 hover:bg-gray-50'}
              `}
            >
              <UploadCloud className="w-4 h-4" />
              Tải lên CV
              {activeTab === 'upload' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#0A65CC]" />
              )}
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-white relative">
          {isLoading ? (
             <div className="flex flex-col items-center justify-center h-full py-20">
                <Loader2 className="w-12 h-12 text-[#0A65CC] animate-spin mb-4" />
                <p className="text-gray-500 font-medium">Đang tải thông tin chi tiết...</p>
             </div>
          ) : (
             <>
               {activeTab === 'manual' ? (
                <ProfileForm 
                  initialData={initialFormData}
                  onSubmit={onSave}
                  isSubmitting={isSaving}
                  mode="candidate"
                  isEditMode={true}
                />
              ) : (
                <div className="py-4">
                  <div className="mb-6 text-center max-w-lg mx-auto">
                    <p className="text-gray-500 text-sm mb-4">
                      Tải lên CV (PDF/Word) để hệ thống tự động cập nhật thông tin kỹ năng và kinh nghiệm.
                    </p>
                  </div>
                  <BdfUploadParser onParseComplete={handleParseComplete} />
                  <div className="mt-6 text-center">
                    <button 
                      onClick={() => setActiveTab('manual')}
                      className="text-sm text-[#0A65CC] hover:underline"
                    >
                      Quay lại nhập thủ công
                    </button>
                  </div>
                </div>
              )}
             </>
          )}
        </div>

         {/* Footer Actions */}
         {!isLoading && activeTab === 'manual' && (
           <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex justify-between items-center">
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                className="flex items-center gap-2 text-red-600 hover:text-red-700 hover:bg-red-50 px-4 py-2 rounded-lg transition-colors font-medium text-sm"
              >
                <Trash2 className="w-4 h-4" />
                Xóa hồ sơ
              </button>
           </div>
        )}
      </div>

       {/* Delete Confirmation Modal */}
       <ConfirmDialog 
        isOpen={showDeleteConfirm}
        title="Xóa hồ sơ?"
        message={`Bạn có chắc chắn muốn xóa "${cv.name}"? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        cancelLabel="Hủy"
        onConfirm={handleConfirmDelete}
        onCancel={() => setShowDeleteConfirm(false)}
        isDestructive={true}
      />
    </div>
  );
};

export default EditCvModal;
