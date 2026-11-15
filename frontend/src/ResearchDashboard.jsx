import React, { useState, useEffect } from 'react';
import Watchlist from './Watchlist';
import Preferences from './Preferences';

export default function ResearchDashboard({ onLogout }) {
  const [ticker, setTicker] = useState('');
  const [market, setMarket] = useState('NASDAQ');
  const [period, setPeriod] = useState('1y');
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  
  // Navigation state: 'research', 'watchlist', or 'preferences'
  const [activeTab, setActiveTab] = useState('research');

  useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search);
    const tokenParam = queryParams.get('token');
    if (tokenParam) {
      localStorage.setItem('token', tokenParam);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const token = localStorage.getItem('token');

  const fetchHistory = async () => {
    try {
      const res = await fetch('http://localhost:8001/research/history', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    try {
      const res = await fetch('http://localhost:8001/research', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ticker: ticker,
          market: market,
          requested_period: period
        })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to create research task');
      }

      setSuccessMessage(`Successfully added ${data.ticker}! Status: ${data.status}`);
      setTicker('');
      fetchHistory();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'Arial, sans-serif', background: '#f8f9fa' }}>
      
      {/* Sidebar Navigation */}
      <div style={{ width: '250px', background: '#ffffff', borderRight: '1px solid #dee2e6', padding: '2rem 1rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '2rem', color: '#333' }}>📈 Stock Analyst</h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <button 
              onClick={() => setActiveTab('research')} 
              style={{ padding: '0.75rem 1rem', textAlign: 'left', background: activeTab === 'research' ? '#007BFF' : 'transparent', color: activeTab === 'research' ? '#fff' : '#333', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
              📊 Research & History
            </button>
            <button 
              onClick={() => setActiveTab('watchlist')} 
              style={{ padding: '0.75rem 1rem', textAlign: 'left', background: activeTab === 'watchlist' ? '#007BFF' : 'transparent', color: activeTab === 'watchlist' ? '#fff' : '#333', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
              ⭐ Watchlist
            </button>
            <button 
              onClick={() => setActiveTab('preferences')} 
              style={{ padding: '0.75rem 1rem', textAlign: 'left', background: activeTab === 'preferences' ? '#007BFF' : 'transparent', color: activeTab === 'preferences' ? '#fff' : '#333', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
              ⚙️ Preferences
            </button>
          </div>
        </div>

        {/* Logout Button at bottom of sidebar */}
        <button onClick={onLogout} style={{ padding: '0.75rem 1rem', background: '#dc3545', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
          Logout
        </button>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, padding: '2.5rem', maxWidth: '900px', margin: '0 auto' }}>
        
        {/* TAB 1: RESEARCH & HISTORY */}
        {activeTab === 'research' && (
          <div>
            <h2>Stock Research Dashboard</h2>
            <p style={{ color: '#666', marginBottom: '2rem' }}>Analyze live market data and review your search history.</p>
            
            <form onSubmit={handleSubmit} style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', border: '1px solid #dee2e6', marginBottom: '2rem' }}>
              <h3>New Research Task</h3>
              {error && <p style={{ color: 'red' }}>{error}</p>}
              {successMessage && <p style={{ color: 'green' }}>{successMessage}</p>}
              
              <div style={{ marginBottom: '1rem', marginTop: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Ticker Symbol: </label>
                <input 
                  type="text" 
                  value={ticker} 
                  onChange={(e) => setTicker(e.target.value)} 
                  placeholder="e.g. AAPL, TSLA" 
                  required 
                  style={{ padding: '0.5rem', width: '100%', borderRadius: '4px', border: '1px solid #ccc' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Market: </label>
                <input 
                  type="text" 
                  value={market} 
                  onChange={(e) => setMarket(e.target.value)} 
                  style={{ padding: '0.5rem', width: '100%', borderRadius: '4px', border: '1px solid #ccc' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Requested Period: </label>
                <input 
                  type="text" 
                  value={period} 
                  onChange={(e) => setPeriod(e.target.value)} 
                  style={{ padding: '0.5rem', width: '100%', borderRadius: '4px', border: '1px solid #ccc' }}
                />
              </div>

              <button type="submit" style={{ padding: '0.7rem 1.5rem', background: '#007BFF', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                Run Research
              </button>
            </form>

            <h3>Your Research History</h3>
            {history.length === 0 ? (
              <p style={{ color: '#666' }}>No research history found. Run your first stock search above!</p>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {history.map((item) => (
                  <li key={item.id} style={{ background: '#fff', border: '1px solid #dee2e6', padding: '1rem', marginBottom: '0.5rem', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong>{item.ticker}</strong> ({item.market}) — Period: {item.requested_period}
                      {item.result_price && <span style={{ marginLeft: '10px', color: '#555' }}>| Price: <strong>${item.result_price}</strong></span>}
                    </div>
                    <div>
                      Status: <span style={{ color: item.status === 'Completed' ? 'green' : item.status === 'Failed' ? 'red' : 'orange', fontWeight: 'bold' }}>{item.status}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* TAB 2: WATCHLIST */}
        {activeTab === 'watchlist' && (
          <div>
            <Watchlist />
          </div>
        )}

        {/* TAB 3: PREFERENCES */}
        {activeTab === 'preferences' && (
          <div>
            <Preferences />
          </div>
        )}

      </div>
    </div>
  );
}