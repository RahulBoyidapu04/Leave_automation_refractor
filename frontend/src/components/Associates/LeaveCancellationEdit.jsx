import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const LeaveCancellationAndEdit = ({ user, selectedLeave, onClose, onUpdate }) => {
  const [form, setForm] = useState({
    leave_type: '',
    start_date: '',
    end_date: '',
    backup_person: ''
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedLeave) {
      setForm({
        leave_type: selectedLeave.leave_type,
        start_date: selectedLeave.start_date,
        end_date: selectedLeave.end_date,
        backup_person: selectedLeave.backup_person || ''
      });
    }
  }, [selectedLeave]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };

  const handleUpdate = async () => {
    setLoading(true);
    try {
      await axios.put(`/leave/${selectedLeave.id}`, form, {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      toast.success('Leave updated');
      onUpdate();   // triggers parent fetch
      onClose();    // closes modal
    } catch (err) {
      toast.error('Failed to update leave');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    setLoading(true);
    try {
      await axios.delete(`/leave/${selectedLeave.id}`, {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      toast.success('Leave cancelled');
      onUpdate();
      onClose();
    } catch (err) {
      toast.error('Failed to cancel leave');
    } finally {
      setLoading(false);
    }
  };

  if (!selectedLeave) return null;

  return (
    <div className="bg-white rounded-xl shadow p-4 space-y-4">
      <h2 className="text-lg font-bold text-gray-800">Edit / Cancel Leave</h2>

      <div className="space-y-2">
        <label className="block text-sm text-gray-600">Leave Type</label>
        <select
          name="leave_type"
          value={form.leave_type}
          onChange={handleChange}
          className="w-full border p-2 rounded"
        >
          <option value="CL">CL</option>
          <option value="AL">AL</option>
          <option value="Optional">Optional</option>
          <option value="Sick">Sick</option>
        </select>
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <label className="block text-sm text-gray-600">Start Date</label>
          <input
            type="date"
            name="start_date"
            value={form.start_date}
            onChange={handleChange}
            className="w-full border p-2 rounded"
          />
        </div>
        <div className="flex-1">
          <label className="block text-sm text-gray-600">End Date</label>
          <input
            type="date"
            name="end_date"
            value={form.end_date}
            onChange={handleChange}
            className="w-full border p-2 rounded"
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="block text-sm text-gray-600">Backup Person</label>
        <input
          type="text"
          name="backup_person"
          value={form.backup_person}
          onChange={handleChange}
          className="w-full border p-2 rounded"
        />
      </div>

      <div className="flex gap-4">
        <button
          onClick={handleUpdate}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700"
        >
          Save Changes
        </button>
        <button
          onClick={handleCancel}
          disabled={loading}
          className="bg-red-600 text-white px-4 py-2 rounded shadow hover:bg-red-700"
        >
          Cancel Leave
        </button>
        <button
          onClick={onClose}
          className="ml-auto text-gray-600 underline text-sm"
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default LeaveCancellationAndEdit;
