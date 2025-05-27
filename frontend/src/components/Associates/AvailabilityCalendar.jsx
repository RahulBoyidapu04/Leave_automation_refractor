import React, { useEffect, useState } from 'react';
import axios from 'axios';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import { format, isBefore } from 'date-fns';

const colorMap = {
  CL: 'bg-blue-500',
  AL: 'bg-yellow-500',
  Optional: 'bg-purple-500',
  Sick: 'bg-red-500',
  Default: 'bg-gray-400'
};

const AvailabilityCalendar = ({ user }) => {
  const [shrinkageData, setShrinkageData] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchShrinkage = async () => {
      try {
        const res = await axios.get('/api/v1/leave/forecast/30days', {
          headers: { Authorization: `Bearer ${user?.token}` }
        });
        const forecast = res.data.data?.forecast || res.data.forecast || res.data;
        setShrinkageData(forecast);
        console.log('ShrinkageData:', forecast);
      } catch (err) {
        setError('Failed to load availability data');
      }
    };
    if (user?.token) fetchShrinkage();
  }, [user?.token]);

  const today = new Date();

  // Use string comparison for date matching
  const getTileClass = ({ date }) => {
    if (isBefore(date, today)) {
      return 'bg-gray-100 text-gray-400 cursor-not-allowed';
    }
    const formattedDate = format(date, 'yyyy-MM-dd');
    const dayData = shrinkageData?.find(d => d.date === formattedDate);
    if (!dayData) return '';
    if (dayData.status === 'Safe') return 'bg-green-100';
    if (dayData.status === 'Tight') return 'bg-yellow-100';
    if (dayData.status === 'Overbooked') return 'bg-red-100';
    return '';
  };

  const getTileContent = ({ date }) => {
    const formattedDate = format(date, 'yyyy-MM-dd');
    const dayData = shrinkageData?.find(d => d.date === formattedDate);

    if (!dayData || !Array.isArray(dayData.on_leave) || dayData.on_leave.length === 0) {
      return null;
    }

    return (
      <div className="flex flex-wrap justify-center gap-1 mt-1">
        {dayData.on_leave.map((person, idx) => {
          const initials = person.username
            .split(/[\s._-]/)
            .map(part => part.charAt(0))
            .join('')
            .toUpperCase();

          const color = colorMap[person.leave_type] || colorMap.Default;

          return (
            <span
              key={idx}
              className={`relative group text-white text-[10px] px-2 py-[2px] rounded-full font-bold ${color}`}
            >
              {initials}
              <span className="absolute z-10 left-1/2 -translate-x-1/2 mt-1 hidden group-hover:block bg-black text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                {person.username} ({person.leave_type})
              </span>
            </span>
          );
        })}
      </div>
    );
  };

  const tileDisabled = ({ date }) => isBefore(date, today);

  // --- Leave type breakdown for selected date ---
  const formattedSelectedDate = format(selectedDate, 'yyyy-MM-dd');
  const selectedDayData = shrinkageData?.find(d => d.date === formattedSelectedDate);

  const leaveTypeSummary = {};
  if (selectedDayData && Array.isArray(selectedDayData.on_leave)) {
    selectedDayData.on_leave.forEach(person => {
      const type = person.leave_type || 'Unknown';
      leaveTypeSummary[type] = (leaveTypeSummary[type] || 0) + 1;
    });
  }
  const pieData = Object.entries(leaveTypeSummary).map(([type, value]) => ({
    type,
    value,
  }));

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <h2 className="text-lg font-bold text-purple-700 mb-2">Next 30-Day Availability</h2>
      {error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : (
        <>
          <Calendar
            onChange={setSelectedDate}
            value={selectedDate}
            tileClassName={getTileClass}
            tileContent={getTileContent}
            tileDisabled={tileDisabled}
          />
          <p className="text-xs text-gray-500 mt-2">
            * Hover over initials to see who’s on leave and their leave type.
          </p>
          {/* Leave type breakdown for selected date */}
          {pieData.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-semibold mb-1">
                Leave Type Breakdown for {formattedSelectedDate}
              </h3>
              <ul className="flex flex-wrap gap-2">
                {pieData.map((item, idx) => (
                  <li key={item.type} className="flex items-center gap-1">
                    <span
                      className={`inline-block w-3 h-3 rounded-full ${colorMap[item.type] || colorMap.Default}`}
                    ></span>
                    <span className="text-xs">{item.type}: {item.value}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AvailabilityCalendar;