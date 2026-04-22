
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, MapPin, ArrowRight, Code, PenTool, BarChart3, 
  Megaphone, HeartHandshake, Coins, Bookmark, Briefcase, Users
} from 'lucide-react';
import { Job, Company, Category, Testimonial } from '../types';
import { PageFindJobsButton, PageFindCandidatesButton } from '../components/PageActionButtons';
import LocationSelect from '../components/LocationSelect';
import { useModal } from '../contexts/ModalContext';
import { useAuth } from '../contexts/AuthContext';

// --- Mock Data ---

const categories: Category[] = [
  { id: 1, name: "IT - Phần mềm", count: 2543, iconName: "Code" },
  { id: 2, name: "Marketing", count: 1876, iconName: "Megaphone" },
  { id: 3, name: "Kinh doanh", count: 1654, iconName: "BarChart3" },
  { id: 4, name: "Thiết kế", count: 892, iconName: "PenTool" },
  { id: 5, name: "Kế toán - Tài chính", count: 1432, iconName: "Coins" },
  { id: 6, name: "Nhân sự", count: 765, iconName: "HeartHandshake" },
  { id: 7, name: "Y tế - Dược", count: 543, iconName: "Users" },
  { id: 8, name: "Giáo dục", count: 987, iconName: "Briefcase" },
];

const featuredJobs: Job[] = [
  { 
    id: 1, 
    title: "Senior Frontend Developer", 
    company: "Tech Innovation Co.", 
    logo: "https://images.unsplash.com/photo-1571171637578-41bc2dd41cd2?w=100&h=100&fit=crop", 
    salary: "$ 25 - 35 triệu", 
    location: "Hà Nội",
    tags: []
  },
  { 
    id: 2, 
    title: "Marketing Manager", 
    company: "Digital Growth Agency", 
    logo: "https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=100&h=100&fit=crop", 
    salary: "$ 20 - 30 triệu", 
    location: "Hồ Chí Minh",
    tags: []
  },
  { 
    id: 3, 
    title: "UX/UI Designer", 
    company: "Creative Studio Ltd.", 
    logo: "https://images.unsplash.com/photo-1551434678-e076c223a692?w=100&h=100&fit=crop", 
    salary: "$ 18 - 25 triệu", 
    location: "Đà Nẵng",
    tags: []
  },
  { 
    id: 4, 
    title: "Business Development Executive", 
    company: "Global Solutions Inc.", 
    logo: "https://images.unsplash.com/photo-1552664730-d307ca884978?w=100&h=100&fit=crop", 
    salary: "$ 15 - 20 triệu + KPI", 
    location: "Hà Nội",
    tags: []
  },
  { 
    id: 5, 
    title: "Full Stack Developer", 
    company: "Startup Innovation Hub", 
    logo: "https://images.unsplash.com/photo-1531973576160-7125cd663d86?w=100&h=100&fit=crop", 
    salary: "$ 30 - 40 triệu", 
    location: "Hồ Chí Minh",
    tags: []
  },
  { 
    id: 6, 
    title: "Content Marketing Specialist", 
    company: "Media & Communications Co.", 
    logo: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=100&h=100&fit=crop", 
    salary: "$ 12 - 18 triệu", 
    location: "Remote",
    tags: []
  },
];

