
import React, { useState, useRef, useEffect } from 'react';
import { UserCV } from '../types';
import { FileText, MapPin, Clock, MoreHorizontal, Pencil, Edit, Trash2, Check, X as XIcon } from 'lucide-react';

interface CvCardProps {
  cv: UserCV;
  onSelect: (cv: UserCV) => void;
  currentUserId?: string;
  onEdit?: (cv: UserCV) => void;
  onDelete?: (cv: UserCV) => void;
  onRename?: (cv: UserCV, newName: string) => void;
}

const CvCard: React.FC<CvCardProps> = ({
  cv, onSelect, currentUserId = "user_123", onEdit, onDelete, onRename
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(cv.name);

  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Default to true for demo purposes, or check if cv.ownerId matches
  const isOwner = !cv.ownerId || cv.ownerId === currentUserId;

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

  useEffect(() => {
    if (isRenaming && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isRenaming]);

  const toggleMenu = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowMenu(!showMenu);
  };

  const handleAction = (e: React.MouseEvent, action: 'edit' | 'delete' | 'rename') => {
    e.stopPropagation();
    setShowMenu(false);

    if (action === 'rename') {
      setIsRenaming(true);
      setRenameValue(cv.name);
    }
    if (action === 'edit' && onEdit) onEdit(cv);
    if (action === 'delete' && onDelete) onDelete(cv);
  };

  const handleRenameSubmit = (e?: React.MouseEvent | React.FormEvent) => {
    if (e) e.stopPropagation();
    if (renameValue.trim() && onRename) {
      onRename(cv, renameValue.trim());
    }
    setIsRenaming(false);
  };

  const handleRenameCancel = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsRenaming(false);
    setRenameValue(cv.name);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleRenameSubmit();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setIsRenaming(false);
      setRenameValue(cv.name);
    }
  };

  return (
    <div className="group relative bg-white rounded-2xl p-5 border border-gray-200 hover:border-blue-200 hover:shadow-lg transition-all duration-300 flex flex-col h-full transform motion-safe:hover:-translate-y-0.5">
      <div className="flex items-start gap-4 mb-3">
        {/* Icon */}
        <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
          <FileText className="w-6 h-6" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start">
            <div className="w-full pr-2">
              {isRenaming ? (
                <div className="flex items-center gap-1 w-full" onClick={e => e.stopPropagation()}>
                  <input
                    ref={inputRef}
                    type="text"
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="flex-1 text-base font-bold text-gray-900 border-b-2 border-blue-500 focus:outline-none bg-transparent px-1 pb-1"
                  />
                  <button onClick={handleRenameSubmit} className="p-1 text-green-600 hover:bg-green-50 rounded">
                    <Check className="w-4 h-4" />
                  </button>
                  <button onClick={handleRenameCancel} className="p-1 text-red-500 hover:bg-red-50 rounded">
                    <XIcon className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <h3 
                  className="text-base font-bold text-gray-900 truncate group-hover:text-[#0A65CC] transition-colors"
                  title={cv.name}
                >
                  {cv.name}
                </h3>
              )}
              <p className="text-sm text-gray-600 truncate mt-1">{cv.title}</p>
            </div>

            {/* Actions Menu */}
            {isOwner && !isRenaming && (
              <div className="relative ml-2">
                <button
                  ref={buttonRef}
                  onClick={toggleMenu}
                  className={`p-1 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-gray-200 
                    ${showMenu ? 'bg-gray-100 text-gray-900' : 'text-gray-300 hover:text-gray-600 hover:bg-gray-50'}`}
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
                      className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 flex items-center gap-2 transition-colors"
                    >
                      <Pencil className="w-4 h-4" /> Đổi tên
                    </button>
                    <button
                      onClick={(e) => handleAction(e, 'edit')}
                      className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 flex items-center gap-2 transition-colors"
                    >
                      <Edit className="w-4 h-4" /> Chỉnh sửa
                    </button>
                    <button
                      onClick={(e) => handleAction(e, 'delete')}
                      className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" /> Xóa
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Details */}
      <div className="mb-5 space-y-2 flex-1">
        <div className="flex items-center gap-2 text-xs text-gray-500">
           <MapPin className="w-3.5 h-3.5" />
           <span className="truncate">{cv.location}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
           <Clock className="w-3.5 h-3.5" />
           <span className="truncate">Cập nhật {cv.lastUpdated}</span>
        </div>
        <div className="mt-2 flex flex-wrap gap-1">
            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                {cv.experienceLevel}
            </span>
            {cv.skills.slice(0, 2).map(skill => (
                <span key={skill} className="text-xs bg-gray-50 border border-gray-100 text-gray-500 px-2 py-0.5 rounded">
                    {skill}
                </span>
            ))}
        </div>
      </div>

      <button
        onClick={() => onSelect(cv)}
        className="w-full py-2.5 rounded-lg font-bold text-sm text-white bg-[#0A65CC] hover:bg-blue-700 shadow-md hover:shadow-lg transition-all focus:outline-none focus:ring-4 focus:ring-blue-100"
      >
        Chọn hồ sơ
      </button>
    </div>
  );
};

export default CvCard;
