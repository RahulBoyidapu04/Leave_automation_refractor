import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const TeamLeaveSummary = ({ user }) => {
  const [summary, setSummary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchTeamLeaveSummary = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await axios.get('/api/v1/leave/team/members', {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      setSummary(res.data.data?.members || []);
    } catch (err) {
      setError(true);
      toast.error('Failed to load team leave summary');
    } finally {
      setLoading(false);
    }
  }, [user.token]);

  useEffect(() => {
    fetchTeamLeaveSummary();
  }, [fetchTeamLeaveSummary]);

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-bold text-indigo-700 mb-4">
        Team Leave Summary (Optional Leaves)
      </h2>

      {loading ? (
        <div className="h-4 w-1/2 bg-gray-300 rounded animate-pulse" />
      ) : error ? (
        <div className="text-red-500 text-sm flex flex-col gap-2">
          <span>Could not load team leave summary.</span>
          <button
            className="bg-indigo-600 text-white px-3 py-1 rounded text-xs w-max"
            onClick={fetchTeamLeaveSummary}
          >
            Retry
          </button>
        </div>
      ) : summary.length === 0 ? (
        <p className="text-sm text-gray-500">No optional leaves recorded for your team.</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {summary.map((item, idx) => (
            <li
              key={idx}
              className="flex justify-between items-center border-b py-1"
            >
              <span className="font-medium text-gray-700">
                {item.username}
              </span>
              <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded-full text-xs font-semibold">
                {item.optional_leave_days ?? 0} days
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TeamLeaveSummary;