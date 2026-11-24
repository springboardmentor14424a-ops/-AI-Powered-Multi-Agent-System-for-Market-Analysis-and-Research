import React, { useState, useEffect, useRef, useMemo } from 'react';
import api from '../api/client';
import {
  Search, Calendar, Database, ShieldCheck, AlertTriangle, 
  BarChart2, FileText, Table, Building2, TrendingUp, Download, 
  Clock, CheckCircle, X, ChevronRight, Bookmark, RefreshCw, 
  Layers, ArrowUpRight, ArrowDownRight, DollarSign, Activity, 
  Award, Eye, Trash2, Check, AlertCircle, Sparkles
} from 'lucide-react';

const EXCHANGES = [
  { id: 'NSE', name: 'NSE', full: 'National Stock Exchange of India', country: 'India', flag: '🇮🇳' },
  { id: 'BSE', name: 'BSE', full: 'Bombay Stock Exchange', country: 'India', flag: '🇮🇳' },
  { id: 'NASDAQ', name: 'NASDAQ', full: 'NASDAQ Stock Market', country: 'United States', flag: '🇺🇸' },
  { id: 'NYSE', name: 'NYSE', full: 'New York Stock Exchange', country: 'United States', flag: '🇺🇸' },
];

const DATE_PRESETS = [
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '6M', days: 180 },
  { label: '1Y', days: 365 },
  { label: '5Y', days: 1825 },
  { label: 'YTD', isYtd: true }
];

