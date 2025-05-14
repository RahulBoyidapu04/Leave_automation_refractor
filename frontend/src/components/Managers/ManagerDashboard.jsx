import React from 'react';
import TeamShrinkageChart from "../Associates/TeamShrinkageChart";
import LeavePatternCard from './LeavePatternCard';
import PendingApprovals from './PendingApprovals';
import ManagerNotificationList from '../ManagerNotificationList';
import ShrinkageCarryForwardCard from './ShrinkageCarryForwardCard';
import UpcomingShrinkageChart from '../Associates/UpcomingShrinkageChart';
import TeamLeaveSummary from '../Associates/TeamLeaveSummary';

const ManagerDashboard = ({ user }) => {
  return (
    <div className="p-6 bg-gray-50 min-h-screen space-y-6">
      <h1 className="text-2xl font-bold text-blue-900 mb-4">Manager Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <TeamShrinkageChart user={user} />
        <LeavePatternCard user={user} />
        <ShrinkageCarryForwardCard user={user} />
        <ManagerNotificationList user={user} />
        <UpcomingShrinkageChart user={user} />
        <TeamLeaveSummary user={user} />
      </div>

      <div>
        <PendingApprovals user={user} />
      </div>
    </div>
  );
};

export default ManagerDashboard;
