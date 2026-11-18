import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function Dashboard() {
  const [data, setData] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [newStock, setNewStock] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      const token = localStorage.getItem('token');
      
      if (!token) {
        navigate('/'); 
        return;
      }

      try {
        // 1. Fetch secure user details
        const userResponse = await fetch('http://127.0.0.1:8000/dashboard', {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (userResponse.ok) {
          const result = await userResponse.json();
          setData(result);
        } else {
          throw new Error('Session expired.');
        }

        // 2. Fetch the user's saved watchlist
        const watchResponse = await fetch('http://127.0.0.1:8000/watchlist', {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (watchResponse.ok) {
          const watchResult = await watchResponse.json();
          setWatchlist(watchResult.watchlist);
        }

      } catch (err) {
        setError('Session expired. Please log in again.');
        localStorage.removeItem('token');
        setTimeout(() => navigate('/'), 2000);
      }
    };

    fetchDashboardData();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    if (!newStock.trim()) return;

    const token = localStorage.getItem('token');
    try {
      const response = await fetch('http://127.0.0.1:8000/watchlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ stock_symbol: newStock.trim() })
      });

      if (response.ok) {
        const result = await response.json();
        // Update the UI immediately with the newly saved stock
        setWatchlist([...watchlist, result.item]);
        setNewStock(''); // Clear the input field
      } else {
        alert("Failed to add stock. Please try again.");
      }
    } catch (err) {
      alert("Error connecting to the server.");
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f3f4f6',
      fontFamily: '"Inter", "Segoe UI", sans-serif',
      padding: '40px 20px'
    }}>
      <div style={{
        maxWidth: '800px', // Widened slightly to fit the new layout
        margin: '0 auto',
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.05)',
        overflow: 'hidden'
      }}>
        
        {/* Header Section */}
        <div style={{
          backgroundColor: '#1f2937',
          padding: '20px 30px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: 0, color: 'white', fontSize: '20px', fontWeight: '600' }}>
            Analyst Dashboard
          </h2>
          <button 
            onClick={handleLogout}
            style={{
              backgroundColor: '#ef4444',
              color: 'white', border: 'none', padding: '8px 16px',
              borderRadius: '6px', fontSize: '14px', fontWeight: '500',
              cursor: 'pointer'
            }}
          >
            Log Out
          </button>
        </div>

        {/* Content Section */}
        <div style={{ padding: '30px', display: 'flex', gap: '40px', flexWrap: 'wrap' }}>
          
          {/* Left Column: Account Info */}
          <div style={{ flex: '1', minWidth: '250px' }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#374151', fontSize: '16px', borderBottom: '1px solid #e5e7eb', paddingBottom: '8px' }}>
              Account Details
            </h3>
            {data ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#6b7280', fontSize: '14px' }}>User</span>
                  <span style={{ color: '#111827', fontWeight: '500' }}>{data.full_name || data.email.split('@')[0]}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#6b7280', fontSize: '14px' }}>Status</span>
                  <span style={{ backgroundColor: '#dbeafe', color: '#1e40af', padding: '2px 10px', borderRadius: '9999px', fontSize: '12px', fontWeight: '600' }}>
                    ACTIVE
                  </span>
                </div>
              </div>
            ) : <span style={{ color: '#6b7280' }}>Loading...</span>}
          </div>

          {/* Right Column: Watchlist */}
          <div style={{ flex: '2', minWidth: '300px' }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#374151', fontSize: '16px', borderBottom: '1px solid #e5e7eb', paddingBottom: '8px' }}>
              My Watchlist
            </h3>
            
            <form onSubmit={handleAddStock} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
              <input 
                type="text" 
                placeholder="e.g. AAPL, RELIANCE.NS" 
                value={newStock}
                onChange={(e) => setNewStock(e.target.value.toUpperCase())}
                style={{ 
                  flex: 1, padding: '10px 12px', fontSize: '14px', 
                  border: '1px solid #d1d5db', borderRadius: '6px', outline: 'none' 
                }}
              />
              <button 
                type="submit"
                style={{ 
                  backgroundColor: '#2563eb', color: 'white', border: 'none', 
                  padding: '10px 20px', borderRadius: '6px', fontWeight: '500', cursor: 'pointer' 
                }}
              >
                Add
              </button>
            </form>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
              {watchlist.length > 0 ? (
                watchlist.map((item) => (
                  <div key={item.id} style={{ 
                    backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', 
                    padding: '12px 16px', borderRadius: '8px', 
                    display: 'flex', alignItems: 'center', gap: '10px'
                  }}>
                    <span style={{ fontWeight: '600', color: '#0f172a' }}>{item.stock_symbol}</span>
                  </div>
                ))
              ) : (
                <div style={{ color: '#6b7280', fontSize: '14px', fontStyle: 'italic' }}>
                  No stocks in your watchlist yet.
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

export default Dashboard;