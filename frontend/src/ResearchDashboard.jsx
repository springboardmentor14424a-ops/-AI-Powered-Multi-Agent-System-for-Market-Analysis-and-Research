import React, { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from 'recharts';
import Watchlist from './Watchlist';
import Preferences from './Preferences';

const APP_NAME = 'Stockens';
const API_BASE = 'http://localhost:8001';

const QUICK_PICKS = [
  { ticker: 'TCS', market: 'NSE', label: 'TCS · NSE' },
  { ticker: 'INFY', market: 'NSE', label: 'INFY · NSE' },
  { ticker: 'RELIANCE', market: 'NSE', label: 'RELIANCE · NSE' },
  { ticker: 'AAPL', market: 'Nasdaq', label: 'AAPL · Nasdaq' },
];

const formatNumber = (val, decimals = 2) => {
  if (val === null || val === undefined || Number.isNaN(Number(val))) return 'N/A';
  return Number(val).toLocaleString(undefined, { maximumFractionDigits: decimals });
};

const formatPct = (val, signed = false) => {
  if (val === null || val === undefined || Number.isNaN(Number(val))) return 'N/A';
  const num = Number(val);
  return `${signed && num > 0 ? '+' : ''}${num.toFixed(2)}%`;
};

const getCurrencySymbol = (mkt) => {
  const m = (mkt || '').toUpperCase();
  return m === 'NSE' || m === 'BSE' ? '₹' : '$';
};

export default function ResearchDashboard({ onLogout }) {
  const [ticker, setTicker] = useState('');
  const [market, setMarket] = useState('NSE');
  const [period, setPeriod] = useState('1y');
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [researchLoading, setResearchLoading] = useState(false);
  const [activeResult, setActiveResult] = useState(null);
  const [ohlcvData, setOhlcvData] = useState([]);

  // Dedicated Fundamental Analysis state
  const [fundamentalData, setFundamentalData] = useState(null);
  const [fundamentalLoading, setFundamentalLoading] = useState(false);
  const [fundamentalError, setFundamentalError] = useState('');
  const [predictionData, setPredictionData] = useState(null);
const [predictionLoading, setPredictionLoading] = useState(false);
const [predictionError, setPredictionError] = useState('');

  // Agent switcher inside Research tab: 'overview' | 'fundamentals'
  const [activeAgentView, setActiveAgentView] = useState('overview');

  // Sidebar navigation state: 'research' | 'watchlist' | 'preferences'
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
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/research/history`, {
        headers: authHeaders
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

  const fetchFundamentalAnalysis = async (targetTicker, targetMarket) => {
    const cleanTicker = (targetTicker || '').trim().toUpperCase();
    if (!cleanTicker) return;

    setFundamentalLoading(true);
    setFundamentalError('');
    setActiveAgentView('fundamentals');

    try {
      const res = await fetch(`${API_BASE}/analyze/fundamentals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders
        },
        body: JSON.stringify({
          ticker: cleanTicker,
          market: targetMarket || market
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to fetch fundamental analysis');
      }
      setFundamentalData(data);
    } catch (err) {
      setFundamentalError(err.message);
      setFundamentalData(null);
    } finally {
      setFundamentalLoading(false);
    }
  };

  const fetchTrendPrediction = async (targetTicker, targetMarket) => {
  const cleanTicker = (targetTicker || '').trim().toUpperCase();
  if (!cleanTicker) return;

  setPredictionLoading(true);
  setPredictionError('');
  setActiveAgentView('prediction');

  try {
    const res = await fetch(`${API_BASE}/predict/trend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders
      },
      body: JSON.stringify({
        ticker: cleanTicker,
        market: targetMarket || market
      })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to run ML trend prediction');
    }
    setPredictionData(data);
  } catch (err) {
    setPredictionError(err.message);
    setPredictionData(null);
  } finally {
    setPredictionLoading(false);
  }
};

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    setActiveResult(null);
    setFundamentalData(null);
    setPredictionData(null);
    setOhlcvData([]);
    setResearchLoading(true);

    const submittedTicker = ticker.trim().toUpperCase();
    const submittedMarket = market;

    try {
      const res = await fetch(`${API_BASE}/research`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders
        },
        body: JSON.stringify({
          ticker: submittedTicker,
          market: submittedMarket,
          requested_period: period
        })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to create research task');
      }

      setSuccessMessage(`Loaded market data for ${data.ticker} (${data.market})`);
      setActiveResult(data);
      setActiveAgentView('overview');
      if (data.ohlcv) {
        setOhlcvData(data.ohlcv);
      }

      setTicker(data.ticker || submittedTicker);
      fetchHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setResearchLoading(false);
    }
  };

  const handleQuickPick = (pick) => {
    setTicker(pick.ticker);
    setMarket(pick.market);
    setError('');
    setSuccessMessage('');
  };

  const currentFundTicker = fundamentalData?.ticker || activeResult?.ticker || ticker.trim().toUpperCase();
  const currentFundMarket = fundamentalData?.market || activeResult?.market || market;
  const displayCurrency = getCurrencySymbol(activeResult?.market || market);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-canvas)' }}>
      {/* Left Sidebar */}
      <aside
        style={{
          width: '250px',
          background: '#ffffff',
          borderRight: '1px solid var(--border-soft)',
          padding: '1.75rem 1.15rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          height: '100vh'
        }}
      >
        <div>
          {/* Brand Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '2rem', padding: '0 0.4rem' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #4f46e5 0%, #0ea5e9 100%)',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: '1.05rem',
                boxShadow: '0 4px 10px rgba(79, 70, 229, 0.25)'
              }}
            >
              S
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: '1.15rem', color: '#0f172a', letterSpacing: '-0.02em' }}>
                {APP_NAME}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>
                Multi-Agent Equity Lab
              </div>
            </div>
          </div>

          {/* Navigation Buttons */}
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {[
              { id: 'research', icon: '📊', label: 'Research & Agents' },
              { id: 'watchlist', icon: '⭐', label: 'Watchlist' },
              { id: 'preferences', icon: '⚙️', label: 'Preferences' }
            ].map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    padding: '0.75rem 0.95rem',
                    textAlign: 'left',
                    background: isActive ? 'var(--brand-soft)' : 'transparent',
                    color: isActive ? 'var(--brand-primary)' : '#475569',
                    border: isActive ? '1px solid #c7d2fe' : '1px solid transparent',
                    borderRadius: '10px',
                    cursor: 'pointer',
                    fontWeight: isActive ? 700 : 600,
                    fontSize: '0.92rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.6rem',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Workspace Pill + Logout */}
        <div>
          <div
            style={{
              background: '#f8fafc',
              border: '1px solid var(--border-soft)',
              borderRadius: '10px',
              padding: '0.7rem 0.85rem',
              marginBottom: '0.75rem',
              fontSize: '0.78rem',
              color: '#475569'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 700, color: '#059669' }}>
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
              Backend Connected
            </div>
            <div style={{ marginTop: '0.2rem', color: '#64748b' }}>Live + Static Agents Ready</div>
          </div>

          <button
            onClick={onLogout}
            style={{
              width: '100%',
              padding: '0.7rem 1rem',
              background: '#fff1f2',
              color: '#e11d48',
              border: '1px solid #fecdd3',
              borderRadius: '10px',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '0.88rem'
            }}
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Workspace */}
      <main style={{ flex: 1, padding: '2rem 2.5rem', maxWidth: '1040px', margin: '0 auto' }}>
        {activeTab === 'research' && (
          <div>
            {/* Top Welcome Header */}
            <header
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-end',
                flexWrap: 'wrap',
                gap: '1rem',
                marginBottom: '1.5rem'
              }}
            >
              <div>
                <span
                  style={{
                    display: 'inline-block',
                    background: 'var(--brand-soft)',
                    color: 'var(--brand-primary)',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '0.25rem 0.65rem',
                    borderRadius: '999px',
                    marginBottom: '0.45rem'
                  }}
                >
                  {APP_NAME} Workspace
                </span>
                <h1 style={{ margin: 0, fontSize: '1.65rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#0f172a' }}>
                  Stock Research & Agent Desk
                </h1>
                <p style={{ margin: '0.3rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.92rem' }}>
                  Pull live OHLCV snapshots or switch to the Fundamental Analysis Agent for static dataset intelligence.
                </p>
              </div>
            </header>

            {/* Search & Action Card */}
            <form onSubmit={handleSubmit} className="stockens-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>New Research Query</h3>

                {/* Quick Pick Chips */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-faint)', fontWeight: 600 }}>Quick picks:</span>
                  {QUICK_PICKS.map((pick) => (
                    <button
                      key={pick.label}
                      type="button"
                      className="stockens-chip"
                      onClick={() => handleQuickPick(pick)}
                    >
                      {pick.label}
                    </button>
                  ))}
                </div>
              </div>

              {error && (
                <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '0.7rem 0.9rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.88rem', fontWeight: 600 }}>
                  ⚠️ {error}
                </div>
              )}

              {successMessage && (
                <div style={{ background: 'var(--accent-mint-soft)', border: '1px solid #a7f3d0', color: '#065f46', padding: '0.7rem 0.9rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.88rem', fontWeight: 600 }}>
                  ✅ {successMessage}
                </div>
              )}

              {/* Compact 3-Column Input Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '1rem', marginBottom: '1.15rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.4rem', fontWeight: 700, fontSize: '0.82rem', color: '#334155' }}>
                    Ticker Symbol
                  </label>
                  <input
                    type="text"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value)}
                    placeholder="e.g. TCS, INFY, AAPL"
                    required
                    style={{
                      padding: '0.6rem 0.8rem',
                      width: '100%',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.92rem',
                      fontWeight: 600
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '0.4rem', fontWeight: 700, fontSize: '0.82rem', color: '#334155' }}>
                    Market Exchange
                  </label>
                  <select
                    value={market}
                    onChange={(e) => setMarket(e.target.value)}
                    style={{
                      padding: '0.6rem 0.8rem',
                      width: '100%',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.92rem',
                      background: '#ffffff'
                    }}
                  >
                    <option value="NSE">NSE (India)</option>
                    <option value="BSE">BSE (India)</option>
                    <option value="Nasdaq">Nasdaq (US)</option>
                    <option value="NYSE">NYSE (US)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '0.4rem', fontWeight: 700, fontSize: '0.82rem', color: '#334155' }}>
                    History Period
                  </label>
                  <select
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                    style={{
                      padding: '0.6rem 0.8rem',
                      width: '100%',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.92rem',
                      background: '#ffffff'
                    }}
                  >
                    <option value="1mo">1 Month (1mo)</option>
                    <option value="3mo">3 Months (3mo)</option>
                    <option value="6mo">6 Months (6mo)</option>
                    <option value="1y">1 Year (1y)</option>
                    <option value="2y">2 Years (2y)</option>
                  </select>
                </div>
              </div>

              <div>
  <button
    type="submit"
    disabled={researchLoading}
    style={{
      padding: '0.7rem 1.5rem',
      background: 'var(--brand-primary)',
      color: '#ffffff',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      fontWeight: 700,
      fontSize: '0.92rem'
    }}
  >
    {researchLoading ? 'Analyzing Stock...' : '🚀 Analyze Stock'}
  </button>
</div>
</form>

            {/* AGENT SELECTOR STRIP */}
            {(activeResult || fundamentalData || ticker.trim()) && (
              <div
                className="stockens-card"
                style={{
                  padding: '0.9rem 1.25rem',
                  marginBottom: '1.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '0.75rem'
                }}
              >
                <div>
                  <span style={{ fontWeight: 700, fontSize: '0.92rem', color: '#0f172a' }}>
                    🤖 Choose View / Agent
                  </span>
                  <span style={{ marginLeft: '0.5rem', fontSize: '0.82rem', color: 'var(--text-faint)' }}>
                    Switch between live overview and fundamental analysis
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => setActiveAgentView('overview')}
                    style={{
                      padding: '0.5rem 0.95rem',
                      borderRadius: '8px',
                      border: activeAgentView === 'overview' ? '1px solid var(--brand-primary)' : '1px solid var(--border-soft)',
                      cursor: 'pointer',
                      fontWeight: 700,
                      fontSize: '0.85rem',
                      background: activeAgentView === 'overview' ? 'var(--brand-primary)' : '#f8fafc',
                      color: activeAgentView === 'overview' ? '#ffffff' : '#334155'
                    }}
                  >
                    📊 Company & Market Overview
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setActiveAgentView('fundamentals');
                      const target = (ticker.trim() || activeResult?.ticker || fundamentalData?.ticker || '').toUpperCase();
                      if (target && fundamentalData?.ticker !== target) {
                        fetchFundamentalAnalysis(target, activeResult?.market || market);
                      }
                    }}
                    style={{
                      padding: '0.5rem 0.95rem',
                      borderRadius: '8px',
                      border: activeAgentView === 'fundamentals' ? '1px solid var(--accent-mint)' : '1px solid var(--border-soft)',
                      cursor: 'pointer',
                      fontWeight: 700,
                      fontSize: '0.85rem',
                      background: activeAgentView === 'fundamentals' ? 'var(--accent-mint)' : '#f8fafc',
                      color: activeAgentView === 'fundamentals' ? '#ffffff' : '#334155'
                    }}
                  >
                    🧭 Fundamental Analysis Agent
                  </button>
                  
<button
  type="button"
  onClick={() => {
    const target = (ticker.trim() || activeResult?.ticker || fundamentalData?.ticker || '').toUpperCase();
    const targetMkt = activeResult?.market || fundamentalData?.market || market;
    setActiveAgentView('prediction');
    if (target && predictionData?.ticker !== target) {
      fetchTrendPrediction(target, targetMkt);
    }
  }}
  style={{
    padding: '0.5rem 0.95rem',
    borderRadius: '8px',
    border: activeAgentView === 'prediction' ? '1px solid #0284c7' : '1px solid var(--border-soft)',
    cursor: 'pointer',
    fontWeight: 700,
    fontSize: '0.85rem',
    background: activeAgentView === 'prediction' ? '#0284c7' : '#f8fafc',
    color: activeAgentView === 'prediction' ? '#ffffff' : '#334155'
  }}
>
  📈 Technical & ML Prediction
</button>

                </div>
              </div>
            )}

            {/* VIEW 1: DEDICATED FUNDAMENTAL ANALYSIS AGENT */}
            {activeAgentView === 'fundamentals' && (
              <section className="stockens-card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.15rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>
                        🧭 Fundamental Analysis{currentFundTicker ? `: ${currentFundTicker}` : ''}
                      </h2>
                      <span style={{ background: 'var(--accent-mint-soft)', color: 'var(--accent-mint)', fontSize: '0.75rem', fontWeight: 700, padding: '0.2rem 0.55rem', borderRadius: '999px' }}>
                        Agent Active
                      </span>
                    </div>
                    <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.83rem', color: 'var(--text-faint)' }}>
                      Market: <strong>{currentFundMarket}</strong>
                      {fundamentalData?.as_of_date ? ` · As of ${fundamentalData.as_of_date}` : ''}
                      {fundamentalData?.source ? ` · ${fundamentalData.source}` : ''}
                    </p>
                  </div>

                  {currentFundTicker && (
                    <button
                      type="button"
                      onClick={() => fetchFundamentalAnalysis(currentFundTicker, currentFundMarket)}
                      disabled={fundamentalLoading}
                      style={{
                        padding: '0.45rem 0.9rem',
                        background: '#f8fafc',
                        color: '#0f172a',
                        border: '1px solid var(--border-soft)',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        fontSize: '0.82rem',
                        fontWeight: 700
                      }}
                    >
                      {fundamentalLoading ? 'Refreshing...' : '↻ Refresh Agent'}
                    </button>
                  )}
                </div>

                {fundamentalError && (
                  <div style={{ color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', padding: '0.8rem', borderRadius: '8px', fontSize: '0.88rem' }}>
                    {fundamentalError}
                  </div>
                )}

                {!fundamentalData && !fundamentalLoading && !fundamentalError && (
                  <div style={{ background: '#f8fafc', border: '1px dashed #cbd5e1', borderRadius: '10px', padding: '1.25rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    Pick a ticker like <strong>TCS</strong>, <strong>INFY</strong>, or <strong>RELIANCE</strong> above and click <strong>Run Fundamental Agent</strong> to inspect valuation, profitability, peers, and data-quality flags.
                  </div>
                )}

                {fundamentalData && (
                  <div>
                    {/* Investment Takeaway Callout */}
                    {fundamentalData.investment_takeaway && (
                      <div
                        style={{
                          background: 'linear-gradient(135deg, #eef2ff 0%, #f0fdf4 100%)',
                          border: '1px solid #c7d2fe',
                          borderRadius: '12px',
                          padding: '1.1rem 1.25rem',
                          marginBottom: '1.25rem'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                          <span style={{ background: 'var(--brand-primary)', color: '#fff', fontSize: '0.75rem', fontWeight: 700, padding: '0.2rem 0.6rem', borderRadius: '999px' }}>
                            {fundamentalData.investment_takeaway.stance}
                          </span>
                        </div>
                        <p style={{ margin: '0 0 0.35rem 0', color: '#0f172a', fontWeight: 700, fontSize: '0.96rem' }}>
                          {fundamentalData.investment_takeaway.one_liner}
                        </p>
                        <p style={{ margin: '0 0 0.4rem 0', fontSize: '0.88rem', color: '#334155' }}>
                          {fundamentalData.investment_takeaway.action_guidance}
                        </p>
                        {fundamentalData.investment_takeaway.disclaimer && (
                          <small style={{ color: '#64748b' }}>{fundamentalData.investment_takeaway.disclaimer}</small>
                        )}
                      </div>
                    )}

                    {/* 4 Core Pillars Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
                      <div style={{ border: '1px solid var(--border-soft)', borderRadius: '10px', padding: '1rem', background: 'var(--bg-subtle)' }}>
                        <h4 style={{ margin: '0 0 0.55rem 0', fontSize: '0.92rem', color: '#0f172a' }}>1. Revenue & Earnings</h4>
                        <p style={{ margin: '0.2rem 0', fontSize: '0.86rem' }}><strong>Revenue:</strong> {formatNumber(fundamentalData.revenue_and_earnings?.latest_revenue)}</p>
                        <p style={{ margin: '0.2rem 0', fontSize: '0.86rem' }}><strong>Net Income:</strong> {formatNumber(fundamentalData.revenue_and_earnings?.latest_net_income)}</p>
                        <p style={{ margin: '0.2rem 0', fontSize: '0.86rem' }}>
                          <strong>Turnover Proxy:</strong> {formatNumber(fundamentalData.revenue_and_earnings?.turnover_proxy?.latest_turnover, 0)} ({formatPct(fundamentalData.revenue_and_earnings?.turnover_proxy?.turnover_change_pct, true)})
                        </p>
                        <p style={{ margin: '0.55rem 0 0 0', fontSize: '0.8rem', color: '#475569' }}>{fundamentalData.revenue_and_earnings?.summary}</p>
                      </div>

                      <div style={{ border: '1px solid var(--border-soft)', borderRadius: '10px', padding: '1rem', background: 'var(--bg-subtle)' }}>
                        <h4 style={{ margin: '0 0 0.55rem 0', fontSize: '0.92rem', color: '#0f172a' }}>2. Profitability</h4>
                        <p style={{ margin: '0.2rem 0', fontSize: '0.86rem' }}>
                          <strong>Gross / Op / Net:</strong> {formatPct(fundamentalData.profitability?.gross_margin_pct)} / {formatPct(fundamentalData.profitability?.operating_margin_pct)} / {formatPct(fundamentalData.profitability?.net_margin_pct)}
                        </p>
                        <p style={{ margin: '0.2rem 0', fontSize: '0.86rem' }}>
                          <strong>Close vs Prev Close:</strong> {formatPct(fundamentalData.profitability?.price_change_vs_prev_close_pct, true)}
                        </p>
                        <p style={{ margin: '0.55rem 0 0 0', fontSize: '0.8rem', color: '#475569' }}>{fundamentalData.profitability?.summary}</p>
                      </div>

                      <div style={{ border: '1px solid var(--border-soft)', borderRadius: '10px', padding: '1rem', background: 'var(--bg-subtle)' }}>
                        <h4 style={{ margin: '0 0 0.55rem 0', fontSize: '0.92rem', color: '#0f172a' }}>3. Debt & Stability</h4>
                        <p style={{ margin: '0.2rem 0', fontSize: '0.86rem' }}><strong>Debt / Equity:</strong> {formatNumber(fundamentalData.debt_and_stability?.debt_to_equity)}</p>
                        <p style={{ margin: '0.2rem 0', fontSize: '0.86rem' }}>
                          <strong>VWAP / %Deliverble:</strong> {formatNumber(fundamentalData.debt_and_stability?.trading_stability_context?.vwap)} / {formatPct(fundamentalData.debt_and_stability?.trading_stability_context?.deliverable_pct)}
                        </p>
                        <p style={{ margin: '0.55rem 0 0 0', fontSize: '0.8rem', color: '#475569' }}>{fundamentalData.debt_and_stability?.summary}</p>
                      </div>

                      <div style={{ border: '1px solid var(--border-soft)', borderRadius: '10px', padding: '1rem', background: 'var(--bg-subtle)' }}>
                        <h4 style={{ margin: '0 0 0.55rem 0', fontSize: '0.92rem', color: '#0f172a' }}>4. Valuation & Ratios</h4>
                        <p style={{ margin: '0.2rem 0', fontSize: '0.86rem' }}><strong>P/E Ratio:</strong> {formatNumber(fundamentalData.valuation_and_ratios?.pe_ratio)}</p>
                        <p style={{ margin: '0.2rem 0', fontSize: '0.86rem' }}><strong>P/B Ratio:</strong> {formatNumber(fundamentalData.valuation_and_ratios?.pb_ratio)}</p>
                        <p style={{ margin: '0.2rem 0', fontSize: '0.86rem' }}><strong>ROE:</strong> {formatPct(fundamentalData.valuation_and_ratios?.roe_pct)}</p>
                        <p style={{ margin: '0.55rem 0 0 0', fontSize: '0.8rem', color: '#475569' }}>{fundamentalData.valuation_and_ratios?.summary}</p>
                      </div>
                    </div>

                    {/* 5. Historical Comparison */}
                    {fundamentalData.historical_comparison && (
                      <div style={{ border: '1px solid var(--border-soft)', borderRadius: '10px', padding: '1rem', marginBottom: '1.25rem' }}>
                        <h4 style={{ margin: '0 0 0.45rem 0', fontSize: '0.95rem' }}>5. Historical Performance Comparison</h4>
                        <p style={{ margin: '0 0 0.65rem 0', fontSize: '0.86rem', color: '#334155' }}>
                          {fundamentalData.historical_comparison.summary}
                        </p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', fontSize: '0.84rem', background: '#f8fafc', padding: '0.65rem 0.85rem', borderRadius: '8px' }}>
                          <span><strong>Records:</strong> {fundamentalData.historical_comparison.records_analyzed}</span>
                          <span><strong>Latest Close:</strong> {formatNumber(fundamentalData.historical_comparison.close_comparison?.latest_close)}</span>
                          <span><strong>vs 20d Avg:</strong> {formatPct(fundamentalData.historical_comparison.close_comparison?.vs_20d_avg_pct, true)}</span>
                          <span><strong>vs All-Time Avg:</strong> {formatPct(fundamentalData.historical_comparison.close_comparison?.vs_all_time_avg_pct, true)}</span>
                          <span><strong>Turnover vs 20d:</strong> {formatPct(fundamentalData.historical_comparison.turnover_comparison?.vs_20d_avg_pct, true)}</span>
                        </div>
                      </div>
                    )}

                    {/* 6. Peer Comparison */}
                    {fundamentalData.peer_comparison && (
                      <div style={{ border: '1px solid var(--border-soft)', borderRadius: '10px', padding: '1rem', marginBottom: '1.25rem' }}>
                        <h4 style={{ margin: '0 0 0.45rem 0', fontSize: '0.95rem' }}>6. Peer Comparison</h4>
                        <p style={{ margin: '0 0 0.75rem 0', fontSize: '0.86rem', color: '#334155' }}>
                          {fundamentalData.peer_comparison.summary}
                        </p>
                        {fundamentalData.peer_comparison.peers?.length > 0 && (
                          <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
                              <thead>
                                <tr style={{ background: '#f8fafc', textAlign: 'left', color: '#475569' }}>
                                  <th style={{ padding: '8px 10px', borderBottom: '1px solid var(--border-soft)' }}>Peer</th>
                                  <th style={{ padding: '8px 10px', borderBottom: '1px solid var(--border-soft)' }}>As Of</th>
                                  <th style={{ padding: '8px 10px', borderBottom: '1px solid var(--border-soft)' }}>Latest Close</th>
                                  <th style={{ padding: '8px 10px', borderBottom: '1px solid var(--border-soft)' }}>% Change</th>
                                  <th style={{ padding: '8px 10px', borderBottom: '1px solid var(--border-soft)' }}>%Deliverble</th>
                                </tr>
                              </thead>
                              <tbody>
                                {fundamentalData.peer_comparison.peers.map((peer, i) => (
                                  <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                    <td style={{ padding: '8px 10px', fontWeight: 700 }}>{peer.peer_symbol}</td>
                                    <td style={{ padding: '8px 10px', color: '#64748b' }}>{peer.as_of_date || 'N/A'}</td>
                                    <td style={{ padding: '8px 10px' }}>{formatNumber(peer.latest_close)}</td>
                                    <td style={{ padding: '8px 10px', fontWeight: 600, color: Number(peer.change_vs_prev_close_pct) >= 0 ? '#059669' : '#dc2626' }}>
                                      {formatPct(peer.change_vs_prev_close_pct, true)}
                                    </td>
                                    <td style={{ padding: '8px 10px' }}>{formatPct(peer.deliverable_pct)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )}

                    {/* 7. Missing or Inconsistent Data */}
                    {fundamentalData.data_quality_issues && (
                      <div style={{ border: '1px solid #fde68a', background: 'var(--accent-amber-soft)', borderRadius: '10px', padding: '1rem' }}>
                        <h4 style={{ margin: '0 0 0.45rem 0', color: '#92400e', fontSize: '0.92rem' }}>7. Data Quality & Missing Fields</h4>
                        <ul style={{ margin: '0 0 0.45rem 0', paddingLeft: '1.2rem', fontSize: '0.84rem', color: '#78350f' }}>
                          {(fundamentalData.data_quality_issues.issues || []).map((issue, idx) => (
                            <li key={idx} style={{ marginBottom: '0.2rem' }}>{issue}</li>
                          ))}
                        </ul>
                        {fundamentalData.data_quality_issues.missing_fundamental_fields?.length > 0 && (
                          <div style={{ fontSize: '0.8rem', color: '#92400e' }}>
                            <strong>Missing Fundamental Fields:</strong> {fundamentalData.data_quality_issues.missing_fundamental_fields.join(', ')}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </section>
            )}

 {/* VIEW 2: DEDICATED PREDICTION ANALYSIS AGENT */}
            {activeAgentView === 'prediction' && (
  <section className="stockens-card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem' }}>
      <div>
        <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: '#0f172a' }}>
          📈 Technical & ML Trend Prediction{(predictionData?.ticker || currentFundTicker) ? `: ${predictionData?.ticker || currentFundTicker}` : ''}
        </h2>
        <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          {predictionData?.model || 'HistGradientBoostingClassifier (Trained on NSE Equity Features)'}
        </p>
      </div>
      {(predictionData?.ticker || currentFundTicker) && (
        <button
          type="button"
          onClick={() => fetchTrendPrediction(predictionData?.ticker || currentFundTicker, predictionData?.market || currentFundMarket)}
          disabled={predictionLoading}
          style={{
            padding: '0.45rem 0.9rem',
            background: '#f8fafc',
            color: '#0f172a',
            border: '1px solid var(--border-soft)',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '0.82rem',
            fontWeight: 700
          }}
        >
          {predictionLoading ? 'Running Model...' : '↻ Re-run Model'}
        </button>
      )}
    </div>

    {predictionError && (
      <div style={{ color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', padding: '0.85rem', borderRadius: '8px', fontSize: '0.88rem', marginBottom: '1rem' }}>
        ⚠️ {predictionError}
      </div>
    )}

    {predictionLoading && (
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Running HistGradientBoosting inference on latest market data...</p>
    )}

    {!predictionLoading && !predictionData && !predictionError && (
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        Enter a ticker above and click <strong>🚀 Analyze Stock</strong>, or click <strong>↻ Re-run Model</strong> to generate a directional prediction.
      </p>
    )}

    {predictionData && !predictionLoading && (
      <div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
          <div style={{ background: predictionData.target_up === 1 ? '#ecfdf5' : '#fef2f2', border: `1px solid ${predictionData.target_up === 1 ? '#a7f3d0' : '#fecaca'}`, borderRadius: '10px', padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: '#475569', fontWeight: 700, letterSpacing: '0.03em' }}>PREDICTED TREND</div>
            <div style={{ fontSize: '1.3rem', fontWeight: 800, marginTop: '0.25rem', color: predictionData.target_up === 1 ? '#047857' : '#b91c1c' }}>
              {predictionData.prediction}
            </div>
            <div style={{ fontSize: '0.78rem', color: '#475569', marginTop: '0.2rem' }}>{predictionData.direction}</div>
          </div>

          <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-soft)', borderRadius: '10px', padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-faint)', fontWeight: 700, letterSpacing: '0.03em' }}>UPWARD PROBABILITY</div>
            <div style={{ fontSize: '1.3rem', fontWeight: 800, marginTop: '0.25rem', color: '#0f172a' }}>
              {predictionData.confidence != null ? `${predictionData.confidence}%` : 'N/A'}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Classifier `predict_proba`</div>
          </div>

          <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-soft)', borderRadius: '10px', padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-faint)', fontWeight: 700, letterSpacing: '0.03em' }}>LATEST CLOSE ({predictionData.market})</div>
            <div style={{ fontSize: '1.3rem', fontWeight: 800, marginTop: '0.25rem', color: '#0f172a' }}>
              {predictionData.latest_close != null ? `${predictionData.market === 'NSE' || predictionData.market === 'BSE' ? '₹' : '$'}${predictionData.latest_close}` : 'N/A'}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Latest daily session</div>
          </div>
        </div>

        <div style={{ background: '#f8fafc', border: '1px solid var(--border-soft)', borderRadius: '8px', padding: '0.75rem 1rem', fontSize: '0.82rem', color: '#475569' }}>
          <strong>Model Note:</strong> Directional signal based on recent daily price and volume action. For research purposes only.
        </div>
      </div>
    )}
  </section>
)}

            {/* VIEW 2: COMPANY & MARKET OVERVIEW */}
            {activeAgentView === 'overview' && activeResult && (
              <section className="stockens-card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
                {/* Top KPI Strip */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <h2 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800 }}>
                        {activeResult.company_name || activeResult.ticker}
                      </h2>
                      <span style={{ background: 'var(--brand-soft)', color: 'var(--brand-primary)', fontSize: '0.76rem', fontWeight: 700, padding: '0.2rem 0.6rem', borderRadius: '999px' }}>
                        {activeResult.ticker} · {activeResult.market}
                      </span>
                    </div>
                    <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.84rem', color: 'var(--text-faint)' }}>
                      Period: <strong>{activeResult.requested_period}</strong>
                      {activeResult.profile?.sector ? ` · ${activeResult.profile.sector}` : ''}
                    </p>
                  </div>

                  {activeResult.result_price !== null && activeResult.result_price !== undefined && (
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-faint)', fontWeight: 700, textTransform: 'uppercase' }}>
                        Latest Close
                      </div>
                      <div style={{ fontSize: '1.55rem', fontWeight: 800, color: '#0f172a' }}>
                        {displayCurrency}{Number(activeResult.result_price).toFixed(2)}
                      </div>
                    </div>
                  )}
                </div>

                {/* Price Trend Chart */}
                <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: 700 }}>Price Trend (Closing Price)</h3>
                {ohlcvData.length === 0 ? (
                  <p style={{ color: 'var(--text-faint)', fontSize: '0.9rem' }}>No chart data available.</p>
                ) : (
                  <div style={{ width: '100%', height: '290px', marginBottom: '1.75rem' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={ohlcvData}>
                        <defs>
                          <linearGradient id="stockensPriceGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.22} />
                            <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="Date" tick={{ fontSize: 11, fill: '#64748b' }} />
                        <YAxis domain={['auto', 'auto']} tick={{ fontSize: 11, fill: '#64748b' }} />
                        <Tooltip />
                        <Area
                          type="monotone"
                          dataKey="Close"
                          stroke="#4f46e5"
                          strokeWidth={2.2}
                          fillOpacity={1}
                          fill="url(#stockensPriceGrad)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Company Profile Box */}
                {activeResult.profile && (
                  <div style={{ background: 'var(--bg-subtle)', padding: '1rem 1.15rem', borderRadius: '10px', border: '1px solid var(--border-soft)', marginBottom: '1.5rem' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', fontSize: '0.84rem', marginBottom: '0.5rem', color: '#334155' }}>
                      <span><strong>Sector:</strong> {activeResult.profile.sector}</span>
                      <span><strong>Industry:</strong> {activeResult.profile.industry}</span>
                      {activeResult.profile.market_cap && (
                        <span><strong>Market Cap:</strong> {displayCurrency}{(activeResult.profile.market_cap / 1e9).toFixed(2)}B</span>
                      )}
                      {activeResult.profile.website && activeResult.profile.website !== 'N/A' && (
                        <span>
                          <strong>Website:</strong>{' '}
                          <a href={activeResult.profile.website} target="_blank" rel="noreferrer" style={{ color: 'var(--brand-primary)', fontWeight: 600 }}>
                            {activeResult.profile.website}
                          </a>
                        </span>
                      )}
                    </div>
                    <p style={{ margin: 0, fontSize: '0.88rem', color: '#475569', lineHeight: '1.55' }}>
                      {activeResult.profile.summary}
                    </p>
                  </div>
                )}

                {/* OHLCV Table */}
                <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: 700 }}>OHLCV Historical Data</h3>
                {ohlcvData.length === 0 ? (
                  <p style={{ color: 'var(--text-faint)' }}>No OHLCV records available for this query yet.</p>
                ) : (
                  <div style={{ maxHeight: '280px', overflowY: 'auto', border: '1px solid var(--border-soft)', borderRadius: '10px', marginBottom: '1.75rem' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
                      <thead>
                        <tr style={{ background: '#f8fafc', textAlign: 'left', color: '#475569', position: 'sticky', top: 0 }}>
                          <th style={{ padding: '10px 12px', borderBottom: '1px solid var(--border-soft)' }}>Date</th>
                          <th style={{ padding: '10px 12px', borderBottom: '1px solid var(--border-soft)' }}>Open</th>
                          <th style={{ padding: '10px 12px', borderBottom: '1px solid var(--border-soft)' }}>High</th>
                          <th style={{ padding: '10px 12px', borderBottom: '1px solid var(--border-soft)' }}>Low</th>
                          <th style={{ padding: '10px 12px', borderBottom: '1px solid var(--border-soft)' }}>Close</th>
                          <th style={{ padding: '10px 12px', borderBottom: '1px solid var(--border-soft)' }}>Volume</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ohlcvData.map((row, index) => (
                          <tr key={index} style={{ borderBottom: '1px solid #f1f5f9' }}>
                            <td style={{ padding: '8px 12px', fontWeight: 600 }}>{row.Date}</td>
                            <td style={{ padding: '8px 12px' }}>{row.Open != null ? row.Open.toFixed(2) : 'N/A'}</td>
                            <td style={{ padding: '8px 12px' }}>{row.High != null ? row.High.toFixed(2) : 'N/A'}</td>
                            <td style={{ padding: '8px 12px' }}>{row.Low != null ? row.Low.toFixed(2) : 'N/A'}</td>
                            <td style={{ padding: '8px 12px', fontWeight: 700 }}>{row.Close != null ? row.Close.toFixed(2) : 'N/A'}</td>
                            <td style={{ padding: '8px 12px', color: '#475569' }}>{row.Volume != null ? row.Volume.toLocaleString() : 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Annual Financial Statements */}
                <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: 700 }}>📑 Key Financial Statements (Annual)</h3>
                {!activeResult.financials || activeResult.financials.length === 0 ? (
                  <p style={{ color: 'var(--text-faint)', fontSize: '0.88rem' }}>No financial statement records available for this ticker.</p>
                ) : (
                  <div style={{ overflowX: 'auto', border: '1px solid var(--border-soft)', borderRadius: '10px', marginBottom: '1.25rem' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
                      <thead>
                        <tr style={{ background: '#f8fafc', textAlign: 'left', color: '#475569' }}>
                          <th style={{ padding: '10px 12px', borderBottom: '1px solid var(--border-soft)' }}>Metric</th>
                          {Object.keys(activeResult.financials[0])
                            .filter((key) => key !== 'metric')
                            .map((dateCol) => (
                              <th key={dateCol} style={{ padding: '10px 12px', borderBottom: '1px solid var(--border-soft)' }}>{dateCol}</th>
                            ))}
                        </tr>
                      </thead>
                      <tbody>
                        {activeResult.financials.map((row, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                            <td style={{ padding: '8px 12px', fontWeight: 700 }}>{row.metric}</td>
                            {Object.keys(row)
                              .filter((key) => key !== 'metric')
                              .map((dateCol) => (
                                <td key={dateCol} style={{ padding: '8px 12px' }}>
                                  {row[dateCol] !== null && row[dateCol] !== undefined
                                    ? `${displayCurrency}${(row[dateCol] / 1e6).toLocaleString(undefined, { maximumFractionDigits: 2 })}M`
                                    : 'N/A'}
                                </td>
                              ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Footer Metadata */}
                <div style={{ paddingTop: '0.75rem', borderTop: '1px solid var(--border-soft)', fontSize: '0.8rem', color: 'var(--text-faint)', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <span><strong>Data Source:</strong> {activeResult.source || 'Yahoo Finance (yfinance)'}</span>
                  <span>
                    <strong>Retrieved At:</strong>{' '}
                    {activeResult.retrieved_at ? new Date(activeResult.retrieved_at).toLocaleString() : 'Just now'}
                  </span>
                </div>
              </section>
            )}

            {/* Recent Research History */}
            <section className="stockens-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ margin: '0 0 0.9rem 0', fontSize: '1.05rem', fontWeight: 700 }}>Recent Research History</h3>
              {history.length === 0 ? (
                <p style={{ color: 'var(--text-faint)', margin: 0, fontSize: '0.9rem' }}>
                  No research history yet. Click one of the quick-pick chips above to run your first search!
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
                  {history.map((item) => (
                    <div
                      key={item.id}
                      style={{
                        background: 'var(--bg-subtle)',
                        border: '1px solid var(--border-soft)',
                        padding: '0.8rem 1rem',
                        borderRadius: '10px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: '0.5rem'
                      }}
                    >
                      <div style={{ fontSize: '0.9rem' }}>
                        <strong>{item.ticker}</strong>{' '}
                        <span style={{ color: 'var(--text-faint)' }}>({item.market}) · Period: {item.requested_period}</span>
                        {item.result_price && (
                          <span style={{ marginLeft: '0.6rem', color: '#0f172a' }}>
                            · Price: <strong>{getCurrencySymbol(item.market)}{item.result_price}</strong>
                          </span>
                        )}
                      </div>
                      <span
                        style={{
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          padding: '0.22rem 0.6rem',
                          borderRadius: '999px',
                          background: item.status === 'Completed' ? 'var(--accent-mint-soft)' : '#fef2f2',
                          color: item.status === 'Completed' ? 'var(--accent-mint)' : '#dc2626'
                        }}
                      >
                        {item.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}

        {/* TAB 2: WATCHLIST */}
        {activeTab === 'watchlist' && (
          <div className="stockens-card" style={{ padding: '1.5rem' }}>
            <Watchlist />
          </div>
        )}

        {/* TAB 3: PREFERENCES */}
        {activeTab === 'preferences' && (
          <div className="stockens-card" style={{ padding: '1.5rem' }}>
            <Preferences />
          </div>
        )}
      </main>
    </div>
  );
}