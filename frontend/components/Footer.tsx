import React from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, Search, Sparkles } from 'lucide-react';

const Footer: React.FC = () => (
  <footer className="border-t border-gray-100 bg-white py-8 text-sm text-gray-500">
    <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-gradient-to-br from-[#0A65CC] to-[#00B14F] p-2">
          <Briefcase className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="font-bold text-gray-900">JobConnect V2</p>
          <p>PostgreSQL + pgvector matching prototype</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Link to="/v2/search" className="inline-flex items-center gap-1.5 hover:text-[#0A65CC]">
          <Search className="h-4 w-4" />
          Search catalog
        </Link>
        <Link to="/v2/matching" className="inline-flex items-center gap-1.5 hover:text-[#0A65CC]">
          <Sparkles className="h-4 w-4" />
          Run matching
        </Link>
      </div>
    </div>
  </footer>
);

export default Footer;
