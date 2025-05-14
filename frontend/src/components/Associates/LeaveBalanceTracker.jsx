import React, { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { FaCheckCircle } from 'react-icons/fa';

const LeaveBalanceTracker = ({ user }) => {
  const [used, setUsed] = useState(0);
  const [total, setTotal] = useState(12); // Can be dynamic later
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const res = await axios.get('/leave/summary', {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        setUsed(res.data.total_days || 0);
      } catch (err) {
        toast.error('Failed to load leave balance');
      } finally {
        setLoading(false);
      }
    };

    fetchBalance();
  }, [user]);

  const percent = Math.min((used / total) * 100, 100);
  const color =
    percent < 50 ? 'bg-green-400' : percent < 80 ? 'bg-yellow-400' : 'bg-red-400';

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-bold text-purple-700 flex items-center gap-2">
          <FaCheckCircle className="text-purple-500" />
          Leave Balance
        </h2>
        {!loading && (
          <span className="text-sm text-gray-500">
            {used} / {total} Used
          </span>
        )}
      </div>

      <div className="w-full bg-gray-200 h-4 rounded-full overflow-hidden relative">
        {loading ? (
          <div className="h-4 bg-gray-300 animate-pulse w-1/2" />
        ) : (
          <div
            className={`h-4 ${color} transition-all duration-500`}
            style={{ width: `${percent}%` }}
          />
        )}
      </div>
    </div>
  );
};

export default LeaveBalanceTracker;
