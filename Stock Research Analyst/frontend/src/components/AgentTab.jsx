import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Search, Loader2, Bot, TrendingUp, TrendingDown, AlertTriangle,
  DollarSign, BarChart2, Shield, Activity, Users, FileSearch,
  CheckCircle, XCircle, ChevronDown, ChevronUp, Zap
} from 'lucide-react';
import api from '../api/axios';

/* ─── Helpers ─── */
const hasVal = (v) => v !== null && v !== undefined && !(typeof v === 'number' && Number.isNaN(v));

const pct = (v, decimals = 2, showSign = false) => {
  if (!hasVal(v)) return '—';
  const n = Number(v);
  const sign = showSign && n > 0 ? '+' : '';
  return `${sign}${n.toFixed(decimals)}%`;
};

const fmt = (v, currency, decimals = 2) => {
  if (!hasVal(v)) return '—';
  const n = Number(v);
  const absN = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (currency === 'INR') {
    const cr = absN / 1e7;
    return cr >= 1e5
      ? `${sign}₹${(cr / 1e5).toFixed(decimals)}L Cr`
      : `${sign}₹${cr.toFixed(decimals)} Cr`;
  }
  const b = absN / 1e9;
  return b >= 1 ? `${sign}$${b.toFixed(decimals)}B` : `${sign}$${(absN / 1e6).toFixed(decimals)}M`;
};

const fmtPrice = (v, currency) => {
  if (!hasVal(v)) return '—';
  return currency === 'INR' ? `₹${Number(v).toLocaleString('en-IN')}` : `$${Number(v).toFixed(2)}`;
};

const fmtMarketCap = (v, currency) => {
  if (!hasVal(v)) return '—';
  const n = Number(v);
  if (currency === 'INR') {
    const cr = n / 1e7;
    return cr >= 1e5 ? `₹${(cr / 1e5).toFixed(2)}L Cr` : `₹${cr.toFixed(0)} Cr`;
  }
  return `$${(n / 1e9).toFixed(2)}B`;
};

/* ─── Badges ─── */
const profitBadge = (range) => {
  const map = {
    'Highly Profitable': 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/60',
    'Moderately Profitable': 'bg-yellow-900/50 text-yellow-300 border border-yellow-700/60',
    'Not Profitable': 'bg-red-900/50 text-red-300 border border-red-700/60',
    'Data Unavailable': 'bg-gray-800 text-gray-400 border border-gray-700',
  };
  const emoji = {
    'Highly Profitable': '🟢',
    'Moderately Profitable': '🟡',
    'Not Profitable': '🔴',
    'Data Unavailable': '⚪',
  };
  return { cls: map[range] || map['Data Unavailable'], emoji: emoji[range] || '⚪' };
};

const earningsBadge = (status) => {
  if (!status) return 'bg-gray-800 text-gray-400';
  if (status.includes('Growing')) return 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/60';
  if (status.includes('Profitable')) return 'bg-yellow-900/50 text-yellow-300 border border-yellow-700/60';
  return 'bg-red-900/50 text-red-300 border border-red-700/60';
};

const valuationBadge = (tier) => {
  if (!tier) return 'bg-gray-800 text-gray-400';
  if (tier.includes('Undervalued')) return 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/60';
  if (tier.includes('Premium') || tier.includes('Overvalued')) return 'bg-red-900/50 text-red-300 border border-red-700/60';
  return 'bg-blue-900/50 text-blue-300 border border-blue-700/60';
};

const stabilityBadge = (cat) => {
  if (!cat) return 'bg-gray-800 text-gray-400';
  if (cat.includes('High')) return 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/60';
  if (cat.includes('Moderate') || cat.includes('Medium')) return 'bg-yellow-900/50 text-yellow-300 border border-yellow-700/60';
  return 'bg-red-900/50 text-red-300 border border-red-700/60';
};

const perfBadge = (tier) => {
  if (!tier) return 'bg-gray-800 text-gray-400';
  if (tier.includes('Strong') || tier.includes('Steady')) return 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/60';
  if (tier.includes('Moderate') || tier.includes('Range')) return 'bg-blue-900/50 text-blue-300 border border-blue-700/60';
  return 'bg-red-900/50 text-red-300 border border-red-700/60';
};

const reliabilityBadge = (status) => {
  if (!status) return 'bg-gray-800 text-gray-400';
  if (status.includes('High') || status.includes('Complete')) return 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/60';
  if (status.includes('Moderate') || status.includes('Partial')) return 'bg-yellow-900/50 text-yellow-300 border border-yellow-700/60';
  return 'bg-red-900/50 text-red-300 border border-red-700/60';
};

const anomalyStyle = (type) => {
  if (type === 'Sudden Downfall') {
    return {
      pill: 'bg-red-900/50 text-red-300 border border-red-700/60',
      moveColor: 'text-red-400',
      Icon: TrendingDown,
    };
  }
  if (type === 'Sudden Surge') {
    return {
      pill: 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/60',
      moveColor: 'text-emerald-400',
      Icon: TrendingUp,
    };
  }
  if (type === 'Volume Spike') {
    return {
      pill: 'bg-amber-900/50 text-amber-300 border border-amber-700/60',
      moveColor: 'text-amber-300',
      Icon: Zap,
    };
  }
  return {
    pill: 'bg-orange-900/50 text-orange-300 border border-orange-700/60',
    moveColor: 'text-orange-400',
    Icon: AlertTriangle,
  };
};

