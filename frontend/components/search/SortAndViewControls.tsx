
import React from 'react';
import { LayoutGrid, List as ListIcon, ChevronDown, Sparkles } from 'lucide-react';
import { SortOption, ViewMode } from '../../types';

interface ControlsProps {
  sort: SortOption;
  onSortChange: (sort: SortOption) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  resultCount: number;
  itemLabel?: string;
  showRelevance?: boolean; // Deprecated in favor of isMatchMode logic, but kept for interface compat if needed elsewhere
  isMatchMode?: boolean; // New prop to control specific behavior
  hideSort?: boolean;
  hideCount?: boolean;
}

const SortAndViewControls: React.FC<ControlsProps> = ({ 
  sort, onSortChange, viewMode, onViewModeChange, resultCount, itemLabel = 'kết quả', 
  isMatchMode = false,
  hideSort = false,
  hideCount = false
}) => {
  return (
    <div className={`flex flex-col sm:flex-row items-center mb-6 gap-4 ${hideCount ? 'justify-end' : 'justify-between'}`}>
      {!hideCount && (
        <p className="text-gray-500 font-medium self-start sm:self-center">
          Tìm thấy <span className="text-gray-900 font-bold">{resultCount}</span> {itemLabel}
        </p>
      )}

      <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
        {!hideSort && (
          <div className="relative flex-1 sm:flex-none">
            {isMatchMode && (
              <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none z-10">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
              </div>
            )}
            <select
              value={isMatchMode ? 'relevance' : sort}
              onChange={(e) => onSortChange(e.target.value as SortOption)}
              disabled={isMatchMode}
              className={`w-full sm:w-56 appearance-none pr-10 py-2.5 bg-white border border-gray-200 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 cursor-pointer
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
                  <option value="salary_high">Lương cao nhất</option>
                  <option value="salary_low">Lương thấp nhất</option>
                </>
              )}
            </select>
            <ChevronDown className={`absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none ${isMatchMode ? 'text-blue-400' : 'text-gray-400'}`} />
          </div>
        )}

        <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-lg shrink-0">
          <button
            onClick={() => onViewModeChange('list')}
            className={`p-2 rounded-md transition-all ${viewMode === 'list' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
            aria-label="List View"
          >
            <ListIcon className="w-5 h-5" />
          </button>
          <button
            onClick={() => onViewModeChange('grid')}
            className={`p-2 rounded-md transition-all ${viewMode === 'grid' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
            aria-label="Grid View"
          >
            <LayoutGrid className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SortAndViewControls;
