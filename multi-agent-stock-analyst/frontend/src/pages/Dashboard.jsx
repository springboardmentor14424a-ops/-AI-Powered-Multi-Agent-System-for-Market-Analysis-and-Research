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
function Dashboard({ token, onLogout ,  onCompanySelected  }) {
    const [user, setUser] = useState(null);

    // Profile loading and error states
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    // Stock search states
    const [ticker, setTicker] = useState("");
    const [period, setPeriod] = useState("1mo");
    const [stockData, setStockData] = useState(null);
    const [historyData, setHistoryData] = useState(null);
    // Independent OHLCV table states
    const [ohlcvPeriod, setOhlcvPeriod] = useState("1mo");
    const [ohlcvData, setOhlcvData] = useState(null);
    const [ohlcvLoading, setOhlcvLoading] = useState(false);
    const [ohlcvError, setOhlcvError] = useState("");
    const [stockLoading, setStockLoading] = useState(false);
    const [stockError, setStockError] = useState("");
    const [showWatchlist, setShowWatchlist] = useState(false);
    const [watchlistMessage, setWatchlistMessage] = useState("");
    const [watchlistError, setWatchlistError] = useState("");
    const [addingToWatchlist, setAddingToWatchlist] = useState(false);
    // Company Research states

    const [companyProfile, setCompanyProfile] = useState(null);
    const [companyLoading, setCompanyLoading] = useState(false);
    const [companyError, setCompanyError] = useState("");

    // Financial statement states
    const [financialData, setFinancialData] = useState(null);
    const [financialPeriod, setFinancialPeriod] = useState("annual");
    const [financialLoading, setFinancialLoading] = useState(false);
    const [financialError, setFinancialError] = useState("");
    const [selectedMarket, setSelectedMarket] = useState("NSE");
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
        const selectedTicker = ticker.trim();

        // Clear previous company's information
        setCompanyProfile(null);
        setCompanyError("");
        setFinancialData(null);
        setFinancialError("");
        setFinancialPeriod("annual");
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
                `http://127.0.0.1:8000/finance/stock/${encodeURIComponent(selectedTicker)}`,
                {
                    params: { market: selectedMarket },
                    headers
                }
            );

            // Fetch historical stock information
            const historyResponse = await axios.get(
                `http://127.0.0.1:8000/finance/history/${encodeURIComponent(selectedTicker)}`,
                {
                    params: {
                        period: period,
                        market: selectedMarket
                    },
                    headers
                }
            );

            setStockData(stockResponse.data);
            setHistoryData(historyResponse.data);
            const ohlcvResponse = await axios.get(
                `http://127.0.0.1:8000/finance/history/${selectedTicker}?period=${ohlcvPeriod}`,
                { headers }
            );

            setOhlcvData(ohlcvResponse.data);
            // Fetch company profile and financial statements
            await fetchCompanyProfile(selectedTicker);

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

    // Fetch company profile using the ticker from the main stock search
    const fetchCompanyProfile = async (selectedTicker) => {
        try {
            setCompanyLoading(true);
            setCompanyError("");
            setCompanyProfile(null);

            const headers = {
                Authorization: `Bearer ${token}`
            };

            const response = await axios.get(
                `http://127.0.0.1:8000/finance/company/${encodeURIComponent(selectedTicker)}/profile`,
                {
                    params: { market: selectedMarket },
                    headers
                }
            );

            setCompanyProfile(response.data);
            const companyName =
    response.data?.profile?.company_name ||
    response.data?.ticker ||
    selectedTicker;

onCompanySelected?.({
    name: companyName,
    ticker: selectedTicker,
    profile: response.data?.profile
});

            // Load annual financial statements for the same company
            setFinancialPeriod("annual");
            await fetchCompanyFinancials(selectedTicker, "annual");

        } catch (err) {
            console.error("Company profile error:", err);

            if (err.response?.status === 401) {
                setCompanyError("Session expired. Please log in again.");
                onLogout();
            } else {
                setCompanyError(
                    err.response?.data?.detail ||
                    "Unable to retrieve company profile."
                );
            }
        } finally {
            setCompanyLoading(false);
        }
    };


    // Fetch annual or quarterly financial statements
    const fetchCompanyFinancials = async (selectedTicker, selectedPeriod) => {
        try {
            setFinancialLoading(true);
            setFinancialError("");
            setFinancialData(null);

            const headers = {
                Authorization: `Bearer ${token}`
            };

            const response = await axios.get(
                `http://127.0.0.1:8000/finance/company/${encodeURIComponent(selectedTicker)}/financials`,
                {
                    params: {
                        period: selectedPeriod,
                        market: selectedMarket
                    },
                    headers
                }
            );

            setFinancialData(response.data);

        } catch (err) {
            console.error("Financial statement error:", err);

            if (err.response?.status === 401) {
                setFinancialError("Session expired. Please log in again.");
                onLogout();
            } else {
                setFinancialError(
                    err.response?.data?.detail ||
                    "Unable to retrieve financial statements."
                );
            }
        } finally {
            setFinancialLoading(false);
        }
    };

    // Fetch OHLCV data independently
    const fetchOHLCVData = async (selectedPeriod) => {
        if (!historyData?.ticker) return;

        try {
            setOhlcvLoading(true);
            setOhlcvError("");

            const headers = {
                Authorization: `Bearer ${token}`
            };

            const response = await axios.get(
                `http://127.0.0.1:8000/finance/history/${encodeURIComponent(ticker.trim())}`,
                {
                    params: {
                        period: selectedPeriod,
                        market: selectedMarket
                    },
                    headers
                }
            );

            setOhlcvData(response.data);

        } catch (err) {
            console.error("OHLCV data error:", err);

            setOhlcvError(
                err.response?.data?.detail ||
                "Unable to fetch OHLCV data."
            );

        } finally {
            setOhlcvLoading(false);
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

    // Render financial statement data as a table
    const renderStatementTable = (title, statement) => {

        if (!statement || Object.keys(statement).length === 0) {
            return (
                <div className="financial-card">
                    <h3>{title}</h3>
                    <p>No data available for this statement.</p>
                </div>
            );
        }

        const periods = Object.keys(statement);

        const metrics = [
            ...new Set(
                periods.flatMap(date =>
                    Object.keys(statement[date] || {})
                )
            )
        ];

        const formatFinancialValue = (value) => {
            if (value === null || value === undefined) {
                return "—";
            }

            return Number(value).toLocaleString("en-IN", {
                maximumFractionDigits: 2
            });
        };

        return (
            <div className="financial-card">
                <h3>{title}</h3>

                <div className="financial-table-wrapper">
                    <table className="financial-table">

                        <thead>
                            <tr>
                                <th>Metric</th>

                                {periods.map(date => (
                                    <th key={date}>{date}</th>
                                ))}
                            </tr>
                        </thead>

                        <tbody>
                            {metrics.map(metric => (
                                <tr key={metric}>
                                    <td>{metric}</td>

                                    {periods.map(date => (
                                        <td key={date}>
                                            {formatFinancialValue(
                                                statement[date]?.[metric]
                                            )}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>

                    </table>
                </div>
            </div>
        );
    };

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
    const stockSuggestions = [
        { name: "Reliance Industries", ticker: "RELIANCE" },
        { name: "Tata Consultancy Services", ticker: "TCS" },
        { name: "Infosys", ticker: "INFY" },
        { name: "HDFC Bank", ticker: "HDFCBANK" },
        { name: "ICICI Bank", ticker: "ICICIBANK" },
        { name: "State Bank of India", ticker: "SBIN" },
        { name: "ITC", ticker: "ITC" },
        { name: "Wipro", ticker: "WIPRO" },
        { name: "Larsen & Toubro", ticker: "LT" },
        { name: "Axis Bank", ticker: "AXISBANK" }
    ];
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
                        <select
                            className="market-select"
                            value={selectedMarket}
                            onChange={(e) => setSelectedMarket(e.target.value)}
                        >
                            <option value="NSE">India - NSE</option>
                            <option value="BSE">India - BSE</option>
                            <option value="NASDAQ">USA - NASDAQ</option>
                            <option value="NYSE">USA - NYSE</option>
                        </select>
                        <input
                            type="text"
                            list="stock-options"
                            placeholder="Search company or enter ticker..."
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value)}
                        />

                        <datalist id="stock-options">
                            {stockSuggestions.map((stock) => (
                                <option
                                    key={stock.ticker}
                                    value={stock.ticker}
                                    label={stock.name}
                                />
                            ))}
                        </datalist>

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

                            {/* OHLCV Historical Data Table */}
                            <div className="ohlcv-section">

                                <div className="ohlcv-header">
                                    <div>
                                        <h3>Historical OHLCV Data</h3>
                                        <p>Daily Open, High, Low, Close and Volume details</p>
                                    </div>

                                    <select
                                        value={ohlcvPeriod}
                                        onChange={(e) => {
                                            const selectedPeriod = e.target.value;
                                            setOhlcvPeriod(selectedPeriod);
                                            fetchOHLCVData(selectedPeriod);
                                        }}
                                    >
                                        <option value="1mo">1 Month</option>
                                        <option value="3mo">3 Months</option>
                                        <option value="6mo">6 Months</option>
                                    </select>
                                </div>

                                <div className="ohlcv-table-wrapper">
                                    <table className="ohlcv-table">
                                        {ohlcvLoading && <p>Loading OHLCV data...</p>}

                                        {ohlcvError && <p className="error">{ohlcvError}</p>}

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
                                            {(ohlcvData?.history || []).map((item, index) => (

                                                <tr key={index}>
                                                    <td>{item.date}</td>

                                                    <td>{formatPrice(item.open)}</td>

                                                    <td>{formatPrice(item.high)}</td>

                                                    <td>{formatPrice(item.low)}</td>

                                                    <td>{formatPrice(item.close)}</td>

                                                    <td>
                                                        {item.volume.toLocaleString("en-IN")}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>

                                    </table>
                                </div>

                            </div>
                            <section className="company-research-section">


                                {companyError && (
                                    <p className="error">{companyError}</p>
                                )}
                                {companyLoading && <p>Loading company information...</p>}

                                {companyError && <p className="error">{companyError}</p>}
                                {/* Company Profile */}
                                {companyProfile && (
                                    <div className="company-profile-result">

                                        <div className="company-profile-header">
                                            <div>
                                                <h2>
                                                    {companyProfile.profile.company_name ||
                                                        companyProfile.ticker}
                                                </h2>

                                                <p>
                                                    {companyProfile.profile.sector || "Sector unavailable"}
                                                    {" · "}
                                                    {companyProfile.profile.industry || "Industry unavailable"}
                                                </p>
                                            </div>

                                            <span className="company-ticker">
                                                {companyProfile.ticker}
                                            </span>
                                        </div>

                                        <div className="company-info-grid">

                                            <div className="company-info-card">
                                                <span>Country</span>
                                                <h3>
                                                    {companyProfile.profile.country || "N/A"}
                                                </h3>
                                            </div>

                                            <div className="company-info-card">
                                                <span>Market Capitalization</span>
                                                <h3>
                                                    {companyProfile.profile.market_cap != null
                                                        ? Number(
                                                            companyProfile.profile.market_cap
                                                        ).toLocaleString("en-IN")
                                                        : "N/A"}
                                                </h3>
                                            </div>

                                            <div className="company-info-card">
                                                <span>Employees</span>
                                                <h3>
                                                    {companyProfile.profile.employees != null
                                                        ? Number(
                                                            companyProfile.profile.employees
                                                        ).toLocaleString("en-IN")
                                                        : "N/A"}
                                                </h3>
                                            </div>

                                            <div className="company-info-card">
                                                <span>Exchange</span>
                                                <h3>
                                                    {companyProfile.profile.exchange || "N/A"}
                                                </h3>
                                            </div>

                                            <div className="company-info-card">
                                                <span>Currency</span>
                                                <h3>
                                                    {companyProfile.profile.currency || "N/A"}
                                                </h3>
                                            </div>

                                            <div className="company-info-card">
                                                <span>Website</span>
                                                <h3>
                                                    {companyProfile.profile.website ? (
                                                        <a
                                                            href={companyProfile.profile.website}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                        >
                                                            Visit Website
                                                        </a>
                                                    ) : "N/A"}
                                                </h3>
                                            </div>

                                        </div>

{/* Valuation and Profitability Ratios */}
<div className="valuation-ratios-section">
    <h3>Valuation & Profitability Ratios</h3>

    <div className="valuation-ratios-grid">

        <div className="company-info-card">
            <span>Price to Earnings (P/E)</span>
            <h3>
                {companyProfile.profile.pe_ratio != null
                    ? Number(companyProfile.profile.pe_ratio).toFixed(2)
                    : "N/A"}
            </h3>
        </div>

        <div className="company-info-card">
            <span>Price to Book (P/B)</span>
            <h3>
                {companyProfile.profile.pb_ratio != null
                    ? Number(companyProfile.profile.pb_ratio).toFixed(2)
                    : "N/A"}
            </h3>
        </div>

        <div className="company-info-card">
            <span>Return on Equity (ROE)</span>
            <h3>
                {companyProfile.profile.roe != null
                    ? `${Number(companyProfile.profile.roe).toFixed(2)}%`
                    : "N/A"}
            </h3>
        </div>

    </div>

    <p className="valuation-note">
        P/E and P/B represent current market valuation ratios.
        ROE represents the reported return on equity.
    </p>
</div>


                                        <div className="company-description">
                                            <h3>About the Company</h3>
                                            <p>
                                                {companyProfile.profile.business_summary ||
                                                    "Company description unavailable."}
                                            </p>
                                        </div>

                                        <div className="company-source">
                                            <span>
                                                Source: {companyProfile.source}
                                            </span>

                                            <span>
                                                Retrieved: {new Date(
                                                    companyProfile.retrieved_at
                                                ).toLocaleString("en-IN")}
                                            </span>
                                        </div>

                                    </div>
                                )}

                                {/* Financial Statements */}
                                {companyProfile && (
                                    <div className="financial-statements-section">

                                        <div className="financial-header">
                                            <div>
                                                <h2>Financial Statements</h2>
                                                <p>
                                                    Explore the company's financial performance.
                                                </p>
                                            </div>

                                            <select
                                                value={financialPeriod}
                                                onChange={(e) => {
                                                    const selectedPeriod = e.target.value;

                                                    setFinancialPeriod(selectedPeriod);
                                                    fetchCompanyFinancials(companyProfile.ticker, selectedPeriod);
                                                }}
                                            >
                                                <option value="annual">Annual</option>
                                                <option value="quarterly">Quarterly</option>
                                            </select>
                                        </div>

                                        {financialLoading && (
                                            <p>Retrieving financial statements...</p>
                                        )}

                                        {financialError && (
                                            <p className="error">{financialError}</p>
                                        )}

                                        {financialData && (
                                            <>
                                                {renderStatementTable(
                                                    "Income Statement",
                                                    financialData.financial_statements.income_statement
                                                )}

                                                {renderStatementTable(
                                                    "Balance Sheet",
                                                    financialData.financial_statements.balance_sheet
                                                )}

                                                {renderStatementTable(
                                                    "Cash Flow Statement",
                                                    financialData.financial_statements.cash_flow_statement
                                                )}

                                                <div className="company-source">
                                                    <span>
                                                        Source: {financialData.source}
                                                    </span>

                                                    <span>
                                                        Retrieved: {new Date(
                                                            financialData.retrieved_at
                                                        ).toLocaleString("en-IN")}
                                                    </span>
                                                </div>
                                            </>
                                        )}

                                    </div>
                                )}

                            </section>
                        </div>
                    )}

                </section>

            </main>
        </div>
    );
}

export default Dashboard;
