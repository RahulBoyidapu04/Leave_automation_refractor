// L5CalendarView.jsx - full code previously providedimport React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LabelList } from 'recharts';

const COLOR_MAP = (value) => {
  if (value < 10) return '#22c55e'; // Safe
  if (value <= 15) return '#facc15'; // Tight
  return '#ef4444'; // Overbooked
};

const L5CalendarView = ({ user }) => {
  const [data, setData] = useState([]);
  const [view, setView] = useState('monthly'); // 'weekly' or 'monthly'

  const fetchData = async () => {
    try {
      const res = await axios.get('/admin/availability/next-30-days', {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch shrinkage data', err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const processChartData = () => {
    const grouped = {};

    data.forEach((entry) => {
      const week = `Week ${Math.floor((new Date(entry.date).getDate() - 1) / 7) + 1}`;
      Object.entries(entry.shrinkage_by_team).forEach(([team, shrinkage]) => {
        const key = view === 'weekly' ? week : 'Full Month';
        if (!grouped[key]) grouped[key] = {};
        if (!grouped[key][team]) grouped[key][team] = [];
        grouped[key][team].push(shrinkage);
      });
    });

    return Object.entries(grouped).map(([period, teams]) => {
      const entry = { period };
      Object.entries(teams).forEach(([team, values]) => {
        const avg = values.reduce((a, b) => a + b, 0) / values.length;
        entry[team] = parseFloat(avg.toFixed(2));
      });
      return entry;
    });
  };

  const chartData = processChartData();
  const teamKeys = chartData.length > 0 ? Object.keys(chartData[0]).filter((k) => k !== 'period') : [];

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-blue-800">Team Shrinkage Forecast</h2>
        <select
          className="border px-3 py-1 rounded text-sm"
          value={view}
          onChange={(e) => setView(e.target.value)}
        >
          <option value="weekly">Weekly View</option>
          <option value="monthly">Monthly View</option>
        </select>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
          <XAxis dataKey="period" />
          <YAxis unit="%" />
          <Tooltip />
          <Legend />
          {teamKeys.map((team, idx) => (
            <Bar key={team} dataKey={team} stackId="a" fill="#ddd">
              <LabelList
                dataKey={team}
                position="top"
                formatter={(val) => `${val}%`}
                fill={(val) => COLOR_MAP(val)}
              />
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 text-sm text-gray-600">
        <p><span className="text-green-600 font-semibold">Safe</span>: &lt; 10%</p>
        <p><span className="text-yellow-500 font-semibold">Tight</span>: 10% – 15%</p>
        <p><span className="text-red-500 font-semibold">Overbooked</span>: &gt; 15%</p>
      </div>
    </div>
  );
};

export default L5CalendarView;
