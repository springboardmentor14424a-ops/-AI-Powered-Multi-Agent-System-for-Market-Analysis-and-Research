import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

function Dashboard() {
  const [data, setData] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [stockDetails, setStockDetails] = useState({});
  const [researchHistory, setResearchHistory] = useState([]);
  const [newStock, setNewStock] = useState('');

  const [preferredMarket, setPreferredMarket] = useState('NASDAQ');
  const [preferredPeriod, setPreferredPeriod] = useState('1 Year');

  // Module 2: Stock Search & Market Data state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [marketData, setMarketData] = useState(null);
  const [isLoadingMarketData, setIsLoadingMarketData] = useState(false);
  const [marketError, setMarketError] = useState('');
  const [activeFinTab, setActiveFinTab] = useState('income_statement');

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
        fetchHistory(token);
      } else {
        alert("Failed to start research.");
      }
    } catch (err) {
      alert("Error connecting to the server.");
    }
  };

  // Module 2: Search Companies by Name or Ticker
  const handleSearchStocks = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    const token = localStorage.getItem('token');
    setIsSearching(true);
    setMarketError('');

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/stocks/search?query=${encodeURIComponent(searchQuery.trim())}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (response.ok) {
        const result = await response.json();
        setSearchResults(result.results || []);
      } else {
        setMarketError('Failed to search stocks.');
      }
    } catch (err) {
      setMarketError('Error connecting to the server.');
    } finally {
      setIsSearching(false);
    }
  };

  // Module 2: Fetch Full Market Data (OHLCV + Profile + Financials + Validation)
  const handleLoadMarketData = async (symbol) => {
    const token = localStorage.getItem('token');
    setIsLoadingMarketData(true);
    setMarketError('');

    try {
      const params = new URLSearchParams({
        market: preferredMarket,
        period: preferredPeriod
      });
      const response = await fetch(
        `http://127.0.0.1:8000/stocks/data/${encodeURIComponent(symbol)}?${params.toString()}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (response.ok) {
        const result = await response.json();
        setMarketData(result);
        setActiveFinTab('income_statement');
      } else {
        const errData = await response.json();
        setMarketError(errData.detail || `Could not load market data for ${symbol}`);
      }
    } catch (err) {
      setMarketError('Error connecting to the server.');
    } finally {
      setIsLoadingMarketData(false);
    }
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    if (Math.abs(num) >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
    if (Math.abs(num) >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (Math.abs(num) >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    return num.toLocaleString();
  };

  const renderFinancialTable = () => {
    if (!marketData || !marketData.financials) return null;
    const statement = marketData.financials[activeFinTab] || {};
    const dates = Object.keys(statement);

    if (dates.length === 0) {
      return <div style={{ color: '#6b7280', fontSize: '13px' }}>No statement data available for this symbol.</div>;
    }

    const latestDate = dates[0];
    const entries = Object.entries(statement[latestDate] || {})
      .filter(([, val]) => val !== null)
      .slice(0, 10);

    return (
      <div style={{ overflowX: 'auto' }}>
        <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px' }}>
          Showing top metrics for period ending: <strong>{latestDate}</strong>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
          <thead>
            <tr style={{ backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
              <th style={{ padding: '8px 12px', color: '#4b5563' }}>Metric</th>
              <th style={{ padding: '8px 12px', color: '#4b5563', textAlign: 'right' }}>Value</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([metric, value]) => (
              <tr key={metric} style={{ borderBottom: '1px solid #f3f4f6' }}>
                <td style={{ padding: '8px 12px', color: '#111827' }}>{metric}</td>
                <td style={{ padding: '8px 12px', textAlign: 'right', fontWeight: '500', color: '#1f2937' }}>
                  {formatNumber(value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div style={{
      minHeight: '100vh', backgroundColor: '#f3f4f6',
      fontFamily: '"Inter", "Segoe UI", sans-serif', padding: '40px 20px'
    }}>
      <div style={{
        maxWidth: '1050px', margin: '0 auto', backgroundColor: 'white',
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
                          <button
                            onClick={() => handleLoadMarketData(item.stock_symbol)}
                            style={{
                              background: 'none', border: 'none', color: '#059669',
                              fontSize: '12px', padding: 0, cursor: 'pointer', fontWeight: '600'
                            }}
                          >
                            View Market Data
                          </button>
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

          {/* MODULE 2: Stock Search & Market Data Explorer */}
          <div style={{ width: '100%', marginTop: '10px' }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#374151', fontSize: '16px', borderBottom: '1px solid #e5e7eb', paddingBottom: '8px' }}>
              Stock Search & Market Data Explorer
            </h3>

            <form onSubmit={handleSearchStocks} style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
              <input
                type="text"
                placeholder="Search by company name or ticker (e.g. Apple, Reliance, TCS)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  flex: 1, padding: '10px 12px', fontSize: '14px',
                  border: '1px solid #d1d5db', borderRadius: '6px', outline: 'none'
                }}
              />
              <button
                type="submit"
                disabled={isSearching}
                style={{
                  backgroundColor: '#0f172a', color: 'white', border: 'none',
                  padding: '10px 20px', borderRadius: '6px', fontWeight: '500', cursor: 'pointer'
                }}
              >
                {isSearching ? 'Searching...' : 'Search'}
              </button>
            </form>

            {marketError && (
              <div style={{ backgroundColor: '#fef2f2', color: '#b91c1c', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', marginBottom: '16px' }}>
                {marketError}
              </div>
            )}

            {/* Search Results List */}
            {searchResults.length > 0 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '10px', marginBottom: '20px' }}>
                {searchResults.map((res) => (
                  <div key={res.symbol} style={{
                    border: '1px solid #e5e7eb', borderRadius: '8px', padding: '12px',
                    backgroundColor: '#f9fafb', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '8px'
                  }}>
                    <div>
                      <div style={{ fontWeight: '700', color: '#111827', fontSize: '14px' }}>{res.symbol}</div>
                      <div style={{ color: '#4b5563', fontSize: '12px', marginTop: '2px' }}>{res.name}</div>
                      <div style={{ color: '#9ca3af', fontSize: '11px', marginTop: '2px' }}>Exchange: {res.exchange || 'N/A'}</div>
                    </div>
                    <button
                      onClick={() => handleLoadMarketData(res.symbol)}
                      style={{
                        backgroundColor: '#2563eb', color: 'white', border: 'none',
                        padding: '6px 10px', borderRadius: '5px', fontSize: '12px', fontWeight: '500', cursor: 'pointer'
                      }}
                    >
                      Load Market Data
                    </button>
                  </div>
                ))}
              </div>
            )}

            {isLoadingMarketData && (
              <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
                Fetching historical OHLCV, company profile, and financial statements...
              </div>
            )}

            {/* Market Data Details Panel */}
            {marketData && !isLoadingMarketData && (
              <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '20px', backgroundColor: '#ffffff' }}>
                {/* Company Header & Metadata */}
                <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', borderBottom: '1px solid #e5e7eb', paddingBottom: '14px', marginBottom: '16px' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '18px', color: '#111827' }}>
                      {marketData.profile.company_name} ({marketData.metadata.resolved_symbol})
                    </h4>
                    <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '4px' }}>
                      {marketData.profile.sector || 'N/A'} • {marketData.profile.industry || 'N/A'} • Market Cap: {formatNumber(marketData.profile.market_cap)} {marketData.profile.currency}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', fontSize: '12px', color: '#6b7280' }}>
                    <div>Source: <strong>{marketData.metadata.source}</strong></div>
                    <div>Retrieved: {new Date(marketData.metadata.retrieved_at).toLocaleString()}</div>
                  </div>
                </div>

                {/* Data Validation Summary */}
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '20px' }}>
                  <span style={{ backgroundColor: '#ecfdf5', color: '#065f46', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '600' }}>
                    Valid OHLCV Rows: {marketData.validation.total_rows_clean}
                  </span>
                  <span style={{ backgroundColor: '#f3f4f6', color: '#374151', padding: '4px 10px', borderRadius: '6px', fontSize: '12px' }}>
                    Duplicates Removed: {marketData.validation.duplicate_dates_removed}
                  </span>
                  <span style={{ backgroundColor: '#f3f4f6', color: '#374151', padding: '4px 10px', borderRadius: '6px', fontSize: '12px' }}>
                    Missing Dropped: {marketData.validation.missing_values_dropped}
                  </span>
                  <span style={{ backgroundColor: '#f3f4f6', color: '#374151', padding: '4px 10px', borderRadius: '6px', fontSize: '12px' }}>
                    Inconsistent Removed: {marketData.validation.inconsistent_rows_removed}
                  </span>
                </div>

                {/* Historical Stock Price Chart */}
                <h5 style={{ margin: '0 0 10px 0', color: '#374151', fontSize: '14px' }}>
                  Historical Closing Price ({marketData.metadata.period})
                </h5>
                <div style={{ width: '100%', height: 280, marginBottom: '24px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={marketData.ohlcv} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} minTickGap={30} />
                      <YAxis
                        domain={['auto', 'auto']}
                        tick={{ fontSize: 11, fill: '#6b7280' }}
                        tickFormatter={(val) => val.toFixed(0)}
                      />
                      <Tooltip
                        formatter={(value) => [`${Number(value).toFixed(2)} ${marketData.profile.currency}`, 'Close']}
                        labelStyle={{ color: '#111827', fontWeight: '600' }}
                      />
                      <Area
                        type="monotone"
                        dataKey="close"
                        stroke="#2563eb"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#priceGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Recent Historical OHLCV Table (Latest 10 Days) */}
                <h5 style={{ margin: '0 0 10px 0', color: '#374151', fontSize: '14px' }}>
                  Recent Historical Prices (OHLCV — Last 10 Trading Days)
                </h5>
                <div style={{ overflowX: 'auto', marginBottom: '24px' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'right' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb', color: '#4b5563' }}>
                        <th style={{ padding: '8px 10px', textAlign: 'left' }}>Date</th>
                        <th style={{ padding: '8px 10px' }}>Open</th>
                        <th style={{ padding: '8px 10px' }}>High</th>
                        <th style={{ padding: '8px 10px' }}>Low</th>
                        <th style={{ padding: '8px 10px' }}>Close</th>
                        <th style={{ padding: '8px 10px' }}>Volume</th>
                      </tr>
                    </thead>
                    <tbody>
                      {marketData.ohlcv.slice(-10).reverse().map((row) => (
                        <tr key={row.date} style={{ borderBottom: '1px solid #f3f4f6' }}>
                          <td style={{ padding: '8px 10px', textAlign: 'left', fontWeight: '500' }}>{row.date}</td>
                          <td style={{ padding: '8px 10px' }}>{row.open.toFixed(2)}</td>
                          <td style={{ padding: '8px 10px' }}>{row.high.toFixed(2)}</td>
                          <td style={{ padding: '8px 10px' }}>{row.low.toFixed(2)}</td>
                          <td style={{ padding: '8px 10px', fontWeight: '600', color: '#111827' }}>{row.close.toFixed(2)}</td>
                          <td style={{ padding: '8px 10px', color: '#6b7280' }}>{row.volume.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Financial Statements Tabs */}
                <h5 style={{ margin: '0 0 10px 0', color: '#374151', fontSize: '14px' }}>
                  Financial Statements
                </h5>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                  {[
                    { key: 'income_statement', label: 'Income Statement' },
                    { key: 'balance_sheet', label: 'Balance Sheet' },
                    { key: 'cash_flow', label: 'Cash Flow' }
                  ].map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveFinTab(tab.key)}
                      style={{
                        padding: '6px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: '600', cursor: 'pointer',
                        border: activeFinTab === tab.key ? '1px solid #2563eb' : '1px solid #d1d5db',
                        backgroundColor: activeFinTab === tab.key ? '#eff6ff' : 'white',
                        color: activeFinTab === tab.key ? '#1d4ed8' : '#374151'
                      }}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
                {renderFinancialTable()}
              </div>
            )}
          </div>

          {/* Research History Section */}
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