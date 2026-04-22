
import React, { useState, useEffect } from 'react';
import { User } from '../../types';
import { Loader2, AlertCircle, CheckCircle2, Plus, X } from 'lucide-react';
import api from '../../lib/api';

interface CareerInfoFormProps {
  user: User;
  onUserUpdate: (updatedUser: User) => void;
}

const CareerInfoForm: React.FC<CareerInfoFormProps> = ({ user, onUserUpdate }) => {
  const [formData, setFormData] = useState({
    currentPosition: user.currentPosition || '',
    experienceLevel: user.experienceLevel || 'Fresher',
    preferredLocation: user.preferredLocation || 'Hà Nội',
    salaryRange: user.salaryRange || '',
    skills: user.skills || []
  });
  
  const [skillInput, setSkillInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    setFormData({
      currentPosition: user.currentPosition || '',
      experienceLevel: user.experienceLevel || 'Fresher',
      preferredLocation: user.preferredLocation || 'Hà Nội',
      salaryRange: user.salaryRange || '',
      skills: user.skills || []
    });
  }, [user]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleAddSkill = () => {
    if (skillInput.trim() && !formData.skills.includes(skillInput.trim())) {
      setFormData(prev => ({ ...prev, skills: [...prev.skills, skillInput.trim()] }));
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setFormData(prev => ({ ...prev, skills: prev.skills.filter(s => s !== skillToRemove) }));
  };

  const handleSkillKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddSkill();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const res = await api.put('/users/me/career', formData);
      onUserUpdate({ ...user, ...res.data });
      setMessage({ type: 'success', text: 'Cập nhật thông tin nghề nghiệp thành công!' });
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || 'Có lỗi xảy ra.';
      setMessage({ type: 'error', text: Array.isArray(errorMsg) ? errorMsg.join(', ') : errorMsg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 h-full">
      <h2 className="text-lg font-bold text-gray-900 mb-4 pb-2 border-b border-gray-50">
        Thông tin nghề nghiệp
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Vị trí hiện tại</label>
          <input 
            type="text" 
            name="currentPosition" 
            value={formData.currentPosition} 
            onChange={handleChange}
            placeholder="VD: Senior React Developer"
            className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-[#0A65CC] outline-none transition-all text-slate-800"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cấp bậc</label>
            <select 
              name="experienceLevel" 
              value={formData.experienceLevel} 
              onChange={handleChange}
              className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-[#0A65CC] outline-none transition-all text-slate-800 bg-white"
            >
              <option value="Intern">Intern</option>
              <option value="Fresher">Fresher</option>
              <option value="Junior">Junior</option>
              <option value="Mid-Level">Mid-Level</option>
              <option value="Senior">Senior</option>
              <option value="Manager">Manager</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nơi làm việc</label>
            <select 
              name="preferredLocation" 
              value={formData.preferredLocation} 
              onChange={handleChange}
              className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-[#0A65CC] outline-none transition-all text-slate-800 bg-white"
            >
              <option value="Hà Nội">Hà Nội</option>
              <option value="Hồ Chí Minh">TP. Hồ Chí Minh</option>
              <option value="Đà Nẵng">Đà Nẵng</option>
              <option value="Remote">Remote</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Mức lương mong muốn</label>
          <input 
            type="text" 
            name="salaryRange" 
            value={formData.salaryRange} 
            onChange={handleChange}
            placeholder="VD: 15 - 25 triệu"
            className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-[#0A65CC] outline-none transition-all text-slate-800"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Kỹ năng</label>
          <div className="flex gap-2 mb-2">
            <input 
              type="text" 
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={handleSkillKeyDown}
              placeholder="Nhập kỹ năng & nhấn Enter"
              className="flex-1 px-4 py-2.5 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-[#0A65CC] outline-none transition-all text-slate-800"
            />
            <button 
              type="button" 
              onClick={handleAddSkill}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 p-2.5 rounded-lg transition-colors"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.skills.map((skill, index) => (
              <span key={index} className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 px-2.5 py-1 rounded text-sm border border-blue-100">
                {skill}
                <button type="button" onClick={() => handleRemoveSkill(skill)} className="hover:text-blue-900">
                  <X className="w-3.5 h-3.5" />
                </button>
              </span>
            ))}
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
            Lưu thay đổi
          </button>
        </div>
      </form>
    </div>
  );
};

export default CareerInfoForm;
