import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { MARKETS } from "../constants";

export default function Watchlist({ items, preferredMarket, analysisPeriod, onChanged, onResearch }) {
  const [q, setQ] = useState("");
  const [market, setMarket] = useState(preferredMarket);
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(null); // key of the row being changed

  useEffect(() => setMarket(preferredMarket), [preferredMarket]);

  // Debounced search; `cancelled` drops out-of-date responses.
  useEffect(() => {
    const term = q.trim();
    if (!term) {
      setResults([]);
      return;
    }
    let cancelled = false;
    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const params = new URLSearchParams({ q: term });
        if (market !== "ALL") params.set("market", market);
        const data = await api(`/stocks/search?${params}`);
        if (!cancelled) setResults(data);
      } catch (e) {
        if (!cancelled && e.status !== 401) setMsg({ type: "error", text: e.message });
      } finally {
        if (!cancelled) setSearching(false);
      }
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [q, market]);

  const saved = new Set(items.map((i) => `${i.market}:${i.ticker}`));

  const run = async (key, action, successText) => {
    setBusy(key);
    setMsg(null);
    try {
      await action();
      if (successText) setMsg({ type: "success", text: successText });
    } catch (err) {
      if (!(err instanceof ApiError)) throw err;
      setMsg({ type: "error", text: err.message });
    } finally {
      setBusy(null);
    }
  };

  const add = (s) =>
    run(`add:${s.market}:${s.ticker}`, async () => {
      await api("/watchlist", { method: "POST", body: { ticker: s.ticker, market: s.market } });
      await onChanged();
    }, `${s.company_name} added to your watchlist.`);

  const remove = (item) =>
    run(`rm:${item.id}`, async () => {
      await api(`/watchlist/${item.id}`, { method: "DELETE" });
      await onChanged();
    }, `${item.company_name} removed.`);

  const research = (item) =>
    run(`go:${item.id}`, () => onResearch(item), `Research started for ${item.company_name} (${analysisPeriod}). See the history below.`);

  return (
    <div>
      <h2>Watchlist</h2>
      <p className="muted small">Search for a company, save it, and start research in one click.</p>

      {msg && (
        <div className={`alert ${msg.type === "error" ? "alert-error" : "alert-success"}`} role={msg.type === "error" ? "alert" : "status"}>
          {msg.text}
        </div>
      )}

      <div className="watch-cols">
        <div>
          <h3>Find a stock</h3>
          <div className="search-row">
            <input
              type="search"
              aria-label="Search by company name or ticker"
              placeholder="Company name or ticker, e.g. Reliance, TCS, AAPL"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
            <select aria-label="Market to search" value={market} onChange={(e) => setMarket(e.target.value)}>
              {MARKETS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.value}
                </option>
              ))}
              <option value="ALL">All markets</option>
            </select>
          </div>
          <ul className="stock-list">
            {results.map((s) => {
              const isSaved = saved.has(`${s.market}:${s.ticker}`);
              const key = `add:${s.market}:${s.ticker}`;
              return (
                <li key={`${s.market}:${s.ticker}`}>
                  <div>
                    <strong>{s.company_name}</strong>
                    <div className="muted small">
                      {s.ticker} · {s.market}
                    </div>
                  </div>
                  <button className="btn btn-ghost btn-sm" onClick={() => add(s)} disabled={isSaved || busy === key}>
                    {isSaved ? "Saved" : "Add to watchlist"}
                  </button>
                </li>
              );
            })}
          </ul>
          {q.trim() && !searching && results.length === 0 && (
            <p className="muted small">No matches in the supported list for this market.</p>
          )}
        </div>

        <div>
          <h3>
            Your saved stocks <span className="muted small">({items.length})</span>
          </h3>
          {items.length === 0 ? (
            <p className="muted small">Nothing saved yet. Search on the left and add a stock.</p>
          ) : (
            <ul className="stock-list">
              {items.map((i) => (
                <li key={i.id}>
                  <div>
                    <strong>{i.company_name}</strong>
                    <div className="muted small">
                      {i.ticker} · {i.market}
                    </div>
                  </div>
                  <div className="row-actions">
                    <button className="btn btn-primary btn-sm" onClick={() => research(i)} disabled={busy === `go:${i.id}`}>
                      {busy === `go:${i.id}` ? "Starting…" : "Research"}
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => remove(i)} disabled={busy === `rm:${i.id}`} aria-label={`Remove ${i.company_name}`}>
                      Remove
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
