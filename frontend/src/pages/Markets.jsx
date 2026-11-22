import { useEffect, useState, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";
import {
  getPreferences,
  getStockHistory,
  searchStocks,
  getWatchlist,
} from "../services/authService";

// Default premier companies for NSE, BSE, NASDAQ, and NYSE
const DEFAULT_COMPANIES = {
  NSE: [
    { ticker: "TCS", company_name: "Tata Consultancy Services", market: "NSE" },
    { ticker: "RELIANCE", company_name: "Reliance Industries", market: "NSE" },
    { ticker: "INFY", company_name: "Infosys Limited", market: "NSE" },
    { ticker: "HDFCBANK", company_name: "HDFC Bank Limited", market: "NSE" },
    { ticker: "ICICIBANK", company_name: "ICICI Bank Limited", market: "NSE" },
    { ticker: "TATAMOTORS", company_name: "Tata Motors Limited", market: "NSE" },
  ],
  BSE: [
    { ticker: "TCS", company_name: "Tata Consultancy Services", market: "BSE" },
    { ticker: "RELIANCE", company_name: "Reliance Industries", market: "BSE" },
    { ticker: "INFY", company_name: "Infosys Limited", market: "BSE" },
    { ticker: "HDFCBANK", company_name: "HDFC Bank Limited", market: "BSE" },
    { ticker: "ICICIBANK", company_name: "ICICI Bank Limited", market: "BSE" },
    { ticker: "TATAMOTORS", company_name: "Tata Motors Limited", market: "BSE" },
  ],
  NASDAQ: [
    { ticker: "AAPL", company_name: "Apple Inc.", market: "NASDAQ" },
    { ticker: "MSFT", company_name: "Microsoft Corporation", market: "NASDAQ" },
    { ticker: "GOOGL", company_name: "Alphabet Inc.", market: "NASDAQ" },
    { ticker: "AMZN", company_name: "Amazon.com Inc.", market: "NASDAQ" },
    { ticker: "NVDA", company_name: "NVIDIA Corporation", market: "NASDAQ" },
    { ticker: "TSLA", company_name: "Tesla Inc.", market: "NASDAQ" },
  ],
  NYSE: [
    { ticker: "KO", company_name: "The Coca-Cola Company", market: "NYSE" },
    { ticker: "JPM", company_name: "JPMorgan Chase & Co.", market: "NYSE" },
    { ticker: "DIS", company_name: "The Walt Disney Company", market: "NYSE" },
    { ticker: "WMT", company_name: "Walmart Inc.", market: "NYSE" },
    { ticker: "BA", company_name: "The Boeing Company", market: "NYSE" },
    { ticker: "IBM", company_name: "International Business Machines", market: "NYSE" },
  ],
};

const COMPARISON_COLORS = [
  "#C6F36B", // Lime
  "#38BDF8", // Sky Blue
  "#F59E0B", // Amber
  "#EC4899", // Pink
  "#A78BFA", // Violet
  "#34D399", // Emerald
];

function getCurrencyPrefix(market) {
  return market === "NASDAQ" || market === "NYSE" ? "$" : "₹";
}

function formatPrice(val, market = "NSE") {
  if (val === undefined || val === null || isNaN(val)) return "—";
  const locale = market === "NASDAQ" || market === "NYSE" ? "en-US" : "en-IN";
  return Number(val).toLocaleString(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatSignedPct(val) {
  if (val === undefined || val === null || isNaN(val)) return "—";
  const num = Number(val);
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(2)}%`;
}

// ============================================================================
// TECHNICAL INDICATORS MATHEMATICAL ENGINE
// ============================================================================

/**
 * Simple Moving Average (SMA)
 * Calculated on historical closing prices.
 */
function calculateSMA(data, period = 20) {
  if (!data || data.length === 0) return [];
  const p = Math.min(period, Math.max(2, data.length));
  const result = new Array(data.length).fill(null);
  let sum = 0;
  for (let i = 0; i < data.length; i++) {
    sum += data[i].close;
    if (i >= p - 1) {
      if (i >= p) {
        sum -= data[i - p].close;
      }
      result[i] = sum / p;
    }
  }
  return { values: result, period: p };
}

/**
 * Exponential Moving Average (EMA)
 * Calculated on historical closing prices using standard multiplier k = 2 / (p + 1).
 */
function calculateEMA(data, period = 20) {
  if (!data || data.length === 0) return { values: [], period: 0 };
  const p = Math.min(period, Math.max(2, data.length));
  const result = new Array(data.length).fill(null);
  if (data.length < p) return { values: result, period: p };

  // Seed with initial SMA
  let sum = 0;
  for (let i = 0; i < p; i++) {
    sum += data[i].close;
  }
  let prevEma = sum / p;
  result[p - 1] = prevEma;

  const k = 2 / (p + 1);
  for (let i = p; i < data.length; i++) {
    const ema = data[i].close * k + prevEma * (1 - k);
    result[i] = ema;
    prevEma = ema;
  }
  return { values: result, period: p };
}

/**
 * Relative Strength Index (RSI)
 * 14-period Wilder's smoothed momentum oscillator on closing prices (0-100 scale).
 */
function calculateRSI(data, period = 14) {
  if (!data || data.length === 0) return { values: [], period: 0 };
  const p = Math.min(period, Math.max(3, Math.floor(data.length / 2)));
  const result = new Array(data.length).fill(null);
  if (data.length <= p) return { values: result, period: p };

  let gains = 0;
  let losses = 0;
  for (let i = 1; i <= p; i++) {
    const diff = data[i].close - data[i - 1].close;
    if (diff >= 0) gains += diff;
    else losses += Math.abs(diff);
  }

  let avgGain = gains / p;
  let avgLoss = losses / p;
  result[p] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);

  for (let i = p + 1; i < data.length; i++) {
    const diff = data[i].close - data[i - 1].close;
    const gain = diff >= 0 ? diff : 0;
    const loss = diff < 0 ? Math.abs(diff) : 0;

    avgGain = (avgGain * (p - 1) + gain) / p;
    avgLoss = (avgLoss * (p - 1) + loss) / p;

    if (avgLoss === 0) {
      result[i] = 100;
    } else {
      const rs = avgGain / avgLoss;
      result[i] = 100 - 100 / (1 + rs);
    }
  }

  return { values: result, period: p };
}

/**
 * Moving Average Convergence Divergence (MACD)
 * Standard (12, 26, 9) or dynamically scaled for short periods.
 * Returns { macdLine, signalLine, histogram }.
 */
function calculateMACD(data, fast = 12, slow = 26, signal = 9) {
  if (!data || data.length === 0) {
    return { macdLine: [], signalLine: [], histogram: [] };
  }

  // Adjust periods if dataset is small
  const slowP = Math.min(slow, Math.max(4, Math.floor(data.length * 0.75)));
  const fastP = Math.min(fast, Math.max(2, Math.floor(slowP / 2)));
  const signalP = Math.min(signal, Math.max(2, Math.floor(data.length * 0.25)));

  const fastEMA = calculateEMA(data, fastP).values;
  const slowEMA = calculateEMA(data, slowP).values;

  const macdLine = new Array(data.length).fill(null);
  for (let i = 0; i < data.length; i++) {
    if (fastEMA[i] !== null && slowEMA[i] !== null) {
      macdLine[i] = fastEMA[i] - slowEMA[i];
    }
  }

  const signalLine = new Array(data.length).fill(null);
  const histogram = new Array(data.length).fill(null);

  const firstValid = macdLine.findIndex((v) => v !== null);
  if (firstValid !== -1 && data.length - firstValid >= signalP) {
    let sum = 0;
    const startIdx = firstValid + signalP - 1;
    for (let i = firstValid; i <= startIdx; i++) {
      sum += macdLine[i];
    }
    let prevSig = sum / signalP;
    signalLine[startIdx] = prevSig;
    histogram[startIdx] = macdLine[startIdx] - prevSig;

    const k = 2 / (signalP + 1);
    for (let i = startIdx + 1; i < data.length; i++) {
      const sig = macdLine[i] * k + prevSig * (1 - k);
      signalLine[i] = sig;
      histogram[i] = macdLine[i] - sig;
      prevSig = sig;
    }
  }

  return { macdLine, signalLine, histogram, fastP, slowP, signalP };
}

// ============================================================================
// MEDIUM STOCK CHART (WITH SMA/EMA OVERLAYS & SEPARATE RSI / MACD PANELS)
// ============================================================================
function MediumStockChart({
  company,
  data,
  loading,
  error,
  period,
  activeIndicators = ["SMA", "EMA", "RSI", "MACD"],
  onToggleIndicator,
  width = 720,
  height = 250,
}) {
  const [hoverIndex, setHoverIndex] = useState(null);

  const padding = { top: 22, right: 24, bottom: 32, left: 65 };

  // Daily price change: calculated using latest close and previous trading day's close
  const dailyStats = useMemo(() => {
    if (!data || !data.length) return null;
    const latest = data[data.length - 1].close;
    const prev = data.length > 1 ? data[data.length - 2].close : latest;
    const diff = latest - prev;
    const pct = prev ? ((diff / prev) * 100).toFixed(2) : "0.00";
    const isUp = diff >= 0;
    return { latest, prev, diff, pct, isUp };
  }, [data]);

  // Overall period change for context
  const periodDiff = useMemo(() => {
    if (!data || data.length < 2) return null;
    const first = data[0].close;
    const latest = data[data.length - 1].close;
    const diff = latest - first;
    const pct = ((diff / first) * 100).toFixed(2);
    return { first, latest, diff, pct, isUp: diff >= 0 };
  }, [data]);

  const prices = useMemo(
    () => (data && data.length ? data.map((d) => d.close) : []),
    [data]
  );

  // Technical indicator calculations
  const smaResult = useMemo(
    () => (activeIndicators.includes("SMA") ? calculateSMA(data, 20) : null),
    [data, activeIndicators]
  );

  const emaResult = useMemo(
    () => (activeIndicators.includes("EMA") ? calculateEMA(data, 20) : null),
    [data, activeIndicators]
  );

  const rsiResult = useMemo(
    () => (activeIndicators.includes("RSI") ? calculateRSI(data, 14) : null),
    [data, activeIndicators]
  );

  const macdResult = useMemo(
    () =>
      activeIndicators.includes("MACD")
        ? calculateMACD(data, 12, 26, 9)
        : null,
    [data, activeIndicators]
  );

  // Min and Max prices for Price Chart (incorporating SMA & EMA to avoid clipping)
  const { minPrice, maxPrice, priceRange } = useMemo(() => {
    if (!prices.length) return { minPrice: 0, maxPrice: 0, priceRange: 1 };
    let min = Math.min(...prices);
    let max = Math.max(...prices);

    if (smaResult?.values) {
      smaResult.values.forEach((v) => {
        if (v !== null) {
          if (v < min) min = v;
          if (v > max) max = v;
        }
      });
    }

    if (emaResult?.values) {
      emaResult.values.forEach((v) => {
        if (v !== null) {
          if (v < min) min = v;
          if (v > max) max = v;
        }
      });
    }

    const pad = (max - min) * 0.05 || 1;
    return {
      minPrice: min - pad,
      maxPrice: max + pad,
      priceRange: max - min + pad * 2,
    };
  }, [prices, smaResult, emaResult]);

  // Points for Price Chart
  const points = useMemo(() => {
    if (!data || !data.length) return [];
    const innerW = width - padding.left - padding.right;
    const innerH = height - padding.top - padding.bottom;

    return data.map((d, i) => {
      const x = padding.left + (i / Math.max(data.length - 1, 1)) * innerW;
      const y =
        padding.top +
        innerH -
        ((d.close - minPrice) / priceRange) * innerH;
      return { ...d, x, y };
    });
  }, [data, width, height, minPrice, priceRange, padding]);

  const linePath = useMemo(() => {
    if (!points.length) return "";
    return points.map((p) => `${p.x},${p.y}`).join(" ");
  }, [points]);

  const areaPath = useMemo(() => {
    if (!points.length) return "";
    const bottomY = height - padding.bottom;
    return `${linePath} ${points[points.length - 1].x},${bottomY} ${points[0].x},${bottomY}`;
  }, [linePath, points, height, padding.bottom]);

  // SMA overlay path on Price Chart
  const smaPoints = useMemo(() => {
    if (!smaResult || !points.length) return "";
    const innerH = height - padding.top - padding.bottom;
    const pts = [];
    smaResult.values.forEach((val, idx) => {
      if (val !== null && points[idx]) {
        const y =
          padding.top + innerH - ((val - minPrice) / priceRange) * innerH;
        pts.push(`${points[idx].x},${y}`);
      }
    });
    return pts.join(" ");
  }, [smaResult, points, height, minPrice, priceRange, padding]);

  // EMA overlay path on Price Chart
  const emaPoints = useMemo(() => {
    if (!emaResult || !points.length) return "";
    const innerH = height - padding.top - padding.bottom;
    const pts = [];
    emaResult.values.forEach((val, idx) => {
      if (val !== null && points[idx]) {
        const y =
          padding.top + innerH - ((val - minPrice) / priceRange) * innerH;
        pts.push(`${points[idx].x},${y}`);
      }
    });
    return pts.join(" ");
  }, [emaResult, points, height, minPrice, priceRange, padding]);

  const activeIdx = hoverIndex !== null ? hoverIndex : points.length - 1;
  const activePoint = points[activeIdx] || null;
  const activeSMA = smaResult?.values[activeIdx] ?? null;
  const activeEMA = emaResult?.values[activeIdx] ?? null;
  const activeRSI = rsiResult?.values[activeIdx] ?? null;
  const activeMACD = macdResult?.macdLine[activeIdx] ?? null;
  const activeSignal = macdResult?.signalLine[activeIdx] ?? null;
  const activeHist = macdResult?.histogram[activeIdx] ?? null;
  const currSymbol = getCurrencyPrefix(company?.market);

  return (
    <div className="mk-chart-card">
      {/* Top Header */}
      <div className="mk-chart-top">
        <div className="mk-chart-meta">
          <div className="mk-chart-title-row">
            <h3 className="mk-chart-name">{company.company_name}</h3>
            <span className="mk-ticker-badge">{company.ticker}</span>
            <span className="mk-market-badge">{company.market}</span>
          </div>
          <div className="mk-period-row">
            <span className="mk-period-label">{period.toUpperCase()} Price Trend</span>
            <span className="mk-data-nature-pill">Market Closing Data</span>
          </div>
        </div>

        {dailyStats && (
          <div className="mk-chart-price-block">
            <div className="mk-price-row-top">
              <span className="mk-current-price">
                {currSymbol}{formatPrice(dailyStats.latest, company?.market)}
              </span>
              <span className={`mk-change-pill ${dailyStats.isUp ? "up" : "down"}`}>
                {dailyStats.isUp ? "▲ +" : "▼ "}
                {currSymbol}{formatPrice(Math.abs(dailyStats.diff), company?.market)} ({dailyStats.pct}%)
              </span>
            </div>
            <span className="mk-daily-change-note">
              Daily change vs prev close ({dailyStats.prev ? `${currSymbol}${formatPrice(dailyStats.prev, company?.market)}` : "—"})
            </span>
          </div>
        )}
      </div>

      {/* Technical Indicators Interactive Controls */}
      <div className="mk-indicators-toolbar">
        <span className="mk-ind-toolbar-label">Technical Overlays:</span>
        <button
          type="button"
          className={`mk-ind-btn ${activeIndicators.includes("SMA") ? "active-sma" : ""}`}
          onClick={() => onToggleIndicator && onToggleIndicator("SMA")}
          title="Simple Moving Average (20-period overlay on price)"
        >
          <span className="mk-ind-dot sma-dot" />
          SMA ({smaResult?.period || 20})
        </button>
        <button
          type="button"
          className={`mk-ind-btn ${activeIndicators.includes("EMA") ? "active-ema" : ""}`}
          onClick={() => onToggleIndicator && onToggleIndicator("EMA")}
          title="Exponential Moving Average (20-period overlay on price)"
        >
          <span className="mk-ind-dot ema-dot" />
          EMA ({emaResult?.period || 20})
        </button>

        <span className="mk-ind-toolbar-sep" />
        <span className="mk-ind-toolbar-label">Sub-Panels:</span>

        <button
          type="button"
          className={`mk-ind-btn ${activeIndicators.includes("RSI") ? "active-rsi" : ""}`}
          onClick={() => onToggleIndicator && onToggleIndicator("RSI")}
          title="Relative Strength Index (0-100 oscillator panel)"
        >
          <span className="mk-ind-dot rsi-dot" />
          RSI ({rsiResult?.period || 14})
        </button>
        <button
          type="button"
          className={`mk-ind-btn ${activeIndicators.includes("MACD") ? "active-macd" : ""}`}
          onClick={() => onToggleIndicator && onToggleIndicator("MACD")}
          title="Moving Average Convergence Divergence panel"
        >
          <span className="mk-ind-dot macd-dot" />
          MACD ({macdResult?.fastP || 12},{macdResult?.slowP || 26})
        </button>

        {/* Live indicator readout values */}
        <div className="mk-ind-readouts">
          {activeSMA !== null && (
            <span className="mk-readout-item sma">
              SMA: {currSymbol}{formatPrice(activeSMA, company?.market)}
            </span>
          )}
          {activeEMA !== null && (
            <span className="mk-readout-item ema">
              EMA: {currSymbol}{formatPrice(activeEMA, company?.market)}
            </span>
          )}
        </div>
      </div>

      {/* Main Price Chart */}
      <div className="mk-svg-wrapper">
        {loading ? (
          <div className="mk-chart-loader">
            <div className="db-spinner db-spinner-lg" />
            <p>Loading historical market data...</p>
          </div>
        ) : error ? (
          <div className="mk-chart-error">
            <span>⚠</span>
            <p>{error}</p>
          </div>
        ) : !data || !data.length ? (
          <div className="mk-chart-error">
            <p>No historical data found for {company.ticker}</p>
          </div>
        ) : (
          <svg
            className="mk-svg-chart"
            viewBox={`0 0 ${width} ${height}`}
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient
                id={`mk-grad-${company.ticker}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopColor={dailyStats?.isUp ? "#C6F36B" : "#FF8791"}
                  stopOpacity="0.28"
                />
                <stop
                  offset="100%"
                  stopColor={dailyStats?.isUp ? "#C6F36B" : "#FF8791"}
                  stopOpacity="0.0"
                />
              </linearGradient>
            </defs>

            {/* Gridlines & Price axis */}
            {[0, 1, 2, 3].map((step) => {
              const y =
                padding.top +
                (step / 3) * (height - padding.top - padding.bottom);
              const val = maxPrice - (step / 3) * priceRange;
              return (
                <g key={step}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={width - padding.right}
                    y2={y}
                    className="mk-grid-line"
                  />
                  <text
                    x={padding.left - 8}
                    y={y + 4}
                    textAnchor="end"
                    className="mk-axis-text"
                  >
                    {currSymbol}{formatPrice(val, company?.market)}
                  </text>
                </g>
              );
            })}

            {/* Price Area & Line */}
            <polygon
              points={areaPath}
              fill={`url(#mk-grad-${company.ticker})`}
            />
            <polyline
              points={linePath}
              className={`mk-poly-line ${dailyStats?.isUp ? "up" : "down"}`}
            />

            {/* SMA-20 Overlay Line */}
            {activeIndicators.includes("SMA") && smaPoints && (
              <polyline
                points={smaPoints}
                className="mk-sma-overlay-line"
              />
            )}

            {/* EMA-20 Overlay Line */}
            {activeIndicators.includes("EMA") && emaPoints && (
              <polyline
                points={emaPoints}
                className="mk-ema-overlay-line"
              />
            )}

            {/* Interactive hover points & vertical cursor */}
            {activePoint && hoverIndex !== null && (
              <line
                x1={activePoint.x}
                y1={padding.top}
                x2={activePoint.x}
                y2={height - padding.bottom}
                className="mk-cursor-line"
              />
            )}

            {points.map((pt, i) => (
              <circle
                key={i}
                cx={pt.x}
                cy={pt.y}
                r={hoverIndex === i ? 5.5 : 2}
                className="mk-chart-dot"
                onMouseEnter={() => setHoverIndex(i)}
                onMouseLeave={() => setHoverIndex(null)}
              />
            ))}

            {/* Dates on X Axis */}
            {data.length > 0 && (
              <>
                <text
                  x={padding.left}
                  y={height - 10}
                  className="mk-axis-text"
                >
                  {data[0].date}
                </text>
                <text
                  x={width - padding.right}
                  y={height - 10}
                  textAnchor="end"
                  className="mk-axis-text"
                >
                  {data[data.length - 1].date}
                </text>
              </>
            )}
          </svg>
        )}
      </div>

      {/* SEPARATE PANEL: RSI (0-100 SCALE) */}
      {activeIndicators.includes("RSI") && data && data.length > 0 && (
        <div className="mk-subpanel-card">
          <div className="mk-subpanel-header">
            <div className="mk-subpanel-title">
              <span className="mk-ind-dot rsi-dot" />
              <strong>RSI ({rsiResult?.period || 14})</strong>
              <span className="mk-subpanel-desc">Relative Strength Index</span>
            </div>
            {activeRSI !== null && (
              <span
                className={`mk-rsi-badge ${
                  activeRSI >= 70
                    ? "overbought"
                    : activeRSI <= 30
                    ? "oversold"
                    : "neutral"
                }`}
              >
                RSI: {activeRSI.toFixed(2)}{" "}
                {activeRSI >= 70
                  ? "(Overbought ≥70)"
                  : activeRSI <= 30
                  ? "(Oversold ≤30)"
                  : "(Neutral)"}
              </span>
            )}
          </div>

          <svg
            className="mk-subpanel-svg"
            viewBox={`0 0 ${width} 110`}
            preserveAspectRatio="none"
          >
            {/* RSI Levels: 70 Overbought, 50 Neutral, 30 Oversold */}
            {[
              { lvl: 70, color: "#EF4444", label: "70 Overbought", dash: "4 3" },
              { lvl: 50, color: "#64748B", label: "50 Neutral", dash: "2 2" },
              { lvl: 30, color: "#10B981", label: "30 Oversold", dash: "4 3" },
            ].map(({ lvl, color, label, dash }) => {
              const y = 15 + (1 - lvl / 100) * 75;
              return (
                <g key={lvl}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={width - padding.right}
                    y2={y}
                    stroke={color}
                    strokeDasharray={dash}
                    strokeWidth="1"
                    opacity="0.65"
                  />
                  <text
                    x={padding.left - 6}
                    y={y + 3}
                    textAnchor="end"
                    fill={color}
                    fontSize="10"
                    fontFamily="monospace"
                  >
                    {lvl}
                  </text>
                  <text
                    x={width - padding.right + 4}
                    y={y + 3}
                    fill={color}
                    fontSize="9"
                    opacity="0.8"
                  >
                    {label}
                  </text>
                </g>
              );
            })}

            {/* RSI Polyline */}
            {rsiResult?.values && points.length > 0 && (
              <polyline
                points={rsiResult.values
                  .map((val, idx) => {
                    if (val === null || !points[idx]) return null;
                    const y = 15 + (1 - val / 100) * 75;
                    return `${points[idx].x},${y}`;
                  })
                  .filter(Boolean)
                  .join(" ")}
                fill="none"
                stroke="#A78BFA"
                strokeWidth="2"
              />
            )}

            {/* Interactive hover circle */}
            {activeRSI !== null && points[activeIdx] && (
              <circle
                cx={points[activeIdx].x}
                cy={15 + (1 - activeRSI / 100) * 75}
                r="4.5"
                fill="#A78BFA"
                stroke="#0F172A"
                strokeWidth="2"
              />
            )}
          </svg>
        </div>
      )}

      {/* SEPARATE PANEL: MACD (MACD LINE, SIGNAL LINE, AND HISTOGRAM) */}
      {activeIndicators.includes("MACD") && data && data.length > 0 && (
        <div className="mk-subpanel-card">
          <div className="mk-subpanel-header">
            <div className="mk-subpanel-title">
              <span className="mk-ind-dot macd-dot" />
              <strong>
                MACD ({macdResult?.fastP || 12}, {macdResult?.slowP || 26},{" "}
                {macdResult?.signalP || 9})
              </strong>
              <span className="mk-subpanel-desc">Convergence / Divergence</span>
            </div>

            <div className="mk-macd-legend">
              <span className="mk-macd-leg-item macd-line-leg">
                <span className="leg-dash sky" /> MACD:{" "}
                {activeMACD !== null ? activeMACD.toFixed(2) : "—"}
              </span>
              <span className="mk-macd-leg-item signal-line-leg">
                <span className="leg-dash amber" /> Signal:{" "}
                {activeSignal !== null ? activeSignal.toFixed(2) : "—"}
              </span>
              <span className="mk-macd-leg-item hist-leg">
                Hist: {activeHist !== null ? activeHist.toFixed(2) : "—"}
              </span>
            </div>
          </div>

          {(() => {
            const allVals = [];
            macdResult?.macdLine?.forEach((v) => v !== null && allVals.push(v));
            macdResult?.signalLine?.forEach((v) => v !== null && allVals.push(v));
            macdResult?.histogram?.forEach((v) => v !== null && allVals.push(v));

            const maxM = allVals.length ? Math.max(...allVals, 0.2) : 1;
            const minM = allVals.length ? Math.min(...allVals, -0.2) : -1;
            const absLimit = Math.max(Math.abs(maxM), Math.abs(minM), 0.5) * 1.15;
            const panelH = 120;
            const topY = 15;
            const botY = panelH - 15;
            const innerH = botY - topY;
            const zeroY = topY + innerH / 2;

            const scaleY = (val) => {
              if (val === null) return zeroY;
              return zeroY - (val / absLimit) * (innerH / 2);
            };

            const macdPts = (macdResult?.macdLine || [])
              .map((val, idx) => {
                if (val === null || !points[idx]) return null;
                return `${points[idx].x},${scaleY(val)}`;
              })
              .filter(Boolean)
              .join(" ");

            const sigPts = (macdResult?.signalLine || [])
              .map((val, idx) => {
                if (val === null || !points[idx]) return null;
                return `${points[idx].x},${scaleY(val)}`;
              })
              .filter(Boolean)
              .join(" ");

            return (
              <svg
                className="mk-subpanel-svg"
                viewBox={`0 0 ${width} ${panelH}`}
                preserveAspectRatio="none"
              >
                {/* Zero line */}
                <line
                  x1={padding.left}
                  y1={zeroY}
                  x2={width - padding.right}
                  y2={zeroY}
                  stroke="#475569"
                  strokeDasharray="3 3"
                  strokeWidth="1"
                />
                <text
                  x={padding.left - 6}
                  y={zeroY + 3}
                  textAnchor="end"
                  fill="#64748B"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  0.0
                </text>

                {/* Histogram Bars */}
                {macdResult?.histogram?.map((hist, idx) => {
                  if (hist === null || !points[idx]) return null;
                  const x = points[idx].x;
                  const barY = scaleY(hist);
                  const isPos = hist >= 0;
                  const barH = Math.max(Math.abs(zeroY - barY), 1);
                  const y = isPos ? barY : zeroY;
                  return (
                    <rect
                      key={idx}
                      x={x - 1.5}
                      y={y}
                      width={3}
                      height={barH}
                      fill={isPos ? "#34D399" : "#F87171"}
                      opacity="0.85"
                    />
                  );
                })}

                {/* MACD Line */}
                {macdPts && (
                  <polyline
                    points={macdPts}
                    fill="none"
                    stroke="#38BDF8"
                    strokeWidth="1.8"
                  />
                )}

                {/* Signal Line */}
                {sigPts && (
                  <polyline
                    points={sigPts}
                    fill="none"
                    stroke="#F59E0B"
                    strokeWidth="1.5"
                    strokeDasharray="4 2"
                  />
                )}
              </svg>
            );
          })()}
        </div>
      )}

      {/* Tooltip bar on hover */}
      {activePoint && (
        <div className="mk-hover-stats">
          <span>
            <strong>Date:</strong> {activePoint.date}
          </span>
          <span>
            <strong>Close:</strong> {currSymbol}{formatPrice(activePoint.close, company?.market)}
          </span>
          <span>
            <strong>High:</strong> {currSymbol}{formatPrice(activePoint.high, company?.market)}
          </span>
          <span>
            <strong>Low:</strong> {currSymbol}{formatPrice(activePoint.low, company?.market)}
          </span>
          <span>
            <strong>Vol:</strong>{" "}
            {Number(activePoint.volume || 0).toLocaleString(
              company?.market === "NASDAQ" || company?.market === "NYSE" ? "en-US" : "en-IN"
            )}
          </span>
        </div>
      )}

      {/* Summary strip */}
      {data && data.length > 0 && (
        <div className="mk-card-footer">
          <div>
            <span>52W / Period High</span>
            <strong>{currSymbol}{formatPrice(maxPrice, company?.market)}</strong>
          </div>
          <div>
            <span>Period Low</span>
            <strong>{currSymbol}{formatPrice(minPrice, company?.market)}</strong>
          </div>
          <div>
            <span>Period Net Return</span>
            <strong
              className={
                periodDiff?.isUp ? "mk-green-text" : "mk-red-text"
              }
            >
              {periodDiff ? formatSignedPct(periodDiff.pct) : "—"}
            </strong>
          </div>
          <div>
            <span>Trading Sessions</span>
            <strong>{data.length}</strong>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// MULTI-COMPANY COMPARISON COMPONENT (NORMALIZED TO 0% BASELINE)
// ============================================================================
function MultiCompanyComparison({
  companies,
  marketDataMap,
  loadingMap,
  activePeriod,
  onRemoveCompany,
  width = 960,
  height = 340,
}) {
  const [hoverDate, setHoverDate] = useState(null);
  const padding = { top: 25, right: 30, bottom: 40, left: 65 };

  // 1. Gather all unique trading dates across all companies, sorted ascending
  const { allDates, companyDataSeries } = useMemo(() => {
    const datesSet = new Set();
    const series = [];

    companies.forEach((comp, idx) => {
      const key = `${comp.ticker}_${comp.market}_${activePeriod}`;
      const raw = marketDataMap[key];

      if (raw && Array.isArray(raw) && raw.length > 0) {
        // Collect dates
        raw.forEach((r) => r.date && datesSet.add(r.date));

        // Normalise each company's closing price to 0% at its first available date
        const baseClose = raw[0].close;
        const dateMap = {};

        raw.forEach((item) => {
          if (item.date && item.close !== undefined && item.close !== null) {
            const pct =
              baseClose !== 0
                ? ((item.close - baseClose) / baseClose) * 100
                : 0;
            dateMap[item.date] = { close: item.close, pct };
          }
        });

        const totalPct =
          raw.length > 1 && baseClose !== 0
            ? ((raw[raw.length - 1].close - baseClose) / baseClose) * 100
            : 0;

        series.push({
          company: comp,
          color: COMPARISON_COLORS[idx % COMPARISON_COLORS.length],
          baseClose,
          latestClose: raw[raw.length - 1].close,
          totalPct,
          dateMap,
          count: raw.length,
        });
      }
    });

    const sortedDates = Array.from(datesSet).sort();
    return { allDates: sortedDates, companyDataSeries: series };
  }, [companies, marketDataMap, activePeriod]);

  // 2. Compute min and max percentage across all companies
  const { minPct, maxPct, pctRange } = useMemo(() => {
    let min = 0;
    let max = 0;

    companyDataSeries.forEach((s) => {
      Object.values(s.dateMap).forEach((val) => {
        if (val.pct < min) min = val.pct;
        if (val.pct > max) max = val.pct;
      });
    });

    const pad = Math.max(Math.abs(max - min) * 0.1, 2);
    const rMin = min - pad;
    const rMax = max + pad;
    return { minPct: rMin, maxPct: rMax, pctRange: rMax - rMin || 1 };
  }, [companyDataSeries]);

  // 3. Map dates to X coordinates
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  const dateToX = useMemo(() => {
    const map = {};
    if (allDates.length === 1) {
      map[allDates[0]] = padding.left + innerW / 2;
    } else {
      allDates.forEach((d, i) => {
        map[d] = padding.left + (i / (allDates.length - 1)) * innerW;
      });
    }
    return map;
  }, [allDates, innerW, padding.left]);

  const scaleY = useCallback(
    (pct) => {
      return padding.top + innerH - ((pct - minPct) / pctRange) * innerH;
    },
    [innerH, minPct, pctRange, padding.top]
  );

  const zeroY = useMemo(() => scaleY(0), [scaleY]);

  // 4. Build polyline points for each company (strictly using actual recorded dates)
  const renderedSeries = useMemo(() => {
    return companyDataSeries.map((s) => {
      const points = [];
      allDates.forEach((d) => {
        if (s.dateMap[d]) {
          const x = dateToX[d];
          const y = scaleY(s.dateMap[d].pct);
          points.push({ x, y, date: d, ...s.dateMap[d] });
        }
      });
      const polylineStr = points.map((p) => `${p.x},${p.y}`).join(" ");
      return { ...s, points, polylineStr };
    });
  }, [companyDataSeries, allDates, dateToX, scaleY]);

  const anyLoading = companies.some(
    (c) => loadingMap[`${c.ticker}_${c.market}_${activePeriod}`]
  );

  return (
    <div className="mk-comparison-card">
      <div className="mk-comparison-header">
        <div>
          <span className="mk-banner-tag">MULTI-COMPANY COMPARISON</span>
          <h2 className="mk-comparison-title">Normalized Relative Price Performance</h2>
          <p className="mk-comparison-subtitle">
            Each stock is normalized to 0.0% at its starting date in {activePeriod.toUpperCase()}. Dates are synchronized across trading calendars without inventing prices.
          </p>
        </div>
      </div>

      {/* Legend & Company Pill Selector */}
      <div className="mk-comparison-legend">
        {companies.map((comp, idx) => {
          const s = companyDataSeries.find(
            (item) => item.company.ticker === comp.ticker
          );
          const color = COMPARISON_COLORS[idx % COMPARISON_COLORS.length];
          return (
            <div
              key={`${comp.ticker}-${comp.market}`}
              className="mk-comp-legend-pill"
              style={{ borderColor: `${color}66` }}
            >
              <span
                className="mk-comp-color-dot"
                style={{ backgroundColor: color }}
              />
              <span className="mk-comp-pill-ticker">{comp.ticker}</span>
              <span className="mk-comp-pill-ret" style={{ color }}>
                {s ? formatSignedPct(s.totalPct) : "Loading..."}
              </span>
              {companies.length > 2 && (
                <button
                  type="button"
                  className="mk-comp-remove-btn"
                  onClick={() => onRemoveCompany(comp)}
                  title={`Remove ${comp.ticker} from comparison`}
                >
                  ✕
                </button>
              )}
            </div>
          );
        })}
      </div>

      {anyLoading && (
        <div className="mk-comp-loading-banner">
          <div className="db-spinner" /> Loading comparison price data...
        </div>
      )}

      {/* Comparison SVG Chart */}
      <div className="mk-svg-wrapper">
        <svg
          className="mk-svg-chart"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
        >
          {/* Grid lines and percentage axis labels */}
          {[0, 1, 2, 3, 4].map((step) => {
            const y = padding.top + (step / 4) * innerH;
            const pctVal = maxPct - (step / 4) * pctRange;
            return (
              <g key={step}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  className="mk-grid-line"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  textAnchor="end"
                  className="mk-axis-text"
                >
                  {formatSignedPct(pctVal)}
                </text>
              </g>
            );
          })}

          {/* 0.0% Baseline reference line */}
          <line
            x1={padding.left}
            y1={zeroY}
            x2={width - padding.right}
            y2={zeroY}
            stroke="#94A3B8"
            strokeWidth="1.5"
            strokeDasharray="4 4"
            opacity="0.8"
          />
          <text
            x={width - padding.right + 6}
            y={zeroY + 4}
            fill="#94A3B8"
            fontSize="11"
            fontWeight="600"
          >
            0.0% (Base)
          </text>

          {/* Lines for each company */}
          {renderedSeries.map((s) => (
            <g key={s.company.ticker}>
              <polyline
                points={s.polylineStr}
                fill="none"
                stroke={s.color}
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {/* Point dots */}
              {s.points.map((pt, pIdx) => (
                <circle
                  key={pIdx}
                  cx={pt.x}
                  cy={pt.y}
                  r={hoverDate === pt.date ? 5 : 1.5}
                  fill={s.color}
                  onMouseEnter={() => setHoverDate(pt.date)}
                  onMouseLeave={() => setHoverDate(null)}
                />
              ))}
            </g>
          ))}

          {/* Date Axis */}
          {allDates.length > 0 && (
            <>
              <text x={padding.left} y={height - 12} className="mk-axis-text">
                {allDates[0]} (Start: 0%)
              </text>
              <text
                x={width - padding.right}
                y={height - 12}
                textAnchor="end"
                className="mk-axis-text"
              >
                {allDates[allDates.length - 1]}
              </text>
            </>
          )}
        </svg>
      </div>

      {/* Synchronized Hover Breakdown */}
      {hoverDate && (
        <div className="mk-comp-hover-card">
          <div className="mk-comp-hover-date">
            <strong>Trading Date:</strong> {hoverDate}
          </div>
          <div className="mk-comp-hover-grid">
            {renderedSeries.map((s) => {
              const dataPoint = s.dateMap[hoverDate];
              return (
                <div key={s.company.ticker} className="mk-comp-hover-row">
                  <span
                    className="mk-comp-color-dot"
                    style={{ backgroundColor: s.color }}
                  />
                  <strong className="mk-comp-hover-ticker">
                    {s.company.ticker}:
                  </strong>
                  {dataPoint ? (
                    <>
                      <span className="mk-comp-hover-pct" style={{ color: s.color }}>
                        {formatSignedPct(dataPoint.pct)}
                      </span>
                      <span className="mk-comp-hover-price">
                        ({getCurrencyPrefix(s.company.market)}{formatPrice(dataPoint.close, s.company.market)})
                      </span>
                    </>
                  ) : (
                    <span className="mk-comp-hover-missing">
                      No session on this date
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// MAIN MARKETS COMPONENT (MARKET EXPLORER)
// ============================================================================
function Markets() {
  const navigate = useNavigate();

  const user = JSON.parse(sessionStorage.getItem("user") || "null");
  const token = sessionStorage.getItem("access_token");

  // Preferences state
  const [preferences, setPreferences] = useState(null);
  const [activeMarket, setActiveMarket] = useState("NSE");
  const [activePeriod, setActivePeriod] = useState("1y");
  const [activeIndicators, setActiveIndicators] = useState([
    "SMA",
    "EMA",
    "RSI",
    "MACD",
  ]);

  // Companies & Data state
  const [companiesList, setCompaniesList] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [marketDataMap, setMarketDataMap] = useState({});
  const [loadingMap, setLoadingMap] = useState({});
  const [errorMap, setErrorMap] = useState({});

  // View Mode: 'focus' (medium focused chart), 'grid' (multiple medium cards), 'compare' (normalized overlay)
  const [viewMode, setViewMode] = useState("focus");

  // Comparison companies set
  const [compareCompanies, setCompareCompanies] = useState([]);

  // Search
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Auth guard
  useEffect(() => {
    if (!token || !user) {
      navigate("/login", { replace: true });
    }
  }, [navigate, token, user]);

  const logout = () => {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    navigate("/login");
  };

  // Toggle single indicator
  const handleToggleIndicator = (indicator) => {
    setActiveIndicators((prev) =>
      prev.includes(indicator)
        ? prev.filter((i) => i !== indicator)
        : [...prev, indicator]
    );
  };

  // Load Preferences & Watchlist
  useEffect(() => {
    const initData = async () => {
      try {
        const [prefs, watchlist] = await Promise.allSettled([
          getPreferences(),
          getWatchlist(),
        ]);

        let prefMarket = "NSE";
        let prefPeriod = "1y";
        let prefInd = ["SMA", "EMA", "RSI", "MACD"];

        if (prefs.status === "fulfilled" && prefs.value) {
          setPreferences(prefs.value);
          prefMarket = prefs.value.preferred_market || "NSE";
          prefPeriod = prefs.value.preferred_analysis_period || "1y";
          prefInd = prefs.value.preferred_indicators?.length
            ? prefs.value.preferred_indicators
            : prefInd;
        }

        setActiveMarket(prefMarket);
        setActivePeriod(prefPeriod);
        setActiveIndicators(prefInd);

        // Build company list starting with defaults for this market
        const defaults = DEFAULT_COMPANIES[prefMarket] || DEFAULT_COMPANIES.NSE;
        const combined = [...defaults];

        // Add user's watchlist companies if they match market
        if (watchlist.status === "fulfilled" && Array.isArray(watchlist.value)) {
          watchlist.value.forEach((wl) => {
            if (
              !combined.some(
                (c) =>
                  c.ticker.toUpperCase() === wl.ticker.toUpperCase() &&
                  c.market.toUpperCase() === wl.market.toUpperCase()
              )
            ) {
              combined.push({
                ticker: wl.ticker,
                company_name: wl.company_name,
                market: wl.market,
              });
            }
          });
        }

        setCompaniesList(combined);
        setSelectedCompany(combined[0]);
        setCompareCompanies(combined.slice(0, 3));
      } catch {
        const fallback = DEFAULT_COMPANIES.NSE;
        setCompaniesList(fallback);
        setSelectedCompany(fallback[0]);
        setCompareCompanies(fallback.slice(0, 3));
      }
    };

    initData();
  }, []);

  // Fetch Stock Data helper
  const fetchStockData = useCallback(
    async (comp, period) => {
      if (!comp || !comp.ticker) return;
      const key = `${comp.ticker}_${comp.market}_${period}`;

      if (marketDataMap[key]) return; // already loaded

      setLoadingMap((prev) => ({ ...prev, [key]: true }));
      setErrorMap((prev) => ({ ...prev, [key]: "" }));

      try {
        const res = await getStockHistory(comp.ticker, comp.market, period);
        if (res && res.success && res.data && res.data.length) {
          setMarketDataMap((prev) => ({ ...prev, [key]: res.data }));
        } else {
          setErrorMap((prev) => ({
            ...prev,
            [key]: res?.message || "No data available",
          }));
        }
      } catch (err) {
        setErrorMap((prev) => ({
          ...prev,
          [key]: err.response?.data?.detail || "Unable to fetch stock history",
        }));
      } finally {
        setLoadingMap((prev) => ({ ...prev, [key]: false }));
      }
    },
    [marketDataMap]
  );

  // Fetch data when selectedCompany or activePeriod changes
  useEffect(() => {
    if (selectedCompany) {
      fetchStockData(selectedCompany, activePeriod);
    }
  }, [selectedCompany, activePeriod, fetchStockData]);

  // When in 'grid' view, fetch data for first 4 companies
  useEffect(() => {
    if (viewMode === "grid" && companiesList.length) {
      companiesList.slice(0, 4).forEach((comp) => {
        fetchStockData(comp, activePeriod);
      });
    }
  }, [viewMode, companiesList, activePeriod, fetchStockData]);

  // When in 'compare' view, fetch data for all compareCompanies
  useEffect(() => {
    if (viewMode === "compare" && compareCompanies.length) {
      compareCompanies.forEach((comp) => {
        fetchStockData(comp, activePeriod);
      });
    }
  }, [viewMode, compareCompanies, activePeriod, fetchStockData]);

  // Handle market change
  const handleMarketChange = (mkt) => {
    setActiveMarket(mkt);
    const list = DEFAULT_COMPANIES[mkt] || DEFAULT_COMPANIES.NSE;
    setCompaniesList(list);
    setSelectedCompany(list[0]);
    setCompareCompanies(list.slice(0, 3));
  };

  // Search Stocks
  const handleSearch = async () => {
    if (searchQuery.trim().length < 2) return;
    try {
      setSearchLoading(true);
      const res = await searchStocks(searchQuery.trim());
      setSearchResults(res.results || []);
    } catch {
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSelectSearchResult = (stock) => {
    const cleanTicker = (stock.ticker || "")
      .replace(/\.(BO|NS)$/i, "")
      .toUpperCase();
    const newComp = {
      ticker: cleanTicker,
      company_name: stock.company_name,
      market: stock.market || activeMarket,
    };

    // Add to list if not present
    if (
      !companiesList.some(
        (c) =>
          c.ticker.toUpperCase() === newComp.ticker.toUpperCase() &&
          c.market.toUpperCase() === newComp.market.toUpperCase()
      )
    ) {
      setCompaniesList((prev) => [newComp, ...prev]);
    }

    setSelectedCompany(newComp);
    if (!compareCompanies.some((c) => c.ticker === newComp.ticker)) {
      setCompareCompanies((prev) => [...prev, newComp]);
    }
    setSearchQuery("");
    setSearchResults([]);
  };

  const handleToggleCompareCompany = (comp) => {
    setCompareCompanies((prev) => {
      const exists = prev.some((c) => c.ticker === comp.ticker);
      if (exists) {
        if (prev.length <= 1) return prev; // keep at least 1
        return prev.filter((c) => c.ticker !== comp.ticker);
      }
      if (prev.length >= 6) return prev; // max 6
      return [...prev, comp];
    });
  };

  if (!user) return null;

  return (
    <DashboardLayout user={user} onLogout={logout}>
      <div className="mk-page">
        {/* Header */}
        <header className="mk-header">
          <div>
            <p className="db-eyebrow">MARKET TERMINAL</p>
            <h1 className="mk-title">
              Market <span>Explorer</span>
            </h1>
            <p className="mk-subtitle">
              Explore market trends, calculate technical indicators, and compare price performance across premier NSE &amp; BSE equities.
            </p>
          </div>

          <div className="mk-header-actions">
            <button
              className="mk-pref-btn"
              onClick={() => navigate("/dashboard/preferences")}
            >
              ⚙ Edit Preferences
            </button>
          </div>
        </header>

        {/* Preference Banner */}
        <div className="mk-pref-banner">
          <div className="mk-pref-banner-left">
            <span className="mk-banner-tag">ACTIVE PREFERENCES</span>
            <div className="mk-banner-details">
              <span>
                <strong>Market:</strong> {activeMarket}
              </span>
              <span>
                <strong>Period:</strong> {activePeriod.toUpperCase()}
              </span>
              <span>
                <strong>Risk View:</strong>{" "}
                {preferences?.preferred_risk_view || "Balanced"}
              </span>
            </div>
          </div>

          <div className="mk-pref-banner-right">
            <span className="mk-ind-title">Active Indicators:</span>
            <div className="mk-ind-pills">
              {["SMA", "EMA", "RSI", "MACD"].map((ind) => (
                <button
                  key={ind}
                  type="button"
                  className={`mk-ind-pill-interactive ${
                    activeIndicators.includes(ind) ? "active" : ""
                  }`}
                  onClick={() => handleToggleIndicator(ind)}
                  title={`Click to toggle ${ind}`}
                >
                  {ind}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Controls Toolbar: Market switch, Period switch, View toggle */}
        <div className="mk-toolbar">
          <div className="mk-toolbar-group">
            <span className="mk-toolbar-label">MARKET:</span>
            <div className="mk-btn-group">
              {["NSE", "BSE", "NASDAQ", "NYSE"].map((mkt) => (
                <button
                  key={mkt}
                  className={`mk-seg-btn ${activeMarket === mkt ? "active" : ""}`}
                  onClick={() => handleMarketChange(mkt)}
                >
                  {mkt}
                </button>
              ))}
            </div>
          </div>

          <div className="mk-toolbar-group">
            <span className="mk-toolbar-label">PERIOD:</span>
            <div className="mk-btn-group">
              {["1mo", "3mo", "6mo", "1y", "5y"].map((p) => (
                <button
                  key={p}
                  className={`mk-seg-btn ${activePeriod === p ? "active" : ""}`}
                  onClick={() => setActivePeriod(p)}
                >
                  {p.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="mk-toolbar-group mk-view-toggle">
            <span className="mk-toolbar-label">VIEW:</span>
            <div className="mk-btn-group">
              <button
                className={`mk-seg-btn ${viewMode === "focus" ? "active" : ""}`}
                onClick={() => setViewMode("focus")}
              >
                Medium Focus
              </button>
              <button
                className={`mk-seg-btn ${viewMode === "grid" ? "active" : ""}`}
                onClick={() => setViewMode("grid")}
              >
                Medium Grid
              </button>
              <button
                className={`mk-seg-btn ${viewMode === "compare" ? "active" : ""}`}
                onClick={() => setViewMode("compare")}
              >
                Compare Performance
              </button>
            </div>
          </div>
        </div>

        {/* Company Quick-Selection Ribbon */}
        <div className="mk-company-ribbon">
          <span className="mk-ribbon-label">
            {viewMode === "compare" ? "TOGGLE COMPARISON:" : "SELECT COMPANY:"}
          </span>
          <div className="mk-chips-scroll">
            {companiesList.map((comp) => {
              const isSelected =
                selectedCompany &&
                selectedCompany.ticker === comp.ticker &&
                selectedCompany.market === comp.market;

              const isCompared = compareCompanies.some(
                (c) => c.ticker === comp.ticker
              );

              return (
                <button
                  key={`${comp.ticker}-${comp.market}`}
                  className={`mk-company-chip ${
                    viewMode === "compare"
                      ? isCompared
                        ? "active"
                        : ""
                      : isSelected
                      ? "active"
                      : ""
                  }`}
                  onClick={() => {
                    if (viewMode === "compare") {
                      handleToggleCompareCompany(comp);
                    } else {
                      setSelectedCompany(comp);
                    }
                  }}
                >
                  <strong>{comp.ticker}</strong>
                  <span>{comp.company_name}</span>
                  {viewMode === "compare" && (
                    <small className="mk-chip-check">
                      {isCompared ? "✓" : "+"}
                    </small>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Search row to pick any custom company */}
        <div className="mk-search-bar-row">
          <input
            type="search"
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            spellCheck="false"
            name="market-search"
            id="market-search"
            className="db-input"
            placeholder="Search company or ticker (e.g. TCS, Reliance, AAPL, MSFT, KO)..."
            value={searchQuery}
            onChange={(e) => {
              const val = e.target.value;
              setSearchQuery(val);
              if (val.trim() === "") setSearchResults([]);
            }}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <button
            className="db-btn-primary"
            onClick={handleSearch}
            disabled={searchLoading}
          >
            {searchLoading ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Search dropdown results */}
        {searchResults.length > 0 && (
          <div className="mk-search-dropdown">
            <p className="db-results-label">
              Select a company to add to your market exploration:
            </p>
            {searchResults.map((stk) => (
              <div
                key={`${stk.ticker}-${stk.market}`}
                className="mk-search-result-item"
                onClick={() => handleSelectSearchResult(stk)}
              >
                <div>
                  <strong>{stk.company_name}</strong>
                  <span>
                    {stk.ticker} · {stk.market} ({stk.sector || "General"})
                  </span>
                </div>
                <button className="mk-select-btn">Explore →</button>
              </div>
            ))}
          </div>
        )}

        {/* CHARTS CONTAINER */}
        {viewMode === "focus" ? (
          /* SINGLE FOCUSED MEDIUM GRAPH WITH INDICATORS */
          <div className="mk-focus-container">
            {selectedCompany ? (
              <MediumStockChart
                company={selectedCompany}
                data={
                  marketDataMap[
                    `${selectedCompany.ticker}_${selectedCompany.market}_${activePeriod}`
                  ]
                }
                loading={
                  loadingMap[
                    `${selectedCompany.ticker}_${selectedCompany.market}_${activePeriod}`
                  ]
                }
                error={
                  errorMap[
                    `${selectedCompany.ticker}_${selectedCompany.market}_${activePeriod}`
                  ]
                }
                period={activePeriod}
                activeIndicators={activeIndicators}
                onToggleIndicator={handleToggleIndicator}
                width={860}
                height={260}
              />
            ) : (
              <div className="db-empty">
                <span className="db-empty-icon">📈</span>
                <h3>No company selected</h3>
                <p>Pick a company from the ribbon above to view its graph.</p>
              </div>
            )}
          </div>
        ) : viewMode === "grid" ? (
          /* MULTIPLE MEDIUM GRAPHS GRID */
          <div className="mk-grid-container">
            {companiesList.slice(0, 4).map((comp) => {
              const key = `${comp.ticker}_${comp.market}_${activePeriod}`;
              return (
                <MediumStockChart
                  key={key}
                  company={comp}
                  data={marketDataMap[key]}
                  loading={loadingMap[key]}
                  error={errorMap[key]}
                  period={activePeriod}
                  activeIndicators={activeIndicators}
                  onToggleIndicator={handleToggleIndicator}
                  width={560}
                  height={220}
                />
              );
            })}
          </div>
        ) : (
          /* MULTI-COMPANY RELATIVE PERFORMANCE COMPARISON */
          <MultiCompanyComparison
            companies={compareCompanies}
            marketDataMap={marketDataMap}
            loadingMap={loadingMap}
            activePeriod={activePeriod}
            onRemoveCompany={handleToggleCompareCompany}
            width={940}
            height={340}
          />
        )}
      </div>
    </DashboardLayout>
  );
}

export default Markets;
