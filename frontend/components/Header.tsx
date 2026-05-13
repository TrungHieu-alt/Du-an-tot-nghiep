import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Briefcase,
  BriefcaseBusiness,
  ChevronDown,
  FileText,
  LogOut,
  UserCircle,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const navItems = [
  { label: 'Trang chủ', to: '/', match: 'home' },
  { label: 'Tìm việc', to: '/jobs/search', match: 'job-search' },
  { label: 'Matching V2', to: '/v2/matching', match: 'matching' },
  { label: 'Tìm ứng viên', to: '/cvs/search?type=cv', match: 'cv-search' },
  { label: 'Công ty', to: '/#companies', match: 'companies' },
  { label: 'Blog', to: '/#blog', match: 'blog' },
];

const Header: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement | null>(null);
  const searchParams = new URLSearchParams(location.search);
  const searchType = searchParams.get('type');

  useEffect(() => {
    setProfileOpen(false);
  }, [location.pathname, location.search]);

  useEffect(() => {
    if (!profileOpen) return;

    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      if (!profileRef.current?.contains(event.target as Node)) {
        setProfileOpen(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('touchstart', handlePointerDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('touchstart', handlePointerDown);
    };
  }, [profileOpen]);

  const isNavActive = (match: string): boolean => {
    if (match === 'home') return location.pathname === '/';
    if (match === 'job-search') {
      return (location.pathname === '/jobs/search' || location.pathname === '/v2/search') && searchType !== 'cv';
    }
    if (match === 'cv-search') {
      return location.pathname === '/cvs/search' || (location.pathname === '/v2/search' && searchType === 'cv');
    }
    if (match === 'matching') return location.pathname === '/v2/matching';
    if (match === 'companies') return location.pathname === '/' && location.hash === '#companies';
    if (match === 'blog') return location.pathname === '/' && location.hash === '#blog';
    return false;
  };

  const handleLogout = () => {
    logout();
    setProfileOpen(false);
    navigate('/jobs/search');
  };

  return (
    <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/95 shadow-sm backdrop-blur-sm">
      <div className="mx-auto flex h-[60px] max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3">
          <div className="rounded-xl bg-gradient-to-br from-[#0F6FD6] to-[#00A86B] p-2 shadow-sm">
            <BriefcaseBusiness className="h-6 w-6 text-white" strokeWidth={2.4} />
          </div>
          <span className="hidden text-xl font-bold sm:inline">
            <span className="text-[#0F6FD6]">Job</span>
            <span className="text-[#00A86B]">Connect</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-4 lg:flex">
          {navItems.map((item) => {
            const isActive = isNavActive(item.match);
            return (
              <Link
                key={item.label}
                to={item.to}
                className={`rounded-full px-2.5 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-[#0F6FD6]'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-[#0F6FD6]'
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          {isAuthenticated && user ? (
            <div ref={profileRef} className="relative">
              <button
                type="button"
                aria-haspopup="menu"
                aria-expanded={profileOpen}
                aria-label={`Tài khoản ${user.full_name || user.email}`}
                onClick={() => setProfileOpen((open) => !open)}
                className="inline-flex max-w-[220px] items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-700 shadow-sm transition-colors hover:border-[#0F6FD6] hover:text-[#0F6FD6]"
              >
                <UserCircle className="h-5 w-5 flex-shrink-0 text-[#0F6FD6]" />
                <span className="hidden truncate sm:inline">{user.full_name || user.email}</span>
                <ChevronDown
                  className={`h-4 w-4 flex-shrink-0 transition-transform ${profileOpen ? 'rotate-180' : ''}`}
                />
              </button>

              {profileOpen ? (
                <div
                  role="menu"
                  className="absolute right-0 mt-2 w-72 overflow-hidden rounded-xl border border-gray-100 bg-white py-2 shadow-xl shadow-gray-900/10"
                >
                  <div className="border-b border-gray-100 px-4 py-3">
                    <p className="truncate text-sm font-semibold text-gray-900">
                      {user.full_name || 'Người dùng JobConnect'}
                    </p>
                    <p className="truncate text-xs text-gray-500">{user.email}</p>
                  </div>
                  <Link
                    role="menuitem"
                    to="/profile"
                    className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-700 transition-colors hover:bg-blue-50 hover:text-[#0F6FD6]"
                    onClick={() => setProfileOpen(false)}
                  >
                    <UserCircle className="h-4 w-4" />
                    Thông tin cá nhân
                  </Link>
                  <Link
                    role="menuitem"
                    to="/cvs"
                    className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-700 transition-colors hover:bg-blue-50 hover:text-[#0F6FD6]"
                    onClick={() => setProfileOpen(false)}
                  >
                    <FileText className="h-4 w-4" />
                    Quản lý CV
                  </Link>
                  <Link
                    role="menuitem"
                    to="/employer/requests"
                    className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-700 transition-colors hover:bg-blue-50 hover:text-[#0F6FD6]"
                    onClick={() => setProfileOpen(false)}
                  >
                    <Briefcase className="h-4 w-4" />
                    Quản lý yêu cầu tuyển dụng
                  </Link>
                  <button
                    type="button"
                    role="menuitem"
                    onClick={handleLogout}
                    className="flex w-full items-center gap-3 border-t border-gray-100 px-4 py-3 text-left text-sm font-semibold text-gray-700 transition-colors hover:bg-red-50 hover:text-red-600"
                  >
                    <LogOut className="h-4 w-4" />
                    Đăng xuất
                  </button>
                </div>
              ) : null}
            </div>
          ) : (
            <>
              <Link
                to="/login"
                className="rounded-full border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-700 shadow-sm transition-colors hover:border-[#0F6FD6] hover:text-[#0F6FD6] sm:px-5"
              >
                Đăng nhập
              </Link>
              <Link
                to="/register"
                className="rounded-full bg-gradient-to-r from-[#0F6FD6] to-[#00A86B] px-3 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-500/20 transition-transform hover:-translate-y-0.5 sm:px-5"
              >
                Đăng ký
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
