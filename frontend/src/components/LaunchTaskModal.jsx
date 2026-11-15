import React, { useState, useEffect } from 'react';
import { 
  X, 
  Sparkles, 
  ArrowRight, 
  Bot, 
  Clock, 
  Globe2, 
  AlertCircle
} from 'lucide-react';
import { historyApi } from '../services/api';

const MARKETS = ['NSE', 'BSE', 'NASDAQ', 'NYSE'];
const PERIODS = ['1 Month', '3 Months', '6 Months', '1 Year', '5 Years'];

export default function LaunchTaskModal({ isOpen, onClose, initialTicker = '', defaultMarket = 'NSE', defaultPeriod = '6 Months', onTaskCreated }) {
  const [ticker, setTicker] = useState(initialTicker);
  const [market, setMarket] = useState(defaultMarket);
  const [period, setPeriod] = useState(defaultPeriod);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (initialTicker) setTicker(initialTicker);
    if (defaultMarket) setMarket(defaultMarket);
    if (defaultPeriod) setPeriod(defaultPeriod);
  }, [initialTicker, defaultMarket, defaultPeriod, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const cleanTicker = ticker.trim().toUpperCase();
    if (!cleanTicker) {
      setError('Please provide a stock ticker.');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const newTask = await historyApi.createTask(cleanTicker, market, period);
      if (onTaskCreated) {
        onTaskCreated(newTask);
      }
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to dispatch research task.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="relative w-full max-w-md bg-white/95 border border-[#E9E8F8] rounded-3xl p-6 sm:p-8 shadow-2xl shadow-[#8DB9F0]/20 text-slate-800"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-slate-800 p-1.5 rounded-full hover:bg-[#E9E8F8] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-[#E9E8F8] border border-[#d7d4f2] text-[#524398] mb-3">
            <Bot className="w-6 h-6 stroke-[2.2]" />
          </div>
          <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
            Launch Multi-Agent Research
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Dispatch fundamental, technical, sentiment, and risk agents for autonomous evaluation.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-2xl bg-rose-50 border border-rose-200 flex items-center space-x-2 text-xs text-rose-700 font-semibold">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Target Stock Ticker
            </label>
            <input
              type="text"
              required
              placeholder="e.g. RELIANCE, TCS, INFY, AAPL"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              className="w-full px-4 py-2.5 bg-white border border-[#E9E8F8] rounded-2xl text-xs text-slate-800 font-mono font-bold focus:outline-none focus:border-[#8DB9F0] focus:ring-2 focus:ring-[#8DB9F0]/30 transition-all uppercase shadow-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center space-x-1">
                <Globe2 className="w-3.5 h-3.5 text-[#3575cb]" />
                <span>Exchange</span>
              </label>
              <select
                value={market}
                onChange={(e) => setMarket(e.target.value)}
                className="w-full px-3 py-2.5 bg-white border border-[#E9E8F8] rounded-2xl text-xs text-slate-800 font-bold focus:outline-none focus:border-[#8DB9F0] focus:ring-2 focus:ring-[#8DB9F0]/30 transition-all cursor-pointer shadow-sm"
              >
                {MARKETS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center space-x-1">
                <Clock className="w-3.5 h-3.5 text-[#524398]" />
                <span>Lookback</span>
              </label>
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="w-full px-3 py-2.5 bg-white border border-[#E9E8F8] rounded-2xl text-xs text-slate-800 font-bold focus:outline-none focus:border-[#8DB9F0] focus:ring-2 focus:ring-[#8DB9F0]/30 transition-all cursor-pointer shadow-sm"
              >
                {PERIODS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || !ticker.trim()}
            className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-[#F5B69E] to-[#ea9e80] hover:from-[#f0a68d] hover:to-[#df8b6b] disabled:opacity-40 text-slate-900 font-extrabold text-xs rounded-2xl shadow-lg shadow-[#F5B69E]/35 transition-all flex items-center justify-center space-x-2 glow-peach"
          >
            {isSubmitting ? (
              <span className="flex items-center space-x-2">
                <span className="w-3.5 h-3.5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin"></span>
                <span>Synthesizing Agent Pipeline...</span>
              </span>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Dispatch Research Task</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
