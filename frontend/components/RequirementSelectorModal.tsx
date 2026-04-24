
import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { JobRequirement } from '../types';
import { X, Plus, Undo2, AlertCircle, Loader2 } from 'lucide-react';
import RequirementCard from './RequirementCard';
import ConfirmDialog from './common/ConfirmDialog';
import EditRequirementModal from './modals/EditRequirementModal';
import api from '../lib/api';

interface RequirementSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectReq: (req: JobRequirement) => void;
  onSkip: () => void;
  requirements: JobRequirement[]; // Kept for prop compatibility, but we fetch fresh data
}

// Interface to hold original backend data for restoration/editing
interface ExtendedJobRequirement extends JobRequirement {
  originalData?: any;
}

const RequirementSelectorModal: React.FC<RequirementSelectorModalProps> = ({ 
  isOpen, onClose, onSelectReq, onSkip 
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  // We assume the logged-in user owns the data fetched from /jobs/user/me
  const CURRENT_USER_ID = "me"; 
  
  // Local state
  const [localReqs, setLocalReqs] = useState<ExtendedJobRequirement[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Action states
  const [editingReq, setEditingReq] = useState<ExtendedJobRequirement | null>(null);
  const [deletingReq, setDeletingReq] = useState<ExtendedJobRequirement | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  
  // Toast state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info'; action?: () => void } | null>(null);
  const [deletedItemBackup, setDeletedItemBackup] = useState<ExtendedJobRequirement | null>(null);

  // Fetch Data when modal opens
  useEffect(() => {
    if (isOpen) {
      fetchRequirements();
      document.body.style.overflow = 'hidden';
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape' && !editingReq && !deletingReq) {
          onClose();
        }
      };
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen, editingReq, deletingReq]);

  const fetchRequirements = async () => {
    setLoading(true);
    try {
      const res = await api.get('/jobs/user/me');
      // Backend may return array directly or { data: [...] } or { items: [...] }
      const rawData = Array.isArray(res.data) 
        ? res.data 
        : (res.data?.data || res.data?.items || []);

      const mappedReqs: ExtendedJobRequirement[] = rawData.map((item: any) => {
        // Build Criteria List for UI Card
        const criteriaList: string[] = [];
        
        // 1. Salary
        if (item.salary && typeof item.salary === 'object' && (item.salary.min || item.salary.max)) {
           const currency = item.salary.currency || '';
           const min = item.salary.min ? item.salary.min.toLocaleString() : '';
           const max = item.salary.max ? item.salary.max.toLocaleString() : '';
           criteriaList.push(`Lương: ${min} - ${max} ${currency}`);
        }

        // 2. Location
        const loc = item.companyLocation || (item.location?.city) || 'Chưa xác định';
        criteriaList.push(loc);

        // 3. Employment Type
        if (Array.isArray(item.employmentType) && item.employmentType.length > 0) {
          criteriaList.push(item.employmentType.join(', '));
        }

        // 4. Requirements (limit to top 3 for card view)
        if (Array.isArray(item.requirements)) {
           item.requirements.slice(0, 3).forEach((r: string) => criteriaList.push(r));
        }

        // Map Skills (Backend returns objects {name, _id}, UI often needs strings or objects)
        const skillNames = Array.isArray(item.skills) 
          ? item.skills.map((s: any) => typeof s === 'string' ? s : s.name)
          : [];

        return {
          id: item._id || item.id,
          title: item.title || 'Untitled Position',
          skills: skillNames,
          experienceLevel: item.seniority || item.experienceLevel || 'Mid-Level',
          location: loc,
          createdAt: item.createdAt ? new Date(item.createdAt).toLocaleDateString('vi-VN') : 'Mới tạo',
          openPositions: 1, // field might not exist in backend
          iconType: 'Code', // fallback icon
          color: 'bg-blue-500', // fallback color
          criteriaList: criteriaList,
          ownerId: CURRENT_USER_ID, // Owned by "me"
          originalData: item // Store full backend object
        };
      });

      setLocalReqs(mappedReqs);
    } catch (error) {
      console.error('RequirementSelectorModal error', error);
      setToast({ message: 'Không tải được yêu cầu tuyển dụng', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Handle Toast Timeout
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => {
        setToast(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  const handleCreateNew = () => {
    onClose();
    navigate('/create-profile?type=req');
  };

  // --- CRUD Handlers ---

  const handleRename = async (req: JobRequirement, newTitle: string) => {
    const originalTitle = req.title;
    
    // Optimistic Update
    setLocalReqs(prev => prev.map(r => r.id === req.id ? { ...r, title: newTitle } : r));

    try {
      // Try specific rename endpoint first
      await api.patch(`/jobs/${req.id}/rename`, { title: newTitle });
      setToast({ message: 'Đổi tên thành công', type: 'success' });
    } catch (error) {
      console.error("Rename failed, attempting fallback PUT", error);
      
      try {
         // Fallback to standard update if specific rename not available
         await api.put(`/jobs/${req.id}`, { title: newTitle });
         setToast({ message: 'Đổi tên thành công', type: 'success' });
      } catch (fallbackError) {
         console.error("Rename fallback failed", fallbackError);
         // Rollback
         setLocalReqs(prev => prev.map(r => r.id === req.id ? { ...r, title: originalTitle } : r));
         setToast({ message: 'Đổi tên thất bại. Vui lòng thử lại.', type: 'error' });
      }
    }
  };

  const handleEdit = (req: ExtendedJobRequirement) => {
    setEditingReq(req);
  };

  const handleSaveEdit = async (formData: any) => {
    if (!editingReq) return;
    setIsSaving(true);
    
    try {
      // Use PUT /jobs/:id to update
      // Ensure we map the form data back to what backend expects if needed,
      // but ProfileForm usually outputs compatible DTO structure.
      await api.put(`/jobs/${editingReq.id}`, formData);
      
      setToast({ message: 'Cập nhật yêu cầu thành công', type: 'success' });
      setEditingReq(null);
      
      // Refresh list to get consistent state
      await fetchRequirements();

    } catch (error) {
      console.error("Update failed", error);
      setToast({ message: 'Cập nhật thất bại. Vui lòng thử lại.', type: 'error' });
    } finally {
      setIsSaving(false);
    }
  };

  const executeDelete = async (itemToDelete: ExtendedJobRequirement) => {
    setDeletedItemBackup(itemToDelete);

    // Optimistic Remove UI
    setLocalReqs(prev => prev.filter(r => r.id !== itemToDelete.id));

    setToast({
      message: `Đã xóa "${itemToDelete.title}"`,
      type: 'info',
      action: () => handleUndoDelete(itemToDelete)
    });

    try {
      await api.delete(`/jobs/${itemToDelete.id}`);
    } catch (error) {
      console.error("Delete failed", error);
      // Rollback
      setLocalReqs(prev => [...prev, itemToDelete]);
      setToast({ message: 'Xóa thất bại.', type: 'error' });
    }
  };

  const handleDeleteClick = (req: ExtendedJobRequirement) => {
    setDeletingReq(req);
  };

  const handleConfirmDelete = async () => {
    if (!deletingReq) return;
    const req = deletingReq;
    setDeletingReq(null);
    executeDelete(req);
  };

  const handleUndoDelete = async (item: ExtendedJobRequirement) => {
    // Optimistic Restore
    setLocalReqs(prev => [item, ...prev]); 
    setDeletedItemBackup(null);
    setToast(null); // Clear previous toast

    try {
      // Prepare payload to recreate the job
      // We strip system fields like _id, createdAt, updatedAt
      const payload = { ...item.originalData };
      delete payload._id;
      delete payload.id;
      delete payload.createdAt;
      delete payload.updatedAt;
      delete payload.__v;
      delete payload.views;
      delete payload.applicationsCount;

      // Re-create via POST
      await api.post('/jobs', payload);
      
      setToast({ message: 'Đã hoàn tác xóa', type: 'success' });
      // Refresh to ensure we have the new ID
      fetchRequirements();
    } catch (error) {
      console.error("Restore failed", error);
      // Rollback removal of item
      setLocalReqs(prev => prev.filter(r => r.id !== item.id));
      setToast({ message: 'Hoàn tác thất bại.', type: 'error' });
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      onClick={handleBackdropClick}
    >
      <div 
        ref={modalRef}
        className="bg-[#F8F9FB] rounded-[24px] shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-8 py-6 bg-white border-b border-gray-100 shrink-0">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Chọn yêu cầu tuyển dụng</h2>
            <p className="text-sm text-gray-500 mt-1">Quản lý các Job Description của bạn để tìm ứng viên.</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Đóng"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="overflow-y-auto p-6 md:p-8 custom-scrollbar relative">
          
          {/* Toast Notification */}
          {toast && (
            <div className={`
              absolute top-4 left-1/2 -translate-x-1/2 z-20 px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 text-sm font-medium animate-in slide-in-from-top-4 fade-in
              ${toast.type === 'error' ? 'bg-red-600 text-white' : 'bg-gray-900 text-white'}
            `}>
              {toast.type === 'error' && <AlertCircle className="w-4 h-4" />}
              <span>{toast.message}</span>
              {toast.action && (
                <button 
                  onClick={toast.action}
                  className="flex items-center gap-1 bg-white/20 hover:bg-white/30 px-2 py-1 rounded text-xs transition-colors"
                >
                  <Undo2 className="w-3 h-3" /> Hoàn tác
                </button>
              )}
            </div>
          )}

          {loading ? (
             <div className="flex flex-col items-center justify-center py-20">
               <Loader2 className="w-10 h-10 text-[#0A65CC] animate-spin mb-4" />
               <p className="text-gray-500">Đang tải danh sách...</p>
             </div>
          ) : localReqs.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {localReqs.map((req) => (
                <RequirementCard 
                  key={req.id} 
                  req={req} 
                  onSelect={onSelectReq}
                  onEdit={() => handleEdit(req)}
                  onDelete={() => handleDeleteClick(req)}
                  onRename={handleRename}
                  currentUserId={CURRENT_USER_ID}
                />
              ))}
              
              <button 
                onClick={handleCreateNew}
                className="group flex flex-col items-center justify-center min-h-[320px] rounded-2xl border-2 border-dashed border-gray-200 bg-white hover:border-[#0A65CC] hover:bg-blue-50/30 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/50"
              >
                <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Plus className="w-8 h-8 text-[#0A65CC]" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 group-hover:text-[#0A65CC] mb-1">Tạo yêu cầu mới</h3>
              </button>
            </div>
          ) : (
             <div className="flex flex-col items-center justify-center py-16 text-center">
               <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                  <Plus className="w-10 h-10 text-gray-400" />
               </div>
               <h3 className="text-xl font-bold text-gray-900 mb-2">Chưa có yêu cầu nào</h3>
               <button 
                onClick={handleCreateNew}
                className="bg-[#0A65CC] text-white px-8 py-3 rounded-full font-bold hover:bg-blue-700 transition"
               >
                 Tạo yêu cầu mới
               </button>
             </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-white border-t border-gray-100 text-center shrink-0">
             <button 
                onClick={onSkip} 
                className="text-sm font-medium text-gray-500 hover:text-[#0A65CC] transition-colors"
             >
               Bỏ qua, tôi muốn tìm kiếm thủ công
             </button>
        </div>
      </div>

      {/* Sub Modals */}
      {editingReq && (
        <EditRequirementModal 
          isOpen={!!editingReq}
          onClose={() => setEditingReq(null)}
          req={editingReq}
          onSave={handleSaveEdit}
          onDelete={executeDelete} // Pass direct delete handler for flexibility
          isSaving={isSaving}
        />
      )}

      {deletingReq && (
        <ConfirmDialog 
          isOpen={!!deletingReq}
          title="Xóa yêu cầu tuyển dụng?"
          message={`Bạn có chắc chắn muốn xóa "${deletingReq.title}"? Hành động này không thể hoàn tác.`}
          confirmLabel="Xóa"
          cancelLabel="Hủy"
          onConfirm={handleConfirmDelete}
          onCancel={() => setDeletingReq(null)}
          isDestructive={true}
        />
      )}
    </div>
  );
};

export default RequirementSelectorModal;
