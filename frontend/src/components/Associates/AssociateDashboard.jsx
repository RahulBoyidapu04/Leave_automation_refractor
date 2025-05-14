import React, { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

import AvailabilityCalendar from './AvailabilityCalendar';
import AvailableDaysChart from '../AvailableDaysChart';
import ApplyLeaveCard from './ApplyLeaveCard';
import LeaveList from './LeaveList';
import NotificationList from './NotificationList';
import LeaveCancellationAndEdit from './LeaveCancellationEdit';
import LeaveBalanceTracker from './LeaveBalanceTracker';
import UpcomingShrinkageChart from './UpcomingShrinkageChart';
import TeamLeaveSummary from './TeamLeaveSummary';

const AssociateDashboard = ({ user }) => {
  const [leaves, setLeaves] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [shrinkageData, setShrinkageData] = useState([]);
  const [selectedLeave, setSelectedLeave] = useState(null);

  const [loadingLeaves, setLoadingLeaves] = useState(true);
  const [loadingNotifications, setLoadingNotifications] = useState(true);
  const [loadingShrinkage, setLoadingShrinkage] = useState(true);

  useEffect(() => {
    fetchLeaves();
    fetchNotifications();
    fetchShrinkageData();
    const interval = setInterval(fetchLeaves, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchLeaves = async () => {
    setLoadingLeaves(true);
    try {
      const res = await axios.get('/leave/my', {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      setLeaves(res.data);
    } catch {
      toast.error('Failed to fetch leaves');
    } finally {
      setLoadingLeaves(false);
    }
  };

  const fetchNotifications = async () => {
    setLoadingNotifications(true);
    try {
      const res = await axios.get('/notifications/me', {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      setNotifications(res.data);
    } catch {
      toast.error('Failed to load notifications');
    } finally {
      setLoadingNotifications(false);
    }
  };

  const fetchShrinkageData = async () => {
    setLoadingShrinkage(true);
    try {
      const res = await axios.get('/availability/next-30-days', {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      setShrinkageData(Array.isArray(res.data) ? res.data : []);
    } catch {
      toast.error('Failed to load shrinkage data');
    } finally {
      setLoadingShrinkage(false);
    }
  };

  const markAllAsRead = async () => {
    try {
      await axios.post('/notifications/mark-all-read', {}, {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      toast.success('All notifications marked as read');
    } catch {
      toast.error('Failed to mark notifications as read');
    }
  };

  const handleCancel = async (leaveId) => {
    try {
      await axios.delete(`/leave/${leaveId}`, {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      toast.success('Leave cancelled successfully');
      fetchLeaves();
    } catch {
      toast.error('Failed to cancel leave');
    }
  };

  const handleUpdate = () => {
    setSelectedLeave(null);
    fetchLeaves();
  };

  const handleEdit = (leave) => {
    setSelectedLeave(leave);
  };

  const Spinner = () => (
    <div className="flex justify-center items-center min-h-[200px]">
      <span className="animate-spin h-6 w-6 border-4 border-blue-500 border-t-transparent rounded-full"></span>
    </div>
  );

  return (
    <div className="p-6 space-y-6 bg-gray-100 min-h-screen">
      {/* Top Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <ApplyLeaveCard user={user} onLeaveApplied={fetchLeaves} />

        {loadingLeaves ? <Spinner /> : (
          <LeaveList
            leaves={leaves}
            onEdit={handleEdit}
            onCancel={handleCancel}
            onRefresh={fetchLeaves}
          />
        )}

        {loadingNotifications ? <Spinner /> : (
          <NotificationList notifications={notifications} onClear={markAllAsRead} />
        )}
      </div>

      {/* Insights Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {loadingShrinkage ? <Spinner /> : (
          <>
            <AvailableDaysChart shrinkageData={shrinkageData} />
            <UpcomingShrinkageChart user={user} />
            <TeamLeaveSummary user={user} />
          </>
        )}
      </div>

      {/* Availability Calendar */}
      <AvailabilityCalendar
        shrinkageData={shrinkageData}
        onSelectDate={(date) => console.log('Selected date:', date)}
      />

      <LeaveBalanceTracker user={user} />

      {selectedLeave && (
        <div className="fixed inset-0 bg-black bg-opacity-40 z-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg w-[90%] max-w-md shadow-xl">
            <LeaveCancellationAndEdit
              user={user}
              selectedLeave={selectedLeave}
              onClose={() => setSelectedLeave(null)}
              onUpdate={handleUpdate}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default AssociateDashboard;
