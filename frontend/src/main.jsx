import { StrictMode, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

let googleCredentialHandler = null;

async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item) => item.msg).join(". ")
      : body.detail;
    throw new Error(detail || "Something went wrong. Please try again.");
  }

  return response.status === 204 ? null : response.json();
}

function AuthForm({ onLogin, googleClientId, googleConfigError }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [googleButtonError, setGoogleButtonError] = useState("");
  const googleButtonRef = useRef(null);

  googleCredentialHandler = async (credential) => {
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const result = await request("/api/auth/google", {
        method: "POST",
        body: JSON.stringify({ credential }),
      });
      onLogin(result.user);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (!googleClientId) return undefined;
    let active = true;
    let attempts = 0;
    let timeoutId;

    function renderGoogleButton() {
      if (!active || !googleButtonRef.current) return;
      if (!window.google?.accounts?.id) {
        if (attempts++ < 25) {
          timeoutId = window.setTimeout(renderGoogleButton, 200);
        } else {
          setGoogleButtonError("Google sign-in could not load. Check your connection and try again.");
        }
        return;
      }

      if (window.__stockResearchGoogleClientId !== googleClientId) {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: ({ credential }) => googleCredentialHandler?.(credential),
        });
        window.__stockResearchGoogleClientId = googleClientId;
      }
      googleButtonRef.current.replaceChildren();
      window.google.accounts.id.renderButton(googleButtonRef.current, {
        type: "standard",
        theme: "outline",
        size: "large",
        shape: "rectangular",
        text: mode === "login" ? "continue_with" : "signup_with",
        width: Math.min(360, googleButtonRef.current.clientWidth),
      });
    }

    renderGoogleButton();
    return () => {
      active = false;
      window.clearTimeout(timeoutId);
    };
  }, [googleClientId, mode]);

  function update(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  function switchMode(nextMode) {
    setMode(nextMode);
    setForm((current) => ({ ...current, password: "", confirm_password: "" }));
    setError("");
    setNotice("");
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    setBusy(true);
    try {
      if (mode === "register") {
        await request("/api/auth/register", {
          method: "POST",
          body: JSON.stringify(form),
        });
        setMode("login");
        setForm({ email: form.email, password: "", confirm_password: "" });
        setNotice("Your account is ready. Sign in to continue.");
      } else {
        const result = await request("/api/auth/login", {
          method: "POST",
          body: JSON.stringify(form),
        });
        onLogin(result.user);
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="intro">
        <p className="eyebrow">STOCK RESEARCH WORKSPACE</p>
        <h1>Research with clarity.</h1>
        <p className="intro-copy">
          Company fundamentals, market data, and your research history in one
          focused workspace.
        </p>
        <div className="feature-list">
          <span>01</span><p>Explore US, NSE, and BSE-listed companies</p>
          <span>02</span><p>Review fundamentals and historical performance</p>
          <span>03</span><p>Keep watchlists and research reports together</p>
        </div>
        <p className="auth-data-note">Market information powered by Yahoo Finance.</p>
      </section>

      <section className="auth-card">
        <div className="auth-brand"><div className="brand-mark">SR</div><span>Stock Research</span></div>
        <h2>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
        <p className="muted">
          {mode === "login"
            ? "Sign in to pick up where your research left off."
            : "Create an account to save your research and watchlists."}
        </p>
        <div className="switcher">
          <button className={mode === "login" ? "selected" : ""} onClick={() => switchMode("login")}>
            Sign in
          </button>
          <button className={mode === "register" ? "selected" : ""} onClick={() => switchMode("register")}>
            Register
          </button>
        </div>
        <form onSubmit={submit}>
          {mode === "register" && (
            <label>
              Full name
              <input name="full_name" required minLength="2" onChange={update} />
            </label>
          )}
          <label>
            Email address
            <input name="email" type="email" required value={form.email || ""} onChange={update} />
          </label>
          <label>
            Password
            <input name="password" type="password" required minLength="8" value={form.password || ""} onChange={update} />
          </label>
          {mode === "register" && (
            <label>
              Confirm password
              <input name="confirm_password" type="password" required minLength="8" value={form.confirm_password || ""} onChange={update} />
            </label>
          )}
          <button className="primary-button" disabled={busy}>
            {busy ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
        {googleClientId ? (
          <>
            <div className="auth-divider"><span>or continue with</span></div>
            <div className={`google-button-wrap ${busy ? "is-busy" : ""}`}>
              <div ref={googleButtonRef} />
              {googleButtonError && <p className="error" role="alert">{googleButtonError}</p>}
            </div>
          </>
        ) : (
          <p className="google-unavailable" role={googleConfigError ? "alert" : undefined}>
            {googleConfigError || "Google sign-in is not configured yet. Add GOOGLE_CLIENT_ID to backend/.env to enable it."}
          </p>
        )}
        {notice && <p className="notice">{notice}</p>}
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  );
}

function formatCurrency(value, currency) {
  if (value == null) return "Not available";
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: currency || "USD",
      notation: "compact",
      maximumFractionDigits: 2,
    }).format(value);
  } catch {
    return value.toLocaleString();
  }
}

