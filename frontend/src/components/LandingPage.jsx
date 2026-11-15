import React, { useState } from 'react';
import { 
  Sparkles, 
  ArrowRight,
  BarChart3,
  LineChart,
  Zap,
  ShieldCheck
} from 'lucide-react';
import { stocksApi } from '../services/api';

export default function LandingPage({ onOpenAuth }) {
  const [previewTicker, setPreviewTicker] = useState('RELIANCE');
  const [previewQuote, setPreviewQuote] = useState(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

  const fetchPreview = async (ticker) => {
    setIsLoadingPreview(true);
    try {
      const q = await stocksApi.getQuote(ticker, 'NSE');
      setPreviewQuote(q);
      setPreviewTicker(ticker);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingPreview(false);
    }
  };

  return (
    <div className="relative overflow-hidden">
      {/* Background Decorative Ambient Gradients (Powder Blue + Soft Lavender + Warm Sunset Peach) */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[650px] bg-gradient-to-b from-[#8DB9F0]/25 via-[#E9E8F8]/40 to-transparent blur-3xl pointer-events-none"></div>
      <div className="absolute top-20 right-10 w-96 h-96 bg-[#F5B69E]/20 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute top-60 left-10 w-96 h-96 bg-[#8DB9F0]/20 rounded-full blur-3xl pointer-events-none"></div>

      {/* Hero Section */}
      <section className="relative pt-12 pb-20 sm:pt-20 sm:pb-28 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Release / Tech Badge */}
        <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-white/90 border border-[#E9E8F8] text-xs font-mono text-[#43377c] mb-8 shadow-sm">
          <span className="w-2 h-2 rounded-full bg-[#8DB9F0] animate-ping"></span>
          <span className="font-semibold">Module 1: User Auth & Research Workspace Active</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-slate-900 max-w-4xl mx-auto leading-[1.15]">
          Institutional Stock Research Powered by{' '}
          <span className="bg-gradient-to-r from-[#3575cb] via-[#524398] to-[#d88160] bg-clip-text text-transparent">
            Multi-Agent Intelligence
          </span>
        </h1>

        {/* Subtitle */}
        <p className="mt-6 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Coordinate autonomous AI agents to scan equities across NSE, BSE, NASDAQ, and NYSE. 
          Get comprehensive fundamental models, technical structures, sentiment feeds, and risk scoring in seconds.
        </p>

        {/* Call to Actions */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={() => onOpenAuth('register')}
            className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-[#F5B69E] to-[#ea9e80] hover:from-[#f0a68d] hover:to-[#df8b6b] text-slate-900 font-bold text-sm rounded-2xl shadow-xl shadow-[#F5B69E]/35 transition-all transform hover:-translate-y-0.5 flex items-center justify-center space-x-2.5 glow-peach"
          >
            <Sparkles className="w-4 h-4" />
            <span>Create Free Account</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </button>
          
          <button
            onClick={() => onOpenAuth('login')}
            className="w-full sm:w-auto px-8 py-4 bg-white/85 hover:bg-white border border-[#E9E8F8] text-slate-800 font-bold text-sm rounded-2xl shadow-sm transition-all"
          >
            Sign In to Existing Workspace
          </button>
        </div>

        {/* Quick Ticker Live Ribbon */}
        <div className="mt-14 max-w-4xl mx-auto">
          <div className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-3 font-semibold">
            Real-Time Market Feeds • NSE / BSE / NASDAQ
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { ticker: 'RELIANCE', price: '₹2,985.50', change: '+1.40%', color: 'text-emerald-600' },
              { ticker: 'TCS', price: '₹4,120.25', change: '+0.85%', color: 'text-emerald-600' },
              { ticker: 'INFY', price: '₹1,892.40', change: '+1.65%', color: 'text-emerald-600' },
              { ticker: 'HDFCBANK', price: '₹1,640.80', change: '-0.30%', color: 'text-rose-600' },
            ].map((stock) => (
              <div 
                key={stock.ticker}
                onClick={() => fetchPreview(stock.ticker)}
                className="cursor-pointer bg-white/80 border border-[#E9E8F8] hover:border-[#8DB9F0] rounded-2xl p-3.5 text-left transition-all group shadow-sm hover:shadow-md"
              >
                <div className="flex justify-between items-center text-xs">
                  <span className="font-extrabold text-slate-800 group-hover:text-[#3575cb]">{stock.ticker}</span>
                  <span className={`font-mono text-[11px] font-bold ${stock.color}`}>{stock.change}</span>
                </div>
                <div className="font-mono text-xs font-bold text-slate-700 mt-1">{stock.price}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Interactive Stock Engine Preview */}
      <section className="py-12 bg-white/40 border-y border-[#E9E8F8]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="glass-panel rounded-3xl p-6 sm:p-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6 pb-6 border-b border-[#E9E8F8]">
              <div>
                <span className="text-xs font-mono uppercase tracking-wider text-[#3575cb] font-bold">
                  Live Engine Verification
                </span>
                <h3 className="text-xl font-extrabold text-slate-800 mt-1">
                  Test Stock Quote & Multi-Agent Lookup
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Supporting Indian Market APIs (NSE/BSE) and Global Equities.
                </p>
              </div>

              {/* Quick lookup buttons */}
              <div className="flex flex-wrap gap-2">
                {['RELIANCE', 'TCS', 'TATAMOTORS', 'AAPL', 'NVDA'].map((sym) => (
                  <button
                    key={sym}
                    onClick={() => fetchPreview(sym)}
                    className={`px-3 py-1.5 text-xs font-mono font-bold rounded-xl border transition-all ${
                      previewTicker === sym 
                        ? 'bg-[#8DB9F0] text-slate-900 border-[#6ea6ec] shadow-sm'
                        : 'bg-white/80 text-slate-700 border-[#E9E8F8] hover:border-[#adcff6]'
                    }`}
                  >
                    {sym}
                  </button>
                ))}
              </div>
            </div>

            {/* Quote details display */}
            <div className="pt-6">
              {isLoadingPreview ? (
                <div className="py-8 flex items-center justify-center space-x-2 text-xs text-slate-500 font-mono">
                  <span className="w-4 h-4 border-2 border-[#8DB9F0] border-t-transparent rounded-full animate-spin"></span>
                  <span>Fetching calibrated market feed...</span>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="bg-white/90 border border-[#E9E8F8] rounded-2xl p-4 shadow-sm">
                    <span className="text-[10px] font-mono text-slate-500 uppercase font-semibold">Ticker & Exchange</span>
                    <p className="text-base font-extrabold text-slate-900 mt-1">
                      {previewQuote?.ticker || 'RELIANCE'} 
                      <span className="text-xs text-[#3575cb] font-mono ml-2 font-bold">({previewQuote?.market || 'NSE'})</span>
                    </p>
                  </div>
                  <div className="bg-white/90 border border-[#E9E8F8] rounded-2xl p-4 shadow-sm">
                    <span className="text-[10px] font-mono text-slate-500 uppercase font-semibold">Current Quote</span>
                    <p className="text-base font-mono font-extrabold text-slate-900 mt-1">
                      {previewQuote?.currency || 'INR'} {previewQuote?.price ? previewQuote.price.toLocaleString() : '2,985.50'}
                    </p>
                  </div>
                  <div className="bg-white/90 border border-[#E9E8F8] rounded-2xl p-4 shadow-sm">
                    <span className="text-[10px] font-mono text-slate-500 uppercase font-semibold">Daily Momentum</span>
                    <p className="text-base font-mono font-extrabold text-emerald-600 mt-1">
                      +{previewQuote?.change_pct || 1.40}%
                    </p>
                  </div>
                  <div className="bg-white/90 border border-[#E9E8F8] rounded-2xl p-4 shadow-sm">
                    <span className="text-[10px] font-mono text-slate-500 uppercase font-semibold">Feed Provider</span>
                    <p className="text-xs font-mono font-bold text-[#3575cb] mt-2 truncate">
                      {previewQuote?.source || 'Indian Market Feed'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Multi-Agent Architecture Cards */}
      <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs uppercase font-mono tracking-wider font-extrabold text-[#524398]">
            Autonomous Collaboration
          </h2>
          <h3 className="text-3xl font-extrabold text-slate-900 mt-2">
            Four Specialized Agents Working as One Desk
          </h3>
          <p className="text-sm text-slate-600 mt-3">
            Every research task triggers coordinated analysis across financial statements, charting setups, market sentiment, and macroeconomic risk.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              agent: 'Fundamental Agent',
              icon: BarChart3,
              desc: 'Parses balance sheets, cash flows, P/E multiples, and quarterly earnings to calculate intrinsic valuation.',
              badge: 'Valuation & DCF',
              bg: 'from-[#e2edfb] to-white/95',
              border: 'border-[#adcff6]',
              accent: 'text-[#3575cb]',
              pillBg: 'bg-[#8DB9F0]/20 text-[#22559c]'
            },
            {
              agent: 'Technical Agent',
              icon: LineChart,
              desc: 'Identifies swing highs/lows, 50/200-day EMAs, RSI divergence, and key liquidity breakout zones.',
              badge: 'Price Action & Trends',
              bg: 'from-[#f4f3fb] to-white/95',
              border: 'border-[#d7d4f2]',
              accent: 'text-[#6755b9]',
              pillBg: 'bg-[#E9E8F8] text-[#524398]'
            },
            {
              agent: 'Sentiment Agent',
              icon: Zap,
              desc: 'Aggregates market sentiment, corporate disclosures, institutional order flow, and analyst consensus.',
              badge: 'Order Flow & News',
              bg: 'from-[#fdeee8] to-white/95',
              border: 'border-[#fad1c2]',
              accent: 'text-[#be6543]',
              pillBg: 'bg-[#F5B69E]/25 text-[#9b5136]'
            },
            {
              agent: 'Risk Manager Agent',
              icon: ShieldCheck,
              desc: 'Computes asset beta, volatility bounds, drawdown probability, and stress-tests portfolio impact.',
              badge: 'Beta & Drawdown',
              bg: 'from-[#f1f6fd] to-white/95',
              border: 'border-[#c5dcf7]',
              accent: 'text-[#3575cb]',
              pillBg: 'bg-[#8DB9F0]/20 text-[#22559c]'
            }
          ].map((item, idx) => (
            <div 
              key={idx}
              className={`rounded-3xl p-6 bg-gradient-to-b ${item.bg} border ${item.border} flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow`}
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-2.5 rounded-2xl bg-white shadow-sm border border-slate-100 ${item.accent}`}>
                    <item.icon className="w-5 h-5 stroke-[2.2]" />
                  </div>
                  <span className={`text-[10px] font-mono px-2.5 py-1 rounded-full font-bold ${item.pillBg}`}>
                    {item.badge}
                  </span>
                </div>
                <h4 className="text-base font-extrabold text-slate-900">{item.agent}</h4>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Tech Architecture Stack Banner */}
      <section className="py-12 bg-white/70 border-t border-[#E9E8F8]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-5 text-center text-xs font-mono">
            <div className="flex flex-col items-center p-3.5 rounded-2xl bg-white/90 border border-[#E9E8F8] shadow-sm">
              <span className="text-[#3575cb] font-extrabold mb-0.5">FastAPI</span>
              <span className="text-[10px] text-slate-500">Python 3 Async Engine</span>
            </div>
            <div className="flex flex-col items-center p-3.5 rounded-2xl bg-white/90 border border-[#E9E8F8] shadow-sm">
              <span className="text-[#524398] font-extrabold mb-0.5">PostgreSQL</span>
              <span className="text-[10px] text-slate-500">SQLAlchemy ORM</span>
            </div>
            <div className="flex flex-col items-center p-3.5 rounded-2xl bg-white/90 border border-[#E9E8F8] shadow-sm">
              <span className="text-[#be6543] font-extrabold mb-0.5">JWT Security</span>
              <span className="text-[10px] text-slate-500">Bcrypt Password Hashing</span>
            </div>
            <div className="flex flex-col items-center p-3.5 rounded-2xl bg-white/90 border border-[#E9E8F8] shadow-sm">
              <span className="text-[#3575cb] font-extrabold mb-0.5">React.js</span>
              <span className="text-[10px] text-slate-500">Component Hierarchy</span>
            </div>
            <div className="flex flex-col items-center p-3.5 rounded-2xl bg-white/90 border border-[#E9E8F8] shadow-sm">
              <span className="text-[#524398] font-extrabold mb-0.5">Tailwind CSS</span>
              <span className="text-[10px] text-slate-500">Pastel Glass Theme</span>
            </div>
            <div className="flex flex-col items-center p-3.5 rounded-2xl bg-white/90 border border-[#E9E8F8] shadow-sm">
              <span className="text-[#be6543] font-extrabold mb-0.5">Market APIs</span>
              <span className="text-[10px] text-slate-500">NSE / BSE / Global</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
