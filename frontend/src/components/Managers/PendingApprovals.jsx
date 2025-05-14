import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import { FaCheckCircle, FaTimesCircle } from 'react-icons/fa';

const PendingApprovals = ({ user }) => {
  const [requests, setRequests] = useState([]);
  const [confirmRejectId, setConfirmRejectId] = useState(null);

  // Fetch pending leaves on mount
  useEffect(() => {
    fetchPending();
    // eslint-disable-next-line
  }, []);

  const fetchPending = async () => {
    try {
      const res = await axios.get('/manager/pending-leaves', {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      setRequests(res.data);
    } catch (err) {
      toast.error('Failed to fetch pending leaves');
    }
  };

  const handleApprove = async (id) => {
    try {
      await axios.post('/manager/leave-decision', {
        leave_id: id,
        decision: 'approved'
      }, {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      toast.success('Leave approved successfully');
      fetchPending();
    } catch (err) {
      toast.error('Failed to approve leave');
    }
  };

  const handleConfirmReject = (id) => {
    setConfirmRejectId(id);
  };

  const handleCancelReject = () => {
    setConfirmRejectId(null);
  };

  const handleFinalReject = async () => {
    try {
      await axios.post('/manager/leave-decision', {
        leave_id: confirmRejectId,
        decision: 'rejected'
      }, {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      toast.error('Leave rejected');
      setConfirmRejectId(null);
      fetchPending();
    } catch (err) {
      toast.error('Failed to reject leave');
    }
  };

  return (
    <div className="bg-white rounded-xl shadow p-6 space-y-4 relative">
      <h2 className="text-xl font-bold text-blue-700 mb-2">Pending Approvals</h2>

      {requests.length === 0 ? (
        <p className="text-sm text-gray-500">No pending leave requests.</p>
      ) : (
        <div className="space-y-3 max-h-80 overflow-y-auto pr-1 custom-scroll">
          {requests.map((req) => (
            <div
              key={req.leave_id}
              className="flex justify-between items-center border-b pb-2 hover:bg-gray-50 rounded-md px-2 transition"
            >
              <div>
                <p className="font-semibold text-gray-700">
                  {req.associate} <span className="text-sm text-gray-400">({req.leave_type})</span>
                </p>
                <p className="text-sm text-gray-500">
                  {format(new Date(req.start_date), 'dd MMM yyyy')} →{' '}
                  {format(new Date(req.end_date), 'dd MMM yyyy')}
                </p>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleApprove(req.leave_id)}
                  className="flex items-center gap-1 px-3 py-1 text-sm text-white bg-green-600 rounded hover:bg-green-700"
                >
                  <FaCheckCircle /> Approve
                </button>
                <button
                  onClick={() => handleConfirmReject(req.leave_id)}
                  className="flex items-center gap-1 px-3 py-1 text-sm text-white bg-red-500 rounded hover:bg-red-600"
                >
                  <FaTimesCircle /> Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 🔒 Modal */}
      {confirmRejectId && (
        <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-96 space-y-4">
            <h3 className="text-lg font-bold text-gray-800">Confirm Rejection</h3>
            <p className="text-sm text-gray-600">
              Are you sure you want to reject this leave request? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={handleCancelReject}
                className="px-4 py-2 text-sm bg-gray-200 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={handleFinalReject}
                className="px-4 py-2 text-sm text-white bg-red-500 rounded hover:bg-red-600"
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PendingApprovals;