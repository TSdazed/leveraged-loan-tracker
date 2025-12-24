import React from 'react';
import { formatPercentage, getStatusColor } from '../utils/formatters';
import './MetricCard.css';

const MetricCard = ({ 
  title, 
  value, 
  subtitle, 
  trend,
  thresholds,
  loading = false 
}) => {
  const color = getStatusColor(value, thresholds);
  
  const getTrendIcon = () => {
    if (!trend) return null;
    if (trend === 'up') return '↑';
    if (trend === 'down') return '↓';
    return '→';
  };

  const getTrendColor = () => {
    if (!trend) return '#gray';
    // For metrics like delinquency, up is bad, down is good
    if (trend === 'up') return '#ef4444';
    if (trend === 'down') return '#10b981';
    return '#6b7280';
  };

  if (loading) {
    return (
      <div className="metric-card loading">
        <div className="metric-card-header">
          <h3>{title}</h3>
        </div>
        <div className="metric-card-body">
          <div className="loading-spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="metric-card">
      <div className="metric-card-header">
        <h3>{title}</h3>
        {trend && (
          <span className="trend-indicator" style={{ color: getTrendColor() }}>
            {getTrendIcon()}
          </span>
        )}
      </div>
      <div className="metric-card-body">
        <div className="metric-value" style={{ color }}>
          {value !== null && value !== undefined ? formatPercentage(value) : 'N/A'}
        </div>
        {subtitle && (
          <div className="metric-subtitle">{subtitle}</div>
        )}
      </div>
    </div>
  );
};

export default MetricCard;
