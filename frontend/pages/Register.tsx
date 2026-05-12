import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  BriefcaseBusiness,
  CheckCircle2,
  Eye,
  EyeOff,
  Lock,
  Mail,
  User,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { normalizeApiError } from '../lib/api-error';
import type { UserRole } from '../src/services/authApi';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Extract<UserRole, 'candidate' | 'employer'>>('candidate');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await register({
        email,
        password,
        role,
        full_name: fullName.trim() || undefined,
      });
      navigate('/login', { replace: true, state: { registered: true } });
    } catch (err) {
      setError(normalizeApiError(err).displayMessage);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F6F8] px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto grid min-h-[540px] max-w-5xl overflow-hidden rounded-3xl bg-white shadow-2xl shadow-gray-300/60 lg:grid-cols-[0.9fr_1.25fr]">
        <aside className="relative hidden overflow-hidden bg-gradient-to-br from-[#0F6FD6] via-[#068E9F] to-[#00A86B] p-7 text-white lg:block">
          <div className="absolute right-[-70px] top-[-70px] h-56 w-56 rounded-full bg-white/10" />
          <div className="absolute bottom-[-70px] left-[-60px] h-48 w-48 rounded-full bg-white/10" />
          <div className="relative flex h-full flex-col">
            <Link to="/" className="flex items-center gap-3 text-lg font-bold">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-white/15">
                <BriefcaseBusiness className="h-5 w-5" />
              </span>
              JobConnect
            </Link>

            <div className="mt-10 max-w-xs">
              <h2 className="text-3xl font-bold leading-tight">Bắt đầu hành trình mới</h2>
              <p className="mt-5 text-sm leading-7 text-white/90">
                Tạo tài khoản miễn phí và khám phá hàng nghìn cơ hội việc làm phù hợp với bạn ngay hôm nay.
              </p>
            </div>

            <div className="mt-14 space-y-4">
              {[
                'Hoàn toàn miễn phí',
                'Kết nối với nhà tuyển dụng hàng đầu',
                'Nhận thông báo việc làm phù hợp',
              ].map((item) => (
                <div key={item} className="flex items-center gap-3 text-sm font-medium">
                  <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-white/20">
                    <CheckCircle2 className="h-4 w-4" />
                  </span>
                  {item}
                </div>
              ))}
            </div>

            <p className="mt-auto text-xs text-white/60">© 2024 JobConnect Inc.</p>
          </div>
        </aside>

        <section className="flex items-center justify-center px-6 py-10 sm:px-10">
          <div className="w-full max-w-[392px]">
            <div className="mb-7">
              <Link to="/" className="text-xs font-semibold uppercase text-gray-500 hover:text-[#0F6FD6]">
                ← Quay lại
              </Link>
              <h1 className="mt-6 text-2xl font-bold text-gray-900">Đăng ký tài khoản</h1>
              <p className="mt-2 text-sm text-gray-500">Điền thông tin của bạn để bắt đầu</p>
            </div>

            {error && (
              <div className="mb-5 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <label className="block">
                <span className="mb-2 block text-sm font-bold text-gray-700">Họ tên (tùy chọn)</span>
                <span className="relative block">
                  <User className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                  <input
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    placeholder="Nguyễn Văn A"
                    className="h-11 w-full rounded-lg border border-gray-200 bg-gray-50 pl-11 pr-4 text-sm outline-none transition-colors placeholder:text-gray-400 focus:border-[#0F6FD6] focus:bg-white focus:ring-2 focus:ring-[#0F6FD6]/10"
                  />
                </span>
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-bold text-gray-700">Email <span className="text-red-500">*</span></span>
                <span className="relative block">
                  <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="name@example.com"
                    className="h-11 w-full rounded-lg border border-gray-200 bg-gray-50 pl-11 pr-4 text-sm outline-none transition-colors placeholder:text-gray-400 focus:border-[#0F6FD6] focus:bg-white focus:ring-2 focus:ring-[#0F6FD6]/10"
                  />
                </span>
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-bold text-gray-700">Mật khẩu <span className="text-red-500">*</span></span>
                <span className="relative block">
                  <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={8}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="••••••••"
                    className="h-11 w-full rounded-lg border border-gray-200 bg-gray-50 pl-11 pr-12 text-sm outline-none transition-colors placeholder:text-gray-400 focus:border-[#0F6FD6] focus:bg-white focus:ring-2 focus:ring-[#0F6FD6]/10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((value) => !value)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#0F6FD6]"
                    aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </span>
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-bold text-gray-700">Vai trò</span>
                <select
                  value={role}
                  onChange={(event) => setRole(event.target.value as Extract<UserRole, 'candidate' | 'employer'>)}
                  className="h-11 w-full rounded-lg border border-gray-200 bg-gray-50 px-4 text-sm font-medium text-gray-700 outline-none transition-colors focus:border-[#0F6FD6] focus:bg-white focus:ring-2 focus:ring-[#0F6FD6]/10"
                >
                  <option value="candidate">Candidate</option>
                  <option value="employer">Employer</option>
                </select>
              </label>

              <button
                type="submit"
                disabled={submitting}
                className="h-12 w-full rounded-lg bg-[#0F6FD6] text-sm font-bold text-white shadow-xl shadow-blue-500/20 transition-colors hover:bg-[#0B5FB9] disabled:cursor-not-allowed disabled:opacity-70"
              >
                {submitting ? 'Đang tạo tài khoản...' : 'Đăng ký tài khoản'}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-gray-500">
              Đã có tài khoản?{' '}
              <Link to="/login" className="font-bold text-[#0F6FD6]">
                Đăng nhập
              </Link>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Register;
