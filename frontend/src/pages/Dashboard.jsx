
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";
import {
  getResearchHistory,
  getResearchReport,
  createResearchTask,
  getStockHistory,
  searchStocks,
  getPreferences,
} from "../services/authService";

/* ── tiny helper ── */
const getStatusClass = (s) =>
  s === "COMPLETED" ? "status-completed"
  : s === "PROCESSING" ? "status-processing"
  : s === "FAILED"    ? "status-failed"
  : "status-pending";

const formatDate = (d) =>
  d
    ? new Date(d).toLocaleDateString("en-IN", {
        day: "2-digit", month: "short", year: "numeric",
      })
    : "—";

/* ── AI agents listed for the overview cards ── */
const AI_AGENTS = [
  {
    icon: "📊",
    label: "Fundamental",
    desc: "P/E, EPS, revenue growth, balance-sheet health",
    color: "#4A9EFF",
  },
  {
    icon: "📈",
    label: "Technical",
    desc: "SMA, EMA, RSI, MACD signals & trend detection",
    color: "#C6F36B",
  },
  {
    icon: "📰",
    label: "News Sentiment",
    desc: "NLP scoring of live market news & announcements",
    color: "#F5C76A",
  },
  {
    icon: "🛡️",
    label: "Risk Analysis",
    desc: "Volatility, beta, drawdown & risk-adjusted returns",
    color: "#FF8791",
  },
];

