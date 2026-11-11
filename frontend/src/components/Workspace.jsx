
import React, { useEffect, useState } from 'react';
import {
  Search, Plus, Trash2, History, Settings, TrendingUp,
  LogOut, Loader2, Sparkles, BarChart3, Globe, Clock,
  Shield, User, Mail, Lock, Activity, ArrowUpRight,
  RefreshCw, Eye, EyeOff, X, Database, Wallet,
  ChevronRight
} from 'lucide-react';

// ======================================================
// CONFIGURATION
// ======================================================

const API_BASE = 'http://127.0.0.1:8000/api';

const DEFAULT_PREFERENCES = {
  preferred_market: 'NSE',
  default_period: '1y',
};

// ======================================================
// API HELPER
// ======================================================

async function apiRequest(path, options = {}, token = '') {
  const headers = { ...(options.headers || {}) };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const text = await response.text();
  let data = {};

  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { detail: text };
  }

  if (!response.ok) {
    throw new Error(
      data.detail || `Request failed (${response.status})`
    );
  }

  return data;
}

// ======================================================
// FORMATTING HELPERS
// ======================================================

function formatPrice(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) return '—';

  return number.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatDate(value) {
  if (!value) return '—';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return String(value);

  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function getStatusColor(status) {
  const value = String(status || '').toLowerCase();

  if (value === 'completed' || value === 'success') {
    return '#16845B';
  }

  if (value === 'failed' || value === 'error') {
    return '#DC4C55';
  }

  return '#D99A26';
}

// ======================================================
// LIGHT BLUE AND WHITE DESIGN SYSTEM
// ======================================================

const colors = {
  background: '#F3F7FD',
  sidebar: '#FFFFFF',
  panel: '#FFFFFF',
  input: '#F7F9FC',
  border: '#E3EAF3',
  text: '#17345D',
  muted: '#61748F',
  subtle: '#91A1B7',
  primary: '#2167E8',
  primaryHover: '#3988F5',
  green: '#16845B',
  red: '#DC4C55',
};

const styles = {
  page: {
    minHeight: '100vh',
    width: '100%',
    background: colors.background,
    color: colors.text,
    fontFamily: 'Inter, system-ui, sans-serif',
  },

  input: {
    width: '100%',
    boxSizing: 'border-box',
    background: colors.input,
    border: `1px solid ${colors.border}`,
    borderRadius: '10px',
    padding: '13px 15px',
    color: colors.text,
    fontSize: '13px',
    outline: 'none',
  },

  button: {
    border: 'none',
    borderRadius: '10px',
    padding: '12px 17px',
    background: colors.primary,
    color: '#FFFFFF',
    fontWeight: 800,
    fontSize: '12px',
    cursor: 'pointer',
    transition: '0.2s',
  },

  secondaryButton: {
    border: `1px solid ${colors.border}`,
    borderRadius: '10px',
    padding: '11px 15px',
    background: '#FFFFFF',
    color: colors.muted,
    fontWeight: 600,
    fontSize: '12px',
    cursor: 'pointer',
  },

  panel: {
    background: colors.panel,
    border: `1px solid ${colors.border}`,
    borderRadius: '15px',
    padding: '22px',
    boxShadow: '0 4px 18px rgba(35,75,130,0.035)',
  },

  label: {
    color: colors.muted,
    fontSize: '10px',
    fontWeight: 800,
    letterSpacing: '1.2px',
    textTransform: 'uppercase',
  },
};

// ======================================================
// MAIN WORKSPACE
// ======================================================

export default function Workspace() {

  // AUTHENTICATION

  const [token, setToken] = useState(
    () => localStorage.getItem('token') || ''
  );

  const [isRegistering, setIsRegistering] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');


  // APPLICATION

  const [activeTab, setActiveTab] = useState('search');
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);

  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  // MARKET DATA

  const [tickerInput, setTickerInput] = useState('');
  const [searchResult, setSearchResult] = useState(null);

  // USER DATA

  const [watchlist, setWatchlist] = useState([]);
  const [history, setHistory] = useState([]);

  const [preferences, setPreferences] = useState(
    DEFAULT_PREFERENCES
  );

  // ====================================================
  // AUTHENTICATION
  // ====================================================

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }, [token]);

  async function handleRegister(event) {
    event.preventDefault();

    setError('');
    setMessage('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (password.length < 8) {
      setError('Password must contain at least 8 characters.');
      return;
    }

    setAuthLoading(true);

    try {
      await apiRequest('/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          confirm_password: confirmPassword,
        }),
      });

      setMessage(
        'Account created successfully! Please sign in.'
      );

      setIsRegistering(false);
      setPassword('');
      setConfirmPassword('');

    } catch (err) {
      setError(err.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogin(event) {
    event.preventDefault();

    setError('');
    setMessage('');
    setAuthLoading(true);

    try {
      const formData = new URLSearchParams();

      formData.append('username', email);
      formData.append('password', password);

      const data = await apiRequest('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      setToken(data.access_token);
      setPassword('');

    } catch (err) {
      setError(err.message);
    } finally {
      setAuthLoading(false);
    }
  }

  function handleLogout() {
    setToken('');
    setActiveTab('search');

    setWatchlist([]);
    setHistory([]);
    setSearchResult(null);

    setEmail('');
    setPassword('');

    setMessage('');
    setError('');
  }

  // ====================================================
  // LOAD USER WORKSPACE
  // ====================================================

  useEffect(() => {
    if (!token) return;

    async function loadWorkspace() {
      try {
        const [
          watchlistData,
          historyData,
          preferenceData,
        ] = await Promise.all([
          apiRequest('/watchlist', {}, token),
          apiRequest('/workspace/history', {}, token),
          apiRequest('/workspace/preferences', {}, token),
        ]);

        setWatchlist(
          Array.isArray(watchlistData)
            ? watchlistData
            : watchlistData.items || []
        );

        setHistory(
          Array.isArray(historyData)
            ? historyData
            : historyData.items || []
        );

        setPreferences({
          ...DEFAULT_PREFERENCES,
          ...preferenceData,
        });

      } catch (err) {
        console.error('Workspace loading error:', err);

        setError(
          `Could not load workspace data: ${err.message}`
        );
      }
    }

    loadWorkspace();
  }, [token]);

  // ====================================================
  // WATCHLIST
  // ====================================================

  async function fetchWatchlist() {
    try {
      const data = await apiRequest(
        '/watchlist',
        {},
        token
      );

      setWatchlist(
        Array.isArray(data) ? data : data.items || []
      );

    } catch (err) {
      setError(err.message);
    }
  }

  async function addToWatchlist() {
    const ticker = tickerInput.trim().toUpperCase();

    if (!ticker) return;

    setError('');
    setMessage('');

    try {
      await apiRequest('/watchlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker }),
      }, token);

      setTickerInput('');

      await fetchWatchlist();

      setMessage(`${ticker} added to your watchlist.`);

    } catch (err) {
      setError(err.message);
    }
  }

  async function removeFromWatchlist(ticker) {
    setError('');

    try {
      await apiRequest(
        `/watchlist/${encodeURIComponent(ticker)}`,
        { method: 'DELETE' },
        token
      );

      await fetchWatchlist();

      setMessage(`${ticker} removed from your watchlist.`);

    } catch (err) {
      setError(err.message);
    }
  }

  // ====================================================
  // RESEARCH HISTORY
  // ====================================================

  async function fetchHistory() {
    try {
      const data = await apiRequest(
        '/workspace/history',
        {},
        token
      );

      setHistory(
        Array.isArray(data) ? data : data.items || []
      );

    } catch (err) {
      setError(err.message);
    }
  }

  // ====================================================
  // STOCK SEARCH
  // ====================================================

  async function handleStockSearch(symbol) {
    const ticker = symbol.trim().toUpperCase();

    if (!ticker) {
      setError('Please enter a stock ticker.');
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');
    setSearchResult(null);

    try {
      const params = new URLSearchParams({
        ticker,
        market: preferences.preferred_market,
        period: preferences.default_period,
      });

      const data = await apiRequest(
        `/market/search?${params.toString()}`,
        {},
        token
      );

      setSearchResult(data);

      await fetchHistory();

      setMessage(`Successfully retrieved data for ${ticker}.`);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // ====================================================
  // USER PREFERENCES
  // ====================================================

  async function handleSavePreferences(event) {
    event.preventDefault();

    setError('');
    setMessage('');

    try {
      const data = await apiRequest(
        '/workspace/preferences',
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(preferences),
        },
        token
      );

      setPreferences({
        ...DEFAULT_PREFERENCES,
        ...data,
      });

      setMessage('Your preferences have been saved.');

    } catch (err) {
      setError(err.message);
    }
  }

  // ====================================================
  // AUTHENTICATION SCREEN
  // ====================================================

  if (!token) {
    return (
      <div style={authPage}>

        <div style={authContainer}>

          {/* LEFT PANEL */}

          <div style={authLeft}>

            <div>
              <div style={brandRow}>
                <div style={brandIcon}>
                  <BarChart3 size={23} />
                </div>

                <div>
                  <div style={brandName}>
                    QUANT ANALYST HUB
                  </div>

                  <div style={brandSubtitle}>
                    MARKET INTELLIGENCE
                  </div>
                </div>
              </div>

              <div style={{ marginTop: '90px' }}>

                <div style={eyebrow}>
                  <Sparkles
                    size={12}
                    style={{
                      display: 'inline',
                      marginRight: '6px',
                      verticalAlign: 'middle',
                    }}
                  />
                  AI-POWERED MARKET RESEARCH
                </div>

                <h1 style={heroTitle}>
                  Smarter research.
                  <br />
                  <span style={{ color: '#2167E8' }}>
                    Clearer decisions.
                  </span>
                </h1>

                <p style={heroDescription}>
                  Explore financial markets, retrieve historical
                  stock data and organise your research in one
                  intelligent workspace.
                </p>

              </div>
            </div>

            {/* DECORATIVE MARKET CARD */}

            <div style={marketPreview}>

              <div style={marketPreviewHeader}>
                <div>
                  <p style={previewLabel}>
                    YOUR RESEARCH WORKSPACE
                  </p>

                  <h2 style={previewTitle}>
                    Market insights
                  </h2>
                </div>

                <div style={previewIcon}>
                  <TrendingUp size={22} />
                </div>
              </div>

              <div style={barChart}>
                {[30, 48, 38, 67, 52, 76, 61, 90, 72, 100, 82, 110]
                  .map((height, index) => (
                    <div
                      key={index}
                      style={{
                        flex: 1,
                        height: `${height * 0.75}px`,
                        maxHeight: '85px',
                        borderRadius: '5px 5px 2px 2px',
                        background: index === 9
                          ? '#2167E8'
                          : 'linear-gradient(180deg, #76ACFF, #D8E9FF)',
                      }}
                    />
                  ))}
              </div>

              <p style={previewFootnote}>
                Illustrative visual • Not live market data
              </p>

            </div>

            <p style={leftFooter}>
              INTELLIGENT RESEARCH • INFORMED DECISIONS
            </p>

          </div>

          {/* RIGHT PANEL */}

          <div style={authRight}>

            <div style={authFormContainer}>

              <div style={authLockIcon}>
                <Lock size={22} />
              </div>

              <h2 style={authHeading}>
                {isRegistering
                  ? 'Create your account.'
                  : 'Welcome back.'}
              </h2>

              <p style={authDescription}>
                {isRegistering
                  ? 'Create an account to access your personal research workspace.'
                  : 'Sign in to continue to your market research workspace.'}
              </p>

              {error && (
  <div style={{
    padding: '12px 14px',
    borderRadius: '12px',
    background: '#FEF2F2',
    color: '#B91C1C',
    border: '1px solid #FECACA',
    fontSize: '13px',
    marginBottom: '14px'
  }}>
    {error}
  </div>
)}

             {message && (
  <div style={{
    padding: '12px 14px',
    borderRadius: '12px',
    background: '#ECFDF5',
    color: '#047857',
    border: '1px solid #A7F3D0',
    fontSize: '13px',
    marginBottom: '14px'
  }}>
    {message}
  </div>
)}
              <form
                onSubmit={isRegistering ? handleRegister : handleLogin}
                style={authForm}
              >

                {isRegistering && (
                  <div>
                    <label style={authLabel}>
                      FULL NAME
                    </label>

                    <div style={authField}>
                      <User size={17} color="#91A1B7" />

                      <input
                        style={authInput}
                        type="text"
                        placeholder="Enter your full name"
                        value={fullName}
                        onChange={e => setFullName(e.target.value)}
                        required
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label style={authLabel}>
                    EMAIL ADDRESS
                  </label>

                  <div style={authField}>
                    <Mail size={17} color="#91A1B7" />

                    <input
                      style={authInput}
                      type="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div>
                  <label style={authLabel}>
                    PASSWORD
                  </label>

                  <div style={authField}>
                    <Lock size={17} color="#91A1B7" />

                    <input
                      style={authInput}
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Enter your password"
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      required
                    />

                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      style={passwordToggle}
                    >
                      {showPassword
                        ? <EyeOff size={17} />
                        : <Eye size={17} />}
                    </button>
                  </div>
                </div>

                {isRegistering && (
                  <div>
                    <label style={authLabel}>
                      CONFIRM PASSWORD
                    </label>

                    <div style={authField}>
                      <Shield size={17} color="#91A1B7" />

                      <input
                        style={authInput}
                        type="password"
                        placeholder="Re-enter your password"
                        value={confirmPassword}
                        onChange={e => setConfirmPassword(e.target.value)}
                        required
                      />
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={authLoading}
                  style={{
                    ...authSubmitButton,
                    opacity: authLoading ? 0.7 : 1,
                  }}
                >
                  {authLoading
                    ? 'PLEASE WAIT...'
                    : isRegistering
                      ? 'CREATE ACCOUNT'
                      : 'SIGN IN TO WORKSPACE'}

                  {!authLoading && (
                    <ArrowUpRight
                      size={16}
                      style={{
                        display: 'inline',
                        marginLeft: '8px',
                        verticalAlign: 'middle',
                      }}
                    />
                  )}
                </button>

              </form>

              {/* GOOGLE SIGN IN */}

              <div style={dividerRow}>
                <div style={dividerLine} />
                <span style={dividerText}>
                  OR CONTINUE WITH
                </span>
                <div style={dividerLine} />
              </div>

              <button
                type="button"
                onClick={() => setMessage(
                  'Google sign-in requires Google OAuth credentials. It has not been configured yet.'
                )}
                style={googleButton}
              >
                <span style={googleLetter}>G</span>
                Continue with Google
              </button>

              {/* REGISTER / LOGIN SWITCH */}

              <p style={authSwitchText}>
                {isRegistering
                  ? 'Already have an account?'
                  : "Don't have an account?"}

                <button
                  type="button"
                  onClick={() => {
                    setIsRegistering(!isRegistering);
                    setError('');
                    setMessage('');
                  }}
                  style={authSwitchButton}
                >
                  {isRegistering
                    ? 'Sign in'
                    : 'Create account'}
                </button>
              </p>

              <div style={authFooter}>
                <Shield size={13} />
                SECURE ACCESS • YOUR RESEARCH, YOUR WORKSPACE
              </div>

            </div>
          </div>

        </div>
      </div>
    );
  }

  // ====================================================
  // DASHBOARD
  // ====================================================

  const tabs = [
    {
      id: 'search',
      label: 'Market Search',
      icon: Search,
    },
    {
      id: 'history',
      label: 'Research History',
      icon: History,
    },
    {
      id: 'preferences',
      label: 'Preferences',
      icon: Settings,
    },
  ];

  const historicalData = searchResult?.historical_data || [];

  return (
    <div style={{
      ...styles.page,
      display: 'flex',
      minHeight: '100vh',
    }}>

      {/* SIDEBAR */}

      <aside style={sidebarStyle}>

        <div>
          <div style={sidebarBrand}>

            <div style={sidebarBrandIcon}>
              <BarChart3 size={21} />
            </div>

            <div>
              <div style={sidebarBrandName}>
                QUANT ANALYST
              </div>

              <div style={sidebarBrandSubtitle}>
                RESEARCH TERMINAL
              </div>
            </div>

          </div>

          <p style={sidebarLabel}>
            WORKSPACE
          </p>

          <nav style={sidebarNav}>
            {tabs.map(tab => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setError('');
                    setMessage('');
                  }}
                  style={{
                    ...navButton,
                    background: active ? '#EAF2FF' : 'transparent',
                    color: active ? '#2167E8' : '#61748F',
                  }}
                >
                  <Icon size={17} />
                  {tab.label}

                  {active && (
                    <ChevronRight
                      size={15}
                      style={{ marginLeft: 'auto' }}
                    />
                  )}
                </button>
              );
            })}
          </nav>

          <div style={systemCard}>
            <div style={systemHeading}>
              <Activity size={14} />
              SYSTEM STATUS
            </div>

            <p style={systemText}>
              Backend connected
            </p>

            <p style={systemSubtext}>
              PostgreSQL workspace
            </p>
          </div>
        </div>

        <div>
          <div style={signedInCard}>
            <div style={signedInLabel}>
              SIGNED IN AS
            </div>

            <div style={signedInEmail}>
              {email || 'Workspace user'}
            </div>
          </div>

          <button
            onClick={handleLogout}
            style={logoutButton}
          >
            <LogOut size={15} />
            Sign out
          </button>
        </div>

      </aside>

      {/* MAIN CONTENT */}

      <main style={{
        flex: 1,
        minWidth: 0,
        padding: '32px',
        overflowX: 'hidden',
      }}>

        {/* HEADER */}

        <header style={headerStyle}>

          <div>
            <p style={headerEyebrow}>
              MARKET INTELLIGENCE PLATFORM
            </p>

            <h1 style={headerTitle}>
              {activeTab === 'search'
                ? 'Market Analysis'
                : activeTab === 'history'
                  ? 'Research History'
                  : 'Workspace Settings'}
            </h1>

            <p style={headerDescription}>
              Research, monitor and analyze financial markets.
            </p>
          </div>

          <div style={headerBadges}>
            <div style={headerBadge}>
              <Globe size={14} color={colors.primary} />
              {preferences.preferred_market}
            </div>

            <div style={headerBadge}>
              <Clock size={14} color={colors.primary} />
              {preferences.default_period}
            </div>
          </div>

        </header>

        {error && (
          <div style={dashboardError}>
            {error}

            <button
              onClick={() => setError('')}
              style={alertCloseStyle}
            >
              <X size={15} />
            </button>
          </div>
        )}

        {message && (
          <div style={dashboardSuccess}>
            {message}

            <button
              onClick={() => setMessage('')}
              style={alertCloseStyle}
            >
              <X size={15} />
            </button>
          </div>
        )}

        {/* MARKET SEARCH */}

        {activeTab === 'search' && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '23px',
          }}>

            {/* SUMMARY CARDS */}

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
              gap: '15px',
            }}>

              <SummaryCard
                icon={Eye}
                label="Watchlist Stocks"
                value={watchlist.length}
                color="#2167E8"
              />

              <SummaryCard
                icon={History}
                label="Research Queries"
                value={history.length}
                color="#16845B"
              />

              <SummaryCard
                icon={Database}
                label="Selected Market"
                value={preferences.preferred_market}
                color="#D99A26"
              />

            </div>

            {/* STOCK SEARCH */}

            <section style={styles.panel}>

              <div style={sectionHeading}>
                <Search size={18} color={colors.primary} />

                <h2 style={sectionTitle}>
                  Stock Data Search
                </h2>
              </div>

              <p style={sectionDescription}>
                Enter a ticker symbol to retrieve historical market data.
              </p>

              <div style={{
                display: 'flex',
                gap: '10px',
                flexWrap: 'wrap',
              }}>

                <input
                  style={{
                    ...styles.input,
                    flex: '1 1 220px',
                    fontFamily: 'monospace',
                    textTransform: 'uppercase',
                  }}
                  placeholder="Example: INFY, RELIANCE, AAPL"
                  value={tickerInput}
                  onChange={e => setTickerInput(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      handleStockSearch(tickerInput);
                    }
                  }}
                />

                <button
                  onClick={() => handleStockSearch(tickerInput)}
                  disabled={loading}
                  style={searchButton}
                >
                  {loading
                    ? <Loader2 size={15} />
                    : <Search size={15} />}
                  {loading ? 'SEARCHING' : 'SEARCH STOCK'}
                </button>

                <button
                  onClick={addToWatchlist}
                  title="Add to watchlist"
                  style={addButton}
                >
                  <Plus size={18} />
                </button>

              </div>
            </section>

            {/* WATCHLIST */}

            <section style={styles.panel}>

              <div style={sectionHeaderRow}>

                <div style={sectionHeading}>
                  <Wallet size={18} color={colors.primary} />

                  <h2 style={sectionTitle}>
                    My Watchlist
                  </h2>
                </div>

                <span style={countText}>
                  {watchlist.length} stocks
                </span>

              </div>

              {watchlist.length === 0 ? (
                <EmptyState
                  title="Your watchlist is empty"
                  description="Search for a stock and add it to your watchlist."
                />
              ) : (
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '10px',
                }}>
                  {watchlist.map(item => (
                    <div
                      key={item.saved_stock_id || item.ticker}
                      style={watchlistItem}
                    >
                      <button
                        onClick={() => handleStockSearch(item.ticker)}
                        style={watchlistTicker}
                      >
                        {item.ticker}
                      </button>

                      <button
                        onClick={() => removeFromWatchlist(item.ticker)}
                        title="Remove stock"
                        style={iconButtonStyle}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

            </section>

            {/* SEARCH RESULTS */}

            {searchResult && (
              <section style={styles.panel}>

                <div style={resultHeader}>

                  <div>
                    <p style={resultLabel}>
                      HISTORICAL MARKET DATA
                    </p>

                    <h2 style={resultTicker}>
                      {searchResult.ticker}
                    </h2>

                    <p style={resultCompany}>
                      {searchResult.company_name || 'Stock information'}
                    </p>
                  </div>

                  <span style={dataRetrievedBadge}>
                    <Activity
                      size={12}
                      style={{
                        display: 'inline',
                        marginRight: '5px',
                      }}
                    />
                    DATA RETRIEVED
                  </span>

                </div>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                  gap: '12px',
                  marginBottom: '22px',
                }}>

                  <MetricCard
                    label="Records"
                    value={historicalData.length}
                  />

                  <MetricCard
                    label="Market"
                    value={preferences.preferred_market}
                  />

                  <MetricCard
                    label="Period"
                    value={preferences.default_period}
                  />

                </div>

                {historicalData.length === 0 ? (
                  <EmptyState
                    title="No historical records"
                    description="The API returned no historical price rows."
                  />
                ) : (
                  <div style={tableContainer}>

                    <table style={tableStyle}>

                      <thead>
                        <tr>
                          {[
                            'DATE',
                            'OPEN',
                            'HIGH',
                            'LOW',
                            'CLOSE',
                            'VOLUME',
                          ].map(heading => (
                            <th key={heading} style={tableHeaderStyle}>
                              {heading}
                            </th>
                          ))}
                        </tr>
                      </thead>

                      <tbody>
                        {historicalData.slice(0, 50).map((row, index) => (
                          <tr key={row.date || index}>
                            <td style={tableCellStyle}>
                              {formatDate(row.date)}
                            </td>

                            <td style={tableCellStyle}>
                              {formatPrice(row.open)}
                            </td>

                            <td style={tableCellStyle}>
                              {formatPrice(row.high)}
                            </td>

                            <td style={tableCellStyle}>
                              {formatPrice(row.low)}
                            </td>

                            <td style={{
                              ...tableCellStyle,
                              fontWeight: 800,
                              color: Number(row.close) >= Number(row.open)
                                ? colors.green
                                : colors.red,
                            }}>
                              {formatPrice(row.close)}
                            </td>

                            <td style={tableCellStyle}>
                              {Number(row.volume || 0).toLocaleString('en-IN')}
                            </td>
                          </tr>
                        ))}
                      </tbody>

                    </table>
                  </div>
                )}

                <p style={tableFootnote}>
                  Showing up to 50 historical records returned by the backend.
                </p>

              </section>
            )}

            {!searchResult && (
              <section style={emptyWelcome}>

                <div style={welcomeIcon}>
                  <TrendingUp size={23} />
                </div>

                <h3 style={welcomeTitle}>
                  Ready for market analysis
                </h3>

                <p style={welcomeDescription}>
                  Search a stock ticker to retrieve its historical data.
                </p>

              </section>
            )}

          </div>
        )}

        {/* RESEARCH HISTORY */}

        {activeTab === 'history' && (
          <section style={styles.panel}>

            <div style={sectionHeaderRow}>

              <div>
                <h2 style={sectionTitle}>
                  Research History
                </h2>

                <p style={sectionDescription}>
                  Your previous stock research requests.
                </p>
              </div>

              <button
                onClick={fetchHistory}
                style={refreshButton}
              >
                <RefreshCw size={14} />
                Refresh
              </button>

            </div>

            {history.length === 0 ? (
              <EmptyState
                title="No research history yet"
                description="Your stock searches will appear here."
              />
            ) : (
              <div style={{ overflowX: 'auto' }}>

                <table style={tableStyle}>

                  <thead>
                    <tr>
                      {[
                        'TASK ID',
                        'TICKER',
                        'MARKET',
                        'PERIOD',
                        'STATUS',
                        'DATE',
                      ].map(item => (
                        <th key={item} style={tableHeaderStyle}>
                          {item}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {history.map(task => (
                      <tr key={task.task_id}>

                        <td style={tableCellStyle}>
                          #{task.task_id}
                        </td>

                        <td style={{
                          ...tableCellStyle,
                          fontWeight: 800,
                          color: colors.primary,
                        }}>
                          {task.ticker}
                        </td>

                        <td style={tableCellStyle}>
                          {task.market}
                        </td>

                        <td style={tableCellStyle}>
                          {task.requested_period}
                        </td>

                        <td style={{
                          ...tableCellStyle,
                          color: getStatusColor(task.status),
                          fontWeight: 800,
                        }}>
                          {task.status}
                        </td>

                        <td style={tableCellStyle}>
                          {formatDate(task.created_at)}
                        </td>

                      </tr>
                    ))}
                  </tbody>

                </table>
              </div>
            )}

          </section>
        )}

        {/* PREFERENCES */}

        {activeTab === 'preferences' && (
          <section style={{
            ...styles.panel,
            maxWidth: '650px',
          }}>

            <div style={{
              display: 'flex',
              gap: '12px',
              alignItems: 'center',
              marginBottom: '25px',
            }}>
              <Settings size={20} color={colors.primary} />

              <div>
                <h2 style={sectionTitle}>
                  Workspace Preferences
                </h2>

                <p style={sectionDescription}>
                  Configure your default market data settings.
                </p>
              </div>
            </div>

            <form
              onSubmit={handleSavePreferences}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '22px',
              }}
            >

              <div>
                <label style={preferenceLabel}>
                  Default Stock Exchange
                </label>

                <select
                  style={styles.input}
                  value={preferences.preferred_market}
                  onChange={e => setPreferences({
                    ...preferences,
                    preferred_market: e.target.value,
                  })}
                >
                  <option value="NSE">NSE — National Stock Exchange</option>
                  <option value="BSE">BSE — Bombay Stock Exchange</option>
                  <option value="US">US — United States Market</option>
                </select>
              </div>

              <div>
                <label style={preferenceLabel}>
                  Historical Data Period
                </label>

                <select
                  style={styles.input}
                  value={preferences.default_period}
                  onChange={e => setPreferences({
                    ...preferences,
                    default_period: e.target.value,
                  })}
                >
                  <option value="1mo">1 Month</option>
                  <option value="3mo">3 Months</option>
                  <option value="6mo">6 Months</option>
                  <option value="1y">1 Year</option>
                  <option value="2y">2 Years</option>
                  <option value="5y">5 Years</option>
                  <option value="10y">10 Years</option>
                  <option value="ytd">Year to Date</option>
                  <option value="max">Maximum Available</option>
                </select>
              </div>

              <button
                type="submit"
                style={{
                  ...styles.button,
                  alignSelf: 'flex-start',
                  padding: '14px 25px',
                }}
              >
                SAVE PREFERENCES
              </button>

            </form>
          </section>
        )}

        {/* FOOTER */}

        <footer style={dashboardFooter}>
          <span>
            QUANT ANALYST HUB • MARKET RESEARCH PLATFORM
          </span>

          <span>
            POWERED BY FASTAPI & POSTGRESQL
          </span>
        </footer>

      </main>
    </div>
  );
}

