import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
} from 'recharts';
import { formatDate } from '../utils/formatters';
import './TimeSeriesChart.css';

const TimeSeriesChart = ({
  data,
  series,
  recessions = [],
  title,
  yAxisLabel,
  height = 400,
  loading = false,
}) => {
  // Transform data for recharts
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    return data.map(point => ({
      ...point,
      timestamp: new Date(point.date).getTime(),
      displayDate: formatDate(point.date, 'MMM yyyy'),
    }));
  }, [data]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div className="custom-tooltip">
        <p className="tooltip-date">{payload[0].payload.displayDate}</p>
        {payload.map((entry, index) => (
          <p key={index} className="tooltip-value" style={{ color: entry.color }}>
            <strong>{entry.name}:</strong> {entry.value.toFixed(2)}%
          </p>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="chart-container loading">
        <h2>{title}</h2>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (!chartData || chartData.length === 0) {
    return (
      <div className="chart-container empty">
        <h2>{title}</h2>
        <p>No data available</p>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <h2>{title}</h2>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          
          <XAxis
            dataKey="timestamp"
            type="number"
            scale="time"
            domain={['dataMin', 'dataMax']}
            tickFormatter={(timestamp) => formatDate(new Date(timestamp), 'yyyy')}
            stroke="#6b7280"
          />
          
          <YAxis
            label={{ value: yAxisLabel, angle: -90, position: 'insideLeft' }}
            stroke="#6b7280"
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          <Legend />

          {/* Recession periods as shaded areas */}
          {recessions.map((recession, index) => {
            const startTime = new Date(recession.start_date).getTime();
            const endTime = recession.end_date
              ? new Date(recession.end_date).getTime()
              : new Date().getTime();

            return (
              <ReferenceArea
                key={index}
                x1={startTime}
                x2={endTime}
                fill="#ef4444"
                fillOpacity={0.1}
                label={{
                  value: recession.name || 'Recession',
                  position: 'top',
                  fill: '#ef4444',
                  fontSize: 10,
                }}
              />
            );
          })}

          {/* Data series lines */}
          {series.map((s, index) => (
            <Line
              key={s.dataKey}
              type="monotone"
              dataKey={s.dataKey}
              name={s.name}
              stroke={s.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TimeSeriesChart;
