import { useState } from "react";
import { api } from "../api.js";

// Search Yahoo Finance by company name or ticker.
export default function StockSearch({ market, onAdd, onView, onResearch, onError }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [busy, setBusy] = useState(false);

  async function search(e) {
    e.preventDefault();
    if (query.trim().length < 2) return;
    setBusy(true);
    try {
      const data = await api(`/stocks/search?q=${encodeURIComponent(query.trim())}&market=${market}`);
      setResults(data);
    } catch (err) {
      onError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h3>Stock search</h3>
      <p className="muted">
        Search by company name or ticker. Results for your preferred market ({market}) are shown first.
      </p>
      <form className="inline" onSubmit={search}>
        <input placeholder="e.g. Tata Consultancy, RELIANCE or Apple" value={query}
               onChange={(e) => setQuery(e.target.value)} maxLength={60} />
        <button className="btn" disabled={busy}>{busy ? "Searching..." : "Search"}</button>
      </form>

      {results && results.length === 0 && <p className="muted">No matching stocks found.</p>}
      {results && results.length > 0 && (
        <ul className="list">
          {results.map((r) => (
            <li key={r.ticker}>
              <span>
                <strong>{r.ticker}</strong> {r.name}
                <span className="tag">{r.market}</span>
              </span>
              <span className="row-actions">
                <button className="link-btn link-blue" onClick={() => onView(r.ticker)}>View prices</button>
                <button className="link-btn link-blue" onClick={() => onAdd(r.ticker)}>Add to watchlist</button>
                <button className="link-btn link-blue" onClick={() => onResearch(r.ticker)}>Start research</button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
