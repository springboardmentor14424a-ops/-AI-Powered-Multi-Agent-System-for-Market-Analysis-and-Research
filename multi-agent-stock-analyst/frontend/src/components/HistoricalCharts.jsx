import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from "recharts";

const toPct = (v) => (v == null ? null : Number((v * 100).toFixed(2)));

function ChartCard({ title, children }) {
  return (
    <div className="finsight-chart-card">
      <span className="finsight-chart-title">{title}</span>
      <div style={{ width: "100%", height: 160 }}>
        <ResponsiveContainer>{children}</ResponsiveContainer>
      </div>
    </div>
  );
}

export default function HistoricalCharts({ history, growth }) {
  // Oldest -> newest, reusing historical_performance.history as-is
  const rows = [...(history || [])]
    .sort((a, b) => a.year - b.year)
    .map((r) => ({
      year: r.year,
      sales: r["Sales"] ?? null,
      profit: r["Net profit"] ?? null,
      profitMargin: toPct(r["Profit_Margin"]),
      operatingMargin: toPct(r["Operating_Margin"]),
    }));

  if (rows.length < 2) {
    return <p>Not enough years of data to draw trend charts.</p>;
  }

  const hasMargins = rows.some((r) => r.profitMargin != null || r.operatingMargin != null);
  const growthRows = Object.entries(growth || {})
    .filter(([, v]) => v != null)
    .map(([metric, value]) => ({ metric, value }));

  const axis = { tick: { fontSize: 10 } };

  return (
    <>
      <ChartCard title="Revenue / Sales trend">
        <LineChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="year" {...axis} />
          <YAxis {...axis} width={45} />
          <Tooltip />
          <Line type="monotone" dataKey="sales" name="Sales" stroke="#4C2365" strokeWidth={2} connectNulls />
        </LineChart>
      </ChartCard>

      <ChartCard title="Net profit trend">
        <LineChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="year" {...axis} />
          <YAxis {...axis} width={45} />
          <Tooltip />
          <Line type="monotone" dataKey="profit" name="Net profit" stroke="#16a34a" strokeWidth={2} connectNulls />
        </LineChart>
      </ChartCard>

      {hasMargins && (
        <ChartCard title="Profitability trend (%)">
          <LineChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="year" {...axis} />
            <YAxis {...axis} width={40} unit="%" />
            <Tooltip />
            <Line type="monotone" dataKey="profitMargin" name="Profit margin" stroke="#c2410c" strokeWidth={2} connectNulls />
            <Line type="monotone" dataKey="operatingMargin" name="Operating margin" stroke="#2563eb" strokeWidth={2} connectNulls />
          </LineChart>
        </ChartCard>
      )}

      {growthRows.length > 0 && (
        <ChartCard title="Year-over-year growth (%)">
          <BarChart data={growthRows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="metric" {...axis} />
            <YAxis {...axis} width={40} unit="%" />
            <Tooltip />
            <Bar dataKey="value" name="Growth %">
              {growthRows.map((r, i) => (
                <Cell key={i} fill={r.value >= 0 ? "#16a34a" : "#c2410c"} />
              ))}
            </Bar>
          </BarChart>
        </ChartCard>
      )}
    </>
  );
}