import { useState } from 'react';

export default function MLPredictionPanel({ defaultMarket = 'NSE' }) {
  const [symbol, setSymbol] = useState('RELIANCE');
  const [market, setMarket] = useState(defaultMarket);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePredict = async (e) => {
    e.preventDefault();
    if (!symbol.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(
        `http://127.0.0.1:8000/agents/ml-predict/${encodeURIComponent(symbol.trim())}?market=${encodeURIComponent(market)}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Prediction failed.');
      } else {
        setResult(data);
      }
    } catch {
      setError('Could not connect to backend server.');
    } finally {
      setLoading(false);
    }
  };

  const isBullish = result?.prediction === 'Bullish';

  return (
    <div style={{
      marginTop: '24px',
      padding: '24px',
      backgroundColor: '#ffffff',
      borderRadius: '12px',
      border: '1px solid #e2e8f0',
      boxShadow: '0 2px 8px rgba(0,0,0,0.04)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '20px', color: '#0f172a' }}>
            ML Trend Predictor (NSE Top 100 Model)
          </h2>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
            Live Bullish/Bearish classification powered by Hist Gradient Boosting
          </p>
        </div>

        <form onSubmit={handlePredict} style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="Ticker (e.g. RELIANCE, TCS)"
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '14px',
              width: '180px'
            }}
          />
          <select
            value={market}
            onChange={(e) => setMarket(e.target.value)}
            style={{
              padding: '8px 10px',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '14px'
            }}
          >
            <option value="NSE">NSE</option>
            <option value="BSE">BSE</option>
            <option value="NASDAQ">NASDAQ</option>
            <option value="NYSE">NYSE</option>
          </select>
          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              backgroundColor: loading ? '#94a3b8' : '#6366f1',
              color: '#ffffff',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Predicting...' : 'Predict Trend'}
          </button>
        </form>
      </div>

      {error && (
        <div style={{
          padding: '12px',
          borderRadius: '8px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          color: '#b91c1c',
          fontSize: '14px'
        }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: '12px',
          marginTop: '12px'
        }}>
          <div style={{
            padding: '14px',
            borderRadius: '8px',
            backgroundColor: isBullish ? '#f0fdf4' : '#fef2f2',
            border: `1px solid ${isBullish ? '#bbf7d0' : '#fecaca'}`
          }}>
            <div style={{ fontSize: '12px', color: '#64748b' }}>Predicted Trend</div>
            <div style={{
              fontSize: '20px',
              fontWeight: '700',
              color: isBullish ? '#15803d' : '#b91c1c',
              marginTop: '4px'
            }}>
              {result.prediction}
            </div>
          </div>

          <div style={{ padding: '14px', borderRadius: '8px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '12px', color: '#64748b' }}>Confidence</div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#0f172a', marginTop: '4px' }}>
              {result.confidence_pct}%
            </div>
          </div>

          <div style={{ padding: '14px', borderRadius: '8px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '12px', color: '#64748b' }}>Latest Close ({result.symbol})</div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#0f172a', marginTop: '4px' }}>
              {result.latest_close}
            </div>
          </div>

          <div style={{ padding: '14px', borderRadius: '8px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '12px', color: '#64748b' }}>Model Accuracy</div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#4f46e5', marginTop: '4px' }}>
              {result.model_accuracy_pct}%
            </div>
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>{result.model_name}</div>
          </div>
        </div>
      )}
    </div>
  );
}