// ======================================================
// REUSABLE DASHBOARD COMPONENTS
// ======================================================

function SummaryCard({ icon: Icon, label, value, color }) {
  return (
    <div style={{
      ...styles.panel,
      display: 'flex',
      alignItems: 'center',
      gap: '15px',
    }}>
      <div style={{
        background: '#EAF2FF',
        color,
        borderRadius: '12px',
        padding: '12px',
      }}>
        <Icon size={21} />
      </div>

      <div>
        <p style={summaryLabel}>
          {label}
        </p>

        <h3 style={summaryValue}>
          {value}
        </h3>
      </div>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div style={metricCardStyle}>
      <p style={metricLabel}>
        {label}
      </p>

      <p style={metricValue}>
        {value}
      </p>
    </div>
  );
}

function EmptyState({ title, description }) {
  return (
    <div style={emptyStateStyle}>
      <Database
        size={23}
        color={colors.subtle}
        style={{ marginBottom: '10px' }}
      />

      <p style={emptyStateTitle}>
        {title}
      </p>

      <p style={emptyStateDescription}>
        {description}
      </p>
    </div>
  );
}

// ======================================================
// AUTHENTICATION STYLES
// ======================================================

const authPage = {
  minHeight: '100vh',
  width: '100%',
  background: '#F3F7FD',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '30px',
  boxSizing: 'border-box',
  fontFamily: 'Inter, Arial, sans-serif',
};

