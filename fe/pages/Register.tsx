
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Briefcase, ArrowLeft, User, Mail, Lock, Eye, EyeOff, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { authApi, RegisterDto } from '../src/api/auth';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterDto>();

  const onSubmit = async (data: RegisterDto) => {
    setIsLoading(true);
    setApiError(null);

    try {
      const response = await authApi.register(data);
      
      // Lưu thông tin vào localStorage theo yêu cầu
      if (response.accessToken) {
        localStorage.setItem('accessToken', response.accessToken);
      }
      localStorage.setItem('user', JSON.stringify(response.user));

      alert('Đăng ký thành công!');
      
      // Điều hướng sang trang đăng nhập (hoặc dashboard tùy logic)
      navigate('/login');
    } catch (error: any) {
      setApiError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const benefits = [
    "Hoàn toàn miễn phí",
    "Kết nối với nhà tuyển dụng hàng đầu",
    "Nhận thông báo việc làm phù hợp"
  ];

  return (
    <div className="h-screen w-full flex items-center justify-center p-4 bg-[#F5F6F8] overflow-hidden">
      <div className="bg-white rounded-[24px] shadow-2xl w-full max-w-[1000px] flex flex-col md:flex-row h-full md:h-auto md:max-h-[90vh] overflow-hidden animate-fade-in">
        
        {/* Left Column - Hero/Info */}
        <div className="hidden md:flex md:w-5/12 bg-gradient-to-br from-[#0A65CC] to-[#00B14F] p-8 flex-col justify-between relative overflow-hidden text-white shrink-0">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full -mr-20 -mt-20"></div>
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-white opacity-5 rounded-full -ml-10 -mb-10"></div>
          
          <div className="relative z-10 mt-4">
            <Link to="/" className="flex items-center gap-2 mb-8 opacity-90 hover:opacity-100 transition-opacity">
              <div className="bg-white/20 p-2 rounded-lg backdrop-blur-sm">
                <Briefcase className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight">JobConnect</span>
            </Link>

            <h1 className="text-3xl font-bold mb-4 leading-tight">Bắt đầu <br />hành trình mới</h1>
            <p className="text-blue-50 text-sm leading-relaxed opacity-90">
              Tạo tài khoản miễn phí và khám phá hàng nghìn cơ hội việc làm phù hợp với bạn ngay hôm nay.
            </p>
          </div>

          <div className="relative z-10 space-y-3 mb-4">
            {benefits.map((benefit, index) => (
              <div key={index} className="flex items-center gap-3 text-blue-50">
                <div className="bg-white/20 p-1 rounded-full">
                  <CheckCircle className="w-3.5 h-3.5 text-white" />
                </div>
                <span className="text-sm font-medium">{benefit}</span>
              </div>
            ))}
          </div>
          
          <div className="text-xs text-blue-100 opacity-60">© 2024 JobConnect Inc.</div>
        </div>

        {/* Right Column - Form */}
        <div className="w-full md:w-7/12 flex flex-col bg-white h-full relative">
            <div className="flex-1 overflow-y-auto p-6 md:p-8 lg:p-10 custom-scrollbar">
                <div className="max-w-md mx-auto">
                    <div className="mb-6">
                        <Link to="/" className="inline-flex items-center text-gray-500 hover:text-[#0A65CC] mb-4 transition-colors text-xs font-semibold uppercase tracking-wide">
                          <ArrowLeft className="w-3 h-3 mr-1" /> Quay lại
                        </Link>
                        <h2 className="text-2xl font-bold text-gray-900 mb-1">Đăng ký tài khoản</h2>
                        <p className="text-sm text-gray-500">Điền thông tin của bạn để bắt đầu</p>
                    </div>

                    {apiError && (
                      <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-lg flex items-center gap-2 text-red-600 text-sm animate-shake">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>{apiError}</span>
                      </div>
                    )}

                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        {/* Name Field */}
                        <div className="space-y-1">
                            <label className="text-sm font-semibold text-gray-700" htmlFor="name">Họ tên (tùy chọn)</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                  <User className="h-4 w-4 text-gray-400" />
                                </div>
                                <input
                                  {...register('name')}
                                  id="name"
                                  className="block w-full pl-9 pr-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/20 focus:border-[#0A65CC] transition-all text-sm font-medium"
                                  placeholder="Nguyễn Văn A"
                                  disabled={isLoading}
                                />
                            </div>
                        </div>

                        {/* Email Field */}
                        <div className="space-y-1">
                            <label className="text-sm font-semibold text-gray-700" htmlFor="email">Email <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                  <Mail className="h-4 w-4 text-gray-400" />
                                </div>
                                <input
                                  {...register('email', { 
                                    required: 'Email là bắt buộc',
                                    pattern: {
                                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                                      message: 'Email không đúng định dạng'
                                    }
                                  })}
                                  id="email"
                                  type="email"
                                  className={`block w-full pl-9 pr-3 py-2.5 bg-gray-50 border ${errors.email ? 'border-red-500' : 'border-gray-200'} rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/20 focus:border-[#0A65CC] transition-all text-sm font-medium`}
                                  placeholder="name@example.com"
                                  disabled={isLoading}
                                />
                            </div>
                            {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
                        </div>

                        {/* Password Field */}
                        <div className="space-y-1">
                            <label className="text-sm font-semibold text-gray-700" htmlFor="password">Mật khẩu <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                  <Lock className="h-4 w-4 text-gray-400" />
                                </div>
                                <input
                                  {...register('password', { 
                                    required: 'Mật khẩu là bắt buộc',
                                    minLength: { value: 6, message: 'Mật khẩu phải có ít nhất 6 ký tự' }
                                  })}
                                  id="password"
                                  type={showPassword ? "text" : "password"}
                                  className={`block w-full pl-9 pr-10 py-2.5 bg-gray-50 border ${errors.password ? 'border-red-500' : 'border-gray-200'} rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/20 focus:border-[#0A65CC] transition-all text-sm font-medium`}
                                  placeholder="••••••••"
                                  disabled={isLoading}
                                />
                                <button
                                  type="button"
                                  onClick={() => setShowPassword(!showPassword)}
                                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
                                >
                                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                            {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
                        </div>

                        <button
                          type="submit"
                          disabled={isLoading}
                          className="w-full bg-[#0A65CC] text-white py-3 rounded-lg font-bold text-sm hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-[#0A65CC]/20 transition-all shadow-lg shadow-blue-500/30 transform active:scale-[0.98] mt-2 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                          {isLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              Đang xử lý...
                            </>
                          ) : (
                            'Đăng ký tài khoản'
                          )}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-sm text-gray-500">
                        Đã có tài khoản?{' '}
                        <Link to="/login" className="font-bold text-[#0A65CC] hover:text-[#004799] hover:underline transition-all">
                          Đăng nhập
                        </Link>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
