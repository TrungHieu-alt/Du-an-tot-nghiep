import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  BarChart3,
  Calculator,
  Code2,
  HeartHandshake,
  MapPin,
  Megaphone,
  Palette,
  Quote,
  Search,
  Stethoscope,
  Users,
  GraduationCap,
  Bookmark,
  MessageCircle,
} from 'lucide-react';

const PRIMARY_BLUE = '#0F6FD6';
const PRIMARY_GREEN = '#00A86B';

const categories = [
  { title: 'IT - Phần mềm', jobs: '2,543 công việc', icon: Code2, tone: 'bg-blue-50 text-blue-600' },
  { title: 'Marketing', jobs: '1,876 công việc', icon: Megaphone, tone: 'bg-red-50 text-red-500' },
  { title: 'Kinh doanh', jobs: '1,654 công việc', icon: BarChart3, tone: 'bg-sky-50 text-sky-600' },
  { title: 'Thiết kế', jobs: '892 công việc', icon: Palette, tone: 'bg-purple-50 text-purple-600' },
  { title: 'Kế toán - Tài chính', jobs: '1,432 công việc', icon: Calculator, tone: 'bg-rose-50 text-rose-500' },
  { title: 'Nhân sự', jobs: '765 công việc', icon: HeartHandshake, tone: 'bg-emerald-50 text-emerald-600' },
  { title: 'Y tế - Dược', jobs: '543 công việc', icon: Stethoscope, tone: 'bg-cyan-50 text-cyan-600' },
  { title: 'Giáo dục', jobs: '987 công việc', icon: GraduationCap, tone: 'bg-amber-50 text-amber-600' },
];

const featuredJobs = [
  {
    title: 'Business Development Executive',
    company: 'Global Solutions Inc.',
    salary: '$ 15 - 20 triệu + KPI',
    location: 'Hà Nội',
    image: 'https://images.unsplash.com/photo-1556761175-b413da4baf72?auto=format&fit=crop&w=96&q=80',
  },
  {
    title: 'Full Stack Developer',
    company: 'Startup Innovation Hub',
    salary: '$ 30 - 40 triệu',
    location: 'Hồ Chí Minh',
    image: 'https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=96&q=80',
  },
  {
    title: 'Content Marketing Specialist',
    company: 'Media & Communications Co.',
    salary: '$ 12 - 18 triệu',
    location: 'Remote',
    image: 'https://images.unsplash.com/photo-1557804506-669a67965ba0?auto=format&fit=crop&w=96&q=80',
  },
];

