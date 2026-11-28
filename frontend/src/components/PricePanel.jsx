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

// A flexible chart for the technical indicators: several lines, optional bars
// (used for the MACD histogram) and optional dashed guide lines (like RSI 30 / 70).
function IndicatorChart({ rows, lines, bars, guides, fixedRange, label }) {
  const w = 600, h = 170, pad = 6;
  const values = [];
  lines.forEach((l) => rows.forEach((r) => { if (r[l.key] != null) values.push(r[l.key]); }));
  if (bars) rows.forEach((r) => { if (r[bars.key] != null) values.push(r[bars.key]); });
  if (guides) guides.forEach((g) => values.push(g.value));
  const min = fixedRange ? fixedRange[0] : Math.min(...values);
  const max = fixedRange ? fixedRange[1] : Math.max(...values);
  const span = max - min || 1;
  const xOf = (i) => pad + (i / Math.max(rows.length - 1, 1)) * (w - 2 * pad);
  const yOf = (v) => h - pad - ((v - min) / span) * (h - 2 * pad);
  const barWidth = Math.max(((w - 2 * pad) / Math.max(rows.length, 1)) * 0.7, 1);

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="chart" role="img" aria-label={label}>
      {guides && guides.map((g) => (
        <g key={g.label}>
          <line
            x1={pad} x2={w - pad} y1={yOf(g.value)} y2={yOf(g.value)}
            stroke="#8c959f" strokeWidth="1" strokeDasharray="4 4"
          />
          <text x={w - pad - 2} y={yOf(g.value) - 3} fontSize="10" fill="#6e7781" textAnchor="end">
            {g.label}
          </text>
        </g>
      ))}
      {bars && rows.map((r, i) => {
        const v = r[bars.key];
        if (v == null) return null;
        const y0 = yOf(0), y1 = yOf(v);
        return (
          <rect
            key={r.date}
            x={xOf(i) - barWidth / 2}
            y={Math.min(y0, y1)}
            width={barWidth}
            height={Math.abs(y1 - y0)}
            fill={v >= 0 ? "#1a7f37" : "#cf222e"}
            opacity="0.45"
          />
        );
      })}
      {lines.map((l) => {
        const pts = rows
          .map((r, i) => (r[l.key] == null ? null : `${xOf(i).toFixed(1)},${yOf(r[l.key]).toFixed(1)}`))
          .filter(Boolean)
          .join(" ");
        return <polyline key={l.key} points={pts} fill="none" stroke={l.color} strokeWidth="2" />;
      })}
    </svg>
  );
}

function Legend({ items }) {
  return (
    <p className="muted">
      {items.map(([name, color]) => (
        <span key={name} style={{ marginRight: 14 }}>
          <span
            style={{ display: "inline-block", width: 10, height: 10, background: color, marginRight: 4 }}
          />
          {name}
        </span>
      ))}
    </p>
  );
}

// The rows of the peer comparison table: [key in the data, label shown on the page]
const PEER_ROWS = [
  ["revenue_growth_percent", "Revenue growth (%)"],
  ["operating_margin_percent", "Operating margin (%)"],
  ["net_margin_percent", "Net margin (%)"],
  ["roe_percent", "Return on equity (%)"],
  ["debt_to_equity", "Debt-to-equity"],
  ["pe_ratio", "P/E ratio"],
  ["pb_ratio", "P/B ratio"],
];

// The indicator table of the technical analysis: [key in the data, label shown on the page]
const INDICATOR_ROWS = [
  ["latest_close", "Latest close"],
  ["sma20", "20-day SMA"],
  ["sma50", "50-day SMA"],
  ["ema20", "20-day EMA"],
  ["rsi14", "RSI (14)"],
  ["macd", "MACD line"],
  ["macd_signal", "Signal line"],
  ["macd_histogram", "MACD histogram"],
];

const SIGNAL_COLORS = {
  bullish: "#1a7f37",
  bearish: "#cf222e",
  overbought: "#9a6700",
  oversold: "#9a6700",
  neutral: "#6e7781",
};

