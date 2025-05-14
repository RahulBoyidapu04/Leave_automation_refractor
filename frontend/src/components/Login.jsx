import React, { useState } from 'react';
import axios from 'axios';

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const login = async () => {
    try {
      // Use URLSearchParams for x-www-form-urlencoded
      const params = new URLSearchParams();
      params.append("username", username);
      params.append("password", password);

      const res = await axios.post('/auth/token', params, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      const token = res.data.access_token;

      // Use relative path so Vite proxy works
      const profile = await axios.get('/me', {
        headers: { Authorization: `Bearer ${token}` }
      });

      onLogin({ ...profile.data, token });
    } catch (err) {
      alert('Invalid credentials');
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white gap-4">
      <h2 className="text-3xl font-bold text-blue-600">Login</h2>
      <input
        type="text"
        placeholder="Username"
        className="border p-2 rounded w-64"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        className="border p-2 rounded w-64"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded shadow"
        onClick={login}
      >
        Sign In
      </button>
    </div>
  );
};

export default Login;