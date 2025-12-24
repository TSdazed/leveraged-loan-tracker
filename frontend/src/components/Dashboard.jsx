import React, { useState, useEffect } from 'react';
import marketDataService from '../services/api';
import MetricCard from './MetricCard';
import TimeSeriesChart from './TimeSeriesChart';
import { getTrend } from '../utils/formatters';
import './Dashboard.css';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [currentData, setCurrentData] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [recessions, setRecessions] = useState([]);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Fetch all data on mount
  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all data in parallel
      const [current, historical, recessionsData] = await Promise.all([
        marketDataService.getCurrentOverview(),
        marketDataService.getHistoricalOverview('1980-01-01'),
        marketDataService.getRecessions('1980-01-01'),
      ]);

      setCurrentData(current);
      setHistoricalData(historical);
      setRecessions(recessionsData);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load market data. Please ensure the backend is running.');
      setLoading(false);
    }
  };

  // Transform historical data for charts
  const getChartData = (seriesId) => {
    if (!historicalData || !historicalData[seriesId]) return [];
    return historicalData[seriesId].data;
  };

  // Get trend for a series
  const getSeriesTrend = (seriesId) => {
    const data = getChartData(seriesId);
    if (!data || data.length === 0) return null;
    const values = data.map(d => d.value);
    return getTrend(values);
  };

  if (error) {
    return (
      <div className="dashboard">
        <div className="error-container">
          <h2>⚠️ Error Loading Data</h2>
          <p>{error}</p>
          <button onClick={fetchAllData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div>
          <h1>T'Smith; Financial Markets and Loan Deliquency Tracking</h1>
          <p className="subtitle">
            Historical analysis from 1980s to present, Each graph depicts a key data set that I believe are strong indicators and pre determinates of a recession
          </p>
        </div>
        <div className="header-actions">
          {lastUpdate && (
            <span className="last-update">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button onClick={fetchAllData} className="refresh-button" disabled={loading}>
            {loading ? '↻ Loading...' : '↻ Refresh'}
          </button>
        </div>
      </header>

      {/* Current Metrics Overview */}
      <section className="metrics-grid">
        <MetricCard
          title="Delinquency Rate"
          value={currentData?.delinquency_rate}
          subtitle="Business loans, all commercial banks"
          trend={getSeriesTrend('DRBLACBS')}
          thresholds={{ good: 2, warning: 4 }}
          loading={loading}
        />
        <MetricCard
          title="Charge-Off Rate"
          value={currentData?.charge_off_rate}
          subtitle="Business loans, all commercial banks"
          trend={getSeriesTrend('CORBLACBS')}
          thresholds={{ good: 1, warning: 2 }}
          loading={loading}
        />
        <MetricCard
          title="High Yield Spread"
          value={currentData?.high_yield_spread}
          subtitle="ICE BofA High Yield Index"
          trend={getSeriesTrend('BAMLH0A0HYM2')}
          thresholds={{ good: 400, warning: 800 }}
          loading={loading}
        />
        <MetricCard
          title="Unemployment Rate"
          value={currentData?.unemployment_rate}
          subtitle="U.S. unemployment rate"
          trend={getSeriesTrend('UNRATE')}
          thresholds={{ good: 5, warning: 7 }}
          loading={loading}
        />
      </section>

      {/* Recession Indicator */}
      {currentData?.in_recession && (
        <div className="recession-alert">
          <span className="alert-icon">⚠️</span>
          <span>Currently in recession period</span>
        </div>
      )}

      {/* Charts */}
      <section className="charts-section">
        <TimeSeriesChart
          data={getChartData('DRBLACBS')}
          series={[
            {
              dataKey: 'value',
              name: 'Delinquency Rate (%)',
              color: '#3b82f6',
            },
          ]}
          recessions={recessions}
          title="Business Loan Delinquency Rate Over Time"
          yAxisLabel="Delinquency Rate (%)"
          loading={loading}
          height={450}
        />

        <TimeSeriesChart
          data={getChartData('CORBLACBS')}
          series={[
            {
              dataKey: 'value',
              name: 'Charge-Off Rate (%)',
              color: '#ef4444',
            },
          ]}
          recessions={recessions}
          title="Business Loan Charge-Off Rate Over Time"
          yAxisLabel="Charge-Off Rate (%)"
          loading={loading}
          height={450}
        />

        <TimeSeriesChart
          data={getChartData('BAMLH0A0HYM2')}
          series={[
            {
              dataKey: 'value',
              name: 'High Yield Spread (bps)',
              color: '#8b5cf6',
            },
          ]}
          recessions={recessions}
          title="High Yield Corporate Bond Spread"
          yAxisLabel="Spread (basis points)"
          loading={loading}
          height={450}
        />

         {/* Combined Economic Indicators */}
<TimeSeriesChart
  data={(() => {
    const unemploymentSeries = historicalData?.UNRATE;
    const fedFundsSeries = historicalData?.FEDFUNDS;
    
    if (!unemploymentSeries?.data && !fedFundsSeries?.data) return [];
    
    // Create a map with all unique dates
    const dateMap = new Map();
    
    // Add unemployment data
    if (unemploymentSeries?.data) {
      unemploymentSeries.data.forEach(point => {
        const dateStr = point.date;
        if (!dateMap.has(dateStr)) {
          dateMap.set(dateStr, { date: dateStr });
        }
        dateMap.get(dateStr).unemployment = point.value;
      });
    }
    
    // Add fed funds data
    if (fedFundsSeries?.data) {
      fedFundsSeries.data.forEach(point => {
        const dateStr = point.date;
        if (!dateMap.has(dateStr)) {
          dateMap.set(dateStr, { date: dateStr });
        }
        dateMap.get(dateStr).fedFunds = point.value;
      });
    }
    
    // Convert to array and sort by date
    const combined = Array.from(dateMap.values()).sort((a, b) => 
      new Date(a.date) - new Date(b.date)
    );
    
    // Filter out entries with no data
    return combined.filter(d => d.unemployment !== undefined || d.fedFunds !== undefined);
  })()}
  series={[
    {
      dataKey: 'unemployment',
      name: 'Unemployment Rate (%)',
      color: '#10b981',
    },
    {
      dataKey: 'fedFunds',
      name: 'Fed Funds Rate (%)',
      color: '#f59e0b',
    },
  ]}
  recessions={recessions}
  title="Economic Indicators"
  yAxisLabel="Rate (%)"
  loading={loading}
  height={450}
/>
      </section>

      {/* Recession History */}
      <section className="recession-history">
        <h2>Historical Recession Periods</h2>
        <div className="recession-list">
          {recessions.map((recession, index) => (
            <div key={index} className="recession-item">
              <div className="recession-indicator"></div>
              <div className="recession-details">
                <h3>{recession.name || 'Recession'}</h3>
                <p>
                  {new Date(recession.start_date).toLocaleDateString()} -{' '}
                  {recession.end_date
                    ? new Date(recession.end_date).toLocaleDateString()
                    : 'Ongoing'}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="dashboard-footer">
        <p>
          Data sourced from FRED (Federal Reserve Economic Data) • Updated daily
        </p>
        <p className="disclaimer">
          This dashboard is for informational purposes only and does not constitute financial advice.
        </p>
      </footer>
    </div>
  );
};

export default Dashboard;
