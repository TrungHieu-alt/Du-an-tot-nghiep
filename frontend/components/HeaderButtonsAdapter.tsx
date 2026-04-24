
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useModal } from '../contexts/ModalContext';
import { useAuth } from '../contexts/AuthContext';

/**
 * Adapter component for the "Tìm việc" link in the header.
 * Checks auth state: opens Modal if logged in, otherwise navigates to manual search.
 */
export const HeaderFindJobsBtn: React.FC = () => {
  const { openCvModal } = useModal();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleClick = () => {
    if (isAuthenticated) {
      openCvModal();
    } else {
      navigate('/jobs?manual=true');
    }
  };

  return (
    <button
      onClick={handleClick}
      className="text-gray-600 hover:text-[#0A65CC] font-medium transition-colors text-sm bg-transparent border-none p-0 cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/20 rounded-sm"
    >
      Tìm việc
    </button>
  );
};

/**
 * Adapter component for the "Tìm ứng viên" link in the header.
 * Checks auth state: opens Modal if logged in, otherwise navigates to manual search.
 */
export const HeaderFindCandidatesBtn: React.FC = () => {
  const { openReqModal } = useModal();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleClick = () => {
    if (isAuthenticated) {
      openReqModal();
    } else {
      navigate('/candidates?manual=true');
    }
  };

  return (
    <button
      onClick={handleClick}
      className="text-gray-600 hover:text-[#0A65CC] font-medium transition-colors text-sm bg-transparent border-none p-0 cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/20 rounded-sm"
    >
      Tìm ứng viên
    </button>
  );
};
