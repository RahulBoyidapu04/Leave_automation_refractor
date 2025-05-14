import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const ApplyLeaveCard = ({ user, onLeaveApplied }) => {
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [leaveType, setLeaveType] = useState('');
  const [backupPerson, setBackupPerson] = useState('');

  const applyLeave = async () => {
    if (!startDate || !endDate || !leaveType) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (startDate > endDate) {
      toast.error('Start date cannot be after end date');
      return;
    }

    try {
      const data = {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        leave_type: leaveType,
        backup_person: backupPerson
      };

      const res = await axios.post('/apply-leave', data, {
        headers: { Authorization: `Bearer ${user.token}` }
      });

      if (res.data.status === 'error' && res.data.message.includes('already have a leave request')) {
        toast.error('You already applied for these dates');
      } else {
        toast.success(res.data.message || 'Leave request submitted');
        onLeaveApplied?.(); // 🔁 Trigger parent to refresh leave list
        // Reset form
        setLeaveType('');
        setStartDate(null);
        setEndDate(null);
        setBackupPerson('');
      }
    } catch (err) {
      toast.error('Failed to apply for leave');
      console.error(err);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 transition hover:shadow-xl">
      <h2 className="text-xl font-bold text-purple-700 mb-4">Apply for Leave</h2>

      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700">Leave Type</label>
        <select
          value={leaveType}
          onChange={(e) => setLeaveType(e.target.value)}
          className="mt-1 w-full border rounded px-3 py-2 text-sm"
        >
          <option value="">Select</option>
          <option value="AL">Annual Leave</option>
          <option value="CL">Casual Leave</option>
          <option value="Sick">Sick Leave</option>
          <option value="Optional">Optional</option>
        </select>
      </div>

      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700">Start Date</label>
        <DatePicker
          selected={startDate}
          onChange={setStartDate}
          className="mt-1 w-full border rounded px-3 py-2 text-sm"
          dateFormat="yyyy-MM-dd"
        />
      </div>

      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700">End Date</label>
        <DatePicker
          selected={endDate}
          onChange={setEndDate}
          className="mt-1 w-full border rounded px-3 py-2 text-sm"
          dateFormat="yyyy-MM-dd"
        />
      </div>

      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700">Backup Person (optional)</label>
        <input
          value={backupPerson}
          onChange={(e) => setBackupPerson(e.target.value)}
          className="mt-1 w-full border rounded px-3 py-2 text-sm"
        />
      </div>

      <button
        className="bg-purple-600 text-white px-4 py-2 rounded w-full hover:bg-purple-700"
        onClick={applyLeave}
      >
        Submit
      </button>
    </div>
  );
};

export default ApplyLeaveCard;
