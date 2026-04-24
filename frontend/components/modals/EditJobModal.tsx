
import React, { useMemo } from 'react';
import { X, Trash2 } from 'lucide-react';
import ProfileForm from '../profile/ProfileForm';
import ConfirmDialog from '../common/ConfirmDialog';

interface EditJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  job: any; // Raw job data
  onSave: (updatedData: any) => void;
  onDelete: () => void;
  isSaving: boolean;
}

const EditJobModal: React.FC<EditJobModalProps> = ({ 
  isOpen, onClose, job, onSave, onDelete, isSaving 
}) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = React.useState(false);

  // Map the normalized job data (or raw data) back to the form structure
  const initialFormData = useMemo(() => {
    if (!job) return {};
    
    // Convert array of strings back to newline separated string for textareas
    const formatList = (list?: string[]) => Array.isArray(list) ? list.map(item => `- ${item}`).join('\n') : '';
    const formatSkills = (list?: any[]) => Array.isArray(list) 
      ? list.map(s => typeof s === 'string' ? s : `${s.name}${s.level ? ':'+s.level : ''}`).join(', ')
      : '';
    
    // Handle salary object
    let salaryRange = '';
    if (job.salary) {
      if (typeof job.salary === 'string') salaryRange = job.salary;
      else if (typeof job.salary === 'object') {
         const { min, max, currency } = job.salary;
         if (min && max) salaryRange = `${min} - ${max} ${currency || ''}`;
         else if (min) salaryRange = `${min} ${currency || ''}`;
      }
    }

    // Ensure no undefined values are passed to controlled inputs
    return {
      title: job.title || '',
      experienceLevel: job.seniority || job.experienceLevel || '',
      location: job.location?.city || job.companyLocation || (typeof job.location === 'string' ? job.location : ''),
      salaryRange: salaryRange,
      
      companyName: job.companyName || job.company || '',
      companyWebsite: job.companyWebsite || '',
      companyLogoUrl: job.companyLogoUrl || '',
      companyIndustry: job.companyIndustry || '',
      
      employmentType: job.employmentType || [],
      experienceYears: job.experienceYears, // can be undefined if number, handled by input type=number
      teamSize: job.teamSize, // can be undefined if number
      department: job.department || '',
      
      description: job.description || '',
      responsibilities: formatList(job.responsibilities),
      requirements: formatList(job.requirements),
      niceToHave: formatList(job.niceToHave),
      skillsList: formatSkills(job.skills),
      
      benefits: Array.isArray(job.benefits) ? job.benefits.join(', ') : (job.benefits || ''),
      
      applyUrl: job.applyUrl || '',
      applyEmail: job.applyEmail || '',
      
      recruiterName: job.recruiter?.name || '',
      recruiterEmail: job.recruiter?.email || '',
      recruiterPhone: job.recruiter?.phone || '',
      
      remote: !!job.remote,
      tags: Array.isArray(job.tags) ? job.tags.join(', ') : ''
    };
  }, [job]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50">
          <h3 className="text-lg font-bold text-gray-900">Chỉnh sửa tin tuyển dụng</h3>
          <button 
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Content */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-white">
          <ProfileForm 
            initialData={initialFormData}
            onSubmit={onSave}
            isSubmitting={isSaving}
            mode="recruiter"
            isEditMode={true}
          />
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex justify-between items-center">
          <button
            type="button"
            onClick={() => setShowDeleteConfirm(true)}
            className="flex items-center gap-2 text-red-600 hover:text-red-700 hover:bg-red-50 px-4 py-2 rounded-lg transition-colors font-medium text-sm"
          >
            <Trash2 className="w-4 h-4" />
            Xóa tin
          </button>
        </div>
      </div>

      <ConfirmDialog 
        isOpen={showDeleteConfirm}
        title="Xóa tin tuyển dụng?"
        message={`Bạn có chắc chắn muốn xóa "${job.title}"? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        cancelLabel="Hủy"
        onConfirm={() => {
          setShowDeleteConfirm(false);
          onDelete();
        }}
        onCancel={() => setShowDeleteConfirm(false)}
        isDestructive={true}
      />
    </div>
  );
};

export default EditJobModal;
