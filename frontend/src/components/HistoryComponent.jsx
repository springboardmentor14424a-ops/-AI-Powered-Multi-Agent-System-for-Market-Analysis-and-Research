import React, { useState, useEffect } from 'react';
import { 
  History, 
  FileText, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  Eye
} from 'lucide-react';
import { historyApi } from '../services/api';

export default function HistoryComponent({ onViewReport, refreshTrigger }) {
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadHistory = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await historyApi.getAll();
      setTasks(data);
    } catch (err) {
      setError(err.message || 'Failed to load research task history.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [refreshTrigger]);

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return (
          <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" />
            <span>Completed</span>
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-[11px] font-bold bg-[#8DB9F0]/20 text-[#22559c] border border-[#adcff6]">
            <RefreshCw className="w-3 h-3 animate-spin" />
            <span>Processing</span>
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-[11px] font-bold bg-[#F5B69E]/25 text-[#9b5136] border border-[#fad1c2]">
            <Clock className="w-3 h-3" />
            <span>Pending</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
            <AlertTriangle className="w-3 h-3" />
            <span>{status || 'Failed'}</span>
          </span>
        );
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return '---';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="glass-panel rounded-3xl p-5 sm:p-7 shadow-xl shadow-[#8DB9F0]/10">
      {/* Header */}
      <div className="flex items-center justify-between pb-5 border-b border-[#E9E8F8]">
        <div className="flex items-center space-x-2">
          <span className="p-2 rounded-xl bg-[#E9E8F8] text-[#524398] border border-[#d7d4f2]">
            <History className="w-4 h-4" />
          </span>
          <div>
            <h3 className="text-lg font-extrabold text-slate-900 tracking-tight">
              Research Task History
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Review generated multi-agent analysis reports and task statuses.
            </p>
          </div>
        </div>

        <button
          onClick={loadHistory}
          disabled={isLoading}
          className="flex items-center space-x-1.5 text-xs text-slate-600 hover:text-slate-900 bg-white/90 border border-[#E9E8F8] rounded-xl px-3 py-1.5 shadow-sm transition-all font-semibold"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-[#8DB9F0]' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-semibold">
          {error}
        </div>
      )}

      {/* Task Table */}
      <div className="mt-5 overflow-x-auto">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-slate-500 font-mono flex items-center justify-center space-x-2">
            <RefreshCw className="w-4 h-4 animate-spin text-[#8DB9F0]" />
            <span>Loading task history from database...</span>
          </div>
        ) : tasks.length === 0 ? (
          <div className="py-12 text-center border-2 border-dashed border-[#E9E8F8] rounded-3xl bg-white/40">
            <FileText className="w-8 h-8 text-[#adcff6] mx-auto mb-2" />
            <p className="text-sm font-bold text-slate-700">No research tasks initiated yet.</p>
            <p className="text-xs text-slate-500 mt-1">
              Select any stock from your watchlist or use the launcher above to dispatch your first research agent.
            </p>
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E9E8F8] text-[11px] font-mono text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-4 font-bold">Company & Ticker</th>
                <th className="py-3 px-4 font-bold">Market</th>
                <th className="py-3 px-4 font-bold">Analysis Period</th>
                <th className="py-3 px-4 font-bold">Research Date</th>
                <th className="py-3 px-4 font-bold">Research Status</th>
                <th className="py-3 px-4 text-right font-bold">Report</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E9E8F8] text-xs">
              {tasks.map((task) => (
                <tr key={task.task_id} className="hover:bg-white/80 transition-colors group">
                  <td className="py-4 px-4">
                    <div className="flex flex-col">
                      <span className="font-sans font-bold text-slate-900 group-hover:text-[#3575cb]">
                        {task.company_name || task.ticker}
                      </span>
                      <div className="flex items-center space-x-2 mt-0.5">
                        <span className="font-mono text-[11px] font-bold text-slate-500 bg-[#E9E8F8]/50 px-1.5 py-0.5 rounded border border-[#d7d4f2]/50">
                          {task.ticker}
                        </span>
                        {task.recommendation && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#E9E8F8] text-[#524398] border border-[#d7d4f2] font-sans font-bold">
                            {task.recommendation}
                          </span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-slate-700 font-semibold font-mono">
                    {task.market}
                  </td>
                  <td className="py-4 px-4 text-slate-600 font-medium font-sans">
                    {task.requested_period}
                  </td>
                  <td className="py-4 px-4 text-slate-500 text-[11px] font-mono">
                    {formatDate(task.created_at)}
                  </td>
                  <td className="py-4 px-4">
                    {getStatusBadge(task.status)}
                  </td>
                  <td className="py-4 px-4 text-right">
                    <button
                      onClick={() => onViewReport(task)}
                      className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-white hover:bg-[#E9E8F8] text-slate-800 rounded-xl text-xs font-sans font-bold transition-all border border-[#E9E8F8] shadow-sm hover:shadow"
                    >
                      <Eye className="w-3.5 h-3.5 text-[#3575cb]" />
                      <span>Open Report</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