/* ─── Reusable UI Primitives ─── */
function Card({ title, icon: Icon, children, iconColor = 'text-emerald-400' }) {
  return (
    <div className="bg-gray-900/60 border border-emerald-900/30 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
        <Icon className={`w-4 h-4 ${iconColor}`} />
        {title}
      </h3>
      {children}
    </div>
  );
}

function KV({ label, value, mono, badge }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-gray-800/60 last:border-0 gap-2">
      <span className="text-xs text-gray-400">{label}</span>
      <div className="flex items-center gap-2 text-right">
        {badge && (
          <span className="text-[11px] px-2 py-0.5 rounded bg-gray-800 text-gray-300 border border-gray-700/60">
            {badge}
          </span>
        )}
        <span className={`text-sm font-medium text-white ${mono ? 'font-mono' : ''}`}>{value}</span>
      </div>
    </div>
  );
}

function ProgressBar({ value, max = 100, colorClass = 'bg-emerald-500' }) {
  const widthPct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all ${colorClass}`}
        style={{ width: `${widthPct}%` }}
      />
    </div>
  );
}

const resolveMarket = (tkr, mkt) => {
  const valid = ['NSE', 'BSE', 'NASDAQ', 'NYSE'];
  const upperMkt = (mkt || '').toUpperCase();
  if (valid.includes(upperMkt)) return upperMkt;
  const upperTkr = (tkr || '').toUpperCase();
  if (upperTkr.endsWith('.NS')) return 'NSE';
  if (upperTkr.endsWith('.BO')) return 'BSE';
  return 'NASDAQ';
};

/* ─── Main Agent Tab ─── */
export default function AgentTab({ initialStock = null }) {
  const [ticker, setTicker] = useState(initialStock?.ticker || '');
  const [market, setMarket] = useState(
    initialStock ? resolveMarket(initialStock.ticker, initialStock.market) : 'NSE'
  );
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [showMissingFields, setShowMissingFields] = useState(false);
  const activeRequestRef = useRef(0);

  const runAnalysis = useCallback(async (targetTicker, targetMarket) => {
    const clean = (targetTicker || '').trim().toUpperCase();
    if (!clean) return;
    const reqId = ++activeRequestRef.current;
    setLoading(true);
    setData(null);
    setError(null);
    try {
      const res = await api.get(`/agent/fundamental/${encodeURIComponent(clean)}`, {
        params: { market: targetMarket },
      });
      if (reqId === activeRequestRef.current) {
        setData(res.data);
      }
    } catch (err) {
      if (reqId === activeRequestRef.current) {
        setError(err.response?.data?.detail || 'Failed to fetch analysis. Check the ticker and try again.');
      }
    } finally {
      if (reqId === activeRequestRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    if (initialStock?.ticker) {
      const resolvedMkt = resolveMarket(initialStock.ticker, initialStock.market);
      setTicker(initialStock.ticker);
      setMarket(resolvedMkt);
      runAnalysis(initialStock.ticker, resolvedMkt);
    }
  }, [initialStock?.ticker, initialStock?.market, initialStock?.requestKey, runAnalysis]);

  const analyze = async (e) => {
    e.preventDefault();
    runAnalysis(ticker, market);
  };

  const currency = data?.valuation_metrics?.currency;

  return (
    <div className="space-y-6">
      {/* Search bar */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Bot className="w-5 h-5 text-emerald-400" />
          Fundamental Analysis Agent
        </h2>
        <form onSubmit={analyze} className="flex gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="Enter ticker (e.g. RELIANCE.NS, AAPL, TCS.NS)..."
              className="w-full bg-gray-800/60 border border-gray-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-500 outline-none transition-all"
            />
          </div>
          <select
            value={market}
            onChange={(e) => setMarket(e.target.value)}
            className="bg-gray-800 border border-gray-700 focus:border-emerald-500 rounded-lg px-3 py-2.5 text-white outline-none text-sm"
          >
            {['NSE', 'BSE', 'NASDAQ', 'NYSE'].map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <button
            type="submit"
            disabled={loading || !ticker.trim()}
            className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold px-5 py-2.5 rounded-lg flex items-center gap-2 transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </form>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
          <p className="text-gray-400 text-sm">Fetching financial data and running ML analysis...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-900/20 border border-red-800/50 rounded-xl p-5 flex items-start gap-3">
          <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-300 font-medium">Analysis Failed</p>
            <p className="text-red-400/80 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {data && !loading && (
        <div className="space-y-5">

          {/* ── Company Header ── */}
          <div className="bg-gradient-to-r from-emerald-900/30 to-gray-900/60 border border-emerald-800/40 rounded-xl p-5">
            <div className="flex items-start justify-between flex-wrap gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">{data.company_name || data.ticker}</h2>
                <p className="text-sm text-gray-400 mt-0.5">
                  <span className="text-emerald-400 font-mono font-semibold">{data.ticker}</span>
                  {data.sector && data.sector !== 'N/A' && <span> · {data.sector}</span>}
                  {data.industry && data.industry !== 'N/A' && <span> · {data.industry}</span>}
                </p>
              </div>
              {(hasVal(data.valuation_metrics?.current_price) || hasVal(data.valuation_metrics?.market_cap)) && (
                <div className="text-right">
                  {hasVal(data.valuation_metrics?.current_price) && (
                    <p className="text-2xl font-bold text-emerald-300">
                      {fmtPrice(data.valuation_metrics.current_price, currency)}
                    </p>
                  )}
                  {hasVal(data.valuation_metrics?.market_cap) && (
                    <p className="text-xs text-gray-400 mt-0.5">
                      Market Cap: {fmtMarketCap(data.valuation_metrics.market_cap, currency)}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

            {/* ── Revenue & Earnings ── */}
            <Card title="Revenue & Earnings" icon={TrendingUp}>
              {(() => {
                const rev = data.revenue_and_earnings_analysis || {};
                const rows = [
                  rev.fiscal_period && rev.fiscal_period !== 'Latest Available' && {
                    label: 'Fiscal Period',
                    value: rev.fiscal_period,
                    mono: true,
                  },
                  hasVal(rev.total_revenue) && {
                    label: 'Total Revenue',
                    value: fmt(rev.total_revenue, currency),
                  },
                  hasVal(rev.revenue_yoy_growth_pct) && {
                    label: 'Revenue YoY Growth',
                    value: pct(rev.revenue_yoy_growth_pct, 2, true),
                  },
                  hasVal(rev.gross_profit) && Number(rev.gross_profit) !== 0 && {
                    label: 'Gross Profit',
                    value: fmt(rev.gross_profit, currency),
                  },
                  hasVal(rev.operating_income) && Number(rev.operating_income) !== 0 && {
                    label: 'Operating Income',
                    value: fmt(rev.operating_income, currency),
                  },
                  hasVal(rev.net_income) && {
                    label: 'Net Income',
                    value: fmt(rev.net_income, currency),
                  },
                  hasVal(rev.earnings_yoy_growth_pct) && {
                    label: 'Earnings YoY Growth',
                    value: pct(rev.earnings_yoy_growth_pct, 2, true),
                  },
                  hasVal(rev.eps) && {
                    label: 'EPS',
                    value: Number(rev.eps).toFixed(2),
                  },
                  hasVal(rev.free_cash_flow) && {
                    label: 'Free Cash Flow',
                    value: fmt(rev.free_cash_flow, currency),
                  },
                ].filter(Boolean);

                return (
                  <div className="space-y-1">
                    {rows.length > 0 ? (
                      rows.map((item) => <KV key={item.label} label={item.label} value={item.value} mono={item.mono} />)
                    ) : (
                      <p className="text-xs text-gray-500 italic">Revenue and earnings breakdown unavailable from data source.</p>
                    )}
                    {rev.earnings_status && rev.earnings_status !== 'Data Pending' && (
                      <div className="pt-2">
                        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${earningsBadge(rev.earnings_status)}`}>
                          {rev.earnings_status}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })()}
            </Card>

            {/* ── Profitability ── */}
            <Card title="Profitability Analysis" icon={DollarSign}>
              {(() => {
                const p = data.profitability_analysis || {};
                const { cls, emoji } = profitBadge(p.profitability_range);
                const rows = [
                  hasVal(p.gross_margin_pct) && { label: 'Gross Margin', value: pct(p.gross_margin_pct) },
                  hasVal(p.operating_margin_pct) && { label: 'Operating Margin', value: pct(p.operating_margin_pct) },
                  hasVal(p.net_profit_margin_pct) && { label: 'Net Profit Margin', value: pct(p.net_profit_margin_pct) },
                  hasVal(p.roe_pct) && { label: 'Return on Equity (ROE)', value: pct(p.roe_pct) },
                ].filter(Boolean);

                return (
                  <div className="space-y-1">
                    {p.profitability_range && (
                      <div className="mb-3">
                        <span className={`text-sm px-3 py-1.5 rounded-full font-semibold ${cls}`}>
                          {emoji} {p.profitability_range}
                        </span>
                      </div>
                    )}
                    {rows.map((item) => <KV key={item.label} label={item.label} value={item.value} />)}
                    {p.profitability_rationale && (
                      <p className="text-xs text-gray-500 italic mt-3 leading-relaxed border-t border-gray-800 pt-2">
                        {p.profitability_rationale}
                      </p>
                    )}
                  </div>
                );
              })()}
            </Card>

            {/* ── Debt & Financial Stability ── */}
            <Card title="Debt & Financial Stability" icon={Shield} iconColor="text-blue-400">
              {(() => {
                const d = data.debt_and_financial_stability_analysis || {};
                const hasScore = hasVal(d.financial_stability_score);
                const score = d.financial_stability_score ?? 0;
                const barColor = score >= 70 ? 'bg-emerald-500' : score >= 45 ? 'bg-yellow-500' : 'bg-red-500';
                const rows = [
                  hasVal(d.debt_to_equity_ratio) && { label: 'Debt-to-Equity (D/E)', value: Number(d.debt_to_equity_ratio).toFixed(2) },
                  hasVal(d.debt_to_assets_ratio) && { label: 'Debt-to-Assets (D/A)', value: Number(d.debt_to_assets_ratio).toFixed(2) },
                  hasVal(d.cash_to_debt_ratio) && { label: 'Cash-to-Debt Ratio', value: Number(d.cash_to_debt_ratio).toFixed(2) },
                  hasVal(d.solvency_buffer_pct) && { label: 'Solvency Buffer', value: pct(d.solvency_buffer_pct) },
                  hasVal(d.total_debt) && { label: 'Total Debt', value: fmt(d.total_debt, currency) },
                  hasVal(d.stockholders_equity) && { label: "Stockholders' Equity", value: fmt(d.stockholders_equity, currency) },
                ].filter(Boolean);

                return (
                  <div className="space-y-1">
                    {(hasScore || d.stability_category) && (
                      <div className="mb-3">
                        {hasScore && (
                          <>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-gray-400">Financial Stability Score</span>
                              <span className="text-sm font-bold text-white">{score}/100</span>
                            </div>
                            <ProgressBar value={score} colorClass={barColor} />
                          </>
                        )}
                        {d.stability_category && (
                          <span className={`mt-2 inline-block text-xs px-2.5 py-1 rounded-full font-medium ${stabilityBadge(d.stability_category)}`}>
                            {d.stability_category}
                          </span>
                        )}
                      </div>
                    )}
                    {rows.length > 0 ? (
                      rows.map((item) => <KV key={item.label} label={item.label} value={item.value} />)
                    ) : (
                      <p className="text-xs text-gray-500 italic">Balance sheet leverage metrics unavailable for this ticker.</p>
                    )}
                  </div>
                );
              })()}
            </Card>

            {/* ── Financial Ratios ── */}
            <Card title="Financial Ratios" icon={BarChart2} iconColor="text-purple-400">
              {(() => {
                const r = data.financial_ratios_calculation || {};
                const rows = [
                  hasVal(r.pe_ratio) && { label: 'P/E Ratio', value: Number(r.pe_ratio).toFixed(2) },
                  hasVal(r.forward_pe) && { label: 'Forward P/E', value: Number(r.forward_pe).toFixed(2) },
                  hasVal(r.peg_ratio) && { label: 'PEG Ratio', value: Number(r.peg_ratio).toFixed(2) },
                  hasVal(r.pb_ratio) && { label: 'P/B Ratio', value: Number(r.pb_ratio).toFixed(2) },
                  hasVal(r.roe_pct) && { label: 'ROE', value: pct(r.roe_pct) },
                ].filter(Boolean);

                return (
                  <div className="space-y-1">
                    {r.valuation_tier && (
                      <div className="mb-3">
                        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${valuationBadge(r.valuation_tier)}`}>
                          {r.valuation_tier}
                        </span>
                      </div>
                    )}
                    {rows.length > 0 ? (
                      rows.map((item) => <KV key={item.label} label={item.label} value={item.value} />)
                    ) : (
                      <p className="text-xs text-gray-500 italic">Valuation ratios unavailable for this ticker.</p>
                    )}
                  </div>
                );
              })()}
            </Card>
          </div>

          {/* ── Historical Financial Performance ── */}
          <Card title="Historical Financial Performance" icon={Activity} iconColor="text-cyan-400">
            {(() => {
              const h = data.historical_financial_performance_comparison || {};
              const rows = h.annual_financial_comparison || [];

              // Only render columns that have at least one non-null value
              const possibleCols = [
                {
                  key: 'fiscal_date',
                  label: 'Fiscal Date',
                  hasData: rows.some((r) => Boolean(r.fiscal_date)),
                  render: (r) => <span className="text-emerald-400 font-mono">{r.fiscal_date || '—'}</span>,
                },
                {
                  key: 'total_revenue',
                  label: 'Revenue',
                  hasData: rows.some((r) => hasVal(r.total_revenue)),
                  render: (r) => <span className="text-white">{fmt(r.total_revenue, currency, 1)}</span>,
                },
                {
                  key: 'revenue_yoy_growth_pct',
                  label: 'Rev YoY%',
                  hasData: rows.some((r) => hasVal(r.revenue_yoy_growth_pct)),
                  render: (r) => (
                    <span className={`font-medium ${(r.revenue_yoy_growth_pct ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {pct(r.revenue_yoy_growth_pct, 1, true)}
                    </span>
                  ),
                },
                {
                  key: 'net_income',
                  label: 'Net Income',
                  hasData: rows.some((r) => hasVal(r.net_income)),
                  render: (r) => <span className="text-gray-200">{fmt(r.net_income, currency, 1)}</span>,
                },
                {
                  key: 'net_margin_pct',
                  label: 'Net Margin%',
                  hasData: rows.some((r) => hasVal(r.net_margin_pct)),
                  render: (r) => <span className="text-gray-300">{pct(r.net_margin_pct, 1)}</span>,
                },
                {
                  key: 'roe_pct',
                  label: 'ROE%',
                  hasData: rows.some((r) => hasVal(r.roe_pct)),
                  render: (r) => <span className="text-gray-300">{pct(r.roe_pct, 1)}</span>,
                },
                {
                  key: 'debt_to_equity',
                  label: 'D/E',
                  hasData: rows.some((r) => hasVal(r.debt_to_equity)),
                  render: (r) => (
                    <span className="text-gray-300">
                      {hasVal(r.debt_to_equity) ? Number(r.debt_to_equity).toFixed(2) : '—'}
                    </span>
                  ),
                },
              ];
              const visibleCols = possibleCols.filter((c) => c.hasData);

              return (
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-6">
                    {hasVal(h.period_price_return_pct) && (
                      <div>
                        <p className="text-xs text-gray-500">Price Return ({h.market_price_sessions} sessions)</p>
                        <p className={`text-lg font-bold ${h.period_price_return_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {pct(h.period_price_return_pct, 2, true)}
                        </p>
                      </div>
                    )}
                    {hasVal(h.period_max_drawdown_pct) && (
                      <div>
                        <p className="text-xs text-gray-500">Max Drawdown</p>
                        <p className="text-lg font-bold text-red-400">{pct(h.period_max_drawdown_pct)}</p>
                      </div>
                    )}
                    {h.performance_tier && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Performance Tier</p>
                        <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${perfBadge(h.performance_tier)}`}>
                          {h.performance_tier}
                        </span>
                      </div>
                    )}
                  </div>
                  {rows.length > 0 && visibleCols.length > 0 && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-emerald-900/30">
                            {visibleCols.map((col) => (
                              <th key={col.key} className="text-left py-2 px-2 text-gray-400 font-medium uppercase tracking-wider whitespace-nowrap">
                                {col.label}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {rows.map((r, i) => (
                            <tr key={i} className="border-b border-gray-800/40 hover:bg-emerald-900/5 transition-colors">
                              {visibleCols.map((col) => (
                                <td key={col.key} className="py-2 px-2 whitespace-nowrap">
                                  {col.render(r)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              );
            })()}
          </Card>

          {/* ── Peer Comparison ── */}
          <Card title="Peer Comparison" icon={Users} iconColor="text-indigo-400">
            {(() => {
              const pc = data.peer_comparison || {};
              const peers = pc.peers || [];
              const avg = pc.peer_average || {};
              const target = {
                ticker: data.ticker,
                company_name: data.company_name,
                pe_ratio: data.financial_ratios_calculation?.pe_ratio,
                pb_ratio: data.financial_ratios_calculation?.pb_ratio,
                roe_pct: data.profitability_analysis?.roe_pct,
                net_margin_pct: data.profitability_analysis?.net_profit_margin_pct,
              };
              const allRows = [target, ...peers];
              const metricCols = [
                { key: 'pe_ratio', label: 'P/E', fmtFn: (v) => (hasVal(v) ? Number(v).toFixed(2) : '—') },
                { key: 'pb_ratio', label: 'P/B', fmtFn: (v) => (hasVal(v) ? Number(v).toFixed(2) : '—') },
                { key: 'roe_pct', label: 'ROE%', fmtFn: (v) => pct(v, 1) },
                { key: 'net_margin_pct', label: 'Net Margin%', fmtFn: (v) => pct(v, 1) },
              ].filter((col) => allRows.some((r) => hasVal(r[col.key])));

              return (
                <div className="space-y-3">
                  <p className="text-xs text-gray-400">{pc.comparison_status}</p>
                  {peers.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-emerald-900/30">
                            <th className="text-left py-2 px-2 text-gray-400 font-medium uppercase tracking-wider whitespace-nowrap">Ticker</th>
                            <th className="text-left py-2 px-2 text-gray-400 font-medium uppercase tracking-wider whitespace-nowrap">Company</th>
                            {metricCols.map((col) => (
                              <th key={col.key} className="text-left py-2 px-2 text-gray-400 font-medium uppercase tracking-wider whitespace-nowrap">
                                {col.label}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {/* Target row */}
                          <tr className="border-b border-emerald-700/40 bg-emerald-900/15">
                            <td className="py-2 px-2 text-emerald-300 font-mono font-bold whitespace-nowrap">{target.ticker}</td>
                            <td className="py-2 px-2 text-emerald-200 font-medium whitespace-nowrap">{target.company_name}</td>
                            {metricCols.map((col) => (
                              <td key={col.key} className="py-2 px-2 text-white whitespace-nowrap">{col.fmtFn(target[col.key])}</td>
                            ))}
                          </tr>
                          {/* Peers */}
                          {peers.map((p, i) => (
                            <tr key={i} className="border-b border-gray-800/40 hover:bg-emerald-900/5 transition-colors">
                              <td className="py-2 px-2 text-emerald-400 font-mono whitespace-nowrap">{p.ticker}</td>
                              <td className="py-2 px-2 text-gray-300 whitespace-nowrap">{p.company_name || p.ticker}</td>
                              {metricCols.map((col) => (
                                <td key={col.key} className="py-2 px-2 text-gray-300 whitespace-nowrap">{col.fmtFn(p[col.key])}</td>
                              ))}
                            </tr>
                          ))}
                          {/* Peer Average */}
                          {Object.keys(avg).length > 0 && metricCols.some((c) => hasVal(avg[c.key])) && (
                            <tr className="bg-gray-800/40">
                              <td colSpan={2} className="py-2 px-2 text-gray-400 font-medium italic text-xs">Peer Average</td>
                              {metricCols.map((col) => (
                                <td key={col.key} className="py-2 px-2 text-gray-300 whitespace-nowrap">{col.fmtFn(avg[col.key])}</td>
                              ))}
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm italic">No peer data available for this sector.</p>
                  )}
                  {pc.unavailable_or_missing_peers?.length > 0 && (
                    <p className="text-xs text-gray-500">
                      Unavailable peers: {pc.unavailable_or_missing_peers.join(', ')}
                    </p>
                  )}
                </div>
              );
            })()}
          </Card>

          {/* ── Data Quality & Price Anomalies ── */}
          <Card title="Data Quality & Price Anomalies" icon={FileSearch} iconColor="text-orange-400">
            {(() => {
              const dq = data.missing_or_inconsistent_financial_info || {};
              const completeness = dq.data_completeness_pct ?? 0;
              const barColor = completeness >= 70 ? 'bg-emerald-500' : completeness >= 40 ? 'bg-yellow-500' : 'bg-red-500';
              const fields = dq.missing_fields || [];
              const anomalies = dq.price_and_market_anomalies || [];
              const summary = dq.anomaly_summary || {};

              return (
                <div className="space-y-4">
                  {/* Completeness & Reliability */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-400">Financial Statement Completeness</span>
                      <span className="text-sm font-bold text-white">{completeness.toFixed(1)}%</span>
                    </div>
                    <ProgressBar value={completeness} colorClass={barColor} />
                    {dq.reliability_status && (
                      <span className={`mt-2 inline-block text-xs px-2.5 py-1 rounded-full font-medium ${reliabilityBadge(dq.reliability_status)}`}>
                        {dq.reliability_status}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-gray-800/60 rounded-lg p-3">
                      <p className="text-xs text-gray-400">Missing Fields</p>
                      <p className="text-lg font-bold text-white">{dq.missing_fields_count ?? 0}</p>
                    </div>
                    <div className="bg-gray-800/60 rounded-lg p-3">
                      <p className="text-xs text-gray-400">Sudden Downfalls</p>
                      <p className={`text-lg font-bold ${(summary.sudden_downfalls ?? 0) > 0 ? 'text-red-400' : 'text-white'}`}>
                        {summary.sudden_downfalls ?? 0}
                      </p>
                    </div>
                    <div className="bg-gray-800/60 rounded-lg p-3">
                      <p className="text-xs text-gray-400">Sudden Surges</p>
                      <p className={`text-lg font-bold ${(summary.sudden_surges ?? 0) > 0 ? 'text-emerald-400' : 'text-white'}`}>
                        {summary.sudden_surges ?? 0}
                      </p>
                    </div>
                    <div className="bg-gray-800/60 rounded-lg p-3">
                      <p className="text-xs text-gray-400">Volume Spikes</p>
                      <p className={`text-lg font-bold ${(summary.volume_spikes ?? 0) > 0 ? 'text-amber-400' : 'text-white'}`}>
                        {summary.volume_spikes ?? 0}
                      </p>
                    </div>
                  </div>

                  {/* Extreme Session Highlights */}
                  {(summary.worst_single_day || summary.best_single_day || summary.peak_volume_day) && (
                    <div className="flex flex-wrap gap-2 text-xs">
                      {summary.worst_single_day && (
                        <span className="px-2.5 py-1 rounded-lg bg-red-950/40 border border-red-900/40 text-red-300">
                          Worst 1D Drop: <strong>{summary.worst_single_day.change_pct}%</strong> on {summary.worst_single_day.date}
                        </span>
                      )}
                      {summary.best_single_day && (
                        <span className="px-2.5 py-1 rounded-lg bg-emerald-950/40 border border-emerald-900/40 text-emerald-300">
                          Best 1D Surge: <strong>+{summary.best_single_day.change_pct}%</strong> on {summary.best_single_day.date}
                        </span>
                      )}
                      {summary.peak_volume_day && (
                        <span className="px-2.5 py-1 rounded-lg bg-amber-950/40 border border-amber-900/40 text-amber-300">
                          Peak Volume: <strong>{summary.peak_volume_day.volume_ratio}x avg</strong> on {summary.peak_volume_day.date}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Price & Market Anomalies Table */}
                  <div className="bg-gray-800/40 rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                        Price & Market Anomalies (Last 250 Sessions)
                      </p>
                      <span className="text-xs text-gray-500">
                        {anomalies.length} event{anomalies.length === 1 ? '' : 's'} shown
                      </span>
                    </div>

                    {anomalies.length > 0 ? (
                      <div className="overflow-x-auto max-h-72 overflow-y-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b border-gray-700/60">
                              {['Date', 'Anomaly Type', 'Move / Vol', 'Details', 'Severity'].map((col) => (
                                <th key={col} className="text-left py-2 px-2 text-gray-400 font-medium uppercase tracking-wider whitespace-nowrap">
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {anomalies.map((a, idx) => {
                              const style = anomalyStyle(a.type);
                              const TypeIcon = style.Icon;
                              return (
                                <tr key={idx} className="border-b border-gray-800/50 last:border-0 hover:bg-gray-800/30">
                                  <td className="py-2 px-2 text-gray-300 font-mono whitespace-nowrap">{a.date}</td>
                                  <td className="py-2 px-2 whitespace-nowrap">
                                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium ${style.pill}`}>
                                      <TypeIcon className="w-3 h-3" />
                                      {a.type}
                                    </span>
                                  </td>
                                  <td className={`py-2 px-2 font-mono font-semibold whitespace-nowrap ${style.moveColor}`}>
                                    {hasVal(a.change_pct)
                                      ? `${a.change_pct > 0 ? '+' : ''}${Number(a.change_pct).toFixed(2)}%`
                                      : hasVal(a.volume_ratio)
                                        ? `${a.volume_ratio}x vol`
                                        : '—'}
                                  </td>
                                  <td className="py-2 px-2 text-gray-300 min-w-[200px]">{a.description}</td>
                                  <td className="py-2 px-2 whitespace-nowrap">
                                    <span className={`text-[11px] px-2 py-0.5 rounded font-medium ${
                                      a.severity === 'High'
                                        ? 'bg-red-900/40 text-red-300 border border-red-800/50'
                                        : 'bg-yellow-900/40 text-yellow-300 border border-yellow-800/50'
                                    }`}>
                                      {a.severity}
                                    </span>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-xs text-emerald-300/90 bg-emerald-950/30 border border-emerald-900/40 rounded-lg p-3">
                        <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        <span>No sudden downfalls (≤ -4%), sharp surges (≥ +5%), extreme volume spikes (≥ 3x), or OHLCV data glitches detected.</span>
                      </div>
                    )}
                  </div>

                  {/* Missing fields expandable */}
                  {fields.length > 0 && (
                    <div className="bg-yellow-900/15 border border-yellow-800/30 rounded-lg p-3">
                      <button
                        className="flex items-center justify-between w-full text-xs text-yellow-400 font-medium"
                        onClick={() => setShowMissingFields((s) => !s)}
                      >
                        <span>Missing Financial Fields Reported by Source ({fields.length})</span>
                        {showMissingFields ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                      {showMissingFields && (
                        <ul className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-1">
                          {fields.map((f, i) => (
                            <li key={i} className="text-xs text-yellow-500/70 font-mono">• {f}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}

                  {/* Statement Inconsistencies */}
                  {dq.inconsistencies_detected?.length > 0 && (
                    <div className="bg-red-900/15 border border-red-800/30 rounded-lg p-3">
                      <p className="text-xs font-medium text-red-400 mb-1">Financial Statement Inconsistencies</p>
                      <ul className="space-y-0.5">
                        {dq.inconsistencies_detected.map((f, i) => (
                          <li key={i} className="text-xs text-red-400/80">• {f}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })()}
          </Card>

          {/* ── Agent Verdict & Investment Outlook ── */}
          <Card title="Agent Verdict & Investment Outlook" icon={Bot} iconColor="text-emerald-400">
            {(() => {
              const ml = data.ml_agent_prediction || {};
              const signals = ml.technical_signals || {};
              const interp = ml.signal_interpretations || {};
              const prof = data.profitability_analysis || {};
              const debt = data.debt_and_financial_stability_analysis || {};
              const ratios = data.financial_ratios_calculation || {};
              const anomSum = data.missing_or_inconsistent_financial_info?.anomaly_summary || {};
              const companyName = data.company_name || data.ticker;

              // Determine bullish vs pullback trend cleanly (works with both old & new backend responses)
              const isUptrend =
                ml.prediction === 1 ||
                ml.regime?.includes('Bullish') ||
                ml.regime?.includes('Uptrend');
              const profTier = prof.profitability_range || '';
              const isProfitable =
                profTier === 'Highly Profitable' || profTier === 'Moderately Profitable';
              const isLowStability =
                hasVal(debt.financial_stability_score) && debt.financial_stability_score < 45;

              // Normalize action badge & plain-English summary even if backend cache returns legacy labels
              let actionLabel = ml.recommendation;
              if (!actionLabel || actionLabel === 'HOLD / NEUTRAL') {
                if (isUptrend) {
                  actionLabel = isProfitable && !isLowStability ? 'ACCUMULATE / BUY' : 'CAUTIOUS / MIXED SIGNALS';
                } else {
                  actionLabel = isProfitable && !isLowStability ? 'HOLD / WAIT FOR RECOVERY' : 'AVOID / HIGH RISK';
                }
              }

              const trendText = isUptrend ? 'Price Trend: Uptrend' : 'Price Trend: Pullback / Weak Momentum';
              const trendStyle = isUptrend
                ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/60'
                : 'bg-amber-900/40 text-amber-300 border border-amber-700/60';

              const recStyle =
                actionLabel.includes('BUY') || actionLabel.includes('ACCUMULATE') || actionLabel.includes('POSITIVE')
                  ? 'bg-emerald-700 text-emerald-100 border border-emerald-600'
                  : actionLabel.includes('HOLD')
                    ? 'bg-amber-800/70 text-amber-100 border border-amber-600/60'
                    : actionLabel.includes('AVOID') || actionLabel.includes('CAUTIOUS') || actionLabel.includes('MIXED')
                      ? 'bg-red-800/80 text-red-100 border border-red-700'
                      : 'bg-gray-700 text-gray-100 border border-gray-600';

              // Plain-English narrative fallback if backend hasn't restarted yet
              let explanation = ml.verdict_explanation;
              if (!explanation) {
                if (isUptrend && isProfitable && !isLowStability) {
                  explanation = `${companyName} combines ${profTier.toLowerCase()} financials with positive recent price momentum. Fundamentals and short-term trend align favorably.`;
                } else if (!isUptrend && isProfitable) {
                  explanation = `${companyName} remains ${profTier.toLowerCase()}, but recent stock price momentum is weak or pulling back. Consider holding and waiting for upward momentum to resume before adding.`;
                } else if (isUptrend) {
                  explanation = `${companyName} shows upward short-term price movement, though weaker profitability or elevated debt suggests keeping position sizes cautious.`;
                } else {
                  explanation = `${companyName} is currently experiencing weak recent price momentum alongside fundamental headwinds. Caution is advised until trends stabilize.`;
                }
              }

              // Investor takeaways (from backend or derived cleanly from already-fetched cards)
              const takeaways = ml.plain_english_takeaways?.length
                ? ml.plain_english_takeaways
                : [
                    profTier && profTier !== 'Data Unavailable' && {
                      topic: 'Profitability',
                      sentiment: profTier === 'Highly Profitable' ? 'positive' : profTier === 'Moderately Profitable' ? 'neutral' : 'negative',
                      detail: `${profTier}${hasVal(prof.net_profit_margin_pct) ? ` (Net Margin ${Number(prof.net_profit_margin_pct).toFixed(1)}%)` : ''}.`,
                    },
                    hasVal(debt.financial_stability_score) && {
                      topic: 'Debt & Safety',
                      sentiment: debt.financial_stability_score >= 70 ? 'positive' : debt.financial_stability_score >= 45 ? 'neutral' : 'negative',
                      detail: `${debt.stability_category}${hasVal(debt.debt_to_equity_ratio) ? ` (D/E: ${Number(debt.debt_to_equity_ratio).toFixed(2)})` : ''}.`,
                    },
                    hasVal(ratios.pe_ratio) && ratios.pe_ratio > 0 && {
                      topic: 'Valuation',
                      sentiment: ratios.pe_ratio < 18 ? 'positive' : ratios.pe_ratio <= 34 ? 'neutral' : 'negative',
                      detail: `P/E of ${Number(ratios.pe_ratio).toFixed(2)}x (${ratios.valuation_tier}).`,
                    },
                    {
                      topic: 'Short-Term Trend',
                      sentiment: isUptrend ? 'positive' : 'negative',
                      detail: isUptrend
                        ? 'Stock is trading in an upward short-term trend.'
                        : 'Stock price momentum is currently weak or consolidating downward.',
                    },
                  ].filter(Boolean);

              if ((anomSum.sudden_downfalls ?? 0) > 0 && anomSum.worst_single_day) {
                takeaways.push({
                  topic: 'Volatility Risk',
                  sentiment: 'negative',
                  detail: `Logged ${anomSum.sudden_downfalls} sudden single-day drop(s) in the last year (worst: ${anomSum.worst_single_day.change_pct}% on ${anomSum.worst_single_day.date}).`,
                });
              }

              const sentimentDot = (s) =>
                s === 'positive' ? 'bg-emerald-400' : s === 'negative' ? 'bg-red-400' : 'bg-amber-400';

              return (
                <div className="space-y-4">
                  {/* Action Recommendation + Price Trend Tag */}
                  <div className="flex flex-wrap items-center gap-3">
                    <span className={`text-sm px-4 py-1.5 rounded-full font-bold tracking-wide ${recStyle}`}>
                      {actionLabel}
                    </span>
                    <span className={`text-xs px-3 py-1.5 rounded-full font-semibold flex items-center gap-1.5 ${trendStyle}`}>
                      {isUptrend ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                      {trendText}
                    </span>
                  </div>

                  {/* Plain-English Investor Summary */}
                  <div className="bg-gray-800/50 border border-emerald-900/40 rounded-lg p-4 text-sm text-gray-100 leading-relaxed">
                    {explanation}
                  </div>

                  {/* Key Takeaways List */}
                  {takeaways.length > 0 && (
                    <div className="bg-gray-800/30 rounded-lg p-3.5 space-y-2">
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Key Takeaways</p>
                      <div className="space-y-2">
                        {takeaways.map((item, idx) => (
                          <div key={idx} className="flex items-start gap-2.5 text-xs">
                            <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${sentimentDot(item.sentiment)}`} />
                            <div>
                              <span className="text-white font-semibold">{item.topic}: </span>
                              <span className="text-gray-300">{item.detail}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Price & Momentum Snapshot (only available values, with plain-English tags) */}
                  {Object.keys(signals).length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                      <div className="space-y-1">
                        {hasVal(signals.sma_spread_pct) && (
                          <KV
                            label="20D vs 50D Avg Price"
                            value={pct(signals.sma_spread_pct, 2, true)}
                            badge={interp.sma_trend}
                          />
                        )}
                        {hasVal(signals.return_20d_pct) && (
                          <KV label="20-Day Price Change" value={pct(signals.return_20d_pct, 2, true)} />
                        )}
                        {hasVal(signals.return_5d_pct) && (
                          <KV label="5-Day Price Change" value={pct(signals.return_5d_pct, 2, true)} />
                        )}
                        {hasVal(signals.latest_close) && (
                          <KV label="Latest Close" value={fmtPrice(signals.latest_close, currency)} />
                        )}
                      </div>
                      <div className="space-y-1">
                        {hasVal(signals.rsi_14) && (
                          <KV
                            label="Momentum Gauge (RSI)"
                            value={Number(signals.rsi_14).toFixed(1)}
                            badge={interp.rsi || (signals.rsi_14 >= 70 ? 'Overbought' : signals.rsi_14 >= 50 ? 'Healthy' : signals.rsi_14 >= 30 ? 'Soft / Weak' : 'Oversold')}
                          />
                        )}
                        {hasVal(signals.macd_hist) && (
                          <KV
                            label="Trend Momentum (MACD)"
                            value={Number(signals.macd_hist) > 0 ? 'Positive' : 'Negative'}
                            badge={interp.macd || (Number(signals.macd_hist) > 0 ? 'Buying Strength' : 'Selling Pressure')}
                          />
                        )}
                        {hasVal(signals.volatility_20d_pct) && (
                          <KV
                            label="Avg Daily Swing (20d)"
                            value={pct(signals.volatility_20d_pct)}
                            badge={interp.volatility || (signals.volatility_20d_pct < 1.5 ? 'Calm' : signals.volatility_20d_pct <= 3 ? 'Moderate' : 'High')}
                          />
                        )}
                        {hasVal(signals.daily_return_pct) && (
                          <KV label="Last Session Move" value={pct(signals.daily_return_pct, 2, true)} />
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}
          </Card>

        </div>
      )}

      {/* Empty state */}
      {!data && !loading && !error && (
        <div className="text-center py-20 bg-gray-900/40 rounded-xl border border-emerald-900/30">
          <Bot className="w-14 h-14 text-emerald-900 mx-auto mb-4" />
          <p className="text-gray-400 font-medium text-lg">Fundamental Analysis Agent</p>
          <p className="text-gray-600 text-sm mt-2 max-w-sm mx-auto">
            Enter a stock ticker above and click Analyze to get a comprehensive financial breakdown with ML insights.
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-2 text-xs text-gray-500">
            {['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'AAPL', 'MSFT', 'GOOGL'].map((t) => (
              <button
                key={t}
                onClick={() => setTicker(t)}
                className="px-3 py-1 bg-gray-800/60 hover:bg-emerald-900/30 hover:text-emerald-400 rounded-full border border-gray-700/50 hover:border-emerald-800 transition-all font-mono"
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
