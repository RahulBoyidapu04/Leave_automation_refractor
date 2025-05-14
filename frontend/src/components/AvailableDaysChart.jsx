import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

const COLORS = {
  Safe: '#34d399',        // Tailwind green-400
  Tight: '#fbbf24',       // Tailwind amber-400
  Overbooked: '#f87171'   // Tailwind red-400
};

const AvailableDaysChart = ({ user }) => {
  const [shrinkageData, setShrinkageData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchShrinkage = async () => {
      setLoading(true);
      setError('');
      try {
        const res = await axios.get('/availability/next-30-days', {
          headers: { Authorization: `Bearer ${user?.token}` }
        });
        setShrinkageData(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        setError('Failed to fetch shrinkage forecast');
        setShrinkageData([]);
        console.error('Failed to fetch shrinkage forecast', err);
      } finally {
        setLoading(false);
      }
    };
    if (user?.token) fetchShrinkage();
  }, [user?.token]);

  const counts = { Safe: 0, Tight: 0, Overbooked: 0 };
  (shrinkageData || []).forEach((item) => {
    if (item.status === 'Safe') counts.Safe++;
    else if (item.status === 'Tight') counts.Tight++;
    else if (item.status === 'Overbooked') counts.Overbooked++;
  });

  const data = Object.entries(counts).map(([name, value]) => ({
    name,
    value,
    fill: COLORS[name]
  }));

  if (loading) {
    return <div className="bg-white rounded-xl shadow p-4">Loading chart...</div>;
  }

  if (error) {
    return <div className="bg-white rounded-xl shadow p-4 text-red-600">{error}</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <h2 className="text-lg font-bold text-gray-800 mb-2">Available Days (Next 30)</h2>
      <PieChart width={250} height={200}>
        <Pie
          data={data}
          cx={120}
          cy={100}
          innerRadius={40}
          outerRadius={70}
          paddingAngle={5}
          dataKey="value"
          label={({ name, percent }) => `${name} ${Math.round(percent * 100)}%`}
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.fill} />
          ))}
        </Pie>
        <Tooltip />
        <Legend layout="horizontal" align="center" verticalAlign="bottom" />
      </PieChart>
    </div>
  );
};

export default AvailableDaysChart;
