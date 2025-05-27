import React, { useEffect, useState } from 'react';
import axios from 'axios';

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
          headers: { Authorization: `Bearer ${user?.token}` },
        });
        setShrinkage(res.data.data || {});
        setError(null);
      } catch (err) {
        console.error('[TodayShrinkage] Error:', err.response?.data || err.message);
        setError('Failed to fetch today’s shrinkage');
      } finally {
        setLoading(false);
      }
    };

    if (user?.token) fetchTodayShrinkage();
    else {
      setLoading(false);
      setError('User not authenticated');
    }
  }, [user, today, refreshKey]);

  const getStatus = (value) => {
    if (value < 6) return { label: 'Safe', color: 'text-green-700', icon: '✅' };
    if (value <= 10) return { label: 'Tight', color: 'text-yellow-700', icon: '⚠️' };
    return { label: 'Overbooked', color: 'text-red-700', icon: '❌' };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className={`animate-spin rounded-full h-6 w-6 border-b-2 ${theme?.spinner || 'border-indigo-500'}`} />
        <span className={`ml-3 text-sm ${theme?.text || 'text-indigo-700'}`}>Loading shrinkage...</span>
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

  const status = getStatus(shrinkage?.shrinkage || 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} shadow-sm`}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-6h13M9 7v1m0 4h1m4-4h1m-1 4h1M4 21h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v15a1 1 0 001 1z" />
            </svg>
          </div>
          <div>
            <h2 className={`text-xl font-bold ${theme?.text || 'text-indigo-700'} drop-shadow-sm`}>
              Today’s Shrinkage
            </h2>
            <p className="text-sm text-gray-500 mt-1">{today}</p>
          </div>
        </div>

        <div className={`px-3 py-1 rounded-full text-xs font-medium ${status.color} bg-white border shadow-sm`}>
          {status.icon} {status.label}
        </div>
      </div>

      {/* Metric Block */}
      <div className="text-center space-y-1">
        <p className="text-4xl font-extrabold text-gray-800">{shrinkage?.shrinkage?.toFixed(2)}%</p>
        {shrinkage?.note && (
          <p className="text-xs text-gray-500 italic">{shrinkage.note}</p>
        )}
      </div>
    </div>
  );
};

export default TodayShrinkageCard;
