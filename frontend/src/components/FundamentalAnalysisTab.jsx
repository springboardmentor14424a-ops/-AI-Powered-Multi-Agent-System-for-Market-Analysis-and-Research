import React, { useState, useEffect, useRef, useMemo } from 'react';
import api from '../api/client';
import {
  Brain, Search, Building2, TrendingUp, TrendingDown, DollarSign,
  Activity, ShieldCheck, AlertTriangle, AlertCircle, CheckCircle,
  FileText, BarChart2, Layers, Award, Clock, Trash2, ChevronRight,
  Download, Printer, Bookmark, RefreshCw, X, ArrowUpRight, ArrowDownRight,
  Sparkles, Check, Info, PieChart
} from 'lucide-react';

const EXCHANGES = [
  { id: 'NSE', name: 'NSE', full: 'National Stock Exchange of India', country: 'India', flag: '🇮🇳' },
  { id: 'BSE', name: 'BSE', full: 'Bombay Stock Exchange', country: 'India', flag: '🇮🇳' },
  { id: 'NASDAQ', name: 'NASDAQ', full: 'NASDAQ Stock Market', country: 'United States', flag: '🇺🇸' },
  { id: 'NYSE', name: 'NYSE', full: 'New York Stock Exchange', country: 'United States', flag: '🇺🇸' },
];

