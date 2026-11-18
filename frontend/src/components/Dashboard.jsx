import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Sparkles, 
  Layers, 
  History as HistoryIcon, 
  Sliders, 
  Database,
  BarChart2
} from 'lucide-react';
import WatchlistComponent from './WatchlistComponent';
import HistoryComponent from './HistoryComponent';
import PreferencesComponent from './PreferencesComponent';
import MarketDataWorkspace from './MarketDataWorkspace';
import TaskReportModal from './TaskReportModal';
import LaunchTaskModal from './LaunchTaskModal';

export default function Dashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('market_data'); // 'market_data' | 'workspace' | 'history' | 'preferences'
  const [currentMarket, setCurrentMarket] = useState('NSE');
  const [currentPeriod, setCurrentPeriod] = useState('6 Months');
  const [selectedReport, setSelectedReport] = useState(null);
  const [launchModalState, setLaunchModalState] = useState({ isOpen: false, ticker: '' });
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

  const handlePreferencesUpdated = (prefs) => {
    if (prefs) {
      if (prefs.preferred_market) setCurrentMarket(prefs.preferred_market);
      if (prefs.preferred_analysis_period) setCurrentPeriod(prefs.preferred_analysis_period);
    }
  };

  const handleOpenLaunchModal = (ticker = '') => {
    setLaunchModalState({ isOpen: true, ticker });
  };

  const handleTaskCreated = (newTask) => {
    // Increment refresh key to trigger re-fetch in HistoryComponent
    setHistoryRefreshKey((prev) => prev + 1);
    if (newTask) {
      setSelectedReport(newTask);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Welcome & Quick Actions Bar */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 shadow-xl shadow-[#8DB9F0]/10 relative overflow-hidden bg-gradient-to-r from-white/95 via-[#faf9fe] to-[#f0f6fd]">
        <div className="absolute right-0 top-0 w-96 h-96 bg-[#F5B69E]/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute left-1/3 bottom-0 w-80 h-80 bg-[#8DB9F0]/20 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center space-x-2 text-xs font-mono text-[#3575cb] mb-2 font-bold">
              <span className="w-2 h-2 rounded-full bg-[#8DB9F0] animate-pulse"></span>
              <span>FastAPI Authenticated Workspace Active</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Welcome back, <span className="bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">{user?.full_name || 'Financial Analyst'}</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-1 max-w-xl">
              Track your equities watchlist, dispatch multi-agent research pipelines, and inspect institutional financial audits.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => handleOpenLaunchModal('')}
              className="px-5 py-3 bg-gradient-to-r from-[#F5B69E] to-[#ea9e80] hover:from-[#f0a68d] hover:to-[#df8b6b] text-slate-900 font-bold text-xs rounded-2xl shadow-lg shadow-[#F5B69E]/30 transition-all flex items-center space-x-2 glow-peach"
            >
              <Sparkles className="w-4 h-4" />
              <span>Launch New Research Task</span>
            </button>
          </div>
        </div>

        {/* Quick Context Pills */}
        <div className="mt-6 pt-5 border-t border-[#E9E8F8] flex flex-wrap items-center gap-3 text-xs font-mono">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white/90 border border-[#E9E8F8] text-slate-700 shadow-sm">
            <span className="text-slate-500">Market:</span>
            <span className="text-[#3575cb] font-bold">{currentMarket}</span>
          </div>
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white/90 border border-[#E9E8F8] text-slate-700 shadow-sm">
            <span className="text-slate-500">Analysis Lookback:</span>
            <span className="text-[#524398] font-bold">{currentPeriod}</span>
          </div>
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white/90 border border-[#E9E8F8] text-slate-700 shadow-sm">
            <Database className="w-3.5 h-3.5 text-[#8DB9F0]" />
            <span className="text-slate-500">Database:</span>
            <span className="text-slate-800 font-semibold">PostgreSQL Engine</span>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center space-x-2 border-b border-[#E9E8F8] pb-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('market_data')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-2xl text-xs font-extrabold transition-all whitespace-nowrap ${
            activeTab === 'market_data'
              ? 'bg-white text-slate-900 shadow-md shadow-[#8DB9F0]/15 border border-[#d7d4f2]'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
          }`}
        >
          <BarChart2 className="w-4 h-4 text-[#3575cb]" />
          <span>Market Data & Stock Search</span>
        </button>

        <button
          onClick={() => setActiveTab('workspace')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-2xl text-xs font-extrabold transition-all whitespace-nowrap ${
            activeTab === 'workspace'
              ? 'bg-white text-slate-900 shadow-md shadow-[#8DB9F0]/15 border border-[#d7d4f2]'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
          }`}
        >
          <Layers className="w-4 h-4 text-[#3575cb]" />
          <span>Watchlist & Live Quotes</span>
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-2xl text-xs font-extrabold transition-all whitespace-nowrap ${
            activeTab === 'history'
              ? 'bg-white text-slate-900 shadow-md shadow-[#8DB9F0]/15 border border-[#d7d4f2]'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
          }`}
        >
          <HistoryIcon className="w-4 h-4 text-[#524398]" />
          <span>Research Task History</span>
        </button>

        <button
          onClick={() => setActiveTab('preferences')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-2xl text-xs font-extrabold transition-all whitespace-nowrap ${
            activeTab === 'preferences'
              ? 'bg-white text-slate-900 shadow-md shadow-[#8DB9F0]/15 border border-[#d7d4f2]'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
          }`}
        >
          <Sliders className="w-4 h-4 text-[#be6543]" />
          <span>Workspace Preferences</span>
        </button>
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === 'market_data' && (
          <MarketDataWorkspace onLaunchTask={(ticker) => handleOpenLaunchModal(ticker)} />
        )}

        {activeTab === 'workspace' && (
          <div className="space-y-8">
            <WatchlistComponent 
              onLaunchTask={(ticker) => handleOpenLaunchModal(ticker)} 
              currentMarket={currentMarket}
            />

            {/* Quick overview of latest history */}
            <HistoryComponent 
              onViewReport={(report) => setSelectedReport(report)}
              refreshTrigger={historyRefreshKey}
            />
          </div>
        )}

        {activeTab === 'history' && (
          <HistoryComponent 
            onViewReport={(report) => setSelectedReport(report)}
            refreshTrigger={historyRefreshKey}
          />
        )}

        {activeTab === 'preferences' && (
          <PreferencesComponent onPreferencesUpdated={handlePreferencesUpdated} />
        )}
      </div>

      {/* Modals */}
      <LaunchTaskModal
        isOpen={launchModalState.isOpen}
        onClose={() => setLaunchModalState({ isOpen: false, ticker: '' })}
        initialTicker={launchModalState.ticker}
        defaultMarket={currentMarket}
        defaultPeriod={currentPeriod}
        onTaskCreated={handleTaskCreated}
      />

      <TaskReportModal
        task={selectedReport}
        onClose={() => setSelectedReport(null)}
      />
    </div>
  );
}
