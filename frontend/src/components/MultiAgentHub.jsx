import { useState } from 'react';
import {
  FileSpreadsheet,
  SlidersHorizontal,
  Newspaper,
  ShieldAlert,
  Brain,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Loader2,
  TrendingUp,
  TrendingDown,
  Sparkles,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const MultiAgentHub = ({ data, loading, symbol, onRefresh }) => {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'fundamental' | 'technical' | 'news' | 'risk'

  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-8 border border-cyan-500/20 text-center">
        <div className="flex flex-col items-center justify-center py-10 space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
          <p className="text-white font-semibold text-sm">
            Orchestrating 4 Autonomous Analysis Agents for {symbol}...
          </p>
          <p className="text-slate-400 text-xs max-w-md">
            Querying real balance sheets, computing SMA/EMA/RSI/MACD, gathering Finnhub headlines, and calculating beta & volatility.
          </p>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const {
    fundamental,
    technical,
    news_sentiment,
    risk,
    composite_verdict,
    composite_score,
    executive_summary,
  } = data;

  const tabs = [
    { id: 'overview', label: 'Executive Synthesis', icon: Brain },
    { id: 'fundamental', label: 'Fundamental Agent', icon: FileSpreadsheet },
    { id: 'technical', label: 'Technical Agent', icon: SlidersHorizontal },
    { id: 'news', label: 'News & Sentiment', icon: Newspaper },
    { id: 'risk', label: 'Risk Analysis', icon: ShieldAlert },
  ];

  return (
    <div className="glass-card rounded-2xl p-6 border border-cyan-500/20 space-y-6">
      {/* Top Header Banner: CIO Verdict & Multi-Agent Score */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-white/10">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
            <h3 className="text-lg font-bold text-white tracking-wide">
              Multi-Agent Stock Research Intelligence
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
              4 Agents Operational
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Real market telemetry analyzed via Google Gemini AI & Quantitative Python Engines
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Composite Verdict
            </div>
            <div className="text-base font-extrabold text-cyan-300">
              {composite_verdict || 'Analysis Complete'}
            </div>
          </div>
          <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/40 text-cyan-300 font-extrabold text-lg shadow-lg shadow-cyan-500/10">
            {composite_score != null ? composite_score.toFixed(0) : 'N/A'}
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 p-1 bg-white/[0.03] border border-white/5 rounded-xl">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Executive Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Executive CIO Summary Card */}
          <div className="p-4 bg-gradient-to-br from-white/[0.04] to-cyan-500/[0.03] border border-cyan-500/20 rounded-xl space-y-2">
            <div className="flex items-center gap-2 text-cyan-300 text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-4 h-4" /> Chief Investment Officer Synthesis
            </div>
            <p className="text-slate-200 text-xs leading-relaxed">
              {executive_summary}
            </p>
          </div>

          {/* 4 Agent Metric Preview Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Fundamental Agent Preview */}
            <div
              onClick={() => setActiveTab('fundamental')}
              className="p-4 bg-white/[0.03] hover:bg-white/[0.05] border border-white/5 hover:border-emerald-500/30 rounded-xl transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">Fundamental</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  {fundamental?.financial_health_score}/100
                </span>
              </div>
              <div className="text-lg font-bold text-white group-hover:text-emerald-300 transition-colors">
                {fundamental?.strengths?.length || 0} Strengths
              </div>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                {fundamental?.financial_health_summary}
              </p>
              <div className="mt-3 flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                View Health Report <ChevronRight className="w-3 h-3" />
              </div>
            </div>

            {/* Technical Agent Preview */}
            <div
              onClick={() => setActiveTab('technical')}
              className="p-4 bg-white/[0.03] hover:bg-white/[0.05] border border-white/5 hover:border-cyan-500/30 rounded-xl transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">Technical</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                  {technical?.overall_signal}
                </span>
              </div>
              <div className="text-lg font-bold text-white group-hover:text-cyan-300 transition-colors">
                Signal: {technical?.signal_score > 0 ? `+${technical?.signal_score}` : technical?.signal_score}
              </div>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                RSI: {technical?.indicators?.rsi_14?.toFixed(1) || 'N/A'} | MACD Hist: {technical?.indicators?.macd_hist > 0 ? `+${technical?.indicators?.macd_hist?.toFixed(2)}` : technical?.indicators?.macd_hist?.toFixed(2)}
              </p>
              <div className="mt-3 flex items-center gap-1 text-[11px] text-cyan-400 font-medium">
                View Signals & Overlays <ChevronRight className="w-3 h-3" />
              </div>
            </div>

            {/* News & Sentiment Preview */}
            <div
              onClick={() => setActiveTab('news')}
              className="p-4 bg-white/[0.03] hover:bg-white/[0.05] border border-white/5 hover:border-blue-500/30 rounded-xl transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">News & Sentiment</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  news_sentiment?.overall_sentiment === 'Positive'
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                    : news_sentiment?.overall_sentiment === 'Negative'
                    ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                    : 'bg-slate-500/15 text-slate-300 border border-slate-500/30'
                }`}>
                  {news_sentiment?.overall_sentiment}
                </span>
              </div>
              <div className="text-lg font-bold text-white group-hover:text-blue-300 transition-colors">
                Score: {news_sentiment?.overall_score > 0 ? `+${news_sentiment?.overall_score}` : news_sentiment?.overall_score}
              </div>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                {news_sentiment?.positive_count} Pos / {news_sentiment?.negative_count} Neg ({news_sentiment?.articles?.length || 0} Articles)
              </p>
              <div className="mt-3 flex items-center gap-1 text-[11px] text-blue-400 font-medium">
                Browse Articles & Links <ChevronRight className="w-3 h-3" />
              </div>
            </div>

            {/* Risk Agent Preview */}
            <div
              onClick={() => setActiveTab('risk')}
              className="p-4 bg-white/[0.03] hover:bg-white/[0.05] border border-white/5 hover:border-purple-500/30 rounded-xl transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">Risk Profile</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  risk?.risk_level === 'Low'
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                    : risk?.risk_level === 'High'
                    ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                    : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                }`}>
                  {risk?.risk_level} Risk
                </span>
              </div>
              <div className="text-lg font-bold text-white group-hover:text-purple-300 transition-colors">
                Score: {risk?.risk_score}/100
              </div>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                Vol: {risk?.volatility_annualized}% | Beta: {risk?.beta != null ? `${risk.beta}x` : 'N/A'} | Max DD: {risk?.max_drawdown}%
              </p>
              <div className="mt-3 flex items-center gap-1 text-[11px] text-purple-400 font-medium">
                Examine Risk Exposures <ChevronRight className="w-3 h-3" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Fundamental Analysis Agent */}
      {activeTab === 'fundamental' && fundamental && (
        <div className="space-y-6">
          {/* Health Score & Key Ratios */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Health Score</span>
              <div className="text-3xl font-extrabold text-emerald-400 mt-1">
                {fundamental.financial_health_score}/100
              </div>
              <p className="text-xs text-slate-400 mt-1">{fundamental.financial_health_summary}</p>
            </div>

            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Revenue & Income</span>
              <div className="text-xl font-bold text-white mt-1">
                {fundamental.revenue != null ? `$${(fundamental.revenue / 1e9).toFixed(1)}B` : 'N/A'}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Net Income: {fundamental.net_income != null ? `$${(fundamental.net_income / 1e9).toFixed(1)}B` : 'N/A'}
              </p>
            </div>

            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Earnings & Debt</span>
              <div className="text-xl font-bold text-white mt-1">
                EPS: {fundamental.eps != null ? `$${fundamental.eps.toFixed(2)}` : 'N/A'}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Total Debt: {fundamental.total_debt != null ? `$${(fundamental.total_debt / 1e9).toFixed(1)}B` : 'N/A'}
              </p>
            </div>
          </div>

          {/* Ratios Breakdown */}
          <div className="p-4 bg-white/[0.02] border border-white/5 rounded-xl">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">
              Calculated Financial Ratios
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
              {[
                { label: 'P/E Ratio', val: fundamental.ratios?.pe_ratio != null ? `${fundamental.ratios.pe_ratio.toFixed(1)}x` : 'N/A' },
                { label: 'EPS', val: fundamental.ratios?.eps != null ? `$${fundamental.ratios.eps.toFixed(2)}` : 'N/A' },
                { label: 'ROE', val: fundamental.ratios?.roe != null ? `${fundamental.ratios.roe.toFixed(1)}%` : 'N/A' },
                { label: 'Debt / Equity', val: fundamental.ratios?.debt_to_equity != null ? `${fundamental.ratios.debt_to_equity.toFixed(2)}x` : 'N/A' },
                { label: 'Current Ratio', val: fundamental.ratios?.current_ratio != null ? `${fundamental.ratios.current_ratio.toFixed(2)}x` : 'N/A' },
                { label: 'Net Margin', val: fundamental.ratios?.net_profit_margin != null ? `${fundamental.ratios.net_profit_margin.toFixed(1)}%` : 'N/A' },
                { label: 'ROA', val: fundamental.ratios?.roa != null ? `${fundamental.ratios.roa.toFixed(1)}%` : 'N/A' },
              ].map((r) => (
                <div key={r.label} className="p-2.5 bg-white/[0.03] rounded-lg border border-white/5">
                  <div className="text-[10px] text-slate-400">{r.label}</div>
                  <div className="text-xs font-bold text-white mt-0.5">{r.val}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Strengths & Weaknesses */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-emerald-500/[0.04] border border-emerald-500/20 rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase">
                <CheckCircle className="w-4 h-4" /> Financial Strengths ({fundamental.strengths.length})
              </div>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {fundamental.strengths.length > 0 ? (
                  fundamental.strengths.map((s, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-emerald-400 mt-0.5">•</span>
                      <span>{s}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-slate-500">No dominant financial strengths detected.</li>
                )}
              </ul>
            </div>

            <div className="p-4 bg-rose-500/[0.04] border border-rose-500/20 rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-rose-400 font-bold text-xs uppercase">
                <AlertCircle className="w-4 h-4" /> Financial Weaknesses ({fundamental.weaknesses.length})
              </div>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {fundamental.weaknesses.length > 0 ? (
                  fundamental.weaknesses.map((w, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-rose-400 mt-0.5">•</span>
                      <span>{w}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-slate-500">No critical balance sheet vulnerabilities detected.</li>
                )}
              </ul>
            </div>
          </div>

          {/* AI Financial Health Executive Report */}
          <div className="p-5 bg-white/[0.03] border border-white/10 rounded-xl space-y-3">
            <div className="flex items-center gap-2 text-cyan-300 font-bold text-xs uppercase tracking-wider">
              <Brain className="w-4 h-4" /> Google Gemini Financial Health Report
            </div>
            <div className="text-xs text-slate-200 leading-relaxed whitespace-pre-line bg-black/30 p-4 rounded-lg font-mono">
              {fundamental.ai_generated_report}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Technical Analysis Agent */}
      {activeTab === 'technical' && technical && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Technical Posture</span>
              <div className="text-2xl font-extrabold text-cyan-300 mt-1">
                {technical.overall_signal}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Signal Conviction Score: {technical.signal_score > 0 ? `+${technical.signal_score}` : technical.signal_score} / 100
              </p>
            </div>

            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Momentum & Oscillators</span>
              <div className="text-xl font-bold text-white mt-1">
                RSI(14): {technical.indicators?.rsi_14 != null ? technical.indicators.rsi_14.toFixed(1) : 'N/A'}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                MACD Hist: {technical.indicators?.macd_hist != null ? technical.indicators.macd_hist.toFixed(3) : 'N/A'}
              </p>
            </div>

            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Moving Averages</span>
              <div className="text-xs text-slate-300 space-y-1 mt-1">
                <div>SMA 20: ${technical.indicators?.sma_20?.toFixed(2) || 'N/A'}</div>
                <div>SMA 50: ${technical.indicators?.sma_50?.toFixed(2) || 'N/A'}</div>
                <div>SMA 200: ${technical.indicators?.sma_200?.toFixed(2) || 'N/A'}</div>
              </div>
            </div>
          </div>

          {/* Technical Summary */}
          <div className="p-4 bg-cyan-500/[0.04] border border-cyan-500/20 rounded-xl">
            <p className="text-xs text-slate-200 leading-relaxed font-medium">
              {technical.summary}
            </p>
          </div>

          {/* Bullish & Bearish Signals */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-emerald-500/[0.04] border border-emerald-500/20 rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase">
                <TrendingUp className="w-4 h-4" /> Bullish Indicators ({technical.bullish_signals.length})
              </div>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {technical.bullish_signals.length > 0 ? (
                  technical.bullish_signals.map((sig, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-emerald-400 mt-0.5">✔</span>
                      <span>{sig}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-slate-500">No active bullish confirmations.</li>
                )}
              </ul>
            </div>

            <div className="p-4 bg-rose-500/[0.04] border border-rose-500/20 rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-rose-400 font-bold text-xs uppercase">
                <TrendingDown className="w-4 h-4" /> Bearish Indicators ({technical.bearish_signals.length})
              </div>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {technical.bearish_signals.length > 0 ? (
                  technical.bearish_signals.map((sig, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-rose-400 mt-0.5">✖</span>
                      <span>{sig}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-slate-500">No active bearish cautions.</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: News & Sentiment Agent */}
      {activeTab === 'news' && news_sentiment && (
        <div className="space-y-6">
          {/* Header metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Overall Sentiment</span>
              <div className="text-2xl font-extrabold text-white mt-1 flex items-center gap-2">
                <span className={`px-2.5 py-0.5 rounded text-sm font-bold ${
                  news_sentiment.overall_sentiment === 'Positive'
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                    : news_sentiment.overall_sentiment === 'Negative'
                    ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                    : 'bg-slate-500/15 text-slate-300 border border-slate-500/30'
                }`}>
                  {news_sentiment.overall_sentiment}
                </span>
                <span className="text-xs text-slate-400 font-normal">
                  Score: {news_sentiment.overall_score > 0 ? `+${news_sentiment.overall_score}` : news_sentiment.overall_score}
                </span>
              </div>
            </div>

            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Article Breakdown</span>
              <div className="text-xs text-slate-300 space-y-1 mt-1">
                <span className="text-emerald-400 font-semibold">{news_sentiment.positive_count} Positive</span> |{' '}
                <span className="text-rose-400 font-semibold">{news_sentiment.negative_count} Negative</span> |{' '}
                <span className="text-slate-400 font-semibold">{news_sentiment.neutral_count} Neutral</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                {news_sentiment.articles?.length || 0} total headlines queried
              </p>
            </div>

            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">News Data Feeds</span>
              <div className="text-xs text-cyan-300 font-semibold mt-1">
                Finnhub Financial News API
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Live articles with source attributions & publication timestamps
              </p>
            </div>
          </div>

          {/* AI Executive News Synthesis */}
          <div className="p-4 bg-white/[0.03] border border-white/10 rounded-xl space-y-2">
            <div className="flex items-center gap-2 text-cyan-300 font-bold text-xs uppercase tracking-wider">
              <Sparkles className="w-4 h-4" /> Gemini AI News & Catalyst Synthesis
            </div>
            <p className="text-xs text-slate-200 leading-relaxed">
              {news_sentiment.executive_summary}
            </p>
          </div>

          {/* Real Articles List with Source, Date, URL */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              Curated Financial Articles & Links
            </h4>
            {news_sentiment.articles && news_sentiment.articles.length > 0 ? (
              <div className="space-y-3">
                {news_sentiment.articles.map((art, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 hover:border-cyan-500/20 rounded-xl transition-all space-y-2"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white/10 text-slate-300 border border-white/10">
                          {art.source}
                        </span>
                        <span className="text-[11px] text-slate-400">
                          {art.published_at}
                        </span>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        art.sentiment === 'Positive'
                          ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                          : art.sentiment === 'Negative'
                          ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                          : 'bg-slate-500/15 text-slate-300 border border-slate-500/30'
                      }`}>
                        {art.sentiment} ({art.sentiment_score > 0 ? `+${art.sentiment_score}` : art.sentiment_score})
                      </span>
                    </div>

                    <h5 className="font-semibold text-white text-xs leading-snug">
                      {art.headline}
                    </h5>

                    {art.description && (
                      <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-2">
                        {art.description}
                      </p>
                    )}

                    <div className="pt-2 flex items-center justify-end">
                      <a
                        href={art.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-cyan-400 hover:text-cyan-300 hover:underline"
                      >
                        Read Original Article <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-xs py-4 text-center">
                No recent financial headlines found for this ticker.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Tab 5: Risk Analysis Agent */}
      {activeTab === 'risk' && risk && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Risk Classification</span>
              <div className="text-2xl font-extrabold text-white mt-1 flex items-center gap-2">
                <span className={`px-2.5 py-0.5 rounded text-sm font-bold ${
                  risk.risk_level === 'Low'
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                    : risk.risk_level === 'High'
                    ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                    : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                }`}>
                  {risk.risk_level} Risk
                </span>
                <span className="text-xs text-slate-400">Score: {risk.risk_score}/100</span>
              </div>
            </div>

            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Volatility & Beta</span>
              <div className="text-xl font-bold text-white mt-1">
                Annualized Vol: {risk.volatility_annualized}%
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Market Beta (vs SPY): {risk.beta != null ? `${risk.beta}x` : 'N/A'}
              </p>
            </div>

            <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Drawdown & Std Dev</span>
              <div className="text-xl font-bold text-rose-400 mt-1">
                Max Drawdown: {risk.max_drawdown}%
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Daily Std Dev: {risk.standard_deviation_daily}% (Annualized: {risk.standard_deviation_annualized}%)
              </p>
            </div>
          </div>

          {/* Risk Summary */}
          <div className="p-4 bg-purple-500/[0.04] border border-purple-500/20 rounded-xl">
            <p className="text-xs text-slate-200 leading-relaxed font-medium">
              {risk.summary}
            </p>
          </div>

          {/* Identified Market Risks */}
          <div className="p-5 bg-white/[0.03] border border-white/10 rounded-xl space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" /> Identified Financial & Market Risks
            </h4>
            <div className="space-y-2">
              {risk.market_risks && risk.market_risks.length > 0 ? (
                risk.market_risks.map((r, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-white/[0.02] border border-white/5 rounded-lg flex items-start gap-2 text-xs text-slate-300"
                  >
                    <span className="text-rose-400 mt-0.5">•</span>
                    <span>{r}</span>
                  </div>
                ))
              ) : (
                <p className="text-slate-500 text-xs">No extraordinary risks flagged.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiAgentHub;
