import { useEffect, useState } from "react";
import { api } from "../api.js";

function LineChart({ rows }) {
  const w = 600, h = 160, pad = 6;
  const closes = rows.map((r) => r.close);
  const min = Math.min(...closes), max = Math.max(...closes);
  const span = max - min || 1;
  const pts = closes
    .map((c, i) => {
      const x = pad + (i / Math.max(closes.length - 1, 1)) * (w - 2 * pad);
      const y = h - pad - ((c - min) / span) * (h - 2 * pad);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="chart" role="img" aria-label="Closing price chart">
      <polyline points={pts} fill="none" stroke="#1f6feb" strokeWidth="2" />
    </svg>
  );
}

// Shows profile, price history (OHLCV), validation notes and the data source.
export default function PricePanel({ ticker, period, market, onClose, onError, onResearch }) {
  const [history, setHistory] = useState(null);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setHistory(null);
    setProfile(null);
    setError("");
    const q = `?period=${period}&market=${market}`;
    api(`/stocks/${encodeURIComponent(ticker)}/history${q}`)
      .then((d) => !cancelled && setHistory(d))
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 401) onError(err);
        else setError(err.message);
      });
    api(`/stocks/${encodeURIComponent(ticker)}/profile?market=${market}`)
      .then((d) => !cancelled && setProfile(d))
      .catch(() => {}); // the profile is optional; prices are the main result
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker, period, market]);

  const rows = history ? history.rows : [];
  const last = rows[rows.length - 1];
  const first = rows[0];
  const change = last && first ? ((last.close - first.close) / first.close) * 100 : null;
  const v = history && history.validation;

  return (
    <section className="card">
      <div className="panel-head">
        <h3>{profile ? `${profile.name} (${ticker})` : ticker}</h3>
        <span className="row-actions">
          <button className="btn" onClick={() => onResearch(ticker)}>Start research</button>
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
        </span>
      </div>

      {!history && !error && <p className="muted">Fetching data from Yahoo Finance...</p>}
      {error && <div className="alert alert-error">{error}</div>}

      {profile && (profile.sector || profile.industry) && (
        <p className="muted">
          {[profile.sector, profile.industry, profile.country, profile.currency].filter(Boolean).join(" · ")}
        </p>
      )}
      {profile && profile.summary && <p className="summary">{profile.summary}</p>}

      {history && (
        <>
          <div className="stats small">
            <div><span className="stat">{last.close}</span> Latest close ({last.date})</div>
            <div><span className="stat">{Math.max(...rows.map((r) => r.high))}</span> Period high</div>
            <div><span className="stat">{Math.min(...rows.map((r) => r.low))}</span> Period low</div>
            <div>
              <span className={`stat ${change >= 0 ? "up" : "down"}`}>{change.toFixed(2)}%</span>
              Change over {period}
            </div>
          </div>

          <LineChart rows={rows} />

          <h4>Latest 10 trading days (OHLCV)</h4>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th></tr>
              </thead>
              <tbody>
                {rows.slice(-10).reverse().map((r) => (
                  <tr key={r.date}>
                    <td>{r.date}</td><td>{r.open}</td><td>{r.high}</td><td>{r.low}</td>
                    <td>{r.close}</td><td>{r.volume.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h4>Data checks</h4>
          <p className="muted">
            {v.rows_received} rows received, {v.rows_kept} kept ({v.first_date} to {v.last_date}).
            Duplicates removed: {v.duplicate_dates_removed}. Rows with missing prices removed:{" "}
            {v.rows_with_missing_prices_removed}. Inconsistent rows removed: {v.inconsistent_rows_removed}.
          </p>
          <p className="muted">
            Source: <a href={history.source.url} target="_blank" rel="noreferrer">{history.source.name}</a>,
            retrieved {new Date(history.source.retrieved_at).toLocaleString()}.
          </p>
        </>
      )}
    </section>
  );
}
