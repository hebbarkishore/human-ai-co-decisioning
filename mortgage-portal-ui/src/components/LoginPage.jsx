import React, { useState } from 'react';
import axios from 'axios';

function LoginPage({ onLogin }) {
  const [id, setId] = useState('');
  const [pwd, setPwd] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault(); // Prevent page reload
    try {
      const url = "http://localhost:8006/underwriter-helper-service/login";  
      console.log("Logging in to:", url);
      const response = await axios.post(url, {
        email: id,
        password: pwd
      });
      if (response.status === 200) {
        console.log("Login successful:", response.data);
        onLogin(response.data); // Trigger post-login flow
      }
    } catch (error) {
      console.error("Login failed:", error.response?.data || error.message);
      setError("Invalid credentials or server error");
    }
  };

  return (
    <div className="flex flex-col items-center mt-40">
      <h1 className="text-2xl font-bold mb-4">Underwriter Login</h1>
      <form onSubmit={handleLogin} className="flex flex-col w-64 gap-3">
        <input
          className="border p-2"
          placeholder="User ID"
          value={id}
          onChange={(e) => setId(e.target.value)}
        />
        <input
          type="password"
          className="border p-2"
          placeholder="Password"
          value={pwd}
          onChange={(e) => setPwd(e.target.value)}
        />
        <button type="submit" className="bg-blue-600 text-white p-2">
          Login
        </button>
        {error && <p className="text-red-500">{error}</p>}
      </form>
    </div>
  );
}

export default LoginPage;