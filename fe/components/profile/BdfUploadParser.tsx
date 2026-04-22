
import React, { useState, useCallback } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import api from '../../lib/api';

interface ParsedData {
  _id?: string;
  id?: string;
  // Common fields
  title?: string;
  skills?: string | any[];
  experienceLevel?: string;
  location?: string | any;
  // CV specific
  fullname?: string;
  email?: string;
  phone?: string;
  summary?: string;
  experiences?: any[];
  education?: any[];
  certifications?: any[];
  projects?: any[];
  languages?: any[];
  // JD specific
  criteria?: string;
  [key: string]: any;
}

interface BdfUploadParserProps {
  onParseComplete: (data: ParsedData) => void;
}

const BdfUploadParser: React.FC<BdfUploadParserProps> = ({ onParseComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const processFile = useCallback(async (file: File) => {
    // Validate file type
    if (!file.name.match(/\.(pdf|doc|docx|bdf)$/i)) {
      setError("Định dạng file không hỗ trợ. Vui lòng tải lên PDF, DOC, DOCX hoặc BDF.");
      return;
    }

    setError(null);
    setFileName(file.name);
    setIsParsing(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Call real API
      const response = await api.post('/cv/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 120s timeout
      });

      const responseData = response.data;
      
      // Smart extraction of the result object
      // Priority: response.data.data.result -> response.data.data -> response.data
      let resultObj = null;

      if (responseData?.data?.result) {
        resultObj = responseData.data.result;
      } else if (responseData?.data && typeof responseData.data === 'object' && !Array.isArray(responseData.data)) {
        // Sometimes data IS the object
        resultObj = responseData.data;
      } else {
        resultObj = responseData;
      }

      // Ensure we catch the ID if it exists anywhere nearby
      if (resultObj) {
         // Fallback lookups for ID if strictly nested structure varies
         if (!resultObj._id && !resultObj.id) {
             if (responseData._id) resultObj._id = responseData._id;
             else if (responseData.data?._id) resultObj._id = responseData.data._id;
         }
         
         onParseComplete(resultObj);
      } else {
         throw new Error("Không nhận được dữ liệu phản hồi hợp lệ từ máy chủ.");
      }

    } catch (err: any) {
      console.error("Upload error:", err);
      const msg = err.response?.data?.message || err.message || "Có lỗi xảy ra khi phân tích tài liệu.";
      setError(msg);
      setFileName(null);
    } finally {
      setIsParsing(false);
    }
  }, [onParseComplete]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full">
      <div 
        className={`
          relative border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-300
          ${isDragging 
            ? 'border-[#0A65CC] bg-blue-50' 
            : 'border-gray-200 bg-gray-50 hover:bg-gray-100 hover:border-gray-300'}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          id="file-upload" 
          className="hidden" 
          accept=".pdf,.doc,.docx,.bdf"
          onChange={handleFileSelect}
        />

        {isParsing ? (
          <div className="flex flex-col items-center animate-in fade-in">
            <Loader2 className="w-12 h-12 text-[#0A65CC] animate-spin mb-4" />
            <p className="font-semibold text-gray-900">Đang phân tích tài liệu...</p>
            <p className="text-sm text-gray-500 mt-1">Hệ thống đang trích xuất thông tin kỹ năng và kinh nghiệm.</p>
          </div>
        ) : fileName ? (
          <div className="flex flex-col items-center animate-in fade-in">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle2 className="w-8 h-8 text-green-600" />
            </div>
            <p className="font-bold text-gray-900 text-lg mb-1">Phân tích thành công!</p>
            <p className="text-gray-600 mb-4">{fileName}</p>
            <p className="text-sm text-[#0A65CC]">Đang xử lý dữ liệu...</p>
          </div>
        ) : (
          <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
            <div className="w-16 h-16 bg-white rounded-full shadow-sm flex items-center justify-center mb-4">
              <UploadCloud className="w-8 h-8 text-[#0A65CC]" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">
              Kéo thả hoặc tải lên CV/JD
            </h3>
            <p className="text-gray-500 text-sm max-w-sm mb-6 leading-relaxed">
              Hỗ trợ định dạng .PDF, .DOCX. Hệ thống sẽ tự động phân tích và điền thông tin cho bạn.
            </p>
            <span className="bg-white border border-gray-200 text-gray-700 px-6 py-2.5 rounded-full font-semibold hover:border-[#0A65CC] hover:text-[#0A65CC] transition-colors shadow-sm">
              Chọn tệp tin
            </span>
          </label>
        )}
      </div>

      {error && (
        <div className="mt-4 bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-xl flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          {error}
        </div>
      )}
    </div>
  );
};

export default BdfUploadParser;
