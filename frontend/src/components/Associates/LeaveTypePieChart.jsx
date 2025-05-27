import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import toast from 'react-hot-toast';

const COLORS = ['#34d399', '#fbbf24', '#60a5fa', '#f87171', '#a78bfa', '#fb923c'];

const LEAVE_SYMBOLS = {
  Annual: '🌴',
  Casual: '🏖️',
  Optional: '🎉',
  Sick: '🤒',
};

const normalizeType = (type) => {
  if (type === 'AL' || type.toLowerCase() === 'annual') return 'Annual';
  if (type === 'CL' || type.toLowerCase() === 'casual') return 'Casual';
  if (type === 'OL' || type.toLowerCase() === 'optional') return 'Optional';
  if (type.toLowerCase() === 'sick') return 'Sick';
  return type;
};

const renderLabel = ({ name, value }) => {
  return `${LEAVE_SYMBOLS[name] || ''} ${name}: ${value}`;
};

const LeaveTypePieChart = ({ user }) => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await axios.get('/api/v1/leave/balance', {
          headers: { Authorization: `Bearer ${user.token}` },
        });

        const summary = res.data.data?.leave_type_summary || {};
        const merged = {};
        Object.entries(summary).forEach(([type, value]) => {
          const norm = normalizeType(type);
          merged[norm] = (merged[norm] || 0) + value;
        });
        const chartData = Object.entries(merged).map(([type, value]) => ({
          type,
          value,
        }));
        setData(chartData);
      } catch {
        toast.error('Failed to load leave summary');
      }
    };

    fetchSummary();
  }, [user]);

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <h2 className="text-lg font-bold text-purple-600 mb-2">Leave Type Breakdown</h2>
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="type"
            cx="50%"
            cy="50%"
            outerRadius={110}
            label={renderLabel}
            labelLine={false}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LeaveTypePieChart;