
import React, { useState, useMemo, useEffect } from 'react';
import { useSearchParams, Link, useLocation } from 'react-router-dom';
import { useSearchResults } from '../hooks/useSearchResults';
import { searchJobsApi } from '../utils/mockApi';
import { MOCK_CVS } from '../utils/matching';
import { Filter, SlidersHorizontal, Info, UserCircle } from 'lucide-react';
import { ViewMode, FilterGroup, UserCV, JobWithMatch } from '../types';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';

import SearchBar from '../components/search/SearchBar';
import FiltersPanel from '../components/search/FiltersPanel';
import SortAndViewControls from '../components/search/SortAndViewControls';
import JobCardWithMatch from '../components/JobCardWithMatch';
import Pagination from '../components/common/Pagination';
import { SkeletonList } from '../components/common/SkeletonLoader';

const JOB_FILTERS: FilterGroup[] = [
  {
    id: 'level',
    title: 'Cấp bậc',
    options: [
      { label: 'Intern / Fresher', value: 'Intern' },
      { label: 'Junior', value: 'Junior' },
      { label: 'Mid-Level', value: 'Mid-Level' },
      { label: 'Senior', value: 'Senior' },
      { label: 'Director / Manager', value: 'Director' }
    ]
  },
  {
    id: 'type',
    title: 'Loại hình công việc',
    options: [
      { label: 'Full-time', value: 'Full-time' },
      { label: 'Part-time', value: 'Part-time' },
      { label: 'Remote', value: 'Remote' },
      { label: 'Freelance', value: 'Freelance' }
    ]
  }
];

