import React, { useState, useEffect, useRef } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { 
  Bookmark, Trash2, Search, Sliders, History, 
  PlayCircle, FileText, CheckCircle, Clock, AlertTriangle,
  X, ExternalLink, ChevronRight, Sparkles, Building2, TrendingUp, AlertCircle, Printer,
  Plus, Check, Eye
} from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();

  // Tab View State: 'overview' | 'history' | 'watchlist'
  const [activeTab, setActiveTab] = useState('overview');

  // Preferences State
  const [preferences, setPreferences] = useState({
    preferred_market: 'NASDAQ',
    default_analysis_period: '1 Year'
  });
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [prefMessage, setPrefMessage] = useState('');

  // Watchlist State
  const [watchlist, setWatchlist] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [watchlistError, setWatchlistError] = useState('');

  // Research Tasks History State
  const [tasks, setTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [launchingResearch, setLaunchingResearch] = useState(false);
  const [directTicker, setDirectTicker] = useState('');
  const [directMarket, setDirectMarket] = useState('NASDAQ');
  const [directPeriod, setDirectPeriod] = useState('1 Year');

  // Dynamic Company Autocomplete State
  const [companyNameInput, setCompanyNameInput] = useState('');
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [companySuggestions, setCompanySuggestions] = useState([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const autocompleteRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const activeQueryRef = useRef('');
  const latestRequestIdRef = useRef(0);
  const abortControllerRef = useRef(null);
  const marketCompaniesCacheRef = useRef({});

  // Selected Report Modal State
  const [selectedReport, setSelectedReport] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);

  // Confirmation Dialog State
  const [confirmModal, setConfirmModal] = useState({
    isOpen: false,
    title: '',
    message: '',
    confirmText: 'Confirm',
    onConfirm: () => {}
  });

  // Toast Notification State
  const [notification, setNotification] = useState({ message: '', type: '' });

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => {
      setNotification({ message: '', type: '' });
    }, 3500);
  };

  useEffect(() => {
    loadPreferences();
    loadWatchlist();
    loadTasks();
    preloadExchangeCompanies(directMarket);
  }, []);

  const preloadExchangeCompanies = async (market) => {
    if (!market || marketCompaniesCacheRef.current[market]) return;
    try {
      const res = await api.get('/watchlist/companies', {
        params: { market }
      });
      marketCompaniesCacheRef.current[market] = res.data;
    } catch (err) {
      console.error('Failed to preload exchange companies:', err);
    }
  };

  // Close company suggestions dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (autocompleteRef.current && !autocompleteRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const loadPreferences = async () => {
    try {
      const res = await api.get('/preferences');
      setPreferences(res.data);
      if (res.data.preferred_market) {
        setDirectMarket(res.data.preferred_market);
        preloadExchangeCompanies(res.data.preferred_market);
      }
      if (res.data.default_analysis_period) setDirectPeriod(res.data.default_analysis_period);
    } catch (err) {
      console.error('Failed to load preferences:', err);
    }
  };

  const handleSavePreferences = async (e) => {
    e.preventDefault();
    setSavingPrefs(true);
    setPrefMessage('');
    try {
      await api.put('/preferences', preferences);
      setPrefMessage('Preferences updated successfully!');
      showNotification('Preferences updated successfully!', 'success');
      setTimeout(() => setPrefMessage(''), 3000);
    } catch (err) {
      setPrefMessage('Failed to update preferences.');
      showNotification('Failed to update preferences.', 'error');
    } finally {
      setSavingPrefs(false);
    }
  };

  const loadWatchlist = async () => {
    try {
      const res = await api.get('/watchlist');
      setWatchlist(res.data);
    } catch (err) {
      console.error('Failed to load watchlist:', err);
    }
  };

  const handleSearchStocks = async (val) => {
    setSearchQuery(val);
    if (!val.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      const res = await api.get(`/watchlist/search?q=${encodeURIComponent(val)}&market=${preferences.preferred_market}`);
      setSearchResults(res.data);
    } catch (err) {
      console.error('Stock search failed:', err);
    }
  };

  const handleAddToWatchlist = async (stock) => {
    setWatchlistError('');
    try {
      await api.post('/watchlist', {
        ticker: stock.ticker,
        company_name: stock.name || stock.company_name,
        market: stock.market
      });
      setSearchQuery('');
      setSearchResults([]);
      await loadWatchlist();
      showNotification(`${stock.ticker} added to your personal watchlist!`, 'success');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to add stock.';
      setWatchlistError(msg);
      showNotification(msg, 'error');
    }
  };

  // Watchlist Removal with Confirmation Dialog
  const promptRemoveFromWatchlist = (stock) => {
    setConfirmModal({
      isOpen: true,
      title: 'Remove from Watchlist',
      message: `Are you sure you want to remove ${stock.company_name || stock.ticker} (${stock.market || 'NASDAQ'}) from your personal watchlist?`,
      confirmText: 'Remove Stock',
      onConfirm: () => handleConfirmRemoveWatchlist(stock.ticker)
    });
  };

  const handleConfirmRemoveWatchlist = async (ticker) => {
    try {
      await api.delete(`/watchlist/${ticker}`);
      await loadWatchlist();
      showNotification(`${ticker} removed from your watchlist.`, 'success');
    } catch (err) {
      showNotification(err.response?.data?.detail || 'Failed to remove stock.', 'error');
    } finally {
      setConfirmModal(prev => ({ ...prev, isOpen: false }));
    }
  };

  // Research a Saved Stock
  const handleResearchSavedStock = async (stock) => {
    const market = stock.market || preferences.preferred_market;
    const ticker = stock.ticker;
    const name = stock.company_name || stock.ticker;

    setDirectMarket(market);
    setCompanyNameInput(name);
    setDirectTicker(ticker);
    setSelectedCompany({ ticker, name, market });

    showNotification(`Initiating research task for ${ticker} (${market})...`, 'success');
    await handleLaunchResearch(ticker, name, market, directPeriod);
  };

  const loadTasks = async (showLoading = true) => {
    if (showLoading) setLoadingTasks(true);
    try {
      const res = await api.get('/tasks');
      setTasks(res.data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      if (showLoading) setLoadingTasks(false);
    }
  };

  // Real-time status tracker: automatically poll backend whenever any research task is in Pending or Processing state
  useEffect(() => {
    const hasActiveTasks = tasks.some(t => t.status === 'Pending' || t.status === 'Processing');
    if (!hasActiveTasks) return;

    const timer = setInterval(() => {
      loadTasks(false);
    }, 1200);

    return () => clearInterval(timer);
  }, [tasks]);

  const handleLaunchResearch = async (ticker, companyName, market, period) => {
    setLaunchingResearch(true);
    try {
      const res = await api.post('/tasks', {
        ticker,
        company_name: companyName,
        market: market || preferences.preferred_market,
        requested_period: period || preferences.default_analysis_period
      });
      // Prepend the new Pending task immediately so the user sees the initial Pending badge right away
      setTasks(prev => [res.data, ...prev.filter(t => t.task_id !== res.data.task_id)]);
      showNotification(`Research initiated for ${ticker}. Analysis in progress...`, 'info');
    } catch (err) {
      showNotification('Error initiating research workflow.', 'error');
    } finally {
      setLaunchingResearch(false);
    }
  };

  // Research Task Deletion with Confirmation Dialog
  const promptDeleteTask = (task) => {
    setConfirmModal({
      isOpen: true,
      title: 'Delete Research Entry',
      message: `Are you sure you want to permanently delete the research task for ${task.company_name || task.ticker} (${task.market})? This action cannot be undone.`,
      confirmText: 'Permanently Delete',
      onConfirm: () => handleConfirmDeleteTask(task.task_id)
    });
  };

  const handleConfirmDeleteTask = async (taskId) => {
    try {
      await api.delete(`/tasks/${taskId}`);
      setTasks(prev => prev.filter(t => t.task_id !== taskId));
      showNotification('Research entry permanently deleted.', 'success');
    } catch (err) {
      showNotification(err.response?.data?.detail || 'Failed to delete research entry.', 'error');
    } finally {
      setConfirmModal(prev => ({ ...prev, isOpen: false }));
    }
  };

  const handleMarketChange = (e) => {
    const newMarket = e.target.value;
    setDirectMarket(newMarket);

    // Cancel in-flight requests and timers
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    if (abortControllerRef.current) abortControllerRef.current.abort();
    activeQueryRef.current = '';
    latestRequestIdRef.current += 1;

    // Requirement: Changing the exchange must clear the previously selected company
    setCompanyNameInput('');
    setSelectedCompany(null);
    setDirectTicker('');
    setCompanySuggestions([]);
    setShowSuggestions(false);
    setLoadingSuggestions(false);

    preloadExchangeCompanies(newMarket);
  };

  const handleCompanyInputChange = (e) => {
    const val = e.target.value;
    setCompanyNameInput(val);
    setSelectedCompany(null);
    setDirectTicker(val);

    const query = val.trim();
    activeQueryRef.current = query;

    // Clear any pending timer and abort in-flight requests
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Clear outdated suggestions when a new search begins
    setCompanySuggestions([]);

    if (!query) {
      setShowSuggestions(false);
      setLoadingSuggestions(false);
      return;
    }

    setShowSuggestions(true);

    // Ensure suggestions update immediately whenever the input changes
    const cached = marketCompaniesCacheRef.current[directMarket];
    if (cached && cached.length > 0) {
      const immediateMatches = cached.filter(comp =>
        comp.market.toUpperCase() === directMarket.toUpperCase() &&
        comp.name.toLowerCase().startsWith(query.toLowerCase())
      );
      setCompanySuggestions(immediateMatches);
      setLoadingSuggestions(false);
    } else {
      setLoadingSuggestions(true);
    }

    // Prevent stale or asynchronous API responses from overwriting newer search results
    const reqId = ++latestRequestIdRef.current;
    const controller = new AbortController();
    abortControllerRef.current = controller;

    debounceTimerRef.current = setTimeout(async () => {
      try {
        const res = await api.get('/watchlist/companies', {
          params: {
            market: directMarket,
            q: query
          },
          signal: controller.signal
        });

        // Discard stale or out-of-order response
        if (reqId !== latestRequestIdRef.current || activeQueryRef.current !== query) {
          return;
        }

        // Apply strict prefix-based matching
        const strictMatches = res.data.filter(comp =>
          comp.market.toUpperCase() === directMarket.toUpperCase() &&
          comp.name.toLowerCase().startsWith(query.toLowerCase())
        );

        setCompanySuggestions(strictMatches);
      } catch (err) {
        if (err.name !== 'CanceledError' && err.code !== 'ERR_CANCELED') {
          console.error('Failed to fetch company suggestions:', err);
        }
      } finally {
        if (reqId === latestRequestIdRef.current) {
          setLoadingSuggestions(false);
        }
      }
    }, 100);
  };

  const handleSelectCompany = (comp) => {
    setSelectedCompany(comp);
    setCompanyNameInput(comp.name);
    setDirectTicker(comp.ticker);
    setShowSuggestions(false);
  };

  const handleDirectResearch = async (e) => {
    e.preventDefault();
    const targetTicker = selectedCompany ? selectedCompany.ticker : (directTicker.trim() || companyNameInput.trim());
    const targetName = selectedCompany ? selectedCompany.name : (companyNameInput.trim() || null);
    if (!targetTicker) return;

    await handleLaunchResearch(targetTicker, targetName, directMarket, directPeriod);
    setCompanyNameInput('');
    setSelectedCompany(null);
    setDirectTicker('');
    setCompanySuggestions([]);
    setShowSuggestions(false);
  };

  const handleOpenReport = async (taskId) => {
    setLoadingReport(true);
    setSelectedReport(null);
    try {
      const res = await api.get(`/tasks/${taskId}`);
      setSelectedReport(res.data);
    } catch (err) {
      showNotification('Failed to retrieve task report.', 'error');
    } finally {
      setLoadingReport(false);
    }
  };

  // Status Badge Component Helper
  const renderStatusBadge = (status) => {
    switch (status) {
      case 'Completed':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded-full font-medium bg-emerald-950/70 text-emerald-400 border border-emerald-800/80">
            <CheckCircle size={12} /> Completed
          </span>
        );
      case 'Processing':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded-full font-medium bg-amber-950/70 text-amber-400 border border-amber-800/80 animate-pulse">
            <Clock size={12} /> Processing
          </span>
        );
      case 'Pending':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded-full font-medium bg-blue-950/70 text-blue-300 border border-blue-800/80">
            <Clock size={12} /> Pending
          </span>
        );
      case 'Failed':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded-full font-medium bg-rose-950/70 text-rose-400 border border-rose-800/80">
            <AlertTriangle size={12} /> Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded-full font-medium bg-slate-800 text-slate-300 border border-slate-700">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-950 via-slate-900 to-indigo-950 border border-blue-900/50 p-6 shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-400 mb-1">
              <Sparkles size={14} /> Research Workspace Dashboard
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white">
              Hello, {user?.full_name}
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Active Focus: <span className="text-blue-300 font-semibold">{preferences.preferred_market}</span> Exchange • Default Period: <span className="text-blue-300 font-semibold">{preferences.default_analysis_period}</span>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('watchlist')}
              className="text-xs bg-slate-800/80 hover:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 transition flex items-center gap-1.5"
            >
              <Bookmark size={13} className="text-emerald-400" />
              <span>Watchlist: <strong className="text-white">{watchlist.length}</strong></span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className="text-xs bg-slate-800/80 hover:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 transition flex items-center gap-1.5"
            >
              <History size={13} className="text-blue-400" />
              <span>Research Tasks: <strong className="text-white">{tasks.length}</strong></span>
            </button>
          </div>
        </div>
      </div>

      {/* View Switcher Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition ${
            activeTab === 'overview'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
              : 'bg-slate-900/80 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <Sparkles size={14} />
          <span>Dashboard Overview</span>
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition ${
            activeTab === 'history'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
              : 'bg-slate-900/80 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <History size={14} />
          <span>Research History ({tasks.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('watchlist')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition ${
            activeTab === 'watchlist'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
              : 'bg-slate-900/80 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <Bookmark size={14} />
          <span>Dedicated Watchlist ({watchlist.length})</span>
        </button>
      </div>

      {/* VIEW 1 & 2: Main Grid or Full History View */}
      {(activeTab === 'overview' || activeTab === 'history') && (
        <div className={`grid grid-cols-1 ${activeTab === 'overview' ? 'lg:grid-cols-12' : 'lg:grid-cols-1'} gap-6`}>
          
          {/* Left Column (Preferences + Watchlist sidebar) - Visible in Overview */}
          {activeTab === 'overview' && (
            <div className="lg:col-span-4 space-y-6">
              
              {/* Preferences Card */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
                <div className="flex items-center gap-2 mb-4 text-white font-semibold border-b border-slate-800 pb-3">
                  <Sliders size={18} className="text-blue-400" />
                  <span>Workspace Preferences</span>
                </div>

                {prefMessage && (
                  <div className="mb-3 p-2.5 bg-emerald-950/60 border border-emerald-800 rounded text-emerald-300 text-xs flex items-center gap-1.5">
                    <CheckCircle size={14} /> {prefMessage}
                  </div>
                )}

                <form onSubmit={handleSavePreferences} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1.5">
                      Stock Market Preference
                    </label>
                    <select
                      value={preferences.preferred_market}
                      onChange={(e) => setPreferences({ ...preferences, preferred_market: e.target.value })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="NASDAQ">NASDAQ – US Stock Exchange</option>
                      <option value="NYSE">NYSE – New York Stock Exchange</option>
                      <option value="NSE">NSE – National Stock Exchange of India</option>
                      <option value="BSE">BSE – Bombay Stock Exchange, India</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1.5">
                      Default Analysis Period
                    </label>
                    <select
                      value={preferences.default_analysis_period}
                      onChange={(e) => setPreferences({ ...preferences, default_analysis_period: e.target.value })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="1 Month">1 Month</option>
                      <option value="3 Months">3 Months</option>
                      <option value="6 Months">6 Months</option>
                      <option value="1 Year">1 Year</option>
                      <option value="5 Years">5 Years</option>
                    </select>
                  </div>

                  <button
                    type="submit"
                    disabled={savingPrefs}
                    className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition disabled:opacity-50"
                  >
                    {savingPrefs ? 'Saving...' : 'Save Preferences'}
                  </button>
                </form>
              </div>

              {/* Watchlist Sidebar Card */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
                <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2 text-white font-semibold">
                    <Bookmark size={18} className="text-emerald-400" />
                    <span>Saved Watchlist</span>
                  </div>
                  <button
                    onClick={() => setActiveTab('watchlist')}
                    className="text-xs text-blue-400 hover:text-blue-300 font-medium"
                  >
                    View All ({watchlist.length}) →
                  </button>
                </div>

                {/* Stock Search Input */}
                <div className="relative mb-3">
                  <input
                    type="text"
                    placeholder="Search stock symbol or name..."
                    value={searchQuery}
                    onChange={(e) => handleSearchStocks(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                  <Search size={16} className="absolute left-3 top-2.5 text-slate-500" />

                  {/* Autocomplete Dropdown */}
                  {searchResults.length > 0 && (
                    <div className="absolute z-20 w-full mt-1.5 bg-slate-900 border border-slate-700 rounded-xl max-h-64 overflow-y-auto shadow-2xl divide-y divide-slate-800">
                      {searchResults.map((s) => (
                        <div
                          key={`${s.market}-${s.ticker}`}
                          className="px-3 py-2 hover:bg-slate-850 flex items-center justify-between gap-2 transition"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span className="text-white font-semibold text-xs">{s.ticker}</span>
                              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-950 text-blue-300 border border-blue-900">
                                {s.market}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-400 truncate">{s.name}</p>
                          </div>
                          <div className="flex items-center gap-1 shrink-0">
                            <button
                              type="button"
                              onClick={() => handleAddToWatchlist(s)}
                              className="px-2 py-1 text-[11px] font-medium bg-slate-800 hover:bg-emerald-950 text-slate-300 hover:text-emerald-400 border border-slate-700 hover:border-emerald-800 rounded transition"
                              title="Save to Watchlist"
                            >
                              + Watchlist
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                handleLaunchResearch(s.ticker, s.name, s.market);
                                setSearchQuery('');
                                setSearchResults([]);
                              }}
                              className="px-2 py-1 text-[11px] font-medium bg-blue-950 hover:bg-blue-900 text-blue-300 border border-blue-800 rounded flex items-center gap-1 transition"
                              title="Run Research Now"
                            >
                              <PlayCircle size={12} />
                              <span>Research</span>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {watchlistError && (
                  <p className="text-xs text-red-400 mb-3 p-2 bg-red-950/40 border border-red-900/50 rounded">
                    {watchlistError}
                  </p>
                )}

                {/* Watchlist Items */}
                <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                  {watchlist.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      <Bookmark size={28} className="mx-auto mb-2 opacity-30" />
                      <p className="text-xs">Your watchlist is empty.</p>
                      <p className="text-[11px] text-slate-600 mt-0.5">Search a ticker above to save it.</p>
                    </div>
                  ) : (
                    watchlist.map((item) => (
                      <div
                        key={item.saved_stock_id}
                        className="flex items-center justify-between p-3 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/50 rounded-xl transition group"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white text-sm">{item.ticker}</span>
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">
                              {item.market || 'NASDAQ'}
                            </span>
                            {item.last_price > 0 && (
                              <span className="text-xs font-semibold text-slate-200 ml-1">
                                {item.currency === 'INR' ? '₹' : '$'}{item.last_price}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-slate-400">
                            <span className="truncate max-w-[130px]">
                              {item.company_name || item.ticker}
                            </span>
                            {item.change_pct !== undefined && item.change_pct !== null && (
                              <span className={`text-[11px] font-mono font-medium ${item.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {item.change >= 0 ? '+' : ''}{item.change_pct}%
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            title="Research Now (Auto-selects company & market)"
                            onClick={() => handleResearchSavedStock(item)}
                            className="p-1.5 text-blue-400 hover:text-blue-300 hover:bg-blue-950/50 rounded-lg transition"
                          >
                            <PlayCircle size={18} />
                          </button>
                          <button
                            title="Remove from Watchlist"
                            onClick={() => promptRemoveFromWatchlist(item)}
                            className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-950/50 rounded-lg transition"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Right / Main Column: Research History */}
          <div className={`${activeTab === 'overview' ? 'lg:col-span-8' : 'w-full'}`}>
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg h-full flex flex-col">
              <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2 text-white font-semibold">
                  <History size={18} className="text-blue-400" />
                  <span>User-Specific Research History</span>
                </div>
                <button
                  onClick={loadTasks}
                  className="text-xs px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
                >
                  Refresh
                </button>
              </div>

              {/* Quick Launch Direct Research */}
              <div className="mb-4 p-4 bg-slate-800/40 border border-slate-700/60 rounded-xl">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                    <PlayCircle size={13} className="text-blue-400" /> Start New Research Task
                  </span>
                  <span className="text-[10px] text-slate-400">Selected exchange market filtering</span>
                </div>

                <form onSubmit={handleDirectResearch} className="flex flex-wrap items-end gap-3">
                  {/* 1. Exchange Market Selection (First) */}
                  <div className="w-full sm:w-auto">
                    <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                      1. Exchange Market
                    </label>
                    <select
                      value={directMarket}
                      onChange={handleMarketChange}
                      className="w-full sm:w-auto bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 font-medium"
                      title="Select Exchange Market"
                    >
                      <option value="NSE">NSE (India)</option>
                      <option value="BSE">BSE (India)</option>
                      <option value="NASDAQ">NASDAQ (US)</option>
                      <option value="NYSE">NYSE (US)</option>
                    </select>
                  </div>

                  {/* 2. Company Name Input with Dynamic Autocomplete Dropdown */}
                  <div ref={autocompleteRef} className="relative flex-1 min-w-[240px]">
                    <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                      2. Company Name ({directMarket})
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        required
                        placeholder={`Search ${directMarket} company (e.g. ${directMarket === 'NSE' || directMarket === 'BSE' ? 'Tata Motors, Infosys' : 'Apple, Microsoft'})...`}
                        value={companyNameInput}
                        onChange={handleCompanyInputChange}
                        onFocus={() => {
                          if (companyNameInput.trim().length > 0) {
                            setShowSuggestions(true);
                          }
                        }}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-3 pr-8 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                      />
                      {loadingSuggestions && (
                        <div className="absolute right-2.5 top-2.5">
                          <div className="animate-spin rounded-full h-3.5 w-3.5 border-t-2 border-b-2 border-blue-400"></div>
                        </div>
                      )}
                    </div>

                    {/* Autocomplete Suggestions Dropdown */}
                    {showSuggestions && companyNameInput.trim().length > 0 && (
                      <div className="absolute left-0 right-0 z-30 mt-1.5 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl max-h-56 overflow-y-auto divide-y divide-slate-800">
                        {loadingSuggestions ? (
                          <div className="p-3 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                            <div className="animate-spin rounded-full h-3 w-3 border-t-2 border-b-2 border-blue-400"></div>
                            <span>Searching {directMarket}-listed companies...</span>
                          </div>
                        ) : companySuggestions.length === 0 ? (
                          <div className="p-3 text-center text-xs text-slate-400">
                            No results found
                          </div>
                        ) : (
                          companySuggestions.map((s) => (
                            <button
                              key={`${s.market}-${s.ticker}`}
                              type="button"
                              onClick={() => handleSelectCompany(s)}
                              className="w-full text-left px-3.5 py-2.5 hover:bg-slate-800/80 flex items-center justify-between gap-2 transition group"
                            >
                              <div className="min-w-0 flex-1">
                                <div className="text-xs font-semibold text-white group-hover:text-blue-300 truncate">
                                  {s.name}
                                </div>
                                <div className="text-[10px] text-slate-400 font-mono">
                                  Ticker: <span className="text-slate-200 font-semibold">{s.ticker}</span>
                                </div>
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                    )}
                  </div>

                  {/* 3. Analysis Period */}
                  <div className="w-full sm:w-auto">
                    <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                      3. Analysis Period
                    </label>
                    <select
                      value={directPeriod}
                      onChange={(e) => setDirectPeriod(e.target.value)}
                      className="w-full sm:w-auto bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 font-medium"
                      title="Historical Analysis Window"
                    >
                      <option value="1 Month">1 Month</option>
                      <option value="3 Months">3 Months</option>
                      <option value="6 Months">6 Months</option>
                      <option value="1 Year">1 Year</option>
                      <option value="5 Years">5 Years</option>
                    </select>
                  </div>

                  {/* 4. Action Button */}
                  <button
                    type="submit"
                    disabled={launchingResearch || !companyNameInput.trim()}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 transition disabled:opacity-50 shadow-md shadow-blue-600/30 shrink-0"
                  >
                    <PlayCircle size={14} />
                    <span>{launchingResearch ? 'Analyzing...' : 'Run Research'}</span>
                  </button>
                </form>
              </div>

              {loadingTasks ? (
                <div className="flex-1 flex justify-center items-center py-16">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                </div>
              ) : tasks.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center py-16 text-slate-500">
                  <History size={40} className="mb-2 opacity-25" />
                  <p className="text-sm font-medium">No research history found</p>
                  <p className="text-xs text-slate-600 mt-1 max-w-sm text-center">
                    Initiate stock research above or from your saved watchlist to generate research records.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto flex-1">
                  <table className="w-full text-left text-sm text-slate-300">
                    <thead className="text-[11px] uppercase tracking-wider bg-slate-800 text-slate-400 border-b border-slate-700">
                      <tr>
                        <th className="px-4 py-3">Company & Ticker</th>
                        <th className="px-4 py-3">Market</th>
                        <th className="px-4 py-3">Period</th>
                        <th className="px-4 py-3">Date</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80">
                      {tasks.map((task) => (
                        <tr key={task.task_id} className="hover:bg-slate-800/40 transition">
                          <td className="px-4 py-3">
                            <div className="font-semibold text-white">{task.ticker}</div>
                            <div className="text-xs text-slate-400 truncate max-w-[180px]">
                              {task.company_name}
                            </div>
                          </td>
                          <td className="px-4 py-3 font-mono text-xs">{task.market}</td>
                          <td className="px-4 py-3 text-xs">{task.requested_period}</td>
                          <td className="px-4 py-3 text-xs text-slate-400">
                            {new Date(task.created_at).toLocaleDateString(undefined, {
                              month: 'short',
                              day: 'numeric',
                              year: 'numeric'
                            })}
                          </td>
                          <td className="px-4 py-3">
                            {renderStatusBadge(task.status)}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                onClick={() => handleOpenReport(task.task_id)}
                                className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 bg-blue-950 hover:bg-blue-900 text-blue-300 border border-blue-800/60 rounded-lg transition"
                                title="View Research Report"
                              >
                                <FileText size={13} />
                                <span>Report</span>
                              </button>
                              <button
                                onClick={() => promptDeleteTask(task)}
                                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-950/50 rounded-lg transition border border-transparent hover:border-rose-900/50"
                                title="Delete Research Entry"
                              >
                                <Trash2 size={15} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* VIEW 3: Dedicated Watchlist View */}
      {activeTab === 'watchlist' && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2 text-white font-bold text-lg">
                <Bookmark size={20} className="text-emerald-400" />
                <span>Personal Stock Watchlist</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800">
                  {watchlist.length} saved
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Monitor key equities across exchanges. Research saved assets with one click.
              </p>
            </div>

            {/* Quick Add Search Bar inside Dedicated Watchlist */}
            <div className="relative w-full md:w-80">
              <input
                type="text"
                placeholder="Search stock to add to watchlist..."
                value={searchQuery}
                onChange={(e) => handleSearchStocks(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />

              {searchResults.length > 0 && (
                <div className="absolute z-30 w-full mt-1.5 bg-slate-900 border border-slate-700 rounded-xl max-h-64 overflow-y-auto shadow-2xl divide-y divide-slate-800">
                  {searchResults.map((s) => (
                    <div
                      key={`dedicated-${s.market}-${s.ticker}`}
                      className="px-3 py-2 hover:bg-slate-800 flex items-center justify-between gap-2 transition"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="text-white font-semibold text-xs">{s.ticker}</span>
                          <span className="text-[10px] font-mono px-1.5 rounded bg-blue-950 text-blue-300 border border-blue-900">
                            {s.market}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 truncate">{s.name}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleAddToWatchlist(s)}
                        className="px-2 py-1 text-[11px] font-medium bg-slate-800 hover:bg-emerald-950 text-slate-300 hover:text-emerald-400 border border-slate-700 hover:border-emerald-800 rounded transition"
                      >
                        + Watchlist
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Dedicated Watchlist Table */}
          {watchlist.length === 0 ? (
            <div className="text-center py-16 text-slate-500">
              <Bookmark size={48} className="mx-auto mb-3 opacity-25" />
              <h3 className="text-sm font-semibold text-slate-300">Your Watchlist is Empty</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Search stocks using the bar above or save companies directly from research reports to track them here.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="text-[11px] uppercase tracking-wider bg-slate-800/80 text-slate-400 border-b border-slate-700">
                  <tr>
                    <th className="px-4 py-3">Company Name</th>
                    <th className="px-4 py-3">Stock Symbol</th>
                    <th className="px-4 py-3">Exchange Market</th>
                    <th className="px-4 py-3">Date Added</th>
                    <th className="px-4 py-3">Current Market Quote</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {watchlist.map((item) => (
                    <tr key={item.saved_stock_id} className="hover:bg-slate-800/40 transition">
                      <td className="px-4 py-3 font-semibold text-white">
                        {item.company_name || item.ticker}
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-mono font-bold text-white text-xs bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                          {item.ticker}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-900">
                          {item.market || 'NASDAQ'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-400">
                        {item.created_at ? new Date(item.created_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric'
                        }) : 'N/A'}
                      </td>
                      <td className="px-4 py-3">
                        {item.last_price > 0 ? (
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white text-xs font-mono">
                              {item.currency === 'INR' ? '₹' : '$'}{item.last_price}
                            </span>
                            {item.change_pct !== undefined && item.change_pct !== null && (
                              <span className={`text-[11px] font-mono font-medium ${item.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {item.change >= 0 ? '+' : ''}{item.change_pct}%
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-slate-500 font-mono">Market closed</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleResearchSavedStock(item)}
                            className="px-3 py-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white rounded-lg flex items-center gap-1.5 transition shadow"
                            title="Auto-selects company and exchange in research form"
                          >
                            <PlayCircle size={13} />
                            <span>Research Now</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => promptRemoveFromWatchlist(item)}
                            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-950/50 rounded-lg transition border border-transparent hover:border-rose-900/50"
                            title="Remove from Watchlist"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Confirmation Dialog Modal */}
      {confirmModal.isOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl relative animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-rose-950/60 border border-rose-800 flex items-center justify-center text-rose-400 shrink-0">
                <Trash2 size={20} />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">{confirmModal.title}</h3>
                <p className="text-xs text-slate-400">Confirmation Required</p>
              </div>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed mb-6">
              {confirmModal.message}
            </p>
            <div className="flex items-center justify-end gap-2.5">
              <button
                type="button"
                onClick={() => setConfirmModal(prev => ({ ...prev, isOpen: false }))}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmModal.onConfirm}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-rose-600/30 transition flex items-center gap-1.5"
              >
                <Trash2 size={13} />
                <span>{confirmModal.confirmText}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Research Report Dossier Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative max-h-[90vh] flex flex-col">
            <button
              onClick={() => setSelectedReport(null)}
              className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
              title="Close Modal"
            >
              <X size={18} />
            </button>

            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-400 mb-1">
              <FileText size={15} /> Research Report Dossier
            </div>

            <h3 className="text-xl font-bold text-white mb-2">
              {selectedReport.report?.title || `${selectedReport.company_name} (${selectedReport.ticker})`}
            </h3>

            {/* Badges + Add to Watchlist Header Action */}
            <div className="flex flex-wrap items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-800">
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="px-2.5 py-0.5 bg-slate-800 text-slate-300 rounded-md border border-slate-700 font-medium">
                  Exchange: <strong className="text-white">{selectedReport.market}</strong>
                </span>
                <span className="px-2.5 py-0.5 bg-slate-800 text-slate-300 rounded-md border border-slate-700 font-medium">
                  Window: <strong className="text-white">{selectedReport.requested_period}</strong>
                </span>
                {renderStatusBadge(selectedReport.status)}
              </div>

              {/* Requirement 3.A: Add to Watchlist from Stock Research page */}
              <button
                type="button"
                onClick={() => handleAddToWatchlist({
                  ticker: selectedReport.ticker,
                  name: selectedReport.company_name,
                  market: selectedReport.market
                })}
                disabled={watchlist.some(w => w.ticker === selectedReport.ticker)}
                className={`px-3 py-1.5 text-xs rounded-lg font-semibold flex items-center gap-1.5 transition ${
                  watchlist.some(w => w.ticker === selectedReport.ticker)
                    ? 'bg-slate-800 text-slate-400 border border-slate-700 cursor-not-allowed'
                    : 'bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-800 shadow'
                }`}
              >
                <Bookmark size={13} className={watchlist.some(w => w.ticker === selectedReport.ticker) ? 'fill-slate-400' : ''} />
                <span>{watchlist.some(w => w.ticker === selectedReport.ticker) ? 'Saved in Watchlist' : '+ Add to Watchlist'}</span>
              </button>
            </div>

            {/* Scrollable Content Body */}
            <div className="overflow-y-auto pr-1 space-y-4 flex-1">
              
              {/* Executive Summary */}
              {selectedReport.report?.summary && (
                <div className="p-3.5 bg-blue-950/40 border border-blue-800/60 rounded-xl">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-blue-300 mb-1 flex items-center gap-1.5">
                    <Sparkles size={14} /> Executive Summary
                  </h4>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {selectedReport.report.summary}
                  </p>
                </div>
              )}

              {/* Detailed Market Findings & OHLCV Records */}
              <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                  <TrendingUp size={14} className="text-emerald-400" /> Dynamic Market Findings & Trading Records
                </h4>
                <div className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed bg-slate-900/90 p-3 rounded-lg border border-slate-800">
                  {selectedReport.report?.analyst_notes || 'No detailed market notes recorded.'}
                </div>
              </div>

              {/* Limitations & Constraints */}
              {selectedReport.report?.limitations && (
                <div className="p-3 bg-amber-950/30 border border-amber-900/50 rounded-xl text-xs text-amber-300/90 flex items-start gap-2">
                  <AlertCircle size={15} className="shrink-0 mt-0.5 text-amber-400" />
                  <div>
                    <strong className="font-semibold block text-amber-300">Data Limitations & Scope:</strong>
                    <span>{selectedReport.report.limitations}</span>
                  </div>
                </div>
              )}

              {/* Task Metadata Footer */}
              <div className="text-[11px] text-slate-500 pt-2 border-t border-slate-800 flex flex-wrap justify-between gap-2">
                <span>Task ID: <code className="text-slate-400">{selectedReport.task_id}</code></span>
                <span>Initiated: {new Date(selectedReport.created_at).toLocaleString()}</span>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-4 mt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => window.print()}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium rounded-lg flex items-center gap-1.5 transition"
              >
                <Printer size={13} />
                <span>Print Report</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedReport(null)}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification Banner */}
      {notification.message && (
        <div className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl text-xs font-medium flex items-center gap-2 border transition ${
          notification.type === 'error'
            ? 'bg-rose-950 text-rose-200 border-rose-800'
            : 'bg-emerald-950 text-emerald-200 border-emerald-800'
        }`}>
          {notification.type === 'error' ? <AlertCircle size={16} /> : <CheckCircle size={16} />}
          <span>{notification.message}</span>
          <button onClick={() => setNotification({ message: '', type: '' })} className="ml-2 hover:opacity-80">
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  );
}
