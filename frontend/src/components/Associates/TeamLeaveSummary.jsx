import React, { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const TeamLeaveSummary = ({ user }) => {
  const [summary, setSummary] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTeamLeaveSummary = async () => {
      try {
        const res = await axios.get('/availability/team-optional-summary', {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        setSummary(res.data);
      } catch (err) {
        toast.error('Failed to load team leave summary');
      } finally {
        setLoading(false);
      }
    };

    fetchTeamLeaveSummary();
  }, [user]);

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-bold text-indigo-700 mb-4">
        Team Leave Summary (Optional Leaves)
      </h2>

      {loading ? (
        <div className="h-4 w-1/2 bg-gray-300 rounded animate-pulse" />
      ) : summary.length === 0 ? (
        <p className="text-sm text-gray-500">No optional leaves recorded.</p>
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
                {item.optional_leave_days} days
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TeamLeaveSummary;
