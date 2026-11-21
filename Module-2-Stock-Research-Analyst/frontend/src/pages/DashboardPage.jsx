import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  TrendingUp, LogOut, Plus, Search, X, ChevronDown,
  BookOpen, Star, Settings, FileText, Trash2, Eye,
  BarChart2, Clock, CheckCircle, AlertCircle, Loader2, LineChart
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import MarketDataTab from '../components/MarketDataTab';

/* ─── Status Badge ─── */
function StatusBadge({ status }) {
  const map = {
    Pending: 'bg-yellow-900/40 text-yellow-400 border border-yellow-800/50',
    Processing: 'bg-emerald-900/40 text-emerald-400 border border-emerald-800/50',
    Completed: 'bg-green-900/40 text-green-400 border border-green-800/50',
    Failed: 'bg-red-900/40 text-red-400 border border-red-800/50',
  };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${map[status] || map.Pending}`}>
      {status}
    </span>
  );
}

/* ─── Stat Card ─── */
function StatCard({ label, value, icon: Icon, color }) {
  return (
    <div className="bg-gray-900/80 border border-emerald-900/50 rounded-xl p-4 flex items-center gap-4">
      <div className={`p-2.5 rounded-lg ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-400">{label}</p>
      </div>
    </div>
  );
}

/* ─── New Research Modal ─── */
function NewResearchModal({ onClose, onSubmit, prefill }) {
  const [form, setForm] = useState({
    company_name: prefill?.company_name || '',
    ticker: prefill?.ticker || '',
    market: prefill?.market || 'NASDAQ',
    analysis_period: '1 Year',
  });
  const [loading, setLoading] = useState(false);

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    if (!form.company_name || !form.ticker) {
      toast.error('Company name and ticker are required.');
      return;
    }
    setLoading(true);
    try {
      await onSubmit(form);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-emerald-900/50 rounded-2xl w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between p-6 border-b border-emerald-900/30">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-emerald-400" />
            New Research Task
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Company Name</label>
            <input
              name="company_name"
              value={form.company_name}
              onChange={handle}
              placeholder="e.g. Apple Inc."
              className="w-full bg-gray-800 border border-gray-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 outline-none transition-all"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Ticker Symbol</label>
            <input
              name="ticker"
              value={form.ticker}
              onChange={handle}
              placeholder="e.g. AAPL"
              className="w-full bg-gray-800 border border-gray-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 outline-none transition-all"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Market</label>
            <select
              name="market"
              value={form.market}
              onChange={handle}
              className="w-full bg-gray-800 border border-gray-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-lg px-4 py-2.5 text-white outline-none transition-all"
            >
              {['NSE', 'BSE', 'NASDAQ', 'NYSE'].map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Analysis Period</label>
            <select
              name="analysis_period"
              value={form.analysis_period}
              onChange={handle}
              className="w-full bg-gray-800 border border-gray-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-lg px-4 py-2.5 text-white outline-none transition-all"
            >
              {['1 Month', '3 Months', '6 Months', '1 Year', '5 Years'].map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium py-2.5 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Start Research
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ─── Tab 1: Research History ─── */
function ResearchHistoryTab() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [reportModal, setReportModal] = useState(null); // { taskId, companyName, reportContent }
  const [loadingReport, setLoadingReport] = useState(false);

  const fetchTasks = () => {
    api.get('/research/tasks')
      .then((r) => setTasks(r.data))
      .catch(() => toast.error('Failed to load research tasks.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleNewResearch = async (form) => {
    try {
      const res = await api.post('/research/tasks', form);
      setTasks((prev) => [res.data, ...prev]);
      toast.success('Research task created! Processing will begin shortly...');

      // Poll for status updates (the backend processes in background)
      const pollInterval = setInterval(async () => {
        try {
          const updated = await api.get('/research/tasks');
          setTasks(updated.data);
          const thisTask = updated.data.find((t) => t.id === res.data.id);
          if (thisTask && (thisTask.status === 'Completed' || thisTask.status === 'Failed')) {
            clearInterval(pollInterval);
            if (thisTask.status === 'Completed') {
              toast.success(`Research on ${thisTask.company_name} completed!`);
            } else {
              toast.error(`Research on ${thisTask.company_name} failed.`);
            }
          }
        } catch {
          clearInterval(pollInterval);
        }
      }, 3000);

      // Clear poll after 60s max
      setTimeout(() => clearInterval(pollInterval), 60000);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create task.');
      throw err;
    }
  };

  const viewReport = async (task) => {
    setLoadingReport(true);
    try {
      const res = await api.get(`/research/tasks/${task.id}/report`);
      setReportModal({
        taskId: task.id,
        companyName: task.company_name,
        ticker: task.ticker,
        reportContent: res.data.report_content,
        generatedAt: res.data.generated_at,
      });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load report.');
    } finally {
      setLoadingReport(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">Research History</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchTasks}
            className="text-gray-400 hover:text-emerald-400 transition-colors p-2"
            title="Refresh"
          >
            <BarChart2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Research
          </button>
        </div>
      </div>

      {tasks.length === 0 ? (
        <div className="text-center py-16 bg-gray-900/40 rounded-xl border border-emerald-900/30">
          <BarChart2 className="w-12 h-12 text-emerald-900 mx-auto mb-3" />
          <p className="text-gray-400 font-medium">No research tasks yet</p>
          <p className="text-gray-600 text-sm mt-1">Click "New Research" to get started</p>
        </div>
      ) : (
        <div className="bg-gray-900/60 rounded-xl border border-emerald-900/30 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-emerald-900/30 bg-gray-900/80">
                  {['Company', 'Ticker', 'Market', 'Period', 'Date', 'Status', 'Action'].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tasks.map((t, i) => (
                  <tr
                    key={t.id}
                    className={`border-b border-emerald-900/20 hover:bg-emerald-900/10 transition-colors ${
                      i % 2 === 0 ? 'bg-transparent' : 'bg-gray-900/20'
                    }`}
                  >
                    <td className="px-4 py-3 text-white font-medium">{t.company_name}</td>
                    <td className="px-4 py-3 text-emerald-400 font-mono font-semibold">{t.ticker}</td>
                    <td className="px-4 py-3 text-gray-300">{t.market}</td>
                    <td className="px-4 py-3 text-gray-300">{t.analysis_period}</td>
                    <td className="px-4 py-3 text-gray-400">
                      {new Date(t.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="px-4 py-3">
                      {t.status === 'Completed' ? (
                        <button
                          onClick={() => viewReport(t)}
                          disabled={loadingReport}
                          className="text-emerald-400 hover:text-emerald-300 flex items-center gap-1 text-xs font-medium transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          View Report
                        </button>
                      ) : t.status === 'Processing' ? (
                        <span className="text-emerald-400 flex items-center gap-1 text-xs font-medium">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          Processing...
                        </span>
                      ) : t.status === 'Failed' ? (
                        <span className="text-red-400 text-xs font-medium">Failed</span>
                      ) : (
                        <span className="text-yellow-400 flex items-center gap-1 text-xs font-medium">
                          <Clock className="w-3.5 h-3.5" />
                          Queued
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showModal && (
        <NewResearchModal
          onClose={() => setShowModal(false)}
          onSubmit={handleNewResearch}
        />
      )}

      {/* Research Report Modal */}
      {reportModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-emerald-900/50 rounded-2xl w-full max-w-3xl shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-emerald-900/30 flex-shrink-0">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-400" />
                Research Report — {reportModal.companyName} ({reportModal.ticker})
              </h2>
              <button onClick={() => setReportModal(null)} className="text-gray-500 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-1">
              <div className="prose prose-invert prose-sm max-w-none">
                {reportModal.reportContent.split('\n').map((line, idx) => {
                  if (line.startsWith('# ')) {
                    return <h1 key={idx} className="text-xl font-bold text-white mt-4 mb-2">{line.substring(2)}</h1>;
                  }
                  if (line.startsWith('## ')) {
                    return <h2 key={idx} className="text-base font-bold text-emerald-400 mt-5 mb-2 border-b border-emerald-900/30 pb-1">{line.substring(3)}</h2>;
                  }
                  if (line.startsWith('**') && line.endsWith('**')) {
                    return <p key={idx} className="text-gray-300 font-medium text-sm mb-1">{line.replace(/\*\*/g, '')}</p>;
                  }
                  if (line.startsWith('- **')) {
                    const parts = line.substring(2).split(':** ');
                    if (parts.length === 2) {
                      return (
                        <div key={idx} className="flex items-start gap-2 text-sm py-0.5">
                          <span className="text-emerald-400 mt-0.5">•</span>
                          <span>
                            <span className="text-white font-medium">{parts[0].replace(/\*\*/g, '')}:</span>{' '}
                            <span className="text-gray-300">{parts[1].replace(/\*\*/g, '')}</span>
                          </span>
                        </div>
                      );
                    }
                  }
                  if (line.startsWith('---')) {
                    return <hr key={idx} className="border-emerald-900/30 my-4" />;
                  }
                  if (line.startsWith('*') && line.endsWith('*')) {
                    return <p key={idx} className="text-gray-500 text-xs italic mt-2">{line.replace(/\*/g, '')}</p>;
                  }
                  if (line.trim() === '') {
                    return <div key={idx} className="h-2" />;
                  }
                  return <p key={idx} className="text-gray-300 text-sm leading-relaxed">{line}</p>;
                })}
              </div>
            </div>
            <div className="p-4 border-t border-emerald-900/30 flex-shrink-0 flex justify-end">
              <button
                onClick={() => setReportModal(null)}
                className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Tab 2: Watchlist ─── */
function WatchlistTab({ onSelectForOHLCV }) {
  const [query, setQuery] = useState('');
  const [market, setMarket] = useState('NASDAQ');
  const [searchResults, setSearchResults] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [searching, setSearching] = useState(false);
  const [loadingWatchlist, setLoadingWatchlist] = useState(true);
  const [showResearchModal, setShowResearchModal] = useState(false);
  const [prefill, setPrefill] = useState(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    api.get('/watchlist')
      .then((r) => setWatchlist(r.data))
      .catch(() => toast.error('Failed to load watchlist.'))
      .finally(() => setLoadingWatchlist(false));
  }, []);

  const handleSearch = useCallback((q, mkt) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!q.trim()) { setSearchResults([]); return; }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await api.get('/stocks/search', { params: { q, market: mkt } });
        setSearchResults(res.data);
      } catch {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 500);
  }, []);

  const onQueryChange = (e) => {
    setQuery(e.target.value);
    handleSearch(e.target.value, market);
  };
  const onMarketChange = (e) => {
    setMarket(e.target.value);
    handleSearch(query, e.target.value);
  };

  const addToWatchlist = async (stock) => {
    try {
      const res = await api.post('/watchlist', {
        ticker: stock.ticker,
        company_name: stock.company_name,
        market: stock.market,
      });
      setWatchlist((prev) => [res.data, ...prev]);
      toast.success(`${stock.ticker} added to watchlist!`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add to watchlist.');
    }
  };

  const removeFromWatchlist = async (id) => {
    try {
      await api.delete(`/watchlist/${id}`);
      setWatchlist((prev) => prev.filter((s) => s.id !== id));
      toast.success('Removed from watchlist.');
    } catch {
      toast.error('Failed to remove.');
    }
  };

  const openResearch = (stock) => {
    setPrefill(stock);
    setShowResearchModal(true);
  };

  const handleNewResearch = async (form) => {
    try {
      await api.post('/research/tasks', form);
      toast.success('Research task created!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create task.');
      throw err;
    }
  };

  return (
    <div className="space-y-6">
      {/* Search */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Search Stocks</h2>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              value={query}
              onChange={onQueryChange}
              placeholder="Search by company name or ticker..."
              className="w-full bg-gray-800/60 border border-gray-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-500 outline-none transition-all"
            />
          </div>
          <select
            value={market}
            onChange={onMarketChange}
            className="bg-gray-800 border border-gray-700 focus:border-emerald-500 rounded-lg px-3 py-2.5 text-white outline-none text-sm"
          >
            {['NSE', 'BSE', 'NASDAQ', 'NYSE'].map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        {/* Search Results */}
        {(searching || searchResults.length > 0) && (
          <div className="mt-3 bg-gray-900/80 border border-emerald-900/40 rounded-xl overflow-hidden">
            {searching ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-5 h-5 text-emerald-400 animate-spin" />
              </div>
            ) : (
              <div className="divide-y divide-emerald-900/20">
                {searchResults.map((s, i) => (
                  <div key={i} className="flex items-center justify-between p-4 hover:bg-emerald-900/10 transition-colors">
                    <div>
                      <p className="text-white font-medium">{s.company_name}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        <span className="text-emerald-400 font-mono font-semibold">{s.ticker}</span>
                        {s.sector && <span> · {s.sector}</span>}
                        {s.price && <span> · ${s.price}</span>}
                      </p>
                    </div>
                    <button
                      onClick={() => addToWatchlist(s)}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3 py-1.5 rounded-lg font-medium flex items-center gap-1 transition-colors"
                    >
                      <Star className="w-3.5 h-3.5" />
                      Add
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* My Watchlist */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">My Watchlist</h2>
        {loadingWatchlist ? (
          <div className="flex justify-center py-10">
            <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
          </div>
        ) : watchlist.length === 0 ? (
          <div className="text-center py-16 bg-gray-900/40 rounded-xl border border-emerald-900/30">
            <Star className="w-12 h-12 text-emerald-900 mx-auto mb-3" />
            <p className="text-gray-400 font-medium">Your watchlist is empty</p>
            <p className="text-gray-600 text-sm mt-1">Search for stocks above and add them here</p>
          </div>
        ) : (
          <div className="bg-gray-900/60 rounded-xl border border-emerald-900/30 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-emerald-900/30 bg-gray-900/80">
                    {['Ticker', 'Company', 'Market', 'Date Added', 'Actions'].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {watchlist.map((s, i) => (
                    <tr
                      key={s.id}
                      className={`border-b border-emerald-900/20 hover:bg-emerald-900/10 transition-colors ${
                        i % 2 === 0 ? 'bg-transparent' : 'bg-gray-900/20'
                      }`}
                    >
                      <td className="px-4 py-3 text-emerald-400 font-mono font-semibold">{s.ticker}</td>
                      <td className="px-4 py-3 text-white">{s.company_name}</td>
                      <td className="px-4 py-3 text-gray-300">{s.market}</td>
                      <td className="px-4 py-3 text-gray-400">
                        {new Date(s.added_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => onSelectForOHLCV && onSelectForOHLCV(s)}
                            className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 text-xs font-medium transition-colors"
                          >
                            <TrendingUp className="w-3.5 h-3.5" />
                            OHLCV
                          </button>
                          <span className="text-gray-700">|</span>
                          <button
                            onClick={() => removeFromWatchlist(s.id)}
                            className="text-red-400 hover:text-red-300 flex items-center gap-1 text-xs font-medium transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            Remove
                          </button>
                          <span className="text-gray-700">|</span>
                          <button
                            onClick={() => openResearch(s)}
                            className="text-emerald-400 hover:text-emerald-300 flex items-center gap-1 text-xs font-medium transition-colors"
                          >
                            <BarChart2 className="w-3.5 h-3.5" />
                            Research
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {showResearchModal && (
        <NewResearchModal
          prefill={prefill}
          onClose={() => setShowResearchModal(false)}
          onSubmit={handleNewResearch}
        />
      )}
    </div>
  );
}

/* ─── Tab 3: Preferences ─── */
function PreferencesTab() {
  const [prefs, setPrefs] = useState({ market: 'NASDAQ', analysis_period: '1 Year' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/preferences')
      .then((r) => setPrefs(r.data))
      .catch(() => {/* no prefs yet is fine */})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/preferences', prefs);
      toast.success('Preferences saved!');
    } catch {
      toast.error('Failed to save preferences.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-md">
      <h2 className="text-lg font-semibold text-white mb-6">Your Preferences</h2>
      <div className="bg-gray-900/60 border border-emerald-900/30 rounded-xl p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">Default Market</label>
          <select
            value={prefs.market}
            onChange={(e) => setPrefs({ ...prefs, market: e.target.value })}
            className="w-full bg-gray-800 border border-gray-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-lg px-4 py-2.5 text-white outline-none transition-all"
          >
            {['NSE', 'BSE', 'NASDAQ', 'NYSE'].map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">Default Analysis Period</label>
          <select
            value={prefs.analysis_period}
            onChange={(e) => setPrefs({ ...prefs, analysis_period: e.target.value })}
            className="w-full bg-gray-800 border border-gray-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-lg px-4 py-2.5 text-white outline-none transition-all"
          >
            {['1 Month', '3 Months', '6 Months', '1 Year', '5 Years'].map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Settings className="w-4 h-4" />}
          Save Preferences
        </button>
      </div>
    </div>
  );
}

/* ─── Main Dashboard ─── */
export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('market-data');
  const [selectedStockForOHLCV, setSelectedStockForOHLCV] = useState(null);
  const [showResearchModal, setShowResearchModal] = useState(false);
  const [researchPrefill, setResearchPrefill] = useState(null);
  const [tasks, setTasks] = useState([]);

  const refreshTasks = () => {
    api.get('/research/tasks')
      .then((r) => setTasks(r.data))
      .catch(() => {});
  };

  useEffect(() => {
    refreshTasks();
  }, [activeTab]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleSelectForOHLCV = (stock) => {
    setSelectedStockForOHLCV(stock.ticker);
    setActiveTab('market-data');
  };

  const handleStartResearch = (stock) => {
    setResearchPrefill(stock);
    setShowResearchModal(true);
  };

  const handleNewResearchSubmit = async (form) => {
    try {
      const res = await api.post('/research/tasks', form);
      setTasks((prev) => [res.data, ...prev]);
      toast.success('Research task started! Generating analysis report...');
      setActiveTab('history');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create task.');
      throw err;
    }
  };

  const stats = {
    total: tasks.length,
    completed: tasks.filter((t) => t.status === 'Completed').length,
    processing: tasks.filter((t) => t.status === 'Processing').length,
    failed: tasks.filter((t) => t.status === 'Failed').length,
  };

  const tabs = [
    { id: 'market-data', label: 'Stock Search & OHLCV', icon: TrendingUp },
    { id: 'history', label: 'Research History', icon: BookOpen },
    { id: 'watchlist', label: 'Watchlist', icon: Star },
    { id: 'preferences', label: 'Preferences', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-emerald-950 to-gray-950">
      {/* Navbar */}
      <nav className="sticky top-0 z-40 bg-gray-950/90 border-b border-emerald-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-1.5 bg-emerald-600 rounded-lg">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <span className="text-white font-bold text-lg hidden sm:block">Stock Research Analyst</span>
            <span className="text-white font-bold text-base sm:hidden">SRA</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400 hidden sm:block">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white px-3 py-1.5 rounded-lg text-sm flex items-center gap-2 transition-colors border border-gray-700"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:block">Logout</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1">
            Welcome back, <span className="text-emerald-400">{user?.full_name?.split(' ')[0] || 'Investor'}</span>
          </h1>
          <p className="text-gray-400 text-sm">Real-time stock search, historical market analysis, and research platform.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Tasks" value={stats.total} icon={BarChart2} color="bg-emerald-700" />
          <StatCard label="Completed" value={stats.completed} icon={CheckCircle} color="bg-green-700" />
          <StatCard label="Processing" value={stats.processing} icon={Loader2} color="bg-emerald-600" />
          <StatCard label="Failed" value={stats.failed} icon={AlertCircle} color="bg-red-700" />
        </div>

        {/* Tab Bar */}
        <div className="flex gap-1 p-1 bg-gray-900/60 border border-emerald-900/30 rounded-xl mb-6 w-fit">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === id
                  ? 'bg-emerald-600 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:block">{label}</span>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="bg-gray-900/40 border border-emerald-900/30 rounded-2xl p-6">
          {activeTab === 'market-data' && (
            <MarketDataTab
              key={selectedStockForOHLCV}
              initialTicker={selectedStockForOHLCV}
              onStartResearch={handleStartResearch}
            />
          )}
          {activeTab === 'history' && <ResearchHistoryTab />}
          {activeTab === 'watchlist' && <WatchlistTab onSelectForOHLCV={handleSelectForOHLCV} />}
          {activeTab === 'preferences' && <PreferencesTab />}
        </div>

        {/* Research Modal */}
        {showResearchModal && (
          <NewResearchModal
            prefill={researchPrefill}
            onClose={() => setShowResearchModal(false)}
            onSubmit={handleNewResearchSubmit}
          />
        )}
      </main>
    </div>
  );
}
