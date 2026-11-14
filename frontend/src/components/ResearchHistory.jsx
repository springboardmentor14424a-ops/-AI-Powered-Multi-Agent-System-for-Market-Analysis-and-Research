import { Link } from "react-router-dom";
import StatusBadge, { formatDate } from "./StatusBadge";

export default function ResearchHistory({ tasks, loading, error }) {
  if (loading) return <p className="muted">Loading your research…</p>;
  if (error)
    return (
      <div className="alert alert-error" role="alert">
        {error}
      </div>
    );
  if (tasks.length === 0)
    return (
      <div className="empty">
        <p>No research yet.</p>
        <p className="muted small">Run your first analysis above and it will appear here.</p>
      </div>
    );

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Company</th>
            <th>Ticker</th>
            <th>Market</th>
            <th>Period</th>
            <th>Researched</th>
            <th>Status</th>
            <th>
              <span className="sr-only">Report</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((t) => (
            <tr key={t.id}>
              <td data-label="Company">{t.company_name}</td>
              <td data-label="Ticker">
                <strong>{t.ticker}</strong>
              </td>
              <td data-label="Market">{t.market}</td>
              <td data-label="Period">{t.analysis_period}</td>
              <td data-label="Researched">{formatDate(t.created_at)}</td>
              <td data-label="Status">
                <StatusBadge status={t.status} />
                {t.status === "failed" && t.error && <div className="row-error">{t.error}</div>}
              </td>
              <td className="actions">
                {t.status === "completed" ? (
                  <Link className="btn btn-ghost btn-sm" to={`/research/${t.id}`}>
                    Open report
                  </Link>
                ) : (
                  <span className="muted small">
                    {t.status === "failed" ? "No report" : "In progress…"}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
