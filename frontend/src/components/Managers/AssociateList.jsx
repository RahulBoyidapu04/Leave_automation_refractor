import React, { useEffect, useState } from 'react';
import axios from 'axios';

const AssociateList = ({ user, refreshKey, colorTheme = 'vibrant', theme }) => {
  const [associates, setAssociates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAssociates = async () => {
      try {
        const res = await axios.get('/api/v1/leave/team/members', {
          headers: { Authorization: `Bearer ${user.token}` }
        });
        setAssociates(res.data.data?.members || []);
      } catch {
        setAssociates([]);
      } finally {
        setLoading(false);
      }
    };
    if (user?.token) fetchAssociates();
  }, [user, refreshKey]);

  // Loading spinner component
  const LoadingSpinner = () => (
    <div className="flex items-center justify-center py-8">
      <div className={`animate-spin rounded-full h-8 w-8 border-b-2 ${theme?.spinner || 'border-indigo-500'}`}></div>
      <span className={`ml-3 text-sm font-medium ${theme?.text || 'text-indigo-700'}`}>
        Loading associates...
      </span>
    </div>
  );

  // Empty state component
  const EmptyState = () => (
    <div className="flex flex-col items-center justify-center py-12">
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        className={`h-12 w-12 ${theme?.icon || 'text-indigo-500'} mb-4 opacity-50`}
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
      <p className={`text-sm font-medium ${theme?.text || 'text-indigo-700'} mb-1`}>
        No Associates Found
      </p>
      <p className="text-xs text-gray-500">
        No associates are currently mapped to you.
      </p>
    </div>
  );

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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <div>
            <h2 className={`text-xl font-bold ${theme?.text || 'text-indigo-700'} drop-shadow-sm`}>
              My Associates
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {loading ? 'Loading...' : `${associates.length} team member${associates.length !== 1 ? 's' : ''}`}
            </p>
          </div>
        </div>
        
        {/* Status indicator */}
        {!loading && (
          <div className={`px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r ${theme?.button || 'from-indigo-500 to-purple-500'} text-white shadow-sm`}>
            {associates.length} Total
          </div>
        )}
      </div>

      {/* Content area */}
      <div className="space-y-4">
        {loading ? (
          <LoadingSpinner />
        ) : associates.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {associates.map((associate, idx) => (
              <div 
                key={associate.id} 
                className={`${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} rounded-lg p-4 border border-gray-200 shadow-sm transition-all duration-300 hover:shadow-md hover:scale-[1.02] hover:border-opacity-50 ${theme?.hover || 'hover:bg-indigo-50'}`}
              >
                {/* Associate number badge */}
                <div className="flex items-start justify-between mb-3">
                  <div className={`w-6 h-6 rounded-full bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} flex items-center justify-center text-white text-xs font-bold shadow-sm`}>
                    {idx + 1}
                  </div>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} ${theme?.text || 'text-indigo-700'} border ${theme?.accent || 'border-indigo-500'} border-opacity-20`}>
                    {associate.role || 'Associate'}
                  </div>
                </div>

                {/* Associate details */}
                <div className="space-y-2">
                  <div>
                    <h3 className={`font-bold ${theme?.text || 'text-indigo-700'} text-base leading-tight`}>
                      {associate.username}
                    </h3>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <svg 
                      xmlns="http://www.w3.org/2000/svg" 
                      className={`h-4 w-4 ${theme?.icon || 'text-indigo-500'} opacity-60`}
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    <span className="text-sm text-gray-600 font-medium">
                      {associate.team_name || 'No Team Assigned'}
                    </span>
                  </div>

                  {/* Additional info if available */}
                  {associate.department && (
                    <div className="flex items-center space-x-2">
                      <svg 
                        xmlns="http://www.w3.org/2000/svg" 
                        className={`h-4 w-4 ${theme?.icon || 'text-indigo-500'} opacity-60`}
                        fill="none" 
                        viewBox="0 0 24 24" 
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                      <span className="text-xs text-gray-500">
                        {associate.department}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer with last updated info */}
      {!loading && associates.length > 0 && (
        <div className="text-xs text-gray-400 text-center pt-4 border-t border-gray-200 border-opacity-50">
          Associate data refreshed • {new Date().toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

export default AssociateList;