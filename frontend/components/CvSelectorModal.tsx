
import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserCV } from '../types';
import { X, Plus, Undo2, FileText, AlertCircle, Loader2 } from 'lucide-react';
import CvCard from './CvCard';
import ConfirmDialog from './common/ConfirmDialog';
import EditCvModal from './modals/EditCvModal';
import api from '../lib/api';

interface CvSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectCv: (cv: UserCV) => void;
  onSkip: () => void;
  cvs: UserCV[]; // Kept for interface compatibility but we fetch fresh data
}

// Interface to hold original backend data for restoration
interface ExtendedUserCV extends UserCV {
  originalData?: any;
}

const CvSelectorModal: React.FC<CvSelectorModalProps> = ({ 
  isOpen, onClose, onSelectCv, onSkip 
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const [localCvs, setLocalCvs] = useState<ExtendedUserCV[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingCv, setEditingCv] = useState<ExtendedUserCV | null>(null);
  const [deletingCv, setDeletingCv] = useState<ExtendedUserCV | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info'; action?: () => void } | null>(null);
  const [deletedItemBackup, setDeletedItemBackup] = useState<ExtendedUserCV | null>(null);
  const [isFetchingDetails, setIsFetchingDetails] = useState(false);
  const [isSkipping, setIsSkipping] = useState(false);

  // Fetch CVs from real API when modal opens
  useEffect(() => {
    if (isOpen) {
      fetchCvs();
      document.body.style.overflow = 'hidden';
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape' && !editingCv && !deletingCv) {
          onClose();
        }
      };
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen, editingCv, deletingCv]); // Added deps to refresh listeners correctly

  const fetchCvs = async () => {
    setLoading(true);
    try {
      const res = await api.get('/cv/user/me');
      
      // Handle potential response wrapping (e.g. { data: [...] } or just [...])
      const rawData = Array.isArray(res.data) ? res.data : (res.data?.data || []);

      const mappedCvs: ExtendedUserCV[] = Array.isArray(rawData) ? rawData.map((item: any) => ({
        id: item._id,
        name: item.fullname || "Hồ sơ không tên",
        title: item.headline || item.targetRole || "Chưa có tiêu đề",
        // Extract skill names if skills is an array of objects
        skills: Array.isArray(item.skills) 
          ? item.skills.map((s: any) => typeof s === 'string' ? s : s.name).filter(Boolean)
          : [],
        experienceLevel: "Mid-Level", // Placeholder or calculate from item.experiences
        location: item.location?.city || item.location?.state || (typeof item.location === 'string' ? item.location : ""),
        lastUpdated: item.updatedAt 
          ? new Date(item.updatedAt).toLocaleDateString('vi-VN') 
          : "Vừa xong",
        ownerId: item.userId || item.createdBy,
        originalData: item // Store full object for editing/restoring
      })) : [];

      setLocalCvs(mappedCvs);
    } catch (error) {
      console.error("Failed to fetch CVs", error);
      // Fallback to empty if API fails
      setLocalCvs([]);
    } finally {
      setLoading(false);
    }
  };

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
    navigate('/create-profile?type=cv');
  };

  const handleSkip = async () => {
    setIsSkipping(true);
    try {
      console.log("🚀 Skipping... Fetching CVs for manual search context");
      const res = await api.get('/cv');
      
      // Safety check: API might return { data: [...] } or just [...]
      const rawData = Array.isArray(res.data) ? res.data : (res.data?.data || []);
      console.log("📥 Received CVs for skip:", rawData);

      if (!Array.isArray(rawData)) {
        console.warn("Unexpected response format from /cv", res.data);
        // Don't throw, just map empty to proceed
      }
      
      // Map to UserCV structure for the Jobs page state
      const mappedCvs = Array.isArray(rawData) ? rawData.map((item: any) => ({
        id: item._id,
        name: item.fullname || "Hồ sơ không tên",
        title: item.headline || item.targetRole || "Chưa có tiêu đề",
        skills: Array.isArray(item.skills) 
          ? item.skills.map((s: any) => typeof s === 'string' ? s : s.name).filter(Boolean)
          : [],
        experienceLevel: "Mid-Level",
        location: item.location?.city || (typeof item.location === 'string' ? item.location : ""),
        lastUpdated: item.updatedAt 
          ? new Date(item.updatedAt).toLocaleDateString('vi-VN') 
          : "Vừa xong"
      })) : [];

      onClose();
      // Navigate with state containing the fetched CVs
      console.log("➡️ Navigating to /jobs with state:", { cvs: mappedCvs });
      navigate('/jobs?manual=true', { state: { cvs: mappedCvs } });
    } catch (error) {
      console.error("Fetch CVs for skip failed", error);
      setToast({ message: 'Không thể tải danh sách CV. Chuyển sang tìm kiếm thủ công.', type: 'error' });
      // Proceed to navigate anyway
      onClose();
      navigate('/jobs?manual=true');
    } finally {
      setIsSkipping(false);
    }
  };

  const handleRename = async (cv: UserCV, newName: string) => {
    const originalName = cv.name;
    // Optimistic Update
    setLocalCvs(prev => prev.map(c => c.id === cv.id ? { ...c, name: newName } : c));

    try {
      // Use specific rename endpoint as per requirements
      const response = await api.patch(`/cv/${cv.id}/rename`, { fullname: newName });
      
      // If server returns updated object, we can update local state with more accurate data (e.g. updatedAt)
      if (response.data) {
        setLocalCvs(prev => prev.map(c => {
          if (c.id === cv.id) {
             return {
               ...c,
               name: response.data.fullname || newName,
               // Update timestamp if available
               lastUpdated: response.data.updatedAt 
                 ? new Date(response.data.updatedAt).toLocaleDateString('vi-VN') 
                 : new Date().toLocaleDateString('vi-VN')
             };
          }
          return c;
        }));
      }

      setToast({ message: 'Đổi tên thành công', type: 'success' });
    } catch (error) {
      console.error("Rename failed", error);
      // Rollback on error
      setLocalCvs(prev => prev.map(c => c.id === cv.id ? { ...c, name: originalName } : c));
      setToast({ message: 'Đổi tên thất bại', type: 'error' });
    }
  };

  const handleEdit = async (cv: ExtendedUserCV) => {
    // 1. Open modal immediately
    setEditingCv(cv);
    // 2. Set loading details state
    setIsFetchingDetails(true);

    try {
      // 3. Fetch full details from API
      const response = await api.get(`/cv/${cv.id}`);
      const data = response.data;

      // 4. Map backend response to Form DTO
      const details = {
        ...data,
        id: data._id, // Ensure id maps to _id
        
        // Normalize skills: if array of strings, convert to objects
        skills: Array.isArray(data.skills) 
          ? data.skills.map((s: any) => {
              if (typeof s === 'string') return { name: s, level: 'Intermediate' };
              return { ...s, id: s._id || s.id }; // Preserve _id
            })
          : [],
        
        // Ensure location is an object
        location: typeof data.location === 'object' ? data.location : { city: data.location || '' },
      };

      // 5. Update editingCv with fetched details
      setEditingCv(prev => {
        if (prev && prev.id === cv.id) {
           return { ...prev, details };
        }
        return prev;
      });

    } catch (error) {
      console.error("Failed to fetch CV details", error);
      setToast({ message: 'Lỗi tải dữ liệu chi tiết', type: 'error' });
      // Close modal on error
      setEditingCv(null);
    } finally {
      setIsFetchingDetails(false);
    }
  };

  const handleSaveEdit = async (formData: any) => {
    if (!editingCv) return;
    setIsSaving(true);
    
    try {
      // Update via API
      await api.put(`/cv/${editingCv.id}`, formData);
      
      // Refresh list to get latest data from server
      await fetchCvs();
      
      setEditingCv(null);
      setToast({ message: 'Cập nhật hồ sơ thành công', type: 'success' });

    } catch (error) {
      console.error("Update failed", error);
      setToast({ message: 'Cập nhật thất bại', type: 'error' });
    } finally {
      setIsSaving(false);
    }
  };

  const executeDelete = async (itemToDelete: ExtendedUserCV) => {
    setDeletedItemBackup(itemToDelete);

    // Optimistic Remove
    setLocalCvs(prev => prev.filter(c => c.id !== itemToDelete.id));
    setToast({
      message: `Đã xóa "${itemToDelete.name}"`,
      type: 'info',
      action: () => handleUndoDelete(itemToDelete)
    });

    try {
      await api.delete(`/cv/${itemToDelete.id}`);
    } catch (error) {
      console.error("Delete failed", error);
      // Rollback
      setLocalCvs(prev => {
        if (prev.find(c => c.id === itemToDelete.id)) return prev;
        return [itemToDelete, ...prev];
      });
      setToast({ message: 'Xóa thất bại', type: 'error' });
    }
  };

  const handleDeleteClick = (cv: ExtendedUserCV) => {
    setDeletingCv(cv);
  };

  const handleConfirmDelete = async () => {
    if (!deletingCv) return;
    const itemToDelete = deletingCv;
    setDeletingCv(null);
    executeDelete(itemToDelete);
  };

  const handleUndoDelete = async (item: ExtendedUserCV) => {
    // Optimistic Restore
    setLocalCvs(prev => [item, ...prev]);
    setDeletedItemBackup(null);
    setToast(null); // Clear toast to prevent multiple undos

    try {
      // Sanitize payload: Remove ID and system fields to treat as new creation
      const payload = { ...item.originalData };
      delete payload._id;
      delete payload.id;
      delete payload.createdAt;
      delete payload.updatedAt;
      delete payload.__v;
      
      // Restore using POST to create a new record based on old data
      await api.post('/cv', payload);
      setToast({ message: 'Đã hoàn tác xóa', type: 'success' });
      
      // Refresh to get the new ID assigned by backend
      fetchCvs();
    } catch (error) {
      console.error("Undo failed", error);
      // Rollback: Remove item if restore failed
      setLocalCvs(prev => prev.filter(c => c.id !== item.id));
      setToast({ message: 'Hoàn tác thất bại', type: 'error' });
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
        <div className="flex items-center justify-between px-8 py-6 bg-white border-b border-gray-100 shrink-0">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Chọn hồ sơ ứng tuyển</h2>
            <p className="text-sm text-gray-500 mt-1">Quản lý các hồ sơ CV của bạn để tìm việc làm tốt nhất.</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Loading Overlay for List Fetch */}
        <div className="overflow-y-auto p-6 md:p-8 custom-scrollbar relative">
          
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
               <p className="text-gray-500">Đang tải danh sách hồ sơ...</p>
             </div>
          ) : localCvs.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {localCvs.map((cv) => (
                <CvCard
                  key={cv.id}
                  cv={cv}
                  onSelect={onSelectCv}
                  onEdit={() => handleEdit(cv)}
                  onDelete={() => handleDeleteClick(cv)}
                  onRename={handleRename}
                  // We bypass owner check for now as we fetched /user/me
                  currentUserId={cv.ownerId}
                />
              ))}

              <button 
                onClick={handleCreateNew}
                className="group flex flex-col items-center justify-center min-h-[200px] rounded-2xl border-2 border-dashed border-gray-200 bg-white hover:border-blue-400 hover:bg-blue-50/30 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Plus className="w-8 h-8 text-[#0A65CC]" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 group-hover:text-[#0A65CC] mb-1">Tạo hồ sơ mới</h3>
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                 <FileText className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Chưa có hồ sơ nào</h3>
              <button 
               onClick={handleCreateNew}
               className="bg-[#0A65CC] text-white px-8 py-3 rounded-full font-bold hover:bg-blue-700 transition"
              >
                Tạo hồ sơ mới
              </button>
            </div>
          )}
        </div>
        
        <div className="p-4 bg-white border-t border-gray-100 text-center shrink-0">
            <button 
                onClick={handleSkip}
                disabled={isSkipping}
                className="text-sm font-medium text-gray-500 hover:text-[#0A65CC] transition-colors disabled:opacity-50 flex items-center justify-center gap-2 w-full"
            >
                {isSkipping && <Loader2 className="w-4 h-4 animate-spin" />}
                {isSkipping ? 'Đang xử lý...' : 'Bỏ qua, tôi muốn tìm kiếm thủ công'}
            </button>
        </div>
      </div>

      {editingCv && (
        <EditCvModal 
          isOpen={!!editingCv}
          onClose={() => setEditingCv(null)}
          cv={editingCv}
          onSave={handleSaveEdit}
          onDelete={executeDelete} // Pass direct delete handler
          isSaving={isSaving}
          isLoading={isFetchingDetails}
        />
      )}

      {deletingCv && (
        <ConfirmDialog 
          isOpen={!!deletingCv}
          title="Xóa hồ sơ?"
          message={`Bạn có chắc chắn muốn xóa "${deletingCv.name}"? Hành động này không thể hoàn tác.`}
          confirmLabel="Xóa"
          cancelLabel="Hủy"
          onConfirm={handleConfirmDelete}
          onCancel={() => setDeletingCv(null)}
          isDestructive={true}
        />
      )}
    </div>
  );
};

export default CvSelectorModal;
