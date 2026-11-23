import React, { useState, useMemo } from 'react';
import { 
  TrendingUp, TrendingDown, BarChart2, DollarSign, Activity, 
  ArrowUpRight, ArrowDownRight, Calendar, Download, Layers, 
  Table, FileText, Sparkles, AlertCircle, Printer, Bookmark, 
  Check, Info, Award
} from 'lucide-react';

/**
 * Intelligent parser to extract structured metrics from raw markdown notes
 * used as a resilient fallback for existing legacy reports in the database.
 */
function parseLegacyNotes(text) {
  if (!text || typeof text !== 'string') return {};

  const getMatch = (regex) => {
    const m = text.match(regex);
    return m ? m[1].trim() : null;
  };

  const parseNum = (val) => {
    if (!val || val === 'N/A') return null;
    const clean = val.replace(/,/g, '').replace(/[^\d.-]/g, '');
    const n = parseFloat(clean);
    return isNaN(n) ? null : n;
  };

  const periodReturn = parseNum(getMatch(/Cumulative Period Return\*\*:\s*([+-]?[\d.]+)%/i));
  const startPrice = parseNum(getMatch(/Initial Price\*\*:\s*([\d.,]+)/i));
  const endPrice = parseNum(getMatch(/Latest Close Price\*\*:\s*([\d.,]+)/i));
  const highLow = getMatch(/Period High \/ Low\*\*:\s*([\d.,]+)\s*\/\s*([\d.,]+)/i);
  const highestPrice = highLow ? parseNum(highLow[1]) : null;
  const lowestPrice = highLow ? parseNum(highLow[2]) : null;

  const trailingPE = parseNum(getMatch(/Trailing P\/E Ratio\*\*:\s*([\d.]+)/i));
  const forwardPE = parseNum(getMatch(/Forward P\/E Ratio\*\*:\s*([\d.]+)/i));
  const trailingEPS = parseNum(getMatch(/Trailing EPS[^:]*:\s*([\d.,]+)/i));
  const targetPrice = parseNum(getMatch(/Consensus Target\*\*:\s*([\d.,]+)/i));
  const rating = getMatch(/Analyst Consensus Rating\*\*:\s*`?([A-Z_ ]+)`?/i) || 'N/A';

  const fiftyDay = parseNum(getMatch(/50-Day Moving Average\*\*:\s*([\d.,]+)/i));
  const twoHundredDay = parseNum(getMatch(/200-Day Moving Average\*\*:\s*([\d.,]+)/i));
  const fiftyTwoRange = getMatch(/52-Week Range\*\*:\s*([\d.,]+)\s*-\s*([\d.,]+)/i);
  const fiftyTwoLow = fiftyTwoRange ? parseNum(fiftyTwoRange[1]) : null;
  const fiftyTwoHigh = fiftyTwoRange ? parseNum(fiftyTwoRange[2]) : null;

  const mktCapStr = getMatch(/Market Capitalization\*\*:\s*([^\n]+)/i);

  // Extract OHLCV records: - 2026-11-13: Open 180.2 | High 182.5 | Low 179.8 | Close 181.4 | Vol 45,210,000
  const ohlcvRecords = [];
  const ohlcvRegex = /-\s*(\d{4}-\d{2}-\d{2}):\s*Open\s*([\d.,]+)\s*\|\s*High\s*([\d.,]+)\s*\|\s*Low\s*([\d.,]+)\s*\|\s*Close\s*([\d.,]+)\s*\|\s*Vol\s*([\d,]+)/gi;
  let match;
  while ((match = ohlcvRegex.exec(text)) !== null) {
    const open = parseNum(match[2]);
    const close = parseNum(match[5]);
    const chg = (open && close) ? round(close - open, 2) : 0;
    const chgPct = open ? round((chg / open) * 100, 2) : 0;
    ohlcvRecords.push({
      date: match[1],
      open,
      high: parseNum(match[3]),
      low: parseNum(match[4]),
      close,
      volume: parseInt(match[6].replace(/,/g, ''), 10) || 0,
      change: chg,
      change_pct: chgPct
    });
  }

  return {
    period_return_pct: periodReturn,
    start_price: startPrice,
    end_price: endPrice,
    highest_price: highestPrice,
    lowest_price: lowestPrice,
    market_cap_str: mktCapStr,
    trailing_pe: trailingPE,
    forward_pe: forwardPE,
    trailing_eps: trailingEPS,
    target_mean_price: targetPrice,
    recommendation_key: rating,
    fifty_day_avg: fiftyDay,
    two_hundred_day_avg: twoHundredDay,
    fifty_two_week_low: fiftyTwoLow,
    fifty_two_week_high: fiftyTwoHigh,
    recent_ohlcv: ohlcvRecords
  };
}

