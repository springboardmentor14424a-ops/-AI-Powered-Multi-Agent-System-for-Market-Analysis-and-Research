import React, { useState, useEffect } from 'react';

export default function Preferences() {
  const [market, setMarket] = useState('NASDAQ');
  const [period, setPeriod] = useState('1y');
  const [message, setMessage] = useState('');

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetch('http://localhost:8001/preferences', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        if (data.default_market) setMarket(data.default_market);
        if (data.default_period) setPeriod(data.default_period);
      })
      .catch(err => console.error('Failed to load preferences'));
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setMessage('');

    try {
      const response = await fetch('http://localhost:8001/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ default_market: market, default_period: period })
      });

      if (response.ok) {
        setMessage('Preferences saved successfully!');
      } else {
        setMessage('Failed to save preferences');
      }
    } catch (err) {
      setMessage('Error connecting to server');
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '20px auto', padding: '20px', background: '#fff', borderRadius: '8px', color: '#333' }}>
      <h3>Workspace Preferences</h3>
      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Default Market:</label>
          <select value={market} onChange={(e) => setMarket(e.target.value)} style={{ padding: '8px', width: '100%' }}>
            <option value="NASDAQ">NASDAQ (US)</option>
            <option value="NYSE">NYSE (US)</option>
            <option value="NSE">NSE (India)</option>
            <option value="BSE">BSE (India)</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Default Analysis Period:</label>
          <select value={period} onChange={(e) => setPeriod(e.target.value)} style={{ padding: '8px', width: '100%' }}>
            <option value="1mo">1 Month</option>
            <option value="3mo">3 Months</option>
            <option value="6mo">6 Months</option>
            <option value="1y">1 Year</option>
            <option value="5y">5 Years</option>
          </select>
        </div>

        <button type="submit" style={{ padding: '10px', background: '#28a745', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
          Save Preferences
        </button>
      </form>
      {message && <p style={{ marginTop: '10px', color: message.includes('success') ? 'green' : 'red', fontWeight: 'bold' }}>{message}</p>}
    </div>
  );
}