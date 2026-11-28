/**
 * Fundamentals.jsx
 * ================
 * Interactive Fundamental Agent view for StockIntel / Stockly.
 * Integrates the completed in-memory Fundamental Agent backend API
 * (POST /api/fundamental/analyze) into the existing React dashboard.
 *
 * All 8 analytical features:
 *   1. Revenue & Earnings Analysis
 *   2. Profitability Analysis
 *   3. Debt & Financial Stability
 *   4. Financial Ratios & Multiples
 *   5. Historical Performance
 *   6. Peer Comparison
 *   7. Data Quality & Validation Audit
 *   8. Profitability Classification
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  ShieldCheck,
  Award,
  AlertTriangle,
  Info,
  CheckCircle,
  BarChart3,
  Percent,
  Layers,
  Scale,
  RotateCcw,
  Activity,
  FileText,
} from "lucide-react";

import DashboardLayout from "../components/DashboardLayout";
import { analyzeFundamentals } from "../services/authService";
import "./Fundamentals.css";

// ── FORMATTING HELPERS ───────────────────────────────────────────────────

function formatCurrency(amount, currency = "INR") {
  if (amount === undefined || amount === null || isNaN(amount)) return "—";
  const num = Number(amount);
  const isNegative = num < 0;
  const abs = Math.abs(num);
  const sign = isNegative ? "-" : "";
  const isUS = currency === "USD";
  const symbol = isUS ? "$" : "₹";

  if (isUS) {
    if (abs >= 1e12) return `${sign}${symbol}${(abs / 1e12).toFixed(2)} T`;
    if (abs >= 1e9)  return `${sign}${symbol}${(abs / 1e9).toFixed(2)} B`;
    if (abs >= 1e6)  return `${sign}${symbol}${(abs / 1e6).toFixed(2)} M`;
    return `${sign}${symbol}${abs.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  // Indian Rupee (Crores / Lakhs)
  if (abs >= 1e7) {
    const cr = abs / 1e7;
    return `${sign}${symbol}${cr.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} Cr`;
  }
  if (abs >= 1e5) {
    const l = abs / 1e5;
    return `${sign}${symbol}${l.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} L`;
  }
  return `${sign}${symbol}${abs.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPercent(val, includeSign = false) {
  if (val === undefined || val === null || isNaN(val)) return "—";
  const num = Number(val);
  const prefix = includeSign && num > 0 ? "+" : "";
  return `${prefix}${num.toFixed(2)}%`;
}

function formatRatio(val, decimals = 2) {
  if (val === undefined || val === null || isNaN(val)) return "—";
  return Number(val).toFixed(decimals);
}

function getTierClass(tier) {
  if (!tier) return "tier-insufficient";
  const t = tier.toLowerCase();
  if (t.includes("highly")) return "tier-highly";
  if (t.includes("moderately")) return "tier-moderately";
  if (t.includes("low")) return "tier-low";
  if (t.includes("not")) return "tier-not";
  return "tier-insufficient";
}

function getSeverityClass(severity) {
  switch ((severity || "").toUpperCase()) {
    case "CRITICAL": return "severity-critical";
    case "WARNING":  return "severity-warning";
    case "INFO":     return "severity-info";
    default:         return "severity-pass";
  }
}

function getStatusPillClass(status) {
  const s = (status || "").toLowerCase();
  if (s.includes("improving") || s.includes("pass") || s.includes("good")) return "status-pill improving";
  if (s.includes("declining") || s.includes("critical") || s.includes("danger")) return "status-pill declining";
  return "status-pill stable";
}

// ── COMPONENT ────────────────────────────────────────────────────────────

export default function Fundamentals() {
  const navigate = useNavigate();

  // User & Auth
  const [user, setUser] = useState(null);

  // Search Controls
  const [ticker, setTicker] = useState("");
  const [market, setMarket] = useState("NSE");
  const [activeTab, setActiveTab] = useState("overview");

  // UX State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);

  // Authenticate on mount
  useEffect(() => {
    const token = sessionStorage.getItem("access_token");
    const storedUser = sessionStorage.getItem("user");

    if (!token) {
      navigate("/login", { replace: true });
      return;
    }

    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        setUser({ full_name: "Analyst" });
      }
    }
  }, [navigate]);

  const handleLogout = () => {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    navigate("/login", { replace: true });
  };

  const handleAnalyze = async (overrideTicker, overrideMarket) => {
    const targetTicker = (overrideTicker || ticker).trim().toUpperCase();
    const targetMarket = (overrideMarket || market).trim().toUpperCase();

    if (!targetTicker) {
      setError("Please enter a valid stock ticker symbol (e.g. TCS, AAPL, RELIANCE).");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await analyzeFundamentals(targetTicker, targetMarket);
      if (result.success) {
        setData(result);
        setActiveTab("overview");
      } else {
        setError(result.error || "Fundamental analysis failed. Please verify the ticker and market.");
      }
    } catch (err) {
      if (err.response?.status === 401) {
        sessionStorage.removeItem("access_token");
        navigate("/login", { replace: true });
        return;
      }
      const msg = err.response?.data?.error || err.response?.data?.detail || err.message || "Failed to analyze fundamentals.";
      setError(typeof msg === "object" ? JSON.stringify(msg) : msg);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickSelect = (qTicker, qMarket) => {
    setTicker(qTicker);
    if (qMarket) {
      setMarket(qMarket);
    }
    setError("");
  };

  // Safe destructuring of analysis components
  const analysis = data?.analysis || {};
  const currency = data?.currency || "INR";
  const revenueEarnings = analysis.revenue_earnings || [];
  const profitability = analysis.profitability || [];
  const debtStability = analysis.debt_stability || [];
  const financialRatios = analysis.financial_ratios || [];
  const historicalDetail = analysis.historical_detail || [];
  const dataQuality = analysis.data_quality || { issues: [], critical_count: 0, warning_count: 0, info_count: 0 };
  const profitClassification = analysis.profitability_classification || { summary: [], detail: [] };
  const peerComparison = analysis.peer_comparison;

  // Extract classification summary map
  const summaryMap = {};
  (profitClassification.summary || []).forEach((row) => {
    summaryMap[row.Item] = row.Value;
  });

  const overallClass = summaryMap["Overall Profitability Class"] || "Not Evaluated";
  const latestNPM = summaryMap["Latest Net Profit Margin (%)"] || "—";
  const marginTrend = summaryMap["Multi-Year Margin Trend"] || "—";
  const classRationale = summaryMap["Classification Rationale"] || "Analysis not completed.";
  const dqStatus = summaryMap["Data Quality Status"] || "Normal";

  // Latest year metric helpers
  const latestRevRow = revenueEarnings[revenueEarnings.length - 1] || {};
  const latestProfitRow = profitability[profitability.length - 1] || {};
  const latestDebtRow = debtStability[debtStability.length - 1] || {};
  const latestRatioRow = financialRatios[financialRatios.length - 1] || {};

  return (
    <DashboardLayout user={user} onLogout={handleLogout}>
      <div className="fundamentals-container">
        
        {/* Header Area */}
        <header className="fundamentals-header">
          <div className="fundamentals-title-area">
            <h1>
              <span>Fundamental Analysis Agent</span>
              <span className="agent-badge">AI Agent • Module 3</span>
            </h1>
            <p>
              Autonomous fundamental engine evaluating audited financial statements across revenue trajectories,
              operating & net profit margins, balance sheet leverage, valuation multiples, and rule-based profitability tiers.
            </p>
          </div>
        </header>

        {/* Search & Configuration Bar */}
        <div className="fundamentals-search-card">
          <form
            className="search-form-row"
            onSubmit={(e) => {
              e.preventDefault();
              handleAnalyze();
            }}
          >
            <div className="input-group-ticker">
              <Search className="search-icon" size={18} />
              <input
                type="text"
                placeholder="Enter ticker (e.g. TCS, AAPL, RELIANCE, INFY)"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                disabled={loading}
              />
            </div>

            <div className="input-group-market">
              <select
                value={market}
                onChange={(e) => setMarket(e.target.value)}
                disabled={loading}
              >
                <option value="NSE">NSE (India)</option>
                <option value="BSE">BSE (India)</option>
                <option value="NASDAQ">NASDAQ (US)</option>
                <option value="NYSE">NYSE (US)</option>
              </select>
            </div>

            <button
              type="submit"
              className="btn-analyze"
              disabled={loading || !ticker.trim()}
            >
              {loading ? (
                <>
                  <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Activity size={16} />
                  <span>Analyze Fundamentals</span>
                </>
              )}
            </button>
          </form>

          {/* Quick stock suggestions */}
          <div className="quick-ticker-chips">
            <span>Try popular stocks:</span>
            <button type="button" className="quick-chip" onClick={() => handleQuickSelect("TCS", "NSE")}>TCS (NSE)</button>
            <button type="button" className="quick-chip" onClick={() => handleQuickSelect("RELIANCE", "NSE")}>RELIANCE (NSE)</button>
            <button type="button" className="quick-chip" onClick={() => handleQuickSelect("INFY", "NSE")}>INFY (NSE)</button>
            <button type="button" className="quick-chip" onClick={() => handleQuickSelect("AAPL", "NASDAQ")}>AAPL (NASDAQ)</button>
            <button type="button" className="quick-chip" onClick={() => handleQuickSelect("MSFT", "NASDAQ")}>MSFT (NASDAQ)</button>
          </div>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="error-banner">
            <div className="error-content">
              <AlertTriangle size={18} />
              <span>{error}</span>
            </div>
            <button type="button" onClick={() => setError("")}>×</button>
          </div>
        )}

        {/* Loading Spinner View */}
        {loading && (
          <div className="loading-card">
            <div className="spinner" />
            <h3>Analyzing {ticker} on {market}...</h3>
            <p>
              Retrieving audited income statements and balance sheets via live market data feed,
              computing multi-year growth trajectories, liquidity ratios, and executing the 8-feature analytical engine.
            </p>
          </div>
        )}

        {/* Empty State View */}
        {!loading && !data && !error && (
          <div className="empty-state-card">
            <h2>Start Your Fundamental Research</h2>
            <p>
              Enter a stock ticker above or select one of the suggested companies to run the complete Fundamental Agent
              evaluation suite powered by real financial filings.
            </p>

            <div className="empty-features-grid">
              <div className="empty-feature-item">
                <span className="feature-icon">📊</span>
                <h4>Revenue & Earnings</h4>
                <p>Multi-year top-line and bottom-line growth, trajectory stability, and trend variance.</p>
              </div>

              <div className="empty-feature-item">
                <span className="feature-icon">💎</span>
                <h4>Profitability Margins</h4>
                <p>Gross margin, operating margin, EBITDA, and net profit margin progression.</p>
              </div>

              <div className="empty-feature-item">
                <span className="feature-icon">⚖️</span>
                <h4>Debt & Financial Stability</h4>
                <p>Solvency, Debt-to-Equity, current liquidity, cash buffers, and balance sheet strength.</p>
              </div>

              <div className="empty-feature-item">
                <span className="feature-icon">🏆</span>
                <h4>Profitability Classification</h4>
                <p>Rule-based tier assignment (Highly Profitable to Not Profitable) with audit rationale.</p>
              </div>
            </div>
          </div>
        )}

        {/* Results View */}
        {!loading && data && (
          <>
            {/* Company Profile Ribbon */}
            <div className="company-ribbon">
              <div className="company-identity">
                <div className="company-name-row">
                  <h2>{data.company_name}</h2>
                  <span className="ticker-badge">{data.ticker} • {data.market}</span>
                </div>
                <span className="company-sector">
                  {data.sector || "General Sector"} {data.industry ? `— ${data.industry}` : ""}
                </span>
              </div>

              <div className="company-meta-pills">
                {data.market_price && (
                  <div className="price-card-pill">
                    <div className="price-label">Current Market Price</div>
                    <div className="price-value">
                      {currency === "USD" ? "$" : "₹"}{data.market_price.toLocaleString(currency === "USD" ? "en-US" : "en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                )}

                <button
                  type="button"
                  className="quick-chip"
                  onClick={() => {
                    setData(null);
                    setTicker("");
                    setError("");
                  }}
                  style={{ height: 40, padding: "0 14px", display: "flex", alignItems: "center", gap: 6 }}
                >
                  <RotateCcw size={14} />
                  <span>New Stock</span>
                </button>
              </div>
            </div>

            {/* Hero Profitability Tier Banner (Feature 8 & 7) */}
            <div className="classification-banner">
              <div className="tier-left">
                <span className="tier-label">Overall Profitability Classification</span>
                <div className={`tier-badge-large ${getTierClass(overallClass)}`}>
                  <Award size={20} />
                  <span>{overallClass}</span>
                </div>
                <div className="tier-rationale">{classRationale}</div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
                  <ShieldCheck size={16} color="#38BDF8" />
                  <span style={{ fontSize: 13, color: "#94A3B8" }}>Data Quality: {dqStatus}</span>
                </div>
              </div>

              <div className="tier-right-metrics">
                <div className="tier-mini-stat">
                  <div className="mini-label">Latest Net Margin</div>
                  <div className="mini-val" style={{ color: "#C6F36B" }}>{latestNPM}</div>
                </div>

                <div className="tier-mini-stat">
                  <div className="mini-label">Margin Trend</div>
                  <div className="mini-val">{marginTrend}</div>
                </div>

                <div className="tier-mini-stat">
                  <div className="mini-label">Filings Analyzed</div>
                  <div className="mini-val">{(data.reporting_periods || []).length} Years</div>
                </div>
              </div>
            </div>

            {/* Feature Tabs Bar */}
            <nav className="features-tab-bar">
              <button
                type="button"
                className={`tab-btn ${activeTab === "overview" ? "active" : ""}`}
                onClick={() => setActiveTab("overview")}
              >
                <Activity size={14} />
                <span>Executive Overview</span>
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "revenue" ? "active" : ""}`}
                onClick={() => setActiveTab("revenue")}
              >
                <TrendingUp size={14} />
                <span>1. Revenue & Earnings</span>
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "profitability" ? "active" : ""}`}
                onClick={() => setActiveTab("profitability")}
              >
                <Percent size={14} />
                <span>2. Profitability</span>
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "stability" ? "active" : ""}`}
                onClick={() => setActiveTab("stability")}
              >
                <Scale size={14} />
                <span>3. Debt & Stability</span>
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "ratios" ? "active" : ""}`}
                onClick={() => setActiveTab("ratios")}
              >
                <BarChart3 size={14} />
                <span>4. Financial Ratios</span>
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "historical" ? "active" : ""}`}
                onClick={() => setActiveTab("historical")}
              >
                <FileText size={14} />
                <span>5. Historical Comparison</span>
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "peers" ? "active" : ""}`}
                onClick={() => setActiveTab("peers")}
              >
                <Layers size={14} />
                <span>6. Peer Comparison</span>
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "data_quality" ? "active" : ""}`}
                onClick={() => setActiveTab("data_quality")}
              >
                <ShieldAlert size={14} />
                <span>7. Data Quality ({dataQuality.issues?.length || 0})</span>
              </button>
            </nav>

            {/* TAB: EXECUTIVE OVERVIEW */}
            {activeTab === "overview" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                
                {/* Highlights KPI Grid */}
                <div className="kpi-cards-grid">
                  <div className="kpi-card">
                    <span className="kpi-label">Latest Total Revenue</span>
                    <span className="kpi-value">{formatCurrency(latestRevRow.Revenue, currency)}</span>
                    <span className={`kpi-sub ${(latestRevRow["Revenue_Growth_%"] || 0) >= 0 ? "positive" : "negative"}`}>
                      {(latestRevRow["Revenue_Growth_%"] || 0) >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                      {formatPercent(latestRevRow["Revenue_Growth_%"], true)} YoY
                    </span>
                  </div>

                  <div className="kpi-card">
                    <span className="kpi-label">Latest Net Income</span>
                    <span className="kpi-value">{formatCurrency(latestRevRow.Net_Income, currency)}</span>
                    <span className={`kpi-sub ${(latestRevRow["Earnings_Growth_%"] || 0) >= 0 ? "positive" : "negative"}`}>
                      {(latestRevRow["Earnings_Growth_%"] || 0) >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                      {formatPercent(latestRevRow["Earnings_Growth_%"], true)} YoY
                    </span>
                  </div>

                  <div className="kpi-card">
                    <span className="kpi-label">Net Profit Margin</span>
                    <span className="kpi-value" style={{ color: "#C6F36B" }}>
                      {formatPercent(latestProfitRow["Net_Profit_Margin_%"])}
                    </span>
                    <span className="kpi-sub">
                      Status: <strong style={{ color: "#F1F5F9" }}>{latestProfitRow["Net_Margin_Status"] || "Stable"}</strong>
                    </span>
                  </div>

                  <div className="kpi-card">
                    <span className="kpi-label">Debt-to-Equity</span>
                    <span className="kpi-value">{formatRatio(latestDebtRow.Debt_to_Equity)}</span>
                    <span className="kpi-sub">
                      Current Ratio: <strong style={{ color: "#F1F5F9" }}>{formatRatio(latestDebtRow.Current_Ratio)}</strong>
                    </span>
                  </div>

                  <div className="kpi-card">
                    <span className="kpi-label">Return on Equity (ROE)</span>
                    <span className="kpi-value">{formatPercent(latestRatioRow["ROE_%"])}</span>
                    <span className="kpi-sub">
                      ROA: <strong style={{ color: "#F1F5F9" }}>{formatPercent(latestRatioRow["ROA_%"])}</strong>
                    </span>
                  </div>

                  <div className="kpi-card">
                    <span className="kpi-label">P/E Valuation Multiple</span>
                    <span className="kpi-value">{formatRatio(latestRatioRow.PE_Ratio)}x</span>
                    <span className="kpi-sub">
                      P/B Multiple: <strong style={{ color: "#F1F5F9" }}>{formatRatio(latestRatioRow.PB_Ratio)}x</strong>
                    </span>
                  </div>
                </div>

                {/* Multi-Year Summary Snapshot */}
                <div className="feature-section-card">
                  <div className="section-header">
                    <div>
                      <h3><Activity size={18} /> Multi-Year Performance Snapshot</h3>
                      <p>Audited annual financial progression across reporting fiscal periods</p>
                    </div>
                  </div>

                  <div className="table-responsive">
                    <table className="financial-table">
                      <thead>
                        <tr>
                          <th>Period (FY)</th>
                          <th>Revenue ({currency})</th>
                          <th>Revenue Growth</th>
                          <th>Net Income ({currency})</th>
                          <th>Net Margin</th>
                          <th>Operating Margin</th>
                          <th>Debt / Equity</th>
                          <th>ROE</th>
                        </tr>
                      </thead>
                      <tbody>
                        {revenueEarnings.map((rev, idx) => {
                          const prof = profitability.find((p) => p.Financial_Year === rev.Financial_Year) || {};
                          const debt = debtStability.find((d) => d.Financial_Year === rev.Financial_Year) || {};
                          const rat = financialRatios.find((r) => r.Financial_Year === rev.Financial_Year) || {};

                          return (
                            <tr key={rev.Financial_Year || idx}>
                              <td className="highlight">{rev.Financial_Year}</td>
                              <td>{formatCurrency(rev.Revenue, currency)}</td>
                              <td className={(rev["Revenue_Growth_%"] || 0) >= 0 ? "positive" : "negative"}>
                                {formatPercent(rev["Revenue_Growth_%"], true)}
                              </td>
                              <td>{formatCurrency(rev.Net_Income, currency)}</td>
                              <td className="highlight" style={{ color: "#C6F36B" }}>
                                {formatPercent(prof["Net_Profit_Margin_%"])}
                              </td>
                              <td>{formatPercent(prof["Operating_Margin_%"])}</td>
                              <td>{formatRatio(debt.Debt_to_Equity)}</td>
                              <td>{formatPercent(rat["ROE_%"])}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

              </div>
            )}

            {/* TAB 1: REVENUE & EARNINGS */}
            {activeTab === "revenue" && (
              <div className="feature-section-card">
                <div className="section-header">
                  <div>
                    <h3><TrendingUp size={18} /> Feature 1 — Revenue & Earnings Analysis</h3>
                    <p>Evaluates top-line sales, bottom-line net profit, year-over-year growth trajectories, and trend variance.</p>
                  </div>
                </div>

                <div className="table-responsive">
                  <table className="financial-table">
                    <thead>
                      <tr>
                        <th>Financial Period</th>
                        <th>Revenue ({currency})</th>
                        <th>Revenue Growth (YoY)</th>
                        <th>Net Income ({currency})</th>
                        <th>Earnings Growth (YoY)</th>
                        <th>Revenue Trend Variance</th>
                        <th>Earnings Trend Variance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {revenueEarnings.map((row, i) => (
                        <tr key={row.Financial_Year || i}>
                          <td className="highlight">{row.Financial_Year}</td>
                          <td>{formatCurrency(row.Revenue, currency)}</td>
                          <td className={(row["Revenue_Growth_%"] || 0) >= 0 ? "positive" : "negative"}>
                            {formatPercent(row["Revenue_Growth_%"], true)}
                          </td>
                          <td>{formatCurrency(row.Net_Income, currency)}</td>
                          <td className={(row["Earnings_Growth_%"] || 0) >= 0 ? "positive" : "negative"}>
                            {formatPercent(row["Earnings_Growth_%"], true)}
                          </td>
                          <td>{formatCurrency(row.Revenue_Trend, currency)}</td>
                          <td>{formatCurrency(row.Earnings_Trend, currency)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 2: PROFITABILITY */}
            {activeTab === "profitability" && (
              <div className="feature-section-card">
                <div className="section-header">
                  <div>
                    <h3><Percent size={18} /> Feature 2 — Profitability Analysis</h3>
                    <p>Margin breakdown across gross, operating, EBITDA, and net profit tiers with multi-year margin delta tracking.</p>
                  </div>
                </div>

                <div className="table-responsive">
                  <table className="financial-table">
                    <thead>
                      <tr>
                        <th>Period</th>
                        <th>Gross Margin %</th>
                        <th>Operating Margin %</th>
                        <th>EBITDA Margin %</th>
                        <th>Net Profit Margin %</th>
                        <th>Gross Margin Status</th>
                        <th>Operating Status</th>
                        <th>Net Margin Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {profitability.map((row, i) => (
                        <tr key={row.Financial_Year || i}>
                          <td className="highlight">{row.Financial_Year}</td>
                          <td>{formatPercent(row["Gross_Profit_Margin_%"])}</td>
                          <td>{formatPercent(row["Operating_Margin_%"])}</td>
                          <td>{formatPercent(row["EBITDA_Margin_%"])}</td>
                          <td className="highlight" style={{ color: "#C6F36B" }}>
                            {formatPercent(row["Net_Profit_Margin_%"])}
                          </td>
                          <td>
                            <span className={getStatusPillClass(row.Gross_Margin_Status)}>
                              {row.Gross_Margin_Status || "—"}
                            </span>
                          </td>
                          <td>
                            <span className={getStatusPillClass(row.Operating_Margin_Status)}>
                              {row.Operating_Margin_Status || "—"}
                            </span>
                          </td>
                          <td>
                            <span className={getStatusPillClass(row.Net_Margin_Status)}>
                              {row.Net_Margin_Status || "—"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 3: DEBT & FINANCIAL STABILITY */}
            {activeTab === "stability" && (
              <div className="feature-section-card">
                <div className="section-header">
                  <div>
                    <h3><Scale size={18} /> Feature 3 — Debt & Financial Stability Analysis</h3>
                    <p>Solvency and liquidity health indicators assessing capital structure and debt coverage.</p>
                  </div>
                </div>

                <div className="table-responsive">
                  <table className="financial-table">
                    <thead>
                      <tr>
                        <th>Period</th>
                        <th>Total Assets</th>
                        <th>Total Liabilities</th>
                        <th>Stockholders Equity</th>
                        <th>Total Debt</th>
                        <th>Cash & Cash Eq.</th>
                        <th>Debt / Equity</th>
                        <th>Debt / Assets</th>
                        <th>Current Ratio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {debtStability.map((row, i) => (
                        <tr key={row.Financial_Year || i}>
                          <td className="highlight">{row.Financial_Year}</td>
                          <td>{formatCurrency(row.Total_Assets, currency)}</td>
                          <td>{formatCurrency(row.Total_Liabilities, currency)}</td>
                          <td>{formatCurrency(row.Stockholders_Equity, currency)}</td>
                          <td>{formatCurrency(row.Total_Debt, currency)}</td>
                          <td>{formatCurrency(row.Cash_And_Cash_Equivalents, currency)}</td>
                          <td className="highlight">{formatRatio(row.Debt_to_Equity)}</td>
                          <td>{formatRatio(row.Debt_to_Assets)}</td>
                          <td className="highlight">{formatRatio(row.Current_Ratio)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 4: FINANCIAL RATIOS */}
            {activeTab === "ratios" && (
              <div className="feature-section-card">
                <div className="section-header">
                  <div>
                    <h3><BarChart3 size={18} /> Feature 4 — Financial Ratios & Valuation Multiples</h3>
                    <p>Comprehensive returns, per-share values, and spot-price valuation multiples.</p>
                  </div>
                </div>

                <div className="table-responsive">
                  <table className="financial-table">
                    <thead>
                      <tr>
                        <th>Period</th>
                        <th>Return on Equity (ROE)</th>
                        <th>Return on Assets (ROA)</th>
                        <th>Earnings Per Share (EPS)</th>
                        <th>Book Value Per Share (BVPS)</th>
                        <th>P/E Ratio</th>
                        <th>P/B Ratio</th>
                        <th>Current Price Ref</th>
                      </tr>
                    </thead>
                    <tbody>
                      {financialRatios.map((row, i) => (
                        <tr key={row.Financial_Year || i}>
                          <td className="highlight">{row.Financial_Year}</td>
                          <td className="highlight">{formatPercent(row["ROE_%"])}</td>
                          <td>{formatPercent(row["ROA_%"])}</td>
                          <td>{currency === "USD" ? "$" : "₹"}{formatRatio(row.EPS)}</td>
                          <td>{currency === "USD" ? "$" : "₹"}{formatRatio(row.BVPS)}</td>
                          <td className="highlight">{formatRatio(row.PE_Ratio)}x</td>
                          <td className="highlight">{formatRatio(row.PB_Ratio)}x</td>
                          <td>{row.Stock_Price ? `${currency} ${row.Stock_Price}` : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <p className="footnote-text">
                  Note: P/E and P/B ratios are calculated using the real-time spot price for the most recent period to prevent historical lookahead bias.
                </p>
              </div>
            )}

            {/* TAB 5: HISTORICAL PERFORMANCE */}
            {activeTab === "historical" && (
              <div className="feature-section-card">
                <div className="section-header">
                  <div>
                    <h3><FileText size={18} /> Feature 5 — Historical Performance Comparison</h3>
                    <p>Compound annual growth rates (CAGR) and total multi-period growth across revenue, earnings, and equity.</p>
                  </div>
                </div>

                <div className="table-responsive">
                  <table className="financial-table">
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>Earliest Evaluated Period</th>
                        <th>Latest Period</th>
                        <th>Absolute Variance</th>
                        <th>Total Percentage Growth</th>
                        <th>Annualized CAGR (%)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historicalDetail.map((item, i) => (
                        <tr key={item.Metric || i}>
                          <td className="highlight">{item.Metric}</td>
                          <td>{formatCurrency(item.Earliest_Value, currency)}</td>
                          <td>{formatCurrency(item.Latest_Value, currency)}</td>
                          <td className={(item.Absolute_Change || 0) >= 0 ? "positive" : "negative"}>
                            {formatCurrency(item.Absolute_Change, currency)}
                          </td>
                          <td className={(item["Percentage_Change_%"] || 0) >= 0 ? "positive" : "negative"}>
                            {formatPercent(item["Percentage_Change_%"], true)}
                          </td>
                          <td className="highlight">
                            {formatPercent(item["CAGR_%"])}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 6: PEER COMPARISON */}
            {activeTab === "peers" && (
              <div className="feature-section-card">
                <div className="section-header">
                  <div>
                    <h3><Layers size={18} /> Feature 6 — Peer Comparison</h3>
                    <p>Benchmarking against industry competitors within the same sector and market.</p>
                  </div>
                  {peerComparison?.peer_count > 0 && (
                    <span className="agent-badge" style={{ fontSize: 11, padding: "4px 10px", borderRadius: 6, background: "rgba(198, 243, 107, 0.12)", color: "#C6F36B", border: "1px solid rgba(198, 243, 107, 0.3)" }}>
                      {peerComparison.discovery_status === "auto_discovered" ? "Auto-Discovered Peer Group" : "Peer Benchmark Group"} ({peerComparison.peer_count} Peers)
                    </span>
                  )}
                </div>

                {peerComparison && peerComparison.peer_count > 0 && peerComparison.comparison_table?.length > 0 ? (
                  <>
                    {/* Warnings (Currency / Sector Mismatches) */}
                    {peerComparison.warnings && peerComparison.warnings.length > 0 && (
                      <div className="peer-warning-box">
                        <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 700 }}>
                          <AlertTriangle size={16} />
                          <span>Comparison Compatibility Notices</span>
                        </div>
                        <ul style={{ margin: 0, paddingLeft: 20 }}>
                          {peerComparison.warnings.map((w, idx) => (
                            <li key={idx} style={{ fontSize: 12 }}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Benchmark KPI Cards (Target Ranking & Peer Averages) */}
                    {peerComparison.peer_benchmarks && (
                      <div className="kpi-cards-grid">
                        {peerComparison.peer_benchmarks["Net_Profit_Margin_%"]?.target_value !== null && (
                          <div className="kpi-card">
                            <span className="kpi-label">Net Profit Margin</span>
                            <span className="kpi-value" style={{ color: "#C6F36B" }}>
                              {formatPercent(peerComparison.peer_benchmarks["Net_Profit_Margin_%"]?.target_value)}
                            </span>
                            <div className="kpi-sub" style={{ justifyContent: "space-between" }}>
                              <span>Peer Avg: {formatPercent(peerComparison.peer_benchmarks["Net_Profit_Margin_%"]?.peer_average)}</span>
                              {peerComparison.peer_benchmarks["Net_Profit_Margin_%"]?.target_rank && (
                                <span className={`rank-badge ${peerComparison.peer_benchmarks["Net_Profit_Margin_%"].target_rank === 1 ? "top" : "mid"}`}>
                                  Rank {peerComparison.peer_benchmarks["Net_Profit_Margin_%"].target_rank} of {peerComparison.peer_benchmarks["Net_Profit_Margin_%"].total_ranked}
                                </span>
                              )}
                            </div>
                          </div>
                        )}

                        {peerComparison.peer_benchmarks["ROE_%"]?.target_value !== null && (
                          <div className="kpi-card">
                            <span className="kpi-label">Return on Equity (ROE)</span>
                            <span className="kpi-value" style={{ color: "#38BDF8" }}>
                              {formatPercent(peerComparison.peer_benchmarks["ROE_%"]?.target_value)}
                            </span>
                            <div className="kpi-sub" style={{ justifyContent: "space-between" }}>
                              <span>Peer Avg: {formatPercent(peerComparison.peer_benchmarks["ROE_%"]?.peer_average)}</span>
                              {peerComparison.peer_benchmarks["ROE_%"]?.target_rank && (
                                <span className={`rank-badge ${peerComparison.peer_benchmarks["ROE_%"].target_rank === 1 ? "top" : "mid"}`}>
                                  Rank {peerComparison.peer_benchmarks["ROE_%"].target_rank} of {peerComparison.peer_benchmarks["ROE_%"].total_ranked}
                                </span>
                              )}
                            </div>
                          </div>
                        )}

                        {peerComparison.peer_benchmarks["Operating_Margin_%"]?.target_value !== null && (
                          <div className="kpi-card">
                            <span className="kpi-label">Operating Margin</span>
                            <span className="kpi-value">
                              {formatPercent(peerComparison.peer_benchmarks["Operating_Margin_%"]?.target_value)}
                            </span>
                            <div className="kpi-sub" style={{ justifyContent: "space-between" }}>
                              <span>Peer Avg: {formatPercent(peerComparison.peer_benchmarks["Operating_Margin_%"]?.peer_average)}</span>
                              {peerComparison.peer_benchmarks["Operating_Margin_%"]?.target_rank && (
                                <span className={`rank-badge ${peerComparison.peer_benchmarks["Operating_Margin_%"].target_rank === 1 ? "top" : "mid"}`}>
                                  Rank {peerComparison.peer_benchmarks["Operating_Margin_%"].target_rank} of {peerComparison.peer_benchmarks["Operating_Margin_%"].total_ranked}
                                </span>
                              )}
                            </div>
                          </div>
                        )}

                        {peerComparison.peer_benchmarks["PE_Ratio"]?.target_value !== null && (
                          <div className="kpi-card">
                            <span className="kpi-label">P/E Multiple</span>
                            <span className="kpi-value">
                              {formatRatio(peerComparison.peer_benchmarks["PE_Ratio"]?.target_value)}x
                            </span>
                            <div className="kpi-sub" style={{ justifyContent: "space-between" }}>
                              <span>Peer Avg: {formatRatio(peerComparison.peer_benchmarks["PE_Ratio"]?.peer_average)}x</span>
                              {peerComparison.peer_benchmarks["PE_Ratio"]?.target_rank && (
                                <span className="rank-badge mid">
                                  Rank {peerComparison.peer_benchmarks["PE_Ratio"].target_rank} of {peerComparison.peer_benchmarks["PE_Ratio"].total_ranked}
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Comparison Table */}
                    <div className="table-responsive">
                      <table className="financial-table">
                        <thead>
                          <tr>
                            <th>Company / Ticker</th>
                            <th>Currency</th>
                            <th>Revenue</th>
                            <th>Net Margin %</th>
                            <th>Operating Margin %</th>
                            <th>ROE %</th>
                            <th>Debt to Equity</th>
                            <th>Current Ratio</th>
                            <th>P/E Ratio</th>
                          </tr>
                        </thead>
                        <tbody>
                          {peerComparison.comparison_table.map((row, i) => (
                            <tr key={row.Ticker || i} className={row.Is_Target ? "peer-target-row" : ""}>
                              <td>
                                <div style={{ display: "flex", alignItems: "center" }}>
                                  <span className="highlight" style={{ color: row.Is_Target ? "#C6F36B" : "#F1F5F9" }}>
                                    {row.Ticker}
                                  </span>
                                  {row.Is_Target && <span className="peer-target-badge">TARGET</span>}
                                </div>
                                <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>
                                  {row.Company_Name}
                                </div>
                              </td>
                              <td>{row.Currency}</td>
                              <td>{formatCurrency(row.Revenue_Cr !== undefined ? row.Revenue_Cr : row.Revenue, row.Currency)}</td>
                              <td className={(row["Net_Profit_Margin_%"] || 0) >= 0 ? "positive" : "negative"}>
                                {formatPercent(row["Net_Profit_Margin_%"])}
                              </td>
                              <td className={(row["Operating_Margin_%"] || 0) >= 0 ? "positive" : "negative"}>
                                {formatPercent(row["Operating_Margin_%"])}
                              </td>
                              <td className="highlight">
                                {formatPercent(row["ROE_%"])}
                              </td>
                              <td>{formatRatio(row.Debt_to_Equity)}</td>
                              <td>{formatRatio(row.Current_Ratio)}</td>
                              <td>{formatRatio(row.PE_Ratio)}x</td>
                            </tr>
                          ))}

                          {/* Benchmark Row: Peer Group Average */}
                          {peerComparison.peer_benchmarks && (
                            <tr className="peer-avg-row">
                              <td>★ Peer Group Average</td>
                              <td>{peerComparison.target_currency}</td>
                              <td>
                                {formatCurrency(
                                  peerComparison.peer_benchmarks["Revenue_Cr"]?.peer_average !== undefined
                                    ? peerComparison.peer_benchmarks["Revenue_Cr"]?.peer_average
                                    : peerComparison.peer_benchmarks["Revenue"]?.peer_average,
                                  peerComparison.target_currency
                                )}
                              </td>
                              <td>{formatPercent(peerComparison.peer_benchmarks["Net_Profit_Margin_%"]?.peer_average)}</td>
                              <td>{formatPercent(peerComparison.peer_benchmarks["Operating_Margin_%"]?.peer_average)}</td>
                              <td>{formatPercent(peerComparison.peer_benchmarks["ROE_%"]?.peer_average)}</td>
                              <td>{formatRatio(peerComparison.peer_benchmarks["Debt_to_Equity"]?.peer_average)}</td>
                              <td>{formatRatio(peerComparison.peer_benchmarks["Current_Ratio"]?.peer_average)}</td>
                              <td>{formatRatio(peerComparison.peer_benchmarks["PE_Ratio"]?.peer_average)}x</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>

                    {peerComparison.disclaimer && (
                      <p className="footnote-text">{peerComparison.disclaimer}</p>
                    )}
                  </>
                ) : (
                  <div className="info-box">
                    <Info size={18} />
                    <span>
                      {peerComparison?.message ||
                        "Peer comparison is currently unavailable. No comparable industry peers with published financial filings could be found for this company."}
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* TAB 7: DATA QUALITY AUDIT */}
            {activeTab === "data_quality" && (
              <div className="feature-section-card">
                <div className="section-header">
                  <div>
                    <h3><ShieldAlert size={18} /> Feature 7 — Financial Data Quality & Validation Audit</h3>
                    <p>Automated verification detecting missing filings, zero-division risks, anomalous signs, and statement inconsistencies.</p>
                  </div>
                </div>

                <div className="kpi-cards-grid" style={{ marginBottom: 10 }}>
                  <div className="kpi-card">
                    <span className="kpi-label">Critical Issues</span>
                    <span className="kpi-value" style={{ color: dataQuality.critical_count > 0 ? "#EF4444" : "#10B981" }}>
                      {dataQuality.critical_count || 0}
                    </span>
                  </div>

                  <div className="kpi-card">
                    <span className="kpi-label">Warnings</span>
                    <span className="kpi-value" style={{ color: dataQuality.warning_count > 0 ? "#F59E0B" : "#10B981" }}>
                      {dataQuality.warning_count || 0}
                    </span>
                  </div>

                  <div className="kpi-card">
                    <span className="kpi-label">Informational Notices</span>
                    <span className="kpi-value" style={{ color: "#38BDF8" }}>
                      {dataQuality.info_count || 0}
                    </span>
                  </div>
                </div>

                {dataQuality.issues && dataQuality.issues.length > 0 ? (
                  <div className="table-responsive">
                    <table className="financial-table">
                      <thead>
                        <tr>
                          <th>Severity</th>
                          <th>Category</th>
                          <th>Period</th>
                          <th>Affected Metric</th>
                          <th>Description</th>
                          <th>Impact</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dataQuality.issues.map((issue, idx) => (
                          <tr key={idx}>
                            <td>
                              <span className={`severity-badge ${getSeverityClass(issue.Severity)}`}>
                                {issue.Severity}
                              </span>
                            </td>
                            <td className="highlight">{issue.Category}</td>
                            <td>{issue.Period}</td>
                            <td>{issue.Metric}</td>
                            <td>{issue.Description}</td>
                            <td style={{ color: "#94A3B8" }}>{issue.Impact}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="info-box" style={{ background: "rgba(16, 185, 129, 0.08)", borderColor: "rgba(16, 185, 129, 0.25)", color: "#6EE7B7" }}>
                    <CheckCircle size={18} />
                    <span>Clean Data Audit: Zero critical or warning data quality issues detected across evaluated financial statements.</span>
                  </div>
                )}
              </div>
            )}

          </>
        )}

      </div>
    </DashboardLayout>
  );
}
