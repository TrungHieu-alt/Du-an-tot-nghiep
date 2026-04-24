
import React from 'react';
import { User } from '../../types';
import AvatarUploader from './AvatarUploader';

interface ProfileHeaderProps {
  user: User;
  onUserUpdate: (updatedUser: User) => void;
}

const ProfileHeader: React.FC<ProfileHeaderProps> = ({ user, onUserUpdate }) => {
  const handleAvatarUpdate = (newAvatarUrl: string) => {
    onUserUpdate({ ...user, avatar: newAvatarUrl });
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex flex-col md:flex-row items-center gap-6">
      <AvatarUploader 
        currentAvatar={user.avatar} 
        userName={user.name} 
        onUploadSuccess={handleAvatarUpdate} 
      />

      <div className="flex-1 text-center md:text-left">
        <h1 className="text-2xl font-bold text-gray-900">{user.name}</h1>
        <p className="text-gray-500">{user.email}</p>
        <div className="flex items-center justify-center md:justify-start gap-2 mt-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 capitalize">
            {user.role || 'Member'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ProfileHeader;
