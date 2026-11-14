
import { useEffect, useState, useCallback } from "react";
import DashboardLayout from "../components/DashboardLayout";
import {
  searchStocks,
  addToWatchlist,
  getWatchlist,
  removeFromWatchlist,
  createResearchTask,
} from "../services/authService";

function Watchlist() {
  const [stocks, setStocks] = useState([]);
  const [results, setResults] = useState([]);
  const [query, setQuery] = useState("");
  const [filterQuery, setFilterQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  const user = JSON.parse(sessionStorage.getItem("user") || "{}");

  const loadWatchlist = useCallback(async () => {
    try {
      const data = await getWatchlist();
      setStocks(Array.isArray(data) ? data : []);
    } catch {
      setError("Unable to load your saved stocks.");
    }
  }, []);

  useEffect(() => {
    loadWatchlist();
  }, [loadWatchlist]);

  const handleSearch = async (e) => {
    e.preventDefault();

    if (query.trim().length < 2) {
      setError("Enter at least 2 characters.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const data = await searchStocks(query.trim());
      setResults(data.results || []);
      setMessage(
        data.results?.length
          ? `${data.results.length} matching stocks found`
          : "No matching NSE or BSE stocks found."
      );
    } catch (err) {
      setError(err.response?.data?.detail || "Search failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (stock) => {
    const key = `${stock.ticker}-${stock.market}`;
    setBusy(key);
    setError("");
    setMessage("");

    try {
      await addToWatchlist({
        company_name: stock.company_name,
        ticker: stock.ticker,
        market: stock.market,
      });

      setMessage(`${stock.company_name} added to your watchlist.`);
      await loadWatchlist();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to add stock.");
    } finally {
      setBusy("");
    }
  };

  const handleRemove = async (id) => {
    setBusy(id);
    setError("");
    setMessage("");

    try {
      await removeFromWatchlist(id);
      setMessage("Stock removed successfully.");
      await loadWatchlist();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to remove stock.");
    } finally {
      setBusy("");
    }
  };

  const handleStartResearch = async (stock) => {
    setBusy(`research-${stock.watchlist_id}`);
    setError("");
    setMessage("");

    try {
      await createResearchTask({
        company_name: stock.company_name,
        ticker: stock.ticker,
        market: stock.market,
        analysis_period: "1y",
      });

      setMessage(
        `Research task created successfully for ${stock.company_name}.`
      );
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to create research task."
      );
    } finally {
      setBusy("");
    }
  };

  const nseCount = stocks.filter(
    (s) => s.market === "NSE"
  ).length;

  const bseCount = stocks.filter(
    (s) => s.market === "BSE"
  ).length;

  const filteredStocks = stocks.filter((stock) => {
    const search = filterQuery.trim().toLowerCase();

    return (
      stock.company_name?.toLowerCase().includes(search) ||
      stock.ticker?.toLowerCase().includes(search) ||
      stock.market?.toLowerCase().includes(search)
    );
  });

  const alreadySaved = (stock) =>
    stocks.some(
      (s) =>
        s.ticker === stock.ticker &&
        s.market === stock.market
    );

  return (
    <DashboardLayout user={user}>
      <div className="watchlist-page">

        <div className="wl-heading">
          <div>
            <span className="wl-eyebrow">
              MARKET RESEARCH / WATCHLIST
            </span>
            <h1>My Watchlist</h1>
            <p>
              Monitor and organise stocks for your research workspace.
            </p>
          </div>
          <span className="wl-live-label">
            PERSONAL WORKSPACE
          </span>
        </div>

        <div className="wl-metrics">
          <div className="wl-metric">
            <span>TOTAL SAVED STOCKS</span>
            <strong>{stocks.length}</strong>
            <small>Stocks in your watchlist</small>
          </div>

          <div className="wl-metric">
            <span>NSE STOCKS</span>
            <strong>{nseCount}</strong>
            <small>National Stock Exchange</small>
          </div>

          <div className="wl-metric">
            <span>BSE STOCKS</span>
            <strong>{bseCount}</strong>
            <small>Bombay Stock Exchange</small>
          </div>
        </div>

        <section className="wl-panel">
          <div className="wl-panel-heading">
            <div>
              <h2>Discover Stocks</h2>
              <p>
                Search for Indian companies by name or ticker.
              </p>
            </div>
            <span className="wl-tag">NSE / BSE</span>
          </div>

          <form className="wl-search" onSubmit={handleSearch}>
            <input
              type="search"
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
              spellCheck="false"
              name="wl-stock-search"
              id="wl-stock-search"
              value={query}
              onChange={(e) => {
                const val = e.target.value;
                setQuery(val);
                if (val.trim() === "") {
                  setResults([]);
                  setMessage("");
                  setError("");
                }
              }}
              placeholder="Search companies, e.g. TCS, Reliance, Infosys..."
            />

            <button type="submit" disabled={loading}>
              {loading ? "Searching..." : "Search Stocks"}
            </button>
          </form>

          {message && <p className="wl-success">{message}</p>}
          {error && <p className="wl-error">{error}</p>}

          {results.length > 0 && (
            <div className="wl-results">
              <h3>Search Results</h3>

              {results.map((stock, index) => (
                <div
                  className="wl-result-row"
                  key={`${stock.ticker}-${stock.market}-${index}`}
                >
                  <div>
                    <strong>{stock.company_name}</strong>
                    <p>
                      {stock.ticker} · {stock.exchange || stock.market}
                    </p>
                    <small>
                      {stock.sector || "Sector unavailable"}
                    </small>
                  </div>

                  <button
                    disabled={
                      alreadySaved(stock) ||
                      busy === `${stock.ticker}-${stock.market}`
                    }
                    onClick={() => handleAdd(stock)}
                  >
                    {alreadySaved(stock)
                      ? "Added"
                      : busy === `${stock.ticker}-${stock.market}`
                      ? "Adding..."
                      : "+ Add"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="wl-panel">
          <div className="wl-panel-heading">
            <div>
              <h2>Saved Stocks</h2>
              <p>
                Your saved companies for market research.
              </p>
            </div>
            <span className="wl-tag">
              {stocks.length} SAVED
            </span>
          </div>

          {stocks.length > 0 && (
            <div className="wl-search">
              <input
                type="search"
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck="false"
                name="wl-filter-search"
                id="wl-filter-search"
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
                placeholder="Filter by company name, ticker or market..."
              />
            </div>
          )}

          {stocks.length === 0 ? (
            <div className="wl-empty">
              <div className="wl-empty-icon">☆</div>
              <h3>No stocks added yet</h3>
              <p>
                Search for a company above and add it to your personal watchlist.
              </p>
            </div>
          ) : filteredStocks.length === 0 ? (
            <div className="wl-empty">
              <h3>No matching stocks found</h3>
              <p>Try another company name, ticker or market.</p>
            </div>
          ) : (
            <div className="wl-table-wrap">
              <table className="wl-table">
                <thead>
                  <tr>
                    <th>COMPANY</th>
                    <th>TICKER</th>
                    <th>MARKET</th>
                    <th>DATE ADDED</th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredStocks.map((stock) => (
                    <tr key={stock.watchlist_id}>
                      <td className="wl-company">
                        {stock.company_name}
                      </td>

                      <td>{stock.ticker}</td>

                      <td>
                        <span className="wl-market">
                          {stock.market}
                        </span>
                      </td>

                      <td>
                        {stock.created_at
                          ? new Date(stock.created_at).toLocaleDateString("en-GB")
                          : "—"}
                      </td>

                      <td>
                        <div className="wl-row-actions">
                          <button
                            className="wl-research-btn"
                            disabled={
                              busy === `research-${stock.watchlist_id}`
                            }
                            onClick={() => handleStartResearch(stock)}
                          >
                            {busy === `research-${stock.watchlist_id}`
                              ? "Creating..."
                              : "Start Research"}
                          </button>

                          <button
                            className="wl-remove"
                            disabled={busy === stock.watchlist_id}
                            onClick={() =>
                              handleRemove(stock.watchlist_id)
                            }
                          >
                            {busy === stock.watchlist_id
                              ? "Removing..."
                              : "Remove"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

      </div>
    </DashboardLayout>
  );
}

export default Watchlist;
