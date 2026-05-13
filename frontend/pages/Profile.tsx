import React from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, FileText, Mail, Shield, UserCircle } from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';

const roleLabel: Record<string, string> = {
  user: 'Người dùng',
  candidate: 'Ứng viên',
  employer: 'Nhà tuyển dụng',
  admin: 'Quản trị viên',
};

const Profile: React.FC = () => {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-gray-900">Cần đăng nhập</h1>
        <p className="mt-2 text-sm text-gray-500">
          Đăng nhập để xem thông tin tài khoản JobConnect của bạn.
        </p>
        <Link
          to="/login"
          className="mt-5 inline-flex rounded-full bg-[#0F6FD6] px-5 py-2 text-sm font-semibold text-white"
        >
          Đăng nhập
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-50 text-[#0F6FD6]">
            <UserCircle className="h-10 w-10" />
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-2xl font-bold text-gray-900">
              {user.full_name || 'Người dùng JobConnect'}
            </h1>
            <p className="mt-1 flex items-center gap-2 text-sm text-gray-500">
              <Mail className="h-4 w-4" />
              {user.email}
            </p>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
              <Shield className="h-4 w-4 text-[#00A86B]" />
              Vai trò
            </div>
            <p className="text-sm text-gray-600">{roleLabel[user.role] || user.role}</p>
          </div>
          <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
              <UserCircle className="h-4 w-4 text-[#0F6FD6]" />
              Mã người dùng
            </div>
            <p className="break-all text-sm text-gray-600">{user.id}</p>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <Link
          to="/cvs"
          className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition-colors hover:border-[#0F6FD6] hover:bg-blue-50"
        >
          <FileText className="mb-3 h-6 w-6 text-[#0F6FD6]" />
          <h2 className="font-bold text-gray-900">Quản lý CV</h2>
          <p className="mt-1 text-sm text-gray-500">Tạo CV thủ công hoặc upload CV PDF.</p>
        </Link>
        <Link
          to="/employer/requests"
          className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition-colors hover:border-[#00A86B] hover:bg-green-50"
        >
          <Briefcase className="mb-3 h-6 w-6 text-[#00A86B]" />
          <h2 className="font-bold text-gray-900">Quản lý yêu cầu tuyển dụng</h2>
          <p className="mt-1 text-sm text-gray-500">
            Tạo và quản lý các job/recruitment request của tài khoản này.
          </p>
        </Link>
      </div>
    </div>
  );
};

export default Profile;
