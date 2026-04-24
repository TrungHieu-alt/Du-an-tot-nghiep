
import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useSearchResults } from './useSearchResults';
import { searchCandidatesApi } from '../utils/mockApi';
import { ContextOption } from '../components/search/SearchBar';
import api from '../lib/api';

/**
 * Specialized hook for Candidate Search Page.
 * Wraps useSearchResults to handle "Requirement" context logic.
 */
export const useCandidatesSearch = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [requirements, setRequirements] = useState<any[]>([]);

  // Use generic search hook configured for Candidates API
  const search = useSearchResults({
    apiCall: searchCandidatesApi,
    contextParamKey: 'req',
    initialSort: 'relevance'
  });

  // Fetch available requirements for the dropdown from API
  useEffect(() => {
    const fetchRequirements = async () => {
      try {
        const res = await api.get('/jobs/user/me');
        // Handle various response shapes (array or object with data/items property)
        const data = Array.isArray(res.data) ? res.data : (res.data?.data || res.data?.items || []);
        
        if (Array.isArray(data)) {
          setRequirements(data);
        }
      } catch (error) {
        console.error("Failed to fetch requirements for search dropdown", error);
      }
    };

    fetchRequirements();
  }, []);

  // Convert to dropdown options
  const contextOptions: ContextOption[] = useMemo(() => {
    return requirements.map(req => ({
      id: req._id || req.id,
      label: req.title || "Tin tuyển dụng không tên"
    }));
  }, [requirements]);

  // Encapsulated handler for switching requirement
  const handleReqChange = (newReqId: string) => {
    setSearchParams(prev => {
      const p = new URLSearchParams(prev);
      p.set('req', newReqId);
      p.delete('manual'); // Remove manual flag if present
      p.set('page', '1'); // Reset to page 1
      p.set('sort', 'relevance'); // Force sort to relevance context
      // Reset filters if needed, or keep them to filter within the new requirement context
      return p;
    });
  };

  return {
    ...search,
    requirements,
    contextOptions,
    handleReqChange // Exporting the handler for the UI
  };
};
