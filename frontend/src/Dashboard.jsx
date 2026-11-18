import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function Dashboard() {
  const [data, setData] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [stockDetails, setStockDetails] = useState({});
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
        const userResponse = await fetch('http://127.0.0.1:8000/dashboard', {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (userResponse.ok) {
          const result = await userResponse.json();
          setData(result);
        } else {
          throw new Error('Session expired.');
        }

        const watchResponse = await fetch('http://127.0.0.1:8000/watchlist', {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (watchResponse.ok) {
          const watchResult = await watchResponse.json();
          setWatchlist(watchResult.watchlist);
          
          watchResult.watchlist.forEach(async (item) => {
            fetchLivePrice(item.stock_symbol, token);
          });
        }
      } catch (err) {
        setError('Session expired. Please log in again.');
        localStorage.removeItem('token');
        setTimeout(() => navigate('/'), 2000);
      }
    };

    fetchDashboardData();
  }, [navigate]);

  const fetchLivePrice = async (symbol, token) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/stock/${symbol}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const result = await response.json();
        setStockDetails(prev => ({
          ...prev,
          [symbol]: result
        }));
      }
    } catch (err) {
      console.error(`Failed to fetch data for ${symbol}`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    if (!newStock.trim()) return;

    const token = localStorage.getItem('token');
    const symbolToAdd = newStock.trim().toUpperCase();

    try {
      const response = await fetch('http://127.0.0.1:8000/watchlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ stock_symbol: symbolToAdd })
      });

      if (response.ok) {
        const result = await response.json();
        setWatchlist([...watchlist, result.item]);
        setNewStock('');
        fetchLivePrice(symbolToAdd, token);
      } else {
        alert("Failed to add stock. Please try again.");
      }
    } catch (err) {
      alert("Error connecting to the server.");
    }
  };

  // NEW: Delete Stock Function
  const handleDeleteStock = async (itemId) => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`http://127.0.0.1:8000/watchlist/${itemId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        // Remove the stock from the React UI immediately
        setWatchlist(watchlist.filter(item => item.id !== itemId));
      } else {
        alert("Failed to delete stock.");
      }
    } catch (err) {
      alert("Error connecting to the server.");
    }
  };

  return (
    <div style={{
      minHeight: '100vh', backgroundColor: '#f3f4f6',
      fontFamily: '"Inter", "Segoe UI", sans-serif', padding: '40px 20px'
    }}>
      <div style={{
        maxWidth: '900px', margin: '0 auto', backgroundColor: 'white',
        borderRadius: '12px', boxShadow: '0 10px 25px rgba(0, 0, 0, 0.05)', overflow: 'hidden'
      }}>
        
        {/* Header Section */}
        <div style={{
          backgroundColor: '#1f2937', padding: '20px 30px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <h2 style={{ margin: 0, color: 'white', fontSize: '20px', fontWeight: '600' }}>
            Analyst Dashboard
          </h2>
          <button 
            onClick={handleLogout}
            style={{
              backgroundColor: '#ef4444', color: 'white', border: 'none', padding: '8px 16px',
              borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: 'pointer'
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
          <div style={{ flex: '2', minWidth: '350px' }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#374151', fontSize: '16px', borderBottom: '1px solid #e5e7eb', paddingBottom: '8px' }}>
              My Watchlist & Live Markets
            </h3>
            
            <form onSubmit={handleAddStock} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
              <input 
                type="text" 
                placeholder="e.g. AAPL, RELIANCE.NS, TSLA" 
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
                Add Stock
              </button>
            </form>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {watchlist.length > 0 ? (
                watchlist.map((item) => {
                  const liveData = stockDetails[item.stock_symbol];
                  
                  return (
                    <div key={item.id} style={{ 
                      backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', 
                      padding: '16px', borderRadius: '8px', 
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                    }}>
                      <div>
                        <div style={{ fontWeight: '700', color: '#0f172a', fontSize: '16px' }}>
                          {item.stock_symbol}
                        </div>
                        <div style={{ color: '#64748b', fontSize: '13px', marginTop: '4px' }}>
                          {liveData ? liveData.company_name : 'Loading data...'}
                        </div>
                        {/* NEW: Remove Button */}
                        <button 
                          onClick={() => handleDeleteStock(item.id)}
                          style={{
                            background: 'none', border: 'none', color: '#ef4444', 
                            fontSize: '12px', padding: 0, marginTop: '8px', 
                            cursor: 'pointer', textDecoration: 'underline'
                          }}
                        >
                          Remove
                        </button>
                      </div>
                      
                      <div style={{ textAlign: 'right' }}>
                        {liveData ? (
                          <div style={{ fontWeight: '600', color: '#10b981', fontSize: '18px' }}>
                            {liveData.current_price.toFixed(2)} <span style={{ fontSize: '12px', color: '#64748b' }}>{liveData.currency}</span>
                          </div>
                        ) : (
                          <div style={{ color: '#94a3b8', fontSize: '14px' }}>--</div>
                        )}
                      </div>
                    </div>
                  );
                })
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