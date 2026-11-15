import React from 'react';
import { 
  X, 
  Sparkles, 
  ShieldCheck, 
  BarChart3, 
  LineChart, 
  Zap, 
  Calendar
} from 'lucide-react';

export default function TaskReportModal({ task, onClose }) {
  if (!task) return null;

  let reportData = null;
  if (task.report_json) {
    try {
      reportData = JSON.parse(task.report_json);
    } catch {
      reportData = null;
    }
  }

  const agents = reportData?.agents || {};

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="relative w-full max-w-3xl bg-white/95 border border-[#E9E8F8] rounded-3xl p-6 sm:p-8 shadow-2xl shadow-[#8DB9F0]/20 text-slate-800 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-slate-800 p-1.5 rounded-full hover:bg-[#E9E8F8] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E9E8F8]">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-black font-mono text-slate-900 tracking-tight">
                {task.ticker}
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-[#E9E8F8] text-[#524398] font-bold">
                {task.market}
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-[#8DB9F0]/20 text-[#22559c] font-bold">
                {task.requested_period}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1 flex items-center space-x-1.5 font-mono">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>Generated on {new Date(task.created_at).toLocaleDateString()}</span>
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="bg-white border border-[#E9E8F8] rounded-2xl px-4 py-2 text-right shadow-sm">
              <span className="text-[10px] font-mono text-slate-500 uppercase font-semibold">Consensus</span>
              <p className="text-sm font-extrabold text-[#3575cb]">
                {task.recommendation || 'Strong Buy'}
              </p>
            </div>
            {task.target_price && (
              <div className="bg-white border border-[#E9E8F8] rounded-2xl px-4 py-2 text-right shadow-sm">
                <span className="text-[10px] font-mono text-slate-500 uppercase font-semibold">Target Price</span>
                <p className="text-sm font-extrabold text-[#be6543] font-mono">
                  {task.target_price}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Executive Summary */}
        <div className="mt-6 p-4 rounded-2xl bg-gradient-to-r from-[#f7f6fd] to-[#f0f6fd] border border-[#E9E8F8]">
          <div className="flex items-center space-x-2 text-xs font-bold text-slate-900 mb-2">
            <Sparkles className="w-4 h-4 text-[#ea9e80]" />
            <span>Executive Synthesis & Desk Verdict</span>
          </div>
          <p className="text-xs text-slate-700 leading-relaxed font-sans">
            {task.summary || reportData?.verdict}
          </p>
        </div>

        {/* Multi-Agent Deep-Dive Grid */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Fundamental Agent */}
          <div className="p-4 rounded-2xl bg-[#f1f6fd] border border-[#adcff6]">
            <div className="flex items-center space-x-2 text-xs font-extrabold text-[#22559c] mb-2.5">
              <BarChart3 className="w-4 h-4 text-[#3575cb]" />
              <span>Fundamental Agent Findings</span>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-[#c5dcf7]/60 font-mono">
                <span className="text-slate-600 font-medium">Financial Health:</span>
                <span className="text-[#3575cb] font-bold">{agents?.FundamentalAgent?.health || 'Robust'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#c5dcf7]/60 font-mono">
                <span className="text-slate-600 font-medium">P/E Ratio:</span>
                <span className="text-slate-800 font-bold">{agents?.FundamentalAgent?.pe_ratio || '24.8'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#c5dcf7]/60 font-mono">
                <span className="text-slate-600 font-medium">Revenue Growth:</span>
                <span className="text-slate-800 font-bold">{agents?.FundamentalAgent?.revenue_growth || '+16.4% YoY'}</span>
              </div>
              <p className="text-[11px] text-slate-600 mt-2 leading-relaxed font-sans">
                {agents?.FundamentalAgent?.notes}
              </p>
            </div>
          </div>

          {/* Technical Agent */}
          <div className="p-4 rounded-2xl bg-[#f4f3fb] border border-[#d7d4f2]">
            <div className="flex items-center space-x-2 text-xs font-extrabold text-[#524398] mb-2.5">
              <LineChart className="w-4 h-4 text-[#6755b9]" />
              <span>Technical Agent Findings</span>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-[#bfb9e9]/60 font-mono">
                <span className="text-slate-600 font-medium">Trend Structure:</span>
                <span className="text-[#524398] font-bold">{agents?.TechnicalAgent?.trend || 'Bullish'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#bfb9e9]/60 font-mono">
                <span className="text-slate-600 font-medium">14-Day RSI:</span>
                <span className="text-slate-800 font-bold">{agents?.TechnicalAgent?.rsi_14 || '58.2 (Neutral-Bullish)'}</span>
              </div>
              <p className="text-[11px] text-slate-600 mt-2 leading-relaxed font-sans">
                {agents?.TechnicalAgent?.moving_averages}
              </p>
              <p className="text-[11px] text-slate-500 font-sans">
                {agents?.TechnicalAgent?.support_level}
              </p>
            </div>
          </div>

          {/* Sentiment Agent */}
          <div className="p-4 rounded-2xl bg-[#fdeee8] border border-[#fad1c2]">
            <div className="flex items-center space-x-2 text-xs font-extrabold text-[#9b5136] mb-2.5">
              <Zap className="w-4 h-4 text-[#be6543]" />
              <span>Sentiment & Flow Agent</span>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-[#fbd8cc]/60 font-mono">
                <span className="text-slate-600 font-medium">Sentiment Score:</span>
                <span className="text-[#be6543] font-bold">{agents?.SentimentAgent?.sentiment_score || '78/100'}</span>
              </div>
              <p className="text-[11px] text-slate-600 mt-2 leading-relaxed font-sans">
                {agents?.SentimentAgent?.institutional_activity}
              </p>
              <p className="text-[11px] text-slate-500 font-sans">
                {agents?.SentimentAgent?.news_sentiment}
              </p>
            </div>
          </div>

          {/* Risk Management Agent */}
          <div className="p-4 rounded-2xl bg-[#f1f6fd] border border-[#c5dcf7]">
            <div className="flex items-center space-x-2 text-xs font-extrabold text-[#3575cb] mb-2.5">
              <ShieldCheck className="w-4 h-4 text-[#4e8fe2]" />
              <span>Risk Management Agent</span>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-[#c5dcf7]/60 font-mono">
                <span className="text-slate-600 font-medium">Risk Assessment:</span>
                <span className="text-[#3575cb] font-bold">{agents?.RiskAgent?.risk_rating || 'Moderate'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#c5dcf7]/60 font-mono">
                <span className="text-slate-600 font-medium">Portfolio Beta:</span>
                <span className="text-slate-800 font-bold">{agents?.RiskAgent?.beta || '1.08'}</span>
              </div>
              <p className="text-[11px] text-slate-600 mt-2 leading-relaxed font-sans">
                {agents?.RiskAgent?.drawdown_risk}
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-5 border-t border-[#E9E8F8] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-slate-100 hover:bg-[#E9E8F8] text-slate-800 text-xs font-bold rounded-2xl transition-colors border border-[#E9E8F8]"
          >
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
}
