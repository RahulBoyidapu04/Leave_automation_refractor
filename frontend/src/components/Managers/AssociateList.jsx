import React from 'react';

const AssociateList = ({ associates = [] }) => {
  return (
    <div className="bg-white rounded-xl shadow p-6 space-y-4">
      <h2 className="text-lg font-bold text-gray-800 mb-2">My Associates</h2>

      {associates.length === 0 ? (
        <p className="text-sm text-gray-500">No associates mapped to you.</p>
      ) : (
        <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {associates.map((associate) => (
            <li key={associate.id} className="border rounded-lg p-4 bg-gray-50">
              <p className="text-blue-700 font-medium">{associate.username}</p>
              <p className="text-sm text-gray-600">Team: {associate.team_name}</p>
              <p className="text-xs text-gray-500">Role: {associate.role}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default AssociateList;
