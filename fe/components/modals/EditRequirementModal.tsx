import React, { useState, useMemo } from 'react';
import { X, Trash2, UploadCloud, Edit3, AlertCircle } from 'lucide-react';
import ProfileForm from '../profile/ProfileForm';
import BdfUploadParser from '../profile/BdfUploadParser';
import ConfirmDialog from '../common/ConfirmDialog';
import { JobRequirement } from '../../types';

interface EditRequirementModalProps {
  isOpen: boolean;
  onClose: () => void;
  req: JobRequirement;
  onSave: (updatedData: any) => void;
  onDelete: (req: JobRequirement) => void;
  isSaving: boolean;
}

const EditRequirementModal: React.FC<EditRequirementModalProps> = ({ 
  isOpen, onClose, req, onSave, onDelete, isSaving 
}) => {
  const [activeTab, setActiveTab] = useState<'manual' | 'upload'>('manual');
  const [formData, setFormData] = useState<any>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);

  // Helper to extract salary from criteria list to pre-fill form
  // Memoized to prevent re-creating the object on every render, which causes ProfileForm to reset
  const initialFormData = useMemo(() => {
    if (formData) return formData; // Return processed data from upload if exists

    const salaryCriteria = req.criteriaList.find(c => 
      c.toLowerCase().includes('lương') || 
      c.toLowerCase().includes('salary') ||
      c.includes('$') ||
      c.includes('triệu')
    );
    const otherCriteria = req.criteriaList.filter(c => c !== salaryCriteria);

    return {
      title: req.title,
      skills: req.skills.join(', '),
      experienceLevel: req.experienceLevel,
      location: req.location,
      salaryRange: salaryCriteria ? salaryCriteria.replace(/^(Lương|Salary|Mức lương):?\s*/i, '') : '',
      criteria: otherCriteria.map(c => `- ${c}`).join('\n')
    };
  }, [req, formData]);

  if (!isOpen) return null;

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
    setParseError(null);
  };

  const handleConfirmDelete = () => {
    setShowDeleteConfirm(false);
    onDelete(req);
    onClose();
  };

  return (
    <div 
      className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200 pointer-events-auto"
      role="dialog"
      aria-modal="true"
      onClick={onClose} // Allow closing by clicking backdrop
    >
      <div 
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 duration-300 pointer-events-auto cursor-default"
        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside
      >
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50">
          <h3 className="text-lg font-bold text-gray-900">Chỉnh sửa yêu cầu tuyển dụng</h3>
          <button 
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Đóng"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
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
            Tải lên BDF / JD
            {activeTab === 'upload' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#0A65CC]" />
            )}
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-white">
          {parseError && (
            <div className="mb-4 bg-red-50 text-red-600 px-4 py-3 rounded-lg flex items-center gap-2 text-sm">
              <AlertCircle className="w-4 h-4" />
              {parseError}
            </div>
          )}

          {activeTab === 'manual' ? (
            <ProfileForm 
              initialData={initialFormData}
              onSubmit={onSave}
              isSubmitting={isSaving}
              mode="recruiter"
              isEditMode={true}
            />
          ) : (
            <div className="py-4">
              <div className="mb-6 text-center max-w-lg mx-auto">
                <p className="text-gray-500 text-sm mb-4">
                  Tải lên bản mô tả công việc (JD) hoặc hồ sơ yêu cầu (BDF) để hệ thống tự động cập nhật thông tin.
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
        </div>

        {/* Footer Actions */}
        {activeTab === 'manual' && (
           <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex justify-between items-center">
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                className="flex items-center gap-2 text-red-600 hover:text-red-700 hover:bg-red-50 px-4 py-2 rounded-lg transition-colors font-medium text-sm"
              >
                <Trash2 className="w-4 h-4" />
                Xóa yêu cầu
              </button>
           </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmDialog 
        isOpen={showDeleteConfirm}
        title="Xóa yêu cầu tuyển dụng?"
        message={`Bạn có chắc chắn muốn xóa "${req.title}"? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        cancelLabel="Hủy"
        onConfirm={handleConfirmDelete}
        onCancel={() => setShowDeleteConfirm(false)}
        isDestructive={true}
      />
    </div>
  );
};

export default EditRequirementModal;