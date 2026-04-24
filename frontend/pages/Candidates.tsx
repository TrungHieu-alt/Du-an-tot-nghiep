
import React, { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useCandidatesSearch } from '../hooks/useCandidatesSearch';
import { SlidersHorizontal, Filter, Info, UserCircle, Sparkles, ChevronDown } from 'lucide-react';
import { ViewMode, FilterGroup } from '../types';
import { useAuth } from '../contexts/AuthContext';

import SearchBar from '../components/search/SearchBar';
import FiltersPanel from '../components/search/FiltersPanel';
import SortAndViewControls from '../components/search/SortAndViewControls';
import CandidateCardWithMatch from '../components/CandidateCardWithMatch';
import Pagination from '../components/common/Pagination';
import { SkeletonList } from '../components/common/SkeletonLoader';

const CANDIDATE_FILTERS: FilterGroup[] = [
  {
    id: 'exp',
    title: 'Kinh nghiệm',
    options: [
      { label: 'Intern / Fresher', value: 'Intern' },
      { label: 'Junior (1-2 năm)', value: 'Junior' },
      { label: 'Mid-Level (2-4 năm)', value: 'Mid-Level' },
      { label: 'Senior (5+ năm)', value: 'Senior' }
    ]
  },
  {
    id: 'availability',
    title: 'Thời gian sẵn sàng',
    options: [
      { label: 'Sẵn sàng ngay', value: 'Immediate' },
      { label: 'Trong 2 tuần', value: '2 weeks' },
      { label: 'Trong 1 tháng', value: '1 month' }
    ]
  }
];

const Candidates: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const { isAuthenticated } = useAuth();
  const [searchParams] = useSearchParams();
  const isManual = searchParams.get('manual') === 'true';

  const {
    data, loading, meta, state, contextId, contextOptions,
    handleQueryChange, handleLocationChange, handleSortChange,
    handlePageChange, handleFilterChange, handleClearFilters, handleClearContext, 
    handleReqChange, // Used directly from hook
    refresh
  } = useCandidatesSearch();

  const isMatchMode = !!contextId;

  return (
    <div className="bg-[#F5F7FC] min-h-screen font-sans pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Top Search Bar with Requirement Switcher */}
        <SearchBar 
          query={state.q}
          location={state.location}
          onQueryChange={handleQueryChange}
          onLocationChange={handleLocationChange}
          onSearch={refresh}
          
          // Context Props
          contextOptions={contextOptions}
          selectedContextId={contextId}
          onContextChange={handleReqChange}
          onContextClear={handleClearContext}
          
          placeholder="Tìm kiếm ứng viên theo tên, kỹ năng..."
        />

        {/* Manual Mode Banner */}
        {((isManual && !isAuthenticated) || (!isAuthenticated && !contextId)) && (
          <div className="bg-white border-l-4 border-blue-500 shadow-sm rounded-r-xl p-4 mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-fade-in">
             <div className="flex items-start gap-3">
                <UserCircle className="w-6 h-6 text-blue-500 mt-1 sm:mt-0" />
                <div>
                  <h3 className="text-sm font-bold text-gray-900">Đăng nhập để tìm ứng viên hiệu quả hơn</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Bạn đang tìm kiếm thủ công. <Link to="/login" className="text-blue-600 hover:underline font-medium">Đăng nhập ngay</Link> để sử dụng tính năng <strong>Tự động ghép nối (AI Matching)</strong> và tìm ứng viên phù hợp nhất.
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
        
        {isAuthenticated && isManual && !contextId && (
           <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-8 flex items-start gap-3 animate-fade-in">
             <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
             <div>
               <h3 className="text-sm font-bold text-blue-800 mb-1">Chế độ tìm kiếm thủ công</h3>
               <p className="text-sm text-blue-600">
                 Để sử dụng tính năng <strong>Tự động ghép nối</strong>, vui lòng chọn một yêu cầu tuyển dụng từ thanh tìm kiếm.
               </p>
             </div>
           </div>
        )}

        <div className="flex flex-col lg:flex-row gap-8">
          
          {/* Filters Sidebar */}
          <FiltersPanel 
            isOpen={isFiltersOpen}
            onClose={() => setIsFiltersOpen(false)}
            groups={CANDIDATE_FILTERS}
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

            <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
               {/* Sort Controls - Custom for Candidates */}
               <div className="flex items-center gap-3 w-full sm:w-auto">
                 <p className="text-gray-500 font-medium text-sm whitespace-nowrap hidden sm:block">
                    Tìm thấy <span className="text-gray-900 font-bold">{meta.total}</span> ứng viên
                 </p>
                 
                 <div className="relative w-full sm:w-auto">
                    {isMatchMode && (
                      <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none z-10">
                        <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                      </div>
                    )}
                    <select
                        value={isMatchMode ? 'relevance' : state.sort}
                        onChange={(e) => handleSortChange(e.target.value as any)}
                        disabled={isMatchMode}
                        className={`w-full sm:min-w-[200px] appearance-none pr-10 py-2.5 bg-white border border-gray-200 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 cursor-pointer
                            ${isMatchMode 
                              ? 'pl-9 text-blue-700 border-blue-200 bg-blue-50/50 cursor-default' 
                              : 'pl-4 text-gray-900'
                            }
                        `}
                    >
                        {isMatchMode ? (
                            <option value="relevance">Sắp xếp: Độ phù hợp nhất</option>
                        ) : (
                            <>
                                <option value="newest">Mới nhất</option>
                                <option value="oldest">Cũ nhất</option>
                                <option value="exp_high">Kinh nghiệm: Cao đến Thấp</option>
                                <option value="exp_low">Kinh nghiệm: Thấp đến Cao</option>
                            </>
                        )}
                    </select>
                    <ChevronDown className={`absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none ${isMatchMode ? 'text-blue-400' : 'text-gray-400'}`} />
                 </div>
               </div>
               
               {/* View Toggle ONLY (Sort and Count hidden) */}
               <SortAndViewControls 
                 sort={state.sort} 
                 onSortChange={() => {}} 
                 viewMode={viewMode} 
                 onViewModeChange={setViewMode} 
                 resultCount={meta.total}
                 itemLabel="ứng viên"
                 hideSort={true}
                 hideCount={true}
               />
            </div>

            {/* Results Grid/List */}
            {loading ? (
              <SkeletonList count={4} />
            ) : data.length > 0 ? (
              <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : 'space-y-4'}>
                {data.map(candidate => (
                  <CandidateCardWithMatch key={candidate.id} candidate={candidate} />
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-xl p-12 text-center border border-gray-100 shadow-sm">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Filter className="w-8 h-8 text-gray-300" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Không tìm thấy ứng viên</h3>
                <p className="text-gray-500">Thử thay đổi từ khóa, bộ lọc hoặc yêu cầu tuyển dụng.</p>
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

export default Candidates;
