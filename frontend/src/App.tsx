
import { useEffect, useState } from "react";
import {
  Activity,
  ArrowRight,
  ShieldCheck,
  LogOut,
  BarChart3,
  Search,
  Trash2,
  Settings
} from "lucide-react";

import { api } from "./api";

type User = {
  user_id: number;
  full_name: string;
  email: string;
};

type DashboardData = {
  message: string;
  user_id: number;
  full_name: string;
  email: string;
  watchlist_count: number;
  research_count: number;
  completed_count: number;
};

type SavedStock = {
  saved_stock_id: number;
  ticker: string;
  created_at: string | null;
  current_price: number | null;
  daily_change_percent: number | null;
};

type StockSearchResult = {
  ticker: string;
  company_name: string;
  exchange: string | null;
  type: string;
};

type ResearchTask = {
  task_id: number;
  ticker: string;
  market: string;
  requested_period: string;
  status: string;
  created_at: string | null;
  completed_at: string | null;
  report: {
    report_id: number;
    summary: string | null;
    report_content: string | null;
    limitations: string | null;
  } | null;
};

type UserPreferences = {
  preference_id: number;
  user_id: number;
  market: string;
  research_period: string;
  updated_at: string | null;
};

type Page =
  | "loading"
  | "landing"
  | "login"
  | "register"
  | "dashboard";

