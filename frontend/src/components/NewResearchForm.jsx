import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { MARKETS, PERIODS } from "../constants";
import Field from "./Field";

// `defaults` = the user's saved preferences.
export default function NewResearchForm({ defaults, onCreated }) {
  const EMPTY = { company_name: "", ticker: "", market: defaults.market, analysis_period: defaults.analysis_period };
  const [form, setForm] = useState(EMPTY);

  // When preferences are saved, the form's market and period follow them.
  useEffect(() => {
    setForm((f) => ({ ...f, market: defaults.market, analysis_period: defaults.analysis_period }));
  }, [defaults.market, defaults.analysis_period]);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    if (errors[name]) setErrors((er) => ({ ...er, [name]: undefined }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setFormError("");
    const local = {};
    if (form.company_name.trim().length < 2) local.company_name = "Enter the company name.";
    if (!form.ticker.trim()) local.ticker = "Enter a ticker symbol."; // the server checks the market's exact format
    if (Object.keys(local).length) return setErrors(local);

    setSubmitting(true);
    try {
      // Note: no user id is sent. The server identifies the user from the JWT cookie.
      const task = await api("/research", { method: "POST", body: { ...form } });
      setForm({ ...EMPTY, market: form.market, analysis_period: form.analysis_period });
      onCreated(task);
    } catch (err) {
      if (!(err instanceof ApiError)) throw err;
      if (err.status === 422) setErrors(err.fieldErrors);
      else setFormError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="research-form" onSubmit={onSubmit} noValidate>
      {formError && (
        <div className="alert alert-error" role="alert">
          {formError}
        </div>
      )}
      <div className="form-grid">
        <Field id="company_name" label="Company name" placeholder="e.g. Apple Inc." value={form.company_name} onChange={onChange} error={errors.company_name} />
        <Field id="ticker" label="Stock ticker" placeholder={{ NSE: "e.g. RELIANCE", BSE: "e.g. 500325", NASDAQ: "e.g. AAPL", NYSE: "e.g. JPM" }[form.market]} value={form.ticker} onChange={onChange} error={errors.ticker} />
        <div className="field">
          <label htmlFor="market">Market</label>
          <select id="market" name="market" value={form.market} onChange={onChange}>
            {MARKETS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.value}
              </option>
            ))}
          </select>
          {errors.market && <p className="field-error" role="alert">{errors.market}</p>}
        </div>
        <div className="field">
          <label htmlFor="analysis_period">Analysis period</label>
          <select id="analysis_period" name="analysis_period" value={form.analysis_period} onChange={onChange}>
            {PERIODS.map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
          {errors.analysis_period && <p className="field-error" role="alert">{errors.analysis_period}</p>}
        </div>
      </div>
      <button className="btn btn-primary" type="submit" disabled={submitting}>
        {submitting ? "Starting…" : "Run analysis"}
      </button>
    </form>
  );
}
