import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';

const ManagerNotificationList = ({ user }) => {
  const [notifications, setNotifications] = useState([]);

  const fetchNotifications = async () => {
    try {
      const res = await axios.get('/notifications/me', {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      setNotifications(res.data || []);
    } catch (err) {
      console.error('Error fetching notifications');
    }
  };

  const markAllRead = async () => {
    try {
      await axios.post('/notifications/mark-read', null, {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      fetchNotifications();
    } catch (err) {
      console.error('Failed to mark notifications as read');
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  return (
    <div className="bg-white shadow rounded-xl p-4 space-y-3">
      <div className="flex justify-between items-center">
        <h2 className="font-semibold text-gray-800">Notifications</h2>
        <button
          onClick={markAllRead}
          className="text-xs text-blue-600 hover:underline"
        >
          Mark all as read
        </button>
      </div>

      {notifications.length === 0 ? (
        <p className="text-sm text-gray-500">No notifications.</p>
      ) : (
        <ul className="space-y-2 max-h-52 overflow-y-auto">
          {notifications.map((n, i) => (
            <li
              key={i}
              className={`text-sm p-2 rounded ${
                n.read ? 'bg-gray-100 text-gray-600' : 'bg-blue-50 text-gray-900'
              }`}
            >
              <p>{n.message}</p>
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

export default ManagerNotificationList;