const authContainer = {
  width: '100%',
  maxWidth: '1320px',
  minHeight: '680px',
  display: 'flex',
  flexWrap: 'wrap',
  background: '#FFFFFF',
  borderRadius: '24px',
  overflow: 'hidden',
  boxShadow: '0 20px 70px rgba(35,75,130,0.10)',
  border: '1px solid #E5ECF6',
};

const authLeft = {
  flex: '1 1 480px',
  minWidth: 0,
  background: 'linear-gradient(145deg, #EDF5FF, #F8FBFF)',
  padding: '55px',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  boxSizing: 'border-box',
};

const authRight = {
  flex: '0 1 480px',
  minWidth: 'min(100%, 340px)',
  padding: '55px 45px',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  boxSizing: 'border-box',
  background: '#FFFFFF',
};

const authFormContainer = {
  maxWidth: '380px',
  width: '100%',
  margin: '0 auto',
};

const brandRow = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
};

const brandIcon = {
  width: '43px',
  height: '43px',
  borderRadius: '13px',
  background: '#2167E8',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: '#FFFFFF',
  boxShadow: '0 6px 15px rgba(33,103,232,0.25)',
};

const brandName = {
  color: '#17345D',
  fontSize: '15px',
  fontWeight: 900,
  letterSpacing: '0.5px',
};

