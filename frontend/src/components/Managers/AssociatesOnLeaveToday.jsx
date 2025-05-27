import React, { useEffect, useState } from 'react';
import axios from 'axios';

const AssociatesOnLeaveToday = ({ user, refreshKey, colorTheme = 'vibrant', theme }) => {
  const [onLeave, setOnLeave] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOnLeave = async () => {
      try {
        const res = await axios.get('/api/v1/leave/dashboard/on-leave-today', {
          headers: { Authorization: `Bearer ${user.token}` }
        });
        setOnLeave(res.data.data || []);
      } catch {
        setOnLeave([]);
      } finally {
        setLoading(false);
      }
    };
    fetchOnLeave();
  }, [user, refreshKey]);

  // Loading spinner component
  const LoadingSpinner = () => (
    <div className="flex items-center justify-center py-8">
      <div className={`animate-spin rounded-full h-8 w-8 border-b-2 ${theme?.spinner || 'border-indigo-500'}`}></div>
      <span className={`ml-3 text-sm font-medium ${theme?.text || 'text-indigo-700'}`}>
        Loading leave data...
      </span>
    </div>
  );

  // Empty state component
  const EmptyState = () => (
    <div className="flex flex-col items-center justify-center py-12">
      <div className={`p-4 rounded-full ${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} mb-4`}>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          className={`h-8 w-8 ${theme?.icon || 'text-indigo-500'} opacity-60`}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <p className={`text-sm font-medium ${theme?.text || 'text-indigo-700'} mb-1`}>
        All Present Today
      </p>
      <p className="text-xs text-gray-500 text-center">
        No associates are on leave today.<br />
        Great attendance!
      </p>
    </div>
  );

  // Get leave type styling
  const getLeaveTypeStyle = (leaveType) => {
    const styles = {
      'Sick Leave': 'bg-red-50 text-red-700 border-red-200',
      'Annual Leave': 'bg-green-50 text-green-700 border-green-200',
      'Personal Leave': 'bg-blue-50 text-blue-700 border-blue-200',
      'Emergency Leave': 'bg-orange-50 text-orange-700 border-orange-200',
      'Maternity Leave': 'bg-pink-50 text-pink-700 border-pink-200',
      'Paternity Leave': 'bg-purple-50 text-purple-700 border-purple-200',
      default: `${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} ${theme?.text || 'text-indigo-700'} border-gray-200`
    };
    return styles[leaveType] || styles.default;
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} shadow-sm`}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-5 w-5 text-white" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 4v10m6-10v10m6-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h2 className={`text-xl font-bold ${theme?.text || 'text-indigo-700'} drop-shadow-sm`}>
              Associates On Leave Today
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Current leave status
            </p>
          </div>
        </div>
        <LoadingSpinner />
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 4v10m6-10v10m6-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h2 className={`text-xl font-bold ${theme?.text || 'text-indigo-700'} drop-shadow-sm`}>
              Associates On Leave Today
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {new Date().toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </p>
          </div>
        </div>
        
        {/* Status indicator */}
        <div className={`px-3 py-1 rounded-full text-xs font-medium shadow-sm ${
          onLeave.length === 0 
            ? 'bg-green-100 text-green-700' 
            : `bg-gradient-to-r ${theme?.button || 'from-indigo-500 to-purple-500'} text-white`
        }`}>
          {onLeave.length === 0 ? 'All Present' : `${onLeave.length} On Leave`}
        </div>
      </div>

      {/* Content area */}
      <div className="space-y-4">
        {onLeave.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-3">
            {onLeave.map((associate, idx) => (
              <div
                key={idx}
                className={`${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} rounded-lg p-4 border border-gray-200 shadow-sm transition-all duration-300 hover:shadow-md hover:scale-[1.01] hover:border-opacity-50`}
              >
                <div className="flex items-center justify-between">
                  {/* Left side - Number and Name */}
                  <div className="flex items-center space-x-3 flex-1">
                    <div className={`w-8 h-8 rounded-full bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} flex items-center justify-center text-white text-sm font-bold shadow-sm`}>
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <h3 className={`font-bold ${theme?.text || 'text-indigo-700'} text-base leading-tight`}>
                        {associate.username}
                      </h3>
                      {associate.department && (
                        <p className="text-xs text-gray-500 mt-1">
                          {associate.department}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Right side - Leave info */}
                  <div className="flex flex-col items-end space-y-2">
                    <div className={`px-3 py-1 rounded-full text-xs font-semibold border ${getLeaveTypeStyle(associate.leave_type)}`}>
                      {associate.leave_type}
                    </div>
                    {associate.is_half_day && (
                      <div className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-50 text-yellow-700 border border-yellow-200">
                        Half Day
                      </div>
                    )}
                  </div>
                </div>

                {/* Additional info row */}
                {(associate.leave_reason || associate.duration) && (
                  <div className="mt-3 pt-3 border-t border-gray-200 border-opacity-50">
                    <div className="flex items-center justify-between text-xs text-gray-600">
                      {associate.leave_reason && (
                        <span className="flex items-center space-x-1">
                          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <span>{associate.leave_reason}</span>
                        </span>
                      )}
                      {associate.duration && (
                        <span className="flex items-center space-x-1">
                          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span>{associate.duration} days</span>
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer with last updated info */}
      <div className="text-xs text-gray-400 text-center pt-4 border-t border-gray-200 border-opacity-50">
        Leave data refreshed • {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
};

export default AssociatesOnLeaveToday;