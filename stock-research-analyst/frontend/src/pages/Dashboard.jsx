import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../AuthContext.jsx";
import Preferences from "../components/Preferences.jsx";
import ResearchHistory from "../components/ResearchHistory.jsx";
import Watchlist from "../components/Watchlist.jsx";

const TABS = [
  { id: "history", label: "Research History" },
  { id: "watchlist", label: "Watchlist" },
  { id: "preferences", label: "Preferences" },
];

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState("history");
  const [prefs, setPrefs] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [error, setError] = useState("");

  // Load the user's saved preferences when the dashboard opens.
  useEffect(() => {
    api.getPreferences().then(setPrefs).catch((e) => setError(e.message));
  }, []);

  // Shared by the history and watchlist tabs. The backend applies the user's saved
  // analysis period; the user id comes from the JWT, never from this request.
  const startResearch = useCallback(async (ticker, market) => {
    await api.startResearch({ ticker, market });
    setRefreshKey((k) => k + 1);
    setTab("history");
  }, []);

  async function onLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="mx-auto max-w-5xl p-4">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Stock Research Analyst</h1>
          <p className="text-sm text-slate-500">Welcome, {user.full_name}</p>
        </div>
        <button className="btn-secondary" onClick={onLogout}>Log out</button>
      </header>

      <nav className="mb-6 flex gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${
              tab === t.id ? "border-indigo-600 text-indigo-600" : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {error && <p role="alert" className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      {tab === "history" && <ResearchHistory prefs={prefs} onStartResearch={startResearch} refreshKey={refreshKey} />}
      {tab === "watchlist" && <Watchlist prefs={prefs} onStartResearch={startResearch} />}
      {tab === "preferences" && <Preferences prefs={prefs} onSaved={setPrefs} />}
    </div>
  );
}
