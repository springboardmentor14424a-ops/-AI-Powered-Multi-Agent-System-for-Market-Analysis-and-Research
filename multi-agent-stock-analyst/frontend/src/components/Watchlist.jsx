import { useEffect, useState } from "react";
import axios from "axios";
import "./Watchlist.css";

function Watchlist({ token }) {
    const [ticker, setTicker] = useState("");
    const [stocks, setStocks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");

    const headers = {
        Authorization: `Bearer ${token}`
    };

    // Fetch saved stocks
    const fetchWatchlist = async () => {
        try {
            const response = await axios.get(
                "http://127.0.0.1:8000/watchlist/",
                { headers }
            );

            setStocks(response.data);
            setError("");
        } catch (err) {
            setError(
                err.response?.data?.detail || "Unable to load watchlist"
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWatchlist();
    }, [token]);
    // Add searched stock to watchlist
    // Add a stock
    const handleAdd = async (e) => {
        e.preventDefault();

        if (!ticker.trim()) {
            setError("Please enter a stock ticker");
            return;
        }

        try {
            const response = await axios.post(
                "http://127.0.0.1:8000/watchlist/add",
                { ticker: ticker.trim().toUpperCase() },
                { headers }
            );

            setMessage(response.data.message);
            setTicker("");
            setError("");

            fetchWatchlist();
        } catch (err) {
            setError(
                err.response?.data?.detail || "Unable to add stock"
            );
            setMessage("");
        }
    };

    // Remove a stock
    const handleRemove = async (stockId) => {
        try {
            await axios.delete(
                `http://127.0.0.1:8000/watchlist/${stockId}`,
                { headers }
            );

            setMessage("Stock removed successfully");
            setError("");

            fetchWatchlist();
        } catch (err) {
            setError(
                err.response?.data?.detail || "Unable to remove stock"
            );
        }
    };

    return (
        <div className="watchlist-container">
            <h2>My Watchlist</h2>
            <p>Save and manage the stocks you want to track.</p>

            <form onSubmit={handleAdd} className="watchlist-form">
                <input
                    type="text"
                    placeholder="Enter ticker (e.g. TCS.NS)"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value)}
                />

                <button type="submit">
                    Add to Watchlist
                </button>
            </form>

            {error && <p className="watchlist-error">{error}</p>}
            {message && <p className="watchlist-success">{message}</p>}

            <h3>Saved Stocks</h3>

            {loading ? (
                <p>Loading watchlist...</p>
            ) : stocks.length === 0 ? (
                <p>Your watchlist is empty. Add your first stock!</p>
            ) : (
                <div className="watchlist-list">
                    {stocks.map((stock) => (
                        <div className="watchlist-item" key={stock.id}>
                            <span>{stock.ticker}</span>

                            <button
                                onClick={() => handleRemove(stock.id)}
                            >
                                Remove
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default Watchlist;