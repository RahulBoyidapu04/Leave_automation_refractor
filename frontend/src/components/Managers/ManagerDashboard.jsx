import React, { useState, useCallback, useMemo, useEffect } from 'react';
import toast from 'react-hot-toast';

import TeamShrinkageChart from "../Associates/TeamShrinkageChart";
import AssociatesOnLeaveToday from './AssociatesOnLeaveToday';
import UpcomingShrinkageChart from '../Associates/UpcomingShrinkageChart';
import LeavePatternCard from './LeavePatternCard';
import ShrinkageCarryForwardCard from './ShrinkageCarryForwardCard';
import ManagerNotificationList from '../ManagerNotificationList';
import PendingApprovals from './PendingApprovals';

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

const ManagerDashboard = ({ user }) => {
  const [refreshKey, setRefreshKey] = useState(0);
  const [refreshTimestamp, setRefreshTimestamp] = useState(Date.now());
  const [colorTheme, setColorTheme] = useState('vibrant');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const theme = useTheme(colorTheme);

  const handleRefresh = useCallback(async () => {
    if (isRefreshing) return;
    
    setIsRefreshing(true);
    const loadingToast = toast.loading('Refreshing dashboard...');
    
    try {
      setRefreshKey(prev => prev + 1);
      setRefreshTimestamp(Date.now());
      
      // Simulate loading time for better UX
      await new Promise(resolve => setTimeout(resolve, 500));
      
      toast.success('Dashboard refreshed successfully', { id: loadingToast });
    } catch (error) {
      toast.error('Failed to refresh dashboard', { id: loadingToast });
    } finally {
      setIsRefreshing(false);
    }
  }, [isRefreshing]);

  const toggleColorTheme = useCallback(() => {
    const themes = ['vibrant', 'sunset', 'ocean', 'forest', 'berry'];
    const currentIndex = themes.indexOf(colorTheme);
    const nextIndex = (currentIndex + 1) % themes.length;
    setColorTheme(themes[nextIndex]);
    toast.success(`Theme updated to ${themes[nextIndex].charAt(0).toUpperCase() + themes[nextIndex].slice(1)}`);
  }, [colorTheme]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      handleRefresh();
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [handleRefresh]);

  // Memoized Card component
  const Card = useMemo(() => ({ children, className = '', fullHeight = false }) => (
    <div className={`${theme.cardGradient} rounded-lg shadow-md border-t-4 border-transparent bg-gradient-to-r ${theme.cardAccent} backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:scale-[1.01] ${fullHeight ? 'h-full' : ''} ${className}`}>
      {children}
    </div>
  ), [theme]);

  return (
    <div className={`p-6 space-y-6 min-h-screen ${theme.background}`}>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <h1 className={`text-3xl font-bold ${theme.text} drop-shadow-sm`}>
          Manager Dashboard
        </h1>
        <div className="flex items-center space-x-4">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 flex items-center bg-gradient-to-r ${theme.button} shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none`}
            aria-label="Refresh dashboard data"
            title="Refresh Dashboard"
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className={`h-4 w-4 mr-1.5 ${isRefreshing ? 'animate-spin' : ''}`} 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor" 
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
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

      {/* Main dashboard grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left/Main Cards - 2/3 width */}
        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="transition-all duration-300">
            <Card>
              <TeamShrinkageChart 
                user={user} 
                refreshKey={refreshKey} 
                colorTheme={colorTheme}
                theme={theme}
              />
            </Card>
          </div>
          
          <div className="transition-all duration-300">
            <Card>
              <AssociatesOnLeaveToday 
                user={user} 
                refreshKey={refreshKey}
                colorTheme={colorTheme}
                theme={theme}
              />
            </Card>
          </div>
          
          <div className="transition-all duration-300">
            <Card>
              <UpcomingShrinkageChart 
                user={user} 
                refreshKey={refreshKey}
                colorTheme={colorTheme}
                theme={theme}
              />
            </Card>
          </div>
          
          <div className="transition-all duration-300">
            <Card>
              <LeavePatternCard 
                user={user} 
                refreshKey={refreshKey}
                colorTheme={colorTheme}
                theme={theme}
              />
            </Card>
          </div>
          
          <div className="transition-all duration-300 md:col-span-2">
            <Card>
              <ManagerNotificationList 
                user={user} 
                refreshKey={refreshKey}
                colorTheme={colorTheme}
                theme={theme}
              />
            </Card>
          </div>
        </div>

        {/* Right: Carry Forward Card - 1/3 width, full height */}
        <div className="lg:col-span-1 transition-all duration-300">
          <Card fullHeight>
            <ShrinkageCarryForwardCard 
              user={user} 
              refreshKey={refreshKey}
              colorTheme={colorTheme}
              theme={theme}
            />
          </Card>
        </div>
      </div>

      {/* Bottom: Pending Approvals - Full width */}
      <div className="transition-all duration-300">
        <Card>
          <PendingApprovals 
            user={user} 
            refreshKey={refreshKey}
            colorTheme={colorTheme}
            theme={theme}
          />
        </Card>
      </div>

      {/* Last refreshed indicator */}
      <div className="text-xs text-gray-500 text-center pt-4 bg-white bg-opacity-30 rounded-full py-1 max-w-xs mx-auto">
        Last refreshed: {new Date(refreshTimestamp).toLocaleTimeString()}
      </div>
    </div>
  );
};

export default ManagerDashboard;