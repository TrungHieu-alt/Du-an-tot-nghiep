
import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useSearchResults } from './useSearchResults';
import { searchCandidatesApi } from '../utils/mockApi';
import { ContextOption } from '../components/search/SearchBar';
import api from '../lib/api';
import { apiRoutes } from '../lib/api-routes';
import { getCurrentUserId } from '../lib/auth-session';
import { normalizeContextId } from '../lib/context-id';

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
        const userId = getCurrentUserId();
        if (!userId) return;
        const res = await api.get(apiRoutes.jobs.byRecruiter(userId));
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
    return requirements
      .map(req => ({
      id: normalizeContextId(req.job_id ?? req._id ?? req.id) || '',
      label: req.title || "Tin tuyển dụng không tên"
      }))
      .filter(req => Boolean(req.id));
  }, [requirements]);

  // Encapsulated handler for switching requirement
  const handleReqChange = (newReqId: string) => {
    const normalizedReqId = normalizeContextId(newReqId);
    setSearchParams(prev => {
      const p = new URLSearchParams(prev);
      if (!normalizedReqId) {
        p.delete('req');
        p.set('sort', 'newest');
        p.set('page', '1');
        return p;
      }
      p.set('req', normalizedReqId);
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
