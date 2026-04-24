import React, { useState } from 'react';
import { FilterGroup } from '../../types';
import { X, ChevronDown, ChevronUp, Filter } from 'lucide-react';

interface FiltersPanelProps {
  groups: FilterGroup[];
  selectedFilters: Record<string, string[]>;
  onFilterChange: (groupId: string, value: string) => void;
  onClearAll: () => void;
  isOpen: boolean;
  onClose: () => void;
}

interface FilterGroupItemProps {
  group: FilterGroup;
  selectedValues: string[];
  onChange: (val: string) => void;
}

// Sub-component for individual group
const FilterGroupItem: React.FC<FilterGroupItemProps> = ({ group, selectedValues, onChange }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="border-b border-gray-100 pb-4 last:border-0">
      <button 
        className="flex items-center justify-between w-full py-2 text-sm font-bold text-gray-900 mb-2"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {group.title}
        {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
      </button>
      
      {isExpanded && (
        <div className="space-y-2.5">
          {group.options.map(option => (
            <label key={option.value} className="flex items-center cursor-pointer group">
              <input 
                type="checkbox" 
                className="w-4 h-4 rounded border-gray-300 bg-white text-[#0A65CC] focus:ring-[#0A65CC] accent-[#0A65CC]"
                style={{ colorScheme: 'light' }}
                checked={selectedValues.includes(option.value)}
                onChange={() => onChange(option.value)}
              />
              <span className="ml-2.5 text-sm text-gray-600 group-hover:text-gray-900">{option.label}</span>
              {option.count !== undefined && (
                <span className="ml-auto text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded-full">{option.count}</span>
              )}
            </label>
          ))}
        </div>
      )}
    </div>
  );
};

const FiltersPanel: React.FC<FiltersPanelProps> = ({ 
  groups, selectedFilters, onFilterChange, onClearAll, isOpen, onClose 
}) => {
  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-72 bg-white text-gray-900 shadow-xl transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:shadow-none lg:w-64 lg:block overflow-y-auto
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-5">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold flex items-center gap-2 text-gray-900">
              <Filter className="w-5 h-5" /> Bộ lọc
            </h2>
            <button 
              onClick={onClose} 
              className="lg:hidden p-1 hover:bg-gray-100 rounded text-gray-500"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-6">
             {/* Render Filter Groups */}
             {groups.map(group => (
               <FilterGroupItem 
                 key={group.id} 
                 group={group} 
                 selectedValues={selectedFilters[group.id] || []}
                 onChange={(val) => onFilterChange(group.id, val)}
               />
             ))}
          </div>

          <button 
            onClick={onClearAll}
            className="w-full mt-8 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 bg-white rounded-lg hover:bg-gray-50 transition-colors"
          >
            Xóa tất cả lọc
          </button>
        </div>
      </aside>
    </>
  );
};

export default FiltersPanel;