export default function MarketDataCollectionTab({ onAddToWatchlist, watchlist = [] }) {
  // Input Selection State
  const [selectedExchange, setSelectedExchange] = useState('NASDAQ');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCompany, setSelectedCompany] = useState({
    ticker: 'AAPL',
    name: 'Apple Inc.',
    market: 'NASDAQ',
    country: 'United States'
  });

  // Autocomplete State
  const [suggestions, setSuggestions] = useState([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const autocompleteRef = useRef(null);
  const debounceTimerRef = useRef(null);

  // Date and Interval State
  const todayStr = useMemo(() => new Date().toISOString().split('T')[0], []);
  const oneYearAgoStr = useMemo(() => {
    const d = new Date();
    d.setFullYear(d.getFullYear() - 1);
    return d.toISOString().split('T')[0];
  }, []);

  const [startDate, setStartDate] = useState(oneYearAgoStr);
  const [endDate, setEndDate] = useState(todayStr);
  const [interval, setInterval] = useState('1d');

  // Collection Results State
  const [collecting, setCollecting] = useState(false);
  const [collectionResult, setCollectionResult] = useState(null);
  const [collectionError, setCollectionError] = useState('');

  // Sub-Tab Navigation: 'ohlcv' | 'profile' | 'financials' | 'validation' | 'saved'
  const [viewSubTab, setViewSubTab] = useState('ohlcv');
  const [financialsTab, setFinancialsTab] = useState('income'); // 'income' | 'balance' | 'cash'
  const [chartMode, setChartMode] = useState('line'); // 'line' | 'candlestick'
  const [hoverChartIndex, setHoverChartIndex] = useState(null);

  // Pagination for OHLCV table
  const [page, setPage] = useState(1);
  const rowsPerPage = 15;

  // Past Collections from PostgreSQL
  const [pastCollections, setPastCollections] = useState([]);
  const [loadingPastCollections, setLoadingPastCollections] = useState(false);

  // Notification Banner
  const [toast, setToast] = useState({ message: '', type: '' });
  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast({ message: '', type: '' }), 4000);
  };

  // Close suggestions on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (autocompleteRef.current && !autocompleteRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch Autocomplete Suggestions with Debouncing
  useEffect(() => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

    debounceTimerRef.current = setTimeout(async () => {
      try {
        setLoadingSuggestions(true);
        const res = await api.get(`/market-data/search?market=${selectedExchange}&q=${encodeURIComponent(searchQuery)}`);
        setSuggestions(res.data || []);
      } catch (err) {
        console.error('Failed to query company search suggestions:', err);
      } finally {
        setLoadingSuggestions(false);
      }
    }, 200);

    return () => clearTimeout(debounceTimerRef.current);
  }, [searchQuery, selectedExchange]);

  // Load Past Collections History from DB
  const loadPastCollections = async () => {
    try {
      setLoadingPastCollections(true);
      const res = await api.get('/market-data/collections');
      setPastCollections(res.data || []);
    } catch (err) {
      console.error('Failed to load past collections:', err);
    } finally {
      setLoadingPastCollections(false);
    }
  };

  useEffect(() => {
    loadPastCollections();
  }, []);

  // Apply quick date preset
  const handleApplyPreset = (preset) => {
    const end = new Date();
    let start = new Date();
    if (preset.isYtd) {
      start = new Date(end.getFullYear(), 0, 1);
    } else {
      start.setDate(end.getDate() - preset.days);
    }
    setStartDate(start.toISOString().split('T')[0]);
    setEndDate(end.toISOString().split('T')[0]);
  };

  // Switch Exchange & reset search query
  const handleSelectExchange = (exch) => {
    setSelectedExchange(exch);
    setSearchQuery('');
    setShowSuggestions(false);
    // Set default company for that exchange
    const defaultSecurities = {
      NSE: { ticker: 'INFY', name: 'Infosys Limited', market: 'NSE', country: 'India' },
      BSE: { ticker: 'TCS', name: 'Tata Consultancy Services Ltd', market: 'BSE', country: 'India' },
      NASDAQ: { ticker: 'AAPL', name: 'Apple Inc.', market: 'NASDAQ', country: 'United States' },
      NYSE: { ticker: 'JNJ', name: 'Johnson & Johnson', market: 'NYSE', country: 'United States' }
    };
    setSelectedCompany(defaultSecurities[exch] || { ticker: 'AAPL', name: 'Apple Inc.', market: exch, country: 'United States' });
  };

  // Perform Market Data Collection
  const handleCollectMarketData = async () => {
    if (!selectedCompany?.ticker || selectedCompany.market?.toUpperCase() !== selectedExchange.toUpperCase()) {
      setCollectionError(`Please select a valid company listed on ${selectedExchange} from the search suggestions.`);
      return;
    }

    setCollecting(true);
    setCollectionError('');
    try {
      const payload = {
        ticker: selectedCompany.ticker,
        market: selectedExchange,
        company_name: selectedCompany.name,
        start_date: startDate,
        end_date: endDate,
        interval: interval
      };

      const res = await api.post('/market-data/collect', payload);
      setCollectionResult(res.data);
      setPage(1);
      showToast(`Successfully collected market data for ${selectedCompany.ticker} (${selectedExchange})!`, 'success');
      loadPastCollections();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to collect market data.';
      setCollectionError(msg);
      showToast(msg, 'error');
    } finally {
      setCollecting(false);
    }
  };

  // Reload a past collection from PostgreSQL
  const handleLoadSavedCollection = async (collectionId) => {
    try {
      setCollecting(true);
      const res = await api.get(`/market-data/collections/${collectionId}`);
      setCollectionResult(res.data);
      setSelectedExchange(res.data.market);
      setSelectedCompany({
        ticker: res.data.ticker,
        name: res.data.company_name,
        market: res.data.market,
        country: res.data.country
      });
      setStartDate(res.data.start_date || oneYearAgoStr);
      setEndDate(res.data.end_date || todayStr);
      setInterval(res.data.interval || '1d');
      setViewSubTab('ohlcv');
      setPage(1);
      showToast(`Loaded stored dataset for ${res.data.ticker}!`, 'success');
    } catch (err) {
      showToast('Failed to load saved collection.', 'error');
    } finally {
      setCollecting(false);
    }
  };

  // Delete past collection
  const handleDeletePastCollection = async (collectionId, e) => {
    e.stopPropagation();
    try {
      await api.delete(`/market-data/collections/${collectionId}`);
      setPastCollections(prev => prev.filter(c => c.collection_id !== collectionId));
      if (collectionResult?.collection_id === collectionId) {
        setCollectionResult(null);
      }
      showToast('Saved market dataset deleted.', 'success');
    } catch (err) {
      showToast('Failed to delete saved dataset.', 'error');
    }
  };

  // Export OHLCV data as CSV
  const handleExportCSV = () => {
    if (!collectionResult?.ohlcv_records?.length) return;
    const records = collectionResult.ohlcv_records;
    const headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change', 'Change_Pct', 'Validation_Status'];
    const rows = records.map(r => [
      r.date,
      r.open ?? '',
      r.high ?? '',
      r.low ?? '',
      r.close ?? '',
      r.volume ?? '',
      r.change ?? '',
      r.change_pct ?? '',
      r.is_valid ? 'VALID' : (r.validation_flags || []).join('; ')
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${collectionResult.ticker}_${collectionResult.market}_OHLCV_${collectionResult.interval}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // OHLCV Pagination calculations
  const ohlcvList = collectionResult?.ohlcv_records || [];
  const totalPages = Math.ceil(ohlcvList.length / rowsPerPage) || 1;
  const paginatedOhlcv = useMemo(() => {
    const start = (page - 1) * rowsPerPage;
    return ohlcvList.slice(start, start + rowsPerPage);
  }, [ohlcvList, page]);

  // SVG Chart Geometry
  const chartGeometry = useMemo(() => {
    if (!ohlcvList || ohlcvList.length < 2) return null;

    const width = 800;
    const height = 230;
    const padX = 45;
    const padTop = 20;
    const padBottom = 35;
    const usableWidth = width - padX * 2;
    const usableHeight = height - padTop - padBottom;

    const prices = ohlcvList.map(d => d.close).filter(p => p !== null && !isNaN(p));
    if (!prices.length) return null;

    const minPrice = Math.min(...prices) * 0.99;
    const maxPrice = Math.max(...prices) * 1.01;
    const priceRange = maxPrice - minPrice || 1;

    const volumes = ohlcvList.map(d => d.volume || 0);
    const maxVolume = Math.max(...volumes, 1);

    const points = ohlcvList.map((d, i) => {
      const x = padX + (i / (ohlcvList.length - 1)) * usableWidth;
      const y = padTop + usableHeight - (((d.close ?? minPrice) - minPrice) / priceRange) * usableHeight;
      const openY = padTop + usableHeight - (((d.open ?? minPrice) - minPrice) / priceRange) * usableHeight;
      const highY = padTop + usableHeight - (((d.high ?? minPrice) - minPrice) / priceRange) * usableHeight;
      const lowY = padTop + usableHeight - (((d.low ?? minPrice) - minPrice) / priceRange) * usableHeight;
      const volHeight = ((d.volume || 0) / maxVolume) * 45;
      const volY = height - padBottom - volHeight;
      return { x, y, openY, highY, lowY, volY, volHeight, ...d };
    });

    const pathD = points.reduce((acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)},${p.y.toFixed(1)}`, '');
    const firstPoint = points[0];
    const lastPoint = points[points.length - 1];
    const areaD = `${pathD} L ${lastPoint.x.toFixed(1)},${(height - padBottom).toFixed(1)} L ${firstPoint.x.toFixed(1)},${(height - padBottom).toFixed(1)} Z`;

    const startPrice = points[0]?.close || 1;
    const endPrice = points[points.length - 1]?.close || 1;
    const isUp = endPrice >= startPrice;

    return {
      width,
      height,
      padX,
      padTop,
      padBottom,
      minPrice,
      maxPrice,
      points,
      pathD,
      areaD,
      isUp
    };
  }, [ohlcvList]);

  const currencySym = (selectedExchange === 'NSE' || selectedExchange === 'BSE') ? '₹' : '$';

  return (
    <div className="space-y-6">
      {/* 1. Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 bg-gradient-to-r from-slate-900 via-blue-950/40 to-slate-900 border border-slate-800 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-400 mb-1">
            <Database size={15} /> Module 2: Market Data Collection
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Stock Search & Multi-Exchange Market Data Engine
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Acquire real-time historical OHLCV prices, company fundamentals, and financial statements with automated integrity validation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-blue-950 text-blue-300 border border-blue-800 rounded-lg text-xs font-semibold flex items-center gap-1.5">
            <ShieldCheck size={14} className="text-emerald-400" />
            Integrity Validation Active
          </span>
          <span className="px-3 py-1 bg-slate-800 text-slate-300 border border-slate-700 rounded-lg text-xs font-mono">
            4 Exchanges Supported
          </span>
        </div>
      </div>

      {/* 2. Control Panel: Exchange, Autocomplete, Dates & Interval */}
      <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-lg space-y-4">
        {/* Exchange Selector */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <Building2 size={14} className="text-blue-400" /> Select Stock Exchange:
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {EXCHANGES.map(exch => (
              <button
                key={exch.id}
                type="button"
                onClick={() => handleSelectExchange(exch.id)}
                className={`p-3 rounded-xl border text-left flex flex-col justify-between transition ${
                  selectedExchange === exch.id
                    ? 'bg-blue-600/20 border-blue-500 text-white shadow-md ring-1 ring-blue-500/50'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold flex items-center gap-1.5">
                    <span>{exch.flag}</span>
                    <span>{exch.name}</span>
                  </span>
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400">
                    {exch.country}
                  </span>
                </div>
                <span className="text-[11px] text-slate-400 truncate mt-1">
                  {exch.full}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Company Search with Dynamic Autocomplete */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          {/* Autocomplete Input */}
          <div className="md:col-span-6 relative" ref={autocompleteRef}>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-1.5 flex items-center gap-1.5">
              <Search size={13} className="text-blue-400" /> Search Company or Ticker ({selectedExchange}):
            </label>
            <div className="relative">
              <input
                type="text"
                value={searchQuery !== '' ? searchQuery : (selectedCompany?.ticker ? `${selectedCompany.name} (${selectedCompany.ticker})` : '')}
                onChange={e => {
                  const val = e.target.value;
                  setSearchQuery(val);
                  setSelectedCompany(null);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                placeholder={`Search ${selectedExchange} by company name or ticker (e.g. ${selectedExchange === 'NSE' ? 'INFY, RELIANCE' : 'AAPL, MSFT'})...`}
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
              />
              {loadingSuggestions && (
                <div className="absolute right-3 top-2.5 text-slate-400">
                  <RefreshCw size={15} className="animate-spin" />
                </div>
              )}
            </div>

            {/* Suggestions Dropdown */}
            {showSuggestions && (
              <div className="absolute left-0 right-0 top-full mt-1 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-30 max-h-64 overflow-y-auto divide-y divide-slate-800/80">
                {suggestions.length > 0 ? (
                  suggestions.map((c, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => {
                        setSelectedCompany(c);
                        setSearchQuery('');
                        setShowSuggestions(false);
                      }}
                      className="w-full px-4 py-2.5 text-left hover:bg-blue-950/40 flex items-center justify-between text-xs transition"
                    >
                      <div className="flex flex-col">
                        <span className="font-bold text-white">{c.name}</span>
                        <span className="text-[11px] text-slate-400 font-mono">{c.ticker}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-[10px]">
                        <span className="px-2 py-0.5 bg-slate-800 text-blue-300 rounded border border-slate-700 font-semibold font-mono">
                          {c.market}
                        </span>
                        <span className="text-slate-400 font-medium">
                          {c.country}
                        </span>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="p-4 text-center text-xs text-slate-400">
                    No results found.
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Date Range Selectors */}
          <div className="md:col-span-4 grid grid-cols-2 gap-2">
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-1">
                Start Date:
              </label>
              <input
                type="date"
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
                className="w-full px-2.5 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-1">
                End Date:
              </label>
              <input
                type="date"
                value={endDate}
                onChange={e => setEndDate(e.target.value)}
                className="w-full px-2.5 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Interval Selector */}
          <div className="md:col-span-2">
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-1">
              Interval:
            </label>
            <select
              value={interval}
              onChange={e => setInterval(e.target.value)}
              className="w-full px-2.5 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="1d">Daily (1d)</option>
              <option value="1wk">Weekly (1wk)</option>
              <option value="1mo">Monthly (1mo)</option>
            </select>
          </div>
        </div>

        {/* Date Presets Strip & Submit Button */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="text-[11px] font-medium mr-1">Quick Range:</span>
            {DATE_PRESETS.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleApplyPreset(p)}
                className="px-2.5 py-1 bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white rounded text-[11px] font-semibold transition"
              >
                {p.label}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={handleCollectMarketData}
            disabled={collecting}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl flex items-center gap-2 shadow-lg transition disabled:opacity-50"
          >
            {collecting ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                <span>Collecting Market Data...</span>
              </>
            ) : (
              <>
                <Database size={14} />
                <span>Collect Market Data</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* 3. Error Banner */}
      {collectionError && (
        <div className="p-4 bg-rose-950/60 border border-rose-800 rounded-xl text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle size={16} className="shrink-0 text-rose-400" />
          <span>{collectionError}</span>
        </div>
      )}

      {/* 4. Active Collection Results Display */}
      {collectionResult && (
        <div className="space-y-4">
          {/* Metadata & Traceability Banner */}
          <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-2xl flex flex-wrap items-center justify-between gap-3 shadow-md">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white">
                  {collectionResult.company_name} ({collectionResult.ticker})
                </h3>
                <span className="px-2 py-0.5 bg-blue-950 text-blue-300 border border-blue-800 rounded font-mono text-[11px] font-bold">
                  {collectionResult.market}
                </span>
                <span className="px-2 py-0.5 bg-slate-800 text-slate-300 border border-slate-700 rounded text-[11px]">
                  {collectionResult.country}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 flex flex-wrap items-center gap-3 mt-1">
                <span>Data Source: <strong className="text-slate-200">{collectionResult.data_source}</strong></span>
                <span>•</span>
                <span>Retrieved: <strong className="text-slate-200">{collectionResult.retrieved_at_local}</strong></span>
                <span>•</span>
                <span>Sessions: <strong className="text-white font-mono">{collectionResult.record_count}</strong></span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Validation Status Badge */}
              <div className={`px-3 py-1 rounded-lg border text-xs font-bold flex items-center gap-1.5 ${
                collectionResult.validation?.status === 'PASSED'
                  ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                  : collectionResult.validation?.status === 'WARNINGS'
                  ? 'bg-amber-950 text-amber-300 border-amber-800'
                  : 'bg-rose-950 text-rose-300 border-rose-800'
              }`}>
                <ShieldCheck size={14} />
                <span>Validation: {collectionResult.validation?.status || 'VERIFIED'}</span>
              </div>

              {/* Add to Watchlist */}
              {onAddToWatchlist && (
                <button
                  type="button"
                  onClick={() => onAddToWatchlist({
                    ticker: collectionResult.ticker,
                    name: collectionResult.company_name,
                    market: collectionResult.market
                  })}
                  disabled={watchlist.some(w => w.ticker === collectionResult.ticker)}
                  className={`px-3 py-1.5 text-xs rounded-lg font-semibold flex items-center gap-1.5 transition ${
                    watchlist.some(w => w.ticker === collectionResult.ticker)
                      ? 'bg-slate-800 text-slate-400 border border-slate-700 cursor-not-allowed'
                      : 'bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-800'
                  }`}
                >
                  <Bookmark size={13} className={watchlist.some(w => w.ticker === collectionResult.ticker) ? 'fill-slate-400' : ''} />
                  <span>{watchlist.some(w => w.ticker === collectionResult.ticker) ? 'In Watchlist' : '+ Watchlist'}</span>
                </button>
              )}

              {/* Export CSV */}
              <button
                type="button"
                onClick={handleExportCSV}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 flex items-center gap-1.5 transition"
              >
                <Download size={13} />
                <span>Export CSV</span>
              </button>
            </div>
          </div>

          {/* Sub-Tab Navigation Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setViewSubTab('ohlcv')}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg flex items-center gap-1.5 transition ${
                  viewSubTab === 'ohlcv'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <TrendingUp size={14} />
                <span>Historical Prices & OHLCV ({collectionResult.record_count})</span>
              </button>

              <button
                type="button"
                onClick={() => setViewSubTab('profile')}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg flex items-center gap-1.5 transition ${
                  viewSubTab === 'profile'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Building2 size={14} />
                <span>Company Profile</span>
              </button>

              <button
                type="button"
                onClick={() => setViewSubTab('financials')}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg flex items-center gap-1.5 transition ${
                  viewSubTab === 'financials'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <FileText size={14} />
                <span>Financial Statements</span>
              </button>

              <button
                type="button"
                onClick={() => setViewSubTab('validation')}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg flex items-center gap-1.5 transition ${
                  viewSubTab === 'validation'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <ShieldCheck size={14} />
                <span>Data Validation Engine</span>
                {collectionResult.validation?.invalid_records > 0 && (
                  <span className="px-1.5 py-0.2 bg-amber-900 text-amber-200 rounded text-[10px]">
                    {collectionResult.validation.invalid_records}
                  </span>
                )}
              </button>
            </div>
          </div>

          {/* VIEW 1: HISTORICAL PRICES & OHLCV TABLE */}
          {viewSubTab === 'ohlcv' && (
            <div className="space-y-4">
              {/* Interactive SVG Price Chart */}
              {chartGeometry && (
                <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-2xl space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <BarChart2 size={15} className="text-blue-400" />
                      <span className="text-xs font-bold text-white uppercase tracking-wider">
                        Interactive Price & Volume Curve ({collectionResult.interval})
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-slate-400">
                      <span>Low: <strong className="text-slate-200">{currencySym}{chartGeometry.minPrice.toFixed(2)}</strong></span>
                      <span>•</span>
                      <span>High: <strong className="text-slate-200">{currencySym}{chartGeometry.maxPrice.toFixed(2)}</strong></span>
                    </div>
                  </div>

                  {/* Chart SVG */}
                  <div className="relative w-full overflow-hidden select-none">
                    <svg
                      viewBox={`0 0 ${chartGeometry.width} ${chartGeometry.height}`}
                      className="w-full h-56 overflow-visible"
                      onMouseLeave={() => setHoverChartIndex(null)}
                    >
                      <defs>
                        <linearGradient id="mktPriceGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={chartGeometry.isUp ? '#10b981' : '#f43f5e'} stopOpacity="0.35" />
                          <stop offset="100%" stopColor={chartGeometry.isUp ? '#10b981' : '#f43f5e'} stopOpacity="0.0" />
                        </linearGradient>
                      </defs>

                      {/* Grid Line */}
                      <line
                        x1={chartGeometry.padX}
                        y1={chartGeometry.padTop}
                        x2={chartGeometry.width - chartGeometry.padX}
                        y2={chartGeometry.padTop}
                        stroke="#1e293b"
                        strokeDasharray="4 4"
                      />
                      <line
                        x1={chartGeometry.padX}
                        y1={chartGeometry.height - chartGeometry.padBottom}
                        x2={chartGeometry.width - chartGeometry.padX}
                        y2={chartGeometry.height - chartGeometry.padBottom}
                        stroke="#334155"
                      />

                      {/* Volume Bars */}
                      {chartGeometry.points.map((p, i) => (
                        <rect
                          key={`vol-${i}`}
                          x={p.x - 1.5}
                          y={p.volY}
                          width="3"
                          height={Math.max(1, p.volHeight)}
                          fill="#334155"
                          opacity={hoverChartIndex === i ? '0.9' : '0.4'}
                        />
                      ))}

                      {/* Gradient Area */}
                      <path d={chartGeometry.areaD} fill="url(#mktPriceGrad)" />

                      {/* Price Line */}
                      <path
                        d={chartGeometry.pathD}
                        fill="none"
                        stroke={chartGeometry.isUp ? '#10b981' : '#f43f5e'}
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />

                      {/* Hover Interactions */}
                      {chartGeometry.points.map((p, i) => (
                        <g key={`hit-${i}`}>
                          <rect
                            x={p.x - (chartGeometry.width / chartGeometry.points.length) / 2}
                            y={0}
                            width={chartGeometry.width / chartGeometry.points.length}
                            height={chartGeometry.height}
                            fill="transparent"
                            className="cursor-crosshair"
                            onMouseEnter={() => setHoverChartIndex(i)}
                          />
                          {hoverChartIndex === i && (
                            <g>
                              <line
                                x1={p.x}
                                y1={chartGeometry.padTop}
                                x2={p.x}
                                y2={chartGeometry.height - chartGeometry.padBottom}
                                stroke="#60a5fa"
                                strokeDasharray="3 3"
                              />
                              <circle
                                cx={p.x}
                                y={p.y}
                                r="5"
                                fill="#60a5fa"
                                stroke="#ffffff"
                                strokeWidth="2"
                              />
                            </g>
                          )}
                        </g>
                      ))}

                      {/* Date Axis Labels */}
                      <text x={chartGeometry.padX} y={chartGeometry.height - 8} fill="#64748b" fontSize="10">
                        {chartGeometry.points[0]?.date}
                      </text>
                      <text x={chartGeometry.width - chartGeometry.padX} y={chartGeometry.height - 8} textAnchor="end" fill="#64748b" fontSize="10">
                        {chartGeometry.points[chartGeometry.points.length - 1]?.date}
                      </text>
                    </svg>

                    {/* Tooltip */}
                    {hoverChartIndex !== null && chartGeometry.points[hoverChartIndex] && (
                      <div
                        className="absolute top-2 pointer-events-none z-10 px-3 py-2 bg-slate-900/95 border border-blue-500/50 rounded-lg shadow-xl text-xs space-y-0.5"
                        style={{
                          left: Math.min(chartGeometry.width - 150, Math.max(10, chartGeometry.points[hoverChartIndex].x - 60))
                        }}
                      >
                        <div className="font-semibold text-slate-200">{chartGeometry.points[hoverChartIndex].date}</div>
                        <div className="font-bold text-white text-sm">
                          Close: {currencySym}{chartGeometry.points[hoverChartIndex].close}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          Vol: {Number(chartGeometry.points[hoverChartIndex].volume).toLocaleString()}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Formatted OHLCV Table */}
              <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Table size={15} className="text-blue-400" />
                    <span className="text-xs font-bold text-white uppercase tracking-wider">
                      OHLCV Data Records (Showing {paginatedOhlcv.length} of {ohlcvList.length} Sessions)
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-slate-400">
                      Page {page} of {totalPages}
                    </span>
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => setPage(p => p - 1)}
                      className="px-2.5 py-1 bg-slate-800 disabled:opacity-40 text-slate-300 rounded text-xs"
                    >
                      Prev
                    </button>
                    <button
                      type="button"
                      disabled={page >= totalPages}
                      onClick={() => setPage(p => p + 1)}
                      className="px-2.5 py-1 bg-slate-800 disabled:opacity-40 text-slate-300 rounded text-xs"
                    >
                      Next
                    </button>
                  </div>
                </div>

                <div className="overflow-x-auto rounded-lg border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 text-[11px] uppercase tracking-wider border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-3 font-semibold">Date</th>
                        <th className="py-2.5 px-3 font-semibold text-right">Open</th>
                        <th className="py-2.5 px-3 font-semibold text-right">High</th>
                        <th className="py-2.5 px-3 font-semibold text-right">Low</th>
                        <th className="py-2.5 px-3 font-semibold text-right">Close</th>
                        <th className="py-2.5 px-3 font-semibold text-right">Day Change</th>
                        <th className="py-2.5 px-3 font-semibold text-right">Volume</th>
                        <th className="py-2.5 px-3 font-semibold text-center">Integrity</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                      {paginatedOhlcv.map((r, idx) => {
                        const isUp = (r.change ?? 0) >= 0;
                        return (
                          <tr key={idx} className="hover:bg-slate-800/40 transition">
                            <td className="py-2 px-3 font-semibold text-white whitespace-nowrap">{r.date}</td>
                            <td className="py-2 px-3 text-right">{r.open !== null ? `${currencySym}${r.open}` : 'N/A'}</td>
                            <td className="py-2 px-3 text-right text-emerald-400">{r.high !== null ? `${currencySym}${r.high}` : 'N/A'}</td>
                            <td className="py-2 px-3 text-right text-rose-400">{r.low !== null ? `${currencySym}${r.low}` : 'N/A'}</td>
                            <td className="py-2 px-3 text-right font-bold text-white">{r.close !== null ? `${currencySym}${r.close}` : 'N/A'}</td>
                            <td className="py-2 px-3 text-right whitespace-nowrap">
                              {r.change !== null && r.change !== undefined ? (
                                <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                  isUp ? 'bg-emerald-950 text-emerald-300' : 'bg-rose-950 text-rose-300'
                                }`}>
                                  {isUp ? '+' : ''}{r.change} ({isUp ? '+' : ''}{r.change_pct}%)
                                </span>
                              ) : '-'}
                            </td>
                            <td className="py-2 px-3 text-right text-slate-400">{Number(r.volume || 0).toLocaleString()}</td>
                            <td className="py-2 px-3 text-center">
                              {r.is_valid ? (
                                <span className="inline-flex items-center text-emerald-400 text-[10px]" title="Validated (No anomalies)">
                                  <CheckCircle size={13} />
                                </span>
                              ) : (
                                <span className="inline-flex items-center text-amber-400 text-[10px]" title={(r.validation_flags || []).join(', ')}>
                                  <AlertTriangle size={13} />
                                </span>
                              )}
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

          {/* VIEW 2: COMPANY PROFILE */}
          {viewSubTab === 'profile' && (
            <div className="space-y-4">
              {/* Profile Card Header */}
              <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="text-xl font-bold text-white">
                      {collectionResult.company_profile?.company_name}
                    </h3>
                    <div className="text-xs text-slate-400 flex items-center gap-2 mt-1">
                      <span>Sector: <strong className="text-slate-200">{collectionResult.company_profile?.sector}</strong></span>
                      <span>•</span>
                      <span>Industry: <strong className="text-slate-200">{collectionResult.company_profile?.industry}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {collectionResult.company_profile?.website !== 'N/A' && (
                      <a
                        href={collectionResult.company_profile?.website}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-blue-400 text-xs rounded-lg transition"
                      >
                        Visit Website
                      </a>
                    )}
                  </div>
                </div>

                {/* Profile Key Stats */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
                    <span className="text-[11px] text-slate-400 block uppercase font-medium">Chief Executive (CEO)</span>
                    <span className="text-sm font-bold text-white mt-1 block">
                      {collectionResult.company_profile?.ceo || 'N/A'}
                    </span>
                  </div>

                  <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
                    <span className="text-[11px] text-slate-400 block uppercase font-medium">Headquarters</span>
                    <span className="text-sm font-bold text-white mt-1 block">
                      {collectionResult.company_profile?.headquarters?.city !== 'N/A'
                        ? `${collectionResult.company_profile.headquarters.city}, ${collectionResult.company_profile.headquarters.country}`
                        : 'N/A'}
                    </span>
                  </div>

                  <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
                    <span className="text-[11px] text-slate-400 block uppercase font-medium">Market Capitalization</span>
                    <span className="text-sm font-bold text-white mt-1 block">
                      {collectionResult.company_profile?.market_cap
                        ? `${currencySym}${Number(collectionResult.company_profile.market_cap).toLocaleString()}`
                        : 'N/A'}
                    </span>
                  </div>

                  <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
                    <span className="text-[11px] text-slate-400 block uppercase font-medium">Full-Time Employees</span>
                    <span className="text-sm font-bold text-white mt-1 block">
                      {collectionResult.company_profile?.employees
                        ? Number(collectionResult.company_profile.employees).toLocaleString()
                        : 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide mb-1.5">
                    Business Overview
                  </h4>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                    {collectionResult.company_profile?.description}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* VIEW 3: FINANCIAL STATEMENTS */}
          {viewSubTab === 'financials' && (
            <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4">
              {/* Financial Statement Tabs */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setFinancialsTab('income')}
                    className={`px-3 py-1.5 text-xs font-bold rounded-lg transition ${
                      financialsTab === 'income'
                        ? 'bg-blue-600 text-white shadow'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    Income Statement
                  </button>
                  <button
                    type="button"
                    onClick={() => setFinancialsTab('balance')}
                    className={`px-3 py-1.5 text-xs font-bold rounded-lg transition ${
                      financialsTab === 'balance'
                        ? 'bg-blue-600 text-white shadow'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    Balance Sheet
                  </button>
                  <button
                    type="button"
                    onClick={() => setFinancialsTab('cash')}
                    className={`px-3 py-1.5 text-xs font-bold rounded-lg transition ${
                      financialsTab === 'cash'
                        ? 'bg-blue-600 text-white shadow'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    Cash Flow Statement
                  </button>
                </div>

                <span className="text-[11px] text-slate-400">
                  Real Financials sourced via yfinance API (in company currency)
                </span>
              </div>

              {/* Financial Data Table */}
              {(() => {
                const fs = collectionResult.financial_statements;
                const activeData = financialsTab === 'income'
                  ? fs?.income_statement
                  : financialsTab === 'balance'
                  ? fs?.balance_sheet
                  : fs?.cash_flow_statement;

                if (!activeData || activeData.length === 0) {
                  return (
                    <div className="p-8 text-center text-xs text-slate-400 bg-slate-950/60 rounded-xl border border-slate-800">
                      No financial statement records published for this ticker on this exchange.
                    </div>
                  );
                }

                // Date columns
                const allKeys = Object.keys(activeData[0] || {}).filter(k => k !== 'metric');

                return (
                  <div className="overflow-x-auto rounded-lg border border-slate-800">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-950 text-slate-300 text-[11px] uppercase tracking-wider border-b border-slate-800">
                        <tr>
                          <th className="py-2.5 px-3 font-semibold">Financial Line Item</th>
                          {allKeys.map((k, i) => (
                            <th key={i} className="py-2.5 px-3 font-semibold text-right font-mono">{k}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-slate-300">
                        {activeData.map((row, i) => (
                          <tr key={i} className="hover:bg-slate-800/40 transition">
                            <td className="py-2 px-3 font-medium text-white">{row.metric}</td>
                            {allKeys.map((k, j) => (
                              <td key={j} className="py-2 px-3 text-right font-mono text-slate-300">
                                {row[k] !== null && row[k] !== undefined
                                  ? Number(row[k]).toLocaleString()
                                  : '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              })()}
            </div>
          )}

          {/* VIEW 4: DATA VALIDATION ENGINE AUDIT */}
          {viewSubTab === 'validation' && (
            <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <ShieldCheck size={16} className="text-emerald-400" />
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Automated Data Quality & Integrity Validation Audit
                  </h4>
                </div>
                <span className="text-[11px] text-slate-400">
                  Total Records Audited: <strong className="text-white font-mono">{collectionResult.validation?.total_records}</strong>
                </span>
              </div>

              {/* 5 Validation Check Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                {/* 1. Null / Missing Values */}
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[11px] text-slate-400 font-medium uppercase block">Missing / Nulls</span>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white">
                      {collectionResult.validation?.null_values_count || 0} Found
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      collectionResult.validation?.checks?.null_values_check === 'PASSED'
                        ? 'bg-emerald-950 text-emerald-300'
                        : 'bg-amber-950 text-amber-300'
                    }`}>
                      {collectionResult.validation?.checks?.null_values_check || 'PASSED'}
                    </span>
                  </div>
                </div>

                {/* 2. Duplicate Dates */}
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[11px] text-slate-400 font-medium uppercase block">Duplicate Dates</span>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white">
                      {collectionResult.validation?.duplicate_dates_count || 0} Found
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      collectionResult.validation?.checks?.duplicate_dates_check === 'PASSED'
                        ? 'bg-emerald-950 text-emerald-300'
                        : 'bg-amber-950 text-amber-300'
                    }`}>
                      {collectionResult.validation?.checks?.duplicate_dates_check || 'PASSED'}
                    </span>
                  </div>
                </div>

                {/* 3. Negative Values */}
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[11px] text-slate-400 font-medium uppercase block">Negative Values</span>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white">
                      {collectionResult.validation?.negative_values_count || 0} Found
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      collectionResult.validation?.checks?.negative_values_check === 'PASSED'
                        ? 'bg-emerald-950 text-emerald-300'
                        : 'bg-rose-950 text-rose-300'
                    }`}>
                      {collectionResult.validation?.checks?.negative_values_check || 'PASSED'}
                    </span>
                  </div>
                </div>

                {/* 4. OHLC Rule Violations */}
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[11px] text-slate-400 font-medium uppercase block">OHLC Relationship</span>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white">
                      {collectionResult.validation?.ohlc_rule_violations_count || 0} Found
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      collectionResult.validation?.checks?.ohlc_relationship_check === 'PASSED'
                        ? 'bg-emerald-950 text-emerald-300'
                        : 'bg-amber-950 text-amber-300'
                    }`}>
                      {collectionResult.validation?.checks?.ohlc_relationship_check || 'PASSED'}
                    </span>
                  </div>
                </div>

                {/* 5. Overall Consistency */}
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[11px] text-slate-400 font-medium uppercase block">Consistency</span>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white">
                      {collectionResult.validation?.valid_records} Valid
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      collectionResult.validation?.status === 'PASSED'
                        ? 'bg-emerald-950 text-emerald-300'
                        : 'bg-amber-950 text-amber-300'
                    }`}>
                      {collectionResult.validation?.status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Validation Warnings List */}
              {collectionResult.validation?.warnings?.length > 0 ? (
                <div className="p-4 bg-amber-950/30 border border-amber-900/60 rounded-xl space-y-2">
                  <span className="text-xs font-bold text-amber-300 uppercase tracking-wide flex items-center gap-1.5">
                    <AlertTriangle size={14} /> Validation Audit Findings:
                  </span>
                  <ul className="text-xs text-amber-200/90 list-disc list-inside space-y-1">
                    {collectionResult.validation.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="p-4 bg-emerald-950/30 border border-emerald-900/50 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
                  <CheckCircle size={15} />
                  <span>All mathematical OHLC relationships and integrity rules verified perfectly with 0 anomalies.</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 5. Past Collections History Panel */}
      <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-lg space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <Clock size={15} className="text-blue-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Persisted Market Collections History ({pastCollections.length})
            </h3>
          </div>
          <button
            type="button"
            onClick={loadPastCollections}
            disabled={loadingPastCollections}
            className="p-1 text-slate-400 hover:text-white rounded"
            title="Refresh history"
          >
            <RefreshCw size={13} className={loadingPastCollections ? 'animate-spin' : ''} />
          </button>
        </div>

        {pastCollections.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {pastCollections.map((c) => (
              <div
                key={c.collection_id}
                onClick={() => handleLoadSavedCollection(c.collection_id)}
                className="p-3 bg-slate-950/70 hover:bg-slate-800/60 border border-slate-800 rounded-xl cursor-pointer transition flex items-center justify-between group"
              >
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-white text-xs">{c.ticker}</span>
                    <span className="px-1.5 py-0.2 bg-blue-950 text-blue-300 border border-blue-900 rounded text-[10px] font-mono">
                      {c.market}
                    </span>
                    <span className={`px-1.5 py-0.2 rounded text-[10px] font-semibold ${
                      c.validation_status === 'PASSED' ? 'text-emerald-400' : 'text-amber-400'
                    }`}>
                      {c.validation_status}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 block truncate max-w-[180px] mt-0.5">
                    {c.company_name}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">
                    {new Date(c.retrieved_at).toLocaleString()} • {c.record_count} bars
                  </span>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={(e) => handleDeletePastCollection(c.collection_id, e)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 rounded-md transition"
                    title="Delete collection"
                  >
                    <Trash2 size={13} />
                  </button>
                  <ChevronRight size={14} className="text-slate-600 group-hover:text-white transition" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 text-center text-xs text-slate-500">
            No market data collections saved in PostgreSQL yet. Select a stock above and click "Collect Market Data".
          </div>
        )}
      </div>

      {/* Toast Notification Banner */}
      {toast.message && (
        <div className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl text-xs font-medium flex items-center gap-2 border transition ${
          toast.type === 'error'
            ? 'bg-rose-950 text-rose-200 border-rose-800'
            : 'bg-emerald-950 text-emerald-200 border-emerald-800'
        }`}>
          {toast.type === 'error' ? <AlertCircle size={16} /> : <CheckCircle size={16} />}
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}
