import React, { useState, useRef, useEffect } from 'react';
import { MapPin, ChevronDown, Check } from 'lucide-react';

const OPTIONS = ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Remote"];

interface LocationSelectProps {
  value?: string;
  onChange?: (value: string) => void;
}

const LocationSelect: React.FC<LocationSelectProps> = ({ value, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [internalSelected, setInternalSelected] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // Use prop value if provided, otherwise fallback to internal state
  const selected = value !== undefined ? value : internalSelected;

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (option: string) => {
    if (onChange) {
      onChange(option);
    } else {
      setInternalSelected(option);
    }
    setIsOpen(false);
    triggerRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      triggerRef.current?.focus();
    } else if (e.key === 'ArrowDown' && !isOpen) {
      setIsOpen(true);
    }
  };

  return (
    <div 
      className="relative w-full" 
      ref={containerRef}
      onKeyDown={handleKeyDown}
    >
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-full flex items-center gap-2 pl-4 pr-4 py-3 
          bg-white border border-gray-200 rounded-full shadow-sm 
          hover:border-[#0A65CC] hover:shadow-md hover:text-[#0A65CC]
          focus:outline-none focus:ring-2 focus:ring-[#0A65CC]/20 focus:border-[#0A65CC]
          transition-all duration-200 group text-left
          ${isOpen ? 'border-[#0A65CC] ring-2 ring-[#0A65CC]/20' : ''}
        `}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Chọn Tỉnh/Thành phố"
      >
        <MapPin 
          className={`w-5 h-5 flex-shrink-0 transition-colors ${selected || isOpen ? 'text-[#0A65CC]' : 'text-gray-400 group-hover:text-[#0A65CC]'}`} 
        />
        <span className={`flex-1 truncate text-[15px] font-medium ${selected ? 'text-gray-900' : 'text-gray-400'}`}>
          {selected || "Tỉnh/Thành phố"}
        </span>
        <ChevronDown 
          className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180 text-[#0A65CC]' : ''}`} 
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 z-50 animate-in fade-in zoom-in-95 duration-100">
          <ul 
            className="bg-white rounded-xl border border-gray-100 shadow-xl py-1.5 overflow-hidden"
            role="listbox"
          >
            {OPTIONS.map((option, index) => (
              <li key={option} role="option" aria-selected={selected === option}>
                <button
                  type="button"
                  onClick={() => handleSelect(option)}
                  className="w-full text-left px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-blue-50 hover:text-[#0A65CC] flex items-center justify-between transition-colors focus:bg-blue-50 focus:outline-none"
                  autoFocus={index === 0} // Basic focus management
                >
                  {option}
                  {selected === option && <Check className="w-4 h-4 text-[#0A65CC]" />}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default LocationSelect;