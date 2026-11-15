import { useEffect, useState } from "react";
import { api, MARKETS, PERIODS } from "../api.js";

export default function Preferences({ prefs, onSaved }) {
  const [form, setForm] = useState(prefs);
  const [msg, setMsg] = useState({ type: "", text: "" });
  const [busy, setBusy] = useState(false);

  useEffect(() => setForm(prefs), [prefs]);
  if (!form) return <p className="text-sm text-slate-500">Loading…</p>;

  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setMsg({ type: "", text: "" });
    try {
      const saved = await api.savePreferences(form);
      onSaved(saved);
      setMsg({ type: "ok", text: "Preferences saved." });
    } catch (err) {
      setMsg({ type: "err", text: err.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save} className="card max-w-xl space-y-4">
      <h2 className="text-lg font-semibold">Preferences</h2>
      {msg.text && (
        <p role="status" className={`rounded-md p-3 text-sm ${msg.type === "ok" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
          {msg.text}
        </p>
      )}
      <div>
        <label className="label" htmlFor="market">Market</label>
        <select id="market" className="input" value={form.market} onChange={(e) => setForm({ ...form, market: e.target.value })}>
          {MARKETS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
        </select>
      </div>
      <div>
        <label className="label" htmlFor="period">Analysis period</label>
        <select id="period" className="input" value={form.analysis_period} onChange={(e) => setForm({ ...form, analysis_period: e.target.value })}>
          {PERIODS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
        </select>
      </div>
      <button className="btn" disabled={busy}>{busy ? "Saving…" : "Save preferences"}</button>
    </form>
  );
}
