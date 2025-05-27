import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { FaBell, FaCheckCircle } from 'react-icons/fa';
import toast from 'react-hot-toast';

const NotificationList = ({ notifications, onClear, colorTheme = 'vibrant', theme }) => {
  const hasUnread = notifications.some((n) => !n.read);

  const handleClearAll = () => {
    if (onClear) {
      onClear();
      toast.success('All notifications marked as read');
    }
  };

  // Empty state component
  const EmptyState = () => (
    <div className="flex flex-col items-center justify-center py-12">
      <div className={`p-4 rounded-full ${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} mb-4`}>
        <FaBell className={`h-6 w-6 ${theme?.icon || 'text-indigo-500'} opacity-70`} />
      </div>
      <p className={`text-sm font-medium ${theme?.text || 'text-indigo-700'} mb-1`}>
        You're all caught up 🎉
      </p>
      <p className="text-xs text-gray-500 text-center">
        No new notifications for now.
      </p>
    </div>
  );

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} shadow-sm`}>
            <FaBell className="text-white h-5 w-5" />
          </div>
          <div>
            <h2 className={`text-xl font-bold ${theme?.text || 'text-indigo-700'} drop-shadow-sm`}>
              Notifications
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Recent activity and alerts
            </p>
          </div>
        </div>

        {hasUnread && (
          <button
            onClick={handleClearAll}
            className={`text-sm font-medium px-3 py-1 rounded-full bg-gradient-to-r ${theme?.button || 'from-indigo-500 to-purple-500'} text-white hover:scale-105 shadow-sm`}
          >
            Mark all as read
          </button>
        )}
      </div>

      {/* Notification List */}
      {notifications.length === 0 ? (
        <EmptyState />
      ) : (
        <ul className="space-y-3 max-h-80 overflow-y-auto custom-scroll">
          {notifications.map((n) => (
            <li
              key={n.id}
              className={`rounded-lg px-4 py-3 shadow-sm border border-gray-200 transition-all duration-200 ${
                n.read
                  ? `${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'} text-gray-600`
                  : `bg-blue-50 border-blue-200 text-blue-800`
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium">{n.message}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                  </p>
                </div>
                <div className="ml-3">
                  {n.read ? (
                    <FaCheckCircle className="text-green-500" />
                  ) : (
                    <span className="text-xs font-semibold bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">
                      New
                    </span>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default NotificationList;
