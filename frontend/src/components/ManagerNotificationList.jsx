import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';

const ManagerNotificationList = ({ user, refreshKey, colorTheme = 'vibrant', theme }) => {
  const [notifications, setNotifications] = useState([]);

  const fetchNotifications = async () => {
    try {
      const res = await axios.get('/api/v1/leave/notifications', {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      setNotifications(res.data.data?.notifications || []);
    } catch {
      console.error('Error fetching notifications');
    }
  };

  const markAllRead = async () => {
    try {
      await axios.post('/api/v1/leave/notifications/mark-read', null, {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      fetchNotifications();
    } catch {
      console.error('Failed to mark notifications as read');
    }
  };

  useEffect(() => {
    if (user?.token) fetchNotifications();
  }, [user, refreshKey]);

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} shadow-sm`}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405M19.6 13.4a9 9 0 10-3.6 3.6L21 21" />
            </svg>
          </div>
          <div>
            <h2 className={`text-xl font-bold ${theme?.text || 'text-indigo-700'} drop-shadow-sm`}>
              Notifications
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Recent activity and updates
            </p>
          </div>
        </div>

        <button
          onClick={markAllRead}
          className={`text-xs font-medium text-white px-3 py-1 rounded bg-gradient-to-r ${theme?.button || 'from-indigo-500 to-purple-500'} shadow-sm hover:scale-105 transition-transform`}
        >
          Mark All Read
        </button>
      </div>

      {/* Content */}
      {notifications.length === 0 ? (
        <div className="text-sm text-gray-500 p-4 text-center italic">
          No notifications to display.
        </div>
      ) : (
        <ul className="space-y-2 max-h-60 overflow-y-auto pr-1 custom-scroll">
          {notifications.map((n, i) => (
            <li
              key={i}
              className={`p-3 rounded-lg shadow-sm transition-all duration-200 ${
                n.read
                  ? 'bg-gray-100 text-gray-600'
                  : `${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} text-gray-900`
              }`}
            >
              <p className="text-sm font-medium">{n.message}</p>
              <p className="text-xs text-gray-400 mt-1">
                {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ManagerNotificationList;
