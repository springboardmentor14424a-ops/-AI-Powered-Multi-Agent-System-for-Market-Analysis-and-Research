
import React, { useEffect, useState } from "react";
import "./Dashboard.css";

const API_URL = "http://127.0.0.1:8000";

function Dashboard({ user, token, onLogout }) {
  const [activePage, setActivePage] = useState("My Watchlists");

  const [watchlist, setWatchlist] = useState([]);
  const [tasks, setTasks] = useState([]);

  const [search, setSearch] = useState("");
  const [stockSearch, setStockSearch] = useState("");
  const [stockResults, setStockResults] = useState([]);

  const [selectedReport, setSelectedReport] = useState(null);

  const [form, setForm] = useState({
    company_name: "",
    stock_ticker: "",
    market: "NASDAQ",
    analysis_period: "3 Months"
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`
  };

  // =====================================
  // LOAD DASHBOARD DATA
  // =====================================

  const loadDashboard = async () => {
    try {
      const [watchResponse, researchResponse] = await Promise.all([
        fetch(`${API_URL}/watchlist`, { headers }),
        fetch(`${API_URL}/research`, { headers })
      ]);

      if (watchResponse.status === 401 ||
          researchResponse.status === 401) {
        setError("Session expired. Please login again.");
        return;
      }

      if (!watchResponse.ok) {
        throw new Error("Unable to load your watchlist.");
      }

      if (!researchResponse.ok) {
        throw new Error("Unable to load research history.");
      }

      const watchData = await watchResponse.json();
      const researchData = await researchResponse.json();

      setWatchlist(watchData);
      setTasks(researchData);

    } catch (err) {
      setError(err.message || "Unable to connect to the backend.");
    }
  };

  useEffect(() => {
    if (token) {
      loadDashboard();
    }
  }, [token]);

  // =====================================
  // NAVIGATION
  // =====================================

  const handleNavigation = (page) => {
    setActivePage(page);
    setMessage("");
    setError("");
    setSelectedReport(null);
    setSearch("");
  };

  // =====================================
  // STOCK SEARCH
  // =====================================

  const handleStockSearch = async (value) => {
    setStockSearch(value);
    setError("");
    setMessage("");

    if (!value.trim()) {
      setStockResults([]);
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/stocks/search?q=${encodeURIComponent(value)}`,
        { headers }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Stock search failed.");
      }

      setStockResults(data);

    } catch (err) {
      setError(err.message);
      setStockResults([]);
    }
  };

  // =====================================
  // ADD STOCK TO WATCHLIST
  // =====================================

  const handleAddStock = async (stock) => {
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_URL}/watchlist`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          stock_ticker: stock.symbol
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to save stock.");
      }

      setMessage(`${stock.symbol} added to your watchlist.`);
      setStockSearch("");
      setStockResults([]);

      await loadDashboard();

    } catch (err) {
      setError(err.message);
    }
  };

  // =====================================
  // REMOVE STOCK
  // =====================================

  const handleRemoveStock = async (ticker) => {
    const confirmed = window.confirm(
      `Are you sure you want to remove ${ticker}?`
    );

    if (!confirmed) return;

    setError("");
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/watchlist/${encodeURIComponent(ticker)}`,
        {
          method: "DELETE",
          headers
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to remove stock.");
      }

      setMessage(data.message);
      await loadDashboard();

    } catch (err) {
      setError(err.message);
    }
  };

  // =====================================
  // SELECT STOCK FOR RESEARCH
  // =====================================

  const handleSelectStock = (stock) => {
    const ticker = stock.stock_ticker || stock.symbol;

    let market = "NASDAQ";

    if (ticker.endsWith(".NS")) {
      market = "NSE";
    } else if (ticker.endsWith(".BO")) {
      market = "BSE";
    }

    setForm({
      company_name: stock.company_name,
      stock_ticker: ticker,
      market,
      analysis_period: "3 Months"
    });

    setActivePage("Stock Research");
    setMessage(`${ticker} selected. You can now start research.`);
    setError("");
  };

  // =====================================
  // CREATE RESEARCH TASK
  // =====================================

  const handleCreateResearch = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setMessage("");
    setSelectedReport(null);

    try {
      const response = await fetch(`${API_URL}/research`, {
        method: "POST",
        headers,
        body: JSON.stringify(form)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Research creation failed.");
      }

      setMessage(
        `Research task created successfully. Status: ${data.status}`
      );

      await loadDashboard();

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // =====================================
  // VIEW RESEARCH REPORT
  // =====================================

  const handleViewReport = async (taskId) => {
    setError("");
    setMessage("");
    setSelectedReport(null);

    try {
      const response = await fetch(
        `${API_URL}/research/${taskId}/report`,
        { headers }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to load report.");
      }

      setSelectedReport(data);

    } catch (err) {
      setError(err.message);
    }
  };

  // =====================================
  // FILTER WATCHLIST
  // =====================================

  const filteredWatchlist = watchlist.filter((stock) => {
    const value =
      `${stock.company_name} ${stock.stock_ticker}`.toLowerCase();

    return value.includes(search.toLowerCase());
  });

  // =====================================
  // SIDEBAR NAVIGATION
  // =====================================

  const menuItems = [
    {
      name: "My Watchlists",
      icon: "☆",
      section: "STOCK MANAGEMENT"
    },
    {
      name: "Stock Search",
      icon: "⌕",
      section: "STOCK MANAGEMENT"
    },
    {
      name: "Stock Research",
      icon: "↗",
      section: "RESEARCH"
    },
    {
      name: "Research History",
      icon: "◷",
      section: "RESEARCH"
    },
    {
      name: "User Profile",
      icon: "♙",
      section: "ACCOUNT"
    }
  ];

  // =====================================
  // WATCHLIST PAGE
  // =====================================

  const renderWatchlist = () => (
    <>
      <div className="page-heading">
        <div>
          <h2>My Watchlists <span className="settings-icon">⚙</span></h2>
          <p>Manage and monitor your saved stocks.</p>
        </div>

        <button
          className="add-stock-button"
          onClick={() => handleNavigation("Stock Search")}
        >
          + Add Stock
        </button>
      </div>

      <div className="content-tabs">
        <button className="content-tab active">
          ☆ My Watchlist
        </button>

        <button
          className="content-tab"
          onClick={() => handleNavigation("Research History")}
        >
          Research History
        </button>
      </div>

      <div className="table-toolbar">
        <span>☷ Watchlist</span>
        <span>{watchlist.length} saved stocks</span>
      </div>

      <div className="table-wrapper">
        <table className="stock-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Ticker</th>
              <th>Company Name</th>
              <th>Saved Date</th>
              <th>Research</th>
              <th>Remove</th>
            </tr>
          </thead>

          <tbody>
            {filteredWatchlist.map((stock, index) => (
              <tr key={stock.id}>
                <td>{index + 1}</td>

                <td className="ticker-cell">
                  {stock.stock_ticker}
                </td>

                <td>{stock.company_name}</td>

                <td>
                  {stock.saved_date
                    ? new Date(stock.saved_date).toLocaleDateString()
                    : "—"}
                </td>

                <td>
                  <button
                    className="small-action-button"
                    onClick={() => handleSelectStock(stock)}
                  >
                    Start Research
                  </button>
                </td>

                <td>
                  <button
                    className="remove-button"
                    onClick={() =>
                      handleRemoveStock(stock.stock_ticker)
                    }
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}

            {filteredWatchlist.length === 0 && (
              <tr>
                <td colSpan="6" className="empty-row">
                  Your watchlist is empty. Add stocks using Stock Search.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );

  // =====================================
  // STOCK SEARCH PAGE
  // =====================================

  const renderStockSearch = () => (
    <>
      <div className="page-heading">
        <div>
          <h2>Stock Search</h2>
          <p>Find companies and add stocks to your watchlist.</p>
        </div>
      </div>

      <div className="search-card">
        <label>Search by company name or ticker symbol</label>

        <input
          type="text"
          value={stockSearch}
          onChange={(e) => handleStockSearch(e.target.value)}
          placeholder="Example: Apple or AAPL"
        />

        <div className="search-results">
          {stockResults.map((stock) => (
            <div className="search-result-item" key={stock.symbol}>
              <div>
                <strong>{stock.symbol}</strong>
                <p>{stock.company_name}</p>
              </div>

              <button
                className="small-action-button"
                onClick={() => handleAddStock(stock)}
              >
                + Add
              </button>
            </div>
          ))}

          {stockSearch.trim() && stockResults.length === 0 && (
            <p className="empty-search">
              No matching stocks found. Check your search or dataset.
            </p>
          )}
        </div>
      </div>
    </>
  );

  // =====================================
  // STOCK RESEARCH PAGE
  // =====================================

  const renderStockResearch = () => (
    <>
      <div className="page-heading">
        <div>
          <h2>Stock Research</h2>
          <p>Generate historical stock performance analysis.</p>
        </div>
      </div>

      <div className="research-layout">
        <div className="form-card">
          <h3>Create Research Task</h3>

          <form onSubmit={handleCreateResearch}>
            <label>Company Name</label>

            <input
              type="text"
              required
              value={form.company_name}
              onChange={(e) =>
                setForm({
                  ...form,
                  company_name: e.target.value
                })
              }
              placeholder="Enter company name"
            />

            <label>Stock Ticker</label>

            <input
              type="text"
              required
              value={form.stock_ticker}
              onChange={(e) =>
                setForm({
                  ...form,
                  stock_ticker: e.target.value.toUpperCase()
                })
              }
              placeholder="Example: AAPL"
            />

            <label>Stock Market</label>

            <select
              value={form.market}
              onChange={(e) =>
                setForm({
                  ...form,
                  market: e.target.value
                })
              }
            >
              <option value="NASDAQ">NASDAQ</option>
              <option value="NYSE">NYSE</option>
              <option value="NSE">NSE</option>
              <option value="BSE">BSE</option>
            </select>

            <label>Analysis Period</label>

            <select
              value={form.analysis_period}
              onChange={(e) =>
                setForm({
                  ...form,
                  analysis_period: e.target.value
                })
              }
            >
              <option value="1 Month">1 Month</option>
              <option value="3 Months">3 Months</option>
              <option value="6 Months">6 Months</option>
              <option value="1 Year">1 Year</option>
              <option value="5 Years">5 Years</option>
            </select>

            <button
              type="submit"
              className="primary-button"
              disabled={loading}
            >
              {loading ? "Processing..." : "Start Research →"}
            </button>
          </form>
        </div>

        <div className="information-card">
          <h3>Research Information</h3>

          <p>Your research task uses the selected stock's local historical dataset.</p>

          <ul>
            <li>Starting and ending prices</li>
            <li>Highest and lowest prices</li>
            <li>Average closing price</li>
            <li>Average trading volume</li>
            <li>Price change</li>
            <li>Percentage change</li>
          </ul>
        </div>
      </div>
    </>
  );

  // =====================================
  // RESEARCH HISTORY PAGE
  // =====================================

  const renderResearchHistory = () => (
    <>
      <div className="page-heading">
        <div>
          <h2>Research History</h2>
          <p>View your previous stock research activities.</p>
        </div>

        <button
          className="add-stock-button"
          onClick={loadDashboard}
        >
          ↻ Refresh
        </button>
      </div>

      <div className="table-wrapper">
        <table className="stock-table">
          <thead>
            <tr>
              <th>Task ID</th>
              <th>Company</th>
              <th>Ticker</th>
              <th>Market</th>
              <th>Period</th>
              <th>Research Date</th>
              <th>Status</th>
              <th>Report</th>
            </tr>
          </thead>

          <tbody>
            {tasks.map((task) => (
              <tr key={task.id}>
                <td>{task.id}</td>
                <td>{task.company_name}</td>
                <td className="ticker-cell">{task.stock_ticker}</td>
                <td>{task.market}</td>
                <td>{task.analysis_period}</td>

                <td>
                  {task.research_date
                    ? new Date(task.research_date).toLocaleDateString()
                    : "—"}
                </td>

                <td>
                  <span className={`status-badge ${task.status?.toLowerCase()}`}>
                    {task.status}
                  </span>
                </td>

                <td>
                  {task.status === "Completed" ? (
                    <button
                      className="small-action-button"
                      onClick={() => handleViewReport(task.id)}
                    >
                      View Report
                    </button>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}

            {tasks.length === 0 && (
              <tr>
                <td colSpan="8" className="empty-row">
                  No research tasks available.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selectedReport && (
        <div className="report-card">
          <div className="report-heading">
            <h3>
              {selectedReport.company_name} Research Report
            </h3>

            <button
              className="close-report"
              onClick={() => setSelectedReport(null)}
            >
              ×
            </button>
          </div>

          <pre>{selectedReport.report_content}</pre>
        </div>
      )}
    </>
  );

  // =====================================
  // USER PROFILE PAGE
  // =====================================

  const renderProfile = () => (
    <>
      <div className="page-heading">
        <div>
          <h2>User Profile</h2>
          <p>Your registered account information.</p>
        </div>
      </div>

      <div className="profile-card">
        <div className="profile-avatar">
          {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
        </div>

        <h3>{user?.full_name || "User"}</h3>

        <p>{user?.email || "Email not available"}</p>

        <div className="profile-details">
          <div>
            <span>Full Name</span>
            <strong>{user?.full_name || "—"}</strong>
          </div>

          <div>
            <span>Email Address</span>
            <strong>{user?.email || "—"}</strong>
          </div>
        </div>
      </div>
    </>
  );

  // =====================================
  // MAIN DASHBOARD
  // =====================================

  return (
    <div className="dashboard-container">

      {/* SIDEBAR */}

      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">S</div>
          <h2>Stock<span>Scope</span></h2>
        </div>

        <div className="sidebar-profile">
          <div className="user-avatar">
            {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
          </div>

          <div>
            <strong>{user?.full_name || "User"}</strong>
            <small>Research Account</small>
          </div>
        </div>

        {["STOCK MANAGEMENT", "RESEARCH", "ACCOUNT"].map((section) => (
          <div className="sidebar-section" key={section}>
            <p className="sidebar-label">{section}</p>

            {menuItems
              .filter((item) => item.section === section)
              .map((item) => (
                <button
                  key={item.name}
                  className={
                    activePage === item.name
                      ? "sidebar-link active"
                      : "sidebar-link"
                  }
                  onClick={() => handleNavigation(item.name)}
                >
                  <span className="sidebar-icon">{item.icon}</span>
                  {item.name}
                </button>
              ))}
          </div>
        ))}

        <div className="sidebar-bottom">
          <button
            className="sidebar-link logout-link"
            onClick={onLogout}
          >
            <span className="sidebar-icon">↪</span>
            Logout
          </button>

          <div className="connection-status">
            <span></span>
            StockScope
          </div>
        </div>

      </aside>

      {/* MAIN CONTENT */}

      <main className="main-content">

        <header className="top-header">

          <div className="global-search">
            <span>⌕</span>

            <input
              type="text"
              placeholder="Search in your watchlist..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setActivePage("My Watchlists");
              }}
            />

            <kbd>Ctrl K</kbd>
          </div>

          <div className="header-user">
            <div className="header-avatar">
              {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
            </div>

            <span>{user?.full_name || "User"}</span>
          </div>

        </header>

        <section className="page-content">

          {/* ALERTS */}

          {message && (
            <div className="alert-message success-message">
              ✓ {message}
            </div>
          )}

          {error && (
            <div className="alert-message error-message">
              ! {error}
            </div>
          )}

          {/* PAGE ROUTING */}

          {activePage === "My Watchlists" && renderWatchlist()}

          {activePage === "Stock Search" && renderStockSearch()}

          {activePage === "Stock Research" && renderStockResearch()}

          {activePage === "Research History" && renderResearchHistory()}

          {activePage === "User Profile" && renderProfile()}

        </section>

      </main>
    </div>
  );
}

export default Dashboard;
