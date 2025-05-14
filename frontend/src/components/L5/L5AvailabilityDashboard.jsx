import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ShrinkageLineChart from './ShrinkageLineChart';
import ShrinkageTable from './ShrinkageTable';

const L5AvailabilityDashboard = ({ user }) => {
  const [calendarData, setCalendarData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get('/admin/availability/l5-next-30-days', {
          headers: { Authorization: `Bearer ${user.token}` }
        });
        setCalendarData(res.data);
      } catch (err) {
        console.error('Failed to fetch shrinkage data', err);
      }
    };

    fetchData();
  }, [user.token]);

  return (
    <div className="space-y-6">
      <ShrinkageLineChart data={calendarData} />
      <ShrinkageTable data={calendarData} />
    </div>
  );
};

export default L5AvailabilityDashboard;
