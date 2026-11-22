
import { useEffect, useState, useMemo, useCallback } from "react";
import { Clock } from "lucide-react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";

import {
  searchStocks,
  getStockHistory,
  createResearchTask,
  getCompanyProfile,
  getFinancialStatement,
} from "../services/authService";

// Helper formatters
function formatRetrievedAt(isoStr) {
  if (!isoStr) return "Retrieval time unavailable";
  try {
    return (
      new Date(isoStr).toLocaleString("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      }) + " IST"
    );
  } catch {
    return "Retrieval time unavailable";
  }
}

function formatPrice(value, market = "NSE") {
  if (value === undefined || value === null || isNaN(value)) return "—";
  const locale = market === "NASDAQ" || market === "NYSE" ? "en-US" : "en-IN";
  return Number(value).toLocaleString(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function getCurrencyPrefix(market, currencyCode) {
  if (currencyCode === "USD" || market === "NASDAQ" || market === "NYSE") {
    return "$";
  }
  return "₹";
}

function formatLargeNumber(val, currency = "INR") {
  if (val === undefined || val === null || isNaN(val)) return "—";
  const num = Number(val);
  const isNegative = num < 0;
  const abs = Math.abs(num);
  const sign = isNegative ? "-" : "";
  const isUS = currency === "USD";
  const prefix = isUS ? "$" : "₹";

  if (isUS) {
    if (abs >= 1e12) {
      return `${sign}${(abs / 1e12).toFixed(2)}T ${prefix}`;
    }
    if (abs >= 1e9) {
      return `${sign}${prefix}${(abs / 1e9).toFixed(2)}B`;
    }
    if (abs >= 1e6) {
      return `${sign}${prefix}${(abs / 1e6).toFixed(2)}M`;
    }
  }

  // 1 Crore = 10,000,000 (1e7)
  if (abs >= 1e7) {
    const cr = abs / 1e7;
    return `${sign}${prefix}${cr.toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })} Cr`;
  }
  // 1 Lakh = 100,000 (1e5)
  if (abs >= 1e5) {
    const l = abs / 1e5;
    return `${sign}${prefix}${l.toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })} L`;
  }
  return `${sign}${prefix}${abs.toLocaleString(isUS ? "en-US" : "en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatRatio(val, suffix = "") {
  if (val === undefined || val === null || isNaN(val)) return "—";
  return `${Number(val).toFixed(2)}${suffix}`;
}

function formatTimestamp(isoStr) {
  if (!isoStr) return "—";
  try {
    const d = new Date(isoStr);
    return d.toLocaleString("en-IN", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      timeZoneName: "short",
    });
  } catch {
    return isoStr;
  }
}

function Research() {
  const navigate = useNavigate();

  // User and session
  const token = sessionStorage.getItem("access_token");
  const user = JSON.parse(sessionStorage.getItem("user") || "null");

  const storageKey = `stockly_research_${user?.user_id || user?.email || "current"}`;

  // Restore previously saved Research data
  const [savedResearch] = useState(() => {
    try {
      return JSON.parse(
        sessionStorage.getItem(storageKey) || "{}"
      );
    } catch {
      return {};
    }
  });

  // State
  const [searchQuery, setSearchQuery] = useState(
    savedResearch.searchQuery || ""
  );
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStock, setSelectedStock] = useState(
    savedResearch.selectedStock || null
  );
  const [analysisPeriod, setAnalysisPeriod] = useState(
    savedResearch.analysisPeriod || "1y"
  );
  const [historicalData, setHistoricalData] = useState(
    savedResearch.historicalData || []
  );

  // Tab State: 'chart' | 'profile' | 'financials'
  const [activeTab, setActiveTab] = useState("chart");

  // Company Profile State
  const [profileData, setProfileData] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState("");

  // Financial Statements State
  const [financialStatement, setFinancialStatement] = useState("income"); // 'income' | 'balance_sheet' | 'cashflow'
  const [financialFrequency, setFinancialFrequency] = useState("annual"); // 'annual' | 'quarterly'
  const [financialsData, setFinancialsData] = useState(null);
  const [financialsLoading, setFinancialsLoading] = useState(false);
  const [financialsError, setFinancialsError] = useState("");
  const [financialSearch, setFinancialSearch] = useState("");

  const [showAllRecords, setShowAllRecords] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [researchLoading, setResearchLoading] = useState(false);

  // Data retrieval metadata
  const [retrievedAt, setRetrievedAt] = useState(null);
  const [dataSource, setDataSource] = useState("");

  const [hoverIndex, setHoverIndex] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  // Save Research data automatically
  useEffect(() => {
    if (!user) return;

    sessionStorage.setItem(
      storageKey,
      JSON.stringify({
        searchQuery,
        selectedStock,
        analysisPeriod,
        historicalData,
      })
    );
  }, [
    user,
    storageKey,
    searchQuery,
    selectedStock,
    analysisPeriod,
    historicalData,
  ]);

  // Login check
  useEffect(() => {
    if (!token || !user) {
      navigate("/login", { replace: true });
    }
  }, [navigate, token, user]);

  // Logout
  const logout = () => {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    navigate("/login");
  };

  // Search companies
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
      setHistoricalData([]);
      setProfileData(null);
      setFinancialsData(null);
      setSearchResults([]);
      setShowAllRecords(false);

      const response = await searchStocks(searchQuery.trim());
      setSearchResults(response.results || []);

      if (!response.results?.length) {
        setMessage("No matching NSE, BSE, NASDAQ or NYSE stocks found.");
      }
    } catch (err) {
      if (err.response?.status === 401) {
        logout();
        return;
      }

      setError(
        err.response?.data?.detail || "Unable to search stocks."
      );
    } finally {
      setSearchLoading(false);
    }
  };

  // Retrieve historical OHLCV data
  const loadHistoricalData = useCallback(async (stock, period) => {
    if (!stock) return;

    try {
      setHistoryLoading(true);
      setHoverIndex(null);
      setError("");
      setMessage("Loading historical market data...");
      setRetrievedAt(null);
      setDataSource("");

      const response = await getStockHistory(
        stock.ticker,
        stock.market,
        period
      );

      if (!response.success || !response.data?.length) {
        throw new Error("No historical stock records found.");
      }

      setHistoricalData(response.data);
      setShowAllRecords(false);
      setRetrievedAt(response.retrieved_at || null);
      setDataSource(response.data_source || "Yahoo Finance (via yfinance)");

      setMessage(
        `${response.total_records} historical records loaded successfully.`
      );
    } catch (err) {
      if (err.response?.status === 401) {
        logout();
        return;
      }

      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to retrieve historical data."
      );
      setMessage("");
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // Retrieve Company Profile
  const loadProfile = useCallback(async (stock) => {
    if (!stock) return;
    try {
      setProfileLoading(true);
      setProfileError("");
      const res = await getCompanyProfile(stock.ticker, stock.market);
      if (res && res.success) {
        setProfileData(res);
      } else {
        setProfileError(res?.message || "Failed to load company profile.");
      }
    } catch (err) {
      if (err.response?.status === 401) {
        logout();
        return;
      }
      setProfileError(
        err.response?.data?.detail ||
          err.message ||
          "Failed to load company profile."
      );
    } finally {
      setProfileLoading(false);
    }
  }, []);

  // Retrieve Financial Statement
  const loadFinancials = useCallback(async (stock, stmt, freq) => {
    if (!stock) return;
    try {
      setFinancialsLoading(true);
      setFinancialsError("");
      const res = await getFinancialStatement(
        stock.ticker,
        stock.market,
        stmt,
        freq
      );
      if (res && res.success) {
        setFinancialsData(res);
      } else {
        setFinancialsError(res?.message || "Financial statement unavailable.");
      }
    } catch (err) {
      if (err.response?.status === 401) {
        logout();
        return;
      }
      setFinancialsError(
        err.response?.data?.detail ||
          err.message ||
          "Financial statement unavailable."
      );
    } finally {
      setFinancialsLoading(false);
    }
  }, []);

  // Reload historical data when selected stock or period changes
  useEffect(() => {
    if (selectedStock) {
      loadHistoricalData(selectedStock, analysisPeriod);
    }
  }, [selectedStock, analysisPeriod, loadHistoricalData]);

  // Load Profile or Financials when switching to those tabs
  useEffect(() => {
    if (!selectedStock) return;
    if (activeTab === "profile" && !profileData) {
      loadProfile(selectedStock);
    } else if (activeTab === "financials") {
      loadFinancials(selectedStock, financialStatement, financialFrequency);
    }
  }, [
    selectedStock,
    activeTab,
    profileData,
    financialStatement,
    financialFrequency,
    loadProfile,
    loadFinancials,
  ]);

  // Create a research task
  const handleStartResearch = async () => {
    if (!selectedStock || historicalData.length === 0) {
      setError("Load historical data before starting research.");
      return;
    }

    try {
      setResearchLoading(true);
      setError("");

      await createResearchTask({
        company_name: selectedStock.company_name,
        ticker: selectedStock.ticker,
        market: selectedStock.market,
        analysis_period: analysisPeriod,
      });

      setMessage(
        "Research task created successfully. Historical data is available above."
      );
    } catch (err) {
      if (err.response?.status === 401) {
        logout();
        return;
      }

      setError(
        err.response?.data?.detail ||
          "Unable to create research task."
      );
    } finally {
      setResearchLoading(false);
    }
  };

  // Download all historical records as CSV
  const downloadCSV = () => {
    if (!historicalData.length || !selectedStock) return;

    const headers = [
      "Date",
      "Open",
      "High",
      "Low",
      "Close",
      "Volume",
    ];

    const escapeCSV = (value) => {
      const text = String(value ?? "");
      return `"${text.replace(/"/g, '""')}"`;
    };

    const rows = historicalData.map((item) => [
      item.date,
      item.open,
      item.high,
      item.low,
      item.close,
      item.volume,
    ]);

    const csvContent = [headers, ...rows]
      .map((row) => row.map(escapeCSV).join(","))
      .join("\n");

    const blob = new Blob(["\uFEFF", csvContent], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = `${selectedStock.ticker}_${analysisPeriod}_historical_data.csv`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  // Graph coordinates
  const graphWidth = 900;
  const graphHeight = 300;
  const graphPadding = 55;

  const prices = useMemo(
    () => (historicalData.length ? historicalData.map((item) => item.close) : []),
    [historicalData]
  );

  const minPrice = useMemo(
    () => (prices.length ? Math.min(...prices) : 0),
    [prices]
  );
  const maxPrice = useMemo(
    () => (prices.length ? Math.max(...prices) : 0),
    [prices]
  );
  const priceRange = maxPrice - minPrice || 1;

  const chartPoints = useMemo(() => {
    return historicalData.map((item, index) => {
      const x =
        graphPadding +
        (index / Math.max(historicalData.length - 1, 1)) *
          (graphWidth - graphPadding * 2);

      const y =
        graphHeight -
        graphPadding -
        ((item.close - minPrice) / priceRange) *
          (graphHeight - graphPadding * 2);

      return { x, y, ...item };
    });
  }, [historicalData, minPrice, priceRange]);

  const chartLine = useMemo(() => {
    return chartPoints.map((point) => `${point.x},${point.y}`).join(" ");
  }, [chartPoints]);

  const chartArea = useMemo(() => {
    return chartPoints.length
      ? `${chartLine} ${chartPoints[chartPoints.length - 1].x},${graphHeight - graphPadding} ${chartPoints[0].x},${graphHeight - graphPadding}`
      : "";
  }, [chartPoints, chartLine]);

  const selectedPoint =
    hoverIndex !== null ? chartPoints[hoverIndex] : null;

  // Daily price change: calculated using latest close and previous trading day's close
  const dailyChange = useMemo(() => {
    if (!historicalData || historicalData.length === 0) return null;
    const latest = historicalData[historicalData.length - 1].close;
    const prev =
      historicalData.length > 1
        ? historicalData[historicalData.length - 2].close
        : latest;
    const diff = latest - prev;
    const pct = prev ? ((diff / prev) * 100).toFixed(2) : "0.00";
    const isUp = diff >= 0;
    return { latest, prev, diff, pct, isUp };
  }, [historicalData]);

  // Collect and filter all financial statement line items across all available reporting periods
  const financialLineItems = useMemo(() => {
    if (!financialsData || !financialsData.data || !financialsData.reporting_periods?.length) {
      return [];
    }
    // Aggregate unique line items across all available periods to ensure no metric is omitted
    const allItems = new Set();
    financialsData.reporting_periods.forEach((period) => {
      const pData = financialsData.data[period];
      if (pData && typeof pData === "object") {
        Object.keys(pData).forEach((key) => allItems.add(key));
      }
    });
    const items = Array.from(allItems);
    if (!financialSearch.trim()) return items;
    const q = financialSearch.toLowerCase();
    return items.filter((item) => item.toLowerCase().includes(q));
  }, [financialsData, financialSearch]);

  const currSymbol = getCurrencyPrefix(selectedStock?.market, profileData?.profile?.currency);

  if (!user) return null;

  return (
    <DashboardLayout user={user} onLogout={logout}>
      <div className="research-page">

        {/* PAGE HEADING */}
        <div className="research-heading">
          <div>
            <span className="research-eyebrow">
              COMPANY INTELLIGENCE WORKSPACE
            </span>
            <h1>Company Research Workspace</h1>
            <p>
              In-depth single-company intelligence, technical price movement, verified corporate profiles, company-reported financial statements, and AI research generation.
            </p>
          </div>
        </div>

        {/* STOCK SEARCH */}
        <section className="research-panel">
          <h2>Find a Company</h2>
          <p>Search for stocks listed on NSE, BSE, NASDAQ and NYSE.</p>

          <div className="research-search">
            <input
              type="search"
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
              spellCheck="false"
              name="research-stock-search"
              id="research-stock-search"
              placeholder="Search TCS, Reliance, Apple, Microsoft, Coca-Cola..."
              value={searchQuery}
              onChange={(e) => {
                const val = e.target.value;
                setSearchQuery(val);
                if (val.trim() === "") {
                  setSearchResults([]);
                  setSelectedStock(null);
                  setHistoricalData([]);
                  setProfileData(null);
                  setFinancialsData(null);
                  setMessage("");
                  setError("");
                  setRetrievedAt(null);
                  setDataSource("");
                }
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleStockSearch();
              }}
            />

            <button
              onClick={handleStockSearch}
              disabled={searchLoading}
            >
              {searchLoading ? "Searching..." : "Search Stocks"}
            </button>
          </div>

          {/* SEARCH RESULTS */}
          {searchResults.length > 0 && (
            <div className="research-results">
              <h3>Matching Companies</h3>

              {searchResults.map((stock) => (
                <div
                  className="research-stock-result"
                  key={`${stock.ticker}-${stock.market}`}
                >
                  <div>
                    <strong>{stock.company_name}</strong>
                    <p>
                      {stock.ticker} · {stock.market}
                    </p>
                    <small>
                      {stock.sector || "Sector unavailable"}
                    </small>
                  </div>

                  <button
                    onClick={() => {
                      setSelectedStock(stock);
                      setSearchResults([]);
                      setProfileData(null);
                      setFinancialsData(null);
                      setProfileError("");
                      setFinancialsError("");
                      setMessage("");
                      setError("");
                    }}
                    disabled={
                      selectedStock?.ticker === stock.ticker &&
                      selectedStock?.market === stock.market
                    }
                  >
                    Select
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* SELECTED STOCK AND PERIOD */}
          {selectedStock && (
            <div className="research-selected-stock">
              <div>
                <span>SELECTED COMPANY</span>
                <h3>{selectedStock.company_name}</h3>
                <p>
                  {selectedStock.ticker} · {selectedStock.market}
                </p>
              </div>

              {activeTab === "chart" && (
                <div className="research-period">
                  <label htmlFor="analysisPeriod">
                    Historical Period
                  </label>

                  <select
                    id="analysisPeriod"
                    value={analysisPeriod}
                    onChange={(e) => setAnalysisPeriod(e.target.value)}
                  >
                    <option value="1mo">1 Month</option>
                    <option value="3mo">3 Months</option>
                    <option value="6mo">6 Months</option>
                    <option value="1y">1 Year</option>
                    <option value="5y">5 Years</option>
                  </select>
                </div>
              )}
            </div>
          )}

          {/* RESEARCH NAVIGATION TABS */}
          {selectedStock && (
            <div className="rs-tabs-container">
              <button
                className={`rs-tab-pill ${activeTab === "chart" ? "active" : ""}`}
                onClick={() => setActiveTab("chart")}
              >
                <span className="rs-tab-icon">📈</span> Market Movement
              </button>
              <button
                className={`rs-tab-pill ${activeTab === "profile" ? "active" : ""}`}
                onClick={() => {
                  setActiveTab("profile");
                  if (!profileData) {
                    loadProfile(selectedStock);
                  }
                }}
              >
                <span className="rs-tab-icon">🏛️</span> Company Profile
              </button>
              <button
                className={`rs-tab-pill ${activeTab === "financials" ? "active" : ""}`}
                onClick={() => {
                  setActiveTab("financials");
                  loadFinancials(selectedStock, financialStatement, financialFrequency);
                }}
              >
                <span className="rs-tab-icon">📑</span> Financial Statements
              </button>
            </div>
          )}

          {historyLoading && activeTab === "chart" && (
            <p className="research-loading">
              Retrieving historical market data...
            </p>
          )}

          {message && activeTab === "chart" && (
            <p className="research-success">{message}</p>
          )}

          {error && activeTab === "chart" && (
            <p className="research-error">{error}</p>
          )}
        </section>

        {/* =========================================================================
            TAB 1: MARKET MOVEMENT (OHLCV CHART & HISTORICAL TABLE)
        ========================================================================= */}
        {activeTab === "chart" && historicalData.length > 0 && selectedStock && (
          <>
            <section className="research-panel">
              <div className="research-chart-heading">
                <div>
                  <span>HISTORICAL PRICE MOVEMENT</span>
                  <h2>{selectedStock.company_name}</h2>
                  <p>
                    {selectedStock.ticker} · {analysisPeriod}
                  </p>
                </div>

                {dailyChange && (
                  <div className="research-chart-price">
                    <span>LATEST CLOSE</span>
                    <div className="rs-chart-price-row">
                      <strong>{currSymbol}{formatPrice(dailyChange.latest, selectedStock?.market)}</strong>
                      <span
                        className={`rs-daily-change-pill ${
                          dailyChange.isUp ? "up" : "down"
                        }`}
                      >
                        {dailyChange.isUp ? "▲ +" : "▼ "}
                        {currSymbol}{formatPrice(Math.abs(dailyChange.diff), selectedStock?.market)} (
                        {dailyChange.pct}%)
                      </span>
                    </div>
                    <small className="rs-chart-daily-note">
                      vs prev close ({dailyChange.prev ? `${currSymbol}${formatPrice(dailyChange.prev, selectedStock?.market)}` : "—"})
                    </small>
                  </div>
                )}
              </div>

              <div className="research-chart-legend">
                <span></span>
                Closing Price ({profileData?.profile?.currency || (selectedStock?.market === "NASDAQ" || selectedStock?.market === "NYSE" ? "USD" : "INR")})
              </div>

              {/* GRAPH */}
              <div className="research-chart-container">
                <svg
                  viewBox={`0 0 ${graphWidth} ${graphHeight}`}
                  preserveAspectRatio="none"
                  className="research-chart"
                >
                  {Array.from({ length: 5 }, (_, index) => {
                    const y =
                      graphPadding +
                      index *
                        ((graphHeight - graphPadding * 2) / 4);

                    const value =
                      maxPrice - index * (priceRange / 4);

                    return (
                      <g key={index}>
                        <line
                          x1={graphPadding}
                          y1={y}
                          x2={graphWidth - graphPadding}
                          y2={y}
                          className="research-grid-line"
                        />

                        <text
                          x="5"
                          y={y + 4}
                          className="research-axis-label"
                        >
                          {formatPrice(value)}
                        </text>
                      </g>
                    );
                  })}

                  <polygon
                    points={chartArea}
                    className="research-chart-area"
                  />

                  <polyline
                    points={chartLine}
                    className="research-chart-line"
                  />

                  {chartPoints.map((point, index) => (
                    <circle
                      key={index}
                      cx={point.x}
                      cy={point.y}
                      r={hoverIndex === index ? 6 : 2.5}
                      className="research-chart-point"
                      onMouseEnter={() => setHoverIndex(index)}
                      onMouseLeave={() => setHoverIndex(null)}
                    />
                  ))}

                  <text
                    x={graphPadding}
                    y={graphHeight - 12}
                    className="research-axis-label"
                  >
                    {historicalData[0].date}
                  </text>

                  <text
                    x={graphWidth - graphPadding}
                    y={graphHeight - 12}
                    textAnchor="end"
                    className="research-axis-label"
                  >
                    {historicalData[historicalData.length - 1].date}
                  </text>
                </svg>
              </div>

              {/* GRAPH TOOLTIP */}
              {selectedPoint && (
                <div className="research-chart-tooltip">
                  <strong>{selectedPoint.date}</strong>
                  <span>Open: {currSymbol}{formatPrice(selectedPoint.open, selectedStock?.market)}</span>
                  <span>High: {currSymbol}{formatPrice(selectedPoint.high, selectedStock?.market)}</span>
                  <span>Low: {currSymbol}{formatPrice(selectedPoint.low, selectedStock?.market)}</span>
                  <span>Close: {currSymbol}{formatPrice(selectedPoint.close, selectedStock?.market)}</span>
                  <span>
                    Volume: {Number(selectedPoint.volume || 0).toLocaleString(
                      selectedStock?.market === "NASDAQ" || selectedStock?.market === "NYSE" ? "en-US" : "en-IN"
                    )}
                  </span>
                </div>
              )}

              {/* GRAPH SUMMARY */}
              <div className="research-chart-summary">
                <div>
                  <span>HIGHEST CLOSE</span>
                  <strong>{currSymbol}{formatPrice(maxPrice, selectedStock?.market)}</strong>
                </div>

                <div>
                  <span>LOWEST CLOSE</span>
                  <strong>{currSymbol}{formatPrice(minPrice, selectedStock?.market)}</strong>
                </div>

                <div>
                  <span>DATA RECORDS</span>
                  <strong>{historicalData.length}</strong>
                </div>
              </div>

              <button
                className="research-start-button"
                onClick={handleStartResearch}
                disabled={researchLoading || historyLoading}
              >
                {researchLoading
                  ? "Creating..."
                  : "Create Research Task"}
              </button>
            </section>

            {/* HISTORICAL DATA TABLE */}
            <section className="research-panel">
              <div className="research-table-heading">
                <div>
                  <h2>Historical Market Dataset</h2>
                  <p>
                    Complete OHLCV records returned by your market data provider.
                  </p>
                </div>

                <div className="research-table-actions">
                  <span>{historicalData.length} RECORDS</span>

                  <button
                    className="research-download-btn"
                    onClick={downloadCSV}
                    disabled={!historicalData.length}
                  >
                    Download CSV
                  </button>

                  <button
                    className="research-view-all-btn"
                    onClick={() => setShowAllRecords((previous) => !previous)}
                    aria-expanded={showAllRecords}
                  >
                    {showAllRecords
                      ? "↑ Show less"
                      : "↓ View all records"}
                  </button>
                </div>
              </div>

              {/* DATA RETRIEVAL METADATA STRIP */}
              {historicalData.length > 0 && (
                <div className="research-retrieval-strip">
                  <span className="research-retrieval-item">
                    <Clock size={12} className="research-retrieval-icon" />
                    <span className="research-retrieval-label">Data Source:</span>
                    <span className="research-retrieval-value">
                      {dataSource || "Yahoo Finance (via yfinance)"}
                    </span>
                  </span>
                  <span className="research-retrieval-sep">·</span>
                  <span className="research-retrieval-item">
                    <span className="research-retrieval-label">Last Retrieved:</span>
                    <span className="research-retrieval-value">
                      {formatRetrievedAt(retrievedAt)}
                    </span>
                  </span>
                </div>
              )}

              <div className="research-table-container">
                <table className="research-data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Open ({currSymbol})</th>
                      <th>High ({currSymbol})</th>
                      <th>Low ({currSymbol})</th>
                      <th>Close ({currSymbol})</th>
                      <th>Volume</th>
                    </tr>
                  </thead>

                  <tbody>
                    {(showAllRecords
                      ? [...historicalData].reverse()
                      : [...historicalData].reverse().slice(0, 4)
                    ).map((item, index) => (
                      <tr key={`${item.date}-${index}`}>
                        <td>{item.date}</td>
                        <td>{formatPrice(item.open, selectedStock?.market)}</td>
                        <td>{formatPrice(item.high, selectedStock?.market)}</td>
                        <td>{formatPrice(item.low, selectedStock?.market)}</td>
                        <td className="research-close-price">
                          {formatPrice(item.close, selectedStock?.market)}
                        </td>
                        <td>
                          {Number(item.volume || 0).toLocaleString("en-IN")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}

        {/* =========================================================================
            TAB 2: COMPANY PROFILE
        ========================================================================= */}
        {activeTab === "profile" && selectedStock && (
          <section className="research-panel cp-panel">
            {profileLoading ? (
              <div className="cp-loading-state">
                <div className="cp-spinner" />
                <p>Retrieving verified company profile from Yahoo Finance...</p>
              </div>
            ) : profileError ? (
              <div className="cp-error-state">
                <p className="research-error">{profileError}</p>
                <button
                  className="db-btn-secondary"
                  onClick={() => loadProfile(selectedStock)}
                >
                  ↻ Retry Profile Retrieval
                </button>
              </div>
            ) : profileData?.profile ? (
              <div className="cp-container">
                {/* Audit & Provider Metadata Strip */}
                <div className="cp-audit-bar">
                  <div className="cp-audit-item">
                    <span className="cp-audit-label">DATA PROVIDER</span>
                    <strong className="cp-audit-value">{profileData.data_source}</strong>
                  </div>
                  <div className="cp-audit-item">
                    <span className="cp-audit-label">RETRIEVAL TIMESTAMP</span>
                    <strong className="cp-audit-value">
                      {formatTimestamp(profileData.retrieved_at)}
                    </strong>
                  </div>
                  <div className="cp-audit-item">
                    <span className="cp-audit-label">EXCHANGE</span>
                    <strong className="cp-audit-value">
                      {profileData.profile.exchange || selectedStock.market}
                    </strong>
                  </div>
                  <div className="cp-audit-item">
                    <span className="cp-audit-label">CURRENCY</span>
                    <strong className="cp-audit-value">
                      {profileData.profile.currency || "INR"}
                    </strong>
                  </div>
                </div>

                {/* Validation Warnings if any */}
                {profileData.validation_warnings?.length > 0 && (
                  <div className="cp-warning-box">
                    <strong>⚠️ Provider Validation Notice:</strong>
                    <ul>
                      {profileData.validation_warnings.map((w, idx) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Hero Profile Card */}
                <div className="cp-hero-card">
                  <div className="cp-hero-left">
                    <div className="cp-tag-row">
                      <span className="cp-tag cp-tag-market">{profileData.profile.market}</span>
                      {profileData.profile.sector && (
                        <span className="cp-tag cp-tag-sector">{profileData.profile.sector}</span>
                      )}
                      {profileData.profile.industry && (
                        <span className="cp-tag cp-tag-industry">{profileData.profile.industry}</span>
                      )}
                    </div>
                    <h2 className="cp-company-title">{profileData.profile.company_name}</h2>
                    <p className="cp-company-symbol">
                      Ticker: <strong>{profileData.profile.ticker_symbol}</strong> · Country:{" "}
                      <strong>{profileData.profile.country || "India"}</strong>
                    </p>
                  </div>

                  <div className="cp-hero-right">
                    {profileData.profile.website && (
                      <a
                        href={profileData.profile.website}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="cp-website-btn"
                      >
                        🌐 Visit Corporate Website ↗
                      </a>
                    )}
                    {profileData.profile.employees && (
                      <div className="cp-employee-stat">
                        <span>Total Employees</span>
                        <strong>
                          {Number(profileData.profile.employees).toLocaleString("en-IN")}
                        </strong>
                      </div>
                    )}
                  </div>
                </div>

                {/* Key Market & Valuation Metrics Grid */}
                <h3 className="cp-section-title">Market Capitalisation &amp; Valuation Ratios</h3>
                <div className="cp-stats-grid">
                  <div className="cp-stat-box">
                    <span>Market Capitalisation</span>
                    <strong>{formatLargeNumber(profileData.profile.market_cap, profileData.profile.currency)}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Current Market Price</span>
                    <strong>{currSymbol}{formatPrice(profileData.profile.current_price, selectedStock?.market)}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Previous Close</span>
                    <strong>{currSymbol}{formatPrice(profileData.profile.previous_close, selectedStock?.market)}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>52-Week Range</span>
                    <strong>
                      {currSymbol}{formatPrice(profileData.profile.fifty_two_week_low, selectedStock?.market)} – {currSymbol}{formatPrice(profileData.profile.fifty_two_week_high, selectedStock?.market)}
                    </strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Trailing P/E Ratio</span>
                    <strong>{formatRatio(profileData.profile.trailing_pe, "x")}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Forward P/E Ratio</span>
                    <strong>{formatRatio(profileData.profile.forward_pe, "x")}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Price-to-Book (P/B)</span>
                    <strong>{formatRatio(profileData.profile.price_to_book, "x")}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Beta (Volatility)</span>
                    <strong>{formatRatio(profileData.profile.beta)}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Dividend Yield</span>
                    <strong>{formatRatio(profileData.profile.dividend_yield, "%")}</strong>
                  </div>
                </div>

                {/* Financial Health Summary */}
                <h3 className="cp-section-title">Financial Health &amp; Performance Summary</h3>
                <div className="cp-stats-grid">
                  <div className="cp-stat-box">
                    <span>Total Revenue</span>
                    <strong>{formatLargeNumber(profileData.profile.total_revenue, profileData.profile.currency)}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Gross Profits</span>
                    <strong>{formatLargeNumber(profileData.profile.gross_profits, profileData.profile.currency)}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>EBITDA</span>
                    <strong>{formatLargeNumber(profileData.profile.ebitda, profileData.profile.currency)}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Net Income</span>
                    <strong>{formatLargeNumber(profileData.profile.net_income, profileData.profile.currency)}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Total Cash</span>
                    <strong>{formatLargeNumber(profileData.profile.total_cash, profileData.profile.currency)}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Total Debt</span>
                    <strong>{formatLargeNumber(profileData.profile.total_debt, profileData.profile.currency)}</strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Return on Equity (ROE)</span>
                    <strong>
                      {profileData.profile.return_on_equity !== null
                        ? `${(profileData.profile.return_on_equity * 100).toFixed(2)}%`
                        : "—"}
                    </strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Return on Assets (ROA)</span>
                    <strong>
                      {profileData.profile.return_on_assets !== null
                        ? `${(profileData.profile.return_on_assets * 100).toFixed(2)}%`
                        : "—"}
                    </strong>
                  </div>
                  <div className="cp-stat-box">
                    <span>Profit Margin</span>
                    <strong>
                      {profileData.profile.profit_margins !== null
                        ? `${(profileData.profile.profit_margins * 100).toFixed(2)}%`
                        : "—"}
                    </strong>
                  </div>
                </div>

                {/* Business Description */}
                {profileData.profile.description && (
                  <div className="cp-description-panel">
                    <h3>About {profileData.profile.company_name}</h3>
                    <p>{profileData.profile.description}</p>
                  </div>
                )}
              </div>
            ) : null}
          </section>
        )}

        {/* =========================================================================
            TAB 3: FINANCIAL STATEMENTS (INCOME, BALANCE SHEET, CASH FLOW)
        ========================================================================= */}
        {activeTab === "financials" && selectedStock && (
          <section className="research-panel fs-panel">
            {/* Statement & Frequency Selector Toolbar */}
            <div className="fs-toolbar">
              <div className="fs-statement-selector">
                <span className="fs-selector-label">STATEMENT:</span>
                <div className="fs-btn-group">
                  <button
                    className={`fs-btn ${financialStatement === "income" ? "active" : ""}`}
                    onClick={() => {
                      setFinancialStatement("income");
                      loadFinancials(selectedStock, "income", financialFrequency);
                    }}
                  >
                    Income Statement
                  </button>
                  <button
                    className={`fs-btn ${financialStatement === "balance_sheet" ? "active" : ""}`}
                    onClick={() => {
                      setFinancialStatement("balance_sheet");
                      loadFinancials(selectedStock, "balance_sheet", financialFrequency);
                    }}
                  >
                    Balance Sheet
                  </button>
                  <button
                    className={`fs-btn ${financialStatement === "cashflow" ? "active" : ""}`}
                    onClick={() => {
                      setFinancialStatement("cashflow");
                      loadFinancials(selectedStock, "cashflow", financialFrequency);
                    }}
                  >
                    Cash Flow Statement
                  </button>
                </div>
              </div>

              <div className="fs-frequency-selector">
                <span className="fs-selector-label">PERIOD FREQUENCY:</span>
                <div className="fs-btn-group">
                  <button
                    className={`fs-btn ${financialFrequency === "annual" ? "active" : ""}`}
                    onClick={() => {
                      setFinancialFrequency("annual");
                      loadFinancials(selectedStock, financialStatement, "annual");
                    }}
                  >
                    Annual (FY)
                  </button>
                  <button
                    className={`fs-btn ${financialFrequency === "quarterly" ? "active" : ""}`}
                    onClick={() => {
                      setFinancialFrequency("quarterly");
                      loadFinancials(selectedStock, financialStatement, "quarterly");
                    }}
                  >
                    Quarterly (Q)
                  </button>
                </div>
              </div>
            </div>

            {/* Audit & Provider Metadata Strip */}
            {financialsData && (
              <div className="cp-audit-bar">
                <div className="cp-audit-item">
                  <span className="cp-audit-label">DATA PROVIDER</span>
                  <strong className="cp-audit-value">{financialsData.data_source}</strong>
                </div>
                <div className="cp-audit-item">
                  <span className="cp-audit-label">RETRIEVAL TIMESTAMP</span>
                  <strong className="cp-audit-value">
                    {formatTimestamp(financialsData.retrieved_at)}
                  </strong>
                </div>
                <div className="cp-audit-item">
                  <span className="cp-audit-label">REPORTING PERIODS</span>
                  <strong className="cp-audit-value">
                    {financialsData.reporting_periods?.length || 0} Periods Available
                  </strong>
                </div>
                <div className="cp-audit-item">
                  <span className="cp-audit-label">FREQUENCY</span>
                  <strong className="cp-audit-value">
                    {financialFrequency.toUpperCase()}
                  </strong>
                </div>
              </div>
            )}

            {/* Validation Warnings or Verification Card */}
            {financialsData?.validation_warnings?.length > 0 ? (
              <div className="fs-warning-card">
                <div className="fs-warning-header">
                  <span className="fs-warning-badge">⚠️ Validation Notice</span>
                  <span className="fs-warning-count">
                    {financialsData.validation_warnings.length} {financialsData.validation_warnings.length === 1 ? "metric warning" : "metric warnings"} detected
                  </span>
                </div>
                <p className="fs-warning-desc">
                  The data provider omitted the following financial metrics for certain reporting periods. All available financial metrics and reporting periods are fully preserved below. Unavailable values are displayed as <code>—</code>.
                </p>
                <ul className="fs-warning-list">
                  {financialsData.validation_warnings.map((w, idx) => (
                    <li key={idx} className="fs-warning-item">
                      <span className="fs-warning-bullet">•</span>
                      <span>{w}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : financialsData ? (
              <div className="fs-verified-card">
                <span className="fs-verified-badge">✓ Verified Complete</span>
                <span className="fs-verified-text">
                  All core financial metrics were successfully retrieved for all available reporting periods.
                </span>
              </div>
            ) : null}

            {/* Line items filter input */}
            <div className="fs-filter-row">
              <input
                type="search"
                autoComplete="off"
                spellCheck="false"
                className="fs-filter-input"
                placeholder="Filter line items (e.g. Revenue, EBITDA, Debt, Cash, Equity)..."
                value={financialSearch}
                onChange={(e) => setFinancialSearch(e.target.value)}
              />
              {financialSearch && (
                <button
                  className="fs-clear-filter"
                  onClick={() => setFinancialSearch("")}
                >
                  Clear filter
                </button>
              )}
            </div>

            {/* Loading / Error / Data States */}
            {financialsLoading ? (
              <div className="cp-loading-state">
                <div className="cp-spinner" />
                <p>Retrieving {financialFrequency} {financialStatement.replace("_", " ")} from provider...</p>
              </div>
            ) : financialsError ? (
              <div className="cp-error-state">
                <p className="research-error">{financialsError}</p>
                <button
                  className="db-btn-secondary"
                  onClick={() =>
                    loadFinancials(selectedStock, financialStatement, financialFrequency)
                  }
                >
                  ↻ Retry Retrieval
                </button>
              </div>
            ) : financialsData && financialsData.data && financialsData.reporting_periods?.length ? (
              <div className="fs-table-wrapper">
                <table className="fs-table">
                  <thead>
                    <tr>
                      <th className="fs-th-metric">Line Item / Metric</th>
                      {financialsData.reporting_periods.map((periodDate) => {
                        const pData = financialsData.data[periodDate];
                        const nonNullCount = pData
                          ? Object.values(pData).filter((v) => v !== null && v !== undefined && !isNaN(v)).length
                          : 0;
                        const totalMetrics = pData ? Object.keys(pData).length : 0;
                        return (
                          <th key={periodDate} className="fs-th-period">
                            <span className="fs-period-badge">{periodDate}</span>
                            <span className="fs-period-meta" title={`${nonNullCount} of ${totalMetrics} metrics reported by provider`}>
                              {nonNullCount}/{totalMetrics} reported
                            </span>
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody>
                    {financialLineItems.length === 0 ? (
                      <tr>
                        <td
                          colSpan={financialsData.reporting_periods.length + 1}
                          className="fs-empty-td"
                        >
                          No line items match "{financialSearch}".
                        </td>
                      </tr>
                    ) : (
                      financialLineItems.map((item, rowIdx) => (
                        <tr key={item} className={rowIdx % 2 === 0 ? "fs-row-even" : "fs-row-odd"}>
                          <td className="fs-td-metric">{item}</td>
                          {financialsData.reporting_periods.map((periodDate) => {
                            const pData = financialsData.data[periodDate];
                            const val = pData ? pData[item] : undefined;
                            const isAvailable = val !== undefined && val !== null && !isNaN(val);

                            return (
                              <td key={periodDate} className="fs-td-val">
                                {isAvailable ? (
                                  <span
                                    className="fs-valid-val"
                                    title={`Exact value: ${Number(val).toLocaleString("en-IN")}`}
                                  >
                                    {formatLargeNumber(val, "INR")}
                                  </span>
                                ) : (
                                  <span
                                    className="fs-null-val"
                                    title={`Value unavailable for ${periodDate}`}
                                  >
                                    —
                                  </span>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="research-loading">No financial statement records available.</p>
            )}
          </section>
        )}

        {/* RESEARCH HISTORY */}
        <section className="research-panel">
          <h2>Research History</h2>
          <p>
            View your previously created research tasks and reports.
          </p>

          <button
            onClick={() => navigate("/dashboard/history")}
            className="research-history-button"
          >
            View Research History
          </button>
        </section>

      </div>
    </DashboardLayout>
  );
}

export default Research;
