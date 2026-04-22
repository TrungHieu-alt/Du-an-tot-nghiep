
import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Briefcase, LogOut, User as UserIcon, ChevronDown, Settings, FileText } from 'lucide-react';
import { HeaderFindJobsBtn, HeaderFindCandidatesBtn } from './HeaderButtonsAdapter';
import { useAuth } from '../contexts/AuthContext';

const Header: React.FC = () => {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
  
  const { isAuthenticated, user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    setShowUserMenu(false);
    navigate('/');
  };

  if (isAuthPage) return null;

  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-sm border-b border-gray-100 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="bg-gradient-to-br from-[#0A65CC] to-[#00B14F] p-2.5 rounded-xl shadow-sm transition-transform duration-300 group-hover:scale-105">
              <Briefcase className="w-7 h-7 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-2xl font-bold tracking-tight">
              <span className="text-[#0A65CC]">Job</span><span className="text-[#00B14F]">Connect</span>
            </span>
          </Link>

          {/* Navigation with Action Buttons */}
          <nav className="hidden lg:flex items-center gap-3">
            <div className="flex items-center gap-6">
              {/* Replaced static Links with Adapter Buttons for Modal Flow */}
              <HeaderFindJobsBtn />
              <HeaderFindCandidatesBtn />
              
              <Link to="/" className="text-gray-600 hover:text-[#0A65CC] font-medium transition-colors text-sm">Công ty</Link>
              <Link to="/" className="text-gray-600 hover:text-[#0A65CC] font-medium transition-colors text-sm">Blog</Link>
            </div>
          </nav>

          {/* Auth Buttons / User Menu */}
          <div className="flex items-center gap-4">
            {isAuthenticated && user ? (
              <div className="relative" ref={userMenuRef}>
                <button 
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-3 hover:bg-gray-50 p-2 rounded-xl transition-colors outline-none focus:ring-2 focus:ring-[#0A65CC]/20"
                >
                  <img 
                    src={user.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=0A65CC&color=fff`} 
                    alt={user.name} 
                    className="w-10 h-10 rounded-full object-cover border border-gray-200"
                  />
                  <div className="text-left hidden md:block">
                    <p className="text-sm font-bold text-gray-900">{user.name}</p>
                    <p className="text-xs text-gray-500 truncate max-w-[120px]">{user.email}</p>
                  </div>
                  <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 top-full mt-2 w-64 bg-white rounded-xl shadow-xl border border-gray-100 py-2 animate-in fade-in zoom-in-95 duration-200 overflow-hidden">
                     {/* Mobile Only Info */}
                     <div className="px-4 py-3 border-b border-gray-100 mb-2 md:hidden">
                        <p className="font-semibold text-gray-900">{user.name}</p>
                        <p className="text-xs text-gray-500">{user.email}</p>
                     </div>

                     <Link to="/profile" className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-blue-50 hover:text-[#0A65CC] transition-colors" onClick={() => setShowUserMenu(false)}>
                        <UserIcon className="w-4 h-4" /> Hồ sơ cá nhân
                     </Link>
                     <Link to="/my-jobs" className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-blue-50 hover:text-[#0A65CC] transition-colors" onClick={() => setShowUserMenu(false)}>
                        <Briefcase className="w-4 h-4" /> Việc làm đã lưu
                     </Link>
                     <Link to="/settings" className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-blue-50 hover:text-[#0A65CC] transition-colors" onClick={() => setShowUserMenu(false)}>
                        <Settings className="w-4 h-4" /> Cài đặt tài khoản
                     </Link>
                     
                     <div className="h-px bg-gray-100 my-2"></div>
                     
                     <button 
                        onClick={handleLogout}
                        className="w-full text-left flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                     >
                        <LogOut className="w-4 h-4" /> Đăng xuất
                     </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <Link 
                  to="/login"
                  className="px-6 py-2.5 rounded-full font-semibold text-gray-600 bg-gray-50 border border-gray-200 hover:bg-white hover:text-[#0A65CC] hover:border-blue-200 hover:shadow-md transition-all duration-300 transform hover:-translate-y-0.5 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/20 focus:ring-offset-2 text-sm hidden sm:block"
                >
                  Đăng nhập
                </Link>
                <Link 
                  to="/register" 
                  className="px-6 py-2.5 rounded-full font-bold text-white bg-gradient-to-r from-[#0A65CC] to-[#00B14F] shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-600/40 transition-all duration-300 transform hover:-translate-y-0.5 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-[#00B14F]/50 focus:ring-offset-2 text-sm"
                >
                  Đăng ký
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