function round(val, dec = 2) {
  if (val === null || val === undefined || isNaN(val)) return 0;
  return Number(Math.round(val + 'e' + dec) + 'e-' + dec);
}

function formatCurrency(val, currency = 'USD') {
  if (val === null || val === undefined || isNaN(val)) return 'N/A';
  const sym = currency === 'INR' ? '₹' : '$';
  return `${sym}${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatLargeNum(val, currency = 'USD') {
  if (!val || isNaN(val)) return 'N/A';
  const sym = currency === 'INR' ? '₹' : '$';
  const num = Number(val);
  if (currency === 'INR') {
    if (num >= 1e7) return `${sym}${(num / 1e7).toFixed(2)} Cr`;
    if (num >= 1e5) return `${sym}${(num / 1e5).toFixed(2)} Lakh`;
    return `${sym}${num.toLocaleString()}`;
  }
  if (num >= 1e12) return `${sym}${(num / 1e12).toFixed(2)}T`;
  if (num >= 1e9) return `${sym}${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e6) return `${sym}${(num / 1e6).toFixed(2)}M`;
  return `${sym}${num.toLocaleString()}`;
}

export default function ReportVisualizer({ report, task, onAddToWatchlist, isSavedInWatchlist }) {
  const [viewTab, setViewTab] = useState('visual'); // 'visual' | 'table' | 'notes'
  const [chartType, setChartType] = useState('line'); // 'line' | 'candlestick'
  const [hoverIndex, setHoverIndex] = useState(null);

  // Merge structured_data from backend with smart fallback parser from analyst_notes
  const metrics = useMemo(() => {
    const rawParsed = parseLegacyNotes(report?.analyst_notes);
    const backendData = report?.structured_data || {};

    const currency = backendData.currency || (task?.market === 'NSE' || task?.market === 'BSE' ? 'INR' : 'USD');
    const returnPct = backendData.period_return_pct ?? rawParsed.period_return_pct ?? 0;
    const startPrice = backendData.start_price ?? rawParsed.start_price;
    const endPrice = backendData.end_price ?? rawParsed.end_price;
    const highPrice = backendData.highest_price ?? rawParsed.highest_price ?? endPrice;
    const lowPrice = backendData.lowest_price ?? rawParsed.lowest_price ?? startPrice;
    const mktCap = backendData.market_cap || rawParsed.market_cap_str;

    const trailingPE = backendData.trailing_pe ?? rawParsed.trailing_pe;
    const forwardPE = backendData.forward_pe ?? rawParsed.forward_pe;
    const eps = backendData.trailing_eps ?? rawParsed.trailing_eps;
    const targetPrice = backendData.target_mean_price ?? rawParsed.target_mean_price;
    const rating = backendData.recommendation_key || rawParsed.recommendation_key || 'N/A';

    const fiftyDay = backendData.fifty_day_avg ?? rawParsed.fifty_day_avg;
    const twoHundredDay = backendData.two_hundred_day_avg ?? rawParsed.two_hundred_day_avg;
    const fiftyTwoHigh = backendData.fifty_two_week_high ?? rawParsed.fifty_two_week_high ?? highPrice;
    const fiftyTwoLow = backendData.fifty_two_week_low ?? rawParsed.fifty_two_week_low ?? lowPrice;

    // Use full price history if available, else recent OHLCV, else synthetic trend points
    let priceHistory = backendData.price_history || [];
    if (!priceHistory.length && rawParsed.recent_ohlcv?.length) {
      priceHistory = rawParsed.recent_ohlcv;
    }
    if (!priceHistory.length && startPrice && endPrice) {
      // Synthesize 5 visual guidepoints if only boundary prices exist
      priceHistory = [
        { date: 'Start', close: startPrice, open: startPrice, high: Math.max(startPrice, lowPrice), low: lowPrice, volume: 1000000 },
        { date: 'Low Point', close: lowPrice, open: startPrice, high: lowPrice, low: lowPrice, volume: 1200000 },
        { date: 'High Point', close: highPrice, open: lowPrice, high: highPrice, low: lowPrice, volume: 1500000 },
        { date: 'Latest', close: endPrice, open: highPrice, high: highPrice, low: endPrice, volume: 2000000 }
      ];
    }

    const recentOhlcv = backendData.recent_ohlcv?.length ? backendData.recent_ohlcv : (rawParsed.recent_ohlcv || []);

    return {
      currency,
      returnPct,
      startPrice,
      endPrice,
      highPrice,
      lowPrice,
      mktCap,
      trailingPE,
      forwardPE,
      eps,
      targetPrice,
      rating,
      fiftyDay,
      twoHundredDay,
      fiftyTwoHigh,
      fiftyTwoLow,
      priceHistory,
      recentOhlcv
    };
  }, [report, task]);

  // Calculate 52-week position percentage (0 to 100%)
  const fiftyTwoPosPct = useMemo(() => {
    if (!metrics.fiftyTwoLow || !metrics.fiftyTwoHigh || !metrics.endPrice) return 50;
    const range = metrics.fiftyTwoHigh - metrics.fiftyTwoLow;
    if (range <= 0) return 50;
    const pct = ((metrics.endPrice - metrics.fiftyTwoLow) / range) * 100;
    return Math.max(2, Math.min(98, Math.round(pct)));
  }, [metrics]);

  // Rating badge styling
  const ratingStyle = useMemo(() => {
    const r = (metrics.rating || '').toUpperCase();
    if (r.includes('STRONG BUY')) return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50';
    if (r.includes('BUY')) return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
    if (r.includes('HOLD')) return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
    if (r.includes('SELL') || r.includes('UNDERPERFORM')) return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
    return 'bg-slate-800 text-slate-300 border-slate-700';
  }, [metrics.rating]);

  // Target price upside calculation
  const targetUpside = useMemo(() => {
    if (!metrics.targetPrice || !metrics.endPrice || metrics.endPrice === 0) return null;
    const diff = ((metrics.targetPrice - metrics.endPrice) / metrics.endPrice) * 100;
    return round(diff, 1);
  }, [metrics.targetPrice, metrics.endPrice]);

  // Download price history as CSV
  const handleExportCSV = () => {
    const dataToExport = metrics.recentOhlcv.length ? metrics.recentOhlcv : metrics.priceHistory;
    if (!dataToExport || !dataToExport.length) return;

    const headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change', 'Change_Percent'];
    const rows = dataToExport.map(r => [
      r.date,
      r.open ?? '',
      r.high ?? '',
      r.low ?? '',
      r.close ?? '',
      r.volume ?? '',
      r.change ?? '',
      r.change_pct ?? ''
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${task?.ticker || 'STOCK'}_Research_Report_${task?.requested_period || 'History'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // SVG Chart Geometry Calculations
  const chartGeometry = useMemo(() => {
    const data = metrics.priceHistory;
    if (!data || data.length < 2) return null;

    const width = 680;
    const height = 210;
    const padX = 40;
    const padTop = 20;
    const padBottom = 35;
    const usableWidth = width - padX * 2;
    const usableHeight = height - padTop - padBottom;

    const prices = data.map(d => d.close).filter(p => p !== null && !isNaN(p));
    if (!prices.length) return null;

    const minPrice = Math.min(...prices) * 0.99;
    const maxPrice = Math.max(...prices) * 1.01;
    const priceRange = maxPrice - minPrice || 1;

    const volumes = data.map(d => d.volume || 0);
    const maxVolume = Math.max(...volumes, 1);

    const points = data.map((d, i) => {
      const x = padX + (i / (data.length - 1)) * usableWidth;
      const y = padTop + usableHeight - ((d.close - minPrice) / priceRange) * usableHeight;
      const volHeight = ((d.volume || 0) / maxVolume) * 45;
      const volY = height - padBottom - volHeight;
      return { x, y, volY, volHeight, ...d };
    });

    const pathD = points.reduce((acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)},${p.y.toFixed(1)}`, '');
    const firstPoint = points[0];
    const lastPoint = points[points.length - 1];
    const areaD = `${pathD} L ${lastPoint.x.toFixed(1)},${(height - padBottom).toFixed(1)} L ${firstPoint.x.toFixed(1)},${(height - padBottom).toFixed(1)} Z`;

    return {
      width,
      height,
      padX,
      padTop,
      padBottom,
      minPrice,
      maxPrice,
      points,
      pathD,
      areaD
    };
  }, [metrics.priceHistory]);

  const isPositiveReturn = (metrics.returnPct || 0) >= 0;

  return (
    <div className="space-y-4">
      {/* 1. Header Control & Navigation Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-900/90 border border-slate-800 rounded-xl">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-950/80 rounded-lg border border-slate-800/80">
          <button
            type="button"
            onClick={() => setViewTab('visual')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md flex items-center gap-1.5 transition ${
              viewTab === 'visual'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <BarChart2 size={13} />
            <span>Interactive Visuals</span>
          </button>

          <button
            type="button"
            onClick={() => setViewTab('table')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md flex items-center gap-1.5 transition ${
              viewTab === 'table'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Table size={13} />
            <span>OHLCV Table</span>
            {metrics.recentOhlcv.length > 0 && (
              <span className="ml-1 px-1.5 py-0.2 bg-blue-900/60 text-blue-200 rounded text-[10px]">
                {metrics.recentOhlcv.length}
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={() => setViewTab('notes')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md flex items-center gap-1.5 transition ${
              viewTab === 'notes'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <FileText size={13} />
            <span>Dossier Notes</span>
          </button>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {/* Add to Watchlist */}
          {onAddToWatchlist && (
            <button
              type="button"
              onClick={() => onAddToWatchlist({
                ticker: task?.ticker,
                name: task?.company_name,
                market: task?.market
              })}
              disabled={isSavedInWatchlist}
              className={`px-2.5 py-1 text-xs rounded-lg font-medium flex items-center gap-1.5 transition ${
                isSavedInWatchlist
                  ? 'bg-slate-800 text-slate-400 border border-slate-700 cursor-not-allowed'
                  : 'bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-800'
              }`}
            >
              <Bookmark size={12} className={isSavedInWatchlist ? 'fill-slate-400' : ''} />
              <span>{isSavedInWatchlist ? 'Saved in Watchlist' : '+ Watchlist'}</span>
            </button>
          )}

          {/* Export CSV */}
          <button
            type="button"
            onClick={handleExportCSV}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg border border-slate-700 flex items-center gap-1.5 transition"
            title="Download OHLCV history as CSV"
          >
            <Download size={12} />
            <span>CSV</span>
          </button>

          {/* Print */}
          <button
            type="button"
            onClick={() => window.print()}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg border border-slate-700 flex items-center gap-1.5 transition"
            title="Print equity research dossier"
          >
            <Printer size={12} />
            <span>Print</span>
          </button>
        </div>
      </div>

      {/* 2. Executive Summary Banner */}
      {report?.summary && (
        <div className="p-3.5 bg-gradient-to-r from-blue-950/40 to-slate-900/60 border border-blue-900/50 rounded-xl">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-blue-400 mb-1">
            <Sparkles size={14} /> Executive Summary
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            {report.summary}
          </p>
        </div>
      )}

      {/* TAB 1: INTERACTIVE VISUAL DASHBOARD */}
      {viewTab === 'visual' && (
        <div className="space-y-4">
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
            {/* 1. Period Return */}
            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col justify-between">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">Period Return</span>
              <div className="my-1 flex items-baseline gap-1.5">
                <span className={`text-lg font-extrabold ${isPositiveReturn ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {metrics.returnPct !== null ? `${metrics.returnPct > 0 ? '+' : ''}${metrics.returnPct}%` : 'N/A'}
                </span>
                {isPositiveReturn ? (
                  <ArrowUpRight size={16} className="text-emerald-400" />
                ) : (
                  <ArrowDownRight size={16} className="text-rose-400" />
                )}
              </div>
              <span className="text-[10px] text-slate-500 font-mono">{task?.requested_period || 'Period'}</span>
            </div>

            {/* 2. Latest Price */}
            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col justify-between">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">Latest Price</span>
              <div className="my-1">
                <span className="text-lg font-extrabold text-white">
                  {formatCurrency(metrics.endPrice, metrics.currency)}
                </span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                Start: {formatCurrency(metrics.startPrice, metrics.currency)}
              </span>
            </div>

            {/* 3. Market Cap */}
            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col justify-between">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">Market Cap</span>
              <div className="my-1">
                <span className="text-base font-bold text-slate-200">
                  {typeof metrics.mktCap === 'number'
                    ? formatLargeNum(metrics.mktCap, metrics.currency)
                    : (metrics.mktCap || 'N/A')}
                </span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">{metrics.currency} Valuation</span>
            </div>

            {/* 4. Consensus Rating */}
            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col justify-between">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">Analyst Stance</span>
              <div className="my-1">
                <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold tracking-wider border ${ratingStyle}`}>
                  {metrics.rating}
                </span>
              </div>
              <span className="text-[10px] text-slate-500">Wall St. Consensus</span>
            </div>

            {/* 5. Target Price */}
            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col justify-between">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">Mean Target</span>
              <div className="my-1 flex items-baseline gap-1">
                <span className="text-base font-bold text-slate-200">
                  {formatCurrency(metrics.targetPrice, metrics.currency)}
                </span>
                {targetUpside !== null && (
                  <span className={`text-[10px] font-bold ${targetUpside >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    ({targetUpside >= 0 ? '+' : ''}{targetUpside}%)
                  </span>
                )}
              </div>
              <span className="text-[10px] text-slate-500">12-Mo Estimate</span>
            </div>

            {/* 6. P/E Multiple */}
            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col justify-between">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">P/E Multiple</span>
              <div className="my-1">
                <span className="text-base font-bold text-slate-200">
                  {metrics.trailingPE ? `${metrics.trailingPE}x` : 'N/A'}
                </span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                Fwd: {metrics.forwardPE ? `${metrics.forwardPE}x` : 'N/A'}
              </span>
            </div>
          </div>

          {/* Interactive SVG Chart Panel */}
          <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5">
              <div className="flex items-center gap-2">
                <TrendingUp size={15} className={isPositiveReturn ? 'text-emerald-400' : 'text-rose-400'} />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Historical Price Trend & Volume Activity
                </span>
                <span className="text-[11px] text-slate-400 font-mono">({task?.requested_period})</span>
              </div>

              {/* Chart Legend & Toggles */}
              <div className="flex items-center gap-2 text-[11px]">
                <span className="flex items-center gap-1 text-slate-400">
                  <span className="w-2.5 h-0.5 bg-blue-500 inline-block rounded" /> Close Price
                </span>
                <span className="flex items-center gap-1 text-slate-400">
                  <span className="w-2.5 h-2 bg-slate-700 inline-block rounded" /> Volume
                </span>
              </div>
            </div>

            {/* SVG Chart */}
            {chartGeometry ? (
              <div className="relative w-full overflow-hidden select-none">
                <svg
                  viewBox={`0 0 ${chartGeometry.width} ${chartGeometry.height}`}
                  className="w-full h-52 overflow-visible"
                  onMouseLeave={() => setHoverIndex(null)}
                >
                  <defs>
                    <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={isPositiveReturn ? '#10b981' : '#f43f5e'} stopOpacity="0.35" />
                      <stop offset="100%" stopColor={isPositiveReturn ? '#10b981' : '#f43f5e'} stopOpacity="0.0" />
                    </linearGradient>
                  </defs>

                  {/* Horizontal Grid lines */}
                  <line
                    x1={chartGeometry.padX}
                    y1={chartGeometry.padTop}
                    x2={chartGeometry.width - chartGeometry.padX}
                    y2={chartGeometry.padTop}
                    stroke="#1e293b"
                    strokeDasharray="4 4"
                  />
                  <line
                    x1={chartGeometry.padX}
                    y1={chartGeometry.height - chartGeometry.padBottom}
                    x2={chartGeometry.width - chartGeometry.padX}
                    y2={chartGeometry.height - chartGeometry.padBottom}
                    stroke="#334155"
                  />

                  {/* Volume Histogram Bars */}
                  {chartGeometry.points.map((p, i) => (
                    <rect
                      key={`vol-${i}`}
                      x={p.x - 2}
                      y={p.volY}
                      width="4"
                      height={Math.max(1, p.volHeight)}
                      fill="#334155"
                      opacity={hoverIndex === i ? '0.9' : '0.45'}
                    />
                  ))}

                  {/* Gradient Area under Price Line */}
                  <path d={chartGeometry.areaD} fill="url(#priceGradient)" />

                  {/* Main Price Line */}
                  <path
                    d={chartGeometry.pathD}
                    fill="none"
                    stroke={isPositiveReturn ? '#10b981' : '#f43f5e'}
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />

                  {/* Hover Interaction Crosshair & Data Point */}
                  {chartGeometry.points.map((p, i) => (
                    <g key={`point-${i}`}>
                      {/* Transparent hit area */}
                      <rect
                        x={p.x - (chartGeometry.width / chartGeometry.points.length) / 2}
                        y={0}
                        width={chartGeometry.width / chartGeometry.points.length}
                        height={chartGeometry.height}
                        fill="transparent"
                        className="cursor-crosshair"
                        onMouseEnter={() => setHoverIndex(i)}
                      />

                      {hoverIndex === i && (
                        <g>
                          {/* Vertical guide line */}
                          <line
                            x1={p.x}
                            y1={chartGeometry.padTop}
                            x2={p.x}
                            y2={chartGeometry.height - chartGeometry.padBottom}
                            stroke="#60a5fa"
                            strokeWidth="1"
                            strokeDasharray="3 3"
                          />
                          {/* Highlighted point circle */}
                          <circle
                            cx={p.x}
                            y={p.y}
                            r="5"
                            fill="#60a5fa"
                            stroke="#ffffff"
                            strokeWidth="2"
                          />
                        </g>
                      )}
                    </g>
                  ))}

                  {/* Min / Max Labels */}
                  <text
                    x={chartGeometry.padX}
                    y={chartGeometry.padTop - 6}
                    fill="#94a3b8"
                    fontSize="10"
                    fontWeight="500"
                  >
                    High: {formatCurrency(chartGeometry.maxPrice, metrics.currency)}
                  </text>
                  <text
                    x={chartGeometry.padX}
                    y={chartGeometry.height - chartGeometry.padBottom + 16}
                    fill="#94a3b8"
                    fontSize="10"
                    fontWeight="500"
                  >
                    Low: {formatCurrency(chartGeometry.minPrice, metrics.currency)}
                  </text>

                  {/* Date boundary labels */}
                  <text
                    x={chartGeometry.padX}
                    y={chartGeometry.height - 8}
                    fill="#64748b"
                    fontSize="10"
                  >
                    {chartGeometry.points[0]?.date || 'Start'}
                  </text>
                  <text
                    x={chartGeometry.width - chartGeometry.padX}
                    y={chartGeometry.height - 8}
                    textAnchor="end"
                    fill="#64748b"
                    fontSize="10"
                  >
                    {chartGeometry.points[chartGeometry.points.length - 1]?.date || 'Latest'}
                  </text>
                </svg>

                {/* Floating Tooltip */}
                {hoverIndex !== null && chartGeometry.points[hoverIndex] && (
                  <div
                    className="absolute top-2 pointer-events-none z-10 px-3 py-2 bg-slate-900/95 border border-blue-500/50 rounded-lg shadow-xl text-xs space-y-0.5 transition-all"
                    style={{
                      left: Math.min(chartGeometry.width - 150, Math.max(10, chartGeometry.points[hoverIndex].x - 60))
                    }}
                  >
                    <div className="font-semibold text-slate-200">
                      {chartGeometry.points[hoverIndex].date}
                    </div>
                    <div className="font-bold text-white text-sm">
                      {formatCurrency(chartGeometry.points[hoverIndex].close, metrics.currency)}
                    </div>
                    {chartGeometry.points[hoverIndex].volume > 0 && (
                      <div className="text-[10px] text-slate-400">
                        Vol: {Number(chartGeometry.points[hoverIndex].volume).toLocaleString()}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                Insufficient price history data points to plot chart curve.
              </div>
            )}
          </div>

          {/* 52-Week Range Visual Gauge & Technical Indicators */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* 52-Week Price Range Slider */}
            <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                  <Activity size={14} className="text-blue-400" /> 52-Week Trading Range
                </span>
                <span className="text-[11px] font-bold text-slate-400">
                  {fiftyTwoPosPct}% of Range
                </span>
              </div>

              {/* Slider Track */}
              <div className="relative pt-3 pb-1">
                <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden flex">
                  <div 
                    className="h-full bg-gradient-to-r from-rose-500 via-amber-500 to-emerald-500 rounded-full" 
                    style={{ width: '100%' }}
                  />
                </div>
                {/* Current Price Pin Marker */}
                <div 
                  className="absolute top-1 transform -translate-x-1/2 flex flex-col items-center"
                  style={{ left: `${fiftyTwoPosPct}%` }}
                >
                  <div className="w-3.5 h-3.5 bg-white border-2 border-blue-600 rounded-full shadow-lg" />
                </div>
              </div>

              {/* Bounds Labels */}
              <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 font-mono">
                <div>
                  <span className="block text-[10px] text-slate-500">52W Low</span>
                  <span>{formatCurrency(metrics.fiftyTwoLow, metrics.currency)}</span>
                </div>
                <div className="text-center">
                  <span className="block text-[10px] text-blue-400 font-bold">Current</span>
                  <span className="font-bold text-white">{formatCurrency(metrics.endPrice, metrics.currency)}</span>
                </div>
                <div className="text-right">
                  <span className="block text-[10px] text-slate-500">52W High</span>
                  <span>{formatCurrency(metrics.fiftyTwoHigh, metrics.currency)}</span>
                </div>
              </div>
            </div>

            {/* Technical Trend Momentum */}
            <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                  <Layers size={14} className="text-indigo-400" /> Moving Average Momentum
                </span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                  metrics.endPrice && metrics.fiftyDay && metrics.endPrice >= metrics.fiftyDay
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    : 'bg-rose-950 text-rose-300 border border-rose-800'
                }`}>
                  {metrics.endPrice && metrics.fiftyDay && metrics.endPrice >= metrics.fiftyDay ? 'Bullish Trend' : 'Bearish Trend'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1">
                <div className="p-2 bg-slate-900/80 rounded-lg border border-slate-800/80">
                  <span className="text-[10px] text-slate-400 block">50-Day Moving Avg</span>
                  <span className="text-xs font-bold text-slate-200">
                    {formatCurrency(metrics.fiftyDay, metrics.currency)}
                  </span>
                  {metrics.endPrice && metrics.fiftyDay && (
                    <span className={`text-[10px] block mt-0.5 ${metrics.endPrice >= metrics.fiftyDay ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {metrics.endPrice >= metrics.fiftyDay ? 'Above 50-DMA' : 'Below 50-DMA'}
                    </span>
                  )}
                </div>

                <div className="p-2 bg-slate-900/80 rounded-lg border border-slate-800/80">
                  <span className="text-[10px] text-slate-400 block">200-Day Moving Avg</span>
                  <span className="text-xs font-bold text-slate-200">
                    {formatCurrency(metrics.twoHundredDay, metrics.currency)}
                  </span>
                  {metrics.endPrice && metrics.twoHundredDay && (
                    <span className={`text-[10px] block mt-0.5 ${metrics.endPrice >= metrics.twoHundredDay ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {metrics.endPrice >= metrics.twoHundredDay ? 'Above 200-DMA' : 'Below 200-DMA'}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: OHLCV STRUCTURED DATA TABLE */}
      {viewTab === 'table' && (
        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Table size={14} className="text-blue-400" /> OHLCV Trading Sessions
              </h4>
              <p className="text-[11px] text-slate-400">
                Detailed Open, High, Low, Close and Volume records from Yahoo Finance
              </p>
            </div>
            <button
              type="button"
              onClick={handleExportCSV}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 flex items-center gap-1 transition"
            >
              <Download size={12} />
              <span>Export CSV</span>
            </button>
          </div>

          {metrics.recentOhlcv.length > 0 ? (
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 text-[11px] uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3 font-semibold">Date</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Open</th>
                    <th className="py-2.5 px-3 font-semibold text-right">High</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Low</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Close</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Day Change</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Volume</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {metrics.recentOhlcv.map((row, idx) => {
                    const isUp = (row.change ?? 0) >= 0;
                    return (
                      <tr key={idx} className="hover:bg-slate-900/60 transition">
                        <td className="py-2 px-3 font-semibold text-white whitespace-nowrap">{row.date}</td>
                        <td className="py-2 px-3 text-right">{formatCurrency(row.open, metrics.currency)}</td>
                        <td className="py-2 px-3 text-right text-emerald-400">{formatCurrency(row.high, metrics.currency)}</td>
                        <td className="py-2 px-3 text-right text-rose-400">{formatCurrency(row.low, metrics.currency)}</td>
                        <td className="py-2 px-3 text-right font-bold text-white">{formatCurrency(row.close, metrics.currency)}</td>
                        <td className="py-2 px-3 text-right whitespace-nowrap">
                          {row.change !== undefined && row.change !== null ? (
                            <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              isUp ? 'bg-emerald-950/70 text-emerald-300' : 'bg-rose-950/70 text-rose-300'
                            }`}>
                              {isUp ? '+' : ''}{row.change} ({isUp ? '+' : ''}{row.change_pct}%)
                            </span>
                          ) : (
                            <span className="text-slate-500">-</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-right text-slate-400">{Number(row.volume || 0).toLocaleString()}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6 text-center text-xs text-slate-500">
              No tabular OHLCV trading sessions recorded.
            </div>
          )}
        </div>
      )}

      {/* TAB 3: DOSSIER NOTES & METHODOLOGY */}
      {viewTab === 'notes' && (
        <div className="space-y-3">
          <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <FileText size={14} className="text-blue-400" /> Comprehensive Analyst Notes & Methodology
            </h4>
            <div className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed bg-slate-900/90 p-3.5 rounded-lg border border-slate-800 max-h-96 overflow-y-auto">
              {report?.analyst_notes || 'No detailed market notes recorded.'}
            </div>
          </div>
        </div>
      )}

      {/* Limitations & Compliance Banner */}
      {report?.limitations && (
        <div className="p-3 bg-amber-950/30 border border-amber-900/50 rounded-xl text-xs text-amber-300/90 flex items-start gap-2">
          <AlertCircle size={15} className="shrink-0 mt-0.5 text-amber-400" />
          <div>
            <strong className="font-semibold block text-amber-300">Data Limitations & Provider Scope:</strong>
            <span>{report.limitations}</span>
          </div>
        </div>
      )}
    </div>
  );
}
