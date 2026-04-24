
import React from 'react';
import { JobWithMatch } from '../types';
import { MapPin, DollarSign, Briefcase, Sparkles, Bookmark, Calendar } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface JobCardProps {
  job: JobWithMatch;
  layout?: 'grid' | 'list';
  onClick?: () => void;
}

const JobCardWithMatch: React.FC<JobCardProps> = ({ job, layout = 'list', onClick }) => {
  const hasMatch = job.match && job.match.score > 0;
  const navigate = useNavigate();
  
  // Navigate to full page details
  const navigateToDetail = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/jobs/${job.id}`);
  };

  // Wrapper click handler
  const handleCardClick = (e: React.MouseEvent) => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/jobs/${job.id}`);
    }
  };

  const handleApplyClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/jobs/${job.id}`);
  };

  // Helper to flatten multiline text to comma separated string
  const formatMatchReason = (text: string) => {
    return text.split(/\n+/).map(s => s.trim()).filter(Boolean).join(', ');
  };

  const containerClasses = `cursor-pointer transition-all duration-300 ${onClick ? 'hover:ring-2 hover:ring-[#0A65CC]/20' : ''}`;

  // Grid View
  if (layout === 'grid') {
    return (
      <div 
        onClick={handleCardClick}
        className={`group bg-white rounded-xl border border-gray-200 p-5 hover:shadow-lg relative flex flex-col h-full ${containerClasses}`}
      >
        {hasMatch && (
           <div className={`absolute top-4 right-4 text-xs font-bold px-2 py-1 rounded-full flex items-center gap-1 ${
             job.match!.score >= 80 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
           }`}>
             <Sparkles className="w-3 h-3" /> {job.match!.score}%
           </div>
        )}

        <div className="flex items-start gap-3 mb-4">
          <img src={job.logo} alt={job.company} className="w-12 h-12 rounded-lg object-cover border border-gray-100" />
          <div>
             <h3 
               className="font-bold text-gray-900 line-clamp-2 group-hover:text-[#0A65CC] transition-colors hover:underline"
               onClick={navigateToDetail}
             >
               {job.title}
             </h3>
             <p className="text-sm text-gray-500">{job.company}</p>
          </div>
        </div>

        <div className="space-y-2 mb-4 flex-1">
           <div className="flex items-center gap-2 text-sm text-gray-600">
             <MapPin className="w-4 h-4 text-gray-400" /> {job.location}
           </div>
           <div className="flex items-center gap-2 text-sm text-green-600 font-medium">
             <DollarSign className="w-4 h-4" /> {job.salary}
           </div>
        </div>

        {hasMatch && job.match?.reason && (
           <div className="mb-4 text-xs text-gray-600 bg-blue-50/50 p-2 rounded border border-blue-100/50 line-clamp-3">
             <span className="font-semibold text-[#0A65CC]">Phù hợp:</span> {formatMatchReason(job.match.reason)}
           </div>
        )}

        <button 
          onClick={handleApplyClick}
          className="w-full mt-auto bg-blue-50 text-[#0A65CC] hover:bg-[#0A65CC] hover:text-white font-medium py-2 rounded-lg transition-colors text-sm"
        >
          Ứng tuyển
        </button>
      </div>
    );
  }

  // List View (Default)
  return (
    <div 
      onClick={handleCardClick}
      className={`
      relative bg-white rounded-xl p-5 transition-all duration-300
      border-2 ${hasMatch && job.match!.score >= 80 ? 'border-green-400 shadow-md' : 'border-transparent border-b-gray-100 shadow-sm'}
      hover:shadow-lg ${containerClasses}
    `}>
      {hasMatch && (
        <div className="absolute top-4 right-4 z-10">
          <div className={`
            flex items-center gap-1 px-3 py-1 rounded-full font-bold text-sm
            ${job.match!.score >= 80 ? 'bg-green-100 text-green-700' : 
              job.match!.score >= 50 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'}
          `}>
            <Sparkles className="w-3.5 h-3.5" />
            {job.match!.score}%
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row items-start gap-4">
        <img src={job.logo} alt={job.company} className="w-14 h-14 rounded-lg object-cover border border-gray-100 flex-shrink-0" />
        
        <div className="flex-1 w-full">
          <div className="flex justify-between items-start">
             <div className={`${hasMatch ? 'pr-20' : ''}`}>
                <h3 
                  className="text-lg font-bold text-gray-900 hover:text-blue-600 transition-colors cursor-pointer mb-1 hover:underline leading-tight"
                  onClick={navigateToDetail}
                >
                  {job.title}
                </h3>
                <p className="text-gray-600 font-medium text-sm mb-2">{job.company}</p>
             </div>
          </div>
          
          {/* Compact details line with comma separation */}
          <div className="flex flex-wrap items-center text-[13px] text-gray-500 mb-2 leading-relaxed">
            <span className="flex items-center font-bold text-[#00B14F]">
              <DollarSign className="w-3.5 h-3.5 mr-0.5" /> {job.salary}
            </span>
            <span className="mx-1.5 text-gray-300">|</span>
            
            <span className="flex items-center">
              {job.location}
            </span>
            <span className="mx-1.5 text-gray-300">|</span>
            
            <span>
              {job.experienceLevel || 'Mọi cấp độ'}
            </span>
             <span className="mx-1.5 text-gray-300">|</span>

             <span className="text-gray-400">
              {job.postedAt || 'Vừa xong'}
            </span>
          </div>

          {/* Compact Match Reason - Flattened and Smaller */}
          {hasMatch && job.match?.reason && (
            <div className="mt-2 text-xs text-gray-600 bg-blue-50/40 p-2 rounded-lg border border-blue-100/50">
              <span className="font-bold text-[#0A65CC] mr-1">Tại sao phù hợp:</span>
              <span className="italic">
                {formatMatchReason(job.match.reason)}
              </span>
            </div>
          )}

          {/* Desktop Actions - Moved inside flow to prevent overlap */}
          <div className="hidden sm:flex justify-end gap-3 mt-3">
            <button 
              onClick={(e) => { e.stopPropagation(); /* Save Logic */ }}
              className="p-1.5 text-gray-400 hover:text-blue-600 transition-colors border border-gray-200 rounded-lg hover:bg-gray-50"
              title="Lưu tin"
            >
              <Bookmark className="w-4 h-4" />
            </button>
            <button 
              onClick={handleApplyClick}
              className="bg-blue-600 text-white px-4 py-1.5 rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-sm text-xs"
            >
              Ứng tuyển ngay
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile Actions */}
      <div className="mt-3 pt-3 flex justify-between items-center sm:hidden border-t border-gray-100">
         <button 
            onClick={(e) => { e.stopPropagation(); }}
            className="text-gray-500 hover:text-blue-600 p-2"
         >
            <Bookmark className="w-5 h-5" />
         </button>
         <button 
           onClick={handleApplyClick}
           className="bg-blue-600 text-white px-5 py-2 rounded-lg font-semibold text-xs"
         >
           Ứng tuyển
         </button>
      </div>
    </div>
  );
};

export default JobCardWithMatch;
