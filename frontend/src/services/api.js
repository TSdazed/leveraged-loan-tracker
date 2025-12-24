import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://leveraged-loan-api.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const marketDataService = {
  // Get health status
  getHealth: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  // Get current market overview
  getCurrentOverview: async () => {
    const response = await api.get('/api/overview/current');
    return response.data;
  },

  // Get historical data for all series
  getHistoricalOverview: async (startDate = '1980-01-01', endDate = null) => {
    const params = { start_date: startDate };
    if (endDate) params.end_date = endDate;
    
    const response = await api.get('/api/overview/historical', { params });
    return response.data;
  },

  // Get specific series data
  getSeries: async (seriesId, startDate = '1980-01-01', endDate = null) => {
    const params = { start_date: startDate };
    if (endDate) params.end_date = endDate;
    
    const response = await api.get(`/api/series/${seriesId}`, { params });
    return response.data;
  },

  // Get recession periods
  getRecessions: async (startDate = '1980-01-01', endDate = null) => {
    const params = { start_date: startDate };
    if (endDate) params.end_date = endDate;
    
    const response = await api.get('/api/recessions', { params });
    return response.data;
  },

  // Get statistics
  getStats: async () => {
    const response = await api.get('/api/stats');
    return response.data;
  },

  // Refresh data
  refreshData: async (startDate = '1980-01-01') => {
    const response = await api.post(`/api/data/refresh?start_date=${startDate}`);
    return response.data;
  },
};

export default marketDataService;
