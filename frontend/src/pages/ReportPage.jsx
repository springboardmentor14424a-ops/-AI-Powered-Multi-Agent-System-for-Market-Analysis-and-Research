import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import Logo from "../components/Logo";
import StatusBadge, { formatDate, isActive } from "../components/StatusBadge";

export default function ReportPage() {
  const { id } = useParams();
  const [task, setTask] = useState(null);
  const [error, setError] = useState("");

  const active = task ? isActive(task.status) : false;

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      api(`/research/${id}`)
        .then((d) => !cancelled && setTask(d))
        .catch((e) => !cancelled && e.status !== 401 && setError(e.status === 404 ? "Report not found." : e.message));
    load();
    // keep refreshing while the agents are still working
    const timer = active ? setInterval(load, 2000) : null;
    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [id, active]);

  return (
    <div className="dash">
      <header className="nav">
        <Logo />
        <Link className="btn btn-ghost" to="/dashboard">
          ← Back to dashboard
        </Link>
      </header>
      <main className="dash-main">
        {error && (
          <div className="card">
            <h1>{error}</h1>
            <p className="muted">It may not exist, or it may belong to another account.</p>
          </div>
        )}
        {!error && !task && <div className="spinner" role="status" aria-label="Loading" />}
        {task && (
          <>
            <section>
              <h1>
                {task.company_name} <span className="muted">({task.ticker})</span>
              </h1>
              <p className="muted">
                {task.market} · {task.analysis_period} · {formatDate(task.created_at)} <StatusBadge status={task.status} />
              </p>
            </section>
            <section className="card">
              {task.status === "completed" && <pre className="report">{task.report}</pre>}
              {isActive(task.status) && <p>The agents are still working on this report. It will appear here automatically.</p>}
              {task.status === "failed" && (
                <div className="alert alert-error" role="alert">
                  {task.error ?? "This analysis failed."}
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
