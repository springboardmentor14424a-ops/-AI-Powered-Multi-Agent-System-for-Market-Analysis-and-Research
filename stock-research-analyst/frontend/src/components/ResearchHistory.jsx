import { useCallback, useEffect, useState } from "react";
import { api, periodLabel } from "../api.js";
import StockSearch from "./StockSearch.jsx";

const STATUS_STYLES = {
  Pending: "bg-slate-100 text-slate-700",
  Processing: "bg-amber-100 text-amber-800",
  Completed: "bg-green-100 text-green-800",
  Failed: "bg-red-100 text-red-800",
};

const fmtDate = (iso) => (iso ? new Date(iso).toLocaleString() : "—");

export default function ResearchHistory({ prefs, onStartResearch, refreshKey }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [report, setReport] = useState(null);
  const [starting, setStarting] = useState(null);

  const load = useCallback(() => {
    return api
      .getResearchHistory()
      .then((t) => {
        setTasks(t);
        setError("");
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  // keep polling while any task is still running
  const hasActive = tasks.some((t) => t.status === "Pending" || t.status === "Processing");
  useEffect(() => {
    if (!hasActive) return;
    const id = setInterval(load, 2000);
    return () => clearInterval(id);
  }, [hasActive, load]);

  async function start(stock) {
    setStarting(stock.ticker);
    setError("");
    try {
      await onStartResearch(stock.ticker, stock.market);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setStarting(null);
    }
  }

  async function openReport(task) {
    try {
      setReport(await api.getResearch(task.task_id));
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="space-y-6">
      <section className="card space-y-3">
        <h2 className="text-lg font-semibold">Start new research</h2>
        <p className="text-sm text-slate-500">
          Uses your saved period ({periodLabel(prefs?.analysis_period)}). Change it under Preferences.
        </p>
        <StockSearch defaultMarket={prefs?.market ?? "NASDAQ"} actionLabel="Research" onSelect={start} busyTicker={starting} />
      </section>

      <section className="card">
        <h2 className="mb-3 text-lg font-semibold">Research history</h2>
        {error && <p role="alert" className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {loading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : tasks.length === 0 ? (
          <p className="text-sm text-slate-500">No research yet. Search for a stock above to get started.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b text-xs uppercase text-slate-500">
                <tr>
                  <th className="py-2 pr-4">Company</th>
                  <th className="py-2 pr-4">Market</th>
                  <th className="py-2 pr-4">Period</th>
                  <th className="py-2 pr-4">Date</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {tasks.map((t) => (
                  <tr key={t.task_id}>
                    <td className="py-2 pr-4">
                      <span className="font-medium">{t.company_name}</span>{" "}
                      <span className="text-slate-500">({t.ticker})</span>
                    </td>
                    <td className="py-2 pr-4">{t.market}</td>
                    <td className="py-2 pr-4">{periodLabel(t.analysis_period)}</td>
                    <td className="py-2 pr-4">{fmtDate(t.created_at)}</td>
                    <td className="py-2 pr-4">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[t.status] ?? ""}`}>{t.status}</span>
                      {t.status === "Failed" && t.error_message && (
                        <p className="mt-1 text-xs text-red-600">{t.error_message}</p>
                      )}
                    </td>
                    <td className="py-2 text-right">
                      {t.status === "Completed" && (
                        <button className="btn-secondary" onClick={() => openReport(t)}>Open report</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {report && (
        <div className="fixed inset-0 z-10 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true">
          <div className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-6 shadow-xl">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-semibold">{report.company_name} ({report.ticker}) report</h3>
              <button className="btn-secondary" onClick={() => setReport(null)}>Close</button>
            </div>
            {/* rendered as plain text on purpose: report content is never injected as HTML */}
            <pre className="whitespace-pre-wrap font-sans text-sm text-slate-700">{report.report}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