const employers = [
  { name: 'TechViet', jobs: '24 vị trí đang tuyển', image: 'https://images.unsplash.com/photo-1551434678-e076c223a692?auto=format&fit=crop&w=96&q=80' },
  { name: 'VinaTech', jobs: '18 vị trí đang tuyển', image: 'https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=96&q=80' },
  { name: 'FPT Software', jobs: '45 vị trí đang tuyển', image: 'https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=96&q=80' },
  { name: 'Viettel Group', jobs: '32 vị trí đang tuyển', image: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=96&q=80' },
  { name: 'MISA', jobs: '15 vị trí đang tuyển', image: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=96&q=80' },
  { name: 'Base.vn', jobs: '12 vị trí đang tuyển', image: 'https://images.unsplash.com/photo-1497366412874-3415097a27e7?auto=format&fit=crop&w=96&q=80' },
];

const testimonials = [
  {
    quote: 'JobConnect đã giúp tôi tìm được công việc mơ ước chỉ sau 2 tuần. Giao diện thân thiện, việc làm đa dạng và chất lượng!',
    name: 'Nguyễn Minh Tuấn',
    title: 'Software Engineer tại FPT',
    image: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=96&q=80',
  },
  {
    quote: 'Tôi rất ấn tượng với chất lượng ứng viên từ JobConnect. Đội ngũ HR của chúng tôi đã tuyển được nhiều nhân tài tốt.',
    name: 'Trần Thúy Hằng',
    title: 'Marketing Manager tại Viettel',
    image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=96&q=80',
  },
  {
    quote: 'Nền tảng tuyệt vời cho cả người tìm việc và nhà tuyển dụng. Quy trình ứng tuyển đơn giản và nhanh chóng.',
    name: 'Lê Hoàng Nam',
    title: 'UX Designer tại Base.vn',
    image: 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=96&q=80',
  },
];

const cityOptions = [
  { value: '', label: 'Tỉnh/Thành phố' },
  { value: 'ha_noi', label: 'Hà Nội' },
  { value: 'tp_hcm', label: 'Hồ Chí Minh' },
  { value: 'da_nang', label: 'Đà Nẵng' },
];

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [keyword, setKeyword] = useState('');
  const [city, setCity] = useState('');

  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault();
    const params = new URLSearchParams();
    if (keyword.trim()) params.set('q', keyword.trim());
    if (city) params.set('location', city);
    navigate(`/v2/search${params.toString() ? `?${params.toString()}` : ''}`);
  };

  return (
    <div className="bg-white text-[#202124]">
      <section className="relative overflow-hidden bg-gradient-to-br from-[#2466E8] via-[#1196B7] to-[#14B86A]">
        <div className="absolute left-[-90px] top-28 h-64 w-64 rounded-full bg-white/10" />
        <div className="absolute right-[-120px] top-[-90px] h-80 w-80 rounded-full bg-white/10" />
        <div className="mx-auto max-w-6xl px-4 pb-28 pt-20 text-center text-white sm:px-6 lg:px-8">
          <h1 className="mx-auto max-w-4xl text-4xl font-bold leading-[1.08] sm:text-5xl lg:text-6xl">
            Kết nối ứng viên và nhà tuyển dụng hàng đầu
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-white/85 sm:text-lg">
            Nền tảng tuyển dụng uy tín giúp bạn tìm kiếm công việc mơ ước hoặc
            kết nối với những nhân tài xuất sắc nhất.
          </p>

          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              to="/v2/search"
              className="inline-flex items-center gap-2 rounded-full bg-[#4F67F3] px-6 py-3 text-sm font-bold text-white shadow-xl shadow-blue-900/20 transition-transform hover:-translate-y-0.5"
            >
              <Search className="h-5 w-5" />
              Tìm việc ngay
            </Link>
            <Link
              to="/v2/search?type=cv"
              className="inline-flex items-center gap-2 rounded-full bg-white/95 px-6 py-3 text-sm font-bold text-gray-700 shadow-xl shadow-blue-900/10 transition-transform hover:-translate-y-0.5"
            >
              <Users className="h-5 w-5" />
              Tìm ứng viên
            </Link>
            <Link
              to="/v2/matching"
              className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/10 px-6 py-3 text-sm font-bold text-white shadow-xl shadow-blue-900/10 transition-transform hover:-translate-y-0.5 hover:bg-white/20"
            >
              <ArrowRight className="h-5 w-5" />
              Matching V2
            </Link>
          </div>

          <form
            onSubmit={submitSearch}
            className="mx-auto mt-10 flex max-w-4xl flex-col gap-3 rounded-2xl bg-white p-3 shadow-2xl shadow-blue-950/20 md:flex-row"
          >
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[#0F6FD6]" />
              <input
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                className="h-12 w-full rounded-xl border border-transparent bg-white pl-12 pr-4 text-sm text-gray-800 outline-none transition-colors placeholder:text-gray-400 focus:border-[#0F6FD6]"
                placeholder="Tên công việc, vị trí..."
              />
            </div>
            <div className="relative md:w-64">
              <MapPin className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <select
                value={city}
                onChange={(event) => setCity(event.target.value)}
                className="h-12 w-full appearance-none rounded-xl border border-gray-200 bg-white pl-12 pr-4 text-sm font-medium text-gray-500 outline-none transition-colors focus:border-[#0F6FD6]"
              >
                {cityOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              className="inline-flex h-12 items-center justify-center rounded-xl bg-[#2563EB] px-8 text-sm font-bold text-white transition-colors hover:bg-[#0F6FD6]"
            >
              Tìm kiếm
            </button>
          </form>
        </div>
      </section>

      <section className="bg-[#FAFAFB] py-16">
        <SectionTitle
          title="Danh mục ngành nghề"
          subtitle="Khám phá hàng nghìn cơ hội việc làm trong các lĩnh vực hàng đầu"
        />
        <div className="mx-auto mt-10 grid max-w-6xl gap-5 px-4 sm:grid-cols-2 sm:px-6 lg:grid-cols-4 lg:px-8">
          {categories.map((category) => {
            const Icon = category.icon;
            return (
              <Link
                key={category.title}
                to={`/v2/search?q=${encodeURIComponent(category.title.split(' ')[0])}`}
                className="group rounded-lg bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg"
              >
                <div className={`mb-5 inline-flex h-11 w-11 items-center justify-center rounded-lg ${category.tone}`}>
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-gray-900">{category.title}</h3>
                <p className="mt-2 text-sm text-gray-500">{category.jobs}</p>
              </Link>
            );
          })}
        </div>
        <div className="mt-10 text-center">
          <Link
            to="/v2/search"
            className="inline-flex items-center gap-2 rounded-full border border-[#0F6FD6] px-6 py-3 text-sm font-bold text-[#0F6FD6] transition-colors hover:bg-[#0F6FD6] hover:text-white"
          >
            Xem tất cả ngành nghề
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <section className="py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="mb-9 flex items-end justify-between gap-4">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">Việc làm nổi bật</h2>
              <p className="mt-3 text-sm text-gray-500">Cơ hội việc làm tốt nhất dành cho bạn</p>
            </div>
            <Link to="/v2/search" className="hidden items-center gap-2 text-sm font-bold text-[#0F6FD6] sm:inline-flex">
              Xem tất cả
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            {featuredJobs.map((job) => (
              <article key={job.title} className="rounded-lg border border-gray-100 bg-white p-5 shadow-sm">
                <div className="mb-4 flex items-start justify-between gap-4">
                  <img src={job.image} alt={job.company} className="h-12 w-12 rounded-lg object-cover" />
                  <Bookmark className="h-5 w-5 text-gray-300" />
                </div>
                <h3 className="text-base font-bold text-gray-900">{job.title}</h3>
                <p className="mt-2 text-sm text-gray-500">{job.company}</p>
                <div className="mt-4 flex flex-wrap items-center gap-4 text-sm">
                  <span className="rounded-md bg-emerald-50 px-3 py-1 font-bold text-[#00A86B]">{job.salary}</span>
                  <span className="inline-flex items-center gap-1 text-gray-500">
                    <MapPin className="h-4 w-4" />
                    {job.location}
                  </span>
                </div>
                <Link
                  to="/login"
                  className="mt-5 inline-flex h-11 w-full items-center justify-center rounded-md bg-blue-50 text-sm font-bold text-[#0F6FD6] transition-colors hover:bg-[#0F6FD6] hover:text-white"
                >
                  Ứng tuyển ngay
                </Link>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="companies" className="bg-[#FAFAFB] py-16">
        <SectionTitle
          title="Nhà tuyển dụng hàng đầu"
          subtitle="Những công ty hàng đầu đang tìm kiếm ứng viên tài năng"
        />
        <div className="mx-auto mt-10 grid max-w-6xl gap-5 px-4 sm:grid-cols-2 sm:px-6 md:grid-cols-3 lg:grid-cols-6 lg:px-8">
          {employers.map((employer) => (
            <Link
              key={employer.name}
              to="/v2/search"
              className="rounded-lg bg-white p-5 text-center shadow-sm transition-transform hover:-translate-y-1"
            >
              <img src={employer.image} alt={employer.name} className="mx-auto h-14 w-14 rounded-lg object-cover" />
              <h3 className="mt-4 font-bold text-gray-900">{employer.name}</h3>
              <span className="mt-3 inline-flex rounded-md bg-blue-50 px-2 py-1 text-xs font-semibold text-[#0F6FD6]">
                {employer.jobs}
              </span>
            </Link>
          ))}
        </div>
        <div className="mt-10 text-center">
          <Link
            to="/v2/search"
            className="inline-flex items-center justify-center rounded-full bg-[#0F6FD6] px-7 py-3 text-sm font-bold text-white shadow-xl shadow-blue-500/20 transition-transform hover:-translate-y-0.5"
          >
            Xem tất cả công ty
          </Link>
        </div>
      </section>

      <section id="blog" className="py-16">
        <SectionTitle
          title="Phản hồi từ người dùng"
          subtitle="Câu chuyện thành công từ những người đã tìm được việc làm lý tưởng"
        />
        <div className="mx-auto mt-10 grid max-w-6xl gap-7 px-4 sm:px-6 lg:grid-cols-3 lg:px-8">
          {testimonials.map((item) => (
            <article key={item.name} className="rounded-lg border border-gray-100 bg-white p-7 shadow-sm">
              <Quote className="h-10 w-10 fill-blue-50 text-blue-50" />
              <p className="mt-5 min-h-[112px] text-base italic leading-7 text-gray-600">"{item.quote}"</p>
              <div className="mt-6 flex items-center gap-4 border-t border-gray-100 pt-6">
                <img src={item.image} alt={item.name} className="h-11 w-11 rounded-full object-cover" />
                <div>
                  <h3 className="font-bold text-gray-900">{item.name}</h3>
                  <p className="text-xs text-gray-500">{item.title}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="relative overflow-hidden bg-gradient-to-br from-[#2868E8] via-[#168FB0] to-[#13B56C] px-4 py-16 text-center text-white sm:px-6 lg:px-8">
        <div className="absolute left-[-80px] top-12 h-60 w-60 rounded-full bg-white/10" />
        <div className="absolute right-[-100px] top-[-70px] h-72 w-72 rounded-full bg-white/10" />
        <div className="relative mx-auto max-w-4xl">
          <h2 className="text-3xl font-bold leading-tight sm:text-4xl">
            Khám phá hàng nghìn cơ hội việc làm ngay hôm nay
          </h2>
          <p className="mt-5 text-white/85">
            Tham gia cùng hơn 500,000 ứng viên và 10,000 doanh nghiệp đã tin tưởng JobConnect
          </p>
          <div className="mt-9 flex flex-col justify-center gap-4 sm:flex-row">
            <Link to="/v2/search" className="rounded-md bg-white px-7 py-3 text-sm font-bold text-[#0F6FD6]">
              Bắt đầu tìm việc
            </Link>
            <Link to="/register" className="rounded-md border-2 border-white px-7 py-3 text-sm font-bold text-white">
              Đăng tin tuyển dụng
            </Link>
          </div>
        </div>
      </section>

      <button
        type="button"
        aria-label="Chat"
        className="fixed bottom-6 right-6 z-40 inline-flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-[#0F6FD6] to-[#00A86B] text-white shadow-xl"
      >
        <MessageCircle className="h-6 w-6" />
      </button>
    </div>
  );
};

const SectionTitle: React.FC<{ title: string; subtitle: string }> = ({ title, subtitle }) => (
  <div className="mx-auto max-w-2xl px-4 text-center sm:px-6">
    <div className="mx-auto mb-4 h-1 w-16 rounded-full" style={{ background: `linear-gradient(90deg, ${PRIMARY_BLUE}, ${PRIMARY_GREEN})` }} />
    <h2 className="text-3xl font-bold text-gray-900">{title}</h2>
    <p className="mt-4 text-sm text-gray-500 sm:text-base">{subtitle}</p>
  </div>
);

export default Home;
