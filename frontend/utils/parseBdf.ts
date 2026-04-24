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
  void file;
  throw new Error('Tính năng parse-bdf chưa được backend hỗ trợ trong contract hiện tại.');
};
