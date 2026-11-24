import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid
} from 'recharts';

const formatBillions = (val, currency = 'USD') => {
  if (val === null || val === undefined) return 'N/A';
  const sign = currency === 'INR' ? '₹' : '$';
  if (Math.abs(val) >= 1e12) return `${sign}${(val / 1e12).toFixed(2)}T`;
  if (Math.abs(val) >= 1e9) return `${sign}${(val / 1e9).toFixed(2)}B`;
  if (Math.abs(val) >= 1e6) return `${sign}${(val / 1e6).toFixed(2)}M`;
  return `${sign}${val.toLocaleString()}`;
};

const formatNum = (val, suffix = '') =>
  val === null || val === undefined ? 'N/A' : `${val}${suffix}`;

export default function FundamentalPanel({ defaultMarket = 'NASDAQ' }) {
  const [symbol, setSymbol] = useState('AAPL');
  const [market, setMarket] = useState(defaultMarket);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const runAnalysis = async (e) => {
    e.preventDefault();
    if (!symbol.trim()) return;

    setLoading(true);
    setError('');
    setData(null);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(
        `http://127.0.0.1:8000/agents/fundamental/${encodeURIComponent(symbol.trim())}?market=${encodeURIComponent(market)}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      const json = await res.json();
      if (!res.ok) {
        setError(json.detail || 'Failed to run fundamental analysis');
      } else {
        setData(json);
      }
    } catch {
      setError('Could not connect to backend server.');
    } finally {
      setLoading(false);
    }
  };

  const chartData = (data?.historical_comparison || []).map((row) => ({
    year: row.year,
    Revenue: row.revenue ? Number((row.revenue / 1e9).toFixed(2)) : 0,
    'Net Income': row.net_income ? Number((row.net_income / 1e9).toFixed(2)) : 0,
  }));

  const currency = data?.metadata?.currency || 'USD';

  return (
    <div style={{
      marginTop: '28px',
      padding: '24px',
      backgroundColor: '#ffffff',
      borderRadius: '12px',
      border: '1px solid #e2e8f0',
      boxShadow: '0 2px 8px rgba(0,0,0,0.04)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '20px', color: '#0f172a' }}>
            Module 3: Fundamental Analysis Agent
          </h2>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
            Valuation ratios, profitability, debt stability, historical trends & peer comparison
          </p>
        </div>

        <form onSubmit={runAnalysis} style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="Ticker (e.g. AAPL, RELIANCE)"
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
            <option value="NASDAQ">NASDAQ</option>
            <option value="NYSE">NYSE</option>
            <option value="NSE">NSE</option>
            <option value="BSE">BSE</option>
          </select>
          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              backgroundColor: loading ? '#94a3b8' : '#10b981',
              color: '#ffffff',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Analyzing...' : 'Run Fundamental Agent'}
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

      {data && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '16px' }}>
          {/* Agent Summary */}
          <div style={{
            padding: '16px',
            borderRadius: '8px',
            backgroundColor: '#f0fdf4',
            border: '1px solid #bbf7d0'
          }}>
            <div style={{ fontWeight: '700', color: '#166534', marginBottom: '6px', fontSize: '14px' }}>
              {data.metadata.company_name} ({data.metadata.resolved_symbol}) • {data.metadata.sector || 'N/A'}
            </div>
            <p style={{ margin: 0, color: '#14532d', fontSize: '14px', lineHeight: '1.6' }}>
              {data.agent_summary}
            </p>
          </div>

          {/* Key Metric Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '12px'
          }}>
            {[
              { label: 'P/E Ratio', value: formatNum(data.valuation_ratios.pe_ratio) },
              { label: 'P/B Ratio', value: formatNum(data.valuation_ratios.pb_ratio) },
              { label: 'ROE', value: formatNum(data.valuation_ratios.roe_pct, '%') },
              { label: 'Net Margin', value: formatNum(data.profitability.net_profit_margin_pct, '%') },
              { label: 'Revenue Growth (YoY)', value: formatNum(data.revenue_and_earnings.revenue_growth_yoy_pct, '%') },
              { label: 'Earnings Growth (YoY)', value: formatNum(data.revenue_and_earnings.earnings_growth_yoy_pct, '%') },
              { label: 'Debt-to-Equity', value: formatNum(data.debt_and_stability.debt_to_equity, 'x') },
              { label: 'Current Ratio', value: formatNum(data.debt_and_stability.current_ratio) },
            ].map((card) => (
              <div key={card.label} style={{
                padding: '12px',
                borderRadius: '8px',
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0'
              }}>
                <div style={{ fontSize: '12px', color: '#64748b' }}>{card.label}</div>
                <div style={{ fontSize: '18px', fontWeight: '700', color: '#0f172a', marginTop: '4px' }}>
                  {card.value}
                </div>
              </div>
            ))}
          </div>

          {/* Historical Revenue vs Net Income Chart */}
          {chartData.length > 0 && (
            <div>
              <h3 style={{ margin: '0 0 10px', fontSize: '15px', color: '#1e293b' }}>
                Historical Performance (in Billions {currency})
              </h3>
              <div style={{ width: '100%', height: '260px' }}>
                <ResponsiveContainer>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="year" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Net Income" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Peer Comparison Table */}
          {data.peer_comparison?.length > 0 && (
            <div>
              <h3 style={{ margin: '0 0 10px', fontSize: '15px', color: '#1e293b' }}>
                Peer Comparison
              </h3>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f1f5f9', textAlign: 'left' }}>
                      <th style={{ padding: '10px', borderBottom: '1px solid #cbd5e1' }}>Company</th>
                      <th style={{ padding: '10px', borderBottom: '1px solid #cbd5e1' }}>Market Cap</th>
                      <th style={{ padding: '10px', borderBottom: '1px solid #cbd5e1' }}>P/E</th>
                      <th style={{ padding: '10px', borderBottom: '1px solid #cbd5e1' }}>P/B</th>
                      <th style={{ padding: '10px', borderBottom: '1px solid #cbd5e1' }}>ROE</th>
                      <th style={{ padding: '10px', borderBottom: '1px solid #cbd5e1' }}>Profit Margin</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.peer_comparison.map((peer) => (
                      <tr key={peer.symbol} style={{ borderBottom: '1px solid #e2e8f0' }}>
                        <td style={{ padding: '10px', fontWeight: '600' }}>{peer.name} ({peer.symbol})</td>
                        <td style={{ padding: '10px' }}>{formatBillions(peer.market_cap, currency)}</td>
                        <td style={{ padding: '10px' }}>{formatNum(peer.pe_ratio)}</td>
                        <td style={{ padding: '10px' }}>{formatNum(peer.pb_ratio)}</td>
                        <td style={{ padding: '10px' }}>{formatNum(peer.roe_pct, '%')}</td>
                        <td style={{ padding: '10px' }}>{formatNum(peer.profit_margin_pct, '%')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Data Quality / Missing Information Check */}
          <div style={{
            padding: '12px 14px',
            borderRadius: '8px',
            backgroundColor: data.data_quality_issues.length ? '#fffbeb' : '#f8fafc',
            border: data.data_quality_issues.length ? '1px solid #fde68a' : '1px solid #e2e8f0',
            fontSize: '13px'
          }}>
            <strong>Data Quality Check: </strong>
            {data.data_quality_issues.length === 0 ? (
              <span style={{ color: '#15803d' }}>All core financial metrics validated with no missing or inconsistent values.</span>
            ) : (
              <ul style={{ margin: '6px 0 0 18px', padding: 0, color: '#92400e' }}>
                {data.data_quality_issues.map((issue, idx) => (
                  <li key={idx}>{issue}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}