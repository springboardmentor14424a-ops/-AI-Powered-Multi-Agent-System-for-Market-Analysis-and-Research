
import React, { useEffect, useState } from "react";
import "./Watchlist.css";

const API_URL = "http://127.0.0.1:8000";

function Watchlist({ token, onSelectStock }) {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [savedStocks, setSavedStocks] = useState([]);

  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const headers = {
    Authorization: `Bearer ${token}`
  };

  // Load the logged-in user's watchlist
  const fetchWatchlist = async () => {
    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/watchlist`, {
        headers
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to load watchlist");
      }

      setSavedStocks(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchWatchlist();
    }
  }, [token]);

  // Search by company name or ticker
  const handleSearch = async (e) => {
    e.preventDefault();

    setError("");
    setMessage("");
    setSearchResults([]);

    if (!query.trim()) {
      setError("Enter a company name or ticker symbol.");
      return;
    }

    try {
      setSearching(true);

      const response = await fetch(
        `${API_URL}/stocks/search?q=${encodeURIComponent(query.trim())}`,
        { headers }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Stock search failed");
      }

      setSearchResults(data);

      if (data.length === 0) {
        setMessage("No matching stocks found in the available dataset.");
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setSearching(false);
    }
  };

  // Add stock to watchlist
  const handleAddStock = async (ticker) => {
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_URL}/watchlist`, {
        method: "POST",
        headers: {
          ...headers,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          stock_ticker: ticker
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to add stock");
      }

      setMessage(`${data.stock_ticker} added to your watchlist.`);

      await fetchWatchlist();

    } catch (err) {
      setError(err.message);
    }
  };

  // Remove stock from watchlist
  const handleRemoveStock = async (ticker) => {
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
        throw new Error(data.detail || "Unable to remove stock");
      }

      setMessage(data.message);
      await fetchWatchlist();

    } catch (err) {
      setError(err.message);
    }
  };

  // Check whether a stock is already saved
  const isSaved = (ticker) => {
    return savedStocks.some(
      (stock) => stock.stock_ticker === ticker
    );
  };

  return (
    <section className="watchlist-card">

      <h2>Saved Stocks & Watchlist</h2>

      <p>
        Search for companies and save your favourite stocks
        for future research.
      </p>

      {/* Stock Search */}
      <form className="stock-search-form" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search company name or ticker (e.g. Microsoft or MSFT)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        <button type="submit" disabled={searching}>
          {searching ? "Searching..." : "Search Stock"}
        </button>
      </form>

      {/* Messages */}
      {error && (
        <p className="watchlist-error">{error}</p>
      )}

      {message && (
        <p className="watchlist-success">{message}</p>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="watchlist-results">
          <h3>Search Results</h3>

          {searchResults.map((stock) => (
            <div className="watchlist-stock" key={stock.symbol}>
              <div>
                <strong>{stock.company_name}</strong>
                <p>{stock.symbol}</p>
              </div>

              {isSaved(stock.symbol) ? (
                <span className="saved-label">Already Saved</span>
              ) : (
                <button
                  type="button"
                  onClick={() => handleAddStock(stock.symbol)}
                >
                  + Add
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Saved Stocks */}
      <div className="saved-stocks-section">
        <h3>My Saved Stocks</h3>

        {loading ? (
          <p>Loading saved stocks...</p>
        ) : savedStocks.length === 0 ? (
          <p>You have not saved any stocks yet.</p>
        ) : (
          savedStocks.map((stock) => (
            <div className="watchlist-stock" key={stock.id}>
              <div>
                <strong>{stock.company_name}</strong>
                <p>{stock.stock_ticker}</p>
                <small>
                  Saved: {new Date(stock.saved_date).toLocaleDateString()}
                </small>
              </div>

              <div className="watchlist-actions">
                <button
                  type="button"
                  onClick={() => onSelectStock(stock)}
                >
                  Research
                </button>

                <button
                  type="button"
                  className="remove-stock-button"
                  onClick={() => handleRemoveStock(stock.stock_ticker)}
                >
                  Remove
                </button>
              </div>
            </div>
          ))
        )}
      </div>

    </section>
  );
}

export default Watchlist;
