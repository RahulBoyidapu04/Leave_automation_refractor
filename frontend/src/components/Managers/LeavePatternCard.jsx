import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { FaCalendarAlt, FaUser } from 'react-icons/fa';

const months = [
  'All', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const LeavePatternCard = ({ user }) => {
  const [selectedMonth, setSelectedMonth] = useState('April');
  const [selectedUser, setSelectedUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetchAssociates();
  }, []);

  useEffect(() => {
    if (selectedUser) fetchLeavePattern();
  }, [selectedMonth, selectedUser]);

  const fetchAssociates = async () => {
    try {
      const res = await axios.get('/manager/associates', {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      setUsers(res.data);
      setSelectedUser(res.data[0]?.id);
    } catch (err) {
      console.error('Failed to fetch associates');
    }
  };

  const fetchLeavePattern = async () => {
    try {
      const res = await axios.get('/manager/associate-leave-pattern', {
        params: { user_id: selectedUser, month: selectedMonth },
        headers: { Authorization: `Bearer ${user.token}` }
      });
      setSummary(res.data);
    } catch (err) {
      console.error('Failed to fetch leave pattern');
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md p-6 space-y-5">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <FaCalendarAlt className="text-blue-600" />
          Leave Pattern Overview
        </h2>

        <select
          className="border border-gray-300 rounded px-3 py-1 text-sm bg-white"
          value={selectedMonth}
          onChange={(e) => setSelectedMonth(e.target.value)}
        >
          {months.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-600 flex items-center gap-2">
          <FaUser /> Select Associate
        </label>
        <select
          className="border border-gray-300 rounded px-3 py-2 w-full"
          value={selectedUser || ''}
          onChange={(e) => setSelectedUser(e.target.value)}
        >
          {users.map((u) => (
            <option key={u.id} value={u.id}>{u.username}</option>
          ))}
        </select>
      </div>

      {summary ? (
        <div className="bg-blue-50 rounded-lg p-4 shadow-inner space-y-2 text-sm">
          <p><span className="font-semibold text-gray-700">Username:</span> {summary.username}</p>
          <p><span className="font-semibold text-gray-700">CL Taken:</span> {summary.monthly_summary?.CL || 0}</p>
          <p><span className="font-semibold text-gray-700">AL Taken:</span> {summary.monthly_summary?.AL || 0}</p>
          <p><span className="font-semibold text-gray-700">Frequent Days:</span> {Object.keys(summary.frequent_days).join(', ') || 'N/A'}</p>
          <p><span className="font-semibold text-gray-700">Leave Dates:</span> {summary.leave_dates.join(', ')}</p>
        </div>
      ) : (
        <p className="text-sm text-gray-500 italic">No leave data available.</p>
      )}
    </div>
  );
};

export default LeavePatternCard;