// Shows profile, price history (OHLCV), validation notes and the data source.
export default function PricePanel({ ticker, period, market, onClose, onError, onResearch }) {
  const [history, setHistory] = useState(null);
  const [profile, setProfile] = useState(null);
  const [financials, setFinancials] = useState(null);
  const [fundamental, setFundamental] = useState(null);
  const [fundamentalFailed, setFundamentalFailed] = useState(false);
  const [technical, setTechnical] = useState(null);
  const [technicalFailed, setTechnicalFailed] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setHistory(null);
    setProfile(null);
    setFinancials(null);
    setFundamental(null);
    setFundamentalFailed(false);
    setTechnical(null);
    setTechnicalFailed(false);
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
    api(`/stocks/${encodeURIComponent(ticker)}/financials`)
      .then((d) => !cancelled && setFinancials(d))
      .catch(() => {}); // financials are optional; prices are the main result
    api(`/stocks/${encodeURIComponent(ticker)}/fundamental-analysis`)
      .then((d) => !cancelled && setFundamental(d))
      .catch(() => !cancelled && setFundamentalFailed(true)); // optional; prices are the main result
    api(`/stocks/${encodeURIComponent(ticker)}/technical-analysis?period=6mo&market=${market}`)
      .then((d) => !cancelled && setTechnical(d))
      .catch(() => !cancelled && setTechnicalFailed(true)); // optional; prices are the main result
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker, period, market]);

  const rows = history ? history.rows : [];
  const last = rows[rows.length - 1];
  const first = rows[0];
  const change = last && first ? ((last.close - first.close) / first.close) * 100 : null;
  const v = history && history.validation;
  const peers = fundamental && fundamental.peer_comparison;
  const peerNames = peers && peers.metrics ? Object.keys(peers.metrics) : [];

  const chartRows = technical ? technical.chart_data : [];
  const trend = technical && technical.price_trend;
  const vol = technical && technical.volatility;
  const cond = technical && technical.technical_conditions;

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

      {financials && (
        <>
          <h4>Financial statements (annual)</h4>
          {Object.entries(financials.statements).map(([name, items]) => {
            const years = [...new Set(Object.values(items).flatMap((o) => Object.keys(o)))].sort().reverse();
            if (years.length === 0) return null;
            return (
              <div key={name}>
                <h5>{name.replace("_", " ")}</h5>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr><th>Item</th>{years.map((y) => <th key={y}>{y}</th>)}</tr>
                    </thead>
                    <tbody>
                      {Object.entries(items).map(([item, byYear]) => (
                        <tr key={item}>
                          <td>{item}</td>
                          {years.map((y) => (
                            <td key={y}>
                              {byYear[y] == null ? "-" : byYear[y].toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
          <p className="muted">
            Source: <a href={financials.source.url} target="_blank" rel="noreferrer">{financials.source.name}</a>
            {financials.from_cache ? " (served from cache)" : ""}.
          </p>
        </>
      )}

      {!fundamental && !fundamentalFailed && history && (
        <p className="muted">Calculating fundamental analysis (this can take a few seconds)...</p>
      )}
      {fundamentalFailed && (
        <p className="muted">Fundamental analysis could not be loaded for this stock.</p>
      )}

      {fundamental && (
        <>
          <h4>Fundamental analysis</h4>

          {fundamental.historical_comparison && (
            <>
              <h5>Trend: oldest year compared with latest year</h5>
              <ul>
                {fundamental.historical_comparison.summary.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </>
          )}

          {fundamental.valuation_analysis && (
            <>
              <h5>Valuation</h5>
              <p className="muted">
                P/E ratio: {fundamental.valuation_analysis.pe_ratio} · P/B ratio:{" "}
                {fundamental.valuation_analysis.pb_ratio}
              </p>
            </>
          )}

          {peerNames.length > 0 && (
            <>
              <h5>Peer comparison (latest financial year)</h5>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Measure</th>{peerNames.map((n) => <th key={n}>{n}</th>)}</tr>
                  </thead>
                  <tbody>
                    {PEER_ROWS.map(([key, label]) => (
                      <tr key={key}>
                        <td>{label}</td>
                        {peerNames.map((n) => (
                          <td key={n}>{peers.metrics[n][key]}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <ul>
                {peers.versus_peer_average.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              <p className="muted">{peers.note}</p>
            </>
          )}
          {peers && peerNames.length === 0 && peers.note && (
            <p className="muted">{peers.note}</p>
          )}

          <h5>Data quality: {fundamental.data_quality_status}</h5>
          {fundamental.data_issues.length > 0 && (
            <ul>
              {fundamental.data_issues.map((issue) => (
                <li key={issue}>{issue}</li>
              ))}
            </ul>
          )}
          <p className="muted">
            Source: {fundamental.source && fundamental.source.name}. These are calculated
            numbers, not investment advice.
          </p>
        </>
      )}

      {!technical && !technicalFailed && history && (
        <p className="muted">Calculating technical analysis (this can take a few seconds)...</p>
      )}
      {technicalFailed && (
        <p className="muted">Technical analysis could not be loaded for this stock.</p>
      )}

      {technical && (
        <>
          <h4>Technical analysis</h4>
          <p>
            Overall signal:{" "}
            <strong>{cond ? cond.overall_signal : "Not available"}</strong>
            {cond && (
              <span className="muted">
                {" "}({cond.bullish_count} bullish, {cond.bearish_count} bearish out of 3 trend rules)
              </span>
            )}
          </p>

          <h5>Indicators (latest day)</h5>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Indicator</th><th>Value</th></tr>
              </thead>
              <tbody>
                {INDICATOR_ROWS.map(([key, label]) => (
                  <tr key={key}>
                    <td>{label}</td>
                    <td>{technical.indicators[key]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {trend && trend.trend !== "Not enough data" && (
            <>
              <h5>Price trend: {trend.trend}</h5>
              <ul>
                <li>Change over the last month: {trend.change_1m_pct}%</li>
                <li>Change over the last 3 months: {trend.change_3m_pct}%</li>
                <li>Change over the whole {technical.period} period: {trend.change_period_pct}%</li>
              </ul>
            </>
          )}

          {vol && vol.volatility_label !== "Not enough data" && (
            <>
              <h5>Historical volatility: {vol.volatility_label}</h5>
              <p className="muted">
                Last 30 trading days: {vol.volatility_30d_pct}% a year · Whole period:{" "}
                {vol.volatility_period_pct}% a year
              </p>
            </>
          )}

          {cond && (
            <>
              <h5>Technical conditions</h5>
              <ul>
                {cond.conditions.map((c) => (
                  <li key={c.name}>
                    <strong>{c.name}:</strong>{" "}
                    <span style={{ color: SIGNAL_COLORS[c.signal] || "#6e7781", fontWeight: 600 }}>
                      {c.signal}
                    </span>
                    . {c.explanation}
                  </li>
                ))}
              </ul>
            </>
          )}

          {chartRows.length > 0 && (
            <>
              <h5>Price with moving averages</h5>
              <IndicatorChart
                rows={chartRows}
                label="Closing price with SMA 20, SMA 50 and EMA 20"
                lines={[
                  { key: "close", color: "#1f6feb" },
                  { key: "sma20", color: "#e36209" },
                  { key: "sma50", color: "#8250df" },
                  { key: "ema20", color: "#1a7f37" },
                ]}
              />
              <Legend
                items={[
                  ["Close", "#1f6feb"],
                  ["SMA 20", "#e36209"],
                  ["SMA 50", "#8250df"],
                  ["EMA 20", "#1a7f37"],
                ]}
              />

              <h5>RSI (14)</h5>
              <IndicatorChart
                rows={chartRows}
                label="Relative Strength Index"
                fixedRange={[0, 100]}
                lines={[{ key: "rsi14", color: "#8250df" }]}
                guides={[
                  { value: 70, label: "70 overbought" },
                  { value: 30, label: "30 oversold" },
                ]}
              />

              <h5>MACD</h5>
              <IndicatorChart
                rows={chartRows}
                label="MACD, signal line and histogram"
                lines={[
                  { key: "macd", color: "#1f6feb" },
                  { key: "signal", color: "#e36209" },
                ]}
                bars={{ key: "histogram" }}
                guides={[{ value: 0, label: "0" }]}
              />
              <Legend
                items={[
                  ["MACD line", "#1f6feb"],
                  ["Signal line", "#e36209"],
                  ["Histogram", "#1a7f37"],
                ]}
              />
              <p className="muted">
                Charts show {chartRows[0].date} to {chartRows[chartRows.length - 1].date}. Lines start
                later where an indicator needs more days of prices first.
              </p>
            </>
          )}

          <p className="muted">
            Source: {technical.source}, retrieved {new Date(technical.retrieved_at).toLocaleString()}.{" "}
            {technical.disclaimer}
          </p>
        </>
      )}
    </section>
  );
}
