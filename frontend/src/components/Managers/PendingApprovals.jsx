import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { FaCheckCircle, FaTimesCircle } from 'react-icons/fa';

const PendingApprovals = ({ user, refreshKey, colorTheme = 'vibrant', theme }) => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [confirmRejectId, setConfirmRejectId] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await axios.get('/api/v1/leave/pending-approvals', {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        setRequests(res.data.data?.pending_leaves || []);
      } catch {
        toast.error('Failed to fetch pending leaves');
      } finally {
        setLoading(false);
      }
    };
    if (user?.token) fetchData();
  }, [user, refreshKey]);

  const handleApprove = async (id) => {
    try {
      await axios.post(
        `/api/v1/leave/approve/${id}`,
        { action: 'Approved', comments: 'Approved via UI' },
        {
          headers: {
            Authorization: `Bearer ${user.token}`,
            'X-Request-ID': `ui-approve-${id}`,
          },
        }
      );
      toast.success('Leave approved');
      setRequests((prev) => prev.filter((r) => r.leave_id !== id));
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Approval failed');
    }
  };

  const handleFinalReject = async () => {
    try {
      await axios.post(
        `/api/v1/leave/approve/${confirmRejectId}`,
        { action: 'Rejected', comments: 'Rejected via UI' },
        {
          headers: {
            Authorization: `Bearer ${user.token}`,
            'X-Request-ID': `ui-reject-${confirmRejectId}`,
          },
        }
      );
      toast.success('Leave rejected');
      setRequests((prev) => prev.filter((r) => r.leave_id !== confirmRejectId));
      setConfirmRejectId(null);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Rejection failed');
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <div className={`p-2 rounded-lg bg-gradient-to-r ${theme?.cardAccent} shadow-sm`}>
          <FaCheckCircle className="h-5 w-5 text-white" />
        </div>
        <div>
          <h2 className={`text-xl font-bold ${theme?.text}`}>Pending Approvals</h2>
          <p className="text-sm text-gray-500">
            {loading ? 'Loading...' : `${requests.length} pending request(s)`}
          </p>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-10">
          <div className={`animate-spin h-6 w-6 border-b-2 ${theme.spinner} rounded-full`}></div>
          <span className={`ml-3 text-sm font-medium ${theme.text}`}>Fetching requests...</span>
        </div>
      ) : requests.length === 0 ? (
        <div className="text-center text-gray-500 py-10">No pending leave requests.</div>
      ) : (
        <div className="space-y-4 max-h-96 overflow-y-auto pr-1 custom-scroll">
          {requests.map((req) => (
            <div
              key={req.leave_id}
              className={`rounded-lg border border-gray-200 p-4 shadow-sm transition-all duration-200 hover:shadow-md hover:scale-[1.01] ${theme.cardGradient}`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className={`font-semibold ${theme.text}`}>{req.associate}</h3>
                  <p className="text-sm text-gray-600">
                    {format(new Date(req.start_date), 'dd MMM yyyy')} →{' '}
                    {format(new Date(req.end_date), 'dd MMM yyyy')}
                  </p>
                  <span className="inline-block mt-1 text-xs text-gray-400">
                    {req.leave_type}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleApprove(req.leave_id)}
                    className="flex items-center gap-1 px-3 py-1 text-xs text-white bg-green-600 rounded hover:bg-green-700"
                  >
                    <FaCheckCircle /> Approve
                  </button>
                  <button
                    onClick={() => setConfirmRejectId(req.leave_id)}
                    className="flex items-center gap-1 px-3 py-1 text-xs text-white bg-red-500 rounded hover:bg-red-600"
                  >
                    <FaTimesCircle /> Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmRejectId && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg p-6 w-96 space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">Confirm Rejection</h3>
            <p className="text-sm text-gray-600">Reject this leave request? This cannot be undone.</p>
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setConfirmRejectId(null)}
                className="px-4 py-2 text-sm bg-gray-100 rounded hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleFinalReject}
                className="px-4 py-2 text-sm bg-red-500 text-white rounded hover:bg-red-600"
              >
                Confirm Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PendingApprovals;
