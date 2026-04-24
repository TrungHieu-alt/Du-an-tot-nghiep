
import React, { useState, useRef, useEffect } from 'react';
import { JobRequirement } from '../types';
import { Code, Megaphone, Server, PenTool, MoreHorizontal, CheckCircle2, Trash2, Edit, Pencil, Check, X as XIcon } from 'lucide-react';

interface RequirementCardProps {
  req: JobRequirement;
  onSelect: (req: JobRequirement) => void;
  currentUserId?: string;
  onEdit?: (req: JobRequirement) => void;
  onDelete?: (req: JobRequirement) => void;
  onRename?: (req: JobRequirement, newTitle: string) => void;
}

const RequirementCard: React.FC<RequirementCardProps> = ({ 
  req, onSelect, currentUserId = "user_123", onEdit, onDelete, onRename 
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(req.title);
  
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Check ownership (If ownerId is missing in mock data, assume owned for demo purposes, or enforce strict check)
  const isOwner = req.ownerId === currentUserId || !req.ownerId;

  // Map icon string to component
  const getIcon = (type: string) => {
    switch (type) {
      case 'Code': return <Code className="w-6 h-6 text-white" />;
      case 'Megaphone': return <Megaphone className="w-6 h-6 text-white" />;
      case 'Server': return <Server className="w-6 h-6 text-white" />;
      case 'PenTool': return <PenTool className="w-6 h-6 text-white" />;
      default: return <Code className="w-6 h-6 text-white" />;
    }
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuRef.current && 
        !menuRef.current.contains(event.target as Node) &&
        !buttonRef.current?.contains(event.target as Node)
      ) {
        setShowMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus input when renaming starts
  useEffect(() => {
    if (isRenaming && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isRenaming]);

  const handleAction = (e: React.MouseEvent, action: 'edit' | 'delete' | 'rename') => {
    e.stopPropagation();
    setShowMenu(false);
    
    if (action === 'rename') {
      setIsRenaming(true);
      setRenameValue(req.title);
    }
    if (action === 'edit' && onEdit) onEdit(req);
    if (action === 'delete' && onDelete) onDelete(req);
  };

  const toggleMenu = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowMenu(!showMenu);
  };

  const handleRenameSubmit = (e?: React.MouseEvent | React.FormEvent) => {
    if (e) e.stopPropagation();
    if (renameValue.trim() && onRename) {
      onRename(req, renameValue.trim());
    }
    setIsRenaming(false);
  };

  const handleRenameCancel = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsRenaming(false);
    setRenameValue(req.title);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleRenameSubmit();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setIsRenaming(false);
      setRenameValue(req.title);
    }
  };

  return (
    <div className="group relative bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all duration-300 flex flex-col h-full transform motion-safe:hover:-translate-y-1">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-lg shadow-gray-200/50 ${req.color}`}>
          {getIcon(req.iconType)}
        </div>
        
        {/* Action Menu - Only visible to owner */}
        {isOwner && !isRenaming && (
          <div className="relative">
            <button 
              ref={buttonRef}
              onClick={toggleMenu}
              className={`p-1 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-gray-200 
                ${showMenu ? 'bg-gray-100 text-gray-900' : 'text-gray-300 hover:text-gray-600 hover:bg-gray-50'}`}
              aria-label="Tùy chọn"
              aria-haspopup="true"
              aria-expanded={showMenu}
            >
              <MoreHorizontal className="w-5 h-5" />
            </button>

            {showMenu && (
              <div 
                ref={menuRef}
                className="absolute right-0 top-full mt-2 w-40 bg-white rounded-xl shadow-xl border border-gray-100 py-1 z-10 animate-in fade-in zoom-in-95 duration-100"
              >
                <button
                  onClick={(e) => handleAction(e, 'rename')}
                  className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 flex items-center gap-2 transition-colors focus:outline-none focus:bg-blue-50"
                >
                  <Pencil className="w-4 h-4" /> Đổi tên
                </button>
                <button
                  onClick={(e) => handleAction(e, 'edit')}
                  className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 flex items-center gap-2 transition-colors focus:outline-none focus:bg-blue-50"
                >
                  <Edit className="w-4 h-4" /> Chỉnh sửa
                </button>
                <button
                  onClick={(e) => handleAction(e, 'delete')}
                  className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 transition-colors focus:outline-none focus:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" /> Xóa
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Title / Inline Rename */}
      <div className="mb-4 min-h-[56px] flex items-center">
        {isRenaming ? (
          <div className="flex items-center gap-2 w-full" onClick={e => e.stopPropagation()}>
            <input
              ref={inputRef}
              type="text"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 text-lg font-bold text-gray-900 border-b-2 border-blue-500 focus:outline-none bg-transparent px-1 pb-1"
              aria-label="Nhập tên mới"
            />
            <button 
              onClick={handleRenameSubmit} 
              className="p-1 text-green-600 hover:bg-green-50 rounded focus:outline-none focus:ring-2 focus:ring-green-500/20" 
              title="Lưu"
              aria-label="Lưu tên mới"
            >
              <Check className="w-5 h-5" />
            </button>
            <button 
              onClick={handleRenameCancel} 
              className="p-1 text-red-500 hover:bg-red-50 rounded focus:outline-none focus:ring-2 focus:ring-red-500/20" 
              title="Hủy"
              aria-label="Hủy đổi tên"
            >
              <XIcon className="w-5 h-5" />
            </button>
          </div>
        ) : (
          <div className="w-full">
            <h3 className="text-lg font-bold text-gray-900 group-hover:text-[#0A65CC] transition-colors line-clamp-1" title={req.title}>
              {req.title}
            </h3>
            <p className="text-sm text-gray-400 font-medium">
              {req.criteriaList.length} tiêu chí
            </p>
          </div>
        )}
      </div>

      {/* Checklist */}
      <div className="flex-1 space-y-2.5 mb-6">
        {req.criteriaList.slice(0, 4).map((criteria, index) => (
          <div key={index} className="flex items-start gap-2.5 text-[15px] text-gray-600 leading-snug">
            <CheckCircle2 className="w-4 h-4 text-[#00B14F] mt-0.5 flex-shrink-0" />
            <span className="line-clamp-2">{criteria}</span>
          </div>
        ))}
        {req.criteriaList.length > 4 && (
          <p className="text-xs text-gray-400 pl-6">+ {req.criteriaList.length - 4} tiêu chí khác</p>
        )}
      </div>

      {/* Action Button */}
      <button
        onClick={() => onSelect(req)}
        className="w-full py-3 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-[#0A65CC] to-[#00B14F] opacity-90 hover:opacity-100 shadow-md hover:shadow-lg transition-all transform active:scale-[0.98] focus:outline-none focus:ring-4 focus:ring-blue-100"
      >
        Chọn
      </button>
    </div>
  );
};

export default RequirementCard;
