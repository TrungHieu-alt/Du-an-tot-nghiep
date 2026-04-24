
import React from 'react';
import { Search, Users } from 'lucide-react';

interface PageButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  onClick?: () => void;
  className?: string;
}

/**
 * Primary "Tìm việc" button for the Hero/Page content.
 * Visuals: Gradient bg, full rounded, gentle lift on hover.
 */
export const PageFindJobsButton: React.FC<PageButtonProps> = ({ onClick, className = '', ...props }) => {
  return (
    <button
      onClick={onClick}
      className={`
        group relative flex items-center justify-center gap-2 px-5 py-2.5 rounded-full font-semibold text-white text-base
        bg-gradient-to-r from-blue-600 to-indigo-500
        shadow-md hover:shadow-2xl hover:shadow-blue-500/30
        transition-all duration-200 ease-out
        transform motion-safe:hover:scale-105 motion-safe:hover:-translate-y-0.5
        focus:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200
        active:scale-100 active:translate-y-0
        ${className}
      `}
      aria-label="Tìm việc ngay"
      {...props}
    >
      <Search className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
      <span>Tìm việc ngay</span>
    </button>
  );
};

/**
 * Secondary "Tìm ứng viên" button for the Hero/Page content.
 * Visuals: Ghost/Outline style, rounded-full.
 */
export const PageFindCandidatesButton: React.FC<PageButtonProps> = ({ onClick, className = '', ...props }) => {
  return (
    <button
      onClick={onClick}
      className={`
        group relative flex items-center justify-center gap-2 px-4 py-2 rounded-full font-semibold text-base
        bg-white/90 border border-slate-200 text-slate-700
        shadow-sm hover:shadow-lg hover:bg-white
        transition-all duration-200 ease-out
        transform motion-safe:hover:scale-105 motion-safe:hover:-translate-y-0.5
        focus:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200
        active:scale-100 active:translate-y-0
        ${className}
      `}
      aria-label="Tìm ứng viên"
      {...props}
    >
      <Users className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
      <span>Tìm ứng viên</span>
    </button>
  );
};
