import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BriefcaseBusiness, LogOut, UserCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const navItems = [
  { label: 'Trang chủ', to: '/', match: 'home' },
  { label: 'Tìm việc', to: '/v2/search', match: 'job-search' },
  { label: 'Matching V2', to: '/v2/matching', match: 'matching' },
  { label: 'Tìm ứng viên', to: '/v2/search?type=cv', match: 'cv-search' },
  { label: 'Công ty', to: '/#companies', match: 'companies' },
  { label: 'Blog', to: '/#blog', match: 'blog' },
];

const Header: React.FC = () => {
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();
  const searchParams = new URLSearchParams(location.search);
  const searchType = searchParams.get('type');

  const isNavActive = (match: string): boolean => {
    if (match === 'home') return location.pathname === '/';
    if (match === 'job-search') {
      return location.pathname === '/v2/search' && searchType !== 'cv';
    }
    if (match === 'cv-search') {
      return location.pathname === '/v2/search' && searchType === 'cv';
    }
    if (match === 'matching') return location.pathname === '/v2/matching';
    if (match === 'companies') return location.pathname === '/' && location.hash === '#companies';
    if (match === 'blog') return location.pathname === '/' && location.hash === '#blog';
    return false;
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
            <>
              <div className="hidden max-w-[220px] items-center gap-2 rounded-full border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-semibold text-gray-700 sm:flex">
                <UserCircle className="h-4 w-4 text-[#0F6FD6]" />
                <span className="truncate">{user.full_name || user.email}</span>
              </div>
              <button
                type="button"
                onClick={logout}
                className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm transition-colors hover:border-[#0F6FD6] hover:text-[#0F6FD6]"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Đăng xuất</span>
              </button>
            </>
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
