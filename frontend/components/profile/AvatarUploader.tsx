
import React, { useRef, useState } from 'react';
import { Camera, Loader2, User as UserIcon } from 'lucide-react';
import api from '../../lib/api';

interface AvatarUploaderProps {
  currentAvatar?: string;
  userName: string;
  onUploadSuccess: (newUrl: string) => void;
}

const AvatarUploader: React.FC<AvatarUploaderProps> = ({ currentAvatar, userName, onUploadSuccess }) => {
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Vui lòng chọn file hình ảnh');
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('avatar', file);

    try {
      const res = await api.post('/users/me/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      // Assuming backend returns { avatar: "url" }
      onUploadSuccess(res.data.avatar);
    } catch (error) {
      console.error("Upload failed", error);
      alert('Tải ảnh lên thất bại. Vui lòng thử lại.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="relative group">
      <div className="w-24 h-24 rounded-full overflow-hidden border-4 border-white shadow-md bg-gray-100">
        {currentAvatar ? (
          <img src={currentAvatar} alt={userName} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-blue-50 text-[#0A65CC]">
            <UserIcon className="w-10 h-10" />
          </div>
        )}
      </div>
      
      <button 
        onClick={() => fileInputRef.current?.click()}
        disabled={isUploading}
        className="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer disabled:cursor-not-allowed"
      >
        {isUploading ? (
          <Loader2 className="w-6 h-6 text-white animate-spin" />
        ) : (
          <Camera className="w-6 h-6 text-white" />
        )}
      </button>
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        className="hidden" 
        accept="image/*" 
      />
    </div>
  );
};

export default AvatarUploader;
