
import React, { useState } from "react";
import "./StockSearch.css";

const API_URL = "http://127.0.0.1:8000";

function StockSearch({ token, onSelectStock }) {
  const [searchText, setSearchText] = useState("");
  const [searchResults, setSearchResults] = useState([]);

  const [selectedStock, setSelectedStock] = useState(null);
  const [marketData, setMarketData] = useState(null);

  const [analysisPeriod, setAnalysisPeriod] = useState("3 Months");

  const [searchLoading, setSearchLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);

  const [error, setError] = useState("");

  // Search companies by name or ticker
  const handleSearch = async (e) => {
    e.preventDefault();

    if (!searchText.trim()) {
      setError("Please enter a company name or ticker symbol.");
      return;
    }

    setError("");
    setSearchResults([]);
    setSelectedStock(null);
    setMarketData(null);
    setSearchLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/stocks/search?q=${encodeURIComponent(searchText.trim())}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Stock search failed.");
      }

      setSearchResults(data);

      if (data.length === 0) {
        setError("No matching companies with available historical data were found.");
      }

    } catch (err) {
      setError(err.message || "Unable to search companies.");
    } finally {
      setSearchLoading(false);
    }
  };

  // Select a company
  const handleSelectStock = (stock) => {
    setSelectedStock(stock);
    setMarketData(null);
    setError("");
  };

  // Collect historical market data
  const handleGetMarketData = async () => {
    if (!selectedStock) {
      setError("Please select a company first.");
      return;
    }

    setError("");
    setMarketData(null);
    setDataLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/stocks/${encodeURIComponent(selectedStock.symbol)}/market-data?analysis_period=${encodeURIComponent(analysisPeriod)}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to collect market data."
        );
      }

      setMarketData(data);

    } catch (err) {
      setError(err.message || "Unable to collect market data.");
    } finally {
      setDataLoading(false);
    }
  };

  // Send selected stock to the next research module
  const handleStartResearch = () => {
    if (!selectedStock) return;

    if (onSelectStock) {
      onSelectStock({
        company_name: selectedStock.company_name,
        stock_ticker: selectedStock.symbol
      });
    }
  };

  return (
    <div className="stock-search-container">

      <div className="stock-search-card">

        <h2>Stock Search and Market Data</h2>

        <p className="stock-search-subtitle">
          Search for companies using their name or ticker symbol.
        </p>

        <form onSubmit={handleSearch} className="stock-search-form">

          <input
            type="text"
            placeholder="Search Apple, Microsoft, AAPL, MSFT..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />

          <button type="submit" disabled={searchLoading}>
            {searchLoading ? "Searching..." : "Search"}
          </button>

        </form>

        {error && (
          <div className="stock-error">
            {error}
          </div>
        )}

        {/* Search results */}
        {searchResults.length > 0 && (
          <div className="stock-results">

            <h3>Search Results</h3>

            {searchResults.map((stock) => (
              <div
                className={`stock-result-item ${
                  selectedStock?.symbol === stock.symbol
                    ? "selected"
                    : ""
                }`}
                key={stock.symbol}
              >

                <div className="stock-result-details">

                  <strong>{stock.company_name}</strong>

                  <span>
                    Ticker: {stock.symbol}
                  </span>

                  <span>
                    Exchange code: {stock.listing_exchange}
                  </span>

                </div>

                <button
                  type="button"
                  onClick={() => handleSelectStock(stock)}
                >
                  {selectedStock?.symbol === stock.symbol
                    ? "Selected"
                    : "Select"}
                </button>

              </div>
            ))}

          </div>
        )}

        {/* Selected company */}
        {selectedStock && (
          <div className="selected-stock-section">

            <h3>Selected Company</h3>

            <p>
              <strong>Company:</strong>{" "}
              {selectedStock.company_name}
            </p>

            <p>
              <strong>Ticker:</strong>{" "}
              {selectedStock.symbol}
            </p>

            <label>Analysis Period</label>

            <select
              value={analysisPeriod}
              onChange={(e) => setAnalysisPeriod(e.target.value)}
            >
              <option value="1 Month">1 Month</option>
              <option value="3 Months">3 Months</option>
              <option value="6 Months">6 Months</option>
              <option value="1 Year">1 Year</option>
              <option value="5 Years">5 Years</option>
            </select>

            <button
              type="button"
              className="market-data-button"
              onClick={handleGetMarketData}
              disabled={dataLoading}
            >
              {dataLoading
                ? "Collecting Data..."
                : "Get Market Data"}
            </button>

          </div>
        )}

        {/* Market statistics */}
        {marketData && (
          <div className="market-data-section">

            <h3>Market Data Summary</h3>

            <p className="data-period">
              {marketData.ticker} | {marketData.analysis_period}
            </p>

            <p>
              <strong>Data period:</strong>{" "}
              {marketData.data_start_date} to{" "}
              {marketData.data_end_date}
            </p>

            <div className="market-stat-grid">

              <div className="market-stat">
                <span>Starting Price</span>
                <strong>{marketData.starting_price}</strong>
              </div>

              <div className="market-stat">
                <span>Ending Price</span>
                <strong>{marketData.ending_price}</strong>
              </div>

              <div className="market-stat">
                <span>Highest Price</span>
                <strong>{marketData.highest_price}</strong>
              </div>

              <div className="market-stat">
                <span>Lowest Price</span>
                <strong>{marketData.lowest_price}</strong>
              </div>

              <div className="market-stat">
                <span>Average Price</span>
                <strong>{marketData.average_price}</strong>
              </div>

              <div className="market-stat">
                <span>Average Volume</span>
                <strong>
                  {Number(marketData.average_volume).toLocaleString()}
                </strong>
              </div>

              <div className="market-stat">
                <span>Price Change</span>
                <strong>
                  {marketData.price_change}
                </strong>
              </div>

              <div className="market-stat">
                <span>Percentage Change</span>
                <strong>
                  {marketData.percentage_change}%
                </strong>
              </div>

            </div>

            <p className="record-count">
              Total historical records: {marketData.records_count}
            </p>

            <h3>Historical Price Records</h3>

            <div className="stock-table-wrapper">

              <table className="stock-data-table">

                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Close</th>
                    <th>Volume</th>
                  </tr>
                </thead>

                <tbody>
                  {marketData.historical_data.map((record) => (
                    <tr key={record.date}>
                      <td>{record.date}</td>
                      <td>{record.open}</td>
                      <td>{record.high}</td>
                      <td>{record.low}</td>
                      <td>{record.close}</td>
                      <td>
                        {Number(record.volume).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>

              </table>

            </div>

            <button
              type="button"
              className="research-select-button"
              onClick={handleStartResearch}
            >
              Use This Stock for Research
            </button>

          </div>
        )}

      </div>

    </div>
  );
}

export default StockSearch;
