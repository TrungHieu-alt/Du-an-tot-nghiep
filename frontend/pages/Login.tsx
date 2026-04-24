
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Briefcase, ArrowLeft, Mail, Lock, Eye, EyeOff, CheckSquare, Square, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { AuthResponse } from '../types';
import api from '../lib/api';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // 1. Send Login Request
      const response = await api.post('/auth/login', {
        email,
        password,
        rememberMe,
      });

      const authData = response.data as AuthResponse;
      
      // 2. Successful Login Handling
      if (authData.accessToken && authData.user) {
        // Save to sessionStorage
        sessionStorage.setItem("accessToken", authData.accessToken);
        sessionStorage.setItem("user", JSON.stringify(authData.user));
        
        // Update global auth state
        login(authData.accessToken, authData.user);
        
        // Redirect to homepage
        navigate('/');
      }
    } catch (err: any) {
      console.error("Login error:", err);
      
      // 3. Failed Login Handling
      // STRICT requirement: Use exact message from backend, no mock fallback.
      if (err.response && err.response.data) {
        const { message } = err.response.data;
        // Display the message field exactly (handle array if validation error, else string)
        const displayMessage = Array.isArray(message) ? message.join(', ') : message;
        setError(displayMessage);
      } else {
        // Fallback only if no response received (Network Error) but NOT a mock login
        setError("Không thể kết nối đến máy chủ. Vui lòng thử lại sau.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen w-full flex items-center justify-center p-4 bg-[#F5F6F8] overflow-hidden">
      <div className="bg-white rounded-[24px] shadow-2xl w-full max-w-[1000px] flex flex-col md:flex-row h-full md:h-auto md:max-h-[85vh] overflow-hidden animate-fade-in">
        
        {/* Left Column - Hero/Info */}
        <div className="hidden md:flex md:w-5/12 bg-gradient-to-br from-[#0A65CC] to-[#00B14F] p-8 flex-col justify-between relative overflow-hidden text-white shrink-0">
          {/* Decorative shapes */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full -mr-20 -mt-20"></div>
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-white opacity-5 rounded-full -ml-10 -mb-10"></div>
          
          <div className="relative z-10">
            <Link to="/" className="flex items-center gap-2 mb-8 opacity-90 hover:opacity-100 transition-opacity">
              <div className="bg-white/20 p-2 rounded-lg backdrop-blur-sm">
                <Briefcase className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight">JobConnect</span>
            </Link>

            <h1 className="text-3xl font-bold mb-4 leading-tight">
              Chào mừng <br />trở lại!
            </h1>
            <p className="text-blue-50 text-sm leading-relaxed mb-6">
              Đăng nhập để tiếp tục hành trình sự nghiệp và kết nối với các cơ hội hàng đầu.
            </p>
          </div>

          <div className="relative z-10 space-y-3">
            <div className="bg-white/10 backdrop-blur-md p-3.5 rounded-xl border border-white/10 flex items-center gap-3">
              <div className="bg-white/20 p-1.5 rounded-lg">
                <CheckSquare className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-sm">Tìm việc nhanh chóng</h3>
                <p className="text-blue-100 text-xs">Cập nhật việc làm mỗi ngày</p>
              </div>
            </div>
            
            <div className="bg-white/10 backdrop-blur-md p-3.5 rounded-xl border border-white/10 flex items-center gap-3">
              <div className="bg-white/20 p-1.5 rounded-lg">
                <Briefcase className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-sm">Quản lý hồ sơ</h3>
                <p className="text-blue-100 text-xs">Lưu trữ công việc quan tâm</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Form */}
        <div className="w-full md:w-7/12 flex flex-col bg-white h-full relative">
            <div className="flex-1 overflow-y-auto p-6 md:p-10 lg:p-12 custom-scrollbar flex flex-col justify-center">
                <div className="max-w-md mx-auto w-full">
                    <div className="mb-6">
                        <Link to="/" className="inline-flex items-center text-gray-500 hover:text-[#0A65CC] mb-6 transition-colors text-xs font-semibold uppercase tracking-wide">
                        <ArrowLeft className="w-3 h-3 mr-1" />
                        Quay lại
                        </Link>
                        <h2 className="text-2xl font-bold text-gray-900 mb-1">Đăng nhập</h2>
                        <p className="text-sm text-gray-500">Nhập thông tin tài khoản của bạn</p>
                    </div>

                    {error && (
                      <div className="mb-4 bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-lg flex items-start gap-2 text-sm animate-in fade-in slide-in-from-top-1">
                        <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                        <span>{error}</span>
                      </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-1.5">
                        <label className="text-sm font-semibold text-gray-700" htmlFor="email">Email</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Mail className="h-4.5 w-4.5 text-gray-400" />
                            </div>
                            <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            disabled={isLoading}
                            className="block w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/20 focus:border-[#0A65CC] transition-all text-sm font-medium disabled:opacity-70 disabled:cursor-not-allowed"
                            placeholder="name@example.com"
                            required
                            />
                        </div>
                        </div>

                        <div className="space-y-1.5">
                        <div className="flex justify-between items-center">
                            <label className="text-sm font-semibold text-gray-700" htmlFor="password">Mật khẩu</label>
                            <button type="button" className="text-xs font-semibold text-[#0A65CC] hover:text-[#004799] transition-colors">
                            Quên mật khẩu?
                            </button>
                        </div>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Lock className="h-4.5 w-4.5 text-gray-400" />
                            </div>
                            <input
                            id="password"
                            type={showPassword ? "text" : "password"}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={isLoading}
                            className="block w-full pl-10 pr-10 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/20 focus:border-[#0A65CC] transition-all text-sm font-medium disabled:opacity-70 disabled:cursor-not-allowed"
                            placeholder="••••••••"
                            required
                            />
                            <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            disabled={isLoading}
                            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-70"
                            >
                            {showPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                            </button>
                        </div>
                        </div>

                        <div className="flex items-center pt-1">
                        <button
                            type="button"
                            onClick={() => setRememberMe(!rememberMe)}
                            disabled={isLoading}
                            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors group disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            {rememberMe ? (
                            <CheckSquare className="w-4.5 h-4.5 text-[#0A65CC]" />
                            ) : (
                            <Square className="w-4.5 h-4.5 text-gray-400 group-hover:text-gray-500" />
                            )}
                            <span className="ml-2 text-sm">Ghi nhớ đăng nhập</span>
                        </button>
                        </div>

                        <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-[#0A65CC] text-white py-3 rounded-lg font-bold text-sm hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-[#0A65CC]/20 transition-all shadow-lg shadow-blue-500/30 transform active:scale-[0.98] mt-2 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
                        >
                        {isLoading ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Đang xử lý...
                          </>
                        ) : (
                          'Đăng nhập'
                        )}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-sm text-gray-500">
                        Chưa có tài khoản?{' '}
                        <Link to="/register" className="font-bold text-[#0A65CC] hover:text-[#004799] hover:underline transition-all">
                        Đăng ký ngay
                        </Link>
                    </div>

                    <div className="mt-6">
                        <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-200"></div>
                        </div>
                        <div className="relative flex justify-center text-xs">
                            <span className="px-3 bg-white text-gray-400 font-medium">Hoặc đăng nhập với</span>
                        </div>
                        </div>

                        <div className="mt-4 grid grid-cols-2 gap-3">
                        <button className="flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-all group">
                            <svg className="h-4 w-4" viewBox="0 0 24 24">
                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                            </svg>
                            <span className="text-xs font-semibold text-gray-600 group-hover:text-gray-800">Google</span>
                        </button>
                        
                        <button className="flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-all group">
                            <svg className="h-4 w-4 text-[#1877F2]" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                            </svg>
                            <span className="text-xs font-semibold text-gray-600 group-hover:text-gray-800">Facebook</span>
                        </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
