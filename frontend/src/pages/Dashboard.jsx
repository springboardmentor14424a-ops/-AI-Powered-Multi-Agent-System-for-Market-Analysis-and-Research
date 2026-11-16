import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { colors, typography } from "../theme";

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("Overview");
  const [stocks, setStocks] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [ticker, setTicker] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [exchange, setExchange] = useState("NSE");
  const [prefs, setPrefs] = useState({
    risk_tolerance: "Moderate",
    preferred_market: "NSE",
    analysis_period: "1 Year",
  });
  const [banner, setBanner] = useState("");
  const [runningTicker, setRunningTicker] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const savedUser = localStorage.getItem("user");
    if (!token || !savedUser) {
      navigate("/login");
      return;
    }
    setUser(JSON.parse(savedUser));
    fetchWorkspaceData();
  }, [navigate]);

  const fetchWorkspaceData = async () => {
    try {
      const [stocksRes, prefsRes, historyRes] = await Promise.all([
        api.get("/workspace/stocks"),
        api.get("/workspace/preferences"),
        api.get("/research/history"),
      ]);
      setStocks(stocksRes.data);
      setPrefs(prefsRes.data);
      setHistory(historyRes.data);
    } catch (err) {
      if (err.response?.status === 401) handleLogout();
    }
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    setBanner("");
    if (!ticker.trim()) return;
    try {
      const res = await api.post("/workspace/stocks", {
        ticker,
        company_name: companyName,
        exchange,
      });
      setStocks([res.data, ...stocks]);
      setTicker("");
      setCompanyName("");
    } catch (err) {
      setBanner(err.response?.data?.detail || "Could not add stock.");
    }
  };

  const handleDeleteStock = async (id) => {
    try {
      await api.delete(`/workspace/stocks/${id}`);
      setStocks(stocks.filter((s) => s.id !== id));
    } catch {
      setBanner("Failed to remove stock.");
    }
  };

  const handleRunResearch = async (stockItem) => {
    setRunningTicker(stockItem.ticker);
    setBanner("");
    try {
      const res = await api.post("/research/start", {
        ticker: stockItem.ticker,
        company_name: stockItem.company_name,
        market: stockItem.exchange,
        analysis_period: prefs.analysis_period,
      });
      setHistory([res.data, ...history]);
      setSelectedReport(res.data);
      setBanner(`Research task completed for ${stockItem.ticker} (${prefs.analysis_period}).`);
      setTimeout(() => setBanner(""), 3000);
    } catch (err) {
      setBanner(err.response?.data?.detail || "Failed to start research task.");
    } finally {
      setRunningTicker(null);
    }
  };

  const handleSavePrefs = async (e) => {
    e.preventDefault();
    try {
      const res = await api.put("/workspace/preferences", prefs);
      setPrefs(res.data);
      setBanner("Market & analysis-period preferences saved.");
      setTimeout(() => setBanner(""), 2500);
    } catch {
      setBanner("Failed to save preferences.");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  if (!user) return null;

  const filteredStocks = stocks.filter(
    (s) =>
      s.ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.company_name && s.company_name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const navItems = ["Overview", "Watchlist", "Research History", "Settings"];

  return (
    <div style={styles.shell}>
      {/* LEFT SIDEBAR */}
      <aside style={styles.sidebar}>
        <div style={styles.brandRow}>
          <img src="/logo.jpg" alt="R-AIstock" style={styles.logoImg} />
          <span style={styles.brandText}>
            R-<span style={{ color: colors.goldBright }}>AI</span>stock
          </span>
        </div>

        <div style={styles.sideSearchWrap}>
          <input
            type="text"
            placeholder="Filter tickers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={styles.sideSearchInput}
          />
          <span style={styles.kbdBadge}>F</span>
        </div>

        <div style={styles.menuSectionLabel}>Menu</div>
        <nav style={styles.navList}>
          {navItems.map((item) => {
            const isActive = activeTab === item;
            return (
              <button
                key={item}
                onClick={() => setActiveTab(item)}
                style={{
                  ...styles.navItem,
                  ...(isActive ? styles.navItemActive : {}),
                }}
              >
                <span
                  style={{
                    ...styles.navDot,
                    backgroundColor: isActive ? colors.goldBright : colors.textMuted,
                  }}
                />
                {item}
              </button>
            );
          })}
        </nav>

        <div style={{ marginTop: "auto" }}>
          <div style={styles.menuSectionLabel}>Account</div>
          <button onClick={handleLogout} style={styles.logoutNavBtn}>
            Logout
          </button>
        </div>
      </aside>

      {/* MAIN WORKSPACE */}
      <main style={styles.main}>
        <header style={styles.topHeader}>
          <div>
            <h1 style={styles.pageTitle}>{activeTab}</h1>
            <p style={styles.pageSubtitle}>Multi-agent equity research & personal watchlist workspace</p>
          </div>

          <div style={styles.headerRight}>
            <div style={styles.statusChip}>
              <span style={{ color: colors.goldBright, fontWeight: "700" }}>★</span>
              <span>{stocks.length} Saved</span>
            </div>
            <div style={styles.profilePill}>
              <div style={styles.avatar}>{user.full_name.charAt(0).toUpperCase()}</div>
              <div>
                <div style={{ fontSize: "13px", fontWeight: "600", color: colors.textPrimary }}>
                  {user.full_name}
                </div>
                <div style={{ fontSize: "11px", color: colors.gold }}>{prefs.risk_tolerance} Analyst</div>
              </div>
            </div>
          </div>
        </header>

        {banner && <div style={styles.banner}>{banner}</div>}

        {/* KPI METRIC ROW */}
        <div style={styles.kpiGrid}>
          <div style={{ ...styles.kpiCard, ...styles.kpiCardHighlight }}>
            <div style={styles.kpiLabel}>Watchlist Tickers</div>
            <div style={styles.kpiValue}>{stocks.length}</div>
            <div style={{ fontSize: "11px", color: colors.goldBright }}>Saved in PostgreSQL</div>
          </div>

          <div style={styles.kpiCard}>
            <div style={styles.kpiLabel}>Preferred Market</div>
            <div style={styles.kpiValue}>{prefs.preferred_market}</div>
            <div style={styles.kpiSub}>Default exchange target</div>
          </div>

          <div style={styles.kpiCard}>
            <div style={styles.kpiLabel}>Analysis Period</div>
            <div style={styles.kpiValue}>{prefs.analysis_period}</div>
            <div style={{ fontSize: "11px", color: colors.amberHold }}>Historical lookback window</div>
          </div>

          <div style={styles.kpiCard}>
            <div style={styles.kpiLabel}>Research Reports</div>
            <div style={styles.kpiValue}>{history.length}</div>
            <div style={{ fontSize: "11px", color: colors.greenBull }}>Saved to your history</div>
          </div>
        </div>

        {/* MAIN CONTENT SPLIT */}
        <div style={styles.contentGrid}>
          {/* LEFT COLUMN: WATCHLIST + RESEARCH HISTORY */}
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* WATCHLIST CARD */}
            <section style={styles.card}>
              <div style={styles.cardHeader}>
                <div>
                  <h2 style={styles.cardTitle}>Saved Stocks & Watchlist</h2>
                  <span style={styles.cardSub}>Add tickers or launch a research task directly</span>
                </div>
              </div>

              <form onSubmit={handleAddStock} style={styles.addRow}>
                <input
                  type="text"
                  placeholder="Ticker (e.g. RELIANCE, AAPL)"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value)}
                  required
                  style={styles.input}
                />
                <input
                  type="text"
                  placeholder="Company Name (optional)"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  style={styles.input}
                />
                <select value={exchange} onChange={(e) => setExchange(e.target.value)} style={styles.input}>
                  <option value="NSE">NSE</option>
                  <option value="BSE">BSE</option>
                  <option value="NASDAQ">NASDAQ</option>
                  <option value="NYSE">NYSE</option>
                </select>
                <button type="submit" style={styles.primaryBtn}>
                  + Add Stock
                </button>
              </form>

              {filteredStocks.length === 0 ? (
                <p style={{ color: colors.textMuted, fontSize: typography.body, marginTop: "20px" }}>
                  No tickers in your watchlist yet. Add a stock above to begin.
                </p>
              ) : (
                <table style={styles.table}>
                  <thead>
                    <tr style={styles.tableHeadRow}>
                      <th style={styles.th}>Ticker</th>
                      <th style={styles.th}>Company</th>
                      <th style={styles.th}>Market</th>
                      <th style={{ ...styles.th, textAlign: "right" }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredStocks.map((s) => (
                      <tr key={s.id} style={styles.tableRow}>
                        <td style={styles.td}>
                          <span style={styles.tickerTag}>{s.ticker}</span>
                        </td>
                        <td style={styles.td}>{s.company_name}</td>
                        <td style={{ ...styles.td, color: colors.textMuted }}>{s.exchange}</td>
                        <td style={{ ...styles.td, textAlign: "right", display: "flex", gap: "8px", justifyContent: "flex-end" }}>
                          <button
                            onClick={() => handleRunResearch(s)}
                            disabled={runningTicker === s.ticker}
                            style={styles.researchBtn}
                          >
                            {runningTicker === s.ticker ? "Running..." : "▶ Research"}
                          </button>
                          <button onClick={() => handleDeleteStock(s.id)} style={styles.ghostBtn}>
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>

            {/* USER-SPECIFIC RESEARCH HISTORY CARD */}
            <section style={styles.card}>
              <div style={styles.cardHeader}>
                <div>
                  <h2 style={styles.cardTitle}>Research History</h2>
                  <span style={styles.cardSub}>Your saved equity analysis tasks & generated briefs</span>
                </div>
              </div>

              {history.length === 0 ? (
                <p style={{ color: colors.textMuted, fontSize: typography.body }}>
                  No research tasks yet. Click <strong>▶ Research</strong> next to any saved stock above.
                </p>
              ) : (
                <table style={styles.table}>
                  <thead>
                    <tr style={styles.tableHeadRow}>
                      <th style={styles.th}>Stock</th>
                      <th style={styles.th}>Market</th>
                      <th style={styles.th}>Period</th>
                      <th style={styles.th}>Date</th>
                      <th style={styles.th}>Status</th>
                      <th style={{ ...styles.th, textAlign: "right" }}>Report</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((item) => (
                      <tr key={item.id} style={styles.tableRow}>
                        <td style={styles.td}>
                          <span style={styles.tickerTag}>{item.ticker}</span>{" "}
                          <span style={{ color: colors.textMuted, marginLeft: "6px" }}>{item.company_name}</span>
                        </td>
                        <td style={{ ...styles.td, color: colors.textMuted }}>{item.market}</td>
                        <td style={styles.td}>{item.analysis_period}</td>
                        <td style={{ ...styles.td, color: colors.textMuted }}>
                          {new Date(item.created_at).toLocaleDateString()}
                        </td>
                        <td style={styles.td}>
                          <span style={styles.signalPill}>● {item.status}</span>
                        </td>
                        <td style={{ ...styles.td, textAlign: "right" }}>
                          <button onClick={() => setSelectedReport(item)} style={styles.viewBtn}>
                            Open Report
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </div>

          {/* RIGHT COLUMN: USER PREFERENCES */}
          <section style={{ ...styles.card, alignSelf: "start" }}>
            <h2 style={styles.cardTitle}>User Preferences</h2>
            <p style={{ ...styles.cardSub, marginBottom: "18px" }}>
              Configure default exchange and historical lookback window
            </p>

            <form onSubmit={handleSavePrefs} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <label style={styles.label}>Preferred Market</label>
              <select
                value={prefs.preferred_market}
                onChange={(e) => {
                  setPrefs({ ...prefs, preferred_market: e.target.value });
                  setExchange(e.target.value);
                }}
                style={styles.input}
              >
                <option value="NSE">NSE – National Stock Exchange of India</option>
                <option value="BSE">BSE – BSE Ltd., India</option>
                <option value="NASDAQ">NASDAQ – US Stock Exchange</option>
                <option value="NYSE">NYSE – New York Stock Exchange</option>
              </select>

              <label style={styles.label}>Analysis Period</label>
              <select
                value={prefs.analysis_period}
                onChange={(e) => setPrefs({ ...prefs, analysis_period: e.target.value })}
                style={styles.input}
              >
                <option value="1 Month">1 Month</option>
                <option value="3 Months">3 Months</option>
                <option value="6 Months">6 Months</option>
                <option value="1 Year">1 Year</option>
                <option value="5 Years">5 Years</option>
              </select>

              <label style={styles.label}>Risk Tolerance</label>
              <select
                value={prefs.risk_tolerance}
                onChange={(e) => setPrefs({ ...prefs, risk_tolerance: e.target.value })}
                style={styles.input}
              >
                <option value="Conservative">Conservative</option>
                <option value="Moderate">Moderate</option>
                <option value="Aggressive">Aggressive</option>
              </select>

              <button type="submit" style={{ ...styles.primaryBtn, marginTop: "10px" }}>
                Save Preferences
              </button>
            </form>
          </section>
        </div>

        {/* REPORT VIEWER MODAL */}
        {selectedReport && (
          <div style={styles.modalOverlay} onClick={() => setSelectedReport(null)}>
            <div style={styles.modalCard} onClick={(e) => e.stopPropagation()}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div>
                  <span style={styles.tickerTag}>{selectedReport.ticker}</span>
                  <span style={{ marginLeft: "10px", fontWeight: "600", fontSize: "16px" }}>
                    {selectedReport.company_name} ({selectedReport.market})
                  </span>
                </div>
                <button onClick={() => setSelectedReport(null)} style={styles.ghostBtn}>
                  Close ✕
                </button>
              </div>
              <div style={{ fontSize: "12px", color: colors.goldBright, marginBottom: "14px" }}>
                Period: {selectedReport.analysis_period} • Status: {selectedReport.status} •{" "}
                {new Date(selectedReport.created_at).toLocaleString()}
              </div>
              <pre style={styles.reportBody}>{selectedReport.report_summary}</pre>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

const styles = {
  shell: { display: "flex", minHeight: "100vh", backgroundColor: colors.bgCanvas, color: colors.textPrimary, fontFamily: typography.fontFamily },
  sidebar: { width: "240px", backgroundColor: colors.bgCanvas, borderRight: `1px solid ${colors.borderSubtle}`, padding: "24px 16px", display: "flex", flexDirection: "column" },
  brandRow: { display: "flex", alignItems: "center", gap: "12px", padding: "0 8px 22px 8px" },
  logoImg: { width: "36px", height: "36px", borderRadius: "10px", objectFit: "cover", border: `1px solid ${colors.gold}`, boxShadow: `0 0 12px ${colors.goldGlow}` },
  brandText: { fontSize: "20px", fontWeight: "700", letterSpacing: "0.4px" },
  sideSearchWrap: { position: "relative", display: "flex", alignItems: "center", marginBottom: "24px" },
  sideSearchInput: { width: "100%", padding: "9px 32px 9px 12px", borderRadius: "10px", border: `1px solid ${colors.borderSubtle}`, backgroundColor: colors.bgSurface, color: colors.textPrimary, fontSize: typography.caption, fontFamily: typography.fontFamily, outline: "none" },
  kbdBadge: { position: "absolute", right: "10px", fontSize: "10px", color: colors.gold, backgroundColor: colors.bgCanvas, padding: "2px 6px", borderRadius: "4px", border: `1px solid rgba(230, 194, 122, 0.35)` },
  menuSectionLabel: { fontSize: "11px", color: colors.textMuted, padding: "0 10px 8px 10px", textTransform: "uppercase", letterSpacing: "0.6px" },
  navList: { display: "flex", flexDirection: "column", gap: "6px" },
  navItem: { display: "flex", alignItems: "center", gap: "10px", padding: "11px 12px", borderRadius: "10px", border: "1px solid transparent", backgroundColor: "transparent", color: colors.textMuted, fontSize: typography.body, fontWeight: "500", fontFamily: typography.fontFamily, cursor: "pointer", textAlign: "left" },
  navItemActive: { background: `linear-gradient(90deg, ${colors.violetGlow}, ${colors.goldGlow})`, borderLeft: `3px solid ${colors.goldBright}`, color: colors.textPrimary, fontWeight: "600" },
  navDot: { width: "7px", height: "7px", borderRadius: "2px" },
  logoutNavBtn: { width: "100%", padding: "10px 12px", borderRadius: "10px", border: `1px solid ${colors.borderSubtle}`, backgroundColor: colors.bgSurface, color: colors.textMuted, fontSize: typography.body, fontFamily: typography.fontFamily, cursor: "pointer", textAlign: "left" },
  main: { flex: 1, padding: "26px 34px", overflowY: "auto" },
  topHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", paddingBottom: "20px", borderBottom: `1px solid ${colors.borderSubtle}`, marginBottom: "24px" },
  pageTitle: { margin: 0, fontSize: typography.heading, fontWeight: "600" },
  pageSubtitle: { margin: "4px 0 0 0", fontSize: typography.caption, color: colors.textMuted },
  headerRight: { display: "flex", alignItems: "center", gap: "14px" },
  statusChip: { display: "flex", alignItems: "center", gap: "6px", padding: "8px 14px", borderRadius: "10px", backgroundColor: colors.bgSurface, border: `1px solid rgba(230, 194, 122, 0.35)`, fontSize: typography.caption },
  profilePill: { display: "flex", alignItems: "center", gap: "10px", padding: "6px 14px 6px 8px", borderRadius: "12px", backgroundColor: colors.bgSurface, border: `1px solid ${colors.borderSubtle}` },
  avatar: { width: "30px", height: "30px", borderRadius: "50%", background: `linear-gradient(135deg, ${colors.violet}, ${colors.gold})`, color: colors.bgCanvas, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "700", fontSize: "13px" },
  banner: { backgroundColor: colors.goldGlow, border: `1px solid ${colors.gold}`, color: colors.goldBright, padding: "10px 16px", borderRadius: "10px", marginBottom: "20px", fontSize: typography.caption },
  kpiGrid: { display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "24px" },
  kpiCard: { backgroundColor: colors.bgSurface, border: `1px solid ${colors.borderSubtle}`, borderRadius: "14px", padding: "18px 20px" },
  kpiCardHighlight: { background: `linear-gradient(135deg, ${colors.violetGlow}, ${colors.bgSurface})`, border: `1px solid ${colors.gold}`, boxShadow: `0 8px 24px ${colors.goldGlow}` },
  kpiLabel: { fontSize: typography.caption, color: colors.textMuted, marginBottom: "8px" },
  kpiValue: { fontSize: "22px", fontWeight: "700", marginBottom: "4px" },
  kpiSub: { fontSize: "11px", color: colors.textMuted },
  contentGrid: { display: "grid", gridTemplateColumns: "2.1fr 1fr", gap: "20px" },
  card: { backgroundColor: colors.bgSurface, border: `1px solid ${colors.borderSubtle}`, borderRadius: "14px", padding: "22px" },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" },
  cardTitle: { margin: 0, fontSize: typography.subHeading, fontWeight: "600" },
  cardSub: { fontSize: typography.caption, color: colors.textMuted },
  addRow: { display: "flex", gap: "10px", flexWrap: "wrap" },
  label: { fontSize: typography.caption, color: colors.textMuted, fontWeight: "500" },
  input: { padding: "10px 12px", borderRadius: "10px", border: `1px solid ${colors.borderSubtle}`, backgroundColor: colors.bgCanvas, color: colors.textPrimary, fontSize: typography.body, fontFamily: typography.fontFamily, flex: 1, outline: "none" },
  primaryBtn: { padding: "10px 18px", borderRadius: "10px", border: `1px solid ${colors.gold}`, background: `linear-gradient(135deg, ${colors.violet}, #4F1FA3)`, color: colors.textPrimary, fontWeight: "600", fontSize: typography.body, fontFamily: typography.fontFamily, cursor: "pointer", boxShadow: `0 4px 16px ${colors.violetGlow}` },
  researchBtn: { padding: "6px 12px", borderRadius: "8px", border: `1px solid ${colors.gold}`, backgroundColor: colors.violetGlow, color: colors.goldBright, fontSize: typography.caption, fontWeight: "600", fontFamily: typography.fontFamily, cursor: "pointer" },
  viewBtn: { padding: "6px 12px", borderRadius: "8px", border: `1px solid ${colors.violet}`, backgroundColor: colors.bgCanvas, color: colors.textPrimary, fontSize: typography.caption, fontFamily: typography.fontFamily, cursor: "pointer" },
  ghostBtn: { padding: "6px 12px", borderRadius: "8px", border: `1px solid ${colors.borderSubtle}`, backgroundColor: colors.bgCanvas, color: colors.textMuted, fontSize: typography.caption, fontFamily: typography.fontFamily, cursor: "pointer" },
  table: { width: "100%", borderCollapse: "collapse", marginTop: "16px" },
  tableHeadRow: { borderBottom: `1px solid ${colors.borderSubtle}`, color: colors.textMuted, fontSize: typography.caption, textAlign: "left" },
  th: { padding: "10px 8px", fontWeight: "500" },
  tableRow: { borderBottom: `1px solid ${colors.borderSubtle}` },
  td: { padding: "13px 8px", fontSize: typography.body },
  tickerTag: { fontWeight: "700", color: colors.goldBright, backgroundColor: colors.bgCanvas, padding: "5px 10px", borderRadius: "6px", border: `1px solid rgba(230, 194, 122, 0.4)` },
  signalPill: { color: colors.greenBull, backgroundColor: "rgba(125, 226, 96, 0.12)", padding: "4px 10px", borderRadius: "999px", fontSize: "11px", fontWeight: "600" },
  modalOverlay: { position: "fixed", inset: 0, backgroundColor: "rgba(6, 7, 26, 0.82)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50, padding: "20px" },
  modalCard: { width: "100%", maxWidth: "600px", backgroundColor: colors.bgSurface, border: `1px solid ${colors.gold}`, borderRadius: "16px", padding: "24px", boxShadow: `0 25px 60px rgba(0,0,0,0.75)` },
  reportBody: { whiteSpace: "pre-wrap", fontFamily: typography.fontFamily, fontSize: "13px", lineHeight: "1.6", backgroundColor: colors.bgCanvas, padding: "16px", borderRadius: "10px", border: `1px solid ${colors.borderSubtle}`, color: colors.textPrimary, margin: 0 },
};