const brandSubtitle = {
  color: '#7790B0',
  fontSize: '9px',
  letterSpacing: '2px',
  marginTop: '4px',
  fontWeight: 700,
};

const eyebrow = {
  display: 'inline-block',
  background: '#DCEAFF',
  color: '#2167E8',
  padding: '8px 13px',
  borderRadius: '30px',
  fontSize: '10px',
  fontWeight: 800,
  letterSpacing: '1px',
  marginBottom: '22px',
};

const heroTitle = {
  fontSize: 'clamp(32px, 4vw, 48px)',
  lineHeight: 1.18,
  color: '#17345D',
  fontWeight: 900,
  letterSpacing: '-1.5px',
  margin: '0 0 20px',
};

const heroDescription = {
  fontSize: '14px',
  lineHeight: 1.9,
  color: '#71839D',
  maxWidth: '390px',
  margin: 0,
};

const marketPreview = {
  background: 'rgba(255,255,255,0.85)',
  border: '1px solid #DFEAF8',
  borderRadius: '18px',
  padding: '24px',
  marginTop: '45px',
  boxShadow: '0 10px 30px rgba(39,91,160,0.05)',
};

const marketPreviewHeader = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: '10px',
};

const previewLabel = {
  color: '#8295B0',
  fontSize: '10px',
  fontWeight: 800,
  letterSpacing: '1px',
  margin: '0 0 9px',
};

