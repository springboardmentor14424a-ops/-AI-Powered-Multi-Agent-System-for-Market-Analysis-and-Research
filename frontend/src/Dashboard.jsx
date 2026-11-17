import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      // 1. Get the token from the browser's storage
      const token = localStorage.getItem('token');
      
      // 2. If no token exists, immediately redirect to login
      if (!token) {
        navigate('/'); 
        return;
      }

      try {
        // 3. Send the token in the Authorization header
        const response = await fetch('http://127.0.0.1:8000/dashboard', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const result = await response.json();
          setData(result);
        } else {
          setError('Session expired or unauthorized. Please log in again.');
          localStorage.removeItem('token');
          setTimeout(() => navigate('/'), 2000);
        }
      } catch (err) {
        setError('Error connecting to backend server.');
      }
    };

    fetchDashboardData();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Analyst Dashboard</h2>
      {error && <p style={{ color: 'red', fontWeight: 'bold' }}>{error}</p>}
      
      {data ? (
        <div style={{ marginTop: '20px', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
          <h3 style={{ color: 'green' }}>{data.message}</h3>
          <p><strong>User ID:</strong> {data.user_id}</p>
          <p><strong>Email:</strong> {data.email}</p>
          <p><strong>Status:</strong> {data.status}</p>
          
          <button 
            onClick={handleLogout} 
            style={{ marginTop: '20px', padding: '10px 20px', cursor: 'pointer' }}
          >
            Log Out
          </button>
        </div>
      ) : (
        !error && <p>Loading secure data...</p>
      )}
    </div>
  );
}

export default Dashboard;