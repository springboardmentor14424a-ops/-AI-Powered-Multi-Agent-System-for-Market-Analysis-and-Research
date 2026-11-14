import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import Logo from "../components/Logo";
import NewResearchForm from "../components/NewResearchForm";
import Preferences from "../components/Preferences";
import ResearchHistory from "../components/ResearchHistory";
import Watchlist from "../components/Watchlist";
import { isActive } from "../components/StatusBadge";

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function initials(name) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("");
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [data, setData] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [historyError, setHistoryError] = useState("");
  const [signingOut, setSigningOut] = useState(false);

  // Calling a protected endpoint proves the JWT cookie is being sent and verified.
  useEffect(() => {
    let cancelled = false;
    api("/dashboard")
      .then((d) => !cancelled && setData(d))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  // The server returns only this user's tasks (identity comes from the JWT).
  const loadTasks = useCallback(async () => {
    try {
      setTasks(await api("/research"));
      setHistoryError("");
    } catch (e) {
      if (e.status !== 401) setHistoryError(e.message);
    } finally {
      setLoadingTasks(false);
    }
  }, []);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  // Preferences and watchlist load when the dashboard opens.
  const [prefs, setPrefs] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [setupError, setSetupError] = useState("");

  const loadWatchlist = useCallback(async () => {
    setWatchlist(await api("/watchlist"));
  }, []);

  useEffect(() => {
    Promise.all([api("/preferences").then(setPrefs), loadWatchlist()]).catch(
      (e) => e.status !== 401 && setSetupError(e.message)
    );
  }, [loadWatchlist]);

  // "Research" on a saved stock: starts a task using the user's preferred period.
  const researchSaved = async (item) => {
    await api("/research", {
      method: "POST",
      body: {
        company_name: item.company_name,
        ticker: item.ticker,
        market: item.market,
        analysis_period: prefs.analysis_period,
      },
    });
    await loadTasks();
  };

  // While any task is pending/processing, refresh every 2 seconds.
  const hasActive = tasks.some((t) => isActive(t.status));
  useEffect(() => {
    if (!hasActive) return;
    const timer = setInterval(loadTasks, 2000);
    return () => clearInterval(timer);
  }, [hasActive, loadTasks]);

  const onLogout = async () => {
    setSigningOut(true);
    await logout(); // clears cookies; the route guard then redirects to /login
  };

  const memberSince = new Date(user.created_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="dash">
      <header className="nav">
        <Logo />
        <div className="nav-actions">
          <span className="avatar" aria-hidden="true">
            {initials(user.full_name)}
          </span>
          <span className="nav-name">{user.full_name}</span>
          <button className="btn btn-ghost" onClick={onLogout} disabled={signingOut}>
            {signingOut ? "Signing out…" : "Sign out"}
          </button>
        </div>
      </header>

      <main className="dash-main">
        <section className="dash-hero">
          <h1>
            {greeting()}, {user.full_name.split(" ")[0]}
          </h1>
          <p className="muted">Your research workspace is ready.</p>
        </section>

        <div className="grid-3">
          <section className="card">
            <h2>Profile</h2>
            <dl className="kv">
              <dt>Name</dt>
              <dd>{user.full_name}</dd>
              <dt>Email</dt>
              <dd>{user.email}</dd>
              <dt>Member since</dt>
              <dd>{memberSince}</dd>
            </dl>
          </section>

          <section className="card">
            <h2>Session</h2>
            <dl className="kv">
              <dt>Status</dt>
              <dd>
                <span className={`status ${data ? "on" : ""}`}>{data ? "Authenticated" : "Verifying…"}</span>
              </dd>
              <dt>Server says</dt>
              <dd>{data ? data.message : "…"}</dd>
              <dt>Protection</dt>
              <dd>Signed JWT in an HTTP-only cookie</dd>
            </dl>
          </section>

          <section className="card">
            {prefs ? <Preferences prefs={prefs} onSaved={setPrefs} /> : <p className="muted">Loading preferences…</p>}
          </section>
        </div>

        {setupError && (
          <div className="alert alert-error" role="alert">
            {setupError}
          </div>
        )}

        {prefs && (
          <section className="card">
            <Watchlist
              items={watchlist}
              preferredMarket={prefs.market}
              analysisPeriod={prefs.analysis_period}
              onChanged={loadWatchlist}
              onResearch={researchSaved}
            />
          </section>
        )}

        <section className="card">
          <h2>New research</h2>
          <p className="muted">Pick a stock and let the agents get to work.</p>
          {prefs && <NewResearchForm defaults={prefs} onCreated={loadTasks} />}
        </section>

        <section className="card">
          <h2>Research history</h2>
          <ResearchHistory tasks={tasks} loading={loadingTasks} error={historyError} />
        </section>
      </main>
    </div>
  );
}