const previewTitle = {
  color: '#17345D',
  fontSize: '20px',
  margin: 0,
};

const previewIcon = {
  background: '#E5F1FF',
  color: '#2167E8',
  padding: '11px',
  borderRadius: '12px',
};

const barChart = {
  height: '95px',
  display: 'flex',
  alignItems: 'flex-end',
  gap: '9px',
  paddingTop: '18px',
};

const previewFootnote = {
  fontSize: '10px',
  color: '#91A1B7',
  margin: '13px 0 0',
};

const leftFooter = {
  color: '#91A1B7',
  fontSize: '10px',
  margin: '35px 0 0',
  letterSpacing: '0.5px',
};

const authLockIcon = {
  width: '48px',
  height: '48px',
  background: '#EAF2FF',
  borderRadius: '14px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: '#2167E8',
  marginBottom: '27px',
};

const authHeading = {
  color: '#17345D',
  fontSize: '29px',
  fontWeight: 900,
  letterSpacing: '-0.7px',
  margin: '0 0 10px',
};

const authDescription = {
  color: '#8291A7',
  fontSize: '13px',
  lineHeight: 1.7,
  margin: '0 0 32px',
};

const authForm = {
  display: 'flex',
  flexDirection: 'column',
  gap: '17px',
};

const authLabel = {
  display: 'block',
  color: '#61748F',
  fontSize: '10px',
  fontWeight: 800,
  letterSpacing: '1px',
  marginBottom: '9px',
};