export default function App() {
  const [page, setPage] = useState<Page>("loading");
  const [user, setUser] = useState<User | null>(null);

  const [dashboardData, setDashboardData] =
    useState<DashboardData | null>(null);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const [ticker, setTicker] = useState("");

  // USER PREFERENCES
  const [market, setMarket] = useState("US");
  const [period, setPeriod] = useState("3 months");
  const [preferencesBusy, setPreferencesBusy] = useState(false);
  const [preferencesLoading, setPreferencesLoading] = useState(false);

  const [researchHistory, setResearchHistory] =
    useState<ResearchTask[]>([]);

  const [savedStocks, setSavedStocks] =
    useState<SavedStock[]>([]);

  const [watchlistTicker, setWatchlistTicker] = useState("");
  const [watchlistBusy, setWatchlistBusy] = useState(false);

  // STOCK SEARCH STATE
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] =
    useState<StockSearchResult[]>([]);
  const [searchBusy, setSearchBusy] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);

  const [researchBusy, setResearchBusy] = useState(false);
  const [historyBusy, setHistoryBusy] = useState(false);
  const [dashboardBusy, setDashboardBusy] = useState(false);

  async function loadDashboard() {
    setDashboardBusy(true);

    try {
      const data = await api("/api/dashboard");
      setDashboardData(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load dashboard data"
      );
    } finally {
      setDashboardBusy(false);
    }
  }

  async function loadResearchHistory() {
    setHistoryBusy(true);

    try {
      const data = await api("/api/research/history");
      setResearchHistory(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load research history"
      );
    } finally {
      setHistoryBusy(false);
    }
  }

  async function loadWatchlist() {
    try {
      const data = await api("/api/watchlist");
      setSavedStocks(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load watchlist"
      );
    }
  }

  // LOAD USER PREFERENCES
  async function loadPreferences() {
    setPreferencesLoading(true);

    try {
      const data: UserPreferences =
        await api("/api/preferences");

      setMarket(data.market);
      setPeriod(data.research_period);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load preferences"
      );
    } finally {
      setPreferencesLoading(false);
    }
  }

  // SAVE USER PREFERENCES
  async function savePreferences(
    e: React.FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();

    setError("");
    setMessage("");
    setPreferencesBusy(true);

    try {
      const data: UserPreferences = await api(
        "/api/preferences",
        {
          method: "PUT",
          body: JSON.stringify({
            market,
            research_period: period
          })
        }
      );

      setMarket(data.market);
      setPeriod(data.research_period);

      setMessage("Your preferences have been saved successfully!");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to save preferences"
      );
    } finally {
      setPreferencesBusy(false);
    }
  }

  async function loadDashboardContent() {
    await Promise.all([
      loadDashboard(),
      loadResearchHistory(),
      loadWatchlist(),
      loadPreferences()
    ]);
  }

  // SEARCH STOCKS
  async function searchStocks(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const cleanQuery = searchQuery.trim();

    if (!cleanQuery) {
      setError("Please enter a company name or ticker");
      return;
    }

    setError("");
    setMessage("");
    setSearchBusy(true);
    setSearchPerformed(false);
    setSearchResults([]);

    try {
      const data = await api(
        `/api/stocks/search?query=${encodeURIComponent(cleanQuery)}`
      );

      setSearchResults(data.results || []);
      setSearchPerformed(true);

      if (!data.results || data.results.length === 0) {
        setMessage("No matching stocks found. Try another search.");
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to search stocks"
      );
    } finally {
      setSearchBusy(false);
    }
  }

  // ADD A SEARCH RESULT TO WATCHLIST
  async function addSearchResultToWatchlist(stock: StockSearchResult) {
    setError("");
    setMessage("");
    setWatchlistBusy(true);

    try {
      await api("/api/watchlist", {
        method: "POST",
        body: JSON.stringify({
          ticker: stock.ticker
        })
      });

      setMessage(`${stock.ticker} added to your watchlist!`);

      await loadWatchlist();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to add stock to watchlist"
      );
    } finally {
      setWatchlistBusy(false);
    }
  }

  // ADD STOCK USING WATCHLIST INPUT
  async function addToWatchlist(
    e: React.FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();

    const cleanTicker = watchlistTicker.trim().toUpperCase();

    if (!cleanTicker) {
      setError("Please enter a stock ticker");
      return;
    }

    setError("");
    setMessage("");
    setWatchlistBusy(true);

    try {
      await api("/api/watchlist", {
        method: "POST",
        body: JSON.stringify({
          ticker: cleanTicker
        })
      });

      setMessage(`${cleanTicker} added to your watchlist!`);
      setWatchlistTicker("");

      await loadWatchlist();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to add stock to watchlist"
      );
    } finally {
      setWatchlistBusy(false);
    }
  }

  // REMOVE STOCK FROM WATCHLIST
  async function removeFromWatchlist(savedStockId: number) {
    setError("");
    setMessage("");

    try {
      await api(`/api/watchlist/${savedStockId}`, {
        method: "DELETE"
      });

      setMessage("Stock removed from your watchlist.");

      await loadWatchlist();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to remove stock"
      );
    }
  }

  // CREATE RESEARCH TASK FOR A SPECIFIC TICKER
  async function startResearchForStock(stockTicker: string) {
    setError("");
    setMessage("");
    setResearchBusy(true);

    try {
      const data = await api("/api/research/tasks", {
        method: "POST",
        body: JSON.stringify({
          ticker: stockTicker.trim().toUpperCase(),
          market,
          requested_period: period
        })
      });

      setMessage(
        `Research task created for ${stockTicker.toUpperCase()}! Task ID: ${data.task_id}`
      );

      setTicker("");

      await loadResearchHistory();
      await loadDashboard();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create research task"
      );
    } finally {
      setResearchBusy(false);
    }
  }

  // CREATE RESEARCH TASK USING THE RESEARCH FORM
  async function createResearchTask(
    e: React.FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();

    if (!ticker.trim()) {
      setError("Please enter a stock ticker");
      return;
    }

    await startResearchForStock(ticker);
  }

  // CHECK EXISTING LOGIN SESSION
  useEffect(() => {
    api("/api/auth/me")
      .then(async (data) => {
        setUser(data);
        setPage("dashboard");
        await loadDashboardContent();
      })
      .catch(() => {
        setPage("landing");
      });
  }, []);

  // REGISTER USER
  async function register(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    setError("");
    setMessage("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setBusy(true);

    try {
      await api("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName.trim(),
          email,
          password
        })
      });

      setMessage("Account created! Please sign in.");
      setPassword("");
      setConfirmPassword("");
      setPage("login");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Registration failed"
      );
    } finally {
      setBusy(false);
    }
  }

  // LOGIN USER
  async function login(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    setError("");
    setMessage("");
    setBusy(true);

    try {
      await api("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });

      const currentUser = await api("/api/auth/me");

      setUser(currentUser);
      setPassword("");
      setPage("dashboard");

      await loadDashboardContent();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Login failed"
      );
    } finally {
      setBusy(false);
    }
  }

  // LOGOUT USER
  async function logout() {
    setError("");

    try {
      await api("/api/auth/logout", {
        method: "POST"
      });

      setUser(null);
      setDashboardData(null);
      setResearchHistory([]);
      setSavedStocks([]);
      setSearchResults([]);
      setSearchQuery("");
      setSearchPerformed(false);

      setMarket("US");
      setPeriod("3 months");

      setPage("landing");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Logout failed"
      );
    }
  }

  // LOADING SCREEN
  if (page === "loading") {
    return (
      <div className="center-screen">
        <Activity size={36} />
        <p>Loading StockPilot...</p>
      </div>
    );
  }

  // LANDING PAGE
  if (page === "landing") {
    return (
      <div className="landing">
        <nav className="navbar">
          <div className="brand">
            <Activity />
            Stock<span>Pilot</span>
          </div>

          <div className="nav-buttons">
            <button
              className="outline-btn"
              onClick={() => {
                setError("");
                setMessage("");
                setPage("login");
              }}
            >
              Sign In
            </button>

            <button
              className="primary-btn"
              onClick={() => {
                setError("");
                setMessage("");
                setPage("register");
              }}
            >
              Sign Up <ArrowRight size={17} />
            </button>
          </div>
        </nav>

        <section className="hero">
          <div className="hero-content">
            <div className="tag">
              <Activity size={15} />
              AI-POWERED STOCK RESEARCH
            </div>

            <h1>
              Research Smarter.
              <br />
              <span>Invest Better.</span>
            </h1>

            <p>
              Discover a smarter way to research stocks.
              Explore company performance, market trends
              and investment opportunities with StockPilot.
            </p>

            <div className="hero-buttons">
              <button
                className="primary-btn big-btn"
                onClick={() => setPage("register")}
              >
                Get Started <ArrowRight />
              </button>

              <button
                className="outline-btn big-btn"
                onClick={() => setPage("login")}
              >
                Sign In
              </button>
            </div>

            <div className="security">
              <ShieldCheck size={17} />
              Secure user authentication
            </div>
          </div>

          <div className="hero-card">
            <div className="card-top">
              <div>
                <small>STOCKPILOT WORKSPACE</small>
                <h2>Market Intelligence</h2>
              </div>
              <BarChart3 color="#35d399" size={30} />
            </div>

            <div className="chart">
              <svg viewBox="0 0 400 160">
                <path
                  d="M0 130 L50 110 L100 120 L150 65 L200 90 L250 40 L300 60 L350 15 L400 30"
                  stroke="#35d399"
                  fill="none"
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              </svg>
            </div>

            <div className="card-bottom">
              <span>Fundamental Analysis</span>
              <span>Technical Analysis</span>
              <span>Risk Assessment</span>
            </div>
          </div>
        </section>

        <section className="features">
          <div>
            <BarChart3 />
            <h3>Financial Analysis</h3>
            <p>Understand company performance and valuation.</p>
          </div>

          <div>
            <Activity />
            <h3>Market Trends</h3>
            <p>Explore stock prices and market movements.</p>
          </div>

          <div>
            <ShieldCheck />
            <h3>Risk Assessment</h3>
            <p>Understand potential investment risks.</p>
          </div>
        </section>

        <footer>
          © 2026 StockPilot. AI-powered stock research.
        </footer>
      </div>
    );
  }

  // REGISTRATION AND LOGIN PAGES
  if (page === "login" || page === "register") {
    const isRegister = page === "register";

    return (
      <div className="auth-screen">
        <div className="auth-card">
          <button
            className="back-button"
            onClick={() => {
              setError("");
              setMessage("");
              setPage("landing");
            }}
          >
            ← Back to home
          </button>

          <div className="brand">
            <Activity />
            Stock<span>Pilot</span>
          </div>

          <h1>
            {isRegister ? "Create your account" : "Welcome back"}
          </h1>

          <p>
            {isRegister
              ? "Join StockPilot and start your research journey."
              : "Sign in to access your personal workspace."}
          </p>

          {message && (
            <div className="success-message">{message}</div>
          )}

          {error && (
            <div className="error-message">{error}</div>
          )}

          <form onSubmit={isRegister ? register : login}>
            {isRegister && (
              <label>
                Full Name
                <input
                  required
                  minLength={2}
                  maxLength={100}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter your full name"
                />
              </label>
            )}

            <label>
              Email Address
              <input
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
              />
            </label>

            <label>
              Password
              <input
                required
                type="password"
                minLength={8}
                maxLength={128}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
              />
            </label>

            {isRegister && (
              <label>
                Confirm Password
                <input
                  required
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                />
              </label>
            )}

            <button
              className="primary-btn submit-btn"
              disabled={busy}
              type="submit"
            >
              {busy
                ? "Please wait..."
                : isRegister
                  ? "Create Account"
                  : "Sign In"}

              {!busy && <ArrowRight size={18} />}
            </button>
          </form>

          <div className="switch-auth">
            {isRegister
              ? "Already have an account?"
              : "Don't have an account?"}

            <button
              onClick={() => {
                setError("");
                setMessage("");
                setPage(isRegister ? "login" : "register");
              }}
            >
              {isRegister ? "Sign In" : "Sign Up"}
            </button>
          </div>

          <div className="security">
            <ShieldCheck size={16} />
            Secure authentication powered by FastAPI
          </div>
        </div>
      </div>
    );
  }

  // AUTHENTICATED DASHBOARD
  return (
    <div className="dashboard">
      <nav className="dashboard-nav">
        <div className="brand">
          <Activity />
          Stock<span>Pilot</span>
        </div>

        <button className="outline-btn" onClick={logout}>
          <LogOut size={17} />
          Sign Out
        </button>
      </nav>

      <main className="dashboard-content">
        <div className="welcome">
          <div>
            <small>PERSONAL WORKSPACE</small>
            <h1>
              Welcome, {dashboardData?.full_name || user?.full_name}!
            </h1>
            <p>
              {dashboardData?.email || user?.email}
            </p>
          </div>

          <div className="avatar">
            {(dashboardData?.full_name || user?.full_name || "?")
              .charAt(0)
              .toUpperCase()}
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        {/* DASHBOARD STATISTICS */}
        <div className="dashboard-grid">
          <div className="dashboard-card">
            <Activity />
            <h3>Watchlist Stocks</h3>
            <h2>
              {dashboardBusy ? "..." : savedStocks.length}
            </h2>
            <p>Stocks saved to your watchlist</p>
          </div>

          <div className="dashboard-card">
            <Search />
            <h3>Research Tasks</h3>
            <h2>
              {dashboardBusy
                ? "..."
                : dashboardData?.research_count ?? 0}
            </h2>
            <p>Total research requests created</p>
          </div>

          <div className="dashboard-card">
            <BarChart3 />
            <h3>Completed Research</h3>
            <h2>
              {dashboardBusy
                ? "..."
                : dashboardData?.completed_count ?? 0}
            </h2>
            <p>Successfully completed research tasks</p>
          </div>
        </div>

        {/* USER PREFERENCES */}
        <div className="account-panel">
          <h2>
            <Settings
              size={21}
              style={{
                verticalAlign: "middle",
                marginRight: "8px"
              }}
            />
            My Preferences
          </h2>

          <p>
            Choose your preferred stock market and research
            period. StockPilot will use these settings when
            creating new research tasks.
          </p>

          {preferencesLoading ? (
            <p>Loading your preferences...</p>
          ) : (
            <form onSubmit={savePreferences}>
              <label>
                Preferred Market
                <select
                  value={market}
                  onChange={(e) => setMarket(e.target.value)}
                >
                  <option value="US">United States (US)</option>
                  <option value="India">India</option>
                </select>
              </label>

              <label>
                Default Research Period
                <select
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                >
                  <option value="1 month">1 Month</option>
                  <option value="3 months">3 Months</option>
                  <option value="6 months">6 Months</option>
                  <option value="1 year">1 Year</option>
                </select>
              </label>

              <button
                className="primary-btn"
                type="submit"
                disabled={preferencesBusy || preferencesLoading}
              >
                {preferencesBusy
                  ? "Saving..."
                  : "Save Preferences"}
              </button>
            </form>
          )}
        </div>

        {/* STOCK SEARCH */}
        <div className="account-panel">
          <h2>Stock Search</h2>

          <p>
            Search for companies by name or ticker symbol.
            Add stocks to your Watchlist or start researching them.
          </p>

          <form onSubmit={searchStocks}>
            <label>
              Company Name or Ticker
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Example: Apple, Microsoft, AAPL"
                maxLength={100}
                required
              />
            </label>

            <button
              className="primary-btn"
              type="submit"
              disabled={searchBusy}
            >
              <Search size={17} />
              {searchBusy ? "Searching..." : "Search Stocks"}
            </button>
          </form>

          {searchBusy && <p>Searching for matching stocks...</p>}

          {searchPerformed && !searchBusy && (
            <div className="research-history">
              {searchResults.length === 0 ? (
                <p>No matching stocks found. Try another search.</p>
              ) : (
                searchResults.map((stock) => (
                  <div
                    className="research-item"
                    key={`${stock.ticker}-${stock.exchange}`}
                  >
                    <h3>{stock.company_name}</h3>

                    <p>
                      <strong>Ticker:</strong> {stock.ticker}
                    </p>

                    <p>
                      <strong>Exchange:</strong>{" "}
                      {stock.exchange || "Not available"}
                    </p>

                    <div className="nav-buttons">
                      <button
                        className="primary-btn"
                        type="button"
                        disabled={watchlistBusy}
                        onClick={() =>
                          addSearchResultToWatchlist(stock)
                        }
                      >
                        Add to Watchlist
                      </button>

                      <button
                        className="outline-btn"
                        type="button"
                        disabled={researchBusy}
                        onClick={() =>
                          startResearchForStock(stock.ticker)
                        }
                      >
                        Start Research
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* RESEARCH AND ACCOUNT FEATURES */}
        <div className="dashboard-grid">
          <div className="dashboard-card">
            <Search />

            <h3>Stock Research</h3>

            <p>
              Submit a new stock research request.
            </p>

            <form onSubmit={createResearchTask}>
              <label>
                Stock Ticker
                <input
                  required
                  maxLength={30}
                  value={ticker}
                  onChange={(e) =>
                    setTicker(e.target.value.toUpperCase())
                  }
                  placeholder="Example: AAPL"
                />
              </label>

              <label>
                Market
                <select
                  value={market}
                  onChange={(e) => setMarket(e.target.value)}
                >
                  <option value="US">United States (US)</option>
                  <option value="India">India</option>
                </select>
              </label>

              <label>
                Research Period
                <select
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                >
                  <option value="1 month">1 Month</option>
                  <option value="3 months">3 Months</option>
                  <option value="6 months">6 Months</option>
                  <option value="1 year">1 Year</option>
                </select>
              </label>

              <button
                className="primary-btn"
                type="submit"
                disabled={researchBusy || preferencesLoading}
              >
                {researchBusy
                  ? "Submitting..."
                  : "Create Research Task"}
              </button>
            </form>
          </div>

          <div className="dashboard-card">
            <BarChart3 />

            <h3>Market Analysis</h3>

            <p>
              Explore company fundamentals and historical market trends.
            </p>

            <span className="coming-soon">
              Analysis module coming next
            </span>
          </div>

          <div className="dashboard-card">
            <ShieldCheck />

            <h3>Account Security</h3>

            <p>
              Your account is authenticated through FastAPI JWT.
            </p>

            <span className="connected">Authenticated</span>
          </div>
        </div>

        {/* WATCHLIST */}
        <div className="account-panel">
          <h2>My Watchlist</h2>

          <p>
            Save stocks you want to monitor and access them whenever
            you return to StockPilot.
          </p>

          <form onSubmit={addToWatchlist}>
            <label>
              Stock Ticker
              <input
                required
                maxLength={30}
                value={watchlistTicker}
                onChange={(e) =>
                  setWatchlistTicker(e.target.value.toUpperCase())
                }
                placeholder="Example: AAPL, MSFT, GOOGL"
              />
            </label>

            <button
              className="primary-btn"
              type="submit"
              disabled={watchlistBusy}
            >
              {watchlistBusy ? "Adding..." : "Add Stock"}
            </button>
          </form>

          <button
            className="outline-btn"
            onClick={loadWatchlist}
          >
            Refresh Watchlist
          </button>

          {savedStocks.length === 0 ? (
            <p>Your watchlist is empty. Add your first stock above.</p>
          ) : (
            <div className="research-history">
              {savedStocks.map((stock) => (
                <div
                  className="research-item"
                  key={stock.saved_stock_id}
                >
                  <h3>{stock.ticker}</h3>

                  <p>
                    <strong>Latest Price:</strong>{" "}
                    {stock.current_price !== null &&
                    stock.current_price !== undefined
                      ? stock.current_price.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2
                        })
                      : "Unavailable"}
                  </p>

                  <p>
                    <strong>Daily Change:</strong>{" "}
                    {stock.daily_change_percent !== null &&
                    stock.daily_change_percent !== undefined ? (
                      <span
                        style={{
                          color:
                            stock.daily_change_percent > 0
                              ? "#16a34a"
                              : stock.daily_change_percent < 0
                                ? "#dc2626"
                                : "inherit",
                          fontWeight: 600
                        }}
                      >
                        {stock.daily_change_percent > 0 ? "+" : ""}
                        {stock.daily_change_percent.toFixed(2)}%
                      </span>
                    ) : (
                      "Unavailable"
                    )}
                  </p>

                  <p>
                    <strong>Saved:</strong>{" "}
                    {stock.created_at
                      ? new Date(stock.created_at).toLocaleString()
                      : "Not available"}
                  </p>

                  <button
                    className="outline-btn"
                    onClick={() =>
                      removeFromWatchlist(stock.saved_stock_id)
                    }
                  >
                    <Trash2 size={16} />
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {message && (
          <div className="success-message">{message}</div>
        )}

        {/* RESEARCH HISTORY */}
        <div className="account-panel">
          <h2>Research History</h2>

          <button
            className="outline-btn"
            onClick={loadResearchHistory}
            disabled={historyBusy}
          >
            {historyBusy ? "Loading..." : "Refresh History"}
          </button>

          {historyBusy ? (
            <p>Loading research history...</p>
          ) : researchHistory.length === 0 ? (
            <p>No research tasks found.</p>
          ) : (
            <div className="research-history">
              {researchHistory.map((task) => (
                <div
                  className="research-item"
                  key={task.task_id}
                >
                  <h3>{task.ticker}</h3>

                  <p>
                    <strong>Task ID:</strong> {task.task_id}
                  </p>

                  <p>
                    <strong>Market:</strong> {task.market}
                  </p>

                  <p>
                    <strong>Period:</strong> {task.requested_period}
                  </p>

                  <p>
                    <strong>Status:</strong> {task.status}
                  </p>

                  <p>
                    <strong>Created:</strong>{" "}
                    {task.created_at
                      ? new Date(task.created_at).toLocaleString()
                      : "Not available"}
                  </p>

                  {task.report?.summary && (
                    <p>
                      <strong>Summary:</strong>{" "}
                      {task.report.summary}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
