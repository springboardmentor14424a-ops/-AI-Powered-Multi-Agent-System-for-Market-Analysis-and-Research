import React, { useState, useEffect } from 'react';
import Register from './Register';
import Login from './Login';
import ResearchDashboard from './ResearchDashboard';

function App() {
  const [token, setToken] = useState(() => {
    // Check URL parameters first in case we just got redirected back from Google OAuth
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    if (urlToken) {
      localStorage.setItem('token', urlToken);
      window.history.replaceState({}, document.title, window.location.pathname);
      return urlToken;
    }
    return localStorage.getItem('token');
  });

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  // Show the Research Dashboard if a token exists
  if (token) {
    return <ResearchDashboard onLogout={handleLogout} />;
  }

  // Otherwise, render Register and Login, updating token state on success
  return (
    <div style={{ padding: '20px' }}>
      <Register />
      <hr style={{ margin: '40px 0' }} />
      <Login onLoginSuccess={() => setToken(localStorage.getItem('token'))} />
    </div>
  );
}

export default App;