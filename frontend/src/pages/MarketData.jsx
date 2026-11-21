import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import Logo from "../components/Logo";
import { formatDate } from "../components/StatusBadge";
import { MARKETS, PERIODS } from "../constants";

const TABS = ["Prices", "Profile", "Financials", "Data log"];
const fmt = (n, d = 2) => (n == null ? "—" : n.toLocaleString(undefined, { maximumFractionDigits: d }));
const compact = (n) => (n == null ? "—" : Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 2 }).format(n));

function Provenance({ p }) {
  if (!p) return null;
  return (
    <p className="muted prov">
      Source: <strong>{p.source}</strong>
      {p.retrieved_at ? <> · retrieved {formatDate(p.retrieved_at)}{p.from_cache ? " (from today's cache)" : ""}</> : " · retrieval time not recorded"}
    </p>
  );
}

function LineChart({ rows }) {
  const pts = rows.filter((r) => r.close != null);
  if (pts.length < 2) return null;
  const W = 760, H = 220, pad = 8;
  const min = Math.min(...pts.map((r) => r.close)), max = Math.max(...pts.map((r) => r.close));
  const x = (i) => pad + (i / (pts.length - 1)) * (W - 2 * pad);
  const y = (v) => H - pad - ((v - min) / (max - min || 1)) * (H - 2 * pad);
  const path = pts.map((r, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(r.close).toFixed(1)}`).join(" ");
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Closing price from ${pts[0].date} to ${pts.at(-1).date}`}>
      <path d={path} fill="none" stroke="var(--accent)" strokeWidth="2" />
      {pts.map((r, i) => r.flag && <circle key={r.date} cx={x(i)} cy={y(r.close)} r="4" fill="var(--danger)"><title>{r.date}: {r.flag}</title></circle>)}
      <text x={pad} y="14" className="chart-label">{fmt(max)}</text>
      <text x={pad} y={H - 12} className="chart-label">{fmt(min)}</text>
    </svg>
  );
}

