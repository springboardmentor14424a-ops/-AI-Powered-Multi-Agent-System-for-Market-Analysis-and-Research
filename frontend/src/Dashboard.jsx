import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function Dashboard() {
  const [data, setData] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [stockDetails, setStockDetails] = useState({});
  const [researchHistory, setResearchHistory] = useState([]);
  const [newStock, setNewStock] = useState('');
  
  const [preferredMarket, setPreferredMarket] = useState('NASDAQ');
  const [preferredPeriod, setPreferredPeriod] = useState('1 Year');
  
  const navigate = useNavigate();

  const fetchHistory = async (token) => {
    try {
      const response = await fetch('http://127.0.0.1:8000/research/history', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const result = await response.json();
        setResearchHistory(result.history);
      }
    } catch (err) {
      console.error("Failed to fetch history");
    }
  };

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
          setPreferredMarket(result.preferred_market);
          setPreferredPeriod(result.preferred_period);
        } else {
          throw new Error('Session expired.');
        }

        const watchResponse = await fetch('http://127.0.0.1:8000/watchlist', {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (watchResponse.ok) {
          const watchResult = await watchResponse.json();
          setWatchlist(watchResult.watchlist);
          watchResult.watchlist.forEach((item) => {
            fetchLivePrice(item.stock_symbol, token);
          });
        }

        // Fetch Research History
        fetchHistory(token);

      } catch (err) {
        localStorage.removeItem('token');
        navigate('/');
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
        setStockDetails(prev => ({ ...prev, [symbol]: result }));
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
      }
    } catch (err) {
      alert("Error connecting to the server.");
    }
  };

  const handleDeleteStock = async (itemId) => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`http://127.0.0.1:8000/watchlist/${itemId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setWatchlist(watchlist.filter(item => item.id !== itemId));
      }
    } catch (err) {
      alert("Error connecting to the server.");
    }
  };

  const handlePreferenceChange = async (field, value) => {
    if (field === 'market') setPreferredMarket(value);
    if (field === 'period') setPreferredPeriod(value);

    const token = localStorage.getItem('token');
    try {
      await fetch('http://127.0.0.1:8000/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          preferred_market: field === 'market' ? value : preferredMarket,
          preferred_period: field === 'period' ? value : preferredPeriod
        })
      });
    } catch (err) {
      console.error("Failed to save preferences");
    }
  };

  // NEW: Launch Research Function
  const handleLaunchResearch = async (ticker) => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch('http://127.0.0.1:8000/research/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ ticker: ticker })
      });

      if (response.ok) {
        alert(`Research started for ${ticker}!`);
        fetchHistory(token); // Instantly refresh the history table
      } else {
        alert("Failed to start research.");
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
        maxWidth: '1000px', margin: '0 auto', backgroundColor: 'white',
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
          
          {/* Left Column: Account & Preferences */}
          <div style={{ flex: '1', minWidth: '250px' }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#374151', fontSize: '16px', borderBottom: '1px solid #e5e7eb', paddingBottom: '8px' }}>
              Account Details
            </h3>
            {data ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '30px' }}>
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

            <h3 style={{ margin: '0 0 16px 0', color: '#374151', fontSize: '16px', borderBottom: '1px solid #e5e7eb', paddingBottom: '8px' }}>
              Research Preferences
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ color: '#6b7280', fontSize: '13px', fontWeight: '500' }}>Default Market</label>
                <select 
                  value={preferredMarket} 
                  onChange={(e) => handlePreferenceChange('market', e.target.value)}
                  style={{ padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '14px', outline: 'none' }}
                >
                  <option value="NSE">NSE (India)</option>
                  <option value="BSE">BSE (India)</option>
                  <option value="NASDAQ">NASDAQ (US)</option>
                  <option value="NYSE">NYSE (US)</option>
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ color: '#6b7280', fontSize: '13px', fontWeight: '500' }}>Analysis Period</label>
                <select 
                  value={preferredPeriod} 
                  onChange={(e) => handlePreferenceChange('period', e.target.value)}
                  style={{ padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '14px', outline: 'none' }}
                >
                  <option value="1 Month">1 Month</option>
                  <option value="3 Months">3 Months</option>
                  <option value="6 Months">6 Months</option>
                  <option value="1 Year">1 Year</option>
                  <option value="5 Years">5 Years</option>
                </select>
              </div>
            </div>
          </div>

          {/* Right Column: Watchlist */}
          <div style={{ flex: '2', minWidth: '350px' }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#374151', fontSize: '16px', borderBottom: '1px solid #e5e7eb', paddingBottom: '8px' }}>
              My Watchlist & Live Markets
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
                        <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
                          {/* NEW: Launch Research Button */}
                          <button 
                            onClick={() => handleLaunchResearch(item.stock_symbol)}
                            style={{
                              background: 'none', border: 'none', color: '#2563eb', 
                              fontSize: '12px', padding: 0, cursor: 'pointer', fontWeight: '600'
                            }}
                          >
                            Launch Research
                          </button>
                          <button 
                            onClick={() => handleDeleteStock(item.id)}
                            style={{
                              background: 'none', border: 'none', color: '#ef4444', 
                              fontSize: '12px', padding: 0, cursor: 'pointer', textDecoration: 'underline'
                            }}
                          >
                            Remove
                          </button>
                        </div>
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
          
          {/* NEW: Research History Section */}
          <div style={{ width: '100%', marginTop: '10px' }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#374151', fontSize: '16px', borderBottom: '1px solid #e5e7eb', paddingBottom: '8px' }}>
              Research History
            </h3>
            
            {researchHistory.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f9fafb', color: '#4b5563', borderBottom: '2px solid #e5e7eb' }}>
                      <th style={{ padding: '12px 16px', fontWeight: '600' }}>Ticker</th>
                      <th style={{ padding: '12px 16px', fontWeight: '600' }}>Market</th>
                      <th style={{ padding: '12px 16px', fontWeight: '600' }}>Period</th>
                      <th style={{ padding: '12px 16px', fontWeight: '600' }}>Date</th>
                      <th style={{ padding: '12px 16px', fontWeight: '600' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {researchHistory.map((task) => (
                      <tr key={task.task_id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <td style={{ padding: '12px 16px', fontWeight: '500', color: '#111827' }}>{task.ticker}</td>
                        <td style={{ padding: '12px 16px', color: '#6b7280' }}>{task.market}</td>
                        <td style={{ padding: '12px 16px', color: '#6b7280' }}>{task.requested_period}</td>
                        <td style={{ padding: '12px 16px', color: '#6b7280' }}>{new Date(task.created_at).toLocaleDateString()}</td>
                        <td style={{ padding: '12px 16px' }}>
                          <span style={{ 
                            backgroundColor: '#fef3c7', color: '#d97706', 
                            padding: '2px 8px', borderRadius: '12px', fontSize: '12px', fontWeight: '600' 
                          }}>
                            {task.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ color: '#6b7280', fontSize: '14px', fontStyle: 'italic', backgroundColor: '#f9fafb', padding: '20px', borderRadius: '8px', textAlign: 'center' }}>
                No research tasks yet. Click "Launch Research" on a saved stock to begin.
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

export default Dashboard;