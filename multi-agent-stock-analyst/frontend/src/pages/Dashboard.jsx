import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from "recharts";
import { useEffect, useState } from "react";
import axios from "axios";
import "./Dashboard.css";
import Watchlist from "../components/Watchlist";
function Dashboard({ token, onLogout }) {
    const [user, setUser] = useState(null);

    // Profile loading and error states
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // Stock search states
    const [ticker, setTicker] = useState("");
    const [period, setPeriod] = useState("1mo");
    const [stockData, setStockData] = useState(null);
    const [historyData, setHistoryData] = useState(null);
    const [stockLoading, setStockLoading] = useState(false);
    const [stockError, setStockError] = useState("");
    const [showWatchlist, setShowWatchlist] = useState(false);
    const [watchlistMessage, setWatchlistMessage] = useState("");
    const [watchlistError, setWatchlistError] = useState("");
    const [addingToWatchlist, setAddingToWatchlist] = useState(false);
    // Fetch logged-in user profile
    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const response = await axios.get(
                    "http://127.0.0.1:8000/auth/me",
                    {
                        headers: {
                            Authorization: `Bearer ${token}`
                        }
                    }
                );

                setUser(response.data);

            } catch (err) {
                console.error("Profile error:", err);
                setError("Session expired. Please log in again.");
                onLogout();

            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, [token]);

    // Fetch stock information and historical data
    const fetchStockData = async (e) => {
        e.preventDefault();

        if (!ticker.trim()) {
            setStockError("Please enter a stock ticker.");
            return;
        }

        try {
            setStockLoading(true);
            setStockError("");
            setStockData(null);
            setHistoryData(null);

            const headers = {
                Authorization: `Bearer ${token}`
            };

            // Fetch current stock information
            const stockResponse = await axios.get(
                `http://127.0.0.1:8000/finance/stock/${ticker.trim()}`,
                { headers }
            );

            // Fetch historical stock information
            const historyResponse = await axios.get(
                `http://127.0.0.1:8000/finance/history/${ticker.trim()}?period=${period}`,
                { headers }
            );

            setStockData(stockResponse.data);
            setHistoryData(historyResponse.data);

        } catch (err) {
            console.error("Stock data error:", err);

            if (err.response?.status === 401) {
                setStockError("Session expired. Please log in again.");
                onLogout();
            } else {
                setStockError(
                    err.response?.data?.detail ||
                    "Unable to fetch stock data. Please check the ticker."
                );
            }

        } finally {
            setStockLoading(false);
        }
    };

