import { useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import { SlidersHorizontal, Activity } from 'lucide-react';

const periods = [
  { label: '1M', value: '1mo' },
  { label: '3M', value: '3mo' },
  { label: '6M', value: '6mo' },
  { label: '1Y', value: '1y' },
  { label: '5Y', value: '5y' },
];

const INDICATOR_CONFIGS = [
  { key: 'sma_20', label: 'SMA 20', color: '#06b6d4', group: 'ma' },
  { key: 'sma_50', label: 'SMA 50', color: '#f59e0b', group: 'ma' },
  { key: 'sma_200', label: 'SMA 200', color: '#ef4444', group: 'ma' },
  { key: 'ema_12', label: 'EMA 12', color: '#10b981', group: 'ma' },
  { key: 'ema_26', label: 'EMA 26', color: '#8b5cf6', group: 'ma' },
  { key: 'ema_50', label: 'EMA 50', color: '#ec4899', group: 'ma' },
];

const PriceTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const p = payload[0]?.payload || {};
    return (
      <div className="bg-[#0a0e1a]/95 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-2xl text-xs space-y-1 z-50">
        <p className="text-slate-400 font-medium">{label}</p>
        <p className="text-white font-bold text-sm">
          Price: ${p.close?.toFixed(2)}
        </p>
        {p.open != null && <p className="text-slate-300">Open: ${p.open?.toFixed(2)}</p>}
        {p.high != null && <p className="text-emerald-400">High: ${p.high?.toFixed(2)}</p>}
        {p.low != null && <p className="text-rose-400">Low: ${p.low?.toFixed(2)}</p>}
        {payload.map((item) => {
          if (item.dataKey === 'close') return null;
          return (
            <p key={item.dataKey} style={{ color: item.color }}>
              {item.name}: ${Number(item.value)?.toFixed(2)}
            </p>
          );
        })}
      </div>
    );
  }
  return null;
};

const RSITooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const val = payload[0]?.value;
    return (
      <div className="bg-[#0a0e1a]/95 backdrop-blur-xl border border-white/10 rounded-lg p-2 text-xs shadow-xl">
        <span className="text-slate-400">{label} | </span>
        <span className="text-purple-400 font-bold">RSI(14): {Number(val)?.toFixed(1)}</span>
      </div>
    );
  }
  return null;
};

const MACDTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const p = payload[0]?.payload || {};
    return (
      <div className="bg-[#0a0e1a]/95 backdrop-blur-xl border border-white/10 rounded-lg p-2 text-xs shadow-xl space-y-0.5">
        <p className="text-slate-400">{label}</p>
        <p className="text-blue-400">MACD: {p.macd?.toFixed(3)}</p>
        <p className="text-amber-400">Signal: {p.macd_signal?.toFixed(3)}</p>
        <p className={p.macd_hist >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
          Hist: {p.macd_hist?.toFixed(3)}
        </p>
      </div>
    );
  }
  return null;
};

