import React from 'react';
import { Search, Users } from 'lucide-react';

interface ActionButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  onClick?: () => void;
  className?: string;
}

/**
 * Primary action button for finding jobs.
 * Gradient background, prominent shadow, and lift effect on hover.
 */
export const FindJobsButton: React.FC<ActionButtonProps> = ({ onClick, className = '', ...props }) => {
  return (
    <button
      onClick={onClick}
      className={`
        group relative flex items-center justify-center gap-2 px-5 py-2.5 rounded-full font-bold text-white text-sm
        bg-gradient-to-r from-[#0A65CC] to-[#00B14F]
        shadow-md hover:shadow-2xl hover:shadow-blue-500/20
        transition-all duration-200 ease-in-out
        transform motion-safe:hover:scale-105 motion-safe:hover:-translate-y-0.5
        focus:outline-none focus-visible:ring-4 focus-visible:ring-[#0A65CC]/20
        active:scale-100 active:translate-y-0
        min-h-[44px] select-none
        ${className}
      `}
      aria-label="Tìm việc"
      {...props}
    >
      <Search 
        className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" 
        strokeWidth={2.5} 
      />
      <span>Tìm việc</span>
      {/* Subtle sheen overlay for extra polish */}
      <div className="absolute inset-0 rounded-full bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
    </button>
  );
};

/**
 * Secondary action button for finding candidates.
 * Outline style, subtle shadow, and lift effect on hover.
 */
export const FindCandidatesButton: React.FC<ActionButtonProps> = ({ onClick, className = '', ...props }) => {
  return (
    <button
      onClick={onClick}
      className={`
        group relative flex items-center justify-center gap-2 px-5 py-2.5 rounded-full font-bold text-gray-700 text-sm
        bg-white border border-gray-200
        shadow-sm hover:shadow-lg hover:border-blue-200 hover:text-[#0A65CC]
        transition-all duration-200 ease-in-out
        transform motion-safe:hover:scale-105 motion-safe:hover:-translate-y-0.5
        focus:outline-none focus-visible:ring-4 focus-visible:ring-[#0A65CC]/10
        active:scale-100 active:translate-y-0
        min-h-[44px] select-none
        ${className}
      `}
      aria-label="Tìm ứng viên"
      {...props}
    >
      <Users 
        className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" 
        strokeWidth={2.5} 
      />
      <span>Tìm ứng viên</span>
    </button>
  );
};
