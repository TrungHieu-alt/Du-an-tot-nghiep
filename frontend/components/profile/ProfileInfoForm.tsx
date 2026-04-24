
import React, { useState, useEffect } from 'react';
import { User } from '../../types';
import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import api from '../../lib/api';

interface ProfileInfoFormProps {
  user: User;
  onUserUpdate: (updatedUser: User) => void;
}

const ProfileInfoForm: React.FC<ProfileInfoFormProps> = ({ user, onUserUpdate }) => {
  const [formData, setFormData] = useState({
    name: user.name || '',
    phone: user.phone || '',
    gender: user.gender || 'Other',
    birthday: user.birthday ? user.birthday.split('T')[0] : ''
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    setFormData({
      name: user.name || '',
      phone: user.phone || '',
      gender: user.gender || 'Other',
      birthday: user.birthday ? user.birthday.split('T')[0] : ''
    });
  }, [user]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      // API expects 'fullName' but state uses 'name' (derived from user.name)
      const payload = {
        fullName: formData.name,
        phone: formData.phone,
        gender: formData.gender,
        birthday: formData.birthday
      };

      const res = await api.put('/users/me', payload);
      onUserUpdate(res.data);
      setMessage({ type: 'success', text: 'Cập nhật thông tin thành công!' });
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || 'Có lỗi xảy ra.';
      setMessage({ type: 'error', text: Array.isArray(errorMsg) ? errorMsg.join(', ') : errorMsg });
    } finally {
      setLoading(false);
    }
  };

  // Explicit styling for inputs to ensure visibility and override defaults
  const inputClass = "w-full px-4 py-2.5 rounded-lg border border-gray-200 bg-white text-slate-800 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/20 focus:border-[#0A65CC] outline-none transition-all";

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 h-full">
      <h2 className="text-lg font-bold text-gray-900 mb-4 pb-2 border-b border-gray-50">
        Thông tin cá nhân
      </h2>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="name">Họ và tên</label>
          <input 
            id="name"
            type="text" 
            name="name" 
            value={formData.name} 
            onChange={handleChange}
            className={inputClass}
            placeholder="Nhập họ và tên"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input 
            type="email" 
            value={user.email} 
            disabled 
            className="w-full px-4 py-2.5 rounded-lg border border-gray-100 bg-gray-50 text-gray-500 cursor-not-allowed"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="phone">Số điện thoại</label>
          <input 
            id="phone"
            type="tel" 
            name="phone" 
            value={formData.phone} 
            onChange={handleChange}
            className={inputClass}
            placeholder="Ví dụ: 0912345678"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="gender">Giới tính</label>
            <select 
              id="gender"
              name="gender" 
              value={formData.gender} 
              onChange={handleChange}
              className={inputClass}
            >
              <option value="Male">Nam</option>
              <option value="Female">Nữ</option>
              <option value="Other">Khác</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="birthday">Ngày sinh</label>
            <input 
              id="birthday"
              type="date" 
              name="birthday" 
              value={formData.birthday} 
              onChange={handleChange}
              className={inputClass}
            />
          </div>
        </div>

        {message && (
          <div className={`p-3 rounded-lg flex items-center gap-2 text-sm ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {message.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            {message.text}
          </div>
        )}

        <div className="pt-4">
          <button 
            type="submit" 
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-[#0A65CC] text-white py-3 rounded-lg font-bold hover:bg-blue-700 transition-colors disabled:opacity-70 shadow-sm hover:shadow-md"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            Lưu thay đổi
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProfileInfoForm;
