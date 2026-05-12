import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Briefcase, Search, Sparkles } from 'lucide-react';

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold transition-colors',
    isActive
      ? 'bg-blue-50 text-[#0A65CC]'
      : 'text-gray-600 hover:bg-gray-50 hover:text-[#0A65CC]',
  ].join(' ');

const Header: React.FC = () => (
  <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/90 backdrop-blur-sm">
    <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
      <Link to="/v2/search" className="flex items-center gap-3 group">
        <div className="rounded-xl bg-gradient-to-br from-[#0A65CC] to-[#00B14F] p-2.5 shadow-sm transition-transform duration-300 group-hover:scale-105">
          <Briefcase className="h-7 w-7 text-white" strokeWidth={2.5} />
        </div>
        <span className="text-2xl font-bold tracking-tight">
          <span className="text-[#0A65CC]">Job</span>
          <span className="text-[#00B14F]">Connect</span>
        </span>
      </Link>

      <nav className="flex items-center gap-2">
        <NavLink to="/v2/search" className={navLinkClass}>
          <Search className="h-4 w-4" />
          Search
        </NavLink>
        <NavLink to="/v2/matching" className={navLinkClass}>
          <Sparkles className="h-4 w-4" />
          Matching V2
        </NavLink>
      </nav>
    </div>
  </header>
);

export default Header;
