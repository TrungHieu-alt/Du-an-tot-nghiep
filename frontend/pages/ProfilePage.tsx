
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';
import { User } from '../types';
import ProfileHeader from '../components/profile/ProfileHeader';
import ProfileInfoForm from '../components/profile/ProfileInfoForm';
import { Loader2 } from 'lucide-react';

const ProfilePage: React.FC = () => {
  const { isAuthenticated, user: authUser, login } = useAuth();
  const navigate = useNavigate();
  
  const [userProfile, setUserProfile] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch full profile data
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    const fetchProfile = async () => {
      try {
        const res = await api.get('/auth/profile');
        setUserProfile(res.data);
      } catch (error) {
        console.error("Failed to fetch profile", error);
        // Fallback to AuthContext user if API fails (rare case)
        if (authUser) setUserProfile(authUser);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [isAuthenticated, navigate, authUser]);

  // Handle updates from child components to keep state in sync
  const handleUserUpdate = (updatedUser: User) => {
    setUserProfile(updatedUser);
    // Also update global auth context if needed
    const token = sessionStorage.getItem('accessToken') || localStorage.getItem('accessToken');
    if (token) {
       login(token, updatedUser);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-10 h-10 text-[#0A65CC] animate-spin" />
      </div>
    );
  }

  if (!userProfile) return null;

  return (
    <div className="min-h-screen bg-[#F5F7FC] py-10 font-sans profile-page">
      {/* Scoped Styles to force input visibility and override any global defaults */}
      <style>{`
        .profile-page input,
        .profile-page select,
        .profile-page textarea {
          background-color: #ffffff !important;
          color: #1e293b !important; /* slate-800 */
          border-color: #e2e8f0;
        }
        .profile-page input:focus,
        .profile-page select:focus,
        .profile-page textarea:focus {
          background-color: #ffffff !important;
          color: #1e293b !important;
        }
        .profile-page input::placeholder,
        .profile-page textarea::placeholder {
          color: #94a3b8 !important; /* slate-400 */
        }
        .profile-page input:disabled {
          background-color: #f9fafb !important; /* gray-50 */
          color: #6b7280 !important; /* gray-500 */
          cursor: not-allowed;
        }
      `}</style>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Header Section */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Hồ sơ cá nhân</h1>
          <p className="text-gray-500 mt-1">Quản lý thông tin tài khoản và cập nhật hồ sơ của bạn.</p>
        </div>

        {/* Profile Summary & Avatar */}
        <ProfileHeader user={userProfile} onUserUpdate={handleUserUpdate} />

        {/* Content - Single Column, Personal Info Only */}
        <div className="max-w-3xl mx-auto">
            <ProfileInfoForm user={userProfile} onUserUpdate={handleUserUpdate} />
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
