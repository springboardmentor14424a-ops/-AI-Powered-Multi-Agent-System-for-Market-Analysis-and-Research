import React, { useState, useEffect, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';
import {
  Search, TrendingUp, TrendingDown, Calendar, BarChart2,
  Download, RefreshCw, Star, ArrowUpRight,
  ArrowDownRight, Loader2, Layers, Sliders,
  Building2, FileSpreadsheet, ShieldCheck, Clock, ExternalLink,
  Users, Globe, MapPin, DollarSign, Activity, FileText, Bot
} from 'lucide-react';
import api from '../api/axios';

const TIMEFRAMES = [
  { label: '1D', period: '1d', defaultInterval: '5m' },
  { label: '5D', period: '5d', defaultInterval: '15m' },
  { label: '1M', period: '1mo', defaultInterval: '1d' },
  { label: '3M', period: '3mo', defaultInterval: '1d' },
  { label: '6M', period: '6mo', defaultInterval: '1d' },
  { label: '1Y', period: '1y', defaultInterval: '1d' },
  { label: '5Y', period: '5y', defaultInterval: '1wk' },
];

const INTERVALS = [
  { label: '5 Min', value: '5m' },
  { label: '15 Min', value: '15m' },
  { label: 'Daily', value: '1d' },
  { label: 'Weekly', value: '1wk' },
  { label: 'Monthly', value: '1mo' },
];

function formatCurrency(val, currency = 'USD') {
  if (val === null || val === undefined) return '—';
  const sym = currency === 'INR' ? '₹' : '$';
  if (Math.abs(val) >= 1e12) return `${sym}${(val / 1e12).toFixed(2)}T`;
  if (Math.abs(val) >= 1e9) return `${sym}${(val / 1e9).toFixed(2)}B`;
  if (Math.abs(val) >= 1e7 && currency === 'INR') return `${sym}${(val / 1e7).toFixed(2)} Cr`;
  if (Math.abs(val) >= 1e6) return `${sym}${(val / 1e6).toFixed(2)}M`;
  return `${sym}${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPercent(val) {
  if (val === null || val === undefined) return '—';
  const num = typeof val === 'number' ? (val < 1 && val > -1 ? val * 100 : val) : parseFloat(val);
  return `${num.toFixed(2)}%`;
}

export default function MarketDataTab({ initialTicker = null, onStartResearch, onAnalyzeWithAgent }) {
  const [query, setQuery] = useState('');
  const [market, setMarket] = useState('ALL');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  // Active view tab: 'chart' | 'profile' | 'financials' | 'audit'
  const [activeSubTab, setActiveSubTab] = useState('chart');
  const [finStmtType, setFinStmtType] = useState('income'); // 'income' | 'balance' | 'cashflow'

  // Selected stock (null until user searches/selects)
  const [selectedStock, setSelectedStock] = useState(null);

  // OHLCV state
  const [period, setPeriod] = useState('1mo');
  const [interval, setInterval] = useState('1d');
  const [ohlcvData, setOhlcvData] = useState(null);
  const [loadingOHLCV, setLoadingOHLCV] = useState(false);
  const [hoveredBar, setHoveredBar] = useState(null);

  // Profile & Financials state
  const [profileData, setProfileData] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [financialsData, setFinancialsData] = useState(null);
  const [loadingFinancials, setLoadingFinancials] = useState(false);

  // Audit logs state
  const [auditLogs, setAuditLogs] = useState([]);
  const [loadingAuditLogs, setLoadingAuditLogs] = useState(false);

  // Supported stock markets metadata (NSE, BSE, NASDAQ, NYSE)
  const [supportedMarkets, setSupportedMarkets] = useState([
    {
      code: 'NSE',
      name: 'National Stock Exchange of India',
      country: 'India',
      country_code: 'IN',
      currency: 'INR',
      currency_symbol: '₹',
      index_name: 'NIFTY 50',
      trading_hours: '09:15 - 15:30 IST',
      popular_stocks: [
        { ticker: 'RELIANCE.NS', name: 'Reliance Industries', price: 1290.45, currency: 'INR' },
        { ticker: 'TCS.NS', name: 'Tata Consultancy Services', price: 4145.20, currency: 'INR' },
        { ticker: 'INFY.NS', name: 'Infosys Limited', price: 1860.50, currency: 'INR' },
        { ticker: 'HDFCBANK.NS', name: 'HDFC Bank Limited', price: 1740.00, currency: 'INR' },
        { ticker: 'TATAMOTORS.NS', name: 'Tata Motors Limited', price: 810.00, currency: 'INR' },
      ],
    },
    {
      code: 'BSE',
      name: 'Bombay Stock Exchange',
      country: 'India',
      country_code: 'IN',
      currency: 'INR',
      currency_symbol: '₹',
      index_name: 'S&P BSE SENSEX',
      trading_hours: '09:15 - 15:30 IST',
      popular_stocks: [
        { ticker: 'RELIANCE.BO', name: 'Reliance Industries', price: 1290.45, currency: 'INR' },
        { ticker: 'TCS.BO', name: 'Tata Consultancy Services', price: 4145.20, currency: 'INR' },
        { ticker: 'INFY.BO', name: 'Infosys Limited', price: 1860.50, currency: 'INR' },
        { ticker: 'HDFCBANK.BO', name: 'HDFC Bank Limited', price: 1740.00, currency: 'INR' },
      ],
    },
    {
      code: 'NASDAQ',
      name: 'NASDAQ Stock Market',
      country: 'United States',
      country_code: 'US',
      currency: 'USD',
      currency_symbol: '$',
      index_name: 'NASDAQ 100',
      trading_hours: '09:30 - 16:00 EST',
      popular_stocks: [
        { ticker: 'AAPL', name: 'Apple Inc.', price: 228.87, currency: 'USD' },
        { ticker: 'MSFT', name: 'Microsoft Corporation', price: 415.50, currency: 'USD' },
        { ticker: 'GOOGL', name: 'Alphabet Inc.', price: 175.25, currency: 'USD' },
        { ticker: 'NVDA', name: 'NVIDIA Corporation', price: 140.20, currency: 'USD' },
        { ticker: 'TSLA', name: 'Tesla, Inc.', price: 220.10, currency: 'USD' },
      ],
    },
    {
      code: 'NYSE',
      name: 'New York Stock Exchange',
      country: 'United States',
      country_code: 'US',
      currency: 'USD',
      currency_symbol: '$',
      index_name: 'S&P 500',
      trading_hours: '09:30 - 16:00 EST',
      popular_stocks: [
        { ticker: 'JPM', name: 'JPMorgan Chase & Co.', price: 242.15, currency: 'USD' },
        { ticker: 'BRK-B', name: 'Berkshire Hathaway Inc.', price: 452.30, currency: 'USD' },
        { ticker: 'DIS', name: 'The Walt Disney Company', price: 115.40, currency: 'USD' },
        { ticker: 'WMT', name: 'Walmart Inc.', price: 84.60, currency: 'USD' },
        { ticker: 'V', name: 'Visa Inc.', price: 310.25, currency: 'USD' },
      ],
    },
  ]);

  useEffect(() => {
    api.get('/stocks/markets')
      .then((res) => {
        if (Array.isArray(res.data) && res.data.length > 0) {
          setSupportedMarkets(res.data);
        }
      })
      .catch(() => {});
  }, []);

  const debounceRef = useRef(null);

  // Debounced search
  const handleSearch = useCallback((q, mkt) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!q.trim()) {
      setSearchResults([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await api.get('/stocks/search', {
          params: { q: q.trim(), market: mkt === 'ALL' ? undefined : mkt },
        });
        setSearchResults(res.data);
      } catch {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 400);
  }, []);

  const onQueryChange = (e) => {
    setQuery(e.target.value);
    handleSearch(e.target.value, market);
  };

  const onMarketSelect = (newMarket) => {
    setMarket(newMarket);
    handleSearch(query, newMarket);
    // Don't auto-select a stock — user must search and pick one
  };

  const onMarketChange = (e) => {
    onMarketSelect(e.target.value);
  };

  // Fetch OHLCV data
  const fetchOHLCV = useCallback(async (ticker, p, i, mkt) => {
    setLoadingOHLCV(true);
    try {
      const res = await api.get(`/stocks/ohlcv/${ticker}`, {
        params: { period: p, interval: i, market: mkt && mkt !== 'ALL' ? mkt : undefined },
      });
      setOhlcvData(res.data);
      if (res.data.company_name) {
        setSelectedStock((prev) => ({
          ...prev,
          ticker: res.data.ticker,
          company_name: res.data.company_name,
          market: res.data.market || prev.market,
          currency: res.data.currency || prev.currency,
        }));
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || `Failed to fetch OHLCV for ${ticker}`);
    } finally {
      setLoadingOHLCV(false);
    }
  }, []);

  // Fetch Company Profile
  const fetchProfile = useCallback(async (ticker, mkt) => {
    setLoadingProfile(true);
    try {
      const res = await api.get(`/stocks/profile/${ticker}`, {
        params: { market: mkt && mkt !== 'ALL' ? mkt : undefined },
      });
      setProfileData(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || `Failed to load profile for ${ticker}`);
    } finally {
      setLoadingProfile(false);
    }
  }, []);

  // Fetch Financial Statements
  const fetchFinancials = useCallback(async (ticker, mkt) => {
    setLoadingFinancials(true);
    try {
      const res = await api.get(`/stocks/financials/${ticker}`, {
        params: { market: mkt && mkt !== 'ALL' ? mkt : undefined },
      });
      setFinancialsData(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || `Failed to load financials for ${ticker}`);
    } finally {
      setLoadingFinancials(false);
    }
  }, []);

  // Fetch Audit Logs
  const fetchAuditLogs = useCallback(async (ticker) => {
    setLoadingAuditLogs(true);
    try {
      const res = await api.get('/stocks/audit-logs', {
        params: { ticker: ticker || undefined, limit: 30 },
      });
      setAuditLogs(res.data);
    } catch {
      toast.error('Failed to load audit provenance logs');
    } finally {
      setLoadingAuditLogs(false);
    }
  }, []);

  // No initial load — data loads only when user selects a stock or clicks from Watchlist
  useEffect(() => {
    if (initialTicker) {
      selectStockItem({
        ticker: initialTicker,
        company_name: initialTicker,
        market: market === 'ALL' ? 'NASDAQ' : market,
        currency: 'USD',
      });
    }
  }, [initialTicker]);

  const selectStockItem = (stock) => {
    setSelectedStock({
      ticker: stock.ticker,
      company_name: stock.company_name,
      market: stock.market,
      currency: stock.currency,
    });
    setSearchResults([]);
    setQuery('');
    fetchOHLCV(stock.ticker, period, interval, stock.market);
    fetchProfile(stock.ticker, stock.market);
    fetchFinancials(stock.ticker, stock.market);
    fetchAuditLogs(stock.ticker);
  };

  const handlePeriodChange = (tf) => {
    setPeriod(tf.period);
    setInterval(tf.defaultInterval);
    if (selectedStock) fetchOHLCV(selectedStock.ticker, tf.period, tf.defaultInterval, selectedStock.market);
  };

  const handleIntervalChange = (newInterval) => {
    setInterval(newInterval);
    if (selectedStock) fetchOHLCV(selectedStock.ticker, period, newInterval, selectedStock.market);
  };

  // Export CSV
  const exportCSV = () => {
    if (!selectedStock || !ohlcvData || !ohlcvData.data.length) return;
    const headers = ['Date', 'Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'];
    const rows = ohlcvData.data.map((b) => [
      b.date,
      b.timestamp,
      b.open,
      b.high,
      b.low,
      b.close,
      b.volume,
      b.adj_close ?? '',
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${selectedStock.ticker}_OHLCV_${period}_${interval}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('OHLCV CSV exported successfully!');
  };

  // Add to watchlist
  const addToWatchlist = async () => {
    if (!selectedStock) { toast.error('Please select a stock first.'); return; }
    try {
      await api.post('/watchlist', {
        ticker: selectedStock.ticker,
        company_name: selectedStock.company_name,
        market: selectedStock.market,
      });
      toast.success(`${selectedStock.ticker} added to Watchlist!`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add to watchlist');
    }
  };

  // Chart rendering helpers
  const bars = ohlcvData?.data || [];
  const minPrice = bars.length ? Math.min(...bars.map((b) => b.low)) : 0;
  const maxPrice = bars.length ? Math.max(...bars.map((b) => b.high)) : 1;
  const priceRange = maxPrice - minPrice || 1;
  const maxVolume = bars.length ? Math.max(...bars.map((b) => b.volume)) : 1;

  const chartWidth = 800;
  const chartHeight = 260;
  const volumeHeight = 60;
  const padding = { top: 20, right: 30, bottom: 25, left: 60 };

  const getCoordinates = (index, price) => {
    const x =
      padding.left +
      (index / Math.max(bars.length - 1, 1)) * (chartWidth - padding.left - padding.right);
    const y =
      padding.top +
      (1 - (price - minPrice) / priceRange) * (chartHeight - padding.top - padding.bottom);
    return { x, y };
  };

  const linePoints = bars.map((b, i) => {
    const { x, y } = getCoordinates(i, b.close);
    return `${x},${y}`;
  });

  const areaPath =
    bars.length > 0
      ? `M ${getCoordinates(0, bars[0].close).x},${chartHeight - padding.bottom} ` +
        bars.map((b, i) => `L ${getCoordinates(i, b.close).x},${getCoordinates(i, b.close).y}`).join(' ') +
        ` L ${getCoordinates(bars.length - 1, bars[bars.length - 1].close).x},${chartHeight - padding.bottom} Z`
      : '';

  const isNetPositive = (ohlcvData?.net_change || 0) >= 0;

  // Active provenance source info
  const activeProvenance = selectedStock ? (
    activeSubTab === 'profile'
      ? { source: profileData?.data_source, ts: profileData?.retrieval_timestamp }
      : activeSubTab === 'financials'
      ? { source: financialsData?.data_source, ts: financialsData?.retrieval_timestamp }
      : { source: ohlcvData?.data_source, ts: ohlcvData?.retrieval_timestamp }
  ) : { source: null, ts: null };

  const activeMarketInfo = supportedMarkets.find((m) => m.code === market);
  const currencySymbol = selectedStock?.currency === 'INR' ? '₹' : '$';

  return (
    <div className="space-y-6">
      {/* ─── Global Market Selector Bar: Support for NSE/BSE & NASDAQ/NYSE ─── */}
      <div className="bg-gray-900/80 border border-emerald-900/50 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <Globe className="w-5 h-5 text-emerald-400" />
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">Supported Stock Markets</h2>
              <p className="text-xs text-gray-400">Select market exchange to filter companies and calibrate financial currency</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400 font-medium">Active Market:</span>
            <span className="bg-emerald-950 text-emerald-300 border border-emerald-700/60 px-2.5 py-1 rounded-lg text-xs font-mono font-bold">
              {market === 'ALL' ? '🌐 ALL MARKETS' : `${activeMarketInfo?.country === 'India' ? '🇮🇳' : '🇺🇸'} ${market}`}
            </span>
          </div>
        </div>

        {/* Market Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
          {[
            { code: 'ALL', label: 'All Markets', flag: '🌐', subtitle: 'Global Search (Any)', badge: 'Multi-Currency' },
            { code: 'NSE', label: 'NSE (India)', flag: '🇮🇳', subtitle: 'National Stock Exchange', badge: 'NIFTY 50 • ₹ INR' },
            { code: 'BSE', label: 'BSE (India)', flag: '🇮🇳', subtitle: 'Bombay Stock Exchange', badge: 'SENSEX • ₹ INR' },
            { code: 'NASDAQ', label: 'NASDAQ', flag: '🇺🇸', subtitle: 'Tech & Growth Equities', badge: 'NDX 100 • $ USD' },
            { code: 'NYSE', label: 'NYSE', flag: '🇺🇸', subtitle: 'New York Stock Exchange', badge: 'S&P 500 • $ USD' },
          ].map((mkt) => (
            <button
              key={mkt.code}
              type="button"
              onClick={() => onMarketSelect(mkt.code)}
              className={`p-3 rounded-xl text-left border transition-all relative overflow-hidden group ${
                market === mkt.code
                  ? 'bg-emerald-600/20 border-emerald-500 text-white shadow-lg shadow-emerald-950/60 ring-1 ring-emerald-500/50'
                  : 'bg-gray-950/60 border-gray-800/80 text-gray-400 hover:text-white hover:border-emerald-800/60 hover:bg-gray-900/60'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-xs text-white">
                  <span className="text-sm">{mkt.flag}</span>
                  <span>{mkt.label}</span>
                </div>
                {market === mkt.code && (
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                )}
              </div>
              <p className="text-[11px] text-gray-400 mt-1 truncate">{mkt.subtitle}</p>
              <span className={`inline-block mt-1 text-[10px] font-mono px-1.5 py-0.5 rounded ${
                market === mkt.code
                  ? 'bg-emerald-900/80 text-emerald-200 border border-emerald-700/50'
                  : 'bg-gray-900 text-gray-500'
              }`}>
                {mkt.badge}
              </span>
            </button>
          ))}
        </div>

        {/* Selected Market Benchmark Details & Quick-Select Benchmark Stocks */}
        {activeMarketInfo && (
          <div className="bg-gray-950/90 border border-emerald-900/40 rounded-xl p-3.5 space-y-2.5">
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                <span className="font-bold text-white text-sm">{activeMarketInfo.name}</span>
                <span className="bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 px-2 py-0.5 rounded-md font-mono">
                  Currency: <strong>{activeMarketInfo.currency_symbol} {activeMarketInfo.currency}</strong>
                </span>
                {activeMarketInfo.index_name && (
                  <span className="bg-gray-900 text-gray-300 border border-gray-800 px-2 py-0.5 rounded-md font-mono">
                    Index: {activeMarketInfo.index_name}
                  </span>
                )}
                {activeMarketInfo.trading_hours && (
                  <span className="text-gray-400 flex items-center gap-1 font-mono">
                    <Clock className="w-3.5 h-3.5 text-emerald-400" />
                    {activeMarketInfo.trading_hours}
                  </span>
                )}
              </div>
            </div>

            {/* Popular Stocks Quick-Selection */}
            {activeMarketInfo.popular_stocks && activeMarketInfo.popular_stocks.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap pt-1 border-t border-emerald-900/20">
                <span className="text-[11px] text-emerald-400 font-semibold tracking-wider uppercase">
                  Quick Select Benchmark Equities:
                </span>
                {activeMarketInfo.popular_stocks.map((stock) => (
                  <button
                    key={stock.ticker}
                    type="button"
                    onClick={() => selectStockItem({
                      ticker: stock.ticker,
                      company_name: stock.name,
                      market: activeMarketInfo.code,
                      currency: activeMarketInfo.currency,
                    })}
                    className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all border flex items-center gap-1.5 ${
                      selectedStock?.ticker === stock.ticker
                        ? 'bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-950'
                        : 'bg-emerald-950/50 text-emerald-300 border-emerald-800/50 hover:bg-emerald-900/80 hover:text-white'
                    }`}
                  >
                    <span>{stock.ticker}</span>
                    {stock.price && (
                      <span className="text-[10px] opacity-80">
                        ({activeMarketInfo.currency_symbol}{stock.price})
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ─── Search Bar: Search by Company Name or Ticker Symbol ─── */}
      <div className="bg-gray-900/70 border border-emerald-900/40 rounded-2xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Search className="w-5 h-5 text-emerald-400" />
            <h2 className="text-base font-semibold text-white">Stock Search & Market Lookup</h2>
          </div>
          <span className="text-xs text-gray-400 hidden sm:inline">
            Search by Company Name (Apple, Reliance) or Ticker Symbol (AAPL, TCS)
          </span>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={onQueryChange}
              placeholder="Search companies by name or ticker (e.g. Apple, Tesla, Reliance, MSFT, TCS)..."
              className="w-full bg-gray-950/80 border border-emerald-900/50 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-xl pl-10 pr-4 py-2.5 text-white placeholder-gray-500 outline-none text-sm transition-all"
            />
          </div>

          <div className="flex items-center gap-2">
            <select
              value={market}
              onChange={onMarketChange}
              className="bg-gray-950/80 border border-emerald-900/50 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-white text-sm outline-none"
            >
              <option value="ALL">All Markets</option>
              <option value="NASDAQ">NASDAQ</option>
              <option value="NYSE">NYSE</option>
              <option value="NSE">NSE (India)</option>
              <option value="BSE">BSE (India)</option>
            </select>
          </div>
        </div>

        {/* Live Search Results */}
        {(searching || searchResults.length > 0) && (
          <div className="mt-3 bg-gray-950 border border-emerald-900/60 rounded-xl overflow-hidden shadow-2xl max-h-80 overflow-y-auto">
            {searching ? (
              <div className="flex items-center justify-center py-6 gap-2 text-emerald-400 text-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Searching live markets...</span>
              </div>
            ) : (
              <div className="divide-y divide-emerald-900/30">
                {searchResults.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 hover:bg-emerald-950/40 flex items-center justify-between transition-colors cursor-pointer"
                    onClick={() => selectStockItem(item)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-bold text-emerald-400 bg-emerald-950/70 border border-emerald-800/60 px-2 py-1 rounded text-xs">
                        {item.ticker}
                      </span>
                      <div>
                        <p className="text-white text-sm font-medium">{item.company_name}</p>
                        <p className="text-xs text-gray-400 flex items-center gap-2 mt-0.5">
                          <span className="text-gray-300 font-medium">{item.market}</span>
                          {item.sector && <span>• {item.sector}</span>}
                          {item.exchange && <span>• Exch: {item.exchange}</span>}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {item.current_price !== null && item.current_price !== undefined && (
                        <div className="text-right">
                          <p className="text-sm font-bold text-white">
                            {item.currency === 'INR' ? '₹' : '$'}
                            {item.current_price.toLocaleString()}
                          </p>
                          {item.day_change !== null && item.day_change !== undefined && (
                            <p
                              className={`text-xs font-medium flex items-center justify-end gap-0.5 ${
                                item.day_change >= 0 ? 'text-emerald-400' : 'text-red-400'
                              }`}
                            >
                              {item.day_change >= 0 ? '+' : ''}
                              {item.day_change} ({item.day_change_pct}%)
                            </p>
                          )}
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        {onAnalyzeWithAgent && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onAnalyzeWithAgent(item);
                            }}
                            className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3.5 py-1.5 rounded-lg font-bold flex items-center gap-1.5 shadow-md shadow-emerald-950/50 transition-colors"
                            title="Run Fundamental Analysis Agent on this company"
                          >
                            <Bot className="w-3.5 h-3.5" />
                            Agent Analysis
                          </button>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            selectStockItem(item);
                          }}
                          className="bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 text-xs px-3 py-1.5 rounded-lg font-medium transition-colors"
                        >
                          View OHLCV
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ─── Selected Stock Header & Provenance Status Banner ─── */}
      {!selectedStock ? (
        <div className="bg-gray-900/80 border border-emerald-900/40 rounded-2xl p-10 shadow-xl text-center">
          <Search className="w-12 h-12 text-emerald-800 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Search for a Company</h2>
          <p className="text-gray-400 text-sm max-w-md mx-auto">
            Use the search bar above to find a company by name or ticker symbol (e.g. Apple, AAPL, Reliance, TCS).
            Select a stock to view its OHLCV chart, company profile, financial statements, and audit logs.
          </p>
          <p className="text-gray-500 text-xs mt-3">
            Or click a <span className="text-emerald-400 font-medium">Quick Select Benchmark Equity</span> button from the market section above.
          </p>
        </div>
      ) : (
      <div className="bg-gray-900/80 border border-emerald-900/40 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-emerald-900/30">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                {selectedStock.company_name}
              </h1>
              <span className="font-mono text-sm font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-700/60 px-2.5 py-0.5 rounded-md">
                {selectedStock.ticker}
              </span>
              <span className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded-md font-medium">
                {selectedStock.market}
              </span>
            </div>

            {/* Provenance Badge: Data Source and Exact Retrieval Timestamp */}
            <div className="flex flex-wrap items-center gap-3 text-xs text-gray-400 mt-2">
              <div className="flex items-center gap-1.5 text-emerald-400 font-medium bg-emerald-950/60 border border-emerald-800/40 px-2.5 py-1 rounded-lg">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Source: {activeProvenance.source || 'Yahoo Finance Live API'}</span>
              </div>
              <div className="flex items-center gap-1.5 text-gray-300 bg-gray-950/60 border border-gray-800 px-2.5 py-1 rounded-lg font-mono">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                <span>Retrieved: {activeProvenance.ts ? new Date(activeProvenance.ts).toLocaleString() : 'Just now'}</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={addToWatchlist}
              className="bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs px-3.5 py-2 rounded-xl font-medium flex items-center gap-1.5 transition-colors border border-gray-700"
            >
              <Star className="w-3.5 h-3.5 text-yellow-400" />
              Watchlist
            </button>
            <button
              onClick={() => onStartResearch && onStartResearch(selectedStock)}
              className="bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs px-3.5 py-2 rounded-xl font-medium flex items-center gap-1.5 transition-colors border border-gray-700"
            >
              <BarChart2 className="w-3.5 h-3.5 text-emerald-400" />
              New Research
            </button>
            <button
              onClick={exportCSV}
              disabled={!bars.length}
              className="bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-200 text-xs px-3.5 py-2 rounded-xl font-medium flex items-center gap-1.5 transition-colors border border-gray-700"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              Export CSV
            </button>
            {onAnalyzeWithAgent && (
              <button
                onClick={() => onAnalyzeWithAgent(selectedStock)}
                className="bg-emerald-600 hover:bg-emerald-500 text-white text-sm px-4 py-2 rounded-xl font-bold flex items-center gap-2 transition-colors shadow-lg shadow-emerald-900/40 ring-1 ring-emerald-400/40"
              >
                <Bot className="w-4 h-4" />
                Agent Analysis
              </button>
            )}
          </div>
        </div>

        {/* ─── Navigation Switcher: OHLCV, Company Profile, Financial Statements, Audit Logs ─── */}
        <div className="flex flex-wrap gap-2 border-b border-emerald-900/30 pb-3">
          <button
            onClick={() => setActiveSubTab('chart')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeSubTab === 'chart'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'text-gray-400 hover:text-white bg-gray-950/60 hover:bg-gray-800/80 border border-gray-800/60'
            }`}
          >
            <BarChart2 className="w-4 h-4" />
            Price & OHLCV Candles
          </button>
          <button
            onClick={() => setActiveSubTab('profile')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeSubTab === 'profile'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'text-gray-400 hover:text-white bg-gray-950/60 hover:bg-gray-800/80 border border-gray-800/60'
            }`}
          >
            <Building2 className="w-4 h-4" />
            Company Profile & Key Stats
          </button>
          <button
            onClick={() => setActiveSubTab('financials')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeSubTab === 'financials'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'text-gray-400 hover:text-white bg-gray-950/60 hover:bg-gray-800/80 border border-gray-800/60'
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            Financial Statements
          </button>
          <button
            onClick={() => {
              setActiveSubTab('audit');
              fetchAuditLogs(selectedStock.ticker);
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeSubTab === 'audit'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'text-gray-400 hover:text-white bg-gray-950/60 hover:bg-gray-800/80 border border-gray-800/60'
            }`}
          >
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            Data Sources & Audit Logs
          </button>
        </div>

        {/* ═══════════════════════════════════════════════════════════════════════
            VIEW 1: PRICE & OHLCV CANDLES
        ═══════════════════════════════════════════════════════════════════════ */}
        {activeSubTab === 'chart' && (
          <div className="space-y-6">
            {/* Timeframe & Interval Selectors */}
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-1 bg-gray-950/80 p-1 rounded-xl border border-emerald-900/40">
                <span className="text-xs text-gray-500 px-2 font-medium">Range:</span>
                {TIMEFRAMES.map((tf) => (
                  <button
                    key={tf.label}
                    onClick={() => handlePeriodChange(tf)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                      period === tf.period
                        ? 'bg-emerald-600 text-white shadow-md'
                        : 'text-gray-400 hover:text-white hover:bg-gray-800'
                    }`}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-1 bg-gray-950/80 p-1 rounded-xl border border-emerald-900/40">
                <span className="text-xs text-gray-500 px-2 font-medium">Interval:</span>
                {INTERVALS.map((intv) => (
                  <button
                    key={intv.value}
                    onClick={() => handleIntervalChange(intv.value)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                      interval === intv.value
                        ? 'bg-emerald-900/70 text-emerald-300 border border-emerald-700/50'
                        : 'text-gray-400 hover:text-white hover:bg-gray-800'
                    }`}
                  >
                    {intv.label}
                  </button>
                ))}
              </div>
            </div>

            {/* OHLCV Summary Cards */}
            {ohlcvData && (
              <div className="space-y-3">
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                    <span className="text-xs text-gray-400 block font-medium">Period Open</span>
                    <p className="text-base font-bold text-white mt-1">
                      {currencySymbol}
                      {ohlcvData.period_open?.toFixed(2) ?? '—'}
                    </p>
                  </div>
                  <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                    <span className="text-xs text-emerald-400 block font-medium">Period High</span>
                    <p className="text-base font-bold text-emerald-300 mt-1">
                      {currencySymbol}
                      {ohlcvData.period_high?.toFixed(2) ?? '—'}
                    </p>
                  </div>
                  <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                    <span className="text-xs text-red-400 block font-medium">Period Low</span>
                    <p className="text-base font-bold text-red-300 mt-1">
                      {currencySymbol}
                      {ohlcvData.period_low?.toFixed(2) ?? '—'}
                    </p>
                  </div>
                  <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                    <span className="text-xs text-gray-400 block font-medium">Period Close</span>
                    <p className="text-base font-bold text-white mt-1">
                      {currencySymbol}
                      {ohlcvData.period_close?.toFixed(2) ?? '—'}
                    </p>
                  </div>
                  <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                    <span className="text-xs text-gray-400 block font-medium">Net Change</span>
                    <p
                      className={`text-base font-bold mt-1 flex items-center gap-1 ${
                        isNetPositive ? 'text-emerald-400' : 'text-red-400'
                      }`}
                    >
                      {isNetPositive ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                      {isNetPositive ? '+' : ''}
                      {ohlcvData.net_change?.toFixed(2)} ({ohlcvData.net_change_pct?.toFixed(2)}%)
                    </p>
                  </div>
                  <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                    <span className="text-xs text-gray-400 block font-medium">Total Volume</span>
                    <p className="text-base font-bold text-gray-200 mt-1">
                      {ohlcvData.total_volume ? ohlcvData.total_volume.toLocaleString() : '—'}
                    </p>
                  </div>
                </div>

                {/* Quantitative Data Validation Card */}
                {ohlcvData.validation_summary && (
                  <div className="bg-emerald-950/40 border border-emerald-800/50 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <span className="font-bold text-white">Data Quality & Validation:</span>
                      <span className="bg-emerald-900/80 text-emerald-300 px-2 py-0.5 rounded border border-emerald-700/60 font-mono font-semibold">
                        {ohlcvData.validation_summary.status || 'VALIDATED_CLEAN'} ({ohlcvData.validation_summary.data_integrity_score || '100%'})
                      </span>
                    </div>
                    <div className="flex items-center gap-3 sm:gap-4 text-gray-300 font-mono text-[11px] flex-wrap">
                      <span>Candles Checked: <strong className="text-white">{ohlcvData.validation_summary.total_records_checked || bars.length}</strong></span>
                      <span>• Missing Imputed: <strong className="text-emerald-400">{ohlcvData.validation_summary.missing_values_imputed ?? 0}</strong></span>
                      <span>• Duplicates Filtered: <strong className="text-emerald-400">{ohlcvData.validation_summary.duplicates_removed ?? 0}</strong></span>
                      <span>• Inconsistencies Corrected: <strong className="text-emerald-400">{ohlcvData.validation_summary.inconsistencies_corrected ?? 0}</strong></span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Interactive SVG Chart */}
            <div className="bg-gray-950/90 border border-emerald-900/40 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 uppercase tracking-wider">
                  <BarChart2 className="w-4 h-4" />
                  Price Movement & Volume ({period.toUpperCase()} / {interval.toUpperCase()})
                </span>
                {hoveredBar && (
                  <div className="text-xs text-gray-300 font-mono bg-emerald-950/80 px-2.5 py-1 rounded border border-emerald-800/50">
                    <span className="text-gray-400">{hoveredBar.date}: </span>
                    <span className="text-white font-bold">
                      Close: {selectedStock.currency === 'INR' ? '₹' : '$'}{hoveredBar.close}
                    </span>
                    <span className="text-gray-400 ml-2">
                      O: {selectedStock.currency === 'INR' ? '₹' : '$'}{hoveredBar.open}
                    </span>
                    <span className="text-emerald-400 ml-2">
                      H: {selectedStock.currency === 'INR' ? '₹' : '$'}{hoveredBar.high}
                    </span>
                    <span className="text-red-400 ml-2">
                      L: {selectedStock.currency === 'INR' ? '₹' : '$'}{hoveredBar.low}
                    </span>
                    <span className="text-cyan-400 ml-2">Vol: {hoveredBar.volume.toLocaleString()}</span>
                  </div>
                )}
              </div>

              {loadingOHLCV ? (
                <div className="flex flex-col items-center justify-center py-24 gap-3">
                  <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                  <p className="text-xs text-gray-400">Loading historical OHLCV candles...</p>
                </div>
              ) : bars.length === 0 ? (
                <div className="py-20 text-center text-gray-500 text-sm">
                  No historical data available for this range.
                </div>
              ) : (
                <div className="w-full overflow-x-auto">
                  <svg
                    viewBox={`0 0 ${chartWidth} ${chartHeight + volumeHeight}`}
                    className="w-full h-auto min-w-[600px]"
                  >
                    <defs>
                      <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>

                    {/* Grid Lines */}
                    {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
                      const y = padding.top + pct * (chartHeight - padding.top - padding.bottom);
                      const priceLabel = (maxPrice - pct * priceRange).toFixed(1);
                      return (
                        <g key={i}>
                          <line
                            x1={padding.left}
                            y1={y}
                            x2={chartWidth - padding.right}
                            y2={y}
                            stroke="#064e3b"
                            strokeDasharray="3 3"
                            strokeOpacity="0.5"
                          />
                          <text
                            x={padding.left - 8}
                            y={y + 4}
                            fill="#6ee7b7"
                            fontSize="9"
                            textAnchor="end"
                            fontFamily="monospace"
                          >
                            {priceLabel}
                          </text>
                        </g>
                      );
                    })}

                    {areaPath && <path d={areaPath} fill="url(#chartGradient)" />}

                    {linePoints.length > 0 && (
                      <polyline
                        fill="none"
                        stroke="#10b981"
                        strokeWidth="2.2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        points={linePoints.join(' ')}
                      />
                    )}

                    {/* Volume Bars */}
                    {bars.map((b, i) => {
                      const { x } = getCoordinates(i, b.close);
                      const barWidth = Math.max(
                        1,
                        ((chartWidth - padding.left - padding.right) / bars.length) * 0.7
                      );
                      const vHeight = (b.volume / maxVolume) * (volumeHeight - 15);
                      const vY = chartHeight + (volumeHeight - vHeight);
                      const isUp = b.close >= b.open;

                      return (
                        <rect
                          key={`vol-${i}`}
                          x={x - barWidth / 2}
                          y={vY}
                          width={barWidth}
                          height={vHeight}
                          fill={isUp ? '#10b981' : '#ef4444'}
                          opacity={0.5}
                        />
                      );
                    })}

                    {/* Hover points */}
                    {bars.map((b, i) => {
                      const { x, y } = getCoordinates(i, b.close);
                      const barWidth = Math.max(
                        2,
                        ((chartWidth - padding.left - padding.right) / bars.length) * 0.7
                      );

                      return (
                        <g
                          key={`point-${i}`}
                          onMouseEnter={() => setHoveredBar(b)}
                          onMouseLeave={() => setHoveredBar(null)}
                          className="cursor-pointer"
                        >
                          <circle
                            cx={x}
                            cy={y}
                            r={hoveredBar === b ? 5 : 2}
                            fill={b.close >= b.open ? '#34d399' : '#f87171'}
                            stroke="#064e3b"
                            strokeWidth="1.5"
                          />
                          <rect
                            x={x - barWidth}
                            y={0}
                            width={barWidth * 2}
                            height={chartHeight + volumeHeight}
                            fill="transparent"
                          />
                        </g>
                      );
                    })}
                  </svg>
                </div>
              )}
            </div>

            {/* OHLCV Data Table */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-emerald-400" />
                  Collected OHLCV Data Points ({bars.length} Records)
                </h3>
                <span className="text-xs text-gray-400">Open · High · Low · Close · Volume</span>
              </div>

              <div className="bg-gray-950/70 border border-emerald-900/30 rounded-xl overflow-hidden max-h-96 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-gray-900 border-b border-emerald-900/40 text-gray-400 uppercase font-semibold">
                    <tr>
                      <th className="px-4 py-2.5 text-left">Date / Time</th>
                      <th className="px-4 py-2.5 text-right">Open</th>
                      <th className="px-4 py-2.5 text-right">High</th>
                      <th className="px-4 py-2.5 text-right">Low</th>
                      <th className="px-4 py-2.5 text-right">Close</th>
                      <th className="px-4 py-2.5 text-right">Volume</th>
                      <th className="px-4 py-2.5 text-right">Bar Change</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-emerald-950/40 font-mono">
                    {bars.map((bar, i) => {
                      const chg = bar.close - bar.open;
                      const chgPct = bar.open ? ((chg / bar.open) * 100).toFixed(2) : '0.00';
                      const isUp = chg >= 0;

                      return (
                        <tr key={i} className="hover:bg-emerald-950/30 transition-colors">
                          <td className="px-4 py-2 text-gray-300 font-sans">{bar.date}</td>
                          <td className="px-4 py-2 text-right text-gray-300">
                            {currencySymbol}
                            {bar.open.toFixed(2)}
                          </td>
                          <td className="px-4 py-2 text-right text-emerald-400">
                            {currencySymbol}
                            {bar.high.toFixed(2)}
                          </td>
                          <td className="px-4 py-2 text-right text-red-400">
                            {currencySymbol}
                            {bar.low.toFixed(2)}
                          </td>
                          <td className="px-4 py-2 text-right font-bold text-white">
                            {currencySymbol}
                            {bar.close.toFixed(2)}
                          </td>
                          <td className="px-4 py-2 text-right text-gray-400">
                            {bar.volume.toLocaleString()}
                          </td>
                          <td
                            className={`px-4 py-2 text-right font-semibold ${
                              isUp ? 'text-emerald-400' : 'text-red-400'
                            }`}
                          >
                            {isUp ? '+' : ''}
                            {chg.toFixed(2)} ({isUp ? '+' : ''}
                            {chgPct}%)
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════════
            VIEW 2: COMPANY PROFILE & FUNDAMENTAL VALUATION
        ═══════════════════════════════════════════════════════════════════════ */}
        {activeSubTab === 'profile' && (
          <div className="space-y-6">
            {loadingProfile ? (
              <div className="flex flex-col items-center justify-center py-24 gap-3">
                <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                <p className="text-xs text-gray-400">Loading comprehensive company profile...</p>
              </div>
            ) : profileData ? (
              <div className="space-y-6">
                {/* Company Header & Key Info */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-950/70 border border-emerald-900/30 rounded-xl p-4 md:col-span-2">
                    <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-emerald-400" />
                      About {profileData.company_name}
                    </h3>
                    <p className="text-xs text-gray-300 leading-relaxed line-clamp-4 hover:line-clamp-none transition-all">
                      {profileData.description || 'No detailed business summary available.'}
                    </p>
                  </div>

                  <div className="bg-gray-950/70 border border-emerald-900/30 rounded-xl p-4 space-y-2.5 text-xs">
                    <h3 className="font-semibold text-white text-sm mb-3">Corporate Details</h3>
                    <div className="flex justify-between text-gray-400">
                      <span>Sector:</span>
                      <span className="text-white font-medium">{profileData.sector || '—'}</span>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Industry:</span>
                      <span className="text-white font-medium text-right max-w-[180px] truncate">{profileData.industry || '—'}</span>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Headquarters:</span>
                      <span className="text-white font-medium">{[profileData.city, profileData.country].filter(Boolean).join(', ') || '—'}</span>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Employees:</span>
                      <span className="text-white font-mono font-medium">{profileData.full_time_employees?.toLocaleString() || '—'}</span>
                    </div>
                    {profileData.website && (
                      <div className="flex justify-between text-gray-400 pt-1">
                        <span>Website:</span>
                        <a
                          href={profileData.website}
                          target="_blank"
                          rel="noreferrer"
                          className="text-emerald-400 hover:underline flex items-center gap-1 font-medium"
                        >
                          Visit Site <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    )}
                  </div>
                </div>

                {/* Key Valuation & Fundamentals Grid */}
                <div>
                  <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-emerald-400" />
                    Valuation & Fundamental Metrics
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 text-xs">
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">Market Cap</span>
                      <p className="text-sm font-bold text-white mt-1">
                        {formatCurrency(profileData.market_cap, profileData.currency)}
                      </p>
                    </div>
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">Enterprise Value</span>
                      <p className="text-sm font-bold text-white mt-1">
                        {formatCurrency(profileData.enterprise_value, profileData.currency)}
                      </p>
                    </div>
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">Trailing P/E</span>
                      <p className="text-sm font-bold text-emerald-400 mt-1">
                        {profileData.pe_ratio ? profileData.pe_ratio.toFixed(2) : '—'}
                      </p>
                    </div>
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">Forward P/E</span>
                      <p className="text-sm font-bold text-emerald-300 mt-1">
                        {profileData.forward_pe ? profileData.forward_pe.toFixed(2) : '—'}
                      </p>
                    </div>
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">PEG Ratio</span>
                      <p className="text-sm font-bold text-white mt-1">
                        {profileData.peg_ratio ? profileData.peg_ratio.toFixed(2) : '—'}
                      </p>
                    </div>
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">Price / Book</span>
                      <p className="text-sm font-bold text-white mt-1">
                        {profileData.price_to_book ? profileData.price_to_book.toFixed(2) : '—'}
                      </p>
                    </div>
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">Beta (5Y)</span>
                      <p className="text-sm font-bold text-white mt-1">
                        {profileData.beta ? profileData.beta.toFixed(2) : '—'}
                      </p>
                    </div>
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">Dividend Yield</span>
                      <p className="text-sm font-bold text-cyan-400 mt-1">
                        {formatPercent(profileData.dividend_yield)}
                      </p>
                    </div>
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">52-Week Range</span>
                      <p className="text-sm font-bold text-white mt-1">
                        {formatCurrency(profileData.fifty_two_week_low, profileData.currency)} -{' '}
                        {formatCurrency(profileData.fifty_two_week_high, profileData.currency)}
                      </p>
                    </div>
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">Profit Margin</span>
                      <p className="text-sm font-bold text-white mt-1">
                        {formatPercent(profileData.profit_margins)}
                      </p>
                    </div>
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">Operating Margin</span>
                      <p className="text-sm font-bold text-white mt-1">
                        {formatPercent(profileData.operating_margins)}
                      </p>
                    </div>
                    <div className="bg-gray-950/60 border border-emerald-900/30 rounded-xl p-3">
                      <span className="text-gray-400 block">Return on Equity</span>
                      <p className="text-sm font-bold text-emerald-400 mt-1">
                        {formatPercent(profileData.return_on_equity)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Key Executives */}
                {profileData.key_executives && profileData.key_executives.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                      <Users className="w-4 h-4 text-emerald-400" />
                      Key Corporate Officers & Leadership
                    </h3>
                    <div className="bg-gray-950/70 border border-emerald-900/30 rounded-xl overflow-hidden">
                      <table className="w-full text-xs">
                        <thead className="bg-gray-900 border-b border-emerald-900/40 text-gray-400 uppercase font-semibold">
                          <tr>
                            <th className="px-4 py-2.5 text-left">Executive Name</th>
                            <th className="px-4 py-2.5 text-left">Title / Role</th>
                            <th className="px-4 py-2.5 text-right">Reported Pay</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-emerald-950/40">
                          {profileData.key_executives.map((exec, idx) => (
                            <tr key={idx} className="hover:bg-emerald-950/20">
                              <td className="px-4 py-2.5 font-medium text-white">{exec.name}</td>
                              <td className="px-4 py-2.5 text-gray-300">{exec.title}</td>
                              <td className="px-4 py-2.5 text-right text-gray-400 font-mono">
                                {exec.pay ? formatCurrency(exec.pay, profileData.currency) : '—'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-center py-16 text-gray-400 text-sm">No profile data available.</p>
            )}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════════
            VIEW 3: FINANCIAL STATEMENTS (INCOME, BALANCE SHEET, CASH FLOW)
        ═══════════════════════════════════════════════════════════════════════ */}
        {activeSubTab === 'financials' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between flex-wrap gap-3">
              {/* Financial Statement Type Selector */}
              <div className="flex gap-1 bg-gray-950/80 p-1 rounded-xl border border-emerald-900/40">
                <button
                  onClick={() => setFinStmtType('income')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    finStmtType === 'income'
                      ? 'bg-emerald-600 text-white shadow-md'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  Income Statement
                </button>
                <button
                  onClick={() => setFinStmtType('balance')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    finStmtType === 'balance'
                      ? 'bg-emerald-600 text-white shadow-md'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  Balance Sheet
                </button>
                <button
                  onClick={() => setFinStmtType('cashflow')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    finStmtType === 'cashflow'
                      ? 'bg-emerald-600 text-white shadow-md'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  Cash Flow Statement
                </button>
              </div>

              <span className="text-xs text-gray-400">
                Reporting Currency: <span className="font-mono text-emerald-400 font-bold">{financialsData?.currency || selectedStock.currency}</span>
              </span>
            </div>

            {loadingFinancials ? (
              <div className="flex flex-col items-center justify-center py-24 gap-3">
                <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                <p className="text-xs text-gray-400">Loading multi-period financial statements...</p>
              </div>
            ) : financialsData ? (
              <div className="bg-gray-950/70 border border-emerald-900/30 rounded-xl overflow-hidden shadow-lg overflow-x-auto">
                {/* 1. Income Statement Table */}
                {finStmtType === 'income' && (
                  <table className="w-full text-xs">
                    <thead className="bg-gray-900 border-b border-emerald-900/40 text-gray-400 uppercase font-semibold">
                      <tr>
                        <th className="px-4 py-3 text-left">Financial Metric</th>
                        {financialsData.income_statements.map((s, idx) => (
                          <th key={idx} className="px-4 py-3 text-right font-mono">
                            {s.date}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-emerald-950/40 font-mono">
                      <tr className="hover:bg-emerald-950/20 font-sans">
                        <td className="px-4 py-2.5 font-bold text-white">Total Revenue</td>
                        {financialsData.income_statements.map((s, idx) => (
                          <td key={idx} className="px-4 py-2.5 text-right font-mono font-bold text-emerald-400">
                            {formatCurrency(s.total_revenue, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20">
                        <td className="px-4 py-2 text-gray-300 font-sans">Cost of Revenue</td>
                        {financialsData.income_statements.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right text-gray-400">
                            {formatCurrency(s.cost_of_revenue, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20 bg-gray-900/30">
                        <td className="px-4 py-2 font-semibold text-white font-sans">Gross Profit</td>
                        {financialsData.income_statements.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right font-semibold text-white">
                            {formatCurrency(s.gross_profit, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20">
                        <td className="px-4 py-2 text-gray-300 font-sans">Operating Expenses</td>
                        {financialsData.income_statements.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right text-gray-400">
                            {formatCurrency(s.operating_expense, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20 bg-gray-900/30">
                        <td className="px-4 py-2 font-semibold text-white font-sans">Operating Income (EBIT)</td>
                        {financialsData.income_statements.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right font-semibold text-emerald-300">
                            {formatCurrency(s.operating_income, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20">
                        <td className="px-4 py-2 text-gray-300 font-sans">EBITDA</td>
                        {financialsData.income_statements.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right text-gray-300">
                            {formatCurrency(s.ebitda, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20 bg-emerald-950/30 border-t border-emerald-900/60 font-sans">
                        <td className="px-4 py-3 font-extrabold text-white">Net Income</td>
                        {financialsData.income_statements.map((s, idx) => (
                          <td key={idx} className="px-4 py-3 text-right font-mono font-bold text-emerald-400 text-sm">
                            {formatCurrency(s.net_income, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                )}

                {/* 2. Balance Sheet Table */}
                {finStmtType === 'balance' && (
                  <table className="w-full text-xs">
                    <thead className="bg-gray-900 border-b border-emerald-900/40 text-gray-400 uppercase font-semibold">
                      <tr>
                        <th className="px-4 py-3 text-left">Balance Sheet Metric</th>
                        {financialsData.balance_sheets.map((s, idx) => (
                          <th key={idx} className="px-4 py-3 text-right font-mono">
                            {s.date}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-emerald-950/40 font-mono">
                      <tr className="hover:bg-emerald-950/20">
                        <td className="px-4 py-2 text-gray-300 font-sans">Cash & Cash Equivalents</td>
                        {financialsData.balance_sheets.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right text-white">
                            {formatCurrency(s.cash_and_equivalents, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20">
                        <td className="px-4 py-2 text-gray-300 font-sans">Short-Term Investments</td>
                        {financialsData.balance_sheets.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right text-gray-300">
                            {formatCurrency(s.short_term_investments, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20 bg-gray-900/30">
                        <td className="px-4 py-2.5 font-bold text-white font-sans">Total Assets</td>
                        {financialsData.balance_sheets.map((s, idx) => (
                          <td key={idx} className="px-4 py-2.5 text-right font-bold text-emerald-400">
                            {formatCurrency(s.total_assets, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20">
                        <td className="px-4 py-2 text-gray-300 font-sans">Current Liabilities</td>
                        {financialsData.balance_sheets.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right text-gray-400">
                            {formatCurrency(s.total_current_liabilities, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20">
                        <td className="px-4 py-2 text-gray-300 font-sans">Long-Term Debt</td>
                        {financialsData.balance_sheets.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right text-red-300">
                            {formatCurrency(s.long_term_debt, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20 bg-gray-900/30">
                        <td className="px-4 py-2.5 font-bold text-white font-sans">Total Liabilities</td>
                        {financialsData.balance_sheets.map((s, idx) => (
                          <td key={idx} className="px-4 py-2.5 text-right font-bold text-red-400">
                            {formatCurrency(s.total_liabilities, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20 bg-emerald-950/30 border-t border-emerald-900/60 font-sans">
                        <td className="px-4 py-3 font-extrabold text-white">Stockholders' Equity</td>
                        {financialsData.balance_sheets.map((s, idx) => (
                          <td key={idx} className="px-4 py-3 text-right font-mono font-bold text-emerald-400 text-sm">
                            {formatCurrency(s.stockholders_equity, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                )}

                {/* 3. Cash Flow Table */}
                {finStmtType === 'cashflow' && (
                  <table className="w-full text-xs">
                    <thead className="bg-gray-900 border-b border-emerald-900/40 text-gray-400 uppercase font-semibold">
                      <tr>
                        <th className="px-4 py-3 text-left">Cash Flow Metric</th>
                        {financialsData.cash_flows.map((s, idx) => (
                          <th key={idx} className="px-4 py-3 text-right font-mono">
                            {s.date}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-emerald-950/40 font-mono">
                      <tr className="hover:bg-emerald-950/20 bg-gray-900/30">
                        <td className="px-4 py-2.5 font-bold text-white font-sans">Operating Cash Flow</td>
                        {financialsData.cash_flows.map((s, idx) => (
                          <td key={idx} className="px-4 py-2.5 text-right font-bold text-emerald-400">
                            {formatCurrency(s.operating_cash_flow, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20">
                        <td className="px-4 py-2 text-gray-300 font-sans">Capital Expenditures (CapEx)</td>
                        {financialsData.cash_flows.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right text-red-300">
                            {formatCurrency(s.capital_expenditures, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20 bg-emerald-950/20">
                        <td className="px-4 py-2 font-bold text-emerald-300 font-sans">Free Cash Flow</td>
                        {financialsData.cash_flows.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right font-bold text-emerald-300">
                            {formatCurrency(s.free_cash_flow, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20">
                        <td className="px-4 py-2 text-gray-300 font-sans">Investing Cash Flow</td>
                        {financialsData.cash_flows.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right text-gray-400">
                            {formatCurrency(s.investing_cash_flow, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20">
                        <td className="px-4 py-2 text-gray-300 font-sans">Financing Cash Flow</td>
                        {financialsData.cash_flows.map((s, idx) => (
                          <td key={idx} className="px-4 py-2 text-right text-gray-400">
                            {formatCurrency(s.financing_cash_flow, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                      <tr className="hover:bg-emerald-950/20 bg-gray-900/40 border-t border-emerald-900/60 font-sans">
                        <td className="px-4 py-3 font-bold text-white">Net Change in Cash</td>
                        {financialsData.cash_flows.map((s, idx) => (
                          <td key={idx} className="px-4 py-3 text-right font-mono font-bold text-white">
                            {formatCurrency(s.net_change_in_cash, financialsData.currency)}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                )}
              </div>
            ) : (
              <p className="text-center py-16 text-gray-400 text-sm">No financial statements available.</p>
            )}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════════
            VIEW 4: DATA SOURCES & AUDIT LOGS (PROVENANCE & TIMESTAMPS)
        ═══════════════════════════════════════════════════════════════════════ */}
        {activeSubTab === 'audit' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Data Retrieval Provenance & Timestamps Audit Log
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Chronological records of all external data sources, query timestamps, and records stored in PostgreSQL.
                </p>
              </div>
              <button
                onClick={() => fetchAuditLogs(selectedStock.ticker)}
                className="bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Refresh Logs
              </button>
            </div>

            {loadingAuditLogs ? (
              <div className="flex justify-center py-16">
                <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
              </div>
            ) : auditLogs.length === 0 ? (
              <p className="text-center py-16 text-gray-500 text-sm">No audit logs recorded yet.</p>
            ) : (
              <div className="bg-gray-950/70 border border-emerald-900/30 rounded-xl overflow-hidden max-h-96 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-gray-900 border-b border-emerald-900/40 text-gray-400 uppercase font-semibold">
                    <tr>
                      <th className="px-4 py-2.5 text-left">Retrieval Timestamp (UTC)</th>
                      <th className="px-4 py-2.5 text-left">Ticker</th>
                      <th className="px-4 py-2.5 text-left">Data Category</th>
                      <th className="px-4 py-2.5 text-left">Data Source</th>
                      <th className="px-4 py-2.5 text-right">Items</th>
                      <th className="px-4 py-2.5 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-emerald-950/40 font-mono">
                    {auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-emerald-950/20">
                        <td className="px-4 py-2 text-gray-300">
                          {new Date(log.retrieval_timestamp).toISOString().replace('T', ' ').slice(0, 19)}
                        </td>
                        <td className="px-4 py-2 text-emerald-400 font-bold">{log.ticker}</td>
                        <td className="px-4 py-2 text-white font-sans">{log.data_type}</td>
                        <td className="px-4 py-2 text-gray-400 font-sans">{log.data_source}</td>
                        <td className="px-4 py-2 text-right text-gray-300">{log.record_count}</td>
                        <td className="px-4 py-2 text-right">
                          <span className="bg-emerald-950 text-emerald-400 border border-emerald-800/60 px-2 py-0.5 rounded text-[10px] font-bold uppercase">
                            {log.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
      )}
    </div>
  );
}
