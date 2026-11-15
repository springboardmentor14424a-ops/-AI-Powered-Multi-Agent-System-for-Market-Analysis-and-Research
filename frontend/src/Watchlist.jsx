import React, { useState, useEffect } from 'react';

export default function Watchlist() {
  const [watchlist, setWatchlist] = useState([]);
  const [ticker, setTicker] = useState('');
  const [market, setMarket] = useState('NASDAQ');
  const [message, setMessage] = useState('');

  const token = localStorage.getItem('token');

  const fetchWatchlist = async () => {
    try {
      const response = await fetch('http://localhost:8001/watchlist', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setWatchlist(data);
      }
    } catch (err) {
      console.error('Failed to fetch watchlist');
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const handleAddTicker = async (e) => {
    e.preventDefault();
    setMessage('');

    try {
      const response = await fetch('http://localhost:8001/watchlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ ticker, market })
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`Successfully added ${data.ticker} to watchlist!`);
        setTicker('');
        fetchWatchlist();
      } else {
        setMessage(`Error: ${data.detail || 'Failed to add'}`);
      }
    } catch (err) {
      setMessage('Error: Could not connect to server');
    }
  };

  const handleDelete = async (id) => {
    try {
      const response = await fetch(`http://localhost:8001/watchlist/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        fetchWatchlist();
      }
    } catch (err) {
      console.error('Failed to delete item');
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '20px auto', padding: '20px', background: '#fff', borderRadius: '8px', color: '#333' }}>
      <h3>My Stock Watchlist</h3>
      
      <form onSubmit={handleAddTicker} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <input
          type="text"
          placeholder="Ticker (e.g. AAPL)"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          required
          style={{ padding: '8px', flex: 1 }}
        />
        <input
          type="text"
          placeholder="Market"
          value={market}
          onChange={(e) => setMarket(e.target.value)}
          required
          style={{ padding: '8px', width: '100px' }}
        />
        <button type="submit" style={{ padding: '8px 16px', background: '#007bff', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Add
        </button>
      </form>

      {message && <p style={{ fontWeight: 'bold', color: message.includes('Error') ? 'red' : 'green' }}>{message}</p>}

      <ul style={{ listStyle: 'none', padding: 0 }}>
        {watchlist.length === 0 ? (
          <p>No stocks in your watchlist yet.</p>
        ) : (
          watchlist.map((item) => (
            <li key={item.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', borderBottom: '1px solid #ddd', alignItems: 'center' }}>
              <span><strong>{item.ticker}</strong> ({item.market})</span>
              <button onClick={() => handleDelete(item.id)} style={{ background: '#dc3545', color: '#fff', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer' }}>
                Remove
              </button>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}