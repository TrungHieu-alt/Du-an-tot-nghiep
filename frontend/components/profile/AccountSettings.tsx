
import React, { useState } from 'react';
import { Loader2, AlertCircle, CheckCircle2, Lock, Trash2 } from 'lucide-react';
import api from '../../lib/api';
import ConfirmDialog from '../common/ConfirmDialog';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const AccountSettings: React.FC = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  
  const [passData, setPassData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPassData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passData.newPassword !== passData.confirmPassword) {
      setMessage({ type: 'error', text: 'Mật khẩu xác nhận không khớp.' });
      return;
    }
    
    setLoading(true);
    setMessage(null);

    try {
      await api.patch('/auth/change-password', {
        oldPassword: passData.oldPassword,
        newPassword: passData.newPassword
      });
      setMessage({ type: 'success', text: 'Đổi mật khẩu thành công!' });
      setPassData({ oldPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || 'Có lỗi xảy ra.';
      setMessage({ type: 'error', text: Array.isArray(errorMsg) ? errorMsg.join(', ') : errorMsg });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    setIsDeleting(true);
    setShowDeleteConfirm(false);
    
    try {
      await api.delete('/users/me');
      logout();
      navigate('/login');
    } catch (err: any) {
      alert(err.response?.data?.message || 'Không thể xóa tài khoản.');
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Change Password Card */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-lg font-bold text-gray-900 mb-4 pb-2 border-b border-gray-50">Đổi mật khẩu</h2>
        
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu hiện tại</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input 
                type="password" 
                name="oldPassword" 
                value={passData.oldPassword} 
                onChange={handleChange}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-[#0A65CC] outline-none transition-all text-slate-800"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu mới</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input 
                type="password" 
                name="newPassword" 
                value={passData.newPassword} 
                onChange={handleChange}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-[#0A65CC] outline-none transition-all text-slate-800"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Xác nhận mật khẩu</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input 
                type="password" 
                name="confirmPassword" 
                value={passData.confirmPassword} 
                onChange={handleChange}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-[#0A65CC] outline-none transition-all text-slate-800"
                required
              />
            </div>
          </div>

          {message && (
            <div className={`p-3 rounded-lg flex items-center gap-2 text-sm ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {message.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
              {message.text}
            </div>
          )}

          <div className="pt-2">
            <button 
              type="submit" 
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-[#0A65CC] text-white py-2.5 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-70"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Cập nhật mật khẩu
            </button>
          </div>
        </form>
      </div>

      {/* Delete Account Card */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 border-l-4 border-l-red-500">
        <h2 className="text-lg font-bold text-gray-900 mb-2 text-red-600 flex items-center gap-2">
          <Trash2 className="w-5 h-5" /> Xóa tài khoản
        </h2>
        <p className="text-gray-600 text-sm mb-4">
          Hành động này không thể hoàn tác. Tất cả dữ liệu của bạn sẽ bị xóa vĩnh viễn khỏi hệ thống.
        </p>
        <button 
          onClick={() => setShowDeleteConfirm(true)}
          disabled={isDeleting}
          className="px-6 py-2.5 bg-red-50 text-red-600 font-semibold rounded-lg hover:bg-red-100 transition-colors disabled:opacity-70"
        >
          {isDeleting ? 'Đang xóa...' : 'Xóa tài khoản'}
        </button>
      </div>

      <ConfirmDialog 
        isOpen={showDeleteConfirm}
        title="Xóa tài khoản?"
        message="Bạn có chắc chắn muốn xóa tài khoản? Mọi dữ liệu sẽ bị mất và không thể khôi phục."
        confirmLabel="Xóa vĩnh viễn"
        cancelLabel="Hủy"
        onConfirm={handleDeleteAccount}
        onCancel={() => setShowDeleteConfirm(false)}
        isDestructive={true}
      />
    </div>
  );
};

export default AccountSettings;
