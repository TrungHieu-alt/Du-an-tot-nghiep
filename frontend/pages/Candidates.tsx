
import React, { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useCandidatesSearch } from '../hooks/useCandidatesSearch';
import { SlidersHorizontal, Filter, Info, UserCircle } from 'lucide-react';
import { ViewMode, FilterGroup } from '../types';
import { useAuth } from '../contexts/AuthContext';

import V2DeprecatedV1Banner from '../components/v2/V2DeprecatedV1Banner';
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
  const formatLastMatchedAt = (value?: string) => {
    if (!value) return '';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return '';
    return d.toLocaleString('vi-VN');
  };
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

        {/* Deprecation banner — Home no longer routes here; this hint helps
            users who arrived via stale bookmarks or the legacy Header buttons. */}
        <V2DeprecatedV1Banner type="cv" />

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

            <SortAndViewControls 
              sort={state.sort} 
              onSortChange={handleSortChange} 
              viewMode={viewMode} 
              onViewModeChange={setViewMode} 
              resultCount={meta.total}
              itemLabel="ứng viên"
              isMatchMode={isMatchMode}
              sortOptions={[
                { value: 'newest', label: 'Mới nhất' },
                { value: 'oldest', label: 'Cũ nhất' },
                { value: 'exp_high', label: 'Kinh nghiệm: Cao đến Thấp' },
                { value: 'exp_low', label: 'Kinh nghiệm: Thấp đến Cao' },
              ]}
            />
            {isMatchMode && (
              <div className="mb-4 flex items-center justify-between gap-3">
                <p className="text-xs text-gray-500">
                  {meta.lastMatchedAt ? `Last matched: ${formatLastMatchedAt(meta.lastMatchedAt)}` : ''}
                </p>
                <button
                  onClick={() => refresh({ forceRematch: true })}
                  disabled={loading}
                  className="px-3 py-2 text-sm font-semibold rounded-lg border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  Re-match
                </button>
              </div>
            )}

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
