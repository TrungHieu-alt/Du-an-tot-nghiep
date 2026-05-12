import React from 'react';
import { Link } from 'react-router-dom';
import { BriefcaseBusiness, Facebook, Linkedin, Twitter, Youtube } from 'lucide-react';

const Footer: React.FC = () => (
  <footer className="bg-[#15171B] text-sm text-gray-400">
    <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6 lg:px-8">
      <div className="grid gap-10 md:grid-cols-[1.3fr_1fr_1fr_1fr]">
        <div>
          <Link to="/" className="mb-6 flex items-center gap-3">
            <div className="rounded-xl bg-gradient-to-br from-[#0F6FD6] to-[#00A86B] p-2">
              <BriefcaseBusiness className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold">
              <span className="text-white">Job</span>
              <span className="text-[#00A86B]">Connect</span>
            </span>
          </Link>
          <p className="max-w-xs leading-7">
            Nền tảng kết nối việc làm và nhân tài hàng đầu Việt Nam. Chúng tôi cam kết
            mang lại giá trị thực cho cộng đồng.
          </p>
          <div className="mt-6 flex gap-3">
            {[Facebook, Twitter, Linkedin, Youtube].map((Icon, index) => (
              <button
                key={index}
                type="button"
                className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-slate-800 text-gray-300 transition-colors hover:bg-[#0F6FD6] hover:text-white"
                aria-label="Social link"
              >
                <Icon className="h-4 w-4" />
              </button>
            ))}
          </div>
        </div>

        <div>
          <h3 className="mb-5 text-base font-bold text-white">Về chúng tôi</h3>
          <div className="flex flex-col gap-4">
            <Link to="/" className="hover:text-white">Giới thiệu</Link>
            <Link to="/" className="hover:text-white">Liên hệ</Link>
            <Link to="/" className="hover:text-white">Tin tức</Link>
            <Link to="/" className="hover:text-white">Bảo mật</Link>
          </div>
        </div>

        <div>
          <h3 className="mb-5 text-base font-bold text-white">Dành cho ứng viên</h3>
          <div className="flex flex-col gap-4">
            <Link to="/v2/search" className="hover:text-white">Tìm việc làm</Link>
            <Link to="/#companies" className="hover:text-white">Công ty hàng đầu</Link>
            <Link to="/" className="hover:text-white">Cẩm nang nghề nghiệp</Link>
            <Link to="/v2/matching" className="hover:text-white">CV Hay</Link>
          </div>
        </div>

        <div>
          <h3 className="mb-5 text-base font-bold text-white">Dành cho nhà tuyển dụng</h3>
          <div className="flex flex-col gap-4">
            <Link to="/register" className="hover:text-white">Đăng tin tuyển dụng</Link>
            <Link to="/v2/search?type=cv" className="hover:text-white">Tìm ứng viên</Link>
            <Link to="/v2/matching" className="hover:text-white">Sản phẩm dịch vụ</Link>
          </div>
        </div>
      </div>

      <div className="mt-12 flex flex-col gap-4 border-t border-slate-800 pt-8 sm:flex-row sm:items-center sm:justify-between">
        <p>© 2024 JobConnect. All rights reserved.</p>
        <Link to="/" className="font-semibold text-gray-300 hover:text-white">
          Hỗ trợ & Chính sách
        </Link>
      </div>
    </div>
  </footer>
);

export default Footer;