const authField = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  background: '#F7F9FC',
  border: '1px solid #E3EAF3',
  borderRadius: '10px',
  padding: '14px',
};

const authInput = {
  background: 'transparent',
  border: 'none',
  outline: 'none',
  color: '#17345D',
  fontSize: '13px',
  flex: 1,
  minWidth: 0,
};

const passwordToggle = {
  border: 'none',
  background: 'transparent',
  color: '#91A1B7',
  cursor: 'pointer',
  display: 'flex',
};

const authSubmitButton = {
  background: 'linear-gradient(100deg, #2167E8, #3988F5)',
  color: '#FFFFFF',
  border: 'none',
  borderRadius: '11px',
  padding: '16px',
  marginTop: '8px',
  fontSize: '12px',
  fontWeight: 800,
  letterSpacing: '0.7px',
  cursor: 'pointer',
  boxShadow: '0 7px 18px rgba(33,103,232,0.22)',
};

const dividerRow = {
  display: 'flex',
  alignItems: 'center',
  gap: '14px',
  margin: '25px 0',
};

const dividerLine = {
  height: '1px',
  background: '#E8EDF5',
  flex: 1,
};

const dividerText = {
  color: '#A0AEC0',
  fontSize: '10px',
  fontWeight: 700,
};

const googleButton = {
  width: '100%',
  padding: '14px',
  border: '1px solid #E1E8F2',
  borderRadius: '11px',
  background: '#FFFFFF',
  color: '#344A68',
  fontSize: '12px',
  fontWeight: 700,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '12px',
};

