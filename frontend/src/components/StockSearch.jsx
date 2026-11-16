import { useState, useEffect, useCallback } from 'react';
import { Search } from 'lucide-react';
import api from '../api/axios';

const StockSearch = ({ onSelectStock }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const searchStocks = useCallback(async (q) => {
    if (!q || q.length < 1) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.get(`/stocks/search?q=${encodeURIComponent(q)}`);
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      searchStocks(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query, searchStocks]);

  return (
    <div className="w-full">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search stocks (e.g. AAPL, MSFT, TSLA)..."
          className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        )}
      </div>

      {results.length > 0 && (
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {results.map((stock, idx) => (
            <button
              key={`${stock.symbol}-${idx}`}
              onClick={() => {
                onSelectStock(stock.symbol);
                setQuery('');
                setResults([]);
              }}
              className="text-left p-4 bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl hover:bg-white/10 hover:border-blue-500/30 transition-all group"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white group-hover:text-blue-400 transition-colors">
                  {stock.symbol}
                </span>
                <span className="text-xs text-slate-500 bg-white/5 px-2 py-0.5 rounded">
                  {stock.exchange || stock.exchDisp || 'N/A'}
                </span>
              </div>
              <p className="text-sm text-slate-400 mt-1 truncate">{stock.name || stock.shortname || stock.longname || ''}</p>
              {stock.quoteType && (
                <span className="text-xs text-slate-500 mt-1 inline-block">{stock.quoteType}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default StockSearch;
