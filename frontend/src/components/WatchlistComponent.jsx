import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Plus, 
  Trash2, 
  TrendingUp, 
  TrendingDown, 
  Sparkles, 
  AlertCircle, 
  CheckCircle2, 
  RefreshCw,
  Layers
} from 'lucide-react';
import { watchlistApi, stocksApi } from '../services/api';

export default function WatchlistComponent({ onLaunchTask, currentMarket }) {
  const [watchlist, setWatchlist] = useState([]);
  const [quotes, setQuotes] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [actionError, setActionError] = useState('');
  const [actionSuccess, setActionSuccess] = useState('');

  // Load Watchlist
  const loadWatchlist = async () => {
    setIsLoading(true);
    setActionError('');
    try {
      const items = await watchlistApi.getAll();
      setWatchlist(items);
      
      // Fetch quotes for all saved stocks
      const quotePromises = items.map(async (item) => {
        try {
          const q = await stocksApi.getQuote(item.ticker, currentMarket);
          return { ticker: item.ticker, quote: q };
        } catch {
          return null;
        }
      });
      const resolved = await Promise.all(quotePromises);
      const quoteMap = {};
      resolved.forEach((res) => {
        if (res) quoteMap[res.ticker] = res.quote;
      });
      setQuotes(quoteMap);
    } catch (err) {
      setActionError(err.message || 'Failed to load watchlist.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadWatchlist();
  }, [currentMarket]);

  // Handle Search Input
  const handleSearchChange = async (e) => {
    const val = e.target.value;
    setSearchTerm(val);
    if (val.trim().length > 0) {
      setIsSearching(true);
      try {
        const res = await stocksApi.search(val);
        setSearchResults(res);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    } else {
      setSearchResults([]);
    }
  };

  // Add stock to watchlist
  const handleAddStock = async (tickerToAdd) => {
    const ticker = (tickerToAdd || searchTerm).trim().toUpperCase();
    if (!ticker) return;

    setActionError('');
    setActionSuccess('');

    try {
      const added = await watchlistApi.add(ticker);
      setSearchTerm('');
      setSearchResults([]);
      setActionSuccess(`Added ${ticker} to your watchlist.`);
      
      // Fetch quote for the newly added stock
      const q = await stocksApi.getQuote(ticker, currentMarket);
      setQuotes((prev) => ({ ...prev, [ticker]: q }));
      setWatchlist((prev) => [added, ...prev]);

      setTimeout(() => setActionSuccess(''), 3000);
    } catch (err) {
      setActionError(err.message || `Failed to add ${ticker}.`);
      setTimeout(() => setActionError(''), 4000);
    }
  };

  // Remove stock from watchlist
  const handleRemoveStock = async (ticker) => {
    setActionError('');
    setActionSuccess('');
    try {
      await watchlistApi.remove(ticker);
      setWatchlist((prev) => prev.filter((item) => item.ticker !== ticker));
      setActionSuccess(`Removed ${ticker} from watchlist.`);
      setTimeout(() => setActionSuccess(''), 3000);
    } catch (err) {
      setActionError(err.message || `Failed to remove ${ticker}.`);
      setTimeout(() => setActionError(''), 4000);
    }
  };

  return (
    <div className="glass-panel rounded-3xl p-5 sm:p-7 shadow-xl shadow-[#8DB9F0]/10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-5 border-b border-[#E9E8F8]">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-[#E9E8F8] text-[#524398] border border-[#d7d4f2]">
              <Layers className="w-4 h-4" />
            </span>
            <h3 className="text-lg font-extrabold text-slate-900 tracking-tight">
              Watchlist & Ticker Intelligence
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Search stocks, monitor real-time prices, and dispatch autonomous research tasks.
          </p>
        </div>

        <button
          onClick={loadWatchlist}
          disabled={isLoading}
          className="flex items-center space-x-1.5 text-xs text-slate-600 hover:text-slate-900 bg-white/90 border border-[#E9E8F8] rounded-xl px-3 py-1.5 shadow-sm transition-all"
          title="Refresh Quotes"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-[#8DB9F0]' : ''}`} />
          <span className="font-semibold">Refresh</span>
        </button>
      </div>

      {/* Action alerts */}
      {actionError && (
        <div className="mt-4 p-3 rounded-2xl bg-rose-50 border border-rose-200 flex items-center space-x-2 text-xs text-rose-700">
          <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
          <span className="font-semibold">{actionError}</span>
        </div>
      )}

      {actionSuccess && (
        <div className="mt-4 p-3 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center space-x-2 text-xs text-emerald-700">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
          <span className="font-semibold">{actionSuccess}</span>
        </div>
      )}

      {/* Search Bar & Add Button */}
      <div className="mt-5 relative">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search ticker (e.g. RELIANCE, TCS, INFY, TATAMOTORS, AAPL)..."
              value={searchTerm}
              onChange={handleSearchChange}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddStock();
              }}
              className="w-full pl-10 pr-4 py-2.5 bg-white/90 border border-[#E9E8F8] rounded-2xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-[#8DB9F0] focus:ring-2 focus:ring-[#8DB9F0]/30 transition-all font-mono shadow-sm"
            />
          </div>
          <button
            onClick={() => handleAddStock()}
            disabled={!searchTerm.trim()}
            className="px-5 py-2.5 bg-[#8DB9F0] hover:bg-[#6ea6ec] disabled:opacity-40 text-slate-900 font-extrabold text-xs rounded-2xl shadow-md shadow-[#8DB9F0]/25 transition-all flex items-center space-x-1.5 shrink-0 glow-powder"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span className="hidden sm:inline">Add to Watchlist</span>
          </button>
        </div>

        {/* Autocomplete Dropdown */}
        {searchResults.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 z-30 bg-white border border-[#E9E8F8] rounded-2xl shadow-2xl overflow-hidden max-h-60 overflow-y-auto">
            {searchResults.map((stock) => (
              <div
                key={stock.ticker}
                onClick={() => handleAddStock(stock.ticker)}
                className="flex items-center justify-between p-3 hover:bg-[#E9E8F8]/50 cursor-pointer border-b border-[#E9E8F8] last:border-b-0 transition-colors"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-xs text-[#3575cb]">{stock.ticker}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#E9E8F8] text-[#524398]">{stock.market}</span>
                  </div>
                  <span className="text-xs text-slate-600 line-clamp-1">{stock.name}</span>
                </div>
                <button
                  type="button"
                  className="text-xs text-[#3575cb] font-bold flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-[#8DB9F0]/20 hover:bg-[#8DB9F0]/30"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Suggested Quick Add Chips */}
      <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
        <span className="text-[11px] font-mono font-semibold mr-1">Popular Equities:</span>
        {['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'TATAMOTORS', 'AAPL', 'NVDA'].map((sym) => (
          <button
            key={sym}
            onClick={() => handleAddStock(sym)}
            className="px-2.5 py-1 rounded-xl bg-white hover:bg-[#E9E8F8] border border-[#E9E8F8] hover:border-[#adcff6] font-mono text-[11px] text-slate-700 transition-colors shadow-sm font-semibold"
          >
            +{sym}
          </button>
        ))}
      </div>

      {/* Watchlist Cards */}
      <div className="mt-6">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-slate-500 font-mono flex items-center justify-center space-x-2">
            <RefreshCw className="w-4 h-4 animate-spin text-[#8DB9F0]" />
            <span>Loading watchlist from PostgreSQL database...</span>
          </div>
        ) : watchlist.length === 0 ? (
          <div className="py-12 text-center border-2 border-dashed border-[#E9E8F8] rounded-3xl bg-white/40">
            <p className="text-sm font-bold text-slate-700">Your watchlist is currently empty.</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Look up any stock above or select a popular ticker chip to begin tracking equities and running multi-agent tasks.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {watchlist.map((item) => {
              const q = quotes[item.ticker];
              const isPositive = q ? q.change >= 0 : true;

              return (
                <div
                  key={item.saved_stock_id}
                  className="p-4 rounded-3xl bg-white/90 border border-[#E9E8F8] hover:border-[#8DB9F0] transition-all flex items-center justify-between gap-4 group shadow-sm hover:shadow-md"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-black text-sm text-slate-900 group-hover:text-[#3575cb] transition-colors">
                        {item.ticker}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#E9E8F8] text-[#524398] font-bold">
                        {q?.market || currentMarket || 'NSE'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 truncate mt-0.5 font-medium">
                      {q?.name || `${item.ticker} Equity`}
                    </p>
                    <div className="mt-2 flex items-center space-x-2 font-mono">
                      <span className="text-sm font-extrabold text-slate-900">
                        {q?.currency || 'INR'} {q?.price ? q.price.toLocaleString() : '---'}
                      </span>
                      {q && (
                        <span className={`flex items-center text-xs font-bold ${isPositive ? 'text-emerald-600' : 'text-rose-600'}`}>
                          {isPositive ? <TrendingUp className="w-3 h-3 mr-0.5" /> : <TrendingDown className="w-3 h-3 mr-0.5" />}
                          {isPositive ? '+' : ''}{q.change_pct}%
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center space-x-2 shrink-0">
                    <button
                      onClick={() => onLaunchTask(item.ticker)}
                      className="px-3.5 py-2 bg-gradient-to-r from-[#F5B69E] to-[#ea9e80] hover:from-[#f0a68d] hover:to-[#df8b6b] text-slate-900 font-extrabold text-xs rounded-xl shadow-md shadow-[#F5B69E]/25 transition-all flex items-center space-x-1.5 glow-peach"
                      title="Launch Multi-Agent Research Task"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span className="hidden sm:inline">Research</span>
                    </button>
                    <button
                      onClick={() => handleRemoveStock(item.ticker)}
                      className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl border border-transparent hover:border-rose-200 transition-all"
                      title="Remove from watchlist"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