const companies: Company[] = [
  { id: 1, name: "TechViet", logo: "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=80&h=80&fit=crop", openPositions: 24 },
  { id: 2, name: "VinaTech", logo: "https://images.unsplash.com/photo-1554774853-719586f8c277?w=80&h=80&fit=crop", openPositions: 18 },
  { id: 3, name: "FPT Software", logo: "https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=80&h=80&fit=crop", openPositions: 45 },
  { id: 4, name: "Viettel Group", logo: "https://images.unsplash.com/photo-1549923746-c502d488b3ea?w=80&h=80&fit=crop", openPositions: 32 },
  { id: 5, name: "MISA", logo: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=80&h=80&fit=crop", openPositions: 15 },
  { id: 6, name: "Base.vn", logo: "https://images.unsplash.com/photo-1497366216548-37526070297c?w=80&h=80&fit=crop", openPositions: 12 },
];

const testimonials: Testimonial[] = [
  {
    id: 1,
    name: "Nguyễn Minh Tuấn",
    role: "Software Engineer tại FPT",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop",
    content: "JobConnect đã giúp tôi tìm được công việc mơ ước chỉ sau 2 tuần. Giao diện thân thiện, việc làm đa dạng và chất lượng!"
  },
  {
    id: 2,
    name: "Trần Thúy Hằng",
    role: "Marketing Manager tại Viettel",
    avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop",
    content: "Tôi rất ấn tượng với chất lượng ứng viên từ JobConnect. Đội ngũ HR của chúng tôi đã tuyển được nhiều nhân tài tốt."
  },
  {
    id: 3,
    name: "Lê Hoàng Nam",
    role: "UX Designer tại Base.vn",
    avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop",
    content: "Nền tảng tuyệt vời cho cả người tìm việc và nhà tuyển dụng. Quy trình ứng tuyển đơn giản và nhanh chóng."
  }
];

// --- Helper Components ---

const CategoryIcon = ({ name }: { name: string }) => {
  const iconProps = { className: "w-7 h-7" };
  const iconMap: Record<string, React.ReactNode> = {
    'Code': <Code className="w-7 h-7 text-[#0A65CC]" />,
    'Megaphone': <Megaphone className="w-7 h-7 text-[#E05151]" />,
    'BarChart3': <BarChart3 className="w-7 h-7 text-[#2563EB]" />,
    'PenTool': <PenTool className="w-7 h-7 text-[#9333EA]" />,
    'Coins': <Coins className="w-7 h-7 text-[#DC2626]" />,
    'HeartHandshake': <HeartHandshake className="w-7 h-7 text-[#059669]" />,
    'Users': <Users className="w-7 h-7 text-[#0891B2]" />,
    'Briefcase': <Briefcase className="w-7 h-7 text-[#D97706]" />,
  };
  
  const bgMap: Record<string, string> = {
    'Code': 'bg-blue-50',
    'Megaphone': 'bg-red-50',
    'BarChart3': 'bg-blue-50',
    'PenTool': 'bg-purple-50',
    'Coins': 'bg-red-50',
    'HeartHandshake': 'bg-green-50',
    'Users': 'bg-cyan-50',
    'Briefcase': 'bg-amber-50',
  };

  return (
    <div className={`${bgMap[name] || 'bg-gray-100'} w-12 h-12 rounded-lg flex items-center justify-center`}>
      {iconMap[name] || <Code {...iconProps} />}
    </div>
  );
};

const Home: React.FC = () => {
  const { openCvModal, openReqModal } = useModal();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLocation, setSearchLocation] = useState('');

  const handleJobsClick = () => {
    if (isAuthenticated) {
      openCvModal();
    } else {
      navigate('/jobs?manual=true');
    }
  };

  const handleCandidatesClick = () => {
    if (isAuthenticated) {
      openReqModal();
    } else {
      navigate('/candidates?manual=true');
    }
  };

  const handleMainSearch = () => {
    const params = new URLSearchParams();
    if (searchQuery.trim()) params.append('q', searchQuery.trim());
    if (searchLocation) params.append('location', searchLocation);
    
    // Default to manual search if coming from home without a CV selected
    params.append('manual', 'true');
    
    navigate({
      pathname: '/jobs',
      search: params.toString()
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleMainSearch();
    }
  };

  return (
    <div className="bg-white font-sans">
      
      {/* 1. Hero Section */}
      <section className="relative bg-gradient-to-r from-[#2563EB] to-[#10B981] pt-24 pb-32 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 opacity-10 bg-[url('https://www.transparenttextures.com/patterns/cross-stripes.png')]"></div>

        <div className="max-w-5xl mx-auto text-center relative z-10">
          <h1 className="text-4xl md:text-5xl lg:text-[56px] font-bold text-white mb-6 leading-[1.2] tracking-tight">
            Kết nối ứng viên và <br/>
            nhà tuyển dụng hàng đầu
          </h1>
          <p className="text-lg text-blue-50 mb-10 max-w-2xl mx-auto font-normal opacity-90">
            Nền tảng tuyển dụng uy tín giúp bạn tìm kiếm công việc mơ ước hoặc <br className="hidden md:block" />
            kết nối với những nhân tài xuất sắc nhất.
          </p>

          {/* Action Buttons - Trigger Global Modals or Manual Search */}
          <div className="flex flex-col sm:flex-row justify-center gap-4 mb-12">
            <PageFindJobsButton onClick={handleJobsClick} />
            <PageFindCandidatesButton onClick={handleCandidatesClick} />
          </div>

          {/* Search Bar - Floating */}
          <div className="bg-white p-2.5 rounded-2xl shadow-xl max-w-4xl mx-auto flex flex-col md:flex-row items-center gap-2">
            <div className="flex-1 w-full md:w-auto relative group px-2">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[#0A65CC]" size={20} />
              <input 
                type="text" 
                placeholder="Tên công việc, vị trí..." 
                className="w-full pl-12 pr-4 py-3 bg-transparent text-gray-800 placeholder-gray-400 focus:outline-none text-[15px]"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleKeyDown}
              />
            </div>
            <div className="w-full md:w-1/3 relative px-2">
              <LocationSelect value={searchLocation} onChange={setSearchLocation} />
            </div>
            <button 
              onClick={handleMainSearch}
              className="w-full md:w-auto bg-[#2563EB] text-white px-8 py-3.5 rounded-xl font-semibold hover:bg-blue-700 transition whitespace-nowrap text-[15px] shadow-sm"
            >
              Tìm kiếm
            </button>
          </div>
        </div>
      </section>

      {/* 2. Job Categories Section */}
      <section className="py-20 bg-[#FAFAFA]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-[#18191C] mb-3">Danh mục ngành nghề</h2>
            <p className="text-gray-500">Khám phá hàng nghìn cơ hội việc làm trong các lĩnh vực hàng đầu</p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {categories.map((cat) => (
              <div key={cat.id} className="group p-6 rounded-xl bg-white border border-transparent hover:border-blue-100 hover:shadow-[0_8px_30px_rgb(0,0,0,0.04)] transition-all duration-300 cursor-pointer flex flex-col items-start">
                <div className="mb-4">
                  <CategoryIcon name={cat.iconName} />
                </div>
                <h3 className="text-[17px] font-bold text-[#18191C] group-hover:text-[#0A65CC] transition-colors mb-1">{cat.name}</h3>
                <p className="text-gray-500 text-sm">{cat.count.toLocaleString()} công việc</p>
              </div>
            ))}
          </div>

          <div className="text-center mt-12">
             <button className="inline-flex items-center text-[#0A65CC] font-semibold border border-[#0A65CC] px-6 py-3 rounded-full hover:bg-blue-50 transition text-sm">
               Xem tất cả ngành nghề <ArrowRight className="ml-2 w-4 h-4" />
             </button>
          </div>
        </div>
      </section>

      {/* 3. Featured Jobs Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-end mb-10">
            <div>
              <h2 className="text-3xl font-bold text-[#18191C] mb-2">Việc làm nổi bật</h2>
              <p className="text-gray-500 text-sm">Cơ hội việc làm tốt nhất dành cho bạn</p>
            </div>
            <a href="#" className="text-[#0A65CC] font-semibold flex items-center gap-1 hover:underline text-sm">
              Xem tất cả <ArrowRight className="w-4 h-4" />
            </a>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {featuredJobs.map((job) => (
              <div key={job.id} className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden flex flex-col h-full group">
                <div className="p-6 flex-grow">
                  <div className="flex justify-between items-start mb-4">
                    <img src={job.logo} alt={job.company} className="w-14 h-14 rounded-lg object-cover" />
                    <button className="text-gray-300 hover:text-[#0A65CC] transition-colors">
                      <Bookmark className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <h3 className="text-lg font-bold text-[#18191C] hover:text-[#0A65CC] cursor-pointer mb-2 leading-tight">
                    {job.title}
                  </h3>
                  
                  <div className="flex items-center gap-2 mb-4">
                     <p className="text-gray-500 text-sm">{job.company}</p>
                  </div>

                  <div className="flex items-center gap-3 text-sm">
                    <span className="px-3 py-1 bg-green-50 text-[#00B14F] font-semibold rounded">{job.salary}</span>
                    <div className="flex items-center text-gray-500">
                      <MapPin className="w-4 h-4 mr-1 text-gray-400" />
                      {job.location}
                    </div>
                  </div>
                </div>
                
                <div className="px-6 pb-6 pt-0">
                  <button className="w-full bg-[#EBF4FF] text-[#0A65CC] font-semibold py-3 rounded-lg hover:bg-[#0A65CC] hover:text-white transition-all duration-300 text-[15px]">
                    Ứng tuyển ngay
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. Top Employers Section */}
      <section className="py-20 bg-[#FAFAFA]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-[#18191C] mb-3">Nhà tuyển dụng hàng đầu</h2>
            <p className="text-gray-500 text-sm">Những công ty hàng đầu đang tìm kiếm ứng viên tài năng</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {companies.map((company) => (
              <div key={company.id} className="bg-white p-6 rounded-xl border border-transparent hover:border-blue-100 hover:shadow-lg transition-all duration-300 cursor-pointer flex flex-col items-center text-center group">
                <div className="w-16 h-16 mb-4 relative">
                    <img src={company.logo} alt={company.name} className="w-full h-full object-contain rounded-lg group-hover:scale-105 transition-transform" />
                </div>
                <h4 className="font-bold text-[#18191C] mb-2 text-[15px]">{company.name}</h4>
                <div className="inline-block bg-blue-50 text-[#0A65CC] text-xs font-medium px-2.5 py-1 rounded">
                  {company.openPositions} vị trí đang tuyển
                </div>
              </div>
            ))}
          </div>
          
          <div className="text-center mt-12">
            <button className="bg-[#0A65CC] text-white font-semibold px-8 py-3.5 rounded-full hover:bg-blue-700 transition shadow-lg shadow-blue-500/30 text-sm">
              Xem tất cả công ty
            </button>
          </div>
        </div>
      </section>

      {/* 5. Testimonials Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
             <h2 className="text-3xl font-bold text-[#18191C] mb-3">Phản hồi từ người dùng</h2>
             <p className="text-gray-500">Câu chuyện thành công từ những người đã tìm được việc làm ý tưởng</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial) => (
              <div key={testimonial.id} className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl transition-all duration-300 relative group">
                <div className="absolute top-8 left-8">
                   <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M14.017 21L14.017 18C14.017 16.8954 14.9124 16 16.017 16H19.017C19.5693 16 20.017 15.5523 20.017 15V9C20.017 8.44772 19.5693 8 19.017 8H15.017C14.4647 8 14.017 8.44772 14.017 9V11C14.017 11.5523 13.5693 12 13.017 12H12.017V5H22.017V15C22.017 18.3137 19.3307 21 16.017 21H14.017ZM5.0166 21L5.0166 18C5.0166 16.8954 5.91203 16 7.0166 16H10.0166C10.5689 16 11.0166 15.5523 11.0166 15V9C11.0166 8.44772 10.5689 8 10.0166 8H6.0166C5.46432 8 5.0166 8.44772 5.0166 9V11C5.0166 11.5523 4.56889 12 4.0166 12H3.0166V5H13.0166V15C13.0166 18.3137 10.3303 21 7.0166 21H5.0166Z" fill="#EBF4FF"/>
                   </svg>
                </div>
                
                <p className="text-gray-600 mb-8 mt-12 italic relative z-10 leading-relaxed text-[15px]">"{testimonial.content}"</p>
                
                <div className="flex items-center gap-4 border-t border-gray-100 pt-6">
                  <img src={testimonial.avatar} alt={testimonial.name} className="w-12 h-12 rounded-full object-cover ring-2 ring-white shadow-sm" />
                  <div>
                    <h5 className="font-bold text-[#18191C] text-[15px]">{testimonial.name}</h5>
                    <p className="text-xs text-gray-500 font-medium">{testimonial.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. CTA Section */}
      <section className="relative py-24 bg-gradient-to-r from-[#2563EB] to-[#00B14F] overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full">
           <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-white opacity-5 rounded-full -mr-32 -mt-32"></div>
           <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-white opacity-5 rounded-full -ml-16 -mb-16"></div>
        </div>

        <div className="max-w-4xl mx-auto text-center px-4 relative z-10">
          <h2 className="text-3xl md:text-4xl lg:text-[40px] font-bold text-white mb-6 leading-tight">
            Khám phá hàng nghìn cơ hội việc làm ngay hôm nay
          </h2>
          <p className="text-white text-lg mb-10 opacity-90 font-light">
            Tham gia cùng hơn 500,000 ứng viên và 10,000 doanh nghiệp đã tin tưởng JobConnect
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-5">
            <button onClick={handleJobsClick} className="bg-white text-[#0A65CC] px-8 py-3.5 rounded-lg font-bold text-base hover:bg-blue-50 transition shadow-xl">
              Bắt đầu tìm việc
            </button>
            <button className="bg-transparent border-2 border-white text-white px-8 py-3.5 rounded-lg font-bold text-base hover:bg-white/10 transition">
              Đăng tin tuyển dụng
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
