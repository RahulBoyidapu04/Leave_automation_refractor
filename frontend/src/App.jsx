import React, { useState } from 'react';
import Login from './components/Login';
import AssociateDashboard from './components/Associates/AssociateDashboard';
import ManagerDashboard from './components/Managers/ManagerDashboard';
import L5Dashboard from './components/L5Dashboard'; // ✅ This is in root of components/
import { Toaster } from 'react-hot-toast';

const App = () => {
  const [user, setUser] = useState(null);

  const handleLogout = () => {
    setUser(null);
  };

  const renderDashboard = () => {
    if (!user || !user.role) {
      return (
        <div className="min-h-screen flex items-center justify-center text-red-600 text-xl">
          No user or role found.
        </div>
      );
    }
    switch (user.role) {
      case 'associate':
        return <AssociateDashboard user={user} />;
      case 'manager':
        return <ManagerDashboard user={user} />;
      case 'l5':
        return <L5Dashboard user={user} />;
      default:
        return (
          <div className="min-h-screen flex items-center justify-center text-red-600 text-xl">
            Unknown role: {user.role}
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Toaster position="top-right" />
      {!user ? (
        <Login
          onLogin={(profile) => {
            console.log('Logged in user:', profile);
            setUser(profile);
          }}
        />
      ) : (
        <>
          <div className="flex justify-end p-4">
            <button
              onClick={handleLogout}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Logout
            </button>
          </div>
          {renderDashboard()}
        </>
      )}
    </div>
  );
};

export default App;