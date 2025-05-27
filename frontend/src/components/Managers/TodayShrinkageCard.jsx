import React, { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const TodayShrinkageCard = ({ user, refreshKey, colorTheme = 'vibrant', theme }) => {
  const [shrinkage, setShrinkage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const today = new Date().toISOString().split('T')[0];

  useEffect(() => {
    const fetchTodayShrinkage = async () => {
      try {
        const res = await axios.get('/api/v1/leave/dashboard/shrinkage', {
          params: { date: today },
          headers: { Authorization: `Bearer ${user?.token}` }
        });
        setShrinkage(res.data.data || {});
        setError(null);
      } catch (err) {
        setError('Failed to fetch today’s shrinkage');
      } finally {
        setLoading(false);
      }
    };

    if (user?.token) fetchTodayShrinkage();
    else {
      setError('User not authenticated');
      setLoading(false);
    }
  }, [user, today, refreshKey]);

  const getStatus = (value) => {
    if (value < 6) return { label: 'Safe', color: 'text-green-600', icon: '✅' };
    if (value <= 10) return { label: 'Tight', color: 'text-amber-600', icon: '⚠️' };
    return { label: 'Overbooked', color: 'text-red-600', icon: '❌' };
  };

  const status = getStatus(shrinkage?.shrinkage || 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className={`animate-spin rounded-full h-6 w-6 border-b-2 ${theme?.spinner || 'border-indigo-500'}`}></div>
        <span className={`ml-3 text-sm ${theme?.text || 'text-indigo-700'}`}>
          Loading today’s shrinkage...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded">
        ⚠️ {error}
      </div>
    );
  }

  return (
    <div className={`p-6 space-y-4 rounded-lg shadow-md border-t-4 border-transparent bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} backdrop-blur-sm`}>
      <div className="flex items-center justify-between">
        <h2 className={`text-lg font-bold ${theme?.text || 'text-indigo-700'}`}>
          Today's Shrinkage
        </h2>
        <span className="text-sm text-gray-500">{today}</span>
      </div>

      <div className="text-center space-y-2">
        <p className="text-4xl font-extrabold text-gray-800">
          {shrinkage?.shrinkage?.toFixed(2)}%
        </p>
        <p className={`text-sm font-semibold ${status.color}`}>
          {status.icon} {status.label}
        </p>
        {shrinkage?.note && (
          <p className="text-xs text-gray-500 italic">{shrinkage.note}</p>
        )}
      </div>
    </div>
  );
};

export default TodayShrinkageCard;
