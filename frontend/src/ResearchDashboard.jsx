import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'; 
import Watchlist from './Watchlist';
import Preferences from './Preferences';

export default function ResearchDashboard({ onLogout }) {
  const [ticker, setTicker] = useState('');
  const [market, setMarket] = useState('NASDAQ');
  const [period, setPeriod] = useState('1y');
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [activeResult, setActiveResult] = useState(null);
  const [ohlcvData, setOhlcvData] = useState([]);
  
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
    setActiveResult(null);
    setOhlcvData([]);

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
      setActiveResult(data); 
      if (data.ohlcv) {
        setOhlcvData(data.ohlcv); 
      }
      
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
            <p style={{ color: '#000000', marginBottom: '2rem' }}>Analyze live market data and review your search history.</p>
            
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
                <select
                  value={market}
                  onChange={(e) => setMarket(e.target.value)}
                  style={{ padding: '0.5rem', width: '100%', borderRadius: '4px', border: '1px solid #ccc' }}
                >
                  <option value="NSE">NSE (India)</option>
                  <option value="BSE">BSE (India)</option>
                  <option value="Nasdaq">Nasdaq (US)</option>
                  <option value="NYSE">NYSE (US)</option>
                  </select>
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

          {/* --- OHLCV --- */}
            {activeResult && (
              <div style={{ background: '#380505', padding: '1.5rem', borderRadius: '8px', border: '1px solid #dee2e6', marginBottom: '2rem' }}>
                <h3 style={{ color: '#ffffff' }}>📊 Company Profile: {activeResult.ticker}</h3>
                <p>
                <strong>Market:</strong> {activeResult.market} | <strong>Period:</strong> {activeResult.requested_period}
                  {activeResult.result_price && <> | <strong>Latest Close:</strong> ${activeResult.result_price.toFixed(2)}</>}
                </p>
                {activeResult.company_name && <p><strong>Name:</strong> {activeResult.company_name}</p>}

                {activeResult.profile && (
                  <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '6px', marginTop: '0.75rem', border: '1px solid #00060c' }}>
                    <p style={{ margin: '0 0 0.5rem 0' }}>
                      <strong>Sector:</strong> {activeResult.profile.sector} | <strong>Industry:</strong> {activeResult.profile.industry}
                      {activeResult.profile.market_cap && (
                        <> | <strong>Market Cap:</strong> ${(activeResult.profile.market_cap / 1e9).toFixed(2)}B</>
                      )}
                    </p>
                    {activeResult.profile.website && activeResult.profile.website !== 'N/A' && (
                      <p style={{ margin: '0 0 0.5rem 0' }}>
                        <strong>Website:</strong> <a href={activeResult.profile.website} target="_blank" rel="noreferrer">{activeResult.profile.website}</a>
                      </p>
                )}
                    <p style={{ margin: 0, fontSize: '0.9rem', color: '#0c0d0f', lineHeight: '1.5' }}>
                      {activeResult.profile.summary}
                    </p>
                  </div>
                )}

                {/* --- LIVE STOCK PRICE CHART --- */}
                <h4 style={{ marginTop: '1.5rem', marginBottom: '0.75rem', color: '#ffffff' }}>Price Trend (Closing Price)</h4>
                {ohlcvData.length === 0 ? (
                  <p style={{ color: '#f8f3f3' }}>No chart data available.</p>
                ) : (
                  <div style={{ width: '100%', height: '300px', marginBottom: '2rem' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={ohlcvData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f3f5" />
                        <XAxis dataKey="Date" tick={{ fontSize: 12 }} />
                        <YAxis domain={['auto', 'auto']} tick={{ fontSize: 12 }} />
                        <Tooltip />
                        <Line 
                          type="monotone" 
                          dataKey="Close" 
                          stroke="#007BFF" 
                          strokeWidth={2} 
                          dot={false} 
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

               {/* TABLE DISPLAY */}
                <h4 style={{ marginTop: '1.5rem', marginBottom: '0.75rem', color: '#ffffff' }}>OHLCV Historical Data</h4>
                {ohlcvData.length === 0 ? (
                  <p style={{ color: '#0a0a0a' }}>No OHLCV records available for this query yet.</p>
                ) : (
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                      <thead>
                        <tr style={{ background: '#000000', textAlign: 'left' }}>
                          <th style={{ padding: '8px', borderBottom: '1px solid #ffffff' }}>Date</th>
                          <th style={{ padding: '8px', borderBottom: '1px solid #ffffff' }}>Open</th>
                          <th style={{ padding: '8px', borderBottom: '1px solid #ffffff' }}>High</th>
                          <th style={{ padding: '8px', borderBottom: '1px solid #ffffff' }}>Low</th>
                          <th style={{ padding: '8px', borderBottom: '1px solid #ffffff' }}>Close</th>
                          <th style={{ padding: '8px', borderBottom: '1px solid #ffffff' }}>Volume</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ohlcvData.map((row, index) => (
                          <tr key={index} style={{ borderBottom: '1px solid #ffffff' }}>
                            <td style={{ padding: '8px' }}>{row.Date}</td>
                            <td style={{ padding: '8px' }}>{row.Open?.toFixed(2)}</td>
                            <td style={{ padding: '8px' }}>{row.High?.toFixed(2)}</td>
                            <td style={{ padding: '8px' }}>{row.Low?.toFixed(2)}</td>
                            <td style={{ padding: '8px' }}>{row.Close?.toFixed(2)}</td>
                            <td style={{ padding: '8px' }}>{row.Volume?.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                {/* --- FINANCIAL STATEMENTS (INCOME STATEMENT) --- */}
                <h4 style={{ marginTop: '2rem', marginBottom: '0.75rem', color: '#ffffff' }}>📑 Key Financial Statements (Annual)</h4>
                {!activeResult.financials || activeResult.financials.length === 0 ? (
                  <p style={{ color: '#080000' }}>No financial statement records available for this ticker.</p>
                ) : (
                  <div style={{ overflowX: 'auto', marginBottom: '1.5rem' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                      <thead>
                        <tr style={{ background: '#000000', textAlign: 'left' }}>
                          <th style={{ padding: '8px', borderBottom: '1px solid #dee2e6' }}>Metric</th>
                          {Object.keys(activeResult.financials[0])
                            .filter((key) => key !== 'metric')
                            .map((dateCol) => (
                              <th key={dateCol} style={{ padding: '8px', borderBottom: '1px solid #dee2e6' }}>{dateCol}</th>
                              ))}
                        </tr>
                      </thead>
                      <tbody>
                          {activeResult.financials.map((row, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid #f1f3f5' }}>
                            <td style={{ padding: '8px', fontWeight: 'bold' }}>{row.metric}</td>
                            {Object.keys(row)
                                .filter((key) => key !== 'metric')
                              .map((dateCol) => (
                                <td key={dateCol} style={{ padding: '8px' }}>
                                  {row[dateCol] !== null && row[dateCol] !== undefined
                                    ? `$${(row[dateCol] / 1e6).toLocaleString(undefined, { maximumFractionDigits: 2 })}M`
                                    : 'N/A'}
                                </td>
                              ))}
                          </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* --- DATA SOURCE & RETRIEVAL TIMESTAMP --- */}
                <div style={{ marginTop: '1.5rem', paddingTop: '0.75rem', borderTop: '1px solid #dee2e6', fontSize: '0.85rem', color: '#6c757d', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <span><strong>Data Source:</strong> {activeResult.source || 'Yahoo Finance (yfinance)'}</span>
                  <span>
                    <strong>Retrieved At:</strong>{' '}
                    {activeResult.retrieved_at ? new Date(activeResult.retrieved_at).toLocaleString() : 'Just now'}
                  </span>
                  </div>
              </div>
            )}

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