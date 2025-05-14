import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, Tooltip } from 'recharts';
import { format } from 'date-fns';
import { FaHeartbeat } from 'react-icons/fa';

const TeamShrinkageChart = ({ user }) => {
  const [shrinkage, setShrinkage] = useState(null);
  const [error, setError] = useState(false);

  const getShrinkage = async () => {
    const today = format(new Date(), 'yyyy-MM-dd');
    try {
      const res = await axios.get('/team-shrinkage', {
        params: { date_str: today },
        headers: { Authorization: `Bearer ${user.token}` },
      });
      setShrinkage(res.data?.shrinkage ?? 0);
    } catch (err) {
      console.error('Failed to fetch shrinkage', err);
      setShrinkage(0);  // fallback to 0
      setError(true);
    }
  };

  useEffect(() => {
    getShrinkage();
  }, []);

  const level =
    shrinkage <= 4 ? 'Safe' : shrinkage <= 10 ? 'Tight' : 'Overbooked';
  const color =
    shrinkage <= 4 ? '#34d399' : shrinkage <= 10 ? '#fbbf24' : '#f87171';

  const data = [
    { name: 'On Leave', value: shrinkage ?? 0 },
    { name: 'Available', value: 100 - (shrinkage ?? 0) },
  ];

  return (
    <div className="bg-white rounded-xl shadow-md p-6 text-center hover:shadow-lg transition duration-300">
      <h2 className="text-lg font-bold text-blue-700 mb-2 flex justify-center items-center gap-2">
        <FaHeartbeat className="text-pink-500" />
        Today’s Shrinkage
      </h2>

      <PieChart width={220} height={220}>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={3}
          startAngle={90}
          endAngle={-270}
          dataKey="value"
        >
          <Cell fill={color} />
          <Cell fill="#e5e7eb" />
        </Pie>
        <Tooltip formatter={(val) => `${(val ?? 0).toFixed(1)}%`} />
      </PieChart>

      <p className="text-sm text-gray-500 mt-3">{format(new Date(), 'PPP')}</p>
      <p className="text-sm font-semibold mt-1" style={{ color }}>
        ● {level} ({shrinkage ?? 0}%)
      </p>
      {error && <p className="text-xs text-red-500 mt-2">Failed to fetch data</p>}
    </div>
  );
};

export default TeamShrinkageChart;
