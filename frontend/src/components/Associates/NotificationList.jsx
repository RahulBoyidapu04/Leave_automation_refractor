import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { FaBell, FaCheckCircle } from 'react-icons/fa';
import toast from 'react-hot-toast';

const NotificationList = ({ notifications, onClear }) => {
  const hasUnread = notifications.some((n) => !n.read);

  const handleClearAll = () => {
    if (onClear) {
      onClear();
      toast.success('All notifications marked as read');
    }
  };

  return (
    <div className="bg-white rounded-xl shadow p-6 space-y-4 max-h-80 overflow-y-auto custom-scroll">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-blue-700 flex items-center gap-2">
          <FaBell className="text-blue-500" />
          Notifications
        </h2>
        {hasUnread && (
          <button
            onClick={handleClearAll}
            className="text-sm text-blue-600 hover:underline"
          >
            Mark all as read
          </button>
        )}
      </div>

      {notifications.length === 0 ? (
        <p className="text-gray-500 text-sm">You're all caught up 🎉</p>
      ) : (
        <ul className="space-y-3">
          {notifications.map((n) => (
            <li
              key={n.id}
              className={`border-l-4 p-3 rounded-md ${
                n.read
                  ? 'border-gray-300 bg-gray-50'
                  : 'border-blue-500 bg-blue-50'
              }`}
            >
              <div className="flex justify-between items-center mb-1">
                <span
                  className={`text-sm font-medium ${
                    n.read ? 'text-gray-600' : 'text-blue-700'
                  }`}
                >
                  {n.message}
                </span>
                {n.read ? (
                  <FaCheckCircle className="text-green-500" />
                ) : (
                  <span className="text-xs text-blue-500">New</span>
                )}
              </div>
              <p className="text-xs text-gray-400">
                {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default NotificationList;
