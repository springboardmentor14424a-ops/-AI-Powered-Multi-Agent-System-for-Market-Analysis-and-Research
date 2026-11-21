import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { formatDate } from "./StatusBadge";

const W = 800, PAD_L = 56, PAD_R = 12;
const COLORS = { close: "#34d399", sma20: "#60a5fa", sma50: "#fbbf24", sma200: "#c084fc", up: "#34d399", down: "#f87171" };
const fmt = (n, d = 2) => (n == null ? "—" : (Math.abs(n) < 1e-9 ? 0 : n).toLocaleString(undefined, { maximumFractionDigits: d }));
const compact = (n) => (n == null ? "—" : Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(n));
const pct = (n) => (n == null ? "—" : `${n >= 0 ? "+" : ""}${(n * 100).toFixed(2)}%`);

function niceTicks(min, max, count = 4) {
  const span = max - min || 1;
  const step = Math.pow(10, Math.floor(Math.log10(span / count)));
  const err = span / count / step;
  const mult = err >= 5 ? 10 : err >= 2 ? 5 : err >= 1 ? 2 : 1;
  const s = step * mult;
  const out = [];
  for (let v = Math.ceil(min / s) * s; v <= max + 1e-9; v += s) out.push(v);
  return out;
}

/** One chart panel. `series` are line series; `bars` are optional vertical bars. All share the x positions. */
function Panel({ rows, height, series = [], bars, hover, setHover, bands = [], yFixed, label, format = fmt }) {
  const n = rows.length;
  const x = (i) => PAD_L + (i / Math.max(n - 1, 1)) * (W - PAD_L - PAD_R);
  const vals = [
    ...series.flatMap((s) => rows.map((r) => r[s.key])),
    ...(bars ? rows.map((r) => r[bars.key]) : []),
    ...bands,
  ].filter((v) => v != null);
  let lo = yFixed ? yFixed[0] : Math.min(...vals), hi = yFixed ? yFixed[1] : Math.max(...vals);
  if (bars && !yFixed) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
  if (!yFixed) { const m = (hi - lo) * 0.06 || 1; if (!(bars && lo === 0)) lo -= m; hi += m; }
  const top = 8, bot = height - 18;
  const y = (v) => bot - ((v - lo) / (hi - lo || 1)) * (bot - top);
  const ticks = niceTicks(lo, hi, height > 150 ? 4 : 2);
  const xTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round(f * (n - 1)));
  const bw = Math.max(1, (W - PAD_L - PAD_R) / n - 1);

  const onMove = (e) => {
    const box = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - box.left) / box.width) * W;
    setHover(Math.min(n - 1, Math.max(0, Math.round(((px - PAD_L) / (W - PAD_L - PAD_R)) * (n - 1)))));
  };

  return (
    <svg className="chart" viewBox={`0 0 ${W} ${height}`} role="img" aria-label={label} onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
      {ticks.map((t) => (
        <g key={t}>
          <line x1={PAD_L} x2={W - PAD_R} y1={y(t)} y2={y(t)} className="grid" />
          <text x={PAD_L - 6} y={y(t) + 4} textAnchor="end" className="chart-label">{format(t)}</text>
        </g>
      ))}
      {bands.map((b) => <line key={b} x1={PAD_L} x2={W - PAD_R} y1={y(b)} y2={y(b)} className="band" />)}
      {bars && rows.map((r, i) => r[bars.key] != null && (
        <rect key={i} x={x(i) - bw / 2} width={bw} y={Math.min(y(r[bars.key]), y(0))} height={Math.abs(y(r[bars.key]) - y(0))}
          fill={bars.color ? bars.color(r, i) : COLORS.close} opacity="0.75" />
      ))}
      {series.map((s) => {
        let d = "", pen = false;
        rows.forEach((r, i) => {
          if (r[s.key] == null) { pen = false; return; }
          d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(r[s.key]).toFixed(1)} `;
          pen = true;
        });
        return <path key={s.key} d={d} fill="none" stroke={s.color} strokeWidth={s.width ?? 1.6} strokeDasharray={s.dash} />;
      })}
      {xTicks.map((i) => (
        <text key={i} x={x(i)} y={height - 4} textAnchor={i === 0 ? "start" : i === n - 1 ? "end" : "middle"} className="chart-label">{rows[i].date}</text>
      ))}
      {hover != null && <line x1={x(hover)} x2={x(hover)} y1={top} y2={bot} className="cross" />}
    </svg>
  );
}

function Legend({ items }) {
  return (
    <ul className="legend">
      {items.map(([name, color]) => <li key={name}><i style={{ background: color }} />{name}</li>)}
    </ul>
  );
}

export default function StockCharts({ taskId }) {
  const [state, setState] = useState({ loading: true });
  const [hover, setHover] = useState(null);
  const [show, setShow] = useState({ sma20: true, sma50: true, sma200: false });

  useEffect(() => {
    let off = false;
    api(`/research/${taskId}/chart`)
      .then((d) => !off && setState({ data: d }))
      .catch((e) => !off && setState({ error: e.message }));
    return () => { off = true; };
  }, [taskId]);

  const rows = state.data?.rows ?? [];
  const cur = useMemo(() => (hover != null ? rows[hover] : rows[rows.length - 1]), [hover, rows]);

  if (state.loading) return <section className="card"><div className="spinner" role="status" aria-label="Loading charts" /></section>;
  if (state.error) return <section className="card"><h2 className="h-md">Price charts</h2><div className="alert alert-error" role="alert">Charts are unavailable: {state.error}</div></section>;

  const { summary, source, retrieved_at } = state.data;
  const up = summary.period_return >= 0;
  const price = [
    { key: "close", color: COLORS.close, width: 2 },
    ...["sma20", "sma50", "sma200"].filter((k) => show[k]).map((k) => ({ key: k, color: COLORS[k], width: 1.3 })),
  ];
  const shared = { rows, hover, setHover };

  return (
    <section className="card charts">
      <h2 className="h-md">Price charts</h2>
      <p className="muted prov">
        Source: <strong>{source}</strong>{retrieved_at ? <> · retrieved {formatDate(retrieved_at)}</> : null}
      </p>

      <div className="stat-row">
        <div><span className="muted">Last close</span><strong>{fmt(summary.last_close)}</strong></div>
        <div><span className="muted">Period return</span><strong className={up ? "pos" : "neg"}>{pct(summary.period_return)}</strong></div>
        <div><span className="muted">Period high</span><strong>{fmt(summary.high)}</strong></div>
        <div><span className="muted">Period low</span><strong>{fmt(summary.low)}</strong></div>
      </div>

      <div className="hoverbar" aria-live="off">
        <strong>{cur.date}</strong>
        <span>O {fmt(cur.open)}</span><span>H {fmt(cur.high)}</span><span>L {fmt(cur.low)}</span>
        <span>C {fmt(cur.close)}</span><span>Vol {compact(cur.volume)}</span>
      </div>

      <div className="toggles">
        {["sma20", "sma50", "sma200"].map((k) => (
          <label key={k}><input type="checkbox" checked={show[k]} onChange={() => setShow({ ...show, [k]: !show[k] })} />
            <i style={{ background: COLORS[k] }} />{k.replace("sma", "")}-day average</label>
        ))}
      </div>
      <Panel {...shared} height={280} series={price} label={`Closing price, ${summary.start_date} to ${summary.end_date}`} />

      <h3 className="chart-title">Volume</h3>
      <Panel {...shared} height={100} bars={{ key: "volume", color: (r, i) => (i > 0 && r.close < rows[i - 1].close ? COLORS.down : COLORS.up) }} format={compact} label="Daily trading volume" />

      <h3 className="chart-title">RSI (14) <span className="muted">above 70 overbought · below 30 oversold</span> <strong className="chart-now">{fmt(cur.rsi, 0)}</strong></h3>
      <Panel {...shared} height={120} series={[{ key: "rsi", color: COLORS.sma20 }]} yFixed={[0, 100]} bands={[30, 70]} format={(v) => v} label="Relative strength index" />

      <h3 className="chart-title">MACD <span className="muted">momentum</span> <strong className="chart-now">{fmt(cur.macd_hist)}</strong></h3>
      <Panel {...shared} height={120} series={[{ key: "macd", color: COLORS.sma20 }, { key: "macd_signal", color: COLORS.sma50 }]}
        bars={{ key: "macd_hist", color: (r) => ((r.macd_hist ?? 0) >= 0 ? COLORS.up : COLORS.down) }} label="MACD" />
      <Legend items={[["MACD line", COLORS.sma20], ["Signal line", COLORS.sma50], ["Histogram", COLORS.up]]} />
    </section>
  );
}