function Quality({ q }) {
  const failed = q.checks.filter((c) => !c.passed);
  const label = { ok: "All checks passed", warnings: "Passed with warnings", errors: "Problems found" }[q.status];
  return (
    <div className="quality">
      <p><span className={`badge q-${q.status}`}>{label}</span> <span className="muted">{q.rows} rows · {q.first_date} → {q.last_date}</span></p>
      <details open={failed.length > 0}>
        <summary>Data-quality checks ({q.checks.length - failed.length}/{q.checks.length} passed)</summary>
        <ul className="checks">
          {q.checks.map((c) => (
            <li key={c.id} className={c.passed ? "pass" : c.severity}>
              <strong>{c.passed ? "✓" : c.severity === "error" ? "✗" : "!"} {c.label}</strong>
              <span className="muted"> — {c.detail}{c.examples.length ? ` e.g. ${c.examples.join(", ")}` : ""}</span>
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}

function Prices({ market, ticker }) {
  const [period, setPeriod] = useState("6 months");
  const [state, setState] = useState({ loading: true });
  useEffect(() => {
    let off = false;
    setState({ loading: true });
    api(`/market/${market}/${ticker}/prices?period=${encodeURIComponent(period)}`)
      .then((d) => !off && setState({ data: d }))
      .catch((e) => !off && setState({ error: e.message }));
    return () => { off = true; };
  }, [market, ticker, period]);

  const recent = useMemo(() => (state.data ? [...state.data.rows].reverse().slice(0, 60) : []), [state.data]);
  return (
    <div>
      <div className="search-row">
        <select aria-label="Period" value={period} onChange={(e) => setPeriod(e.target.value)}>
          {PERIODS.map((p) => <option key={p}>{p}</option>)}
        </select>
      </div>
      {state.loading && <p className="muted">Loading prices…</p>}
      {state.error && <div className="alert alert-error" role="alert">{state.error}</div>}
      {state.data && (
        <>
          <Provenance p={state.data.provenance} />
          <LineChart rows={state.data.rows} />
          <Quality q={state.data.quality} />
          <h3>Daily OHLCV <span className="muted">(latest {recent.length} of {state.data.rows.length} days)</span></h3>
          <div className="table-wrap tall">
            <table className="table num">
              <thead><tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th></tr></thead>
              <tbody>
                {recent.map((r) => (
                  <tr key={r.date} className={r.flag ? "row-flag" : ""} title={r.flag || undefined}>
                    <td>{r.date}</td><td>{fmt(r.open)}</td><td>{fmt(r.high)}</td><td>{fmt(r.low)}</td><td>{fmt(r.close)}</td><td>{fmt(r.volume, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function useLoad(path) {
  const [s, setS] = useState({ loading: true });
  useEffect(() => {
    let off = false;
    setS({ loading: true });
    api(path).then((d) => !off && setS({ data: d })).catch((e) => !off && setS({ error: e.message }));
    return () => { off = true; };
  }, [path]);
  return s;
}

function Status({ s }) {
  if (s.loading) return <p className="muted">Loading…</p>;
  if (s.error) return <div className="alert alert-error" role="alert">{s.error}</div>;
  return null;
}

function Notes({ notes }) {
  return notes?.length ? <ul className="notes muted">{notes.map((n) => <li key={n}>{n}</li>)}</ul> : null;
}

function Profile({ market, ticker }) {
  const s = useLoad(`/market/${market}/${ticker}/profile`);
  const p = s.data?.profile;
  return (
    <div>
      <Status s={s} />
      {p && (
        <>
          <Provenance p={s.data.provenance} />
          <dl className="kv">
            {[["Name", p.name], ["Exchange", p.exchange], ["Sector", p.sector], ["Industry", p.industry],
              ["Country", p.country], ["City", p.city], ["Employees", p.employees != null ? fmt(p.employees, 0) : null],
              ["Market cap", p.market_cap != null ? `${compact(p.market_cap)} ${p.currency ?? ""}` : null],
              ["Website", p.website]].map(([k, v]) => (
              <div key={k} style={{ display: "contents" }}><dt>{k}</dt><dd>{v ?? "—"}</dd></div>
            ))}
          </dl>
          {p.summary && <p className="summary">{p.summary}</p>}
          <Notes notes={s.data.notes} />
        </>
      )}
    </div>
  );
}

const STATEMENTS = [["income_statement", "Income statement"], ["balance_sheet", "Balance sheet"], ["cash_flow", "Cash flow"]];

function Financials({ market, ticker }) {
  const s = useLoad(`/market/${market}/${ticker}/financials`);
  return (
    <div>
      <Status s={s} />
      {s.data && (
        <>
          <Provenance p={s.data.provenance} />
          {STATEMENTS.filter(([k]) => s.data.statements[k]).map(([k, title]) => {
            const st = s.data.statements[k];
            return (
              <div key={k}>
                <h3>{title} <span className="muted">(annual)</span></h3>
                <div className="table-wrap">
                  <table className="table num">
                    <thead><tr><th>Item</th>{st.periods.map((p) => <th key={p}>{p}</th>)}</tr></thead>
                    <tbody>{st.rows.map((r) => <tr key={r.item}><td>{r.item}</td>{r.values.map((v, i) => <td key={i}>{compact(v)}</td>)}</tr>)}</tbody>
                  </table>
                </div>
              </div>
            );
          })}
          <Notes notes={s.data.notes} />
        </>
      )}
    </div>
  );
}

function DataLog() {
  const s = useLoad("/market/retrievals");
  return (
    <div>
      <Status s={s} />
      {s.data && (s.data.length === 0 ? <p className="muted">Nothing retrieved yet. Open a stock to start the log.</p> : (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Stock</th><th>Dataset</th><th>Source</th><th>Retrieved</th><th>Rows</th><th>Quality</th></tr></thead>
            <tbody>
              {s.data.map((r) => (
                <tr key={r.id}>
                  <td>{r.ticker} <span className="muted">{r.market}</span></td><td>{r.dataset}</td><td>{r.source}</td>
                  <td>{r.retrieved_at ? formatDate(r.retrieved_at) : "—"}{r.from_cache ? " (cache)" : ""}</td>
                  <td>{r.rows ?? "—"}</td><td>{r.quality_status ? <span className={`badge q-${r.quality_status}`}>{r.quality_status}</span> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

export default function MarketData() {
  const { user } = useAuth();
  const [q, setQ] = useState("");
  const [market, setMarket] = useState("ALL");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [selected, setSelected] = useState(null);
  const [tab, setTab] = useState("Prices");

  useEffect(() => {
    const term = q.trim();
    if (!term) { setResults([]); return; }
    let off = false;
    const t = setTimeout(async () => {
      setSearching(true); setSearchError("");
      try {
        const params = new URLSearchParams({ q: term });
        if (market !== "ALL") params.set("market", market);
        const d = await api(`/market/search?${params}`);
        if (!off) setResults(d);
      } catch (e) {
        if (!off) setSearchError(e.message);
      } finally {
        if (!off) setSearching(false);
      }
    }, 300);
    return () => { off = true; clearTimeout(t); };
  }, [q, market]);

  return (
    <div className="dash">
      <header className="nav">
        <Logo />
        <div className="nav-actions">
          <Link className="btn btn-ghost" to="/dashboard">← Dashboard</Link>
          <span className="nav-name">{user.full_name}</span>
        </div>
      </header>
      <main className="dash-main">
        <section className="card">
          <h1 className="h-md">Stock search &amp; market data</h1>
          <p className="muted">Search by company name or ticker. Prices, profile and financials show their source and retrieval time.</p>
          <div className="search-row">
            <input aria-label="Search companies" placeholder="e.g. Reliance, TCS, AAPL" value={q} onChange={(e) => setQ(e.target.value)} />
            <select aria-label="Market" value={market} onChange={(e) => setMarket(e.target.value)}>
              <option value="ALL">All markets</option>
              {MARKETS.map((m) => <option key={m.value} value={m.value}>{m.value}</option>)}
            </select>
          </div>
          {searching && <p className="muted">Searching…</p>}
          {searchError && <div className="alert alert-error" role="alert">{searchError}</div>}
          {!searching && q.trim() && results.length === 0 && !searchError && <p className="muted">No companies found.</p>}
          <ul className="stock-list">
            {results.map((s) => (
              <li key={`${s.market}:${s.ticker}`}>
                <span><strong>{s.company_name}</strong> <span className="muted">{s.ticker} · {s.market}</span></span>
                <button className="btn btn-ghost btn-sm" onClick={() => { setSelected(s); setTab("Prices"); }}>View data</button>
              </li>
            ))}
          </ul>
        </section>

        {selected && (
          <section className="card">
            <h2 className="h-md">{selected.company_name} <span className="muted">{selected.ticker} · {selected.market}</span></h2>
            <div className="tabs" role="tablist">
              {TABS.map((t) => <button key={t} role="tab" aria-selected={tab === t} className={`tab${tab === t ? " on" : ""}`} onClick={() => setTab(t)}>{t}</button>)}
            </div>
            {tab === "Prices" && <Prices market={selected.market} ticker={selected.ticker} />}
            {tab === "Profile" && <Profile market={selected.market} ticker={selected.ticker} />}
            {tab === "Financials" && <Financials market={selected.market} ticker={selected.ticker} />}
            {tab === "Data log" && <DataLog />}
          </section>
        )}
      </main>
    </div>
  );
}
