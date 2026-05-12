import React, { useEffect, useRef, useState } from 'react';
import { MapPin, ChevronDown, Check, X } from 'lucide-react';
import type { LocationV2 } from '../../types';
import { LOCATION_OPTIONS, formatLocationV2 } from './v2-format';

/**
 * V2 location dropdown — typed, enum-only.
 *
 * Emits LocationV2 enum slugs instead of free-form strings, so callers can
 * pass the value straight to V2 search/match endpoints.
 *
 * Empty value `''` represents "no filter / all locations".
 */

export type V2LocationValue = LocationV2 | '';

interface V2LocationSelectProps {
  value: V2LocationValue;
  onChange: (next: V2LocationValue) => void;
  placeholder?: string;
  className?: string;
  /** Optional: hide the "Tất cả khu vực" reset row (use when caller wants
   *  to force a non-empty selection). Defaults to true. */
  showClear?: boolean;
}

const V2LocationSelect: React.FC<V2LocationSelectProps> = ({
  value,
  onChange,
  placeholder = 'Tỉnh/Thành phố',
  className = '',
  showClear = true,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (next: V2LocationValue) => {
    onChange(next);
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

  const displayLabel = value ? formatLocationV2(value as LocationV2) : '';

  return (
    <div
      ref={containerRef}
      className={`relative w-full ${className}`}
      onKeyDown={handleKeyDown}
    >
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setIsOpen((o) => !o)}
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
          className={`w-5 h-5 flex-shrink-0 transition-colors ${
            value || isOpen ? 'text-[#0A65CC]' : 'text-gray-400 group-hover:text-[#0A65CC]'
          }`}
        />
        <span
          className={`flex-1 truncate text-[15px] font-medium ${
            value ? 'text-gray-900' : 'text-gray-400'
          }`}
        >
          {displayLabel || placeholder}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-[#0A65CC]' : ''
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 z-50 animate-in fade-in zoom-in-95 duration-100">
          <ul
            className="bg-white rounded-xl border border-gray-100 shadow-xl py-1.5 overflow-hidden"
            role="listbox"
          >
            {showClear && (
              <li role="option" aria-selected={value === ''}>
                <button
                  type="button"
                  onClick={() => handleSelect('')}
                  className="w-full text-left px-4 py-2.5 text-sm font-medium text-gray-500 hover:bg-blue-50 hover:text-[#0A65CC] flex items-center justify-between transition-colors focus:bg-blue-50 focus:outline-none"
                >
                  <span className="flex items-center gap-2">
                    <X className="w-4 h-4" /> Tất cả khu vực
                  </span>
                  {value === '' && <Check className="w-4 h-4 text-[#0A65CC]" />}
                </button>
              </li>
            )}
            {LOCATION_OPTIONS.map((opt) => (
              <li key={opt.value} role="option" aria-selected={value === opt.value}>
                <button
                  type="button"
                  onClick={() => handleSelect(opt.value)}
                  className="w-full text-left px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-blue-50 hover:text-[#0A65CC] flex items-center justify-between transition-colors focus:bg-blue-50 focus:outline-none"
                >
                  {opt.label}
                  {value === opt.value && <Check className="w-4 h-4 text-[#0A65CC]" />}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default V2LocationSelect;
