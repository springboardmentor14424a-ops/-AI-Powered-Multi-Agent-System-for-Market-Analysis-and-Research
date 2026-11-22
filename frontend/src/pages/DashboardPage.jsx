import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import StockSearch from '../components/StockSearch';
import StockChart from '../components/StockChart';
import api from '../api/axios';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  Activity,
  Star,
  Clock,
  Loader2,
  Trash2,
  Settings,
  Brain,
  ShieldAlert,
  SlidersHorizontal,
  Compass,
  FileSpreadsheet,
  CheckCircle,
  AlertCircle,
  User,
  Lock,
  Mail,
  Save,
  Layers,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const DashboardPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('research'); // 'research' | 'watchlist' | 'agents' | 'settings'

  // Stock & Analysis state
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [quote, setQuote] = useState(null);
  const [history, setHistory] = useState([]);
  const [period, setPeriod] = useState('1y');
  const [loadingQuote, setLoadingQuote] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  // Watchlist & Recent Searches
  const [watchlist, setWatchlist] = useState([]);
  const [recentSearches, setRecentSearches] = useState([]);
  const [watchlistLoading, setWatchlistLoading] = useState(false);

  // User Profile Settings state
  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    current_password: '',
    new_password: '',
  });
  const [profileStatus, setProfileStatus] = useState({ type: '', message: '' });
  const [savingProfile, setSavingProfile] = useState(false);

  useEffect(() => {
    loadWatchlist();
    loadRecentSearches();
    if (user) {
      setProfileForm((prev) => ({
        ...prev,
        full_name: user.full_name || '',
        email: user.email || '',
      }));
    }
  }, [user]);

  const loadWatchlist = async () => {
    try {
      const res = await api.get('/user/watchlist');
      setWatchlist(res.data);
    } catch (e) {
      console.error('Failed to load watchlist:', e);
    }
  };

  const loadRecentSearches = async () => {
    try {
      const res = await api.get('/user/recent-searches');
      setRecentSearches(res.data);
    } catch (e) {
      console.error('Failed to load recent searches:', e);
    }
  };

  const toggleWatchlist = async (symbol, name) => {
    const isSaved = watchlist.some((item) => item.symbol === symbol);
    setWatchlistLoading(true);
    try {
      if (isSaved) {
        await api.delete(`/user/watchlist/${symbol}`);
        setWatchlist((prev) => prev.filter((item) => item.symbol !== symbol));
      } else {
        await api.post('/user/watchlist', { symbol, name });
        await loadWatchlist();
      }
    } catch (e) {
      console.error('Watchlist action error:', e);
    } finally {
      setWatchlistLoading(false);
    }
  };

  const clearAllRecent = async () => {
    try {
      await api.delete('/user/recent-searches');
      setRecentSearches([]);
    } catch (e) {
      console.error('Failed to clear recent searches:', e);
    }
  };

  const fetchStockData = async (symbol, p = period) => {
    setSelectedSymbol(symbol);
    setLoadingQuote(true);
    setLoadingHistory(true);
    setLoadingAnalysis(true);

    api.post('/user/recent-searches', { symbol }).then(() => loadRecentSearches()).catch(() => {});

    try {
      const [quoteRes, histRes, analysisRes] = await Promise.allSettled([
        api.get(`/stocks/${symbol}/quote`),
        api.get(`/stocks/${symbol}/history?period=${p}&interval=1d`),
        api.get(`/stocks/${symbol}/analysis`),
      ]);
      setQuote(quoteRes.status === 'fulfilled' ? quoteRes.value.data : null);
      setHistory(histRes.status === 'fulfilled' ? histRes.value.data : []);
      setAiAnalysis(analysisRes.status === 'fulfilled' ? analysisRes.value.data : null);
    } catch (err) {
      console.error('Failed to fetch stock data:', err);
      setQuote(null);
      setHistory([]);
      setAiAnalysis(null);
    } finally {
      setLoadingQuote(false);
      setLoadingHistory(false);
      setLoadingAnalysis(false);
    }
  };

  const handlePeriodChange = (p) => {
    setPeriod(p);
    if (selectedSymbol) {
      setLoadingHistory(true);
      api
        .get(`/stocks/${selectedSymbol}/history?period=${p}&interval=1d`)
        .then((res) => setHistory(res.data))
        .catch(() => setHistory([]))
        .finally(() => setLoadingHistory(false));
    }
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileStatus({ type: '', message: '' });

    try {
      const payload = {
        full_name: profileForm.full_name,
        email: profileForm.email,
      };
      if (profileForm.new_password) {
        payload.current_password = profileForm.current_password;
        payload.new_password = profileForm.new_password;
      }
      const res = await api.put('/auth/profile', payload);
      setProfileStatus({ type: 'success', message: 'Profile details updated successfully!' });
      setProfileForm((prev) => ({
        ...prev,
        current_password: '',
        new_password: '',
      }));
    } catch (err) {
      setProfileStatus({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to update profile. Please try again.',
      });
    } finally {
      setSavingProfile(false);
    }
  };

  const formatNumber = (n) => {
    if (n == null) return 'N/A';
    if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
    if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
    if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
    return `$${n.toLocaleString()}`;
  };

  const formatVolume = (n) => {
    if (n == null) return 'N/A';
    if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
    if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
    if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
    return n.toLocaleString();
  };

  const price = quote?.price ?? quote?.currentPrice;
  const prevClose = quote?.previous_close ?? quote?.previousClose;
  const change = quote?.change ?? (price != null && prevClose != null ? price - prevClose : null);
  const changePercent =
    quote?.changePercent ?? (change != null && prevClose ? (change / prevClose) * 100 : null);
  const isPositive = change != null ? change >= 0 : true;
  const isCurrentInWatchlist = selectedSymbol && watchlist.some((item) => item.symbol === selectedSymbol);

  // Left Sidebar Navigation Items
  const navItems = [
    { id: 'research', label: 'Stock Research', icon: Compass, badge: 'Live' },
    { id: 'watchlist', label: 'Saved Watchlist', icon: Star, count: watchlist.length },
    { id: 'agents', label: 'AI Agent Console', icon: Brain, badge: 'Trained' },
    { id: 'settings', label: 'User Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-white bg-grid-pattern">
      <Navbar />

      <div className="pt-16 flex min-h-[calc(100vh-4rem)]">
        {/* ============================================================== */}
        {/* LEFT SIDEBAR: ADVANCED NAVIGATION & PLATFORM FEATURES           */}
        {/* ============================================================== */}
        <aside className="w-64 border-r border-white/10 bg-[#060912]/80 backdrop-blur-xl p-4 flex flex-col justify-between hidden md:flex">
          <div>
            {/* Header Badge */}
            <div className="px-3 py-2.5 mb-6 rounded-xl bg-gradient-to-r from-blue-500/10 via-cyan-500/10 to-violet-500/10 border border-cyan-500/20">
              <div className="flex items-center gap-2 text-cyan-400 font-bold text-xs uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5" /> Platform Intelligence
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Multi-Agent S&P 500 Engine</div>
            </div>

            {/* Navigation Tabs */}
            <div className="space-y-1.5">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-400/30 shadow-lg shadow-cyan-500/10'
                        : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-cyan-400/20 text-cyan-300 border border-cyan-400/30">
                        {item.badge}
                      </span>
                    )}
                    {item.count !== undefined && item.count > 0 && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-amber-400/20 text-amber-300 border border-amber-400/30">
                        {item.count}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Active AI Agent Status Widget */}
            <div className="mt-8 pt-6 border-t border-white/10">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-3 px-1">
                Active AI Agents
              </div>
              <div className="space-y-2 text-xs">
                {[
                  { name: 'Fundamental Agent', color: 'text-emerald-400', status: 'Online' },
                  { name: 'Technical Agent', color: 'text-cyan-400', status: 'Online' },
                  { name: 'Risk Agent', color: 'text-violet-400', status: 'Online' },
                  { name: 'Sentiment Agent', color: 'text-amber-400', status: 'Calibrating' },
                ].map((ag) => (
                  <div key={ag.name} className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02] border border-white/5">
                    <span className="text-slate-300 text-[11px]">{ag.name}</span>
                    <span className={`text-[10px] font-semibold flex items-center gap-1 ${ag.color}`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                      {ag.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* User mini badge at bottom */}
          <div className="pt-4 border-t border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center font-bold text-xs text-white">
                {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
              </div>
              <div className="overflow-hidden">
                <div className="text-xs font-semibold text-white truncate max-w-[120px]">{user?.full_name || 'User'}</div>
                <div className="text-[10px] text-slate-400 truncate max-w-[120px]">{user?.email || ''}</div>
              </div>
            </div>
            <button
              onClick={() => setActiveTab('settings')}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              title="User Settings"
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </aside>

        {/* ============================================================== */}
        {/* MAIN BODY VIEW AREA                                            */}
        {/* ============================================================== */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full overflow-y-auto">
          {/* Top Bar for Mobile Mode */}
          <div className="flex md:hidden items-center justify-between pb-4 mb-4 border-b border-white/10 gap-2 overflow-x-auto">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
                  activeTab === item.id ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/40' : 'text-slate-400'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* TAB 1: STOCK RESEARCH VIEW */}
          {activeTab === 'research' && (
            <div>
              <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
                <h1 className="text-2xl font-bold text-white">
                  Stock Research & Multi-Agent Analytics
                </h1>
                <p className="text-slate-400 text-sm mt-0.5">
                  Analyze fundamentals, technical patterns, and downside risk with pre-trained AI agents.
                </p>
              </motion.div>

              <div className="flex flex-col xl:flex-row gap-6">
                <div className="flex-1 min-w-0">
                  {/* Search Bar */}
                  <div className="mb-6">
                    <StockSearch onSelectStock={(sym) => fetchStockData(sym)} />
                  </div>

                  {/* Stock Quote Header */}
                  {selectedSymbol && (
                    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
                      <div className="glass-card rounded-2xl p-6">
                        {loadingQuote ? (
                          <div className="flex items-center justify-center py-8">
                            <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
                          </div>
                        ) : quote ? (
                          <>
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                              <div>
                                <div className="flex items-center gap-3">
                                  <h2 className="text-2xl font-bold text-white">{selectedSymbol}</h2>
                                  <button
                                    onClick={() => toggleWatchlist(selectedSymbol, quote.name)}
                                    disabled={watchlistLoading}
                                    className={`p-1.5 rounded-lg border transition-all ${
                                      isCurrentInWatchlist
                                        ? 'bg-amber-400/20 text-amber-300 border-amber-400/40 hover:bg-amber-400/30'
                                        : 'bg-white/5 text-slate-400 border-white/10 hover:text-white hover:bg-white/10'
                                    }`}
                                    title={isCurrentInWatchlist ? 'Remove from Watchlist' : 'Add to Watchlist'}
                                  >
                                    <Star className={`w-4 h-4 ${isCurrentInWatchlist ? 'fill-amber-400 text-amber-400' : ''}`} />
                                  </button>
                                  <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-sm font-medium ${
                                    isPositive ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                                  }`}>
                                    {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                                    {change != null ? `${change >= 0 ? '+' : ''}${change.toFixed(2)}` : ''}
                                    {changePercent != null ? ` (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)` : ''}
                                  </span>
                                </div>
                                <p className="text-slate-400 text-sm mt-1">{quote.name || quote.shortName || quote.longName || ''}</p>
                              </div>
                              <div className="text-right">
                                <p className="text-3xl font-bold text-white">
                                  ${price != null ? price.toFixed(2) : 'N/A'}
                                </p>
                              </div>
                            </div>

                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                              <div className="p-3 bg-white/[0.04] border border-white/5 rounded-xl">
                                <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                                  <DollarSign className="w-3.5 h-3.5 text-cyan-400" /> Market Cap
                                </div>
                                <p className="text-white font-semibold">{formatNumber(quote.market_cap ?? quote.marketCap)}</p>
                              </div>
                              <div className="p-3 bg-white/[0.04] border border-white/5 rounded-xl">
                                <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                                  <Activity className="w-3.5 h-3.5 text-blue-400" /> Volume
                                </div>
                                <p className="text-white font-semibold">{formatVolume(quote.volume)}</p>
                              </div>
                              <div className="p-3 bg-white/[0.04] border border-white/5 rounded-xl">
                                <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Day High
                                </div>
                                <p className="text-white font-semibold">
                                  {(quote.day_high ?? quote.dayHigh) != null ? `$${(quote.day_high ?? quote.dayHigh).toFixed(2)}` : 'N/A'}
                                </p>
                              </div>
                              <div className="p-3 bg-white/[0.04] border border-white/5 rounded-xl">
                                <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                                  <TrendingDown className="w-3.5 h-3.5 text-rose-400" /> Day Low
                                </div>
                                <p className="text-white font-semibold">
                                  {(quote.day_low ?? quote.dayLow) != null ? `$${(quote.day_low ?? quote.dayLow).toFixed(2)}` : 'N/A'}
                                </p>
                              </div>
                            </div>
                          </>
                        ) : (
                          <p className="text-slate-400 text-center py-4">Failed to load quote data</p>
                        )}
                      </div>
                    </motion.div>
                  )}

                  {/* Chart */}
                  {selectedSymbol && (
                    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mb-6">
                      <div className="glass-card rounded-2xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">Price History</h3>
                        {loadingHistory ? (
                          <div className="flex items-center justify-center py-20">
                            <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
                          </div>
                        ) : (
                          <StockChart
                            data={history}
                            selectedPeriod={period}
                            onPeriodChange={handlePeriodChange}
                            symbol={selectedSymbol}
                          />
                        )}
                      </div>
                    </motion.div>
                  )}

                  {/* AI Multi-Agent Intelligence Section */}
                  {selectedSymbol && (
                    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="mb-6">
                      <div className="glass-card rounded-2xl p-6 border border-cyan-500/20">
                        <div className="flex flex-wrap items-center justify-between gap-3 mb-6 pb-4 border-b border-white/10">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
                              <h3 className="text-lg font-bold text-white">AI Agent Intelligence (Model Predictions)</h3>
                            </div>
                            <p className="text-xs text-slate-400 mt-0.5">
                              Trained on 850k+ price bars and 1,780+ fundamental filings across S&P 500 companies
                            </p>
                          </div>
                          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                            v1.0.0 S&P 500 ML Models
                          </span>
                        </div>

                        {loadingAnalysis ? (
                          <div className="flex items-center justify-center py-12">
                            <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
                          </div>
                        ) : aiAnalysis ? (
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {/* Fundamental Agent Card */}
                            <div className="p-4 bg-white/[0.03] border border-white/10 rounded-xl">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Fundamental Agent</span>
                                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                                  {aiAnalysis.fundamental_analysis?.financial_health_rating}
                                </span>
                              </div>
                              <div className="mt-2 space-y-1.5">
                                <div className="text-2xl font-bold text-white">
                                  ${aiAnalysis.fundamental_analysis?.predicted_forward_eps}
                                </div>
                                <p className="text-xs text-slate-400">Predicted Forward EPS</p>
                                <div className="text-xs text-slate-500 pt-2 border-t border-white/5">
                                  Model Confidence: <span className="text-slate-300">{(aiAnalysis.fundamental_analysis?.confidence * 100).toFixed(0)}%</span>
                                </div>
                              </div>
                            </div>

                            {/* Technical Agent Card */}
                            <div className="p-4 bg-white/[0.03] border border-white/10 rounded-xl">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Technical Agent</span>
                                <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                                  aiAnalysis.technical_analysis?.direction_up
                                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                                    : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                                }`}>
                                  {aiAnalysis.technical_analysis?.signal}
                                </span>
                              </div>
                              <div className="mt-2 space-y-1.5">
                                <div className="text-2xl font-bold text-white">
                                  {aiAnalysis.technical_analysis?.expected_forward_5d_return >= 0 ? '+' : ''}
                                  {aiAnalysis.technical_analysis?.expected_forward_5d_return}%
                                </div>
                                <p className="text-xs text-slate-400">Expected 5-Day Trajectory</p>
                                <div className="text-xs text-slate-500 pt-2 border-t border-white/5">
                                  Status: <span className="text-slate-300">{aiAnalysis.technical_analysis?.technical_indicators?.trend_status}</span>
                                </div>
                              </div>
                            </div>

                            {/* Risk Agent Card */}
                            <div className="p-4 bg-white/[0.03] border border-white/10 rounded-xl">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Risk Agent</span>
                                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-violet-500/15 text-violet-300 border border-violet-500/30">
                                  {aiAnalysis.risk_assessment?.risk_level}
                                </span>
                              </div>
                              <div className="mt-2 space-y-1.5">
                                <div className="text-2xl font-bold text-white">
                                  {aiAnalysis.risk_assessment?.annualized_volatility_pct}%
                                </div>
                                <p className="text-xs text-slate-400">Annualized Volatility</p>
                                <div className="text-xs text-slate-500 pt-2 border-t border-white/5">
                                  95% Daily VaR: <span className="text-rose-400">{aiAnalysis.risk_assessment?.daily_value_at_risk_95_pct}%</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <p className="text-slate-500 text-sm">Model inference not available for this ticker</p>
                        )}
                      </div>
                    </motion.div>
                  )}

                  {/* Empty state */}
                  {!selectedSymbol && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card rounded-2xl p-12 text-center">
                      <BarChart3 className="w-12 h-12 text-cyan-400/60 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-slate-200 mb-2">Search for a Stock</h3>
                      <p className="text-sm text-slate-400 max-w-sm mx-auto mb-6">
                        Search by ticker or select one of the actively tracked S&P 500 benchmarks below:
                      </p>
                      <div className="flex flex-wrap items-center justify-center gap-2">
                        {['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'TSLA', 'JPM'].map((ticker) => (
                          <button
                            key={ticker}
                            onClick={() => fetchStockData(ticker)}
                            className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-white/[0.06] border border-white/10 text-cyan-300 hover:bg-cyan-500/20 hover:border-cyan-400/40 transition-all"
                          >
                            {ticker}
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </div>

                {/* Right Mini Side Column: Quick Watchlist & Recent */}
                <div className="w-full xl:w-72 flex-shrink-0 space-y-6">
                  {/* Watchlist card */}
                  <div className="glass-card rounded-2xl p-5">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                        <h4 className="text-sm font-semibold text-white">Watchlist</h4>
                      </div>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-slate-300">
                        {watchlist.length}
                      </span>
                    </div>

                    {watchlist.length === 0 ? (
                      <p className="text-xs text-slate-500 text-center py-4">No stocks added yet. Star any stock to track it.</p>
                    ) : (
                      <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                        {watchlist.map((item) => (
                          <div
                            key={item.symbol}
                            onClick={() => fetchStockData(item.symbol)}
                            className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.06] cursor-pointer transition-colors"
                          >
                            <div>
                              <div className="font-semibold text-xs text-white">{item.symbol}</div>
                              <div className="text-[10px] text-slate-400 truncate max-w-[100px]">{item.name}</div>
                            </div>
                            <div className="text-right">
                              {item.price != null && <div className="text-xs font-medium text-white">${item.price.toFixed(2)}</div>}
                              {item.changePercent != null && (
                                <div className={`text-[10px] ${item.changePercent >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                  {item.changePercent >= 0 ? '+' : ''}{item.changePercent}%
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Recent Searches card */}
                  <div className="glass-card rounded-2xl p-5">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-cyan-400" />
                        <h4 className="text-sm font-semibold text-white">Recent Searches</h4>
                      </div>
                      {recentSearches.length > 0 && (
                        <button onClick={clearAllRecent} className="text-[10px] text-slate-500 hover:text-slate-300">
                          Clear
                        </button>
                      )}
                    </div>
                    {recentSearches.length === 0 ? (
                      <p className="text-xs text-slate-500 text-center py-4">No recent searches</p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {recentSearches.map((item) => (
                          <button
                            key={item.symbol}
                            onClick={() => fetchStockData(item.symbol)}
                            className="px-2.5 py-1 rounded bg-white/[0.04] hover:bg-white/[0.08] text-xs text-slate-300 border border-white/5 transition-colors"
                          >
                            {item.symbol}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: WATCHLIST DETAILED VIEW */}
          {activeTab === 'watchlist' && (
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              <div>
                <h1 className="text-2xl font-bold text-white">Your Stock Watchlist</h1>
                <p className="text-slate-400 text-sm mt-0.5">
                  Track and monitor your selected equities with live performance indicators.
                </p>
              </div>

              {watchlist.length === 0 ? (
                <div className="glass-card rounded-2xl p-12 text-center">
                  <Star className="w-12 h-12 text-amber-400/40 mx-auto mb-3" />
                  <h3 className="text-lg font-semibold text-white mb-2">Watchlist is currently empty</h3>
                  <p className="text-sm text-slate-400 max-w-sm mx-auto mb-4">
                    Go to the Stock Research tab and click the star icon on any company to save it here.
                  </p>
                  <button
                    onClick={() => setActiveTab('research')}
                    className="btn-gradient px-4 py-2 rounded-xl text-xs font-semibold"
                  >
                    Explore Stocks
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {watchlist.map((item) => (
                    <div
                      key={item.symbol}
                      className="glass-card rounded-2xl p-5 hover:border-cyan-400/30 transition-all cursor-pointer group"
                      onClick={() => {
                        setActiveTab('research');
                        fetchStockData(item.symbol);
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="text-lg font-bold text-white group-hover:text-cyan-400 transition-colors">
                            {item.symbol}
                          </div>
                          <div className="text-xs text-slate-400 truncate max-w-[180px]">{item.name || 'Stock'}</div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleWatchlist(item.symbol);
                          }}
                          className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-white/5 transition-colors"
                          title="Remove from Watchlist"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="mt-4 pt-4 border-t border-white/5 flex items-end justify-between">
                        <div>
                          <div className="text-xs text-slate-500">Market Price</div>
                          <div className="text-xl font-bold text-white">
                            ${item.price != null ? item.price.toFixed(2) : 'N/A'}
                          </div>
                        </div>
                        {item.changePercent != null && (
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                            item.changePercent >= 0 ? 'bg-emerald-500/15 text-emerald-300' : 'bg-rose-500/15 text-rose-300'
                          }`}>
                            {item.changePercent >= 0 ? '+' : ''}{item.changePercent}%
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* TAB 3: AI AGENTS CONSOLE & ARCHITECTURE */}
          {activeTab === 'agents' && (
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              <div>
                <h1 className="text-2xl font-bold text-white">Multi-Agent AI Architecture</h1>
                <p className="text-slate-400 text-sm mt-0.5">
                  Detailed inspection of specialized agents and trained models deployed for market research.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[
                  {
                    title: 'Fundamental Analysis Agent',
                    icon: FileSpreadsheet,
                    status: 'Live & Operational',
                    tagColor: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
                    desc: 'Evaluates balance sheets, operating margins, debt-to-equity ratios, and projects forward EPS earnings.',
                    models: ['Random Forest Regressor (EPS Projection)', 'Gradient Boosting Health Classifier (99.4% Accuracy)'],
                    features: ['Gross/Operating Margins', 'Current/Quick/Cash Ratios', 'ROE', 'Debt Coverage', 'Revenue'],
                  },
                  {
                    title: 'Technical Analysis Agent',
                    icon: SlidersHorizontal,
                    status: 'Live & Operational',
                    tagColor: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
                    desc: 'Discovers trend patterns, multi-horizon moving average crossovers, and classifies forward 5-day trajectory.',
                    models: ['Random Forest Direction Classifier', 'Gradient Boosting Return Regressor'],
                    features: ['5/10/20/50 SMAs', 'RSI-14', 'MACD & Signal', '20-Day Rolling Volatility', 'Volume Ratio'],
                  },
                  {
                    title: 'Risk Analysis Agent',
                    icon: ShieldAlert,
                    status: 'Live & Operational',
                    tagColor: 'bg-violet-500/15 text-violet-300 border-violet-500/30',
                    desc: 'Calculates portfolio Value-at-Risk (95% VaR), annualized volatility, historical drawdowns, and assigns risk tiers.',
                    models: ['Risk Tier Classifier', 'Volatility Estimator', '501-Ticker S&P Profiles'],
                    features: ['Annualized Volatility', '95% Daily VaR', 'Max Drawdown', 'Debt-to-Assets'],
                  },
                  {
                    title: 'LangGraph Supervisor Agent',
                    icon: Layers,
                    status: 'Upcoming Milestone',
                    tagColor: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
                    desc: 'Orchestrates the multi-agent graph, resolves conflicting signals between fundamentals and technicals, and formats the research memo.',
                    models: ['LangGraph StateGraph Engine', 'Multi-Agent Consensus Layer'],
                    features: ['Dynamic Tool Routing', 'Multi-perspective Memo Synthesis', 'Risk-Adjusted Conviction Score'],
                  },
                ].map((ag) => {
                  const Icon = ag.icon;
                  return (
                    <div key={ag.title} className="glass-card rounded-2xl p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2.5 rounded-xl bg-white/[0.05] border border-white/10 text-cyan-400">
                            <Icon className="w-5 h-5" />
                          </div>
                          <h3 className="font-bold text-white text-base">{ag.title}</h3>
                        </div>
                        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${ag.tagColor}`}>
                          {ag.status}
                        </span>
                      </div>
                      <p className="text-slate-300 text-xs leading-relaxed mb-4">{ag.desc}</p>
                      
                      <div className="space-y-3 pt-3 border-t border-white/5 text-xs">
                        <div>
                          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Models & Engines</div>
                          <div className="space-y-1">
                            {ag.models.map((m) => (
                              <div key={m} className="text-slate-300 flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                                {m}
                              </div>
                            ))}
                          </div>
                        </div>

                        <div>
                          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Key Signals & Metrics</div>
                          <div className="flex flex-wrap gap-1.5">
                            {ag.features.map((f) => (
                              <span key={f} className="px-2 py-0.5 rounded bg-white/[0.04] text-[10px] text-slate-400 border border-white/5">
                                {f}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          )}

          {/* TAB 4: USER SETTINGS & PROFILE DETAILS */}
          {activeTab === 'settings' && (
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl mx-auto space-y-6">
              <div>
                <h1 className="text-2xl font-bold text-white">User Settings & Profile</h1>
                <p className="text-slate-400 text-sm mt-0.5">
                  Manage your personal account credentials, security, and profile details stored in PostgreSQL.
                </p>
              </div>

              {profileStatus.message && (
                <div
                  className={`p-4 rounded-xl flex items-center gap-3 border ${
                    profileStatus.type === 'success'
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                      : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                  }`}
                >
                  {profileStatus.type === 'success' ? (
                    <CheckCircle className="w-5 h-5 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  )}
                  <span className="text-sm">{profileStatus.message}</span>
                </div>
              )}

              <form onSubmit={handleProfileSubmit} className="glass-card rounded-2xl p-6 sm:p-8 space-y-6">
                <div className="flex items-center gap-4 pb-6 border-b border-white/10">
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-xl font-bold text-white shadow-lg shadow-cyan-500/20">
                    {profileForm.full_name ? profileForm.full_name[0].toUpperCase() : 'U'}
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-base">{user?.full_name || 'StockMind User'}</h3>
                    <p className="text-xs text-slate-400">Authenticated Investor Account</p>
                  </div>
                </div>

                <div className="space-y-4">
                  {/* Full Name */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                      Full Name
                    </label>
                    <div className="relative">
                      <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                      <input
                        type="text"
                        value={profileForm.full_name}
                        onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                        required
                        className="input-fintech pl-10"
                        placeholder="John Doe"
                      />
                    </div>
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                      <input
                        type="email"
                        value={profileForm.email}
                        onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                        required
                        className="input-fintech pl-10"
                        placeholder="john@example.com"
                      />
                    </div>
                  </div>

                  {/* Password section */}
                  <div className="pt-4 border-t border-white/5 space-y-4">
                    <h4 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">
                      Security & Password Change (Optional)
                    </h4>

                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1.5">
                        Current Password
                      </label>
                      <div className="relative">
                        <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                        <input
                          type="password"
                          value={profileForm.current_password}
                          onChange={(e) => setProfileForm({ ...profileForm, current_password: e.target.value })}
                          className="input-fintech pl-10"
                          placeholder="••••••••"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1.5">
                        New Password
                      </label>
                      <div className="relative">
                        <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                        <input
                          type="password"
                          value={profileForm.new_password}
                          onChange={(e) => setProfileForm({ ...profileForm, new_password: e.target.value })}
                          className="input-fintech pl-10"
                          placeholder="Min. 6 characters"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 flex justify-end">
                  <button
                    type="submit"
                    disabled={savingProfile}
                    className="btn-gradient px-6 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2"
                  >
                    {savingProfile ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Saving Changes...</span>
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" />
                        <span>Save Profile Settings</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          )}
        </main>
      </div>
    </div>
  );
};

export default DashboardPage;