const googleLetter = {
  color: '#4285F4',
  fontSize: '17px',
  fontWeight: 900,
};

const authSwitchText = {
  textAlign: 'center',
  color: '#8291A7',
  fontSize: '12px',
  marginTop: '30px',
};

const authSwitchButton = {
  border: 'none',
  background: 'transparent',
  color: '#2167E8',
  fontWeight: 800,
  marginLeft: '6px',
  cursor: 'pointer',
  fontSize: '12px',
};

const authFooter = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '7px',
  marginTop: '45px',
  color: '#A0AEC0',
  fontSize: '10px',
};

// ======================================================
// DASHBOARD STYLES
// ======================================================

const sidebarStyle = {
  width: '245px',
  minWidth: '220px',
  background: '#FFFFFF',
  borderRight: '1px solid #E3EAF3',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  padding: '25px 16px',
  boxSizing: 'border-box',
};

const sidebarBrand = {
  display: 'flex',
  alignItems: 'center',
  gap: '11px',
  padding: '5px 8px',
  marginBottom: '40px',
};

const sidebarBrandIcon = {
  background: '#EAF2FF',
  padding: '9px',
  borderRadius: '10px',
  color: '#2167E8',
};

const sidebarBrandName = {
  fontWeight: 900,
  fontSize: '12px',
  letterSpacing: '1px',
  color: '#17345D',
};

const sidebarBrandSubtitle = {
  fontSize: '9px',
  color: '#91A1B7',
  letterSpacing: '1.5px',
  marginTop: '3px',
};

const sidebarLabel = {
  ...styles.label,
  paddingLeft: '12px',
  marginBottom: '12px',
};

const sidebarNav = {
  display: 'flex',
  flexDirection: 'column',
  gap: '6px',
};

const navButton = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  padding: '13px 14px',
  border: 'none',
  borderRadius: '10px',
  textAlign: 'left',
  fontSize: '12px',
  fontWeight: 700,
  cursor: 'pointer',
};

const systemCard = {
  ...styles.panel,
  marginTop: '35px',
  padding: '15px',
  background: '#F5F9FF',
  boxShadow: 'none',
};

const systemHeading = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  color: '#16845B',
  fontSize: '11px',
  fontWeight: 800,
};

const systemText = {
  fontSize: '11px',
  color: '#61748F',
  margin: '9px 0 0',
};

const systemSubtext = {
  fontSize: '10px',
  color: '#91A1B7',
  margin: '5px 0 0',
};

const signedInCard = {
  borderTop: '1px solid #E3EAF3',
  padding: '17px 8px',
  marginBottom: '10px',
};

const signedInLabel = {
  fontSize: '10px',
  color: '#91A1B7',
  marginBottom: '5px',
};

const signedInEmail = {
  fontSize: '12px',
  fontWeight: 700,
  color: '#17345D',
  overflowWrap: 'anywhere',
};

const logoutButton = {
  ...styles.secondaryButton,
  width: '100%',
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  justifyContent: 'center',
  color: '#DC4C55',
};

const headerStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '15px',
  flexWrap: 'wrap',
  paddingBottom: '24px',
  borderBottom: '1px solid #E3EAF3',
  marginBottom: '27px',
};

const headerEyebrow = {
  color: '#2167E8',
  fontSize: '10px',
  fontWeight: 800,
  letterSpacing: '2px',
  margin: '0 0 7px',
};

const headerTitle = {
  fontSize: '23px',
  fontWeight: 900,
  color: '#17345D',
  margin: 0,
};

const headerDescription = {
  color: '#91A1B7',
  fontSize: '12px',
  marginTop: '7px',
};

const headerBadges = {
  display: 'flex',
  gap: '10px',
  alignItems: 'center',
};

const headerBadge = {
  ...styles.secondaryButton,
  display: 'flex',
  gap: '8px',
  alignItems: 'center',
  cursor: 'default',
};

const dashboardError = {
  ...alertStyle('error'),
  background: '#FFF0F0',
  border: '1px solid #FFD5D5',
  color: '#C03945',
};

const dashboardSuccess = {
  ...alertStyle('success'),
  background: '#ECFDF5',
  border: '1px solid #B7EBD1',
  color: '#16845B',
};

