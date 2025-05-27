import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { format, startOfWeek, endOfWeek, isWithinInterval } from 'date-fns';

const SHRINKAGE_THRESHOLDS = {
  safe: 10,
  warning: 15
};

const getColor = (value) => {
  if (value <= SHRINKAGE_THRESHOLDS.safe) return 'bg-green-200 text-green-800';
  if (value <= SHRINKAGE_THRESHOLDS.warning) return 'bg-yellow-200 text-yellow-800';
  return 'bg-red-200 text-red-800';
};

const L5Dashboard = ({ user }) => {
  const [calendar, setCalendar] = useState([]);
  const [filter, setFilter] = useState('monthly');

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line
  }, []);

  const fetchData = async () => {
    try {
      // Updated endpoint to match backend
      const res = await axios.get('/api/v1/leave/forecast/30days', {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      setCalendar(res.data.data?.forecast || []);
    } catch (err) {
      console.error('Error fetching L5 calendar');
    }
  };

  const filteredData = () => {
    if (filter === 'weekly') {
      const thisWeek = [startOfWeek(new Date()), endOfWeek(new Date())];
      return calendar.filter(item =>
        isWithinInterval(new Date(item.date), { start: thisWeek[0], end: thisWeek[1] })
      );
    }
    return calendar;
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-blue-900">L5 Availability Calendar</h1>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="border rounded px-3 py-1 text-sm"
        >
          <option value="monthly">Next 30 Days</option>
          <option value="weekly">This Week</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredData().map((entry) => (
          <div key={entry.date} className="bg-white rounded-xl shadow p-4">
            <h2 className="text-lg font-semibold text-gray-800">
              {format(new Date(entry.date), 'MMMM dd, yyyy')}
            </h2>
            <div className="mt-2 space-y-2">
              {Object.entries(entry.shrinkage_by_team || {}).map(([team, shrinkage]) => (
                <div
                  key={team}
                  className={`p-2 rounded text-sm font-medium flex justify-between ${getColor(shrinkage)}`}
                >
                  <span>{team}</span>
                  <span>{shrinkage}%</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* 👇 Add Widget Box */}
      {/* <Add /> */}
    </div>
  );
};

export default L5Dashboard;