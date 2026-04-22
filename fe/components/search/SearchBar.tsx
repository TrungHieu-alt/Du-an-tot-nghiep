
import React from 'react';
import { Search, MapPin, X, ChevronDown } from 'lucide-react';

export interface ContextOption {
  id: string;
  label: string;
}

interface SearchBarProps {
  query: string;
  location: string;
  
  // Context props (Optional)
  contextLabel?: string; 
  contextOptions?: ContextOption[];
  selectedContextId?: string;
  onContextChange?: (id: string) => void;
  onContextClear?: () => void;

  onQueryChange: (val: string) => void;
  onLocationChange: (val: string) => void;
  onSearch: () => void;
  placeholder?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({
  query, location, 
  contextLabel, contextOptions, selectedContextId, onContextChange, onContextClear,
  onQueryChange, onLocationChange, onSearch, placeholder
}) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') onSearch();
  };

  return (
    <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 mb-6">
      <div className="flex flex-col md:flex-row items-center gap-4">
        
        {/* Keyword Input */}
        <div className="flex-1 w-full relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || "Tìm kiếm theo từ khóa..."}
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm text-gray-900 placeholder:text-gray-500"
          />
        </div>

        {/* Location Select */}
        <div className="w-full md:w-64 relative">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <select
            value={location}
            onChange={(e) => onLocationChange(e.target.value)}
            className="w-full pl-10 pr-8 py-2.5 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 appearance-none text-sm cursor-pointer text-gray-900"
          >
            <option value="">Tất cả địa điểm</option>
            <option value="Hà Nội">Hà Nội</option>
            <option value="Hồ Chí Minh">TP. Hồ Chí Minh</option>
            <option value="Đà Nẵng">Đà Nẵng</option>
            <option value="Remote">Remote</option>
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none border-l pl-2 border-gray-300">
             <span className="text-gray-400 text-xs">▼</span>
          </div>
        </div>

        {/* Search Button */}
        <button
          onClick={onSearch}
          className="w-full md:w-auto px-8 py-2.5 bg-[#0A65CC] text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-sm focus:ring-4 focus:ring-blue-200"
        >
          Tìm kiếm
        </button>
      </div>

      {/* Context Badge or Dropdown */}
      {(contextLabel || (contextOptions && contextOptions.length > 0)) && (
        <div className="mt-3 flex items-center gap-2 flex-wrap">
          <span className="text-sm text-gray-500">Đang lọc theo:</span>
          
          {contextOptions && onContextChange ? (
            // Context Selector Dropdown
            <div className="relative inline-block">
              <select
                value={selectedContextId || ''}
                onChange={(e) => onContextChange(e.target.value)}
                className="appearance-none bg-white text-blue-700 pl-3 pr-8 py-1.5 rounded-full text-sm font-medium border border-blue-100 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/30 max-w-[250px] truncate"
              >
                 <option value="" disabled>Chọn yêu cầu...</option>
                 {contextOptions.map(opt => (
                   <option key={opt.id} value={opt.id} className="text-gray-900">{opt.label}</option>
                 ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-blue-700 pointer-events-none" />
            </div>
          ) : (
             // Simple Badge
             <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full text-sm font-medium border border-blue-100">
               {contextLabel}
             </div>
          )}
          
          {selectedContextId && onContextClear && (
            <button 
              onClick={onContextClear}
              className="text-gray-400 hover:text-red-500 hover:bg-red-50 p-1 rounded-full transition-colors"
              title="Xóa bộ lọc (Chuyển sang tìm kiếm thủ công)"
              aria-label="Clear context"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
