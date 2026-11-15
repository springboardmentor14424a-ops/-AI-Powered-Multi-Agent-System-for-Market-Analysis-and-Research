import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import StockSearch from "./StockSearch.jsx";

export default function Watchlist({ prefs, onStartResearch }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(() => {
    api
      .getWatchlist()
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  async function add(stock) {
    setError("");
    setNotice("");
    try {
      await api.addToWatchlist({ ticker: stock.ticker, market: stock.market });
      setNotice(`${stock.ticker} added to your watchlist.`);
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function research(item) {
    setError("");
    setNotice("");
    try {
      await onStartResearch(item.ticker, item.market);
    } catch (e) {
      setError(e.message);
    }
  }

  async function remove(item) {
    setError("");
    setNotice("");
    try {
      await api.removeFromWatchlist(item.saved_stock_id);
      setItems((prev) => prev.filter((i) => i.saved_stock_id !== item.saved_stock_id));
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="space-y-6">
      <section className="card space-y-3">
        <h2 className="text-lg font-semibold">Add to watchlist</h2>
        <StockSearch defaultMarket={prefs?.market ?? "NASDAQ"} actionLabel="Add to Watchlist" onSelect={add} />
      </section>

      <section className="card">
        <h2 className="mb-3 text-lg font-semibold">Saved stocks</h2>
        {error && <p role="alert" className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {notice && <p role="status" className="mb-3 rounded-md bg-green-50 p-3 text-sm text-green-700">{notice}</p>}
        {loading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500">Your watchlist is empty.</p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {items.map((i) => (
              <li key={i.saved_stock_id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div>
                  <p className="text-sm font-medium">{i.company_name}</p>
                  <p className="text-xs text-slate-500">{i.ticker} · {i.market}</p>
                </div>
                <div className="flex gap-2">
                  <button className="btn-secondary" onClick={() => research(i)}>Research</button>
                  <button className="btn-secondary text-red-700" onClick={() => remove(i)}>Remove</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
