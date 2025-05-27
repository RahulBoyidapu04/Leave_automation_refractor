import React from 'react';
import { format } from 'date-fns';
import { FaEdit, FaTrashAlt, FaSyncAlt } from 'react-icons/fa';

const statusColor = {
  Approved: 'text-green-600 bg-green-100',
  Pending: 'text-amber-600 bg-amber-100',
  Cancelled: 'text-gray-600 bg-gray-100',
  Rejected: 'text-red-600 bg-red-100'
};

const LeaveList = ({ leaves, onEdit, onCancel, onRefresh }) => {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 transition hover:shadow-xl">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-purple-700">My Leave Requests</h2>
        {onRefresh && (
          <button
            className="text-sm flex items-center gap-1 text-blue-600 hover:text-blue-800"
            onClick={onRefresh}
            title="Refresh leave list"
          >
            <FaSyncAlt size={14} />
            Refresh
          </button>
        )}
      </div>

      {leaves.length === 0 ? (
        <p className="text-sm text-gray-500">You haven’t applied for any leave yet.</p>
      ) : (
        <div className="divide-y max-h-80 overflow-y-auto pr-1 custom-scroll">
          {leaves.map((leave) => (
            <div key={leave.id} className="flex justify-between items-start py-4">
              <div>
                <p className="font-semibold text-gray-800 capitalize">{leave.leave_type}</p>
                <p className="text-sm text-gray-500">
                  {format(new Date(leave.start_date + "T00:00:00"), 'dd MMM yyyy')} →{' '}
                  {format(new Date(leave.end_date + "T00:00:00"), 'dd MMM yyyy')}
                </p>
              </div>

              <div className="flex flex-col items-end gap-1">
                <span
                  className={`text-xs px-2 py-1 rounded-full font-medium ${statusColor[leave.status]}`}
                >
                  {leave.status}
                </span>

                {(leave.status === 'Pending' || leave.status === 'Approved') &&
                  new Date(leave.start_date + "T00:00:00") > new Date() && (
                    <div className="flex gap-2 mt-1">
                      <button
                        className="p-1 rounded-full hover:bg-blue-100 text-blue-600"
                        title="Edit"
                        onClick={() => onEdit?.(leave)}
                      >
                        <FaEdit size={14} />
                      </button>
                      <button
                        className="p-1 rounded-full hover:bg-red-100 text-red-600"
                        title="Cancel"
                        onClick={() => onCancel?.(leave.id)}
                      >
                        <FaTrashAlt size={14} />
                      </button>
                    </div>
                  )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LeaveList;