const Jobs: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const isManual = searchParams.get('manual') === 'true';

  const [userCvs, setUserCvs] = useState<UserCV[]>([]);

  // Debugging: Check what state we received from navigation
  useEffect(() => {
    if (location.state?.cvs) {
      console.log("JobsPage: Received CVs from state:", location.state.cvs);
    }
  }, [location.state]);

  // Fetch real CVs if authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const fetchCvs = async () => {
        try {
          const res = await api.get('/cv/user/me');
          const data = res.data;
          
          // Map backend response to UserCV
          const mapped: UserCV[] = Array.isArray(data) ? data.map((item: any) => ({
             id: item._id,
             name: item.fullname || "Hồ sơ không tên",
             title: item.headline || item.targetRole || "Chưa có tiêu đề",
             // Map skills from object array {name, level, ...} to string array
             skills: Array.isArray(item.skills) ? item.skills.map((s: any) => s.name) : [],
             experienceLevel: "Mid-Level", 
             location: item.location?.city || "",
             lastUpdated: item.updatedAt ? new Date(item.updatedAt).toLocaleDateString('vi-VN') : "",
             ownerId: item.createdBy || item.userId
          })) : [];
          setUserCvs(mapped);
        } catch (e) {
          console.error("Failed to fetch user CVs", e);
        }
      };
      fetchCvs();
    }
  }, [isAuthenticated]);

  // Get CVs passed from CvSelectorModal (if skip/manual flow)
  const passedCvs = (location.state?.cvs || []) as UserCV[];

  // Determine the source of CVs: API User CVs > Passed State > Mock Data
  const effectiveCvs = useMemo(() => {
    if (userCvs.length > 0) return userCvs;
    if (passedCvs.length > 0) return passedCvs;
    return MOCK_CVS;
  }, [userCvs, passedCvs]);

  // Prepare context options for the dropdown
  const cvOptions = useMemo(() => {
    return effectiveCvs.map(c => ({ id: c.id, label: c.name }));
  }, [effectiveCvs]);

  const {
    data, loading, meta, state, contextId,
    handleQueryChange, handleLocationChange, handleSortChange,
    handlePageChange, handleFilterChange, handleClearFilters, handleClearContext, refresh
  } = useSearchResults({
    apiCall: searchJobsApi,
    contextParamKey: 'cv',
    initialSort: 'newest'
  });

  // Determine selected CV object for label or matching logic
  const selectedCv = useMemo(() => {
    return effectiveCvs.find(c => c.id === contextId);
  }, [contextId, effectiveCvs]);

  const handleCvChange = (newCvId: string) => {
    setSearchParams(prev => {
      const p = new URLSearchParams(prev);
      p.set('cv', newCvId);
      p.delete('manual'); // Switch from manual to matching mode
      p.set('page', '1');
      p.set('sort', 'relevance'); // Force sort to relevance when picking a CV
      return p;
    });
  };

  return (
    <div className="bg-[#F5F7FC] min-h-screen font-sans pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Top Search Bar */}
        <SearchBar 
          query={state.q}
          location={state.location}
          onQueryChange={handleQueryChange}
          onLocationChange={handleLocationChange}
          onSearch={refresh}
          
          // Context Props
          contextOptions={cvOptions}
          selectedContextId={contextId}
          onContextChange={handleCvChange}
          contextLabel={selectedCv ? `Theo CV: ${selectedCv.name}` : undefined}
          onContextClear={handleClearContext}
          
          placeholder="Tìm kiếm việc làm, kỹ năng, công ty..."
        />

        {/* Auth / Manual Mode Banner */}
        {((isManual && !isAuthenticated) || (!isAuthenticated && !contextId)) && (
          <div className="bg-white border-l-4 border-blue-500 shadow-sm rounded-r-xl p-4 mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-fade-in">
             <div className="flex items-start gap-3">
                <UserCircle className="w-6 h-6 text-blue-500 mt-1 sm:mt-0" />
                <div>
                  <h3 className="text-sm font-bold text-gray-900">Đăng nhập để tìm việc hiệu quả hơn</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Bạn đang tìm kiếm thủ công. <Link to="/login" className="text-blue-600 hover:underline font-medium">Đăng nhập ngay</Link> để sử dụng tính năng <strong>Phù hợp với CV</strong> và nhận gợi ý việc làm tốt nhất.
                  </p>
                </div>
             </div>
             <Link 
               to="/login"
               className="shrink-0 px-4 py-2 bg-blue-50 text-blue-700 font-semibold text-sm rounded-lg hover:bg-blue-100 transition-colors whitespace-nowrap"
             >
               Đăng nhập ngay
             </Link>
          </div>
        )}

        <div className="flex flex-col lg:flex-row gap-8">
          
          {/* Filters Sidebar */}
          <FiltersPanel 
            isOpen={isFiltersOpen}
            onClose={() => setIsFiltersOpen(false)}
            groups={JOB_FILTERS}
            selectedFilters={state.filters}
            onFilterChange={handleFilterChange}
            onClearAll={handleClearFilters}
          />

          {/* Main Content */}
          <div className="flex-1">
            <div className="flex justify-between items-center lg:hidden mb-4">
               <button 
                 onClick={() => setIsFiltersOpen(true)}
                 className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-gray-200 text-sm font-semibold shadow-sm"
               >
                 <SlidersHorizontal className="w-4 h-4" /> Bộ lọc
               </button>
            </div>

            <SortAndViewControls 
              sort={state.sort} 
              onSortChange={handleSortChange} 
              viewMode={viewMode} 
              onViewModeChange={setViewMode} 
              resultCount={meta.total}
              itemLabel="công việc"
              isMatchMode={!!contextId} // Lock to relevance if CV selected
            />

            {loading ? (
              <SkeletonList count={5} />
            ) : data.length > 0 ? (
              <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-6' : 'space-y-4'}>
                {data.map(job => (
                  <JobCardWithMatch 
                    key={job.id} 
                    job={job} 
                    layout={viewMode}
                    // onClick prop removed to allow default navigation to Job Detail Page
                  />
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-xl p-12 text-center border border-gray-100 shadow-sm">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Filter className="w-8 h-8 text-gray-300" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Không tìm thấy kết quả</h3>
                <p className="text-gray-500">Thử thay đổi từ khóa hoặc bộ lọc của bạn</p>
                <button onClick={handleClearFilters} className="mt-4 text-[#0A65CC] font-semibold hover:underline">
                  Xóa bộ lọc
                </button>
              </div>
            )}

            <Pagination 
              currentPage={meta.page} 
              totalPages={meta.totalPages} 
              onPageChange={handlePageChange} 
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Jobs;
