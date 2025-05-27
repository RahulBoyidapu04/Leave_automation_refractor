import React, { useEffect, useState, useCallback, useMemo } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

import AvailabilityCalendar from './AvailabilityCalendar';
import ApplyLeaveCard from './ApplyLeaveCard';
import LeaveList from './LeaveList';
import NotificationList from './NotificationList';
import LeaveCancellationAndEdit from './LeaveCancellationEdit';
import LeaveBalanceTracker from './LeaveBalanceTracker';
import UpcomingShrinkageChart from './UpcomingShrinkageChart';
import LeaveTypePieChart from './LeaveTypePieChart';

// Custom hook for theme management
const useTheme = (colorTheme) => {
  return useMemo(() => {
    const themes = {
      vibrant: {
        background: 'bg-gradient-to-br from-blue-100 via-purple-50 to-pink-100',
        primary: 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700',
        accent: 'border-indigo-500',
        text: 'text-indigo-700',
        hover: 'hover:bg-indigo-50',
        icon: 'text-indigo-500',
        cardGradient: 'bg-gradient-to-r from-indigo-50 to-purple-50',
        cardAccent: 'from-indigo-500 to-purple-500',
        spinner: 'border-indigo-500',
        button: 'from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600'
      },
      sunset: {
        background: 'bg-gradient-to-br from-orange-100 via-red-50 to-yellow-100',
        primary: 'bg-gradient-to-r from-orange-500 to-pink-500 text-white hover:from-orange-600 hover:to-pink-600',
        accent: 'border-orange-500',
        text: 'text-orange-700',
        hover: 'hover:bg-orange-50',
        icon: 'text-orange-500',
        cardGradient: 'bg-gradient-to-r from-red-50 to-yellow-50',
        cardAccent: 'from-orange-500 to-red-500',
        spinner: 'border-orange-500',
        button: 'from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600'
      },
      ocean: {
        background: 'bg-gradient-to-br from-cyan-100 via-blue-50 to-teal-100',
        primary: 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white hover:from-cyan-600 hover:to-blue-600',
        accent: 'border-cyan-500',
        text: 'text-cyan-700',
        hover: 'hover:bg-cyan-50',
        icon: 'text-cyan-500',
        cardGradient: 'bg-gradient-to-r from-blue-50 to-teal-50',
        cardAccent: 'from-cyan-500 to-blue-500',
        spinner: 'border-cyan-500',
        button: 'from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600'
      },
      forest: {
        background: 'bg-gradient-to-br from-green-100 via-emerald-50 to-teal-100',
        primary: 'bg-gradient-to-r from-green-600 to-teal-600 text-white hover:from-green-700 hover:to-teal-700',
        accent: 'border-green-500',
        text: 'text-green-700',
        hover: 'hover:bg-green-50',
        icon: 'text-green-500',
        cardGradient: 'bg-gradient-to-r from-emerald-50 to-lime-50',
        cardAccent: 'from-green-500 to-emerald-500',
        spinner: 'border-green-500',
        button: 'from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600'
      },
      berry: {
        background: 'bg-gradient-to-br from-pink-100 via-rose-50 to-purple-100',
        primary: 'bg-gradient-to-r from-pink-500 to-purple-500 text-white hover:from-pink-600 hover:to-purple-600',
        accent: 'border-pink-500',
        text: 'text-pink-700',
        hover: 'hover:bg-pink-50',
        icon: 'text-pink-500',
        cardGradient: 'bg-gradient-to-r from-pink-50 to-fuchsia-50',
        cardAccent: 'from-pink-500 to-fuchsia-500',
        spinner: 'border-pink-500',
        button: 'from-pink-500 to-fuchsia-500 hover:from-pink-600 hover:to-fuchsia-600'
      }
    };
    return themes[colorTheme] || themes.vibrant;
  }, [colorTheme]);
};

