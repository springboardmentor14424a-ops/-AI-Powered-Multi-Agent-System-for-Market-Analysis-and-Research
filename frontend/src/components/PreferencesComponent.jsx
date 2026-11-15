import React, { useState, useEffect } from 'react';
import { 
  Sliders, 
  Save, 
  CheckCircle2, 
  AlertCircle, 
  Globe2, 
  Clock, 
  Info
} from 'lucide-react';
import { preferencesApi } from '../services/api';

const MARKETS = [
  { id: 'NSE', label: 'NSE (National Stock Exchange of India)', country: 'India' },
  { id: 'BSE', label: 'BSE (Bombay Stock Exchange)', country: 'India' },
  { id: 'NASDAQ', label: 'NASDAQ (National Association of Securities Dealers)', country: 'US' },
  { id: 'NYSE', label: 'NYSE (New York Stock Exchange)', country: 'US' }
];

const PERIODS = [
  '1 Month',
  '3 Months',
  '6 Months',
  '1 Year',
  '5 Years'
];

export default function PreferencesComponent({ onPreferencesUpdated }) {
  const [preferredMarket, setPreferredMarket] = useState('NSE');
  const [preferredPeriod, setPreferredPeriod] = useState('6 Months');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  // Load Preferences on Mount
  useEffect(() => {
    const fetchPreferences = async () => {
      setIsLoading(true);
      try {
        const data = await preferencesApi.get();
        if (data) {
          setPreferredMarket(data.preferred_market || 'NSE');
          setPreferredPeriod(data.preferred_analysis_period || '6 Months');
          if (onPreferencesUpdated) {
            onPreferencesUpdated(data);
          }
        }
      } catch (err) {
        console.error("Failed to load user preferences:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPreferences();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setMessage({ text: '', type: '' });

    try {
      const updated = await preferencesApi.update(preferredMarket, preferredPeriod);
      setMessage({ text: 'Workspace preferences updated successfully!', type: 'success' });
      if (onPreferencesUpdated) {
        onPreferencesUpdated(updated);
      }
      setTimeout(() => setMessage({ text: '', type: '' }), 3500);
    } catch (err) {
      setMessage({ text: err.message || 'Failed to save preferences.', type: 'error' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="glass-panel rounded-3xl p-5 sm:p-7 shadow-xl shadow-[#8DB9F0]/10">
      {/* Header */}
      <div className="flex items-center space-x-2 pb-5 border-b border-[#E9E8F8]">
        <span className="p-2 rounded-xl bg-[#E9E8F8] text-[#524398] border border-[#d7d4f2]">
          <Sliders className="w-4 h-4" />
        </span>
        <div>
          <h3 className="text-lg font-extrabold text-slate-900 tracking-tight">
            Research Workspace Preferences
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure your default target market and historical analysis timeframe.
          </p>
        </div>
      </div>

      {/* Alert Banner */}
      {message.text && (
        <div className={`mt-4 p-3 rounded-2xl border flex items-center space-x-2 text-xs font-semibold ${
          message.type === 'success'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : 'bg-rose-50 border-rose-200 text-rose-800'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Preferences Form */}
      <form onSubmit={handleSave} className="mt-5 space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Target Market Dropdown */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center space-x-1.5">
              <Globe2 className="w-3.5 h-3.5 text-[#3575cb]" />
              <span>Target Financial Market</span>
            </label>
            <div className="relative">
              <select
                disabled={isLoading}
                value={preferredMarket}
                onChange={(e) => setPreferredMarket(e.target.value)}
                className="w-full px-4 py-2.5 bg-white/90 border border-[#E9E8F8] rounded-2xl text-xs text-slate-800 font-bold focus:outline-none focus:border-[#8DB9F0] focus:ring-2 focus:ring-[#8DB9F0]/30 transition-all cursor-pointer appearance-none shadow-sm"
              >
                {MARKETS.map((m) => (
                  <option key={m.id} value={m.id} className="bg-white text-slate-800">
                    {m.id} - {m.label}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3.5 text-slate-400">
                <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                  <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/>
                </svg>
              </div>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              Selects the exchange for live price queries and agent financial filings.
            </p>
          </div>

          {/* Analysis Period Dropdown */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center space-x-1.5">
              <Clock className="w-3.5 h-3.5 text-[#524398]" />
              <span>Default Analysis Period</span>
            </label>
            <div className="relative">
              <select
                disabled={isLoading}
                value={preferredPeriod}
                onChange={(e) => setPreferredPeriod(e.target.value)}
                className="w-full px-4 py-2.5 bg-white/90 border border-[#E9E8F8] rounded-2xl text-xs text-slate-800 font-bold focus:outline-none focus:border-[#8DB9F0] focus:ring-2 focus:ring-[#8DB9F0]/30 transition-all cursor-pointer appearance-none shadow-sm"
              >
                {PERIODS.map((period) => (
                  <option key={period} value={period} className="bg-white text-slate-800">
                    {period} Lookback Horizon
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3.5 text-slate-400">
                <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                  <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/>
                </svg>
              </div>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              Historical candle duration & statement cycles evaluated by the research models.
            </p>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center space-x-1.5 text-[11px] text-slate-500 font-mono">
            <Info className="w-3.5 h-3.5 text-[#8DB9F0] shrink-0" />
            <span>Preferences are stored in your PostgreSQL UserPreference profile.</span>
          </div>

          <button
            type="submit"
            disabled={isSaving || isLoading}
            className="px-5 py-2.5 bg-gradient-to-r from-[#F5B69E] to-[#ea9e80] hover:from-[#f0a68d] hover:to-[#df8b6b] disabled:opacity-40 text-slate-900 font-extrabold text-xs rounded-2xl shadow-md shadow-[#F5B69E]/30 transition-all flex items-center space-x-1.5 glow-peach"
          >
            {isSaving ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin"></span>
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5" />
                <span>Save Preferences</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
