import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { format } from 'date-fns';

const COLORS = {
  Safe: '#34d399',
  Tight: '#fbbf24',
  Overbooked: '#f87171'
};

const UpcomingShrinkageChart = ({ user, refreshKey, colorTheme = 'vibrant', theme }) => {
  const [forecast, setForecast] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchShrinkage = async () => {
      try {
        const res = await axios.get('/api/v1/leave/forecast/30days', {
          headers: { Authorization: `Bearer ${user?.token}` }
        });
        const data = (res.data.data?.forecast || []).map(d => ({
          ...d,
          day: format(new Date(d.date), 'dd MMM'),
          fill: COLORS[d.status] || '#d1d5db'
        }));
        setForecast(data);
        setError(null);
      } catch (err) {
        console.error('Shrinkage forecast fetch failed:', err);
        setError('Failed to load forecast');
      }
    };

    if (user?.token) fetchShrinkage();
  }, [user?.token, refreshKey]);

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <div className={`p-2 rounded-lg bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} shadow-sm`}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-6h13M9 7v1m0 4h1m4-4h1m-1 4h1M4 21h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v15a1 1 0 001 1z" />
          </svg>
        </div>
        <div>
          <h2 className={`text-xl font-bold ${theme?.text || 'text-indigo-700'} drop-shadow-sm`}>
            Upcoming 30-Day Shrinkage
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Daily shrinkage outlook to plan better
          </p>
        </div>
      </div>

      {/* Chart Content */}
      {error ? (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 p-4 rounded">{error}</div>
      ) : forecast.length === 0 ? (
        <div className="text-sm text-gray-500 italic text-center p-4">
          No shrinkage data available for upcoming days.
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 bg-white p-2 shadow-sm">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={forecast}>
              <XAxis dataKey="day" fontSize={10} angle={-45} textAnchor="end" />
              <YAxis unit="%" />
              <Tooltip formatter={(v) => `${v.toFixed(1)}%`} />
              <Bar dataKey="shrinkage" isAnimationActive={false}>
                {forecast.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default UpcomingShrinkageChart;