function formatNumber(value, suffix = "") {
  return value == null
    ? "Not available"
    : `${new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value)}${suffix}`;
}

const dashboardTabs = [
  { id: "research", label: "Research", mark: "R" },
  { id: "watchlists", label: "Watchlists", mark: "W" },
  { id: "history", label: "Research history", mark: "H" },
  { id: "preferences", label: "Preferences", mark: "P" },
];

function Workspace({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState("research");
  const [query, setQuery] = useState("");
  const [ticker, setTicker] = useState("");
  const [period, setPeriod] = useState("1y");
  const [market, setMarket] = useState("US");
  const [watchlistName, setWatchlistName] = useState("My Watchlist");
  const [watchlistFilter, setWatchlistFilter] = useState("");
  const [matches, setMatches] = useState([]);
  const [savedStocks, setSavedStocks] = useState([]);
  const [researchHistory, setResearchHistory] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingWorkspace, setLoadingWorkspace] = useState(true);

  async function refreshHistory() {
    setResearchHistory(await request("/api/research/history"));
  }

  async function refreshSavedStocks() {
    setSavedStocks(await request("/api/stocks/saved"));
  }

  useEffect(() => {
    let active = true;
    Promise.all([
      request("/api/preferences"),
      request("/api/stocks/saved"),
      request("/api/research/history"),
    ])
      .then(([preferences, saved, history]) => {
        if (!active) return;
        setMarket(preferences.market);
        setPeriod(preferences.analysis_period);
        setSavedStocks(saved);
        setResearchHistory(history);
      })
      .catch((requestError) => {
        if (active) setError(requestError.message);
      })
      .finally(() => {
        if (active) setLoadingWorkspace(false);
      });
    return () => { active = false; };
  }, []);

  async function logout() {
    await request("/api/auth/logout", { method: "POST" });
    onLogout();
  }

  async function savePreferences(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    try {
      await request("/api/preferences", {
        method: "PUT",
        body: JSON.stringify({ market, analysis_period: period }),
      });
      setNotice("Your market and analysis period preferences were saved.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function search(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    setAnalysis(null);
    setBusy(true);
    try {
      const result = await request(
        `/api/stocks/search?q=${encodeURIComponent(query)}&market=${market}`,
      );
      setMatches(result.results);
      if (!result.results.length) setError("No matching stocks were found.");
    } catch (requestError) {
      setMatches([]);
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function analyzeStock(selectedTicker, selectedMarket = market) {
    setActiveTab("research");
    setError("");
    setNotice("");
    setAnalysis(null);
    setBusy(true);
    try {
      const result = await request("/api/research/fundamental", {
        method: "POST",
        body: JSON.stringify({ ticker: selectedTicker, market: selectedMarket, period }),
      });
      setAnalysis(result);
      setTicker(result.ticker);
      setMarket(result.market);
      try {
        await refreshHistory();
      } catch (historyError) {
        setError(`Analysis completed, but research history could not be refreshed: ${historyError.message}`);
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function analyze(event) {
    event.preventDefault();
    await analyzeStock(ticker);
  }

  async function saveStock() {
    if (!analysis) return;
    setError("");
    setNotice("");
    try {
      await request("/api/stocks/saved", {
        method: "POST",
        body: JSON.stringify({
          ticker: analysis.ticker,
          market: analysis.market,
          watchlist_name: watchlistName.trim() || "My Watchlist",
        }),
      });
      await refreshSavedStocks();
      setNotice(`${analysis.ticker} was saved to ${watchlistName.trim() || "My Watchlist"}.`);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function removeSavedStock(savedStockId) {
    setError("");
    try {
      await request(`/api/stocks/saved/${savedStockId}`, { method: "DELETE" });
      await refreshSavedStocks();
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function openSavedStock(stock) {
    setQuery(stock.ticker);
    setMarket(stock.market);
    setTicker(stock.ticker);
    await analyzeStock(stock.ticker, stock.market);
  }

  async function openResearchReport(taskId) {
    setError("");
    setBusy(true);
    try {
      const report = await request(`/api/research/history/${taskId}`);
      if (!report.result) {
        setError(report.error_message || "This research task has no completed report.");
        return;
      }
      setAnalysis(report.result);
      setActiveTab("research");
      setTicker(report.ticker);
      setMarket(report.market);
      setPeriod(report.requested_period);
      setQuery(report.ticker);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  const watchlistNames = [...new Set(savedStocks.map((stock) => stock.watchlist_name))];
  const visibleSavedStocks = watchlistFilter
    ? savedStocks.filter((stock) => stock.watchlist_name === watchlistFilter)
    : savedStocks;

  function handleTabKeyDown(event, currentIndex) {
    let nextIndex;
    if (event.key === "ArrowRight") nextIndex = (currentIndex + 1) % dashboardTabs.length;
    else if (event.key === "ArrowLeft") nextIndex = (currentIndex - 1 + dashboardTabs.length) % dashboardTabs.length;
    else if (event.key === "Home") nextIndex = 0;
    else if (event.key === "End") nextIndex = dashboardTabs.length - 1;
    else return;

    event.preventDefault();
    const tabs = event.currentTarget.parentElement.querySelectorAll('[role="tab"]');
    tabs[nextIndex]?.focus();
    setActiveTab(dashboardTabs[nextIndex].id);
  }

  return (
    <main className="workspace">
      <aside className="dashboard-sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark small">SR</div>
          <div><strong>Stock Research</strong><span>ANALYST WORKSPACE</span></div>
        </div>
        <p className="sidebar-section-label">WORKSPACE</p>
        <nav className="dashboard-tabs" role="tablist" aria-label="Dashboard sections">
          {dashboardTabs.map((tab, index) => {
            const count = tab.id === "watchlists"
              ? savedStocks.length
              : tab.id === "history"
                ? researchHistory.length
                : null;
            return (
              <button
                key={tab.id}
                id={`dashboard-tab-${tab.id}`}
                className={`dashboard-tab ${activeTab === tab.id ? "active" : ""}`}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                aria-controls={`dashboard-panel-${tab.id}`}
                tabIndex={activeTab === tab.id ? 0 : -1}
                onClick={() => setActiveTab(tab.id)}
                onKeyDown={(event) => handleTabKeyDown(event, index)}
              >
                <span className="dashboard-tab-icon" aria-hidden="true">{tab.mark}</span>
                <span className="dashboard-tab-label">{tab.label}</span>
                {count !== null && <span className="tab-count">{count}</span>}
              </button>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <span className="sidebar-footer-label">MARKET DATA</span>
          <strong>Yahoo Finance</strong>
          <span>Company and historical financial information</span>
        </div>
      </aside>
      <div className="dashboard-main">
      <header className="topbar">
        <div className="breadcrumb">
          <span>Workspace</span>
          <span aria-hidden="true">/</span>
          <strong>{dashboardTabs.find((tab) => tab.id === activeTab)?.label}</strong>
        </div>
        <div className="topbar-actions">
          <div className="workspace-user">
            <strong>{user.full_name}</strong>
            <span>{user.email}</span>
          </div>
          <button className="ghost-button" onClick={logout}>Sign out</button>
        </div>
      </header>
      <div className="dashboard-content">
      <section className="welcome-card">
        <p className="eyebrow">INVESTMENT RESEARCH WORKSPACE</p>
        <h1>Research dashboard</h1>
        <p className="muted">Review company fundamentals, saved stocks, and recent analysis.</p>
        <div className="welcome-meta">
          <span className="session-badge"><span /> Secure session</span>
          <span className="muted">{market} market · {period} analysis period</span>
        </div>
      </section>

      <section className="dashboard-overview" aria-label="Workspace overview">
        <div className="overview-card">
          <span>Saved stocks</span>
          <strong>{savedStocks.length}</strong>
          <small>{watchlistNames.length} watchlists</small>
        </div>
        <div className="overview-card">
          <span>Research reports</span>
          <strong>{researchHistory.length}</strong>
          <small>{researchHistory.filter((task) => task.status === "completed").length} completed</small>
        </div>
        <div className="overview-card">
          <span>Selected market</span>
          <strong>{market}</strong>
          <small>{period} analysis period</small>
        </div>
      </section>

      {error && <p className="error dashboard-feedback" role="alert">{error}</p>}
      {notice && <p className="notice dashboard-feedback" role="status">{notice}</p>}

      <section
        className="research-panel preferences-panel"
        id="dashboard-panel-preferences"
        role="tabpanel"
        aria-labelledby="dashboard-tab-preferences"
        tabIndex={0}
        hidden={activeTab !== "preferences"}
      >
        <div className="section-heading">
          <div>
            <p className="eyebrow">WORKSPACE SETTINGS</p>
            <h2>Research preferences</h2>
          </div>
        </div>
        <form className="preferences-form" onSubmit={savePreferences}>
          <label>
            Market
            <select value={market} onChange={(event) => setMarket(event.target.value)}>
              <option value="US">United States</option>
              <option value="NSE">India - NSE</option>
              <option value="BSE">India - BSE</option>
            </select>
          </label>
          <label>
            Analysis period
            <select value={period} onChange={(event) => setPeriod(event.target.value)}>
              <option value="1mo">1 month</option>
              <option value="3mo">3 months</option>
              <option value="6mo">6 months</option>
              <option value="1y">1 year</option>
              <option value="2y">2 years</option>
              <option value="5y">5 years</option>
              <option value="10y">10 years</option>
              <option value="max">Maximum available</option>
            </select>
          </label>
          <button className="primary-button" disabled={busy}>Save preferences</button>
        </form>
      </section>

      <div className="dashboard-list-panels">
        <section
          className="research-panel"
          id="dashboard-panel-watchlists"
          role="tabpanel"
          aria-labelledby="dashboard-tab-watchlists"
          tabIndex={0}
          hidden={activeTab !== "watchlists"}
        >
          <div className="section-heading">
            <div>
              <p className="eyebrow">SAVED STOCKS</p>
              <h2>Watchlists</h2>
            </div>
            {watchlistNames.length > 0 && (
              <select
                className="list-filter"
                aria-label="Filter watchlist"
                value={watchlistFilter}
                onChange={(event) => setWatchlistFilter(event.target.value)}
              >
                <option value="">All watchlists</option>
                {watchlistNames.map((name) => <option key={name} value={name}>{name}</option>)}
              </select>
            )}
          </div>
          {visibleSavedStocks.length ? (
            <div className="saved-stock-list">
              {visibleSavedStocks.map((stock) => (
                <div className="saved-stock-row" key={stock.saved_stock_id}>
                  <button disabled={busy} onClick={() => openSavedStock(stock)}>
                    <strong>{stock.ticker}</strong><small>{stock.watchlist_name} · {stock.market}</small>
                  </button>
                  <button
                    className="remove-button"
                    aria-label={`Remove ${stock.ticker}`}
                    onClick={() => removeSavedStock(stock.saved_stock_id)}
                  >Remove</button>
                </div>
              ))}
            </div>
          ) : <p className="muted">No saved stocks yet. Save a stock after analyzing it.</p>}
        </section>

        <section
          className="research-panel"
          id="dashboard-panel-history"
          role="tabpanel"
          aria-labelledby="dashboard-tab-history"
          tabIndex={0}
          hidden={activeTab !== "history"}
        >
          <div className="section-heading">
            <div>
              <p className="eyebrow">RECENT ACTIVITY</p>
              <h2>Research history</h2>
            </div>
          </div>
          {researchHistory.length ? (
            <div className="saved-stock-list">
              {researchHistory.map((task) => (
                <button
                  className="history-row"
                  key={task.task_id}
                  disabled={busy || task.status !== "completed"}
                  onClick={() => openResearchReport(task.task_id)}
                >
                  <span><strong>{task.ticker}</strong><small>{task.market} · {task.requested_period}</small></span>
                  <span className={`task-status ${task.status}`}>{task.status}</span>
                </button>
              ))}
            </div>
          ) : <p className="muted">Completed analyses will appear here.</p>}
        </section>
      </div>

      <div
        className="dashboard-tab-panel"
        id="dashboard-panel-research"
        role="tabpanel"
        aria-labelledby="dashboard-tab-research"
        tabIndex={0}
        hidden={activeTab !== "research"}
      >
      <section className="research-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">FUNDAMENTAL ANALYSIS</p>
            <h2>Research a public company</h2>
          </div>
          <span className="provider-badge">Powered by yfinance</span>
        </div>
        <form className="search-market-form" onSubmit={search}>
          <label>
            Company name or ticker
            <input
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setTicker("");
                setMatches([]);
              }}
              placeholder="Search a company or ticker (e.g. Apple or AAPL)"
              required
              minLength="2"
            />
          </label>
          <button className="primary-button" disabled={busy}>
            {busy ? "Searching..." : "Search stocks"}
          </button>
        </form>

        {matches.length > 0 && (
          <div className="stock-results" aria-label="Stock search results">
            {matches.map((stock) => (
              <button
                className={`stock-result ${ticker === stock.ticker ? "active" : ""}`}
                key={`${stock.ticker}-${stock.exchange || ""}`}
                onClick={() => {
                  setTicker(stock.ticker);
                  setQuery(`${stock.name} (${stock.ticker})`);
                  setMatches([]);
                  setError("");
                }}
              >
                <span><strong>{stock.name}</strong><small>{stock.exchange || "Exchange unavailable"}</small></span>
                <b>{stock.ticker}</b>
              </button>
            ))}
          </div>
        )}

        {ticker && (
          <form className="analysis-form" onSubmit={analyze}>
            <p className="selected-stock">{ticker} · {market} · {period}</p>
            <button type="submit" className="primary-button" disabled={busy}>
              {busy ? "Analyzing..." : `Analyze ${ticker}`}
            </button>
          </form>
        )}
        {loadingWorkspace && <p className="muted">Loading your saved workspace...</p>}
      </section>

      {analysis && (
        <section className="analysis-results">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{analysis.ticker} · {analysis.market} · FUNDAMENTAL ANALYSIS</p>
              <h2>{analysis.company_name}</h2>
            </div>
            <div className="analysis-actions">
              <p className="data-timestamp">Retrieved {new Date(analysis.source.retrieved_at).toLocaleString()}</p>
              <input
                aria-label="Watchlist name"
                value={watchlistName}
                onChange={(event) => setWatchlistName(event.target.value)}
                placeholder="Watchlist name"
                maxLength="60"
              />
              <button className="ghost-button" disabled={busy} onClick={saveStock}>Save to watchlist</button>
            </div>
          </div>

          <div className="metric-grid">
            <Metric label="Market cap" value={formatCurrency(analysis.metrics.market_cap, analysis.currency)} />
            <Metric label="Latest price" value={formatCurrency(analysis.metrics.current_price, analysis.currency)} />
            <Metric label="Trailing P/E" value={formatNumber(analysis.metrics.trailing_pe)} />
            <Metric label="Price to book" value={formatNumber(analysis.metrics.price_to_book)} />
            <Metric label="Return on equity" value={formatNumber(analysis.metrics.return_on_equity_percent, "%")} />
            <Metric label="Profit margin" value={formatNumber(analysis.metrics.profit_margin_percent, "%")} />
            <Metric label="Operating margin" value={formatNumber(analysis.metrics.operating_margin_percent, "%")} />
            <Metric label="Revenue growth" value={formatNumber(analysis.metrics.revenue_growth_percent, "%")} />
            <Metric label="Net income growth" value={formatNumber(analysis.metrics.net_income_growth_percent, "%")} />
            <Metric label="Debt to equity" value={formatNumber(analysis.metrics.debt_to_equity_percent, "%")} />
            <Metric label="Net debt" value={formatCurrency(analysis.metrics.net_debt, analysis.currency)} />
            <Metric label="Current ratio" value={formatNumber(analysis.metrics.current_ratio)} />
          </div>

          <div className="analysis-columns">
            <section className="result-card">
              <h3>Agent findings</h3>
              {analysis.findings.length
                ? <ul>{analysis.findings.map((item) => <li key={item}>{item}</li>)}</ul>
                : <p className="muted">No findings available.</p>}
            </section>
            <section className="result-card">
              <h3>Data gaps and limitations</h3>
              {[...analysis.data_gaps, ...analysis.market_data.warnings].length
                ? <ul>{[...analysis.data_gaps, ...analysis.market_data.warnings].map((item) => <li key={item}>{item}</li>)}</ul>
                : <p className="muted">No data-quality issues were reported.</p>}
            </section>
          </div>

          <section className="result-card peer-history">
            <h3>Peer comparison {analysis.industry ? `· ${analysis.industry}` : ""}</h3>
            {analysis.peer_comparisons.length ? (
              <div className="table-scroll">
                <table>
                  <thead><tr><th>Company</th><th>P/E</th><th>P/B</th><th>ROE</th><th>Profit margin</th><th>Debt/equity</th></tr></thead>
                  <tbody>
                    <tr className="subject-company">
                      <td>{analysis.company_name} ({analysis.ticker})</td>
                      <td>{formatNumber(analysis.metrics.trailing_pe)}</td>
                      <td>{formatNumber(analysis.metrics.price_to_book)}</td>
                      <td>{formatNumber(analysis.metrics.return_on_equity_percent, "%")}</td>
                      <td>{formatNumber(analysis.metrics.profit_margin_percent, "%")}</td>
                      <td>{formatNumber(analysis.metrics.debt_to_equity_percent, "%")}</td>
                    </tr>
                    {analysis.peer_comparisons.map((peer) => (
                      <tr key={peer.ticker}>
                        <td>{peer.company_name} ({peer.ticker})</td>
                        <td>{formatNumber(peer.trailing_pe)}</td>
                        <td>{formatNumber(peer.price_to_book)}</td>
                        <td>{formatNumber(peer.return_on_equity_percent, "%")}</td>
                        <td>{formatNumber(peer.profit_margin_percent, "%")}</td>
                        <td>{formatNumber(peer.debt_to_equity_percent, "%")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <p className="muted">Comparable-company ratios were not available. See the data gaps above.</p>}
          </section>

          <section className="result-card financial-history">
            <h3>Reported financial performance</h3>
            {analysis.historical_financials.length ? (
              <div className="table-scroll">
                <table>
                  <thead><tr><th>Period</th><th>Revenue</th><th>Net income</th><th>Total debt</th><th>Cash</th></tr></thead>
                  <tbody>
                    {analysis.historical_financials.map((row) => (
                      <tr key={row.period}>
                        <td>{row.period}</td>
                        <td>{formatCurrency(row.revenue, analysis.currency)}</td>
                        <td>{formatCurrency(row.net_income, analysis.currency)}</td>
                        <td>{formatCurrency(row.total_debt, analysis.currency)}</td>
                        <td>{formatCurrency(row.cash, analysis.currency)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <p className="muted">Annual financial statements were not available.</p>}
          </section>

          <section className="result-card price-history">
            <div className="section-heading">
              <h3>Recent OHLCV prices</h3>
              <span>{analysis.market_data.period} · {analysis.currency || "currency unavailable"}</span>
            </div>
            <div className="table-scroll">
              <table>
                <thead><tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th></tr></thead>
                <tbody>
                  {analysis.market_data.prices.slice(-5).reverse().map((row) => (
                    <tr key={row.date}>
                      <td>{row.date}</td>
                      <td>{formatNumber(row.open)}</td>
                      <td>{formatNumber(row.high)}</td>
                      <td>{formatNumber(row.low)}</td>
                      <td>{formatNumber(row.close)}</td>
                      <td>{row.volume == null ? "Not available" : row.volume.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <p className="source-note">
            Source: <a href={analysis.source.url} target="_blank" rel="noreferrer">{analysis.source.provider}</a>.
            Historical data and calculated metrics are informational, not investment advice.
          </p>
        </section>
      )}
      </div>
      </div>
      </div>
    </main>
  );
}

function Metric({ label, value }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong></div>;
}

function App() {
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [googleClientId, setGoogleClientId] = useState("");
  const [googleConfigError, setGoogleConfigError] = useState("");

  useEffect(() => {
    request("/api/auth/me")
      .then(setUser)
      .catch(() => {})
      .finally(() => setCheckingSession(false));
    request("/api/auth/google/config")
      .then((config) => setGoogleClientId(config.enabled ? config.client_id : ""))
      .catch((requestError) => setGoogleConfigError(requestError.message));
  }, []);

  if (checkingSession) return <div className="loading">Loading workspace...</div>;
  return user
    ? <Workspace user={user} onLogout={() => setUser(null)} />
    : <AuthForm onLogin={setUser} googleClientId={googleClientId} googleConfigError={googleConfigError} />;
}

createRoot(document.getElementById("root")).render(
  <StrictMode><App /></StrictMode>,
);
