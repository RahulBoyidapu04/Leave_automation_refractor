import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Label
} from 'recharts';

const COLORS = {
  Safe: '#34d399',
  Tight: '#fbbf24',
  Overbooked: '#f87171'
};

const AvailableDaysChart = ({ token, shrinkageData: propShrinkageData }) => {
  const [shrinkageData, setShrinkageData] = useState(propShrinkageData || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (propShrinkageData) return; // Use prop if provided
    if (!token) return;
    setLoading(true);
    axios
      .get('/api/v1/leave/forecast/30days', {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => {
        setShrinkageData(res.data.data.forecast || []);
        setError('');
      })
      .catch(err => {
        setError('Failed to fetch shrinkage data');
        setShrinkageData([]);
      })
      .finally(() => setLoading(false));
  }, [token, propShrinkageData]);

  const counts = { Safe: 0, Tight: 0, Overbooked: 0 };
  (shrinkageData || []).forEach((item) => {
    if (item.status === 'Safe') counts.Safe++;
    else if (item.status === 'Tight') counts.Tight++;
    else if (item.status === 'Overbooked') counts.Overbooked++;
  });

  const totalDays = counts.Safe + counts.Tight + counts.Overbooked;

  const data = Object.entries(counts)
    .filter(([_, value]) => value > 0)
    .map(([name, value]) => ({
      name,
      value,
      fill: COLORS[name],
      label: `${name}: ${value} day${value > 1 ? 's' : ''}`
    }));

  const cardBg =
    totalDays === 0
      ? 'bg-white'
      : counts.Safe >= counts.Tight && counts.Safe >= counts.Overbooked
      ? 'bg-green-50'
      : counts.Tight >= counts.Overbooked
      ? 'bg-yellow-50'
      : 'bg-red-50';

  if (loading) {
    return (
      <div className={`rounded-xl shadow p-4 min-h-[200px] flex items-center justify-center bg-white`}>
        <span className="text-sm text-gray-600">Loading chart...</span>
      </div>
    );
  }

  if (error) {
    return <div className="bg-white rounded-xl shadow p-4 text-red-600">{error}</div>;
  }

  return (
    <div className={`rounded-xl shadow p-4 ${cardBg}`}>
      <h2 className="text-lg font-bold text-gray-800 mb-2">📊 Available Days (Next 30)</h2>
      {totalDays === 0 ? (
        <p className="text-sm text-gray-500">No shrinkage data found for the next 30 days.</p>
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={4}
              dataKey="value"
              label={({ name, value }) => `${value}d`}
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.fill} />
              ))}
              <Label
                value={`Total: ${totalDays} Days`}
                position="center"
                fill="#374151"
                fontSize={14}
              />
            </Pie>
            <Tooltip
              formatter={(value, name) => [`${value} day${value > 1 ? 's' : ''}`, `${name} Days`]}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default AvailableDaysChart;