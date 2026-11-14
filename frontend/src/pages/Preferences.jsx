
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";

import {
  getPreferences,
  updatePreferences,
} from "../services/authService";

const DEFAULTS = {
  preferred_market: "NSE",
  preferred_analysis_period: "1y",
  preferred_indicators: ["SMA", "EMA", "RSI", "MACD"],
  preferred_news_window: "30 days",
  preferred_risk_view: "Balanced",
  preferred_report_format: "Markdown",
};

function Preferences() {
  const navigate = useNavigate();

  const user = JSON.parse(
    sessionStorage.getItem("user") || "null"
  );

  const token = sessionStorage.getItem("access_token");

  const [preferences, setPreferences] = useState(DEFAULTS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (!token || !user) {
      navigate("/login", { replace: true });
      return;
    }

    const loadPreferences = async () => {
      try {
        const data = await getPreferences();

        setPreferences({
          ...DEFAULTS,
          ...data,
          preferred_indicators:
            data.preferred_indicators || DEFAULTS.preferred_indicators,
        });

      } catch (err) {
        if (err.response?.status === 401) {
          sessionStorage.removeItem("access_token");
          sessionStorage.removeItem("user");
          navigate("/login", { replace: true });
          return;
        }

        setError("Unable to load your preferences.");

      } finally {
        setLoading(false);
      }
    };

    loadPreferences();
  }, [navigate, token]);

  const updatePreference = (key, value) => {
    setPreferences((previous) => ({
      ...previous,
      [key]: value,
    }));

    setDirty(true);
    setMessage("");
    setError("");
  };

  const toggleIndicator = (indicator) => {
    const current = preferences.preferred_indicators;

    if (current.includes(indicator)) {
      if (current.length === 1) return;

      updatePreference(
        "preferred_indicators",
        current.filter((item) => item !== indicator)
      );
    } else {
      updatePreference(
        "preferred_indicators",
        [...current, indicator]
      );
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage("");
      setError("");

      await updatePreferences(preferences);

      setDirty(false);
      setMessage("Preferences saved successfully!");

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to save preferences."
      );

    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setPreferences({
      ...DEFAULTS,
      preferred_indicators: [...DEFAULTS.preferred_indicators],
    });

    setDirty(true);
    setMessage("");
    setError("");
  };

  const logout = () => {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    navigate("/login");
  };

  const market = preferences.preferred_market;

  const tickerExample =
    market === "NSE" ? "RELIANCE.NS" : "RELIANCE.BO";

  const currency = "INR";

  if (!user) return null;

  const options = [
    {
      key: "preferred_market",
      title: "Preferred Market",
      help: "Choose the stock exchange for your research.",
      values: ["NSE", "BSE"],
    },
    {
      key: "preferred_analysis_period",
      title: "Analysis Period",
      help: "How much historical price data should be analysed?",
      values: [
        { label: "1 Month", value: "1mo" },
        { label: "3 Months", value: "3mo" },
        { label: "6 Months", value: "6mo" },
        { label: "1 Year", value: "1y" },
        { label: "5 Years", value: "5y" },
      ],
    },
    {
      key: "preferred_news_window",
      title: "News Window",
      help: "How far back should the news agent search?",
      values: ["7 days", "30 days", "90 days"],
    },
    {
      key: "preferred_risk_view",
      title: "Risk View",
      help: "Choose how sensitive the risk analysis should be.",
      values: ["Conservative", "Balanced", "Aggressive"],
    },
    {
      key: "preferred_report_format",
      title: "Default Report Export",
      help: "Choose your preferred report format.",
      values: ["Markdown", "PDF"],
    },
  ];

  return (
    <DashboardLayout user={user} onLogout={logout}>
      <main className="dashboard-content settings-page">

        <div className="dashboard-heading">
          <div>
            <p className="eyebrow">PERSONAL SETTINGS</p>
            <h1>Research Preferences</h1>
            <p>
              These settings become the defaults for every new
              research run. You can still change them for an
              individual search.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="dashboard-message">
            Loading your preferences...
          </div>
        ) : (
          <div className="settings-layout">

            <section className="dashboard-card settings-card">

              {options.map((group) => (
                <div className="settings-group" key={group.key}>
                  <div>
                    <strong>{group.title}</strong>
                    <p>{group.help}</p>
                  </div>

                  <div className="settings-options">
                    {group.values.map((item) => {
                      const value =
                        typeof item === "string"
                          ? item
                          : item.value;

                      const label =
                        typeof item === "string"
                          ? item
                          : item.label;

                      const selected =
                        preferences[group.key] === value;

                      return (
                        <button
                          key={value}
                          type="button"
                          className={`settings-option ${
                            selected ? "selected" : ""
                          }`}
                          aria-pressed={selected}
                          onClick={() =>
                            updatePreference(group.key, value)
                          }
                        >
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              <div className="settings-group">
                <div>
                  <strong>Technical Indicators</strong>
                  <p>
                    Select the indicators used in technical analysis.
                    Choose at least one.
                  </p>
                </div>

                <div className="settings-options">
                  {["SMA", "EMA", "RSI", "MACD"].map((indicator) => {
                    const selected =
                      preferences.preferred_indicators.includes(
                        indicator
                      );

                    return (
                      <button
                        key={indicator}
                        type="button"
                        className={`settings-option ${
                          selected ? "selected" : ""
                        }`}
                        aria-pressed={selected}
                        onClick={() => toggleIndicator(indicator)}
                      >
                        {selected ? "✓ " : ""}
                        {indicator}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="settings-actions">
                <button
                  className="settings-save"
                  onClick={handleSave}
                  disabled={saving || !dirty}
                >
                  {saving ? "Saving..." : "Save Preferences"}
                </button>

                <button
                  className="settings-reset"
                  onClick={handleReset}
                  disabled={saving}
                >
                  Reset to Defaults
                </button>
              </div>

              {message && (
                <p className="dashboard-success">{message}</p>
              )}

              {error && (
                <div className="dashboard-error">{error}</div>
              )}

              {dirty && (
                <p className="settings-status">
                  You have unsaved changes.
                </p>
              )}
            </section>

            <aside className="dashboard-card settings-preview">
              <p className="eyebrow">NEXT RUN PREVIEW</p>

              <h2>What the agents will use</h2>

              <div className="settings-preview-row">
                <span>Ticker format</span>
                <strong>{tickerExample}</strong>
              </div>

              <div className="settings-preview-row">
                <span>Currency</span>
                <strong>{currency}</strong>
              </div>

              <div className="settings-preview-row">
                <span>Price history</span>
                <strong>
                  {options[1].values.find(
                    (item) =>
                      typeof item !== "string" &&
                      item.value === preferences.preferred_analysis_period
                  )?.label}
                </strong>
              </div>

              <div className="settings-preview-row">
                <span>Indicators</span>
                <strong>
                  {preferences.preferred_indicators.join(", ")}
                </strong>
              </div>

              <div className="settings-preview-row">
                <span>News</span>
                <strong>
                  Last {preferences.preferred_news_window}
                </strong>
              </div>

              <div className="settings-preview-row">
                <span>Risk view</span>
                <strong>{preferences.preferred_risk_view}</strong>
              </div>

              <div className="settings-preview-row">
                <span>Export</span>
                <strong>{preferences.preferred_report_format}</strong>
              </div>

              <p className="settings-note">
                Technical indicators describe historical price
                movements. They are not predictions or financial
                advice.
              </p>
            </aside>

          </div>
        )}

      </main>
    </DashboardLayout>
  );
}

export default Preferences;