const StockChart = ({ data, selectedPeriod, onPeriodChange, symbol }) => {
  const [activeIndicators, setActiveIndicators] = useState({
    sma_20: true,
    sma_50: true,
    sma_200: false,
    ema_12: false,
    ema_26: false,
    ema_50: false,
    showRSI: true,
    showMACD: true,
  });

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        No chart data available
      </div>
    );
  }

  const toggleIndicator = (key) => {
    setActiveIndicators((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const firstPrice = data[0]?.close;
  const lastPrice = data[data.length - 1]?.close;
  const isPositive = lastPrice >= firstPrice;
  const lineColor = isPositive ? '#10b981' : '#ef4444';

  return (
    <div className="space-y-4">
      {/* Controls row */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Period Selector */}
        <div className="flex items-center gap-1.5 bg-white/[0.03] p-1 rounded-xl border border-white/5">
          {periods.map((p) => (
            <button
              key={p.value}
              onClick={() => onPeriodChange(p.value)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                selectedPeriod === p.value
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Technical Indicators Toggle Bar */}
        <div className="flex flex-wrap items-center gap-1.5 bg-white/[0.03] p-1 rounded-xl border border-white/5">
          <div className="flex items-center gap-1 px-2 text-[11px] font-semibold uppercase text-slate-400">
            <SlidersHorizontal className="w-3.5 h-3.5 text-cyan-400" /> Overlays:
          </div>
          {INDICATOR_CONFIGS.map((cfg) => {
            const isActive = activeIndicators[cfg.key];
            return (
              <button
                key={cfg.key}
                onClick={() => toggleIndicator(cfg.key)}
                className={`px-2.5 py-1 text-[11px] font-medium rounded-lg border transition-all ${
                  isActive
                    ? 'border-transparent text-white font-semibold'
                    : 'border-white/5 text-slate-500 hover:text-slate-300'
                }`}
                style={{
                  backgroundColor: isActive ? `${cfg.color}25` : 'transparent',
                  borderColor: isActive ? cfg.color : undefined,
                }}
              >
                <span
                  className="inline-block w-2 h-2 rounded-full mr-1.5"
                  style={{ backgroundColor: cfg.color }}
                />
                {cfg.label}
              </button>
            );
          })}

          <button
            onClick={() => toggleIndicator('showRSI')}
            className={`px-2.5 py-1 text-[11px] font-medium rounded-lg border transition-all ${
              activeIndicators.showRSI
                ? 'bg-purple-500/20 border-purple-500 text-purple-300 font-semibold'
                : 'border-white/5 text-slate-500 hover:text-slate-300'
            }`}
          >
            RSI (14)
          </button>
          <button
            onClick={() => toggleIndicator('showMACD')}
            className={`px-2.5 py-1 text-[11px] font-medium rounded-lg border transition-all ${
              activeIndicators.showMACD
                ? 'bg-cyan-500/20 border-cyan-500 text-cyan-300 font-semibold'
                : 'border-white/5 text-slate-500 hover:text-slate-300'
            }`}
          >
            MACD
          </button>
        </div>
      </div>

      {/* Main Price Chart */}
      <div className="w-full h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
            <defs>
              <linearGradient id={`gradient-${symbol}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={lineColor} stopOpacity={0.25} />
                <stop offset="100%" stopColor={lineColor} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={false}
              tickFormatter={(val) => {
                const d = new Date(val);
                return `${d.getMonth() + 1}/${d.getDate()}`;
              }}
              minTickGap={40}
            />
            <YAxis
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={false}
              domain={['auto', 'auto']}
              tickFormatter={(val) => `$${val?.toFixed(0)}`}
            />
            <Tooltip content={<PriceTooltip />} />
            <Area
              type="monotone"
              dataKey="close"
              name="Price"
              stroke={lineColor}
              strokeWidth={2}
              fill={`url(#gradient-${symbol})`}
              dot={false}
              activeDot={{ r: 5, fill: lineColor, stroke: '#0a0e1a', strokeWidth: 2 }}
            />
            {INDICATOR_CONFIGS.map((cfg) => {
              if (!activeIndicators[cfg.key]) return null;
              return (
                <Line
                  key={cfg.key}
                  type="monotone"
                  dataKey={cfg.key}
                  name={cfg.label}
                  stroke={cfg.color}
                  strokeWidth={1.5}
                  dot={false}
                  isAnimationActive={false}
                />
              );
            })}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* RSI Sub-Chart */}
      {activeIndicators.showRSI && (
        <div className="pt-2 border-t border-white/5">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1 px-2">
            <span className="font-semibold text-purple-300">RSI (14-day Wilder Smoothing)</span>
            <span className="text-[10px]">Overbought 70 / Oversold 30</span>
          </div>
          <div className="w-full h-[110px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <YAxis
                  domain={[0, 100]}
                  ticks={[30, 50, 70]}
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                  tickLine={false}
                  orientation="right"
                />
                <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.6} />
                <ReferenceLine y={50} stroke="#64748b" strokeDasharray="2 2" strokeOpacity={0.3} />
                <ReferenceLine y={30} stroke="#10b981" strokeDasharray="3 3" strokeOpacity={0.6} />
                <Tooltip content={<RSITooltip />} />
                <Line
                  type="monotone"
                  dataKey="rsi_14"
                  stroke="#a855f7"
                  strokeWidth={1.8}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* MACD Sub-Chart */}
      {activeIndicators.showMACD && (
        <div className="pt-2 border-t border-white/5">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1 px-2">
            <span className="font-semibold text-cyan-300">MACD (12, 26, 9)</span>
            <span className="text-[10px]">MACD (Blue) | Signal (Amber) | Histogram</span>
          </div>
          <div className="w-full h-[120px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                  tickLine={false}
                  orientation="right"
                />
                <Tooltip content={<MACDTooltip />} />
                <ReferenceLine y={0} stroke="rgba(255,255,255,0.15)" />
                <Bar
                  dataKey="macd_hist"
                  name="Histogram"
                  shape={(props) => {
                    const { x, y, width, height, value } = props;
                    const fill = value >= 0 ? '#10b981' : '#ef4444';
                    return <rect x={x} y={y} width={width} height={height} fill={fill} rx={1} />;
                  }}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="macd"
                  name="MACD"
                  stroke="#38bdf8"
                  strokeWidth={1.5}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="macd_signal"
                  name="Signal"
                  stroke="#fbbf24"
                  strokeWidth={1.5}
                  dot={false}
                  isAnimationActive={false}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default StockChart;
