import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CandidateWithMatch } from '../types';
import { MapPin, Briefcase, Star, MessageCircle, Bookmark } from 'lucide-react';

interface CandidateCardProps {
  candidate: CandidateWithMatch;
}

const CandidateCardWithMatch: React.FC<CandidateCardProps> = ({ candidate }) => {
  const navigate = useNavigate();
  const hasMatch = candidate.match && candidate.match.score > 0;
  const score = candidate.match?.score || 0;
  
  // Design constants for the circle
  // Using a slightly larger viewBox with padding to prevent stroke clipping
  const size = 60;
  const strokeWidth = 5;
  const center = size / 2;
  // Radius calculation: ensure (radius + strokeWidth/2) < (size/2)
  const radius = 26; // 26 + 2.5 = 28.5 < 30 (center), leaves 1.5px padding
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  // Color logic with more vibrant palette
  let colorClass = 'text-gray-400';
  let bgClass = 'bg-gray-50';
  let textClass = 'text-gray-700';
  let badgeBorderClass = 'border-gray-200';
  
  if (score >= 80) {
    colorClass = 'text-emerald-500';
    bgClass = 'bg-emerald-50';
    textClass = 'text-emerald-700';
    badgeBorderClass = 'border-emerald-200';
  } else if (score >= 50) {
    colorClass = 'text-amber-500';
    bgClass = 'bg-amber-50';
    textClass = 'text-amber-700';
    badgeBorderClass = 'border-amber-200';
  } else {
    colorClass = 'text-red-500';
    bgClass = 'bg-red-50';
    textClass = 'text-red-700';
    badgeBorderClass = 'border-red-200';
  }

  const handleClick = () => {
    navigate(`/candidates/${candidate.id}`);
  };

  const handleActionClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Action logic here (e.g., message or save)
  };

  return (
    <div 
      onClick={handleClick}
      className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm hover:shadow-lg hover:border-blue-200 transition-all duration-200 relative group cursor-pointer"
    >
      {/* Match Badge - Circular Progress */}
      {hasMatch && (
        <div className="absolute top-5 right-5 flex flex-col items-center z-10">
          <div className="relative flex items-center justify-center">
            {/* SVG Circle */}
            <svg 
              width={size} 
              height={size} 
              viewBox={`0 0 ${size} ${size}`} 
              className="transform -rotate-90 drop-shadow-sm" 
              style={{ overflow: 'visible' }}
            >
              {/* Background Track */}
              <circle
                cx={center}
                cy={center}
                r={radius}
                stroke="currentColor"
                strokeWidth={strokeWidth}
                fill="white"
                className="text-gray-100"
              />
              {/* Progress Track */}
              <circle
                cx={center}
                cy={center}
                r={radius}
                stroke="currentColor"
                strokeWidth={strokeWidth}
                fill="transparent"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className={`${colorClass} transition-all duration-1000 ease-out`}
              />
            </svg>
            
            {/* Percentage Text */}
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-sm font-bold ${textClass}`}>
                {score}%
              </span>
            </div>
          </div>
          
          {/* Star Label */}
          <div className={`flex items-center gap-1 text-[10px] font-bold mt-1.5 px-2.5 py-0.5 rounded-full border ${badgeBorderClass} ${bgClass} ${textClass}`}>
            <Star className="w-3 h-3 fill-current" />
            <span>Phù hợp</span>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-5">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <img 
            src={candidate.avatar} 
            alt={candidate.name} 
            className="w-20 h-20 rounded-full object-cover border-2 border-gray-100 shadow-sm"
          />
        </div>

        {/* Content */}
        <div className="flex-1 pr-20"> {/* Increased padding for badge */}
          <div className="mb-1">
            <h3 className="text-lg font-bold text-gray-900 group-hover:text-[#0A65CC] transition-colors inline-block">
              {candidate.name}
            </h3>
          </div>
          <p className="text-[#0A65CC] font-medium text-sm mb-2 line-clamp-1">{candidate.headline}</p>

          <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-gray-500 mb-3">
             <div className="flex items-center gap-1">
               <MapPin className="w-3.5 h-3.5" />
               {candidate.location}
             </div>
             <div className="flex items-center gap-1">
               <Briefcase className="w-3.5 h-3.5" />
               {candidate.yearsOfExperience} năm kinh nghiệm ({candidate.experienceLevel})
             </div>
          </div>

          {/* Skills Tags */}
          <div className="flex flex-wrap gap-2 mb-4">
            {candidate.skills.slice(0, 5).map((skill, i) => (
              <span key={i} className="px-2.5 py-1 bg-gray-50 text-gray-600 text-xs rounded-md border border-gray-100 font-medium">
                {skill}
              </span>
            ))}
            {candidate.skills.length > 5 && (
              <span className="px-2.5 py-1 bg-gray-50 text-gray-400 text-xs rounded-md border border-gray-100">+{candidate.skills.length - 5}</span>
            )}
          </div>

          {/* Match Reason - Only show if reason exists */}
          {hasMatch && candidate.match?.reason && (
            <div className={`p-3 rounded-lg border text-sm mb-4 transition-colors ${
                score >= 80 ? 'bg-emerald-50/60 border-emerald-100 text-emerald-800' : 
                score >= 50 ? 'bg-amber-50/60 border-amber-100 text-amber-800' :
                'bg-gray-50 border-gray-100 text-gray-600'
            }`}>
              <span className="font-semibold">AI Match:</span> {candidate.match.reason}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2 border-t border-gray-50">
            <button 
              onClick={handleActionClick}
              className="bg-[#0A65CC] hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-colors z-10 shadow-sm"
            >
              <MessageCircle className="w-4 h-4" />
              Nhắn tin
            </button>
            <button 
              onClick={handleActionClick}
              className="border border-gray-200 hover:border-[#0A65CC] hover:text-[#0A65CC] text-gray-600 px-4 py-2 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-colors z-10 bg-white"
            >
              <Bookmark className="w-4 h-4" />
              Lưu hồ sơ
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CandidateCardWithMatch;