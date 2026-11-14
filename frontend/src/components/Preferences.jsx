import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { MARKETS, PERIODS } from "../constants";

export default function Preferences({ prefs, onSaved }) {
  const [market, setMarket] = useState(prefs.market);
  const [period, setPeriod] = useState(prefs.analysis_period);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    setMarket(prefs.market);
    setPeriod(prefs.analysis_period);
  }, [prefs]);

  const dirty = market !== prefs.market || period !== prefs.analysis_period;

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    try {
      const saved = await api("/preferences", { method: "PUT", body: { market, analysis_period: period } });
      onSaved(saved);
      setMsg({ type: "success", text: "Preferences saved." });
    } catch (err) {
      if (!(err instanceof ApiError)) throw err;
      setMsg({ type: "error", text: err.message });
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={save}>
      <h2>Preferences</h2>
      <p className="muted small">Used as the defaults for search and new research.</p>
      <div className="field">
        <label htmlFor="pref_market">Preferred market</label>
        <select id="pref_market" value={market} onChange={(e) => setMarket(e.target.value)}>
          {MARKETS.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="pref_period">Default analysis period</label>
        <select id="pref_period" value={period} onChange={(e) => setPeriod(e.target.value)}>
          {PERIODS.map((p) => (
            <option key={p}>{p}</option>
          ))}
        </select>
      </div>
      <button className="btn btn-primary" type="submit" disabled={saving || !dirty}>
        {saving ? "Saving…" : "Save preferences"}
      </button>
      {msg && (
        <p className={msg.type === "error" ? "field-error" : "ok-text"} role={msg.type === "error" ? "alert" : "status"}>
          {msg.text}
        </p>
      )}
    </form>
  );
}
