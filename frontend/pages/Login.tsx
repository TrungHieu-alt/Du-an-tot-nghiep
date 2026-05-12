import React, { useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  BriefcaseBusiness,
  Briefcase,
  CheckSquare,
  Eye,
  EyeOff,
  Facebook,
  Lock,
  Mail,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { normalizeApiError } from '../lib/api-error';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const justRegistered = useMemo(
    () => Boolean((location.state as { registered?: boolean } | null)?.registered),
    [location.state]
  );

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login({ email, password });
      navigate('/v2/search', { replace: true });
    } catch (err) {
      setError(normalizeApiError(err).displayMessage);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthPageFrame
      title="Chào mừng trở lại!"
      subtitle="Đăng nhập để tiếp tục hành trình sự nghiệp và kết nối với các cơ hội hàng đầu."
      cards={[
        { icon: CheckSquare, title: 'Tìm việc nhanh chóng', text: 'Cập nhật việc làm mỗi ngày' },
        { icon: Briefcase, title: 'Quản lý hồ sơ', text: 'Lưu trữ công việc quan tâm' },
      ]}
    >
      <div className="mb-7">
        <Link to="/" className="text-xs font-semibold uppercase text-gray-500 hover:text-[#0F6FD6]">
          ← Quay lại
        </Link>
        <h1 className="mt-6 text-2xl font-bold text-gray-900">Đăng nhập</h1>
        <p className="mt-2 text-sm text-gray-500">Nhập thông tin tài khoản của bạn</p>
      </div>

      {justRegistered && (
        <div className="mb-5 rounded-lg border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
          Đăng ký thành công. Vui lòng đăng nhập để tiếp tục.
        </div>
      )}

      {error && (
        <div className="mb-5 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <label className="block">
          <span className="mb-2 block text-sm font-bold text-gray-700">Email</span>
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
          <span className="mb-2 flex items-center justify-between text-sm font-bold text-gray-700">
            Mật khẩu
            <Link to="/login" className="text-xs font-bold text-[#0F6FD6]">
              Quên mật khẩu?
            </Link>
          </span>
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

        <label className="flex items-center gap-3 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={remember}
            onChange={(event) => setRemember(event.target.checked)}
            className="h-5 w-5 rounded border-gray-300 text-[#0F6FD6]"
          />
          Ghi nhớ đăng nhập
        </label>

        <button
          type="submit"
          disabled={submitting}
          className="h-12 w-full rounded-lg bg-[#0F6FD6] text-sm font-bold text-white shadow-xl shadow-blue-500/20 transition-colors hover:bg-[#0B5FB9] disabled:cursor-not-allowed disabled:opacity-70"
        >
          {submitting ? 'Đang đăng nhập...' : 'Đăng nhập'}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        Chưa có tài khoản?{' '}
        <Link to="/register" className="font-bold text-[#0F6FD6]">
          Đăng ký ngay
        </Link>
      </p>

      <div className="my-7 flex items-center gap-3 text-xs text-gray-400">
        <div className="h-px flex-1 bg-gray-200" />
        Hoặc đăng nhập với
        <div className="h-px flex-1 bg-gray-200" />
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <SocialButton label="Google" mark="G" />
        <SocialButton label="Facebook" icon={<Facebook className="h-4 w-4 text-[#1877F2]" />} />
      </div>
    </AuthPageFrame>
  );
};

interface AuthPageFrameProps {
  title: string;
  subtitle: string;
  cards: Array<{ icon: React.ElementType; title: string; text: string }>;
  children: React.ReactNode;
}

const AuthPageFrame: React.FC<AuthPageFrameProps> = ({ title, subtitle, cards, children }) => (
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

          <div className="mt-8 max-w-xs">
            <h2 className="text-3xl font-bold leading-tight">{title}</h2>
            <p className="mt-5 text-sm leading-7 text-white/90">{subtitle}</p>
          </div>

          <div className="mt-auto space-y-3">
            {cards.map((card) => {
              const Icon = card.icon;
              return (
                <div key={card.title} className="flex items-center gap-3 rounded-lg border border-white/15 bg-white/10 p-4">
                  <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-white/15">
                    <Icon className="h-5 w-5" />
                  </span>
                  <span>
                    <span className="block text-sm font-bold">{card.title}</span>
                    <span className="block text-xs text-white/80">{card.text}</span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </aside>

      <section className="flex items-center justify-center px-6 py-10 sm:px-10">
        <div className="w-full max-w-[392px]">{children}</div>
      </section>
    </div>
  </div>
);

const SocialButton: React.FC<{ label: string; mark?: string; icon?: React.ReactNode }> = ({
  label,
  mark,
  icon,
}) => (
  <button
    type="button"
    className="inline-flex h-10 items-center justify-center gap-3 rounded-lg border border-gray-200 bg-white text-sm font-bold text-gray-600 transition-colors hover:border-[#0F6FD6] hover:text-[#0F6FD6]"
  >
    {mark ? <span className="font-bold text-[#EA4335]">{mark}</span> : icon}
    {label}
  </button>
);

export default Login;