function Dashboard() {
  const navigate = useNavigate();

  /* state */
  const [researchHistory, setResearchHistory]   = useState([]);
  const [loading, setLoading]                   = useState(true);
  const [error, setError]                       = useState("");
  const [message, setMessage]                   = useState("");

  const [selectedReport, setSelectedReport]     = useState(null);
  const [reportLoading, setReportLoading]       = useState(false);

  const [searchQuery, setSearchQuery]           = useState("");
  const [searchResults, setSearchResults]       = useState([]);
  const [searchLoading, setSearchLoading]       = useState(false);
  const [selectedStock, setSelectedStock]       = useState(null);

  const [analysisPeriod, setAnalysisPeriod]     = useState("1y");
  const [researchLoading, setResearchLoading]   = useState(false);

  /* auth */
  const token  = sessionStorage.getItem("access_token");
  const user   = JSON.parse(sessionStorage.getItem("user") || "null");
  const userId = user?.user_id;

  /* load history */
  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await getResearchHistory();
      setResearchHistory(data);
    } catch (err) {
      if (err.response?.status === 401) {
        sessionStorage.removeItem("access_token");
        sessionStorage.removeItem("user");
        navigate("/login", { replace: true });
        return;
      }
      setError(err.response?.data?.detail || "Unable to load research history.");
    } finally {
      setLoading(false);
    }
  };

  /* boot */
  useEffect(() => {
    if (!token || !user) {
      navigate("/login", { replace: true });
      return;
    }
    fetchHistory();

    const loadPrefs = async () => {
      try {
        const data = await getPreferences();
        if (data.preferred_analysis_period) setAnalysisPeriod(data.preferred_analysis_period);
      } catch {
        // use defaults if preferences fail
      }
    };
    loadPrefs();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigate, token, userId]);

  const logout = () => {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    navigate("/login");
  };

  /* search */
  const handleStockSearch = async () => {
    if (searchQuery.trim().length < 2) {
      setError("Enter at least 2 characters to search.");
      return;
    }
    try {
      setSearchLoading(true);
      setError("");
      setMessage("");
      setSelectedStock(null);
      setSearchResults([]);
      const data = await searchStocks(searchQuery.trim());
      setSearchResults(data.results || []);
      if (!data.results?.length) setMessage("No matching NSE or BSE stocks found.");
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to search stocks.");
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSelectStock = (stock) => {
    setSelectedStock(stock);
    setMessage(`${stock.company_name} selected.`);
    setError("");
  };

  /* start research */
  const handleStartResearch = async () => {
    if (!selectedStock) { setError("Please search and select a stock first."); return; }
    try {
      setResearchLoading(true);
      setError("");
      setMessage("Fetching historical data…");

      const stockData = await getStockHistory(
        selectedStock.ticker, selectedStock.market, analysisPeriod,
      );

      if (!stockData.success || !stockData.data?.length)
        throw new Error("No valid historical stock data found.");

      await createResearchTask({
        company_name:    selectedStock.company_name,
        ticker:          selectedStock.ticker,
        market:          selectedStock.market,
        analysis_period: analysisPeriod,
      });

      setMessage(
        `✓ Research task created — ${stockData.total_records} records retrieved for ${selectedStock.company_name}.`,
      );
      setSearchQuery("");
      setSearchResults([]);
      setSelectedStock(null);
      await fetchHistory();
    } catch (err) {
      if (err.response?.status === 401) {
        sessionStorage.removeItem("access_token");
        sessionStorage.removeItem("user");
        navigate("/login", { replace: true });
        return;
      }
      setError(err.response?.data?.detail || err.message || "Unable to start research.");
      setMessage("");
    } finally {
      setResearchLoading(false);
    }
  };

  /* open report */
  const openReport = async (taskId) => {
    try {
      setReportLoading(true);
      setError("");
      const report = await getResearchReport(taskId);
      setSelectedReport(report);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to open report.");
    } finally {
      setReportLoading(false);
    }
  };

  if (!user) return null;

  /* ── derived stats ── */
  const stats = [
    { label: "Total Research",   value: researchHistory.length,                                       accent: "#4A9EFF" },
    { label: "Completed",        value: researchHistory.filter(t => t.status === "COMPLETED").length,  accent: "#C6F36B" },
    { label: "Processing",       value: researchHistory.filter(t => t.status === "PROCESSING").length, accent: "#F5C76A" },
    { label: "Failed",           value: researchHistory.filter(t => t.status === "FAILED").length,     accent: "#FF8791" },
  ];

  return (
    <DashboardLayout user={user} onLogout={logout}>
      <div className="db-page">

        {/* ── TOP HEADER ── */}
        <header className="db-header">
          <div>
            <p className="db-eyebrow">AI-POWERED MARKET ANALYSIS &amp; RESEARCH</p>
            <h1 className="db-title">Welcome back, <span>{user.full_name}</span></h1>
            <p className="db-subtitle">
              Your intelligent multi-agent research workspace
            </p>
          </div>
          <div className="db-header-badge">
            <span className="db-live-dot" />
            LIVE
          </div>
        </header>

        {/* ── STAT CARDS ── */}
        <section className="db-stats">
          {stats.map((s) => (
            <div className="db-stat-card" key={s.label}>
              <p className="db-stat-label">{s.label}</p>
              <p className="db-stat-value" style={{ color: s.accent }}>{s.value}</p>
            </div>
          ))}
        </section>

        {/* ── MAIN GRID ── */}
        <div className="db-grid">

          {/* ── LEFT COLUMN ── */}
          <div className="db-col-left">

            {/* Search card */}
            <div className="db-card">
              <div className="db-card-header">
                <div>
                  <p className="db-eyebrow">MARKET DATA</p>
                  <h2>New Stock Research</h2>
                  <p className="db-card-desc">
                    Search any company by name or ticker symbol (NSE / BSE)
                  </p>
                </div>
                <span className="db-card-icon">🔍</span>
              </div>

              <div className="db-search-row">
                <input
                  className="db-input"
                  type="search"
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck="false"
                  name="stock-search"
                  id="stock-search"
                  placeholder="e.g. Tata Consultancy Services or TCS"
                  value={searchQuery}
                  onChange={(e) => {
                    const val = e.target.value;
                    setSearchQuery(val);
                    if (val.trim() === "") {
                      setSearchResults([]);
                      setSelectedStock(null);
                      setMessage("");
                      setError("");
                    }
                  }}
                  onKeyDown={(e) => e.key === "Enter" && handleStockSearch()}
                />
                <button
                  className="db-btn-primary"
                  onClick={handleStockSearch}
                  disabled={searchLoading}
                >
                  {searchLoading ? (
                    <><span className="db-spinner" /> Searching…</>
                  ) : "Search"}
                </button>
              </div>

              {/* Results */}
              {searchResults.length > 0 && (
                <div className="db-results">
                  <p className="db-results-label">
                    {searchResults.length} result{searchResults.length !== 1 ? "s" : ""} found
                  </p>
                  {searchResults.map((stock) => (
                    <div
                      key={`${stock.ticker}-${stock.market}`}
                      className={`db-result-row ${selectedStock?.ticker === stock.ticker ? "db-result-selected" : ""}`}
                    >
                      <div className="db-result-info">
                        <div className="db-result-ticker">{stock.ticker}</div>
                        <div>
                          <strong>{stock.company_name}</strong>
                          <span className="db-result-meta">
                            {stock.market} · {stock.sector}
                          </span>
                        </div>
                      </div>
                      <button
                        className="db-btn-select"
                        onClick={() => handleSelectStock(stock)}
                        disabled={selectedStock?.ticker === stock.ticker}
                      >
                        {selectedStock?.ticker === stock.ticker ? "✓ Selected" : "Select"}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Selected stock config */}
              {selectedStock && (
                <div className="db-selected">
                  <div className="db-selected-top">
                    <div>
                      <p className="db-selected-company">{selectedStock.company_name}</p>
                      <p className="db-selected-meta">
                        <span className="db-badge">{selectedStock.ticker}</span>
                        <span className="db-badge db-badge-mkt">{selectedStock.market}</span>
                      </p>
                    </div>
                    <span className="db-selected-check">✓</span>
                  </div>

                  <label className="db-label" htmlFor="analysisPeriod">
                    Analysis Period
                  </label>
                  <div className="db-period-row">
                    {["1mo","3mo","6mo","1y","5y"].map((p) => (
                      <button
                        key={p}
                        className={`db-period-chip ${analysisPeriod === p ? "active" : ""}`}
                        onClick={() => setAnalysisPeriod(p)}
                      >
                        {p === "1mo" ? "1M" : p === "3mo" ? "3M" : p === "6mo" ? "6M" : p === "1y" ? "1Y" : "5Y"}
                      </button>
                    ))}
                  </div>

                  <button
                    className="db-btn-launch"
                    onClick={handleStartResearch}
                    disabled={researchLoading}
                  >
                    {researchLoading ? (
                      <><span className="db-spinner" /> Launching Research…</>
                    ) : "🚀 Launch AI Research"}
                  </button>
                </div>
              )}

              {message && <p className="db-msg-success">{message}</p>}
              {error   && <p className="db-msg-error">{error}</p>}
            </div>

            {/* Research history table */}
            <div className="db-card db-card-table">
              <div className="db-card-header">
                <div>
                  <p className="db-eyebrow">ACTIVITY LOG</p>
                  <h2>Research History</h2>
                  <p className="db-card-desc">All your stock research tasks</p>
                </div>
                <span className="db-card-icon">📋</span>
              </div>

              {loading ? (
                <div className="db-empty">
                  <div className="db-spinner db-spinner-lg" />
                  <p>Loading history…</p>
                </div>
              ) : researchHistory.length === 0 ? (
                <div className="db-empty">
                  <span className="db-empty-icon">🔭</span>
                  <h3>No research yet</h3>
                  <p>Start your first stock research above.</p>
                </div>
              ) : (
                <div className="db-table-wrap">
                  <table className="db-table">
                    <thead>
                      <tr>
                        <th>Company</th>
                        <th>Market</th>
                        <th>Period</th>
                        <th>Date</th>
                        <th>Status</th>
                        <th>Report</th>
                      </tr>
                    </thead>
                    <tbody>
                      {researchHistory.map((task) => (
                        <tr key={task.task_id}>
                          <td>
                            <div className="db-company-cell">
                              <strong>{task.company_name}</strong>
                              <span>{task.ticker}</span>
                            </div>
                          </td>
                          <td>{task.market}</td>
                          <td>{task.analysis_period}</td>
                          <td>{formatDate(task.started_at)}</td>
                          <td>
                            <span className={`db-status ${getStatusClass(task.status)}`}>
                              {task.status}
                            </span>
                          </td>
                          <td>
                            {task.status === "COMPLETED" ? (
                              <button
                                className="db-report-btn"
                                onClick={() => openReport(task.task_id)}
                                disabled={reportLoading}
                              >
                                View Report
                              </button>
                            ) : (
                              <span className="db-report-na">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* ── RIGHT COLUMN ── */}
          <div className="db-col-right">

            {/* AI Agents overview */}
            <div className="db-card">
              <div className="db-card-header">
                <div>
                  <p className="db-eyebrow">MULTI-AGENT SYSTEM</p>
                  <h2>AI Research Agents</h2>
                  <p className="db-card-desc">
                    Specialised agents work in parallel on each research task
                  </p>
                </div>
                <span className="db-card-icon">🤖</span>
              </div>

              <div className="db-agents">
                {AI_AGENTS.map((a) => (
                  <div className="db-agent-row" key={a.label}>
                    <div className="db-agent-icon">{a.icon}</div>
                    <div className="db-agent-info">
                      <strong style={{ color: a.color }}>{a.label} Agent</strong>
                      <p>{a.desc}</p>
                    </div>
                    <div className="db-agent-status">READY</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick links */}
            <div className="db-card db-quick-links">
              <p className="db-eyebrow">QUICK ACCESS</p>
              <h2>Navigate</h2>
              {[
                { icon: "☆", label: "Watchlist",   path: "/dashboard/watchlist",  desc: "Monitor saved stocks" },
                { icon: "▤", label: "Research",    path: "/dashboard/research",   desc: "Advanced research terminal" },
                { icon: "◷", label: "History",     path: "/dashboard/history",    desc: "Full research archive" },
                { icon: "⚙", label: "Preferences", path: "/dashboard/preferences",desc: "Customise your workspace" },
              ].map((l) => (
                <button
                  key={l.label}
                  className="db-quick-btn"
                  onClick={() => navigate(l.path)}
                >
                  <span className="db-quick-icon">{l.icon}</span>
                  <div className="db-quick-text">
                    <strong>{l.label}</strong>
                    <span>{l.desc}</span>
                  </div>
                  <span className="db-quick-arrow">›</span>
                </button>
              ))}
            </div>

          </div>
        </div>
      </div>

      {/* ── REPORT MODAL ── */}
      {selectedReport && (
        <div className="db-modal-overlay" onClick={() => setSelectedReport(null)}>
          <div className="db-modal" onClick={(e) => e.stopPropagation()}>
            <button className="db-modal-close" onClick={() => setSelectedReport(null)}>✕</button>
            <p className="db-eyebrow">STOCKINTEL RESEARCH REPORT</p>
            <h2 className="db-modal-title">Research Report</h2>
            <p className="db-modal-summary">{selectedReport.summary}</p>
            <div className="db-modal-content">{selectedReport.report_content}</div>
            {selectedReport.limitations && (
              <div className="db-modal-limitations">
                <h4>Limitations</h4>
                <p>{selectedReport.limitations}</p>
              </div>
            )}
            <p className="db-modal-date">
              Generated: {formatDate(selectedReport.created_at)}
            </p>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

export default Dashboard;
