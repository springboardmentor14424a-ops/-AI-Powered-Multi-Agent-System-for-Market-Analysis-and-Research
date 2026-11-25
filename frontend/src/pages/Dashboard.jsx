import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";

function safeParseUser() {
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function normalizeArray(payload, key) {
  if (Array.isArray(payload)) return payload;
  if (payload && Array.isArray(payload[key])) return payload[key];
  return [];
}

function formatMarketCap(cap, currency = "") {
  if (cap === null || cap === undefined || Number.isNaN(Number(cap))) return "N/A";
  const val = Number(cap);
  const prefix = currency ? `${currency} ` : "";
  if (val >= 1e12) return `${prefix}${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `${prefix}${(val / 1e9).toFixed(2)}B`;
  if (val >= 1e6) return `${prefix}${(val / 1e6).toFixed(2)}M`;
  return `${prefix}${val.toLocaleString()}`;
}

function formatShortDate(isoOrDate) {
  if (!isoOrDate) return "—";
  const d = new Date(isoOrDate);
  if (Number.isNaN(d.getTime())) return String(isoOrDate).slice(0, 10);
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const yyyy = d.getFullYear();
  return `${mm}/${dd}/${yyyy}`;
}

function buildPolyline(series, key, minVal, span, width, height, padX, padY) {
  if (!Array.isArray(series) || series.length === 0) return "";
  const plotW = width - padX * 2;
  const plotH = height - padY * 2;
  return series
    .map((pt, idx) => {
      const val = Number(pt?.[key]);
      if (!Number.isFinite(val)) return null;
      const x =
        series.length === 1
          ? padX + plotW / 2
          : padX + (idx / (series.length - 1)) * plotW;
      const y = padY + (1 - (val - minVal) / span) * plotH;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .filter(Boolean)
    .join(" ");
}

function PriceAndSmaChart({ series = [], currency = "" }) {
  if (!Array.isArray(series) || series.length < 2) return null;

  const width = 760;
  const height = 210;
  const padX = 14;
  const padY = 18;

  const allVals = series.flatMap((pt) =>
    [pt.close, pt.sma_20, pt.sma_50].map(Number).filter(Number.isFinite)
  );
  if (allVals.length === 0) return null;

  const rawMin = Math.min(...allVals);
  const rawMax = Math.max(...allVals);
  const pad = (rawMax - rawMin) * 0.08 || 1;
  const minVal = rawMin - pad;
  const maxVal = rawMax + pad;
  const span = maxVal - minVal || 1;

  const closeLine = buildPolyline(series, "close", minVal, span, width, height, padX, padY);
  const sma20Line = buildPolyline(series, "sma_20", minVal, span, width, height, padX, padY);
  const sma50Line = buildPolyline(series, "sma_50", minVal, span, width, height, padX, padY);

  const firstPt = series[0];
  const lastPt = series[series.length - 1];
  const prefix = currency ? `${currency} ` : "";

  return (
    <div className="p-4 rounded-xl bg-[#06071A] border border-[#E6C27A]/15 space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="font-semibold text-[#F5D793]">Price & Moving Averages</span>
        <div className="flex flex-wrap items-center gap-3 text-[11px]">
          <span className="text-[#F5D793]">● Close ({prefix}{lastPt.close})</span>
          <span className="text-[#C084FC]">● SMA 20 ({prefix}{lastPt.sma_20})</span>
          <span className="text-[#38BDF8]">● SMA 50 ({prefix}{lastPt.sma_50})</span>
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-48 overflow-visible">
        {[0.25, 0.5, 0.75].map((ratio) => {
          const y = padY + ratio * (height - padY * 2);
          return (
            <line
              key={ratio}
              x1={padX}
              x2={width - padX}
              y1={y}
              y2={y}
              stroke="rgba(230,194,122,0.1)"
              strokeDasharray="3 3"
            />
          );
        })}

        {sma50Line && (
          <polyline
            fill="none"
            stroke="#38BDF8"
            strokeWidth="1.5"
            strokeDasharray="4 3"
            points={sma50Line}
          />
        )}
        {sma20Line && (
          <polyline
            fill="none"
            stroke="#C084FC"
            strokeWidth="1.5"
            points={sma20Line}
          />
        )}
        {closeLine && (
          <polyline
            fill="none"
            stroke="#F5D793"
            strokeWidth="2.2"
            points={closeLine}
          />
        )}
      </svg>

      <div className="flex items-center justify-between text-[11px] text-slate-400">
        <span>{firstPt.date}</span>
        <span>
          Range: {prefix}{rawMin.toFixed(2)} – {prefix}{rawMax.toFixed(2)}
        </span>
        <span>{lastPt.date}</span>
      </div>
    </div>
  );
}

function buildReportFromResponse(data) {
  if (data?.report) {
    return {
      ...data.report,
      profile: data.report.profile || data?.market_data?.profile || {},
      summary_metrics:
        data.report.summary_metrics || data?.market_data?.summary_metrics || {},
      chart_series:
        data.report.chart_series || data?.market_data?.chart_series || [],
    };
  }
  const bundle = data?.market_data;
  const task = data?.task;
  if (!bundle && !task) return null;

  const profile = bundle?.profile || {};
  const metrics = bundle?.summary_metrics || {};
  const validation = bundle?.validation || {};
  const retPct = Number(metrics.period_return_pct ?? 0);
  const conviction =
    retPct > 8 ? "High Conviction Buy" : retPct < -5 ? "Cautious / Underweight" : "Moderate / Hold";

  return {
    company_name: profile.company_name || task?.ticker || bundle?.symbol || "Equity",
    symbol: bundle?.symbol || task?.ticker || "",
    market: bundle?.market || task?.market || "",
    analysis_period: bundle?.analysis_period || task?.analysis_period || "",
    profile,
    summary_metrics: metrics,
    chart_series: bundle?.chart_series || [],
    cio_synthesis: {
      conviction,
      summary: task?.summary || "Market data and validation bundle retrieved.",
    },
    agents: {
      fundamental: `Sector: ${profile.sector || "N/A"} | Industry: ${profile.industry || "N/A"} | Currency: ${profile.currency || "N/A"}`,
      technical: `Latest Close: ${metrics.latest_close ?? "N/A"} | Period Return: ${retPct >= 0 ? "+" : ""}${retPct.toFixed(2)}% (${metrics.rows_count ?? 0} sessions)`,
      risk:
        validation.warnings && validation.warnings.length > 0
          ? validation.warnings.join("; ")
          : "OHLCV integrity checks passed with zero anomalies.",
    },
  };
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(safeParseUser);

  const [activeTab, setActiveTab] = useState("search");
  const [prefs, setPrefs] = useState({
    preferred_market: "NSE",
    analysis_period: "1 Year",
    risk_tolerance: "Moderate",
  });
  const [stocks, setStocks] = useState([]);
  const [history, setHistory] = useState([]);

  const [newTicker, setNewTicker] = useState("");
  const [newCompany, setNewCompany] = useState("");
  const [researchTicker, setResearchTicker] = useState("");
  const [compareTickers, setCompareTickers] = useState("");
  const [comparisonResults, setComparisonResults] = useState([]);
  const [report, setReport] = useState(null);

  const [statusMsg, setStatusMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [runningResearch, setRunningResearch] = useState(false);

  const loadWorkspace = async () => {
    try {
      const [meRes, prefRes, stocksRes, histRes] = await Promise.all([
        api.get("/auth/me").catch(() => null),
        api.get("/workspace/preferences"),
        api.get("/workspace/stocks"),
        api.get("/research/history"),
      ]);

      if (meRes?.data) {
        setUser(meRes.data);
        localStorage.setItem("user", JSON.stringify(meRes.data));
      }

      const prefPayload = prefRes.data?.preferences || prefRes.data;
      if (prefPayload && typeof prefPayload === "object") {
        setPrefs((prev) => ({ ...prev, ...prefPayload }));
      }

      setStocks(normalizeArray(stocksRes.data, "stocks"));
      setHistory(normalizeArray(histRes.data, "tasks"));
    } catch (err) {
      if (err.response?.status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("access_token");
        navigate("/login");
      } else {
        setErrorMsg("Could not load workspace data.");
      }
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("token") || localStorage.getItem("access_token");
    if (!token) {
      navigate("/login");
      return;
    }
    loadWorkspace();
  }, []);

  const safeHistory = Array.isArray(history) ? history : [];
  const safeStocks = Array.isArray(stocks) ? stocks : [];

  const stats = useMemo(() => {
    const total = safeHistory.length;
    const completed = safeHistory.filter(
      (t) => String(t.status || "").toLowerCase() === "completed"
    ).length;
    const processing = safeHistory.filter(
      (t) => String(t.status || "").toLowerCase() === "processing"
    ).length;
    const failed = safeHistory.filter(
      (t) => String(t.status || "").toLowerCase() === "failed"
    ).length;
    return { total, completed, processing, failed };
  }, [safeHistory]);

  const firstName = useMemo(() => {
    const raw = user?.full_name || user?.name || user?.email || "Analyst";
    return String(raw).trim().split(/\s+/)[0].replace(/@.*/, "");
  }, [user]);

  const handleSavePreferences = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setStatusMsg("");
    try {
      const res = await api.put("/workspace/preferences", prefs);
      const updated = res.data?.preferences || res.data;
      if (updated && typeof updated === "object") {
        setPrefs((prev) => ({ ...prev, ...updated }));
      }
      setStatusMsg("Preferences saved.");
    } catch {
      setErrorMsg("Failed to save preferences.");
    }
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    if (!newTicker.trim()) return;
    setErrorMsg("");
    try {
      const res = await api.post("/workspace/stocks", {
        ticker: newTicker.trim().toUpperCase(),
        company_name: newCompany.trim() || newTicker.trim().toUpperCase(),
        market: prefs.preferred_market,
      });
      const added = res.data?.stock || res.data;
      if (added && added.ticker) {
        setStocks((prev) => [
          added,
          ...prev.filter((item) => item.ticker !== added.ticker),
        ]);
      } else {
        const stocksRes = await api.get("/workspace/stocks");
        setStocks(normalizeArray(stocksRes.data, "stocks"));
      }
      setNewTicker("");
      setNewCompany("");
      setStatusMsg("Stock added to watchlist.");
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Could not add stock to watchlist.");
    }
  };

  const handleRemoveStock = async (stockId) => {
    setErrorMsg("");
    try {
      await api.delete(`/workspace/stocks/${stockId}`);
      setStocks((prev) => prev.filter((item) => item.id !== stockId));
    } catch {
      setErrorMsg("Could not remove stock.");
    }
  };

  const handleRunResearch = async (tickerToRun, options = {}) => {
    const target = (tickerToRun || researchTicker).trim().toUpperCase();
    if (!target) return;
    setResearchTicker(target);
    setErrorMsg("");
    setStatusMsg("");
    setRunningResearch(true);

    try {
      const res = await api.post("/research/run", {
        ticker: target,
        market: options.market || prefs.preferred_market,
        analysis_period: options.analysis_period || prefs.analysis_period,
        risk_tolerance: options.risk_tolerance || prefs.risk_tolerance,
      });
      const built = buildReportFromResponse(res.data);
      setReport(built);
      if (options.switchToSearch) {
        setActiveTab("search");
      }
      const histRes = await api.get("/research/history");
      setHistory(normalizeArray(histRes.data, "tasks"));
      setStatusMsg(`Completed research for ${target}.`);
    } catch (err) {
      setErrorMsg(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          err.message ||
          "Research run failed."
      );
    } finally {
      setRunningResearch(false);
    }
  };

  const handleCompareStocks = async (e) => {
    e.preventDefault();
    const list = compareTickers
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean)
      .slice(0, 4);
    if (list.length < 2) {
      setErrorMsg("Enter at least 2 comma-separated tickers to compare (e.g. TCS, INFY).");
      return;
    }

    setErrorMsg("");
    setStatusMsg("");
    setRunningResearch(true);
    try {
      const settled = await Promise.all(
        list.map(async (sym) => {
          const res = await api.post("/research/run", {
            ticker: sym,
            market: prefs.preferred_market,
            analysis_period: prefs.analysis_period,
            risk_tolerance: prefs.risk_tolerance,
          });
          const built = buildReportFromResponse(res.data);
          return {
            symbol: built?.symbol || sym,
            company_name: built?.company_name || sym,
            market: built?.market || prefs.preferred_market,
            latest_close: built?.summary_metrics?.latest_close ?? "N/A",
            period_return_pct: built?.summary_metrics?.period_return_pct ?? 0,
            volatility_pct: built?.summary_metrics?.volatility_pct ?? 0,
            pe_ratio: built?.profile?.pe_ratio,
            currency: built?.profile?.currency || "",
            conviction: built?.cio_synthesis?.conviction || "N/A",
          };
        })
      );
      setComparisonResults(settled);
      const histRes = await api.get("/research/history");
      setHistory(normalizeArray(histRes.data, "tasks"));
      setStatusMsg(`Compared ${settled.map((r) => r.symbol).join(" vs ")}.`);
    } catch (err) {
      setErrorMsg(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          err.message ||
          "Comparison run failed."
      );
    } finally {
      setRunningResearch(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <div
      className="min-h-screen text-slate-100 px-4 py-6 sm:px-8"
      style={{
        background:
          "radial-gradient(circle at 80% 10%, rgba(104, 46, 199, 0.24), transparent 44%), radial-gradient(circle at 15% 0%, rgba(230, 194, 122, 0.11), transparent 38%), #06071A",
      }}
    >
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Top Navigation Bar */}
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E6C27A]/15 pb-4">
          <div className="flex items-center gap-3">
            <img
              src="/logo.jpg"
              alt="R-AIstock"
              className="w-9 h-9 rounded-lg object-cover border border-[#E6C27A]/40"
            />
            <span className="font-semibold tracking-tight text-[#F5D793] text-base">
              R-AIstock Terminal
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs sm:text-sm text-slate-400">
              {user?.email || "analyst@raistock.local"}
            </span>
            <button
              onClick={handleLogout}
              className="px-3.5 py-1.5 rounded-lg bg-[#0E1029] hover:bg-white/10 border border-[#E6C27A]/20 text-xs sm:text-sm text-slate-200 transition"
            >
              Sign Out
            </button>
          </div>
        </header>

        {/* Welcome Header */}
        <section className="space-y-1">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Welcome back, <span className="text-[#F5D793]">{firstName}</span>
          </h1>
          <p className="text-sm text-slate-400">
            Real-time stock search, historical market analysis, and research platform.
          </p>
        </section>

        {/* Feedback Banners */}
        {errorMsg && (
          <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/40 text-rose-200 text-sm">
            {errorMsg}
          </div>
        )}
        {statusMsg && (
          <div className="p-3 rounded-xl bg-[#682EC7]/20 border border-[#E6C27A]/40 text-[#F5D793] text-sm">
            {statusMsg}
          </div>
        )}

        {/* 4 KPI Stat Cards */}
        <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-center gap-3.5 bg-[#0E1029] border border-[#E6C27A]/15 rounded-xl p-4">
            <div className="w-10 h-10 rounded-lg bg-[#682EC7]/25 border border-[#8B5CF6]/40 text-[#F5D793] flex items-center justify-center font-bold">
              ▮
            </div>
            <div>
              <div className="text-xl font-bold text-white leading-tight">{stats.total}</div>
              <div className="text-xs text-slate-400">Total Tasks</div>
            </div>
          </div>

          <div className="flex items-center gap-3.5 bg-[#0E1029] border border-[#E6C27A]/15 rounded-xl p-4">
            <div className="w-10 h-10 rounded-lg bg-[#E6C27A]/15 border border-[#E6C27A]/35 text-[#F5D793] flex items-center justify-center font-bold">
              ✓
            </div>
            <div>
              <div className="text-xl font-bold text-[#F5D793] leading-tight">{stats.completed}</div>
              <div className="text-xs text-slate-400">Completed</div>
            </div>
          </div>

          <div className="flex items-center gap-3.5 bg-[#0E1029] border border-[#E6C27A]/15 rounded-xl p-4">
            <div className="w-10 h-10 rounded-lg bg-[#682EC7]/25 border border-[#8B5CF6]/40 text-[#C084FC] flex items-center justify-center font-bold">
              ↻
            </div>
            <div>
              <div className="text-xl font-bold text-white leading-tight">{stats.processing}</div>
              <div className="text-xs text-slate-400">Processing</div>
            </div>
          </div>

          <div className="flex items-center gap-3.5 bg-[#0E1029] border border-[#E6C27A]/15 rounded-xl p-4">
            <div className="w-10 h-10 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-300 flex items-center justify-center font-bold">
              !
            </div>
            <div>
              <div className="text-xl font-bold text-white leading-tight">{stats.failed}</div>
              <div className="text-xs text-slate-400">Failed</div>
            </div>
          </div>
        </section>

        {/* Pill Tab Bar */}
        <nav className="inline-flex flex-wrap items-center gap-1.5 bg-[#0E1029] border border-[#E6C27A]/15 rounded-xl p-1.5">
          {[
            { id: "search", label: "Stock Search & OHLCV", icon: "↗" },
            { id: "history", label: "Research History", icon: "☰" },
            { id: "watchlist", label: "Watchlist", icon: "♡" },
            { id: "preferences", label: "Preferences", icon: "⚙" },
          ].map((tab) => {
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-medium transition ${
                  active
                    ? "bg-[#682EC7] text-[#F5D793] border border-[#E6C27A]/50 font-semibold shadow-sm"
                    : "text-slate-300 hover:bg-white/5"
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* TAB 1: Stock Search & OHLCV */}
        {activeTab === "search" && (
          <section className="bg-[#0E1029] border border-[#E6C27A]/15 rounded-2xl p-5 space-y-6">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-base font-semibold text-[#F5D793]">
                  Stock Search & Multi-Agent Analysis
                </h2>
                <span className="text-xs text-slate-400">
                  Market:{" "}
                  <strong className="text-[#E6C27A]">{prefs.preferred_market}</strong> • Period:{" "}
                  <strong className="text-slate-200">{prefs.analysis_period}</strong> • Risk:{" "}
                  <strong className="text-slate-200">{prefs.risk_tolerance}</strong>
                </span>
              </div>

              <div className="flex flex-col sm:flex-row gap-2.5">
                <input
                  type="text"
                  value={researchTicker}
                  onChange={(e) => setResearchTicker(e.target.value)}
                  placeholder="Enter ticker (e.g. TCS, RELIANCE, AAPL, INFY)"
                  className="flex-1 px-3.5 py-2.5 rounded-lg bg-[#06071A] border border-white/15 focus:border-[#E6C27A]/60 outline-none text-sm uppercase text-white placeholder:normal-case"
                />
                <button
                  onClick={() => handleRunResearch()}
                  disabled={runningResearch}
                  className="px-5 py-2.5 rounded-lg bg-[#682EC7] hover:bg-[#5823ad] text-[#F5D793] border border-[#E6C27A]/40 text-sm font-semibold disabled:opacity-60 transition"
                >
                  {runningResearch ? "Analyzing..." : "Run Research"}
                </button>
              </div>
            </div>

            {report && (
              <div className="bg-[#06071A] border border-[#E6C27A]/15 rounded-xl p-4 sm:p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="text-lg font-bold text-white">
                      {report.company_name}{" "}
                      <span className="text-[#E6C27A] text-sm font-mono">({report.symbol})</span>
                    </h3>
                    <p className="text-xs text-slate-400">
                      {report.market} • {report.analysis_period}
                    </p>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-[#E6C27A]/15 text-[#F5D793] border border-[#E6C27A]/40">
                    {report.cio_synthesis?.conviction}
                  </span>
                </div>

                {report.profile && (
                  <div className="p-3.5 rounded-xl bg-[#0E1029] border border-[#E6C27A]/15 space-y-2.5">
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                      <span className="font-semibold text-[#E6C27A]">Company Profile</span>
                      <span className="text-slate-400">
                        {report.profile.exchange || report.market} • {report.profile.currency || ""}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div>
                        <span className="text-slate-400 block">Sector</span>
                        <span className="text-slate-100 font-medium">{report.profile.sector || "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Industry</span>
                        <span className="text-slate-100 font-medium">{report.profile.industry || "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Market Cap</span>
                        <span className="text-slate-100 font-medium">
                          {formatMarketCap(report.profile.market_cap, report.profile.currency)}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Trailing P/E</span>
                        <span className="text-slate-100 font-medium">
                          {report.profile.pe_ratio ? Number(report.profile.pe_ratio).toFixed(2) : "N/A"}
                        </span>
                      </div>
                    </div>
                    {report.profile.summary && (
                      <p className="text-xs text-slate-400 leading-relaxed">{report.profile.summary}</p>
                    )}
                  </div>
                )}

                <PriceAndSmaChart
                  series={report.chart_series}
                  currency={report.profile?.currency}
                />

                <p className="text-sm text-slate-200 leading-relaxed">
                  {report.cio_synthesis?.summary}
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-300">
                  <div className="p-3.5 rounded-xl bg-[#0E1029] border border-[#E6C27A]/15">
                    <div className="font-semibold text-[#E6C27A] mb-1">Fundamental</div>
                    {report.agents?.fundamental}
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#0E1029] border border-[#E6C27A]/15">
                    <div className="font-semibold text-[#E6C27A] mb-1">Technical</div>
                    {report.agents?.technical}
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#0E1029] border border-[#E6C27A]/15">
                    <div className="font-semibold text-[#E6C27A] mb-1">Risk</div>
                    {report.agents?.risk}
                  </div>
                </div>
              </div>
            )}

            {/* Side-by-Side Comparison */}
            <div className="pt-4 border-t border-[#E6C27A]/15 space-y-3">
              <h3 className="text-sm font-semibold text-[#E6C27A]">Side-by-Side Stock Comparison</h3>
              <form onSubmit={handleCompareStocks} className="flex flex-col sm:flex-row gap-2.5">
                <input
                  type="text"
                  value={compareTickers}
                  onChange={(e) => setCompareTickers(e.target.value)}
                  placeholder="Compare tickers (e.g. TCS, INFY, WIPRO)"
                  className="flex-1 px-3.5 py-2 rounded-lg bg-[#06071A] border border-white/15 focus:border-[#E6C27A]/60 outline-none text-sm uppercase text-white placeholder:normal-case"
                />
                <button
                  type="submit"
                  disabled={runningResearch}
                  className="px-4 py-2 rounded-lg bg-[#682EC7]/35 hover:bg-[#682EC7]/55 border border-[#E6C27A]/30 text-[#F5D793] text-xs sm:text-sm font-medium transition"
                >
                  Compare Stocks
                </button>
              </form>

              {comparisonResults.length > 0 && (
                <div className="overflow-x-auto rounded-xl border border-[#E6C27A]/15 bg-[#06071A]">
                  <table className="w-full text-left text-xs sm:text-sm">
                    <thead className="border-b border-[#E6C27A]/15 text-[11px] uppercase tracking-wider text-slate-400">
                      <tr>
                        <th className="py-3 px-4">Company</th>
                        <th className="py-3 px-4">Ticker</th>
                        <th className="py-3 px-4">Latest Close</th>
                        <th className="py-3 px-4">Return</th>
                        <th className="py-3 px-4">Volatility</th>
                        <th className="py-3 px-4">Conviction</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                      {comparisonResults.map((row) => {
                        const ret = Number(row.period_return_pct ?? 0);
                        return (
                          <tr key={row.symbol} className="hover:bg-white/[0.03]">
                            <td className="py-3 px-4 font-medium text-white">{row.company_name}</td>
                            <td className="py-3 px-4 font-mono text-[#E6C27A]">{row.symbol}</td>
                            <td className="py-3 px-4 text-slate-200">
                              {row.currency ? `${row.currency} ` : ""}
                              {row.latest_close}
                            </td>
                            <td
                              className={`py-3 px-4 font-medium ${
                                ret >= 0 ? "text-[#F5D793]" : "text-rose-400"
                              }`}
                            >
                              {ret >= 0 ? "+" : ""}
                              {ret.toFixed(2)}%
                            </td>
                            <td className="py-3 px-4 text-slate-300">
                              {Number(row.volatility_pct ?? 0).toFixed(2)}%
                            </td>
                            <td className="py-3 px-4 text-xs text-[#F5D793]">{row.conviction}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>
        )}

        {/* TAB 2: Research History */}
        {activeTab === "history" && (
          <section className="bg-[#0E1029] border border-[#E6C27A]/15 rounded-2xl p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-base font-semibold text-[#F5D793]">Research History</h2>
              <button
                onClick={() => setActiveTab("search")}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[#682EC7] hover:bg-[#5823ad] text-[#F5D793] border border-[#E6C27A]/40 text-xs sm:text-sm font-semibold transition"
              >
                <span>+</span>
                <span>New Research</span>
              </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-[#E6C27A]/15 bg-[#06071A]">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-[#E6C27A]/15 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                    <th className="py-3.5 px-4">Company</th>
                    <th className="py-3.5 px-4">Ticker</th>
                    <th className="py-3.5 px-4">Market</th>
                    <th className="py-3.5 px-4">Period</th>
                    <th className="py-3.5 px-4">Date</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10 text-sm">
                  {safeHistory.map((task) => {
                    const statusLower = String(task.status || "").toLowerCase();
                    const isProcessing = statusLower === "processing";
                    const isFailed = statusLower === "failed";
                    const matchedWatch = safeStocks.find(
                      (s) =>
                        String(s.ticker || "").toUpperCase() ===
                        String(task.ticker || "").toUpperCase()
                    );
                    const companyLabel = matchedWatch?.company_name || task.ticker;

                    return (
                      <tr key={task.id} className="hover:bg-white/[0.02] transition">
                        <td className="py-3.5 px-4 font-medium text-white">{companyLabel}</td>
                        <td className="py-3.5 px-4 font-mono text-[#E6C27A]">{task.ticker}</td>
                        <td className="py-3.5 px-4 text-slate-300">{task.market}</td>
                        <td className="py-3.5 px-4 text-slate-300">{task.analysis_period}</td>
                        <td className="py-3.5 px-4 text-slate-400">
                          {formatShortDate(task.created_at)}
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                              isProcessing
                                ? "bg-[#682EC7]/25 text-[#C084FC] border-[#8B5CF6]/40"
                                : isFailed
                                ? "bg-rose-500/15 text-rose-300 border-rose-500/30"
                                : "bg-[#E6C27A]/15 text-[#F5D793] border-[#E6C27A]/35"
                            }`}
                          >
                            {task.status || "Completed"}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          {isProcessing ? (
                            <span className="inline-flex items-center gap-1.5 text-xs text-slate-400">
                              <span>↻</span>
                              <span>Processing...</span>
                            </span>
                          ) : (
                            <button
                              onClick={() =>
                                handleRunResearch(task.ticker, {
                                  market: task.market,
                                  analysis_period: task.analysis_period,
                                  switchToSearch: true,
                                })
                              }
                              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-200 hover:text-[#F5D793] transition"
                            >
                              <span>👁</span>
                              <span>View Report</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}

                  {safeHistory.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-8 px-4 text-center text-sm text-slate-400">
                        No research runs yet. Click <strong>+ New Research</strong> to analyze a stock.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* TAB 3: Watchlist */}
        {activeTab === "watchlist" && (
          <section className="bg-[#0E1029] border border-[#E6C27A]/15 rounded-2xl p-5 space-y-4">
            <h2 className="text-base font-semibold text-[#F5D793]">Watchlist</h2>
            <form onSubmit={handleAddStock} className="flex flex-wrap gap-2.5">
              <input
                type="text"
                value={newTicker}
                onChange={(e) => setNewTicker(e.target.value)}
                placeholder="Ticker (e.g. INFY)"
                className="w-36 px-3 py-2 rounded-lg bg-[#06071A] border border-white/15 focus:border-[#E6C27A]/60 outline-none text-sm uppercase text-white placeholder:normal-case"
              />
              <input
                type="text"
                value={newCompany}
                onChange={(e) => setNewCompany(e.target.value)}
                placeholder="Company name (optional)"
                className="flex-1 min-w-[160px] px-3 py-2 rounded-lg bg-[#06071A] border border-white/15 focus:border-[#E6C27A]/60 outline-none text-sm text-white"
              />
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-[#682EC7] hover:bg-[#5823ad] text-[#F5D793] border border-[#E6C27A]/40 text-sm font-semibold"
              >
                Add Stock
              </button>
            </form>

            <ul className="space-y-2">
              {safeStocks.map((item) => (
                <li
                  key={item.id}
                  className="flex flex-wrap items-center justify-between gap-2 bg-[#06071A] px-4 py-3 rounded-xl border border-white/10"
                >
                  <div>
                    <span className="font-mono font-semibold text-sm text-[#E6C27A]">
                      {item.ticker}
                    </span>
                    <span className="text-sm text-slate-300 ml-2.5">{item.company_name}</span>
                    <span className="text-xs text-slate-400 ml-2">• {item.market}</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() =>
                        handleRunResearch(item.ticker, {
                          market: item.market,
                          switchToSearch: true,
                        })
                      }
                      className="text-xs px-3 py-1.5 rounded-lg bg-[#682EC7]/30 text-[#F5D793] hover:bg-[#682EC7]/50 border border-[#E6C27A]/25 font-medium"
                    >
                      Research
                    </button>
                    <button
                      onClick={() => handleRemoveStock(item.id)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-rose-500/15 text-rose-300 hover:bg-rose-500/25"
                    >
                      Remove
                    </button>
                  </div>
                </li>
              ))}
              {safeStocks.length === 0 && (
                <p className="text-xs text-slate-400">No stocks saved in your watchlist yet.</p>
              )}
            </ul>
          </section>
        )}

        {/* TAB 4: Preferences */}
        {activeTab === "preferences" && (
          <section className="bg-[#0E1029] border border-[#E6C27A]/15 rounded-2xl p-5 max-w-xl space-y-4">
            <h2 className="text-base font-semibold text-[#F5D793]">Workspace Preferences</h2>
            <form onSubmit={handleSavePreferences} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Market</label>
                <select
                  value={prefs.preferred_market}
                  onChange={(e) => setPrefs({ ...prefs, preferred_market: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-[#06071A] border border-white/15 focus:border-[#E6C27A]/60 outline-none text-sm text-white"
                >
                  <option value="NSE">NSE</option>
                  <option value="BSE">BSE</option>
                  <option value="NASDAQ">NASDAQ</option>
                  <option value="NYSE">NYSE</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Analysis Period</label>
                <select
                  value={prefs.analysis_period}
                  onChange={(e) => setPrefs({ ...prefs, analysis_period: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-[#06071A] border border-white/15 focus:border-[#E6C27A]/60 outline-none text-sm text-white"
                >
                  <option value="1 Month">1 Month</option>
                  <option value="3 Months">3 Months</option>
                  <option value="6 Months">6 Months</option>
                  <option value="1 Year">1 Year</option>
                  <option value="5 Years">5 Years</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Risk Tolerance</label>
                <select
                  value={prefs.risk_tolerance}
                  onChange={(e) => setPrefs({ ...prefs, risk_tolerance: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-[#06071A] border border-white/15 focus:border-[#E6C27A]/60 outline-none text-sm text-white"
                >
                  <option value="Conservative">Conservative</option>
                  <option value="Moderate">Moderate</option>
                  <option value="Aggressive">Aggressive</option>
                </select>
              </div>

              <button
                type="submit"
                className="px-5 py-2.5 rounded-lg bg-[#682EC7] hover:bg-[#5823ad] text-[#F5D793] border border-[#E6C27A]/40 text-sm font-semibold"
              >
                Save Preferences
              </button>
            </form>
          </section>
        )}
      </div>
    </div>
  );
}