import { useEffect, useState, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";
import {
  getPreferences,
  getStockHistory,
  searchStocks,
  getWatchlist,
} from "../services/authService";

// Default premier companies for NSE and BSE
const DEFAULT_COMPANIES = {
  NSE: [
    { ticker: "TCS", company_name: "Tata Consultancy Services", market: "NSE" },
    { ticker: "RELIANCE", company_name: "Reliance Industries", market: "NSE" },
    { ticker: "INFY", company_name: "Infosys Limited", market: "NSE" },
    { ticker: "HDFCBANK", company_name: "HDFC Bank Limited", market: "NSE" },
    { ticker: "ICICIBANK", company_name: "ICICI Bank Limited", market: "NSE" },
    { ticker: "TATAMOTORS", company_name: "Tata Motors Limited", market: "NSE" },
  ],
  BSE: [
    { ticker: "TCS", company_name: "Tata Consultancy Services", market: "BSE" },
    { ticker: "RELIANCE", company_name: "Reliance Industries", market: "BSE" },
    { ticker: "INFY", company_name: "Infosys Limited", market: "BSE" },
    { ticker: "HDFCBANK", company_name: "HDFC Bank Limited", market: "BSE" },
    { ticker: "ICICIBANK", company_name: "ICICI Bank Limited", market: "BSE" },
    { ticker: "TATAMOTORS", company_name: "Tata Motors Limited", market: "BSE" },
  ],
};

function formatPrice(val) {
  if (val === undefined || val === null || isNaN(val)) return "—";
  return Number(val).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function MediumStockChart({
  company,
  data,
  loading,
  error,
  period,
  indicators,
  width = 640,
  height = 240,
}) {
  const [hoverIndex, setHoverIndex] = useState(null);

  const padding = { top: 20, right: 20, bottom: 35, left: 55 };

  const prices = useMemo(
    () => (data && data.length ? data.map((d) => d.close) : []),
    [data]
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

  const points = useMemo(() => {
    if (!data || !data.length) return [];
    const innerW = width - padding.left - padding.right;
    const innerH = height - padding.top - padding.bottom;

    return data.map((d, i) => {
      const x = padding.left + (i / Math.max(data.length - 1, 1)) * innerW;
      const y =
        padding.top +
        innerH -
        ((d.close - minPrice) / priceRange) * innerH;
      return { ...d, x, y };
    });
  }, [data, width, height, minPrice, priceRange, padding.left, padding.right, padding.top, padding.bottom]);

  const linePath = useMemo(() => {
    if (!points.length) return "";
    return points.map((p) => `${p.x},${p.y}`).join(" ");
  }, [points]);

  const areaPath = useMemo(() => {
    if (!points.length) return "";
    const bottomY = height - padding.bottom;
    return `${linePath} ${points[points.length - 1].x},${bottomY} ${points[0].x},${bottomY}`;
  }, [linePath, points, height, padding.bottom]);

  // Price change calculation
  const stats = useMemo(() => {
    if (!prices.length) return null;
    const first = prices[0];
    const latest = prices[prices.length - 1];
    const diff = latest - first;
    const pct = ((diff / first) * 100).toFixed(2);
    const isUp = diff >= 0;
    return { latest, diff, pct, isUp };
  }, [prices]);

  const activePoint = hoverIndex !== null && points[hoverIndex] ? points[hoverIndex] : null;

  return (
    <div className="mk-chart-card">
      <div className="mk-chart-top">
        <div className="mk-chart-meta">
          <div className="mk-chart-title-row">
            <h3 className="mk-chart-name">{company.company_name}</h3>
            <span className="mk-ticker-badge">{company.ticker}</span>
            <span className="mk-market-badge">{company.market}</span>
          </div>
          <span className="mk-period-label">{period} Price Trend</span>
        </div>

        {stats && (
          <div className="mk-chart-price-block">
            <span className="mk-current-price">₹{formatPrice(stats.latest)}</span>
            <span className={`mk-change-pill ${stats.isUp ? "up" : "down"}`}>
              {stats.isUp ? "▲ +" : "▼ "}
              ₹{formatPrice(Math.abs(stats.diff))} ({stats.pct}%)
            </span>
          </div>
        )}
      </div>

      {indicators && indicators.length > 0 && (
        <div className="mk-indicators-row">
          <span className="mk-ind-label">Indicators:</span>
          {indicators.map((ind) => (
            <span className="mk-ind-chip" key={ind}>
              {ind}
            </span>
          ))}
        </div>
      )}

      <div className="mk-svg-wrapper">
        {loading ? (
          <div className="mk-chart-loader">
            <div className="db-spinner db-spinner-lg" />
            <p>Loading market data...</p>
          </div>
        ) : error ? (
          <div className="mk-chart-error">
            <span>⚠</span>
            <p>{error}</p>
          </div>
        ) : !data || !data.length ? (
          <div className="mk-chart-error">
            <p>No historical data found for {company.ticker}</p>
          </div>
        ) : (
          <svg
            className="mk-svg-chart"
            viewBox={`0 0 ${width} ${height}`}
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient
                id={`mk-grad-${company.ticker}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopColor={stats?.isUp ? "#C6F36B" : "#FF8791"}
                  stopOpacity="0.32"
                />
                <stop
                  offset="100%"
                  stopColor={stats?.isUp ? "#C6F36B" : "#FF8791"}
                  stopOpacity="0.0"
                />
              </linearGradient>
            </defs>

            {/* Gridlines & Price axis */}
            {[0, 1, 2, 3].map((step) => {
              const y =
                padding.top +
                (step / 3) * (height - padding.top - padding.bottom);
              const val = maxPrice - (step / 3) * priceRange;
              return (
                <g key={step}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={width - padding.right}
                    y2={y}
                    className="mk-grid-line"
                  />
                  <text
                    x={padding.left - 8}
                    y={y + 4}
                    textAnchor="end"
                    className="mk-axis-text"
                  >
                    ₹{formatPrice(val)}
                  </text>
                </g>
              );
            })}

            {/* Area & Line */}
            <polygon
              points={areaPath}
              fill={`url(#mk-grad-${company.ticker})`}
            />
            <polyline
              points={linePath}
              className={`mk-poly-line ${stats?.isUp ? "up" : "down"}`}
            />

            {/* Interactive hover points */}
            {points.map((pt, i) => (
              <circle
                key={i}
                cx={pt.x}
                cy={pt.y}
                r={hoverIndex === i ? 5.5 : 2}
                className="mk-chart-dot"
                onMouseEnter={() => setHoverIndex(i)}
                onMouseLeave={() => setHoverIndex(null)}
              />
            ))}

            {/* Dates on X Axis */}
            {data.length > 0 && (
              <>
                <text
                  x={padding.left}
                  y={height - 10}
                  className="mk-axis-text"
                >
                  {data[0].date}
                </text>
                <text
                  x={width - padding.right}
                  y={height - 10}
                  textAnchor="end"
                  className="mk-axis-text"
                >
                  {data[data.length - 1].date}
                </text>
              </>
            )}
          </svg>
        )}
      </div>

      {/* Tooltip bar on hover */}
      {activePoint && (
        <div className="mk-hover-stats">
          <span>
            <strong>Date:</strong> {activePoint.date}
          </span>
          <span>
            <strong>Close:</strong> ₹{formatPrice(activePoint.close)}
          </span>
          <span>
            <strong>High:</strong> ₹{formatPrice(activePoint.high)}
          </span>
          <span>
            <strong>Low:</strong> ₹{formatPrice(activePoint.low)}
          </span>
          <span>
            <strong>Vol:</strong>{" "}
            {Number(activePoint.volume || 0).toLocaleString("en-IN")}
          </span>
        </div>
      )}

      {/* Summary strip */}
      {data && data.length > 0 && (
        <div className="mk-card-footer">
          <div>
            <span>High</span>
            <strong>₹{formatPrice(maxPrice)}</strong>
          </div>
          <div>
            <span>Low</span>
            <strong>₹{formatPrice(minPrice)}</strong>
          </div>
          <div>
            <span>Records</span>
            <strong>{data.length}</strong>
          </div>
        </div>
      )}
    </div>
  );
}

function Markets() {
  const navigate = useNavigate();

  const user = JSON.parse(sessionStorage.getItem("user") || "null");
  const token = sessionStorage.getItem("access_token");

  // Preferences state
  const [preferences, setPreferences] = useState(null);
  const [activeMarket, setActiveMarket] = useState("NSE");
  const [activePeriod, setActivePeriod] = useState("1y");
  const [activeIndicators, setActiveIndicators] = useState([]);

  // Companies & Data state
  const [companiesList, setCompaniesList] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [marketDataMap, setMarketDataMap] = useState({});
  const [loadingMap, setLoadingMap] = useState({});
  const [errorMap, setErrorMap] = useState({});

  // View Mode: 'focus' (medium focused chart) or 'grid' (multiple medium cards)
  const [viewMode, setViewMode] = useState("focus");

  // Search
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Auth guard
  useEffect(() => {
    if (!token || !user) {
      navigate("/login", { replace: true });
    }
  }, [navigate, token, user]);

  const logout = () => {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    navigate("/login");
  };

  // Load Preferences & Watchlist
  useEffect(() => {
    const initData = async () => {
      try {
        const [prefs, watchlist] = await Promise.allSettled([
          getPreferences(),
          getWatchlist(),
        ]);

        let prefMarket = "NSE";
        let prefPeriod = "1y";
        let prefInd = ["SMA", "EMA", "RSI", "MACD"];

        if (prefs.status === "fulfilled" && prefs.value) {
          setPreferences(prefs.value);
          prefMarket = prefs.value.preferred_market || "NSE";
          prefPeriod = prefs.value.preferred_analysis_period || "1y";
          prefInd = prefs.value.preferred_indicators || prefInd;
        }

        setActiveMarket(prefMarket);
        setActivePeriod(prefPeriod);
        setActiveIndicators(prefInd);

        // Build company list starting with defaults for this market
        const defaults = DEFAULT_COMPANIES[prefMarket] || DEFAULT_COMPANIES.NSE;
        const combined = [...defaults];

        // Add user's watchlist companies if they match market
        if (watchlist.status === "fulfilled" && Array.isArray(watchlist.value)) {
          watchlist.value.forEach((wl) => {
            if (
              !combined.some(
                (c) =>
                  c.ticker.toUpperCase() === wl.ticker.toUpperCase() &&
                  c.market.toUpperCase() === wl.market.toUpperCase()
              )
            ) {
              combined.push({
                ticker: wl.ticker,
                company_name: wl.company_name,
                market: wl.market,
              });
            }
          });
        }

        setCompaniesList(combined);
        setSelectedCompany(combined[0]);
      } catch {
        const fallback = DEFAULT_COMPANIES.NSE;
        setCompaniesList(fallback);
        setSelectedCompany(fallback[0]);
      }
    };

    initData();
  }, []);

  // Fetch Stock Data helper
  const fetchStockData = useCallback(
    async (comp, period) => {
      if (!comp || !comp.ticker) return;
      const key = `${comp.ticker}_${comp.market}_${period}`;

      if (marketDataMap[key]) return; // already loaded

      setLoadingMap((prev) => ({ ...prev, [key]: true }));
      setErrorMap((prev) => ({ ...prev, [key]: "" }));

      try {
        const res = await getStockHistory(comp.ticker, comp.market, period);
        if (res && res.success && res.data && res.data.length) {
          setMarketDataMap((prev) => ({ ...prev, [key]: res.data }));
        } else {
          setErrorMap((prev) => ({
            ...prev,
            [key]: res?.message || "No data available",
          }));
        }
      } catch (err) {
        setErrorMap((prev) => ({
          ...prev,
          [key]: err.response?.data?.detail || "Unable to fetch stock history",
        }));
      } finally {
        setLoadingMap((prev) => ({ ...prev, [key]: false }));
      }
    },
    [marketDataMap]
  );

  // Fetch data when selectedCompany or activePeriod changes
  useEffect(() => {
    if (selectedCompany) {
      fetchStockData(selectedCompany, activePeriod);
    }
  }, [selectedCompany, activePeriod, fetchStockData]);

  // When in 'grid' view, fetch data for first 4 companies
  useEffect(() => {
    if (viewMode === "grid" && companiesList.length) {
      companiesList.slice(0, 4).forEach((comp) => {
        fetchStockData(comp, activePeriod);
      });
    }
  }, [viewMode, companiesList, activePeriod, fetchStockData]);

  // Handle market change
  const handleMarketChange = (mkt) => {
    setActiveMarket(mkt);
    const list = DEFAULT_COMPANIES[mkt] || DEFAULT_COMPANIES.NSE;
    setCompaniesList(list);
    setSelectedCompany(list[0]);
  };

  // Search Stocks
  const handleSearch = async () => {
    if (searchQuery.trim().length < 2) return;
    try {
      setSearchLoading(true);
      const res = await searchStocks(searchQuery.trim());
      setSearchResults(res.results || []);
    } catch {
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSelectSearchResult = (stock) => {
    const cleanTicker = (stock.ticker || "").replace(/\.(BO|NS)$/i, "").toUpperCase();
    const newComp = {
      ticker: cleanTicker,
      company_name: stock.company_name,
      market: stock.market || activeMarket,
    };

    // Add to list if not present
    if (
      !companiesList.some(
        (c) =>
          c.ticker.toUpperCase() === newComp.ticker.toUpperCase() &&
          c.market.toUpperCase() === newComp.market.toUpperCase()
      )
    ) {
      setCompaniesList((prev) => [newComp, ...prev]);
    }

    setSelectedCompany(newComp);
    setSearchQuery("");
    setSearchResults([]);
  };

  if (!user) return null;

  return (
    <DashboardLayout user={user} onLogout={logout}>
      <div className="mk-page">
        {/* Header */}
        <header className="mk-header">
          <div>
            <p className="db-eyebrow">MARKET TERMINAL</p>
            <h1 className="mk-title">
              Live Market Trends &amp; <span>Company Graphs</span>
            </h1>
            <p className="mk-subtitle">
              Interactive medium-size technical price charts configured by your preferences
            </p>
          </div>

          <div className="mk-header-actions">
            <button
              className="mk-pref-btn"
              onClick={() => navigate("/dashboard/preferences")}
            >
              ⚙ Edit Preferences
            </button>
          </div>
        </header>

        {/* Preference Banner */}
        <div className="mk-pref-banner">
          <div className="mk-pref-banner-left">
            <span className="mk-banner-tag">ACTIVE PREFERENCES</span>
            <div className="mk-banner-details">
              <span>
                <strong>Market:</strong> {activeMarket}
              </span>
              <span>
                <strong>Period:</strong> {activePeriod}
              </span>
              <span>
                <strong>Risk View:</strong> {preferences?.preferred_risk_view || "Balanced"}
              </span>
            </div>
          </div>

          <div className="mk-pref-banner-right">
            <span className="mk-ind-title">Selected Indicators:</span>
            <div className="mk-ind-pills">
              {activeIndicators.map((ind) => (
                <span key={ind} className="mk-ind-pill">
                  {ind}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Controls Toolbar: Market switch, Period switch, View toggle */}
        <div className="mk-toolbar">
          <div className="mk-toolbar-group">
            <span className="mk-toolbar-label">MARKET:</span>
            <div className="mk-btn-group">
              <button
                className={`mk-seg-btn ${activeMarket === "NSE" ? "active" : ""}`}
                onClick={() => handleMarketChange("NSE")}
              >
                NSE
              </button>
              <button
                className={`mk-seg-btn ${activeMarket === "BSE" ? "active" : ""}`}
                onClick={() => handleMarketChange("BSE")}
              >
                BSE
              </button>
            </div>
          </div>

          <div className="mk-toolbar-group">
            <span className="mk-toolbar-label">PERIOD:</span>
            <div className="mk-btn-group">
              {["1mo", "3mo", "6mo", "1y", "5y"].map((p) => (
                <button
                  key={p}
                  className={`mk-seg-btn ${activePeriod === p ? "active" : ""}`}
                  onClick={() => setActivePeriod(p)}
                >
                  {p.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="mk-toolbar-group mk-view-toggle">
            <span className="mk-toolbar-label">VIEW:</span>
            <div className="mk-btn-group">
              <button
                className={`mk-seg-btn ${viewMode === "focus" ? "active" : ""}`}
                onClick={() => setViewMode("focus")}
              >
                Medium Focus
              </button>
              <button
                className={`mk-seg-btn ${viewMode === "grid" ? "active" : ""}`}
                onClick={() => setViewMode("grid")}
              >
                Medium Grid
              </button>
            </div>
          </div>
        </div>

        {/* Company Quick-Selection Ribbon */}
        <div className="mk-company-ribbon">
          <span className="mk-ribbon-label">SELECT COMPANY:</span>
          <div className="mk-chips-scroll">
            {companiesList.map((comp) => {
              const isSelected =
                selectedCompany &&
                selectedCompany.ticker === comp.ticker &&
                selectedCompany.market === comp.market;
              return (
                <button
                  key={`${comp.ticker}-${comp.market}`}
                  className={`mk-company-chip ${isSelected ? "active" : ""}`}
                  onClick={() => setSelectedCompany(comp)}
                >
                  <strong>{comp.ticker}</strong>
                  <span>{comp.company_name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Search row to pick any custom company */}
        <div className="mk-search-bar-row">
          <input
            type="search"
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            spellCheck="false"
            name="market-search"
            id="market-search"
            className="db-input"
            placeholder="Search another company to graph (e.g. Wipro, SBI, Airtel)..."
            value={searchQuery}
            onChange={(e) => {
              const val = e.target.value;
              setSearchQuery(val);
              if (val.trim() === "") setSearchResults([]);
            }}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <button
            className="db-btn-primary"
            onClick={handleSearch}
            disabled={searchLoading}
          >
            {searchLoading ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Search dropdown results */}
        {searchResults.length > 0 && (
          <div className="mk-search-dropdown">
            <p className="db-results-label">
              Select a company to load its medium-sized price graph:
            </p>
            {searchResults.map((stk) => (
              <div
                key={`${stk.ticker}-${stk.market}`}
                className="mk-search-result-item"
                onClick={() => handleSelectSearchResult(stk)}
              >
                <div>
                  <strong>{stk.company_name}</strong>
                  <span>
                    {stk.ticker} · {stk.market} ({stk.sector || "General"})
                  </span>
                </div>
                <button className="mk-select-btn">Graph →</button>
              </div>
            ))}
          </div>
        )}

        {/* CHARTS CONTAINER */}
        {viewMode === "focus" ? (
          /* SINGLE FOCUSED MEDIUM GRAPH */
          <div className="mk-focus-container">
            {selectedCompany ? (
              <MediumStockChart
                company={selectedCompany}
                data={
                  marketDataMap[
                    `${selectedCompany.ticker}_${selectedCompany.market}_${activePeriod}`
                  ]
                }
                loading={
                  loadingMap[
                    `${selectedCompany.ticker}_${selectedCompany.market}_${activePeriod}`
                  ]
                }
                error={
                  errorMap[
                    `${selectedCompany.ticker}_${selectedCompany.market}_${activePeriod}`
                  ]
                }
                period={activePeriod}
                indicators={activeIndicators}
                width={720}
                height={260}
              />
            ) : (
              <div className="db-empty">
                <span className="db-empty-icon">📈</span>
                <h3>No company selected</h3>
                <p>Pick a company from the ribbon above to view its graph.</p>
              </div>
            )}
          </div>
        ) : (
          /* MULTIPLE MEDIUM GRAPHS GRID */
          <div className="mk-grid-container">
            {companiesList.slice(0, 4).map((comp) => {
              const key = `${comp.ticker}_${comp.market}_${activePeriod}`;
              return (
                <MediumStockChart
                  key={key}
                  company={comp}
                  data={marketDataMap[key]}
                  loading={loadingMap[key]}
                  error={errorMap[key]}
                  period={activePeriod}
                  indicators={activeIndicators}
                  width={560}
                  height={220}
                />
              );
            })}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default Markets;