const sectionHeading = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  marginBottom: '10px',
};

const sectionTitle = {
  fontSize: '14px',
  fontWeight: 800,
  color: '#17345D',
  margin: 0,
};

const sectionDescription = {
  color: '#91A1B7',
  fontSize: '12px',
  margin: '0 0 20px',
};

const searchButton = {
  ...styles.button,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '9px',
  minWidth: '145px',
};

const addButton = {
  ...styles.secondaryButton,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: '#2167E8',
};

const sectionHeaderRow = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '12px',
  marginBottom: '18px',
};

const countText = {
  color: '#91A1B7',
  fontSize: '11px',
};

const watchlistItem = {
  display: 'flex',
  alignItems: 'center',
  gap: '9px',
  background: '#F7F9FC',
  border: '1px solid #E3EAF3',
  borderRadius: '10px',
  padding: '10px 12px',
};

const watchlistTicker = {
  background: 'none',
  border: 'none',
  color: '#2167E8',
  fontWeight: 800,
  fontSize: '12px',
  cursor: 'pointer',
};

const iconButtonStyle = {
  background: 'transparent',
  border: 'none',
  color: '#DC4C55',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const resultHeader = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  flexWrap: 'wrap',
  gap: '10px',
  marginBottom: '22px',
};

const resultLabel = {
  ...styles.label,
  marginBottom: '8px',
};

const resultTicker = {
  fontSize: '20px',
  color: '#17345D',
  margin: 0,
};

const resultCompany = {
  color: '#91A1B7',
  fontSize: '12px',
  marginTop: '5px',
};

const dataRetrievedBadge = {
  color: '#16845B',
  background: '#E9F8F1',
  borderRadius: '8px',
  padding: '8px 11px',
  fontSize: '10px',
  fontWeight: 800,
};

const tableContainer = {
  overflowX: 'auto',
  border: '1px solid #E3EAF3',
  borderRadius: '10px',
};

const tableStyle = {
  width: '100%',
  borderCollapse: 'collapse',
  minWidth: '550px',
  fontSize: '12px',
};

const tableHeaderStyle = {
  padding: '13px',
  textAlign: 'left',
  color: '#8291A7',
  fontSize: '10px',
  letterSpacing: '1px',
  borderBottom: '1px solid #E3EAF3',
  whiteSpace: 'nowrap',
  background: '#F7F9FC',
};

const tableCellStyle = {
  padding: '13px',
  color: '#61748F',
  borderBottom: '1px solid #EDF1F7',
  whiteSpace: 'nowrap',
};

const tableFootnote = {
  color: '#91A1B7',
  fontSize: '10px',
  marginTop: '12px',
};

const emptyWelcome = {
  ...styles.panel,
  textAlign: 'center',
  padding: '40px 20px',
};

const welcomeIcon = {
  width: '48px',
  height: '48px',
  margin: '0 auto 15px',
  background: '#EAF2FF',
  borderRadius: '14px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: '#2167E8',
};

const welcomeTitle = {
  fontSize: '14px',
  color: '#17345D',
  margin: '0 0 8px',
};

const welcomeDescription = {
  color: '#91A1B7',
  fontSize: '12px',
  margin: 0,
};

const refreshButton = {
  ...styles.secondaryButton,
  display: 'flex',
  alignItems: 'center',
  gap: '7px',
  color: '#2167E8',
};

const preferenceLabel = {
  ...styles.label,
  display: 'block',
  marginBottom: '10px',
};

const dashboardFooter = {
  borderTop: '1px solid #E3EAF3',
  marginTop: '35px',
  paddingTop: '18px',
  color: '#91A1B7',
  fontSize: '10px',
  display: 'flex',
  justifyContent: 'space-between',
  flexWrap: 'wrap',
  gap: '10px',
};

const summaryLabel = {
  color: '#91A1B7',
  fontSize: '10px',
  margin: '0 0 7px',
  fontWeight: 700,
  textTransform: 'uppercase',
};

const summaryValue = {
  fontSize: '20px',
  color: '#17345D',
  margin: 0,
  fontWeight: 900,
};

const metricCardStyle = {
  background: '#F7F9FC',
  border: '1px solid #E3EAF3',
  padding: '14px',
  borderRadius: '10px',
};

const metricLabel = {
  color: '#91A1B7',
  fontSize: '10px',
  margin: '0 0 8px',
  textTransform: 'uppercase',
  fontWeight: 700,
};

const metricValue = {
  fontSize: '17px',
  color: '#17345D',
  fontWeight: 800,
  margin: 0,
};

const emptyStateStyle = {
  textAlign: 'center',
  padding: '30px 15px',
  background: '#F7F9FC',
  borderRadius: '10px',
  border: '1px dashed #DCE5F0',
};

const emptyStateTitle = {
  fontSize: '13px',
  fontWeight: 700,
  color: '#17345D',
  margin: '0 0 7px',
};

const emptyStateDescription = {
  fontSize: '11px',
  color: '#91A1B7',
  margin: 0,
};

// ======================================================
// SHARED STYLE HELPERS
// ======================================================

function alertStyle(type) {
  const isError = type === 'error';

  return {
    background: isError ? '#FFF0F0' : '#ECFDF5',
    border: `1px solid ${isError ? '#FFD5D5' : '#B7EBD1'}`,
    color: isError ? '#C03945' : '#16845B',
    borderRadius: '10px',
    padding: '13px 15px',
    fontSize: '12px',
    marginBottom: '16px',
    position: 'relative',
    paddingRight: '35px',
  };
}

const alertCloseStyle = {
  position: 'absolute',
  right: '10px',
  top: '10px',
  border: 'none',
  background: 'transparent',
  color: 'inherit',
  cursor: 'pointer',
};
