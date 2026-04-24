import React from 'react';
import { Facebook, Linkedin, Twitter, Youtube, Briefcase } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-[#18191C] text-gray-400 py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-12">
          
          {/* Brand Column */}
          <div className="space-y-6">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-[#0A65CC] to-[#00B14F] p-2.5 rounded-xl">
                <Briefcase className="w-7 h-7 text-white" strokeWidth={2.5} />
              </div>
              <span className="text-2xl font-bold tracking-tight text-white">
                Job<span className="text-[#00B14F]">Connect</span>
              </span>
            </div>
            <p className="text-gray-400 leading-relaxed text-sm">
              Nền tảng kết nối việc làm và nhân tài hàng đầu Việt Nam. Chúng tôi cam kết mang lại giá trị thực cho cộng đồng.
            </p>
            <div className="flex gap-3">
              <a href="#" className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center hover:bg-[#0A65CC] hover:text-white transition-all">
                <Facebook className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center hover:bg-[#1DA1F2] hover:text-white transition-all">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center hover:bg-[#0077B5] hover:text-white transition-all">
                <Linkedin className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center hover:bg-[#FF0000] hover:text-white transition-all">
                <Youtube className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Links Columns */}
          <div>
            <h3 className="text-white font-bold text-lg mb-6">Về chúng tôi</h3>
            <ul className="space-y-4 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">Giới thiệu</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Liên hệ</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Tin tức</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Bảo mật</a></li>
            </ul>
          </div>

          <div>
            <h3 className="text-white font-bold text-lg mb-6">Dành cho ứng viên</h3>
            <ul className="space-y-4 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">Tìm việc làm</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Công ty hàng đầu</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Cẩm nang nghề nghiệp</a></li>
              <li><a href="#" className="hover:text-white transition-colors">CV Hay</a></li>
            </ul>
          </div>

          <div>
            <h3 className="text-white font-bold text-lg mb-6">Dành cho nhà tuyển dụng</h3>
            <ul className="space-y-4 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">Đăng tin tuyển dụng</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Tìm ứng viên</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Sản phẩm dịch vụ</a></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center text-sm">
          <p>© 2024 JobConnect. All rights reserved.</p>
          <div className="flex gap-6 mt-4 md:mt-0 font-medium text-gray-400">
             <span className="text-white">Hỗ trợ & Chính sách</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;