export default function FundamentalAnalysisTab({ onAddToWatchlist, watchlist = [] }) {
  // Search & Exchange Selection State
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

  // Analysis State
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState('');

  // History State
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // View Sub-Tab: 'overview' | 'profitability' | 'debt' | 'valuation' | 'historical' | 'peers' | 'audit'
  const [activeSubTab, setActiveSubTab] = useState('overview');

  // Toast State
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

  // Fetch search suggestions
  useEffect(() => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

    debounceTimerRef.current = setTimeout(async () => {
      try {
        setLoadingSuggestions(true);
        const res = await api.get(`/market-data/search?market=${selectedExchange}&q=${encodeURIComponent(searchQuery)}`);
        setSuggestions(res.data || []);
      } catch (err) {
        console.error('Failed to search companies:', err);
      } finally {
        setLoadingSuggestions(false);
      }
    }, 200);

    return () => clearTimeout(debounceTimerRef.current);
  }, [searchQuery, selectedExchange]);

  // Load Past Analyses
  const loadHistory = async () => {
    try {
      setLoadingHistory(true);
      const res = await api.get('/fundamental/history');
      setHistory(res.data || []);
    } catch (err) {
      console.error('Failed to load fundamental history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  // Exchange Switcher
  const handleSelectExchange = (exch) => {
    setSelectedExchange(exch);
    setSearchQuery('');
    setShowSuggestions(false);
    const defaults = {
      NSE: { ticker: 'INFY', name: 'Infosys Limited', market: 'NSE', country: 'India' },
      BSE: { ticker: 'TCS', name: 'Tata Consultancy Services Ltd', market: 'BSE', country: 'India' },
      NASDAQ: { ticker: 'AAPL', name: 'Apple Inc.', market: 'NASDAQ', country: 'United States' },
      NYSE: { ticker: 'JPM', name: 'JPMorgan Chase & Co.', market: 'NYSE', country: 'United States' }
    };
    setSelectedCompany(defaults[exch] || { ticker: 'AAPL', name: 'Apple Inc.', market: exch, country: 'United States' });
  };

  // Run Fundamental Analysis
  const handleRunAnalysis = async () => {
    if (!selectedCompany?.ticker) {
      setAnalysisError('Please select a company ticker first.');
      return;
    }

    setAnalyzing(true);
    setAnalysisError('');
    try {
      const payload = {
        ticker: selectedCompany.ticker,
        market: selectedExchange,
        company_name: selectedCompany.name
      };

      const res = await api.post('/fundamental/analyze', payload);
      setAnalysisResult(res.data);
      setActiveSubTab('overview');
      showToast(`Fundamental Analysis completed for ${selectedCompany.ticker}!`, 'success');
      loadHistory();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to complete fundamental analysis.';
      setAnalysisError(msg);
      showToast(msg, 'error');
    } finally {
      setAnalyzing(false);
    }
  };

  // Reload saved analysis
  const handleLoadSavedAnalysis = async (analysisId) => {
    try {
      setAnalyzing(true);
      const res = await api.get(`/fundamental/${analysisId}`);
      setAnalysisResult(res.data);
      setSelectedExchange(res.data.market);
      setSelectedCompany({
        ticker: res.data.ticker,
        name: res.data.company_name,
        market: res.data.market,
        country: res.data.country || 'Global'
      });
      setActiveSubTab('overview');
      showToast(`Loaded saved fundamental analysis for ${res.data.ticker}!`, 'success');
    } catch (err) {
      showToast('Failed to load saved analysis.', 'error');
    } finally {
      setAnalyzing(false);
    }
  };

  // Delete saved analysis
  const handleDeleteSaved = async (analysisId, e) => {
    e.stopPropagation();
    try {
      await api.delete(`/fundamental/${analysisId}`);
      setHistory(prev => prev.filter(h => h.analysis_id !== analysisId));
      if (analysisResult?.analysis_id === analysisId) {
        setAnalysisResult(null);
      }
      showToast('Saved analysis removed from database.', 'success');
    } catch (err) {
      showToast('Failed to delete analysis.', 'error');
    }
  };

  const currencySym = (analysisResult?.currency === 'INR' || selectedExchange === 'NSE' || selectedExchange === 'BSE') ? '₹' : '$';

  // SVG Multi-Year Chart Geometry
  const multiYearChartGeometry = useMemo(() => {
    const years = analysisResult?.historical_trends || [];
    if (!years || years.length < 2) return null;

    // Years are ordered [latest, ..., oldest]. Reverse to plot chronologically left-to-right
    const chrono = [...years].reverse();
    const width = 640;
    const height = 220;
    const padX = 40;
    const padTop = 25;
    const padBottom = 35;
    const usableW = width - padX * 2;
    const usableH = height - padTop - padBottom;

    const revenues = chrono.map(y => y.revenue || 0);
    const maxRev = Math.max(...revenues, 1);

    const stepW = usableW / chrono.length;

    const bars = chrono.map((y, i) => {
      const x = padX + i * stepW + stepW * 0.15;
      const barW = stepW * 0.7;
      const revH = ((y.revenue || 0) / maxRev) * usableH;
      const incH = Math.max(0, ((y.net_income || 0) / maxRev) * usableH);
      const revY = height - padBottom - revH;
      const incY = height - padBottom - incH;
      return {
        year: y.year,
        x,
        barW,
        revH,
        revY,
        incH,
        incY,
        revenue: y.revenue,
        net_income: y.net_income,
        net_margin_pct: y.net_margin_pct
      };
    });

    return { width, height, padX, padTop, padBottom, maxRev, bars, chrono };
  }, [analysisResult]);

  return (
    <div className="space-y-6">
      {/* 1. Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-400 mb-1">
            <Brain size={15} /> Agent 3: Fundamental Analysis Agent
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            AI-Powered Corporate Financial & Valuation Intelligence
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Evaluates financial performance, profitability margins, debt stability, valuation multiples, historical growth trends, and peer benchmarks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-indigo-950 text-indigo-300 border border-indigo-800 rounded-lg text-xs font-semibold flex items-center gap-1.5">
            <Award size={14} className="text-indigo-400" />
            Zero-Fabrication Data Engine
          </span>
          <span className="px-3 py-1 bg-slate-800 text-slate-300 border border-slate-700 rounded-lg text-xs font-mono">
            NSE • BSE • NASDAQ • NYSE
          </span>
        </div>
      </div>

      {/* 2. Control Panel: Exchange & Search Autocomplete */}
      <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-lg space-y-4">
        {/* Exchange Selector */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <Building2 size={14} className="text-indigo-400" /> Select Stock Market / Exchange:
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {EXCHANGES.map(exch => (
              <button
                key={exch.id}
                type="button"
                onClick={() => handleSelectExchange(exch.id)}
                className={`p-3 rounded-xl border text-left flex flex-col justify-between transition ${
                  selectedExchange === exch.id
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md ring-1 ring-indigo-500/50'
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

        {/* Company Search with Autocomplete */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          <div className="md:col-span-8 relative" ref={autocompleteRef}>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-1.5 flex items-center gap-1.5">
              <Search size={13} className="text-indigo-400" /> Search Company for Fundamental Analysis:
            </label>
            <div className="relative">
              <input
                type="text"
                value={searchQuery || (selectedCompany?.ticker ? `${selectedCompany.name} (${selectedCompany.ticker})` : '')}
                onChange={e => {
                  setSearchQuery(e.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                placeholder={`Search ${selectedExchange} (e.g. ${selectedExchange === 'NSE' ? 'INFY, TCS, RELIANCE' : 'AAPL, MSFT, NVDA'})...`}
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
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
                      className="w-full px-4 py-2.5 text-left hover:bg-indigo-950/40 flex items-center justify-between text-xs transition"
                    >
                      <div className="flex flex-col">
                        <span className="font-bold text-white">{c.name}</span>
                        <span className="text-[11px] text-slate-400 font-mono">{c.ticker}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-[10px]">
                        <span className="px-2 py-0.5 bg-slate-800 text-indigo-300 rounded border border-slate-700 font-semibold font-mono">
                          {c.market}
                        </span>
                        <span className="text-slate-400 font-medium">{c.country}</span>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="p-4 text-center text-xs text-slate-400">
                    No results found matching "{searchQuery}" on {selectedExchange}.
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="md:col-span-4">
            <button
              type="button"
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 shadow-lg transition disabled:opacity-50"
            >
              {analyzing ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  <span>Evaluating Financials...</span>
                </>
              ) : (
                <>
                  <Brain size={14} />
                  <span>Run Fundamental Analysis</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {analysisError && (
        <div className="p-4 bg-rose-950/60 border border-rose-800 rounded-xl text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle size={16} className="shrink-0 text-rose-400" />
          <span>{analysisError}</span>
        </div>
      )}

      {/* 3. Analysis Results View */}
      {analysisResult && (
        <div className="space-y-4">
          {/* Company Overview & Health Scorecard Banner */}
          <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-xl flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold text-white">
                  {analysisResult.company_name} ({analysisResult.ticker})
                </h3>
                <span className="px-2 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-800 rounded font-mono text-[11px] font-bold">
                  {analysisResult.market}
                </span>
                <span className="px-2 py-0.5 bg-slate-800 text-slate-300 border border-slate-700 rounded text-[11px]">
                  {analysisResult.reporting_period}
                </span>
              </div>
              <div className="text-xs text-slate-400 flex flex-wrap items-center gap-2 mt-1">
                <span>Sector: <strong className="text-slate-200">{analysisResult.sector}</strong></span>
                <span>•</span>
                <span>Industry: <strong className="text-slate-200">{analysisResult.industry}</strong></span>
                <span>•</span>
                <span>Data Source: <strong className="text-slate-200">{analysisResult.data_source}</strong></span>
              </div>
            </div>

            {/* Health Score Badge Card */}
            <div className="flex items-center gap-3 bg-slate-950/80 p-3 rounded-xl border border-slate-800">
              <div className="text-center">
                <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Health Score</span>
                <div className="text-2xl font-black text-indigo-400 font-mono">
                  {analysisResult.health_score?.score}
                  <span className="text-xs font-normal text-slate-500">/100</span>
                </div>
              </div>
              <div className="border-l border-slate-800 pl-3">
                <span className={`inline-block px-2.5 py-0.5 rounded text-xs font-bold border ${
                  analysisResult.health_score?.grade === 'A'
                    ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                    : analysisResult.health_score?.grade === 'B'
                    ? 'bg-blue-950 text-blue-300 border-blue-800'
                    : 'bg-amber-950 text-amber-300 border-amber-800'
                }`}>
                  Grade {analysisResult.health_score?.grade} • {analysisResult.health_score?.verdict}
                </span>
                <span className="text-[10px] text-slate-400 block mt-0.5">
                  Financial Risk Level: <strong className="text-white">{analysisResult.health_score?.risk_level}</strong>
                </span>
              </div>
            </div>
          </div>

          {/* Sub-Tabs Navigation */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
            <div className="flex flex-wrap items-center gap-1.5">
              {[
                { id: 'overview', label: 'Executive Synthesis', icon: Sparkles },
                { id: 'revenue', label: 'Revenue & Earnings', icon: TrendingUp },
                { id: 'profitability', label: 'Profitability Margins', icon: Award },
                { id: 'debt', label: 'Debt & Solvency', icon: ShieldCheck },
                { id: 'valuation', label: 'Valuation Metrics', icon: DollarSign },
                { id: 'historical', label: 'Historical Trends', icon: BarChart2 },
                { id: 'peers', label: 'Peer Benchmarking', icon: Layers },
                { id: 'audit', label: 'Data Quality Audit', icon: Info },
              ].map(tab => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveSubTab(tab.id)}
                    className={`px-3 py-1.5 text-xs font-bold rounded-lg flex items-center gap-1.5 transition ${
                      activeSubTab === tab.id
                        ? 'bg-indigo-600 text-white shadow'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800'
                    }`}
                  >
                    <Icon size={13} />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            <div className="flex items-center gap-2">
              {onAddToWatchlist && (
                <button
                  type="button"
                  onClick={() => onAddToWatchlist({
                    ticker: analysisResult.ticker,
                    name: analysisResult.company_name,
                    market: analysisResult.market
                  })}
                  disabled={watchlist.some(w => w.ticker === analysisResult.ticker)}
                  className={`px-2.5 py-1 text-xs rounded-lg font-semibold flex items-center gap-1.5 transition ${
                    watchlist.some(w => w.ticker === analysisResult.ticker)
                      ? 'bg-slate-800 text-slate-400 border border-slate-700 cursor-not-allowed'
                      : 'bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-800'
                  }`}
                >
                  <Bookmark size={12} className={watchlist.some(w => w.ticker === analysisResult.ticker) ? 'fill-slate-400' : ''} />
                  <span>{watchlist.some(w => w.ticker === analysisResult.ticker) ? 'In Watchlist' : '+ Watchlist'}</span>
                </button>
              )}
              <button
                type="button"
                onClick={() => window.print()}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 flex items-center gap-1.5 transition"
              >
                <Printer size={12} />
                <span>Print Dossier</span>
              </button>
            </div>
          </div>

          {/* TAB 1: EXECUTIVE SYNTHESIS */}
          {activeSubTab === 'overview' && (
            <div className="space-y-4">
              {/* Highlight KPI 4-Card Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">YoY Revenue Growth</span>
                  <div className="flex items-baseline gap-1.5 my-1">
                    <span className={`text-xl font-black ${
                      (analysisResult.revenue_earnings_analysis?.revenue_growth_yoy ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {analysisResult.revenue_earnings_analysis?.revenue_growth_yoy !== null
                        ? `${analysisResult.revenue_earnings_analysis.revenue_growth_yoy > 0 ? '+' : ''}${analysisResult.revenue_earnings_analysis.revenue_growth_yoy}%`
                        : 'N/A'}
                    </span>
                    {(analysisResult.revenue_earnings_analysis?.revenue_growth_yoy ?? 0) >= 0 ? (
                      <ArrowUpRight size={16} className="text-emerald-400" />
                    ) : (
                      <ArrowDownRight size={16} className="text-rose-400" />
                    )}
                  </div>
                  <span className="text-[10px] text-slate-500">{analysisResult.revenue_earnings_analysis?.trend_verdict}</span>
                </div>

                <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">Return on Equity (ROE)</span>
                  <div className="my-1">
                    <span className="text-xl font-black text-indigo-400">
                      {analysisResult.profitability_analysis?.roe_pct !== null
                        ? `${analysisResult.profitability_analysis.roe_pct}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500">Capital Efficiency</span>
                </div>

                <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">Debt-to-Equity</span>
                  <div className="my-1">
                    <span className="text-xl font-black text-white">
                      {analysisResult.debt_stability_analysis?.debt_to_equity !== null
                        ? `${analysisResult.debt_stability_analysis.debt_to_equity}x`
                        : 'N/A'}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500">{analysisResult.debt_stability_analysis?.solvency_grade}</span>
                </div>

                <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">Trailing P/E Ratio</span>
                  <div className="my-1">
                    <span className="text-xl font-black text-white">
                      {analysisResult.valuation_analysis?.pe_ratio !== null
                        ? `${analysisResult.valuation_analysis.pe_ratio}x`
                        : 'N/A'}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500">{analysisResult.valuation_analysis?.valuation_verdict}</span>
                </div>
              </div>

              {/* AI-Generated Executive Summary Narrative */}
              <div className="p-5 bg-slate-950/80 border border-slate-800 rounded-2xl space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider pb-2 border-b border-slate-800">
                  <Sparkles size={15} className="text-indigo-400" />
                  Executive Fundamental Analysis Synthesis
                </div>
                <div className="text-xs text-slate-300 font-sans whitespace-pre-wrap leading-relaxed space-y-3">
                  {analysisResult.executive_summary}
                </div>
              </div>

              {/* Key Financial Risks & Observations */}
              <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-2xl space-y-2">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck size={14} className="text-emerald-400" /> Balance Sheet Observations & Potential Risks
                </span>
                <ul className="text-xs text-slate-300 list-disc list-inside space-y-1.5 pl-1">
                  {analysisResult.debt_stability_analysis?.financial_risks?.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* TAB 2: REVENUE AND EARNINGS ANALYSIS */}
          {activeSubTab === 'revenue' && (
            <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <TrendingUp size={14} className="text-indigo-400" /> Top-Line Revenue & Net Income Trajectory
                </h4>
                <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                  Trend: {analysisResult.revenue_earnings_analysis?.trend_verdict}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2">
                  <span className="text-xs text-slate-400 font-medium">Latest Annual Total Revenue</span>
                  <div className="text-2xl font-black text-white font-mono">
                    {analysisResult.revenue_earnings_analysis?.latest_revenue_formatted}
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-slate-400">Year-over-Year Growth:</span>
                    <span className={`font-bold font-mono ${
                      (analysisResult.revenue_earnings_analysis?.revenue_growth_yoy ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {analysisResult.revenue_earnings_analysis?.revenue_growth_yoy !== null
                        ? `${analysisResult.revenue_earnings_analysis.revenue_growth_yoy > 0 ? '+' : ''}${analysisResult.revenue_earnings_analysis.revenue_growth_yoy}%`
                        : 'N/A'}
                    </span>
                  </div>
                </div>

                <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2">
                  <span className="text-xs text-slate-400 font-medium">Latest Annual Net Income (Earnings)</span>
                  <div className="text-2xl font-black text-white font-mono">
                    {analysisResult.revenue_earnings_analysis?.latest_net_income_formatted}
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-slate-400">Year-over-Year Growth:</span>
                    <span className={`font-bold font-mono ${
                      (analysisResult.revenue_earnings_analysis?.earnings_growth_yoy ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {analysisResult.revenue_earnings_analysis?.earnings_growth_yoy !== null
                        ? `${analysisResult.revenue_earnings_analysis.earnings_growth_yoy > 0 ? '+' : ''}${analysisResult.revenue_earnings_analysis.earnings_growth_yoy}%`
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl text-xs text-slate-300 leading-relaxed">
                <strong>Analyst Finding:</strong> {analysisResult.revenue_earnings_analysis?.explanation}
              </div>
            </div>
          )}

          {/* TAB 3: PROFITABILITY ANALYSIS */}
          {activeSubTab === 'profitability' && (
            <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Award size={14} className="text-indigo-400" /> Profitability & Capital Returns
                </h4>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                {[
                  { label: 'Gross Margin', val: analysisResult.profitability_analysis?.gross_margin_pct, benchmark: '40% Avg' },
                  { label: 'Operating Margin', val: analysisResult.profitability_analysis?.operating_margin_pct, benchmark: '15% Avg' },
                  { label: 'Net Profit Margin', val: analysisResult.profitability_analysis?.net_margin_pct, benchmark: '10% Avg' },
                  { label: 'Return on Equity (ROE)', val: analysisResult.profitability_analysis?.roe_pct, benchmark: '15% Target', highlight: true },
                  { label: 'Return on Assets (ROA)', val: analysisResult.profitability_analysis?.roa_pct, benchmark: '5% Target' },
                ].map((item, idx) => (
                  <div key={idx} className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
                    <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide block">{item.label}</span>
                    <div className={`text-xl font-black ${item.highlight ? 'text-indigo-400' : 'text-white'}`}>
                      {item.val !== null && item.val !== undefined ? `${item.val}%` : 'N/A'}
                    </div>
                    {/* Visual Bar */}
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-indigo-500 h-full rounded-full"
                        style={{ width: `${Math.min(100, Math.max(0, item.val || 0))}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-slate-500 block">{item.benchmark}</span>
                  </div>
                ))}
              </div>

              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl text-xs text-slate-300 leading-relaxed">
                <strong>Profitability Thesis:</strong> {analysisResult.profitability_analysis?.evaluation}
              </div>
            </div>
          )}

          {/* TAB 4: DEBT AND FINANCIAL STABILITY */}
          {activeSubTab === 'debt' && (
            <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck size={14} className="text-emerald-400" /> Debt Levels, Liquidity & Solvency
                </h4>
                <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-slate-800 text-slate-200 border border-slate-700">
                  {analysisResult.debt_stability_analysis?.solvency_grade}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase font-medium">Debt-to-Equity</span>
                  <div className="text-xl font-black text-white">
                    {analysisResult.debt_stability_analysis?.debt_to_equity !== null
                      ? `${analysisResult.debt_stability_analysis.debt_to_equity}x`
                      : 'N/A'}
                  </div>
                  <span className="text-[10px] text-slate-500">&lt; 0.5x Conservative, &gt; 1.5x Elevated</span>
                </div>

                <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase font-medium">Current Ratio</span>
                  <div className="text-xl font-black text-white">
                    {analysisResult.debt_stability_analysis?.current_ratio !== null
                      ? `${analysisResult.debt_stability_analysis.current_ratio}x`
                      : 'N/A'}
                  </div>
                  <span className="text-[10px] text-slate-500">&gt; 1.5x Healthy Working Capital</span>
                </div>

                <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase font-medium">Total Debt</span>
                  <div className="text-base font-bold text-white font-mono">
                    {analysisResult.debt_stability_analysis?.total_debt_formatted}
                  </div>
                  <span className="text-[10px] text-slate-500">Short & Long Term</span>
                </div>

                <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase font-medium">Stockholders' Equity</span>
                  <div className="text-base font-bold text-white font-mono">
                    {analysisResult.debt_stability_analysis?.stockholders_equity_formatted}
                  </div>
                  <span className="text-[10px] text-slate-500">Net Asset Base</span>
                </div>
              </div>

              {/* Solvency Audit List */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wide">
                  Financial Solvency Observations:
                </span>
                <ul className="text-xs text-slate-300 list-disc list-inside space-y-1 pl-1">
                  {analysisResult.debt_stability_analysis?.financial_risks?.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* TAB 5: VALUATION METRICS */}
          {activeSubTab === 'valuation' && (
            <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <DollarSign size={14} className="text-indigo-400" /> Market Valuation & Multiples
                </h4>
                <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                  {analysisResult.valuation_analysis?.valuation_verdict}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase font-medium">Trailing P/E</span>
                  <div className="text-xl font-black text-white">
                    {analysisResult.valuation_analysis?.pe_ratio !== null ? `${analysisResult.valuation_analysis.pe_ratio}x` : 'N/A'}
                  </div>
                  <span className="text-[10px] text-slate-500">Price to Earnings</span>
                </div>

                <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase font-medium">Forward P/E</span>
                  <div className="text-xl font-black text-white">
                    {analysisResult.valuation_analysis?.forward_pe !== null ? `${analysisResult.valuation_analysis.forward_pe}x` : 'N/A'}
                  </div>
                  <span className="text-[10px] text-slate-500">Next 12-Month Multiple</span>
                </div>

                <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase font-medium">Price-to-Book (P/B)</span>
                  <div className="text-xl font-black text-white">
                    {analysisResult.valuation_analysis?.pb_ratio !== null ? `${analysisResult.valuation_analysis.pb_ratio}x` : 'N/A'}
                  </div>
                  <span className="text-[10px] text-slate-500">Book Value Multiple</span>
                </div>

                <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase font-medium">EV / EBITDA</span>
                  <div className="text-xl font-black text-white">
                    {analysisResult.valuation_analysis?.ev_to_ebitda !== null ? `${analysisResult.valuation_analysis.ev_to_ebitda}x` : 'N/A'}
                  </div>
                  <span className="text-[10px] text-slate-500">Enterprise Multiple</span>
                </div>
              </div>

              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl text-xs text-slate-300 leading-relaxed">
                <strong>Valuation Commentary:</strong> {analysisResult.valuation_analysis?.explanation}
              </div>
            </div>
          )}

          {/* TAB 6: HISTORICAL TRENDS & VISUAL CHART */}
          {activeSubTab === 'historical' && (
            <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <BarChart2 size={14} className="text-indigo-400" /> Multi-Year Historical Revenue & Net Income Comparison
                </h4>
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 bg-indigo-500 inline-block rounded" /> Total Revenue
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 bg-emerald-500 inline-block rounded" /> Net Income
                  </span>
                </div>
              </div>

              {/* Multi-Year SVG Chart */}
              {multiYearChartGeometry ? (
                <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
                  <svg viewBox={`0 0 ${multiYearChartGeometry.width} ${multiYearChartGeometry.height}`} className="w-full h-56 select-none">
                    {/* Baseline */}
                    <line
                      x1={multiYearChartGeometry.padX}
                      y1={multiYearChartGeometry.height - multiYearChartGeometry.padBottom}
                      x2={multiYearChartGeometry.width - multiYearChartGeometry.padX}
                      y2={multiYearChartGeometry.height - multiYearChartGeometry.padBottom}
                      stroke="#334155"
                    />

                    {/* Bars */}
                    {multiYearChartGeometry.bars.map((b, i) => (
                      <g key={i}>
                        {/* Revenue Bar */}
                        <rect
                          x={b.x}
                          y={b.revY}
                          width={b.barW * 0.48}
                          height={Math.max(1, b.revH)}
                          fill="#6366f1"
                          rx="3"
                          opacity="0.85"
                        />
                        {/* Net Income Bar */}
                        <rect
                          x={b.x + b.barW * 0.52}
                          y={b.incY}
                          width={b.barW * 0.48}
                          height={Math.max(1, b.incH)}
                          fill="#10b981"
                          rx="3"
                          opacity="0.85"
                        />
                        {/* Year Label */}
                        <text
                          x={b.x + b.barW / 2}
                          y={multiYearChartGeometry.height - 12}
                          textAnchor="middle"
                          fill="#94a3b8"
                          fontSize="11"
                          fontWeight="bold"
                        >
                          FY {b.year}
                        </text>
                        {/* Net Margin Label */}
                        {b.net_margin_pct !== null && (
                          <text
                            x={b.x + b.barW / 2}
                            y={Math.min(b.revY, b.incY) - 6}
                            textAnchor="middle"
                            fill="#a5b4fc"
                            fontSize="10"
                            fontWeight="500"
                          >
                            {b.net_margin_pct}% margin
                          </text>
                        )}
                      </g>
                    ))}
                  </svg>
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-slate-500">
                  Insufficient historical financial statement periods to plot chart.
                </div>
              )}

              {/* Historical Data Table */}
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 text-[11px] uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Fiscal Period</th>
                      <th className="py-2.5 px-3 font-semibold text-right">Total Revenue</th>
                      <th className="py-2.5 px-3 font-semibold text-right">Net Income</th>
                      <th className="py-2.5 px-3 font-semibold text-right">Operating Margin</th>
                      <th className="py-2.5 px-3 font-semibold text-right">Net Margin</th>
                      <th className="py-2.5 px-3 font-semibold text-right">YoY Revenue Growth</th>
                      <th className="py-2.5 px-3 font-semibold text-right">YoY Earnings Growth</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    {(analysisResult.historical_trends || []).map((row, i) => (
                      <tr key={i} className="hover:bg-slate-800/40 transition">
                        <td className="py-2 px-3 font-bold text-white whitespace-nowrap">FY {row.year} ({row.period_date})</td>
                        <td className="py-2 px-3 text-right">{row.revenue ? `${currencySym}${Number(row.revenue).toLocaleString()}` : '-'}</td>
                        <td className="py-2 px-3 text-right text-emerald-400">{row.net_income ? `${currencySym}${Number(row.net_income).toLocaleString()}` : '-'}</td>
                        <td className="py-2 px-3 text-right">{row.operating_margin_pct !== null ? `${row.operating_margin_pct}%` : '-'}</td>
                        <td className="py-2 px-3 text-right">{row.net_margin_pct !== null ? `${row.net_margin_pct}%` : '-'}</td>
                        <td className="py-2 px-3 text-right">
                          {row.revenue_growth_yoy !== null && row.revenue_growth_yoy !== undefined ? (
                            <span className={row.revenue_growth_yoy >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                              {row.revenue_growth_yoy >= 0 ? '+' : ''}{row.revenue_growth_yoy}%
                            </span>
                          ) : '-'}
                        </td>
                        <td className="py-2 px-3 text-right">
                          {row.earnings_growth_yoy !== null && row.earnings_growth_yoy !== undefined ? (
                            <span className={row.earnings_growth_yoy >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                              {row.earnings_growth_yoy >= 0 ? '+' : ''}{row.earnings_growth_yoy}%
                            </span>
                          ) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 7: PEER BENCHMARKING */}
          {activeSubTab === 'peers' && (
            <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Layers size={14} className="text-indigo-400" /> Industry Peer Benchmarking ({analysisResult.peer_comparison?.peer_count} Peers)
                </h4>
              </div>

              {/* Peer Table */}
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 text-[11px] uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Company / Peer</th>
                      <th className="py-2.5 px-3 font-semibold text-right">P/E Ratio</th>
                      <th className="py-2.5 px-3 font-semibold text-right">Net Margin</th>
                      <th className="py-2.5 px-3 font-semibold text-right">ROE</th>
                      <th className="py-2.5 px-3 font-semibold text-right">Debt / Equity</th>
                      <th className="py-2.5 px-3 font-semibold text-right">YoY Rev Growth</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    {(analysisResult.peer_comparison?.benchmark_table || []).map((p, i) => (
                      <tr key={i} className={`transition ${p.is_target ? 'bg-indigo-950/40 font-bold border-l-4 border-indigo-500' : 'hover:bg-slate-800/40'}`}>
                        <td className="py-2.5 px-3 whitespace-nowrap">
                          <span className="text-white block">{p.name} ({p.ticker})</span>
                          {p.is_target && <span className="text-[10px] text-indigo-400 font-normal">Target Asset</span>}
                        </td>
                        <td className="py-2.5 px-3 text-right">{p.pe_ratio !== null ? `${p.pe_ratio}x` : 'N/A'}</td>
                        <td className="py-2.5 px-3 text-right">{p.net_margin_pct !== null ? `${p.net_margin_pct}%` : 'N/A'}</td>
                        <td className="py-2.5 px-3 text-right text-indigo-300">{p.roe_pct !== null ? `${p.roe_pct}%` : 'N/A'}</td>
                        <td className="py-2.5 px-3 text-right">{p.debt_to_equity !== null ? `${p.debt_to_equity}x` : 'N/A'}</td>
                        <td className="py-2.5 px-3 text-right">{p.revenue_growth_yoy !== null ? `${p.revenue_growth_yoy}%` : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Strengths and Weaknesses */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                <div className="p-3.5 bg-emerald-950/30 border border-emerald-900/50 rounded-xl space-y-1.5">
                  <span className="text-xs font-bold text-emerald-300 uppercase tracking-wide flex items-center gap-1.5">
                    <CheckCircle size={14} /> Competitive Strengths vs Peers:
                  </span>
                  <ul className="text-xs text-emerald-200/90 list-disc list-inside space-y-1">
                    {analysisResult.peer_comparison?.relative_strengths?.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>

                <div className="p-3.5 bg-amber-950/30 border border-amber-900/50 rounded-xl space-y-1.5">
                  <span className="text-xs font-bold text-amber-300 uppercase tracking-wide flex items-center gap-1.5">
                    <AlertTriangle size={14} /> Relative Vulnerabilities vs Peers:
                  </span>
                  <ul className="text-xs text-amber-200/90 list-disc list-inside space-y-1">
                    {analysisResult.peer_comparison?.relative_weaknesses?.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* TAB 8: DATA QUALITY AUDIT */}
          {activeSubTab === 'audit' && (
            <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Info size={14} className="text-indigo-400" /> Data Quality, Integrity & Missing Metrics Audit
                </h4>
                <span className="text-xs text-slate-400">
                  Audited Line Items: <strong className="text-white font-mono">{analysisResult.missing_data_audit?.audited_items_count}</strong>
                </span>
              </div>

              <div className="p-3.5 bg-emerald-950/30 border border-emerald-900/50 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
                <CheckCircle size={15} />
                <span>{analysisResult.missing_data_audit?.integrity_confirmation}</span>
              </div>

              {analysisResult.missing_data_audit?.has_missing_data ? (
                <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
                  <span className="text-xs font-bold text-amber-400 uppercase tracking-wide">
                    Uncomputed Metrics ({analysisResult.missing_data_audit.missing_items_count} Disclosures Missing):
                  </span>
                  <div className="space-y-2 pt-1">
                    {analysisResult.missing_data_audit.missing_items.map((item, idx) => (
                      <div key={idx} className="p-2.5 bg-slate-900/80 rounded-lg border border-slate-800/80 text-xs">
                        <span className="font-bold text-white block">{item.metric}</span>
                        <span className="text-slate-400">{item.reason}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="p-6 text-center text-xs text-slate-400 bg-slate-950/60 rounded-xl border border-slate-800">
                  All 10 required fundamental metrics were disclosed and computed cleanly with 0 missing items.
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 4. Past Saved Analyses History */}
      <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-lg space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <Clock size={15} className="text-indigo-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Persisted Fundamental Reports ({history.length})
            </h3>
          </div>
          <button
            type="button"
            onClick={loadHistory}
            disabled={loadingHistory}
            className="p-1 text-slate-400 hover:text-white rounded"
            title="Refresh history"
          >
            <RefreshCw size={13} className={loadingHistory ? 'animate-spin' : ''} />
          </button>
        </div>

        {history.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {history.map((h) => (
              <div
                key={h.analysis_id}
                onClick={() => handleLoadSavedAnalysis(h.analysis_id)}
                className="p-3 bg-slate-950/70 hover:bg-slate-800/60 border border-slate-800 rounded-xl cursor-pointer transition flex items-center justify-between group"
              >
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-white text-xs">{h.ticker}</span>
                    <span className="px-1.5 py-0.2 bg-indigo-950 text-indigo-300 border border-indigo-900 rounded text-[10px] font-mono">
                      {h.market}
                    </span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-bold text-indigo-400">
                      Score: {h.overall_score}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 block truncate max-w-[180px] mt-0.5">
                    {h.company_name}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">
                    {new Date(h.retrieved_at).toLocaleString()}
                  </span>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={(e) => handleDeleteSaved(h.analysis_id, e)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 rounded-md transition"
                    title="Delete report"
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
            No fundamental analyses saved in PostgreSQL yet. Select a stock above and click "Run Fundamental Analysis".
          </div>
        )}
      </div>

      {/* Toast Notification */}
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