// Add searched stock to watchlist
const handleAddToWatchlist = async () => {
    try {
        setAddingToWatchlist(true);
        setWatchlistMessage("");
        setWatchlistError("");

        const headers = {
            Authorization: `Bearer ${token}`
        };

        const response = await axios.post(
            "http://127.0.0.1:8000/watchlist/add",
            {
                ticker: historyData.ticker
            },
            { headers }
        );

        setWatchlistMessage(response.data.message);

    } catch (err) {
        if (err.response?.status === 409) {
            setWatchlistError(
                "This stock is already in your watchlist."
            );
        } else {
            setWatchlistError(
                err.response?.data?.detail ||
                "Unable to add stock to watchlist."
            );
        }
    } finally {
        setAddingToWatchlist(false);
    }
};

    // Prepare historical data for the chart
    const chartData = historyData?.history || [];

    const latestClose = chartData.length
        ? chartData[chartData.length - 1].close
        : 0;

    const firstClose = chartData.length
        ? chartData[0].close
        : 0;

    const priceChange = latestClose - firstClose;

    const percentageChange = firstClose
        ? (priceChange / firstClose) * 100
        : 0;

    const formatPrice = (value) =>
        new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 2
        }).format(value);
    // Skeleton loading screen
    if (loading) {
        return (
            <div className="dashboard-page">
                <nav className="dashboard-navbar">
                    <h2>
                        Market Research <span>AI</span>
                    </h2>
                    <div className="skeleton skeleton-button"></div>
                </nav>

                <main className="dashboard-content">
                    <div className="skeleton skeleton-heading"></div>
                    <div className="skeleton skeleton-subheading"></div>
                </main>
            </div>
        );
    }

    if (error) {
        return <p className="error">{error}</p>;
    }

    return (
        <div className="dashboard-page">

            {/* Navbar */}
            <nav className="dashboard-navbar">
                <h2>
                    Market Research <span>AI</span>
                </h2>

                <div className="navbar-user">
                    <span className="username">
                        {user?.full_name}
                    </span>

                    <button
                        className="logout-button"
                        onClick={onLogout}
                    >
                        Logout
                    </button>
                </div>
            </nav>

            <main className="dashboard-content">

                {/* Welcome section */}
                <h1>
                    Welcome back, {user?.full_name}!
                </h1>

                <p className="welcome-message">
                    Welcome to your AI-powered market research dashboard.
                    Explore market trends and discover intelligent insights.
                </p>

                <p className="user-email">
                    Email: {user?.email}
                </p>


                {/* Stock search section */}
                <section className="stock-search-section">
                    <h2>Stock Market Research</h2>
                    <button
                        className={`watchlist-toggle-btn ${showWatchlist ? "active" : ""}`}
                        onClick={() => setShowWatchlist(!showWatchlist)}
                    >
                        <span className="watchlist-icon">
                            {showWatchlist ? "✕" : "☆"}
                        </span>

                        {showWatchlist ? "Hide Watchlist" : "My Watchlist"}
                    </button>
                    {showWatchlist && (
                        <Watchlist token={token} />
                    )}
                    <form onSubmit={fetchStockData}>
                        <input
                            type="text"
                            placeholder="Enter ticker (e.g. RELIANCE.NS)"
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value)}
                        />

                        <select
                            value={period}
                            onChange={(e) => setPeriod(e.target.value)}
                        >
                            <option value="1mo">1 Month</option>
                            <option value="3mo">3 Months</option>
                            <option value="6mo">6 Months</option>
                            <option value="1y">1 Year</option>
                            <option value="5y">5 Years</option>
                        </select>

                        <button type="submit" disabled={stockLoading}>
                            {stockLoading ? "Loading..." : "Search Stock"}
                        </button>
                    </form>

                    {stockError && (
                        <p className="error">{stockError}</p>
                    )}

                    {stockLoading && (
                        <p>Fetching stock information...</p>
                    )}

                    {historyData && (
                        <div className="history-result">

                            <div className="chart-header">
                                <div>
                                    <h3>{historyData.ticker} Price History</h3>
                                    <p>Historical closing prices</p>
                                </div>

                                <span className="period-label">
                                    {historyData.period}
                                </span>
                            </div>
                            <div className="add-watchlist-section">
                                <button
                                    className="add-watchlist-btn"
                                    onClick={handleAddToWatchlist}
                                    disabled={addingToWatchlist}
                                >
                                    {addingToWatchlist
                                        ? "Adding..."
                                        : "☆ Add to Watchlist"}
                                </button>

                                {watchlistMessage && (
                                    <p className="watchlist-success">
                                        {watchlistMessage}
                                    </p>
                                )}

                                {watchlistError && (
                                    <p className="watchlist-error">
                                        {watchlistError}
                                    </p>
                                )}
                            </div>
                            {/* Price Summary */}
                            <div className="price-summary">

                                <div className="price-card">
                                    <p>Latest Closing Price</p>
                                    <h2>{formatPrice(latestClose)}</h2>
                                </div>

                                <div className="price-card">
                                    <p>Change During Period</p>

                                    <h2 className={priceChange >= 0 ? "positive" : "negative"}>
                                        {priceChange >= 0 ? "+" : ""}
                                        {formatPrice(priceChange)}
                                    </h2>

                                    <span className={percentageChange >= 0 ? "positive" : "negative"}>
                                        {percentageChange >= 0 ? "+" : ""}
                                        {percentageChange.toFixed(2)}%
                                    </span>
                                </div>

                            </div>

                            {/* Historical Price Chart */}
                            <div className="chart-container">

                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart
                                        data={chartData}
                                        margin={{
                                            top: 15,
                                            right: 25,
                                            left: 15,
                                            bottom: 10
                                        }}
                                    >
                                        <CartesianGrid
                                            strokeDasharray="3 3"
                                            stroke="#e2e8f0"
                                        />

                                        <XAxis
                                            dataKey="date"
                                            tick={{ fontSize: 11 }}
                                            tickFormatter={(date) => {
                                                const parsedDate = new Date(date + "T00:00:00");
                                                return parsedDate.toLocaleDateString(
                                                    "en-IN",
                                                    { day: "numeric", month: "short" }
                                                );
                                            }}
                                        />

                                        <YAxis
                                            domain={["auto", "auto"]}
                                            tick={{ fontSize: 11 }}
                                            tickFormatter={(value) => `₹${value}`}
                                        />

                                        <Tooltip
                                            labelFormatter={(date) => `Date: ${date}`}
                                            formatter={(value) => [
                                                formatPrice(value),
                                                "Closing Price"
                                            ]}
                                            contentStyle={{
                                                borderRadius: "10px",
                                                border: "1px solid #e2e8f0"
                                            }}
                                        />

                                        <Line
                                            type="monotone"
                                            dataKey="close"
                                            stroke="#2563eb"
                                            strokeWidth={3}
                                            dot={false}
                                            activeDot={{
                                                r: 6,
                                                fill: "#2563eb"
                                            }}
                                        />

                                    </LineChart>
                                </ResponsiveContainer>

                            </div>

                            <p className="chart-note">
                                Chart based on historical closing prices.
                                Market data may be delayed.
                            </p>

                        </div>
                    )}

                </section>

            </main>
        </div>
    );
}

export default Dashboard;
