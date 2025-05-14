import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

const COLORS = {
  Safe: '#34d399',
  Tight: '#fbbf24',
  Overbooked: '#f87171'
};

const UpcomingShrinkageChart = ({ user }) => {
  const [forecast, setForecast] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchShrinkage = async () => {
      try {
        const res = await axios.get('/availability/next-30-days', {
          headers: { Authorization: `Bearer ${user?.token}` }
        });
        const data = (res.data || []).map(d => ({
          ...d,
          day: format(new Date(d.date), 'dd MMM'),
          fill: COLORS[d.status] || '#d1d5db'
        }));
        setForecast(data);
      } catch (err) {
        console.error('Shrinkage forecast fetch failed:', err);
        setError('Failed to load forecast');
      }
    };

    if (user?.token) fetchShrinkage();
  }, [user?.token]);

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <h2 className="text-lg font-bold text-gray-800 mb-2">Upcoming 30-Day Shrinkage</h2>
      {error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={forecast}>
            <XAxis dataKey="day" fontSize={10} angle={-45} textAnchor="end" />
            <YAxis unit="%" />
            <Tooltip formatter={(v) => `${v.toFixed(1)}%`} />
            <Bar dataKey="shrinkage" isAnimationActive={false}>
              {forecast.map((entry, index) => (
                <cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default UpcomingShrinkageChart;
