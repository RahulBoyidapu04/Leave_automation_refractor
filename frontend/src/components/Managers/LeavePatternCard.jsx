import React, { useEffect, useState } from 'react';
import axios from 'axios';

const months = [
  'All', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const currentMonthName = months[new Date().getMonth() + 1];

const LeavePatternCard = ({ user, refreshKey, colorTheme = 'vibrant', theme }) => {
  const [selectedMonth, setSelectedMonth] = useState(currentMonthName);
  const [selectedUser, setSelectedUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [patternLoading, setPatternLoading] = useState(false);

  useEffect(() => {
    fetchAssociates();
  }, [user, refreshKey]);

  useEffect(() => {
    if (selectedUser) fetchLeavePattern();
  }, [selectedMonth, selectedUser, user, refreshKey]);

  const fetchAssociates = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/v1/leave/team/members', {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      const members = res.data.data?.members || [];
      setUsers(members);
      setSelectedUser(members[0]?.id);
    } catch (err) {
      console.error('Failed to fetch associates');
    } finally {
      setLoading(false);
    }
  };

  const fetchLeavePattern = async () => {
    setPatternLoading(true);
    try {
      const res = await axios.get('/api/v1/leave/analytics', {
        params: { user_id: selectedUser, month: selectedMonth },
        headers: { Authorization: `Bearer ${user.token}` }
      });
      setSummary(res.data.data || null);
    } catch (err) {
      console.error('Failed to fetch leave pattern');
      setSummary(null);
    } finally {
      setPatternLoading(false);
    }
  };

  // Loading spinner component
  const LoadingSpinner = ({ size = 'sm', text = 'Loading...' }) => (
    <div className="flex items-center justify-center py-4">
      <div className={`animate-spin rounded-full border-b-2 ${theme?.spinner || 'border-indigo-500'} ${size === 'sm' ? 'h-5 w-5' : 'h-8 w-8'}`}></div>
      <span className={`ml-2 text-sm ${theme?.text || 'text-indigo-700'}`}>
        {text}
      </span>
    </div>
  );

  // Empty state component
  const EmptyState = () => (
    <div className="flex flex-col items-center justify-center py-8">
      <div className={`p-3 rounded-full ${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} mb-3`}>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          className={`h-6 w-6 ${theme?.icon || 'text-indigo-500'} opacity-60`}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <p className={`text-sm font-medium ${theme?.text || 'text-indigo-700'} mb-1`}>
        No Leave Data
      </p>
      <p className="text-xs text-gray-500 text-center">
        No leave pattern available for the selected period.
      </p>
    </div>
  );

  // Get leave type color
  const getLeaveTypeColor = (type) => {
    const colors = {
      'CL': 'text-red-600 bg-red-50 border-red-200',
      'AL': 'text-green-600 bg-green-50 border-green-200',
      'SL': 'text-orange-600 bg-orange-50 border-orange-200',
      'ML': 'text-pink-600 bg-pink-50 border-pink-200',
      'PL': 'text-purple-600 bg-purple-50 border-purple-200'
    };
    return colors[type] || `${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} ${theme?.text || 'text-indigo-700'} border-gray-200`;
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} shadow-sm`}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div>
            <h2 className={`text-xl font-bold ${theme?.text || 'text-indigo-700'} drop-shadow-sm`}>
              Leave Pattern Overview
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Analyzing leave patterns
            </p>
          </div>
        </div>
        <LoadingSpinner text="Loading associates..." />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header with consistent styling */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} shadow-sm`}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-5 w-5 text-white" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div>
            <h2 className={`text-xl font-bold ${theme?.text || 'text-indigo-700'} drop-shadow-sm`}>
              Leave Pattern Overview
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Analyze individual leave patterns
            </p>
          </div>
        </div>
        
        {/* Month selector */}
        <div className="flex items-center space-x-2">
          <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 ${theme?.icon || 'text-indigo-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 4v10m6-10v10m6-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <select
            className={`border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-opacity-50 transition-all ${theme?.accent || 'focus:ring-indigo-500 focus:border-indigo-500'}`}
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
          >
            {months.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Controls section */}
      <div className={`${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} rounded-lg p-4 border border-gray-200 shadow-sm space-y-3`}>
        <div className="flex items-center space-x-2">
          <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 ${theme?.icon || 'text-indigo-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <label className={`text-sm font-medium ${theme?.text || 'text-indigo-700'}`}>
            Select Associate
          </label>
        </div>
        
        <select
          className={`border border-gray-300 rounded-lg px-3 py-2 w-full bg-white focus:ring-2 focus:ring-opacity-50 transition-all ${theme?.accent || 'focus:ring-indigo-500 focus:border-indigo-500'}`}
          value={selectedUser || ''}
          onChange={(e) => setSelectedUser(e.target.value)}
          disabled={users.length === 0}
        >
          {users.length === 0 ? (
            <option value="">No associates available</option>
          ) : (
            users.map((u) => (
              <option key={u.id} value={u.id}>{u.username}</option>
            ))
          )}
        </select>
      </div>

      {/* Content area */}
      <div className="space-y-4">
        {patternLoading ? (
          <LoadingSpinner text="Loading leave pattern..." />
        ) : summary ? (
          <div className={`${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} rounded-lg p-5 shadow-sm border border-gray-200 space-y-4`}>
            {/* Associate info header */}
            <div className="flex items-center justify-between pb-3 border-b border-gray-200 border-opacity-50">
              <div className="flex items-center space-x-3">
                <div className={`w-10 h-10 rounded-full bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} flex items-center justify-center shadow-sm`}>
                  <span className="text-white font-bold text-sm">
                    {summary.username?.charAt(0)?.toUpperCase() || 'A'}
                  </span>
                </div>
                <div>
                  <h3 className={`font-bold ${theme?.text || 'text-indigo-700'} text-base`}>
                    {summary.username}
                  </h3>
                  <p className="text-xs text-gray-500">
                    {selectedMonth} Pattern Analysis
                  </p>
                </div>
              </div>
            </div>

            {/* Leave statistics */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-red-200 shadow-sm">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <span className="text-sm font-medium text-gray-700">Casual Leave</span>
                  </div>
                  <span className="font-bold text-red-600">{summary.monthly_summary?.CL || 0}</span>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-green-200 shadow-sm">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-gray-700">Annual Leave</span>
                  </div>
                  <span className="font-bold text-green-600">{summary.monthly_summary?.AL || 0}</span>
                </div>
              </div>

              <div className="space-y-2">
                {/* Frequent days */}
                <div className="p-3 bg-white rounded-lg border border-gray-200 shadow-sm">
                  <div className="flex items-center space-x-2 mb-2">
                    <svg className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 4v10m6-10v10m6-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-sm font-medium text-gray-700">Frequent Days</span>
                  </div>
                  <div className="text-xs text-gray-600">
                    {summary.frequent_days && Object.keys(summary.frequent_days).length > 0 
                      ? Object.keys(summary.frequent_days).join(', ')
                      : 'No pattern detected'
                    }
                  </div>
                </div>
              </div>
            </div>

            {/* Approved leave dates only */}
            {summary.leave_dates && summary.leave_dates.length > 0 && (
              <div className="p-3 bg-white rounded-lg border border-gray-200 shadow-sm">
                <div className="flex items-center space-x-2 mb-2">
                  <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <span className="text-sm font-medium text-green-700">Approved Leave Dates</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {summary.leave_dates.slice(0, 8).map((date, idx) => (
                    <span key={idx} className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                      {new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                  ))}
                  {summary.leave_dates.length > 8 && (
                    <span className="px-2 py-1 bg-green-200 text-green-700 text-xs rounded-full">
                      +{summary.leave_dates.length - 8} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <EmptyState />
        )}
      </div>

      {/* Footer with last updated info */}
      <div className="text-xs text-gray-400 text-center pt-4 border-t border-gray-200 border-opacity-50">
        Pattern data refreshed • {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
};

export default LeavePatternCard;