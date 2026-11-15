import { useEffect, useState } from "react";
import { api, MARKETS } from "../api.js";

// Search a company by name or ticker; shows results with one action button each.
export default function StockSearch({ defaultMarket, actionLabel, onSelect, busyTicker }) {
  const [market, setMarket] = useState(defaultMarket);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => setMarket(defaultMarket), [defaultMarket]);

  // debounce so we don't call the API on every keystroke
  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setResults([]);
      return;
    }
    const t = setTimeout(() => {
      api
        .searchStocks(q, market)
        .then((r) => {
          setResults(r);
          setError("");
        })
        .catch((e) => setError(e.message));
    }, 300);
    return () => clearTimeout(t);
  }, [query, market]);

  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          className="input"
          placeholder="Search by company name or ticker (e.g. AAPL, TCS)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search stocks"
        />
        <select className="input sm:w-40" value={market} onChange={(e) => setMarket(e.target.value)} aria-label="Market">
          {MARKETS.map((m) => (
            <option key={m.value} value={m.value}>{m.value}</option>
          ))}
        </select>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {query.trim() && !error && results.length === 0 && (
        <p className="text-sm text-slate-500">No matching stocks on {market}.</p>
      )}

      {results.length > 0 && (
        <ul className="divide-y divide-slate-100 rounded-md border border-slate-200">
          {results.map((s) => (
            <li key={`${s.market}-${s.ticker}`} className="flex items-center justify-between gap-3 p-3">
              <div>
                <p className="text-sm font-medium">{s.name}</p>
                <p className="text-xs text-slate-500">{s.ticker} · {s.market} · data symbol {s.provider_symbol} · {s.source === "yahoo" ? "Yahoo Finance" : "built-in list"}</p>
              </div>
              <button className="btn-secondary" disabled={busyTicker === s.ticker} onClick={() => onSelect(s)}>
                {actionLabel}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
