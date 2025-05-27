import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';

const allowedTypes = [
  { value: 'CL', label: 'Casual Leave (CL)' },
  { value: 'AL', label: 'Annual Leave (AL)' },
  { value: 'SL', label: 'Sick Leave (SL)' },
  { value: 'Sick', label: 'Sick' },
  { value: 'Emergency', label: 'Emergency' },
  { value: 'Maternity', label: 'Maternity' }
];

const ApplyLeaveCard = ({ user, onLeaveApplied }) => {
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [leaveType, setLeaveType] = useState('');
  const [backupPerson, setBackupPerson] = useState('');
  const [isHalfDay, setIsHalfDay] = useState(false);

  // Helper function to format dates properly without timezone issues
  const formatDateForAPI = (date) => {
    if (!date) return null;
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const applyLeave = async () => {
    if (!startDate || !endDate || !leaveType) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (startDate > endDate) {
      toast.error('Start date cannot be after end date');
      return;
    }

    // Validate leave type
    if (!allowedTypes.map(t => t.value).includes(leaveType)) {
      toast.error('Invalid leave type selected');
      return;
    }

    try {
      const data = {
        user_id: user.id,
        start_date: formatDateForAPI(startDate),
        end_date: formatDateForAPI(endDate),
        leave_type: leaveType,
        backup_person: backupPerson || null,
        is_half_day: isHalfDay
      };

      await axios.post('/api/v1/leave/apply', data, {
        headers: {
          Authorization: `Bearer ${user.token}`,
          'Content-Type': 'application/json'
        }
      });

      toast.success('Leave applied successfully');
      onLeaveApplied(); // Refresh leaves list
      setStartDate(null);
      setEndDate(null);
      setLeaveType('');
      setBackupPerson('');
      setIsHalfDay(false);
    } catch (error) {
      console.error(error);
      console.log(error.response?.data);
      const detail = error.response?.data?.detail;
      let errorMsg = 'Failed to apply for leave';
      if (Array.isArray(detail)) {
        errorMsg = detail.map(d => d.msg).join(', ');
      } else if (typeof detail === 'string') {
        errorMsg = detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      toast.error(errorMsg);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">Apply for Leave</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Leave Type</label>
          <select
            value={leaveType}
            onChange={(e) => setLeaveType(e.target.value)}
            className="w-full border p-2 rounded"
          >
            <option value="">Select leave type</option>
            {allowedTypes.map(type => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium">Start Date</label>
          <DatePicker
            selected={startDate}
            onChange={(date) => setStartDate(date)}
            className="w-full border p-2 rounded"
            dateFormat="yyyy-MM-dd"
            placeholderText="Select start date"
          />
        </div>

        <div>
          <label className="block text-sm font-medium">End Date</label>
          <DatePicker
            selected={endDate}
            onChange={(date) => setEndDate(date)}
            className="w-full border p-2 rounded"
            dateFormat="yyyy-MM-dd"
            placeholderText="Select end date"
            minDate={startDate}
          />
        </div>

        <div>
          <label className="block text-sm font-medium">Backup Person (optional)</label>
          <input
            type="text"
            value={backupPerson}
            onChange={(e) => setBackupPerson(e.target.value)}
            className="w-full border p-2 rounded"
            placeholder="Enter backup person name"
          />
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            checked={isHalfDay}
            onChange={() => setIsHalfDay(!isHalfDay)}
            className="mr-2"
          />
          <label className="text-sm">Is this a half-day leave?</label>
        </div>

        <button
          onClick={applyLeave}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Submit Leave
        </button>
      </div>
    </div>
  );
};

export default ApplyLeaveCard;