
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";

import {
  searchStocks,
  getStockHistory,
  createResearchTask,
} from "../services/authService";

function Research() {
  const navigate = useNavigate();

  // User and session
  const token = sessionStorage.getItem("access_token");
  const user = JSON.parse(sessionStorage.getItem("user") || "null");

  const storageKey = `stockintel_research_${user?.user_id || user?.email || "current"}`;

  // Restore previously saved Research data
  const [savedResearch] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem(storageKey) || "{}");
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

  const [showAllRecords, setShowAllRecords] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [researchLoading, setResearchLoading] = useState(false);

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
      setSearchResults([]);
      setShowAllRecords(false);

      const response = await searchStocks(searchQuery.trim());
      setSearchResults(response.results || []);

      if (!response.results?.length) {
        setMessage("No matching NSE or BSE stocks found.");
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

  // Retrieve historical data
  const loadHistoricalData = async (stock, period) => {
    if (!stock) return;

    try {
      setHistoryLoading(true);
      setHoverIndex(null);
      setError("");
      setMessage("Loading historical market data...");

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
  };

  // Reload data when selected stock or period changes
  useEffect(() => {
    if (selectedStock) {
      loadHistoricalData(selectedStock, analysisPeriod);
    }
  }, [selectedStock, analysisPeriod]);

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

  const prices = historicalData.map((item) => item.close);

  const minPrice = prices.length ? Math.min(...prices) : 0;
  const maxPrice = prices.length ? Math.max(...prices) : 0;
  const priceRange = maxPrice - minPrice || 1;

  const chartPoints = historicalData.map((item, index) => {
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

  const chartLine = chartPoints
    .map((point) => `${point.x},${point.y}`)
    .join(" ");

  const chartArea = chartPoints.length
    ? `${chartLine} ${chartPoints[chartPoints.length - 1].x},${graphHeight - graphPadding} ${chartPoints[0].x},${graphHeight - graphPadding}`
    : "";

  const selectedPoint =
    hoverIndex !== null ? chartPoints[hoverIndex] : null;

  const formatPrice = (value) =>
    Number(value).toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

  if (!user) return null;

  return (
    <DashboardLayout user={user} onLogout={logout}>
      <div className="research-page">

        {/* PAGE HEADING */}
        <div className="research-heading">
          <div>
            <span className="research-eyebrow">
              STOCKINTEL / MARKET DATA
            </span>
            <h1>Stock Research</h1>
            <p>
              Explore historical market prices and analyse stock performance.
            </p>
          </div>
        </div>

        {/* STOCK SEARCH */}
        <section className="research-panel">
          <h2>Find a Company</h2>
          <p>Search for Indian stocks listed on NSE and BSE.</p>

          <div className="research-search">
            <input
              type="search"
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
              spellCheck="false"
              name="research-stock-search"
              id="research-stock-search"
              placeholder="Search TCS, Reliance, Infosys..."
              value={searchQuery}
              onChange={(e) => {
                const val = e.target.value;
                setSearchQuery(val);
                if (val.trim() === "") {
                  setSearchResults([]);
                  setSelectedStock(null);
                  setHistoricalData([]);
                  setMessage("");
                  setError("");
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

              <div className="research-period">
                <label htmlFor="analysisPeriod">
                  Historical Period
                </label>

                <select
                  id="analysisPeriod"
                  value={analysisPeriod}
                  onChange={(e) => setAnalysisPeriod(e.target.value)}
                >
                  <option value="3mo">3 Months</option>
                  <option value="6mo">6 Months</option>
                  <option value="1y">1 Year</option>
                  <option value="5y">5 Years</option>
                </select>
              </div>
            </div>
          )}

          {historyLoading && (
            <p className="research-loading">
              Retrieving historical market data...
            </p>
          )}

          {message && (
            <p className="research-success">{message}</p>
          )}

          {error && (
            <p className="research-error">{error}</p>
          )}
        </section>

        {/* HISTORICAL DATA GRAPH */}
        {historicalData.length > 0 && selectedStock && (
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

                <div className="research-chart-price">
                  <span>LATEST CLOSE</span>
                  <strong>
                    ₹{formatPrice(
                      historicalData[historicalData.length - 1].close
                    )}
                  </strong>
                </div>
              </div>

              <div className="research-chart-legend">
                <span></span>
                Closing Price (INR)
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
                  <span>Open: ₹{formatPrice(selectedPoint.open)}</span>
                  <span>High: ₹{formatPrice(selectedPoint.high)}</span>
                  <span>Low: ₹{formatPrice(selectedPoint.low)}</span>
                  <span>Close: ₹{formatPrice(selectedPoint.close)}</span>
                  <span>
                    Volume: {Number(selectedPoint.volume || 0).toLocaleString("en-IN")}
                  </span>
                </div>
              )}

              {/* GRAPH SUMMARY */}
              <div className="research-chart-summary">
                <div>
                  <span>HIGHEST CLOSE</span>
                  <strong>₹{formatPrice(maxPrice)}</strong>
                </div>

                <div>
                  <span>LOWEST CLOSE</span>
                  <strong>₹{formatPrice(minPrice)}</strong>
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

              <div className="research-table-container">
                <table className="research-data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Open (₹)</th>
                      <th>High (₹)</th>
                      <th>Low (₹)</th>
                      <th>Close (₹)</th>
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
                        <td>{formatPrice(item.open)}</td>
                        <td>{formatPrice(item.high)}</td>
                        <td>{formatPrice(item.low)}</td>
                        <td className="research-close-price">
                          {formatPrice(item.close)}
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
