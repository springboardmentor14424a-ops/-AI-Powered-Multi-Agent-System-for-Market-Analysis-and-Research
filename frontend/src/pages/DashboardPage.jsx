import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import StockSearch from '../components/StockSearch';
import StockChart from '../components/StockChart';
import api from '../api/axios';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  Activity,
  Star,
  Clock,
  Loader2,
} from 'lucide-react';
import { motion } from 'framer-motion';

const DashboardPage = () => {
  const { user } = useAuth();
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [quote, setQuote] = useState(null);
  const [history, setHistory] = useState([]);
  const [period, setPeriod] = useState('1y');
  const [loadingQuote, setLoadingQuote] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const fetchStockData = async (symbol, p = period) => {
    setSelectedSymbol(symbol);
    setLoadingQuote(true);
    setLoadingHistory(true);

    try {
      const [quoteRes, histRes] = await Promise.all([
        api.get(`/stocks/${symbol}/quote`),
        api.get(`/stocks/${symbol}/history?period=${p}&interval=1d`),
      ]);
      setQuote(quoteRes.data);
      setHistory(histRes.data);
    } catch (err) {
      console.error('Failed to fetch stock data:', err);
      setQuote(null);
      setHistory([]);
    } finally {
      setLoadingQuote(false);
      setLoadingHistory(false);
    }
  };

  const handlePeriodChange = (p) => {
    setPeriod(p);
    if (selectedSymbol) {
      setLoadingHistory(true);
      api
        .get(`/stocks/${selectedSymbol}/history?period=${p}&interval=1d`)
        .then((res) => setHistory(res.data))
        .catch(() => setHistory([]))
        .finally(() => setLoadingHistory(false));
    }
  };

  const formatNumber = (n) => {
    if (n == null) return 'N/A';
    if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
    if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
    if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
    return `$${n.toLocaleString()}`;
  };

  const formatVolume = (n) => {
    if (n == null) return 'N/A';
    if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
    if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
    if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
    return n.toLocaleString();
  };

  const price = quote?.price ?? quote?.currentPrice;
  const prevClose = quote?.previous_close ?? quote?.previousClose;
  const change = quote?.change ?? (price != null && prevClose != null ? price - prevClose : null);
  const changePercent =
    quote?.changePercent ?? (change != null && prevClose ? (change / prevClose) * 100 : null);
  const isPositive = change != null ? change >= 0 : true;

  return (
    <div className="min-h-screen bg-[#0a0e1a] bg-grid-pattern">
      <Navbar />

      <main className="pt-20 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {/* Greeting */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-2xl md:text-3xl font-bold text-white">
            Welcome back,{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
              {user?.full_name || 'User'}
            </span>
            !
          </h1>
          <p className="text-slate-400 mt-1">Search and analyze stocks with AI-powered insights.</p>
        </motion.div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {/* Search */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mb-6"
            >
              <StockSearch onSelectStock={(sym) => fetchStockData(sym)} />
            </motion.div>

            {/* Quote Card */}
            {selectedSymbol && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6"
              >
                <div className="glass-card rounded-2xl p-6">
                  {loadingQuote ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
                    </div>
                  ) : quote ? (
                    <>
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                        <div>
                          <div className="flex items-center gap-3">
                            <h2 className="text-2xl font-bold text-white">{selectedSymbol}</h2>
                            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-sm font-medium ${
                              isPositive ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                            }`}>
                              {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                              {change != null ? `${change >= 0 ? '+' : ''}${change.toFixed(2)}` : ''}
                              {changePercent != null ? ` (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)` : ''}
                            </span>
                          </div>
                          <p className="text-slate-400 text-sm mt-1">{quote.name || quote.shortName || quote.longName || ''}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-3xl font-bold text-white">
                            ${price != null ? price.toFixed(2) : 'N/A'}
                          </p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <div className="p-3 bg-white/[0.04] border border-white/5 rounded-xl">
                          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                            <DollarSign className="w-3.5 h-3.5 text-cyan-400" /> Market Cap
                          </div>
                          <p className="text-white font-semibold">{formatNumber(quote.market_cap ?? quote.marketCap)}</p>
                        </div>
                        <div className="p-3 bg-white/[0.04] border border-white/5 rounded-xl">
                          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                            <Activity className="w-3.5 h-3.5 text-blue-400" /> Volume
                          </div>
                          <p className="text-white font-semibold">{formatVolume(quote.volume)}</p>
                        </div>
                        <div className="p-3 bg-white/[0.04] border border-white/5 rounded-xl">
                          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Day High
                          </div>
                          <p className="text-white font-semibold">
                            {(quote.day_high ?? quote.dayHigh) != null ? `$${(quote.day_high ?? quote.dayHigh).toFixed(2)}` : 'N/A'}
                          </p>
                        </div>
                        <div className="p-3 bg-white/[0.04] border border-white/5 rounded-xl">
                          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                            <TrendingDown className="w-3.5 h-3.5 text-rose-400" /> Day Low
                          </div>
                          <p className="text-white font-semibold">
                            {(quote.day_low ?? quote.dayLow) != null ? `$${(quote.day_low ?? quote.dayLow).toFixed(2)}` : 'N/A'}
                          </p>
                        </div>
                      </div>
                    </>
                  ) : (
                    <p className="text-slate-400 text-center py-4">Failed to load quote data</p>
                  )}
                </div>
              </motion.div>
            )}

            {/* Chart */}
            {selectedSymbol && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <div className="glass-card rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Price History</h3>
                  {loadingHistory ? (
                    <div className="flex items-center justify-center py-20">
                      <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
                    </div>
                  ) : (
                    <StockChart
                      data={history}
                      selectedPeriod={period}
                      onPeriodChange={handlePeriodChange}
                      symbol={selectedSymbol}
                    />
                  )}
                </div>
              </motion.div>
            )}

            {/* Empty state */}
            {!selectedSymbol && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="glass-card rounded-2xl p-12 text-center"
              >
                <BarChart3 className="w-12 h-12 text-cyan-400/60 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-200 mb-2">Search for a Stock</h3>
                <p className="text-sm text-slate-400 max-w-sm mx-auto mb-6">
                  Use the search bar above to find stocks by symbol or name, or pick a popular ticker below:
                </p>
                <div className="flex flex-wrap items-center justify-center gap-2">
                  {['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'TSLA'].map((ticker) => (
                    <button
                      key={ticker}
                      onClick={() => fetchStockData(ticker)}
                      className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-white/[0.06] border border-white/10 text-cyan-300 hover:bg-cyan-500/20 hover:border-cyan-400/40 transition-all"
                    >
                      {ticker}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </div>

          {/* Sidebar */}
          <div className="w-full lg:w-80 flex-shrink-0 space-y-6">
            {/* Watchlist */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
            >
              <div className="flex items-center gap-2 mb-4">
                <Star className="w-5 h-5 text-yellow-400" />
                <h3 className="text-white font-semibold">Watchlist</h3>
              </div>
              <div className="text-center py-6">
                <Star className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p className="text-sm text-slate-500">Your watchlist is empty</p>
                <p className="text-xs text-slate-600 mt-1">Search and add stocks to track</p>
              </div>
            </motion.div>

            {/* Recent Searches */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
            >
              <div className="flex items-center gap-2 mb-4">
                <Clock className="w-5 h-5 text-slate-400" />
                <h3 className="text-white font-semibold">Recent Searches</h3>
              </div>
              <div className="text-center py-6">
                <Clock className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p className="text-sm text-slate-500">No recent searches</p>
                <p className="text-xs text-slate-600 mt-1">Your search history will appear here</p>
              </div>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;
