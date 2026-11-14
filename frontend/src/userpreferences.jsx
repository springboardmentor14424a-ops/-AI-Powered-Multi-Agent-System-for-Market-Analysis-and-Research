
import React, { useEffect, useState } from "react";
import "./UserPreferences.css";

const API_URL = "http://127.0.0.1:8000";

function UserPreferences({ token, onPreferencesLoaded }) {
  const [market, setMarket] = useState("NASDAQ");
  const [analysisPeriod, setAnalysisPeriod] = useState("3 Months");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Load saved preferences when dashboard opens
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(`${API_URL}/preferences`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail || "Unable to load preferences"
          );
        }

        setMarket(data.market);
        setAnalysisPeriod(data.analysis_period);

        onPreferencesLoaded({
          market: data.market,
          analysis_period: data.analysis_period
        });

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      loadPreferences();
    }
  }, [token]);

  // Save preferences to backend
  const handleSavePreferences = async () => {
    setError("");
    setSuccess("");
    setSaving(true);

    try {
      const response = await fetch(`${API_URL}/preferences`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          market: market,
          analysis_period: analysisPeriod
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to save preferences"
        );
      }

      setMarket(data.market);
      setAnalysisPeriod(data.analysis_period);

      onPreferencesLoaded({
        market: data.market,
        analysis_period: data.analysis_period
      });

      setSuccess("Your preferences have been saved successfully.");

    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <section className="preferences-card">
        <p>Loading your preferences...</p>
      </section>
    );
  }

  return (
    <section className="preferences-card">

      <h2>User Preferences</h2>

      <p>
        Choose your preferred stock market and historical
        analysis period.
      </p>

      <div className="preferences-form">

        <div className="preference-field">
          <label htmlFor="preferred-market">
            Preferred Market
          </label>

          <select
            id="preferred-market"
            value={market}
            onChange={(e) => setMarket(e.target.value)}
          >
            <option value="NSE">
              NSE - National Stock Exchange
            </option>

            <option value="BSE">
              BSE - Bombay Stock Exchange
            </option>

            <option value="NASDAQ">
              NASDAQ - US Stock Exchange
            </option>

            <option value="NYSE">
              NYSE - New York Stock Exchange
            </option>
          </select>
        </div>

        <div className="preference-field">
          <label htmlFor="preferred-period">
            Preferred Analysis Period
          </label>

          <select
            id="preferred-period"
            value={analysisPeriod}
            onChange={(e) => setAnalysisPeriod(e.target.value)}
          >
            <option value="1 Month">1 Month</option>
            <option value="3 Months">3 Months</option>
            <option value="6 Months">6 Months</option>
            <option value="1 Year">1 Year</option>
            <option value="5 Years">5 Years</option>
          </select>
        </div>

        <button
          type="button"
          onClick={handleSavePreferences}
          disabled={saving}
        >
          {saving ? "Saving..." : "Save Preferences"}
        </button>

      </div>

      {error && (
        <p className="preferences-error">{error}</p>
      )}

      {success && (
        <p className="preferences-success">{success}</p>
      )}

    </section>
  );
}

export default UserPreferences;
