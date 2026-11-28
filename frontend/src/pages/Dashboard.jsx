import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, clearToken } from "../api.js";
import StockSearch from "../components/StockSearch.jsx";
import PricePanel from "../components/PricePanel.jsx";

const MARKETS = [
  ["NSE", "NSE – National Stock Exchange of India"],
  ["BSE", "BSE – BSE Ltd., India"],
  ["NASDAQ", "NASDAQ – US"],
  ["NYSE", "NYSE – New York Stock Exchange"],
];
const PERIODS = [
  ["1M", "1 Month"], ["3M", "3 Months"], ["6M", "6 Months"], ["1Y", "1 Year"], ["5Y", "5 Years"],
];

// The pages of the side menu: [id used in the address (#id), label, icon]
const PAGES = [
  ["home", "Home", "🏠"],
  ["search", "Stock search", "🔎"],
  ["watchlist", "Watchlist", "⭐"],
  ["history", "Research history", "🕘"],
  ["preferences", "Preferences", "⚙️"],
];

function readPage() {
  const id = window.location.hash.replace("#", "");
  return PAGES.some(([p]) => p === id) ? id : "home";
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [history, setHistory] = useState([]);
  const [prefs, setPrefs] = useState({ preferred_market: "NSE", default_period: "1Y" });
  const [ticker, setTicker] = useState("");
  const [viewTicker, setViewTicker] = useState(null);
  const [note, setNote] = useState({ type: "", text: "" });
  const [page, setPage] = useState(readPage());

  function signOut() {
    clearToken();
    navigate("/signin");
  }

  // If the token is missing, wrong or expired the backend says 401 -> back to sign in.
  function handle(err) {
    if (err.status === 401) signOut();
    else setNote({ type: "error", text: err.message });
  }

  function go(id) {
    window.location.hash = id;
  }

  // Show the page named in the address (#search, #watchlist ...) and clear old messages.
  useEffect(() => {
    function onHashChange() {
      setPage(readPage());
      setNote({ type: "", text: "" });
      window.scrollTo(0, 0);
    }
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const me = await api("/me");
        setUser(me);
        setPrefs({ preferred_market: me.preferred_market, default_period: me.default_period });
        setWatchlist(await api("/watchlist"));
        setHistory(await api("/research-history"));
      } catch (err) {
        handle(err);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function savePrefs(e) {
    e.preventDefault();
    try {
      await api("/me/preferences", { method: "PUT", body: prefs });
      setNote({ type: "ok", text: "Preferences saved." });
    } catch (err) {
      handle(err);
    }
  }

  async function addTicker(t) {
    try {
      const item = await api("/watchlist", { method: "POST", body: { ticker: t } });
      setWatchlist([item, ...watchlist]);
      setNote({ type: "ok", text: `${item.ticker} added to your watchlist.` });
      return true;
    } catch (err) {
      handle(err);
      return false;
    }
  }

  async function startResearch(t) {
    try {
      const task = await api("/research-tasks", {
        method: "POST",
        body: { ticker: t, market: prefs.preferred_market, period: prefs.default_period },
      });
      setHistory([task, ...history]);
      setNote({ type: "ok", text: `Research for ${task.ticker} added to your history (status: ${task.status}).` });
    } catch (err) {
      handle(err);
    }
  }

  async function addStock(e) {
    e.preventDefault();
    if (!ticker.trim()) return;
    if (await addTicker(ticker)) setTicker("");
  }

  async function removeStock(id) {
    try {
      await api(`/watchlist/${id}`, { method: "DELETE" });
      setWatchlist(watchlist.filter((s) => s.saved_stock_id !== id));
    } catch (err) {
      handle(err);
    }
  }

  // From the watchlist: open the price panel on the Stock search page.
  function viewFromWatchlist(t) {
    setViewTicker(t);
    go("search");
  }

  if (!user) return <div className="auth-wrap"><p className="muted">Loading your workspace...</p></div>;

  const alertBox = note.text && (
    <div className={`alert ${note.type === "ok" ? "alert-ok" : "alert-error"}`}>{note.text}</div>
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <span className="side-brand">Stock Research Analyst</span>
        <nav className="side-nav">
          {PAGES.map(([id, label, icon]) => (
            <a key={id} href={`#${id}`} className={page === id ? "active" : ""}>
              <span>{icon}</span> {label}
            </a>
          ))}
        </nav>
        <div className="side-foot">
          <span className="muted">{user.email}</span>
          <button className="btn btn-ghost" onClick={signOut}>Log out</button>
        </div>
      </aside>

      <main className="content dash">
        {page === "home" && (
          <>
            <h1>Welcome, {user.full_name.split(" ")[0]}</h1>
            <p className="muted">Your personal research workspace.</p>
            {alertBox}

            <div className="stats">
              <div className="card"><span className="stat">{watchlist.length}</span> Saved stocks</div>
              <div className="card"><span className="stat">{history.length}</span> Research tasks</div>
              <div className="card"><span className="stat">{prefs.preferred_market}</span> Preferred market</div>
            </div>

            <h4>Where do you want to go?</h4>
            <div className="grid">
              <a className="card quick" href="#search">
                <strong>🔎 Stock search</strong>
                <span>Find a company and see its prices, fundamental and technical analysis.</span>
              </a>
              <a className="card quick" href="#watchlist">
                <strong>⭐ Watchlist</strong>
                <span>Your saved stocks, with quick links to view prices or start research.</span>
              </a>
              <a className="card quick" href="#history">
                <strong>🕘 Research history</strong>
                <span>Every research task you have started.</span>
              </a>
              <a className="card quick" href="#preferences">
                <strong>⚙️ Preferences</strong>
                <span>Choose your market and analysis period.</span>
              </a>
            </div>
          </>
        )}

        {page === "search" && (
          <>
            <h1>Stock search</h1>
            <p className="muted">Search by company name or ticker.</p>
            {alertBox}

            <StockSearch market={prefs.preferred_market} onAdd={addTicker} onView={setViewTicker} onResearch={startResearch} onError={handle} />

            {viewTicker && (
              <PricePanel onResearch={startResearch} ticker={viewTicker} period={prefs.default_period} market={prefs.preferred_market}
                          onClose={() => setViewTicker(null)} onError={handle} />
            )}
          </>
        )}

        {page === "watchlist" && (
          <>
            <h1>Watchlist</h1>
            <p className="muted">Stocks you have saved.</p>
            {alertBox}

            <section className="card">
              <form className="inline" onSubmit={addStock}>
                <input placeholder="Ticker, e.g. TCS or AAPL" value={ticker}
                       onChange={(e) => setTicker(e.target.value)} maxLength={20} />
                <button className="btn">Add</button>
              </form>
              {watchlist.length === 0 ? (
                <p className="muted">No saved stocks yet.</p>
              ) : (
                <ul className="list">
                  {watchlist.map((s) => (
                    <li key={s.saved_stock_id}>
                      <strong>{s.ticker}</strong>
                      <span className="row-actions">
                        <button className="link-btn link-blue" onClick={() => viewFromWatchlist(s.ticker)}>View prices</button>
                        <button className="link-btn link-blue" onClick={() => startResearch(s.ticker)}>Start research</button>
                        <button className="link-btn" onClick={() => removeStock(s.saved_stock_id)}>Remove</button>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}

        {page === "history" && (
          <>
            <h1>Research history</h1>
            <p className="muted">Every research task you have started.</p>
            {alertBox}

            <section className="card">
              {history.length === 0 ? (
                <p className="muted">
                  No research yet. Once the research agents are built, every stock you research will appear here.
                </p>
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr><th>Ticker</th><th>Market</th><th>Period</th><th>Date</th><th>Status</th><th>Report</th></tr>
                    </thead>
                    <tbody>
                      {history.map((t) => (
                        <tr key={t.task_id}>
                          <td>{t.ticker}</td><td>{t.market}</td><td>{t.requested_period}</td>
                          <td>{new Date(t.created_at).toLocaleDateString()}</td><td>{t.status}</td>
                          <td className="muted">{t.status === "Completed" ? "Open" : "Not ready yet"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}

        {page === "preferences" && (
          <>
            <h1>Preferences</h1>
            <p className="muted">These settings are used when you search and research stocks.</p>
            {alertBox}

            <section className="card">
              <form onSubmit={savePrefs}>
                <label>Market
                  <select value={prefs.preferred_market}
                          onChange={(e) => setPrefs({ ...prefs, preferred_market: e.target.value })}>
                    {MARKETS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </label>
                <label>Analysis period
                  <select value={prefs.default_period}
                          onChange={(e) => setPrefs({ ...prefs, default_period: e.target.value })}>
                    {PERIODS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </label>
                <button className="btn">Save preferences</button>
              </form>
            </section>
          </>
        )}
      </main>
    </div>
  );
}