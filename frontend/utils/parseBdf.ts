import api from '../lib/api';

interface ParsedBdfResponse {
  title?: string;
  skills?: string;
  experienceLevel?: string;
  location?: string;
  salaryRange?: string;
  criteria?: string;
  rawText?: string;
}

/**
 * Uploads and parses a BDF/PDF/DOC file.
 */
export const parseBdfApi = async (file: File): Promise<ParsedBdfResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/parse-bdf', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};