const AssociateDashboard = ({ user }) => {
  const [leaves, setLeaves] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [shrinkageData, setShrinkageData] = useState([]);
  const [selectedLeave, setSelectedLeave] = useState(null);
  const [colorTheme, setColorTheme] = useState('vibrant');
  const [refreshTimestamp, setRefreshTimestamp] = useState(Date.now());

  const [loadingLeaves, setLoadingLeaves] = useState(true);
  const [loadingNotifications, setLoadingNotifications] = useState(true);
  const [loadingShrinkage, setLoadingShrinkage] = useState(true);

  const theme = useTheme(colorTheme);

  // API call configurations
  const apiConfig = useMemo(() => ({
    headers: { Authorization: `Bearer ${user.token}` }
  }), [user.token]);

  // Enhanced error handling
  const handleApiError = useCallback((error, defaultMessage) => {
    const message = error.response?.data?.message || defaultMessage;
    const status = error.response?.status;
    
    if (status === 401) {
      toast.error('Session expired. Please login again.');
    } else if (status === 403) {
      toast.error('Access denied. Insufficient permissions.');
    } else if (status >= 500) {
      toast.error('Server error. Please try again later.');
    } else {
      toast.error(message);
    }
  }, []);

  // Updated API endpoints with better error handling
  const fetchLeaves = useCallback(async () => {
    setLoadingLeaves(true);
    try {
      const res = await axios.get('/api/v1/leave/history', apiConfig);
      setLeaves(res.data.data?.history || []);
    } catch (error) {
      handleApiError(error, 'Failed to fetch leaves');
      setLeaves([]);
    } finally {
      setLoadingLeaves(false);
    }
  }, [apiConfig, handleApiError]);

  const fetchNotifications = useCallback(async () => {
    setLoadingNotifications(true);
    try {
      const res = await axios.get('/api/v1/leave/notifications', apiConfig);
      setNotifications(res.data.data?.notifications || []);
    } catch (error) {
      handleApiError(error, 'Failed to load notifications');
      setNotifications([]);
    } finally {
      setLoadingNotifications(false);
    }
  }, [apiConfig, handleApiError]);

  const fetchShrinkageData = useCallback(async () => {
    setLoadingShrinkage(true);
    try {
      const res = await axios.get('/api/v1/leave/forecast/30days', apiConfig);
      setShrinkageData(res.data.data?.forecast || []);
    } catch (error) {
      handleApiError(error, 'Failed to load shrinkage data');
      setShrinkageData([]);
    } finally {
      setLoadingShrinkage(false);
    }
  }, [apiConfig, handleApiError]);

  const refreshAllData = useCallback(async () => {
    setRefreshTimestamp(Date.now());
    
    // Show loading toast
    const loadingToast = toast.loading('Refreshing data...');
    
    try {
      await Promise.all([
        fetchLeaves(),
        fetchNotifications(),
        fetchShrinkageData()
      ]);
      toast.success('Data refreshed successfully', { id: loadingToast });
    } catch (error) {
      toast.error('Failed to refresh some data', { id: loadingToast });
    }
  }, [fetchLeaves, fetchNotifications, fetchShrinkageData]);

  useEffect(() => {
    const initializeData = async () => {
      await Promise.all([
        fetchLeaves(),
        fetchNotifications(),
        fetchShrinkageData()
      ]);
    };
    
    initializeData();
  }, [fetchLeaves, fetchNotifications, fetchShrinkageData]);

  const markAllAsRead = useCallback(async () => {
    try {
      await axios.post('/api/v1/leave/notifications/mark-read', {}, apiConfig);
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      toast.success('All notifications marked as read');
    } catch (error) {
      handleApiError(error, 'Failed to mark notifications as read');
    }
  }, [apiConfig, handleApiError]);

  const handleCancel = useCallback(async (leaveId) => {
    const confirmToast = toast.loading('Cancelling leave...');
    try {
      await axios.delete(`/api/v1/leave/cancel/${leaveId}`, apiConfig);
      toast.success('Leave cancelled successfully', { id: confirmToast });
      await fetchLeaves();
    } catch (error) {
      handleApiError(error, 'Failed to cancel leave');
      toast.dismiss(confirmToast);
    }
  }, [apiConfig, handleApiError, fetchLeaves]);

  const handleUpdate = useCallback(() => {
    setSelectedLeave(null);
    fetchLeaves();
  }, [fetchLeaves]);

  const handleEdit = useCallback((leave) => {
    setSelectedLeave(leave);
  }, []);

  const toggleColorTheme = useCallback(() => {
    const themes = ['vibrant', 'sunset', 'ocean', 'forest', 'berry'];
    const currentIndex = themes.indexOf(colorTheme);
    const nextIndex = (currentIndex + 1) % themes.length;
    setColorTheme(themes[nextIndex]);
    toast.success(`Theme updated to ${themes[nextIndex].charAt(0).toUpperCase() + themes[nextIndex].slice(1)}`);
  }, [colorTheme]);

  // Memoized components
  const Spinner = useMemo(() => () => (
    <div className="flex justify-center items-center h-60" role="status" aria-label="Loading">
      <div className="relative">
        <div className="w-12 h-12 rounded-full border-2 border-gray-200"></div>
        <div className={`absolute top-0 left-0 w-12 h-12 rounded-full border-t-2 ${theme.spinner} animate-spin`}></div>
      </div>
    </div>
  ), [theme.spinner]);

  const Card = useMemo(() => ({ title, icon, children, className = '' }) => (
    <div className={`${theme.cardGradient} rounded-lg shadow-md border-t-4 border-transparent bg-gradient-to-r ${theme.cardAccent} backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:scale-[1.01] ${className}`}>
      <div className="p-4 border-b border-white border-opacity-30 flex items-center">
        <span className={`mr-2 ${theme.icon} text-xl`} role="img" aria-label={title}>
          {icon}
        </span>
        <h2 className={`font-semibold text-lg ${theme.text}`}>{title}</h2>
      </div>
      <div className="p-4">
        {children}
      </div>
    </div>
  ), [theme]);

  // Keyboard event handlers
  const handleKeyDown = useCallback((event) => {
    if (event.key === 'Escape' && selectedLeave) {
      setSelectedLeave(null);
    }
  }, [selectedLeave]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className={`p-6 space-y-6 min-h-screen ${theme.background}`}>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <h1 className={`text-3xl font-bold ${theme.text} drop-shadow-sm`}>
          Associate Dashboard
        </h1>
        <div className="flex items-center space-x-4">
          <button 
            onClick={refreshAllData}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 flex items-center bg-gradient-to-r ${theme.button} shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transform hover:scale-105`}
            aria-label="Refresh all data"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
          <button 
            onClick={toggleColorTheme}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 flex items-center bg-gradient-to-r ${theme.button} shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transform hover:scale-105`}
            aria-label="Change color theme"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
            </svg>
            Theme
          </button>
        </div>
      </div>
      
      {/* Top section - Primary actions and notifications */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="transition-all duration-300 md:col-span-1">
          <Card title="Apply for Leave" icon="🗓️" className="h-full">
            <ApplyLeaveCard user={user} onLeaveApplied={fetchLeaves} />
          </Card>
        </div>
        
        <div className="transition-all duration-300 md:col-span-1">
          <Card title="My Leaves" icon="📅" className="h-full">
            {loadingLeaves ? (
              <Spinner />
            ) : (
              <LeaveList
                leaves={leaves}
                onEdit={handleEdit}
                onCancel={handleCancel}
                onRefresh={fetchLeaves}
                theme={theme}
              />
            )}
          </Card>
        </div>
        
        <div className="transition-all duration-300 md:col-span-1">
          <Card title="Notifications" icon="🔔" className="h-full">
            {loadingNotifications ? (
              <Spinner />
            ) : (
              <NotificationList 
                notifications={notifications} 
                onClear={markAllAsRead}
                theme={theme} 
              />
            )}
          </Card>
        </div>
      </div>

      {/* Middle section - Charts and analytics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="transition-all duration-300">
          <Card title="Upcoming Shrinkage" icon="📈" className="h-full">
            {loadingShrinkage ? (
              <Spinner />
            ) : (
              <UpcomingShrinkageChart user={user} colorTheme={colorTheme} />
            )}
          </Card>
        </div>
        <div className="transition-all duration-300">
          <Card title="Leave Types" icon="📋" className="h-full">
            {loadingShrinkage ? (
              <Spinner />
            ) : (
              <LeaveTypePieChart user={user} colorTheme={colorTheme} />
            )}
          </Card>
        </div>
      </div>

      {/* Calendar section */}
      <div className="grid grid-cols-1 gap-6">
        <div className="transition-all duration-300">
          <Card title="Availability Calendar" icon="📆" className="h-full">
            <AvailabilityCalendar
              shrinkageData={shrinkageData}
              onSelectDate={(date) => console.log('Selected date:', date)}
              colorTheme={colorTheme}
            />
          </Card>
        </div>
      </div>

      {/* Bottom section - Leave Balance Tracker */}
      <div className="grid grid-cols-1 gap-6">
        <div className="transition-all duration-300">
          <Card title="Leave Balance Tracker" icon="⚖️" className="h-full">
            <LeaveBalanceTracker user={user} colorTheme={colorTheme} />
          </Card>
        </div>
      </div>

      {/* Modal for editing leave */}
      {selectedLeave && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-40 z-50 flex items-center justify-center backdrop-filter backdrop-blur-sm"
          onClick={(e) => e.target === e.currentTarget && setSelectedLeave(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="edit-leave-title"
        >
          <div className={`${theme.cardGradient} rounded-lg shadow-xl w-[90%] max-w-md transform transition-all duration-300 scale-100 hover:scale-[1.01]`}>
            <div className={`p-4 border-b border-t-4 border-transparent bg-gradient-to-r ${theme.cardAccent}`}>
              <div className="flex justify-between items-center">
                <h2 id="edit-leave-title" className={`font-semibold text-lg ${theme.text}`}>
                  Edit Leave
                </h2>
                <button 
                  onClick={() => setSelectedLeave(null)}
                  className="text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-300 rounded p-1"
                  aria-label="Close edit leave dialog"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="p-6">
              <LeaveCancellationAndEdit
                user={user}
                selectedLeave={selectedLeave}
                onClose={() => setSelectedLeave(null)}
                onUpdate={handleUpdate}
                theme={theme}
              />
            </div>
          </div>
        </div>
      )}
      
      {/* Last refreshed indicator */}
      <div className="text-xs text-gray-500 text-center pt-4 bg-white bg-opacity-30 rounded-full py-1 max-w-xs mx-auto">
        Last refreshed: {new Date(refreshTimestamp).toLocaleTimeString()}
      </div>
    </div>
  );
};

export default AssociateDashboard;