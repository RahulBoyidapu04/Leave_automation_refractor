import React, { useState } from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import { format } from 'date-fns';

const colorMap = {
  CL: 'bg-blue-500',
  AL: 'bg-yellow-500',
  Optional: 'bg-purple-500',
  Sick: 'bg-red-500',
  Default: 'bg-gray-400'
};

const AvailabilityCalendar = ({ shrinkageData }) => {
  const [selectedDate, setSelectedDate] = useState(new Date());

  const getTileClass = ({ date }) => {
    const dayData = shrinkageData?.find(d => d.date === format(date, 'yyyy-MM-dd'));
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
            .split(/[\s._-]/) // split by common separators
            .map(part => part.charAt(0))
            .join('')
            .toUpperCase();

          const color = colorMap[person.leave_type] || colorMap.Default;

          return (
            <span
              key={idx}
              title={`${person.username} (${person.leave_type})`}
              className={`text-white text-[10px] px-2 py-[2px] rounded-full font-bold ${color}`}
            >
              {initials}
            </span>
          );
        })}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <h2 className="text-lg font-bold text-purple-700 mb-2">Next 30-Day Availability</h2>
      <Calendar
        onChange={setSelectedDate}
        value={selectedDate}
        tileClassName={getTileClass}
        tileContent={getTileContent}
      />
      <p className="text-xs text-gray-500 mt-2">
        * Hover over initials to see who’s on leave and their leave type.
      </p>
    </div>
  );
};

export default AvailabilityCalendar;
