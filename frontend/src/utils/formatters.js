import { format, parseISO } from 'date-fns';

/**
 * Format a date string for display
 */
export const formatDate = (dateString, formatStr = 'MMM yyyy') => {
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString;
    return format(date, formatStr);
  } catch (error) {
    return dateString;
  }
};

/**
 * Format a number as percentage
 */
export const formatPercentage = (value, decimals = 2) => {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(decimals)}%`;
};

/**
 * Format a number with commas
 */
export const formatNumber = (value, decimals = 0) => {
  if (value === null || value === undefined) return 'N/A';
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

/**
 * Convert API data to chart format
 */
export const transformToChartData = (apiData) => {
  if (!apiData || !apiData.data) return [];
  
  return apiData.data.map(point => ({
    date: new Date(point.date).getTime(),
    value: point.value,
    formattedDate: formatDate(point.date),
  }));
};

/**
 * Get color based on value (for indicators)
 */
export const getStatusColor = (value, thresholds = { good: 2, warning: 4 }) => {
  if (value === null || value === undefined) return '#gray';
  if (value <= thresholds.good) return '#10b981'; // green
  if (value <= thresholds.warning) return '#f59e0b'; // yellow
  return '#ef4444'; // red
};

/**
 * Merge multiple series data by date
 */
export const mergeSeriesData = (seriesDataMap) => {
  const dateMap = new Map();

  // Collect all data points
  Object.entries(seriesDataMap).forEach(([seriesId, seriesData]) => {
    if (seriesData && seriesData.data) {
      seriesData.data.forEach(point => {
        const dateStr = point.date;
        if (!dateMap.has(dateStr)) {
          dateMap.set(dateStr, { date: dateStr });
        }
        dateMap.get(dateStr)[seriesId] = point.value;
      });
    }
  });

  // Convert to array and sort by date
  return Array.from(dateMap.values()).sort((a, b) => 
    new Date(a.date) - new Date(b.date)
  );
};

/**
 * Calculate year-over-year change
 */
export const calculateYoYChange = (current, previous) => {
  if (!current || !previous || previous === 0) return null;
  return ((current - previous) / previous) * 100;
};

/**
 * Get trend indicator (up/down/stable)
 */
export const getTrend = (values) => {
  if (!values || values.length < 2) return 'stable';
  
  const recent = values.slice(-5); // Last 5 points
  const firstValue = recent[0];
  const lastValue = recent[recent.length - 1];
  
  const change = ((lastValue - firstValue) / firstValue) * 100;
  
  if (Math.abs(change) < 2) return 'stable';
  return change > 0 ? 'up' : 'down';
};
