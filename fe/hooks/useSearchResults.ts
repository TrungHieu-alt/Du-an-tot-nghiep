import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SearchState, SortOption, SearchResponse } from '../types';

interface UseSearchResultsProps<T> {
  apiCall: (params: SearchState, contextId?: string) => Promise<SearchResponse<T>>;
  initialSort?: SortOption;
  contextParamKey?: string; // 'cv' or 'req'
}

export function useSearchResults<T>({ apiCall, initialSort = 'relevance', contextParamKey }: UseSearchResultsProps<T>) {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Initialize state from URL params
  const [state, setState] = useState<SearchState>(() => ({
    q: searchParams.get('q') || '',
    location: searchParams.get('location') || '',
    filters: {}, // Complex filters are harder to sync deeply in URL for this demo, keeping simple
    sort: (searchParams.get('sort') as SortOption) || initialSort,
    page: parseInt(searchParams.get('page') || '1', 10),
  }));

  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [meta, setMeta] = useState({ page: 1, limit: 10, total: 0, totalPages: 0 });

  const contextId = contextParamKey ? searchParams.get(contextParamKey) || undefined : undefined;

  // Sync state to URL (Debounced effect for text inputs could be added here)
  useEffect(() => {
    const params: Record<string, string> = {};
    if (state.q) params.q = state.q;
    if (state.location) params.location = state.location;
    if (state.sort !== 'relevance') params.sort = state.sort;
    if (state.page > 1) params.page = state.page.toString();
    if (contextId) params[contextParamKey!] = contextId;
    
    // In a real app, serialize filters to URL here
    
    setSearchParams(params, { replace: true });
  }, [state, contextId, setSearchParams, contextParamKey]);

  // Fetch Data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiCall(state, contextId);
      // Safely handle missing data/meta to prevent crashes
      setData(response?.data || []);
      setMeta(response?.meta || { page: 1, limit: 10, total: 0, totalPages: 0 });
    } catch (error) {
      console.error("Search failed", error);
      // Reset to empty state on error
      setData([]);
      setMeta({ page: 1, limit: 10, total: 0, totalPages: 0 });
    } finally {
      setLoading(false);
    }
  }, [state, contextId, apiCall]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handlers
  const handleQueryChange = (q: string) => setState(s => ({ ...s, q, page: 1 }));
  const handleLocationChange = (loc: string) => setState(s => ({ ...s, location: loc, page: 1 }));
  const handleSortChange = (sort: SortOption) => setState(s => ({ ...s, sort, page: 1 }));
  const handlePageChange = (page: number) => setState(s => ({ ...s, page }));
  
  const handleFilterChange = (groupId: string, value: string) => {
    setState(s => {
      const currentgroup = s.filters[groupId] || [];
      const newGroup = currentgroup.includes(value)
        ? currentgroup.filter(v => v !== value)
        : [...currentgroup, value];
      
      return {
        ...s,
        filters: { ...s.filters, [groupId]: newGroup },
        page: 1
      };
    });
  };

  const handleClearFilters = () => setState(s => ({ ...s, filters: {}, page: 1 }));
  const handleClearContext = () => {
    if (contextParamKey) {
       searchParams.delete(contextParamKey);
       setSearchParams(searchParams);
       setState(s => ({ ...s, sort: 'newest' })); // Default sort when Manual
    }
  };

  return {
    data,
    loading,
    meta,
    state,
    contextId,
    handleQueryChange,
    handleLocationChange,
    handleSortChange,
    handlePageChange,
    handleFilterChange,
    handleClearFilters,
    handleClearContext,
    refresh: fetchData
  };
}