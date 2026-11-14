
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import DashboardLayout from "../components/DashboardLayout";

import {
  getResearchHistory,
  getResearchReport,
} from "../services/authService";

function History() {
  const navigate = useNavigate();

  const [history, setHistory] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);

  const token = sessionStorage.getItem("access_token");

  const user = JSON.parse(
    sessionStorage.getItem("user") || "null"
  );

  useEffect(() => {
    if (!token || !user) {
      navigate("/login", { replace: true });
      return;
    }

    const fetchHistory = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getResearchHistory();
        setHistory(data);

      } catch (err) {
        if (err.response?.status === 401) {
          sessionStorage.removeItem("access_token");
          sessionStorage.removeItem("user");
          navigate("/login", { replace: true });
          return;
        }

        setError(
          err.response?.data?.detail ||
          "Unable to load your research history."
        );

      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [navigate, token]);

  const logout = () => {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    navigate("/login");
  };

  const formatDate = (date) => {
    if (!date) return "Not available";

    return new Date(date).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  const getStatusClass = (status) => {
    switch (status) {
      case "COMPLETED":
        return "status-completed";
      case "PROCESSING":
        return "status-processing";
      case "FAILED":
        return "status-failed";
      default:
        return "status-pending";
    }
  };

  const openReport = async (taskId) => {
    try {
      setReportLoading(true);
      setError("");

      const report = await getResearchReport(taskId);
      setSelectedReport(report);

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to open research report."
      );

    } finally {
      setReportLoading(false);
    }
  };

  if (!user) return null;

  const filteredHistory = history.filter((task) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase().trim();
    return (
      task.company_name?.toLowerCase().includes(q) ||
      task.ticker?.toLowerCase().includes(q) ||
      task.market?.toLowerCase().includes(q) ||
      task.status?.toLowerCase().includes(q)
    );
  });

  return (
    <DashboardLayout user={user} onLogout={logout}>
      <div className="dashboard-content">

        <div className="dashboard-heading">
          <div>
            <p className="eyebrow">YOUR WORKSPACE</p>
            <h1>Research History</h1>
            <p>
              View and manage your previous stock research activities.
            </p>
          </div>
        </div>

        <section className="research-history-section">
          <div className="section-heading">
            <div>
              <h2>My Research Activities</h2>
              <p>
                Your personal research tasks and generated reports.
              </p>
            </div>

            <span className="history-count">
              {filteredHistory.length} of {history.length} Tasks
            </span>
          </div>

          {history.length > 0 && (
            <div className="history-search-row">
              <input
                type="search"
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck="false"
                name="history-search"
                id="history-search"
                placeholder="Search history by company name or ticker..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          )}

          {loading ? (
            <div className="dashboard-message">
              Loading your research history...
            </div>
          ) : error ? (
            <div className="dashboard-error">{error}</div>
          ) : history.length === 0 ? (
            <div className="dashboard-message">
              <h3>No research history yet</h3>
              <p>
                Your stock research activities will appear here
                after you start researching a company.
              </p>
              <button onClick={() => navigate("/dashboard/research")}>
                Start New Research
              </button>
            </div>
          ) : filteredHistory.length === 0 ? (
            <div className="dashboard-message">
              <p>No research tasks matching "{searchQuery}".</p>
            </div>
          ) : (
            <div className="research-table-wrapper">
              <table className="research-table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Market</th>
                    <th>Analysis Period</th>
                    <th>Research Date</th>
                    <th>Status</th>
                    <th>Report</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredHistory.map((task) => (
                    <tr key={task.task_id}>
                      <td>
                        <div className="company-cell">
                          <strong>{task.company_name}</strong>
                          <span>{task.ticker}</span>
                        </div>
                      </td>

                      <td>{task.market}</td>
                      <td>{task.analysis_period}</td>
                      <td>{formatDate(task.started_at)}</td>

                      <td>
                        <span
                          className={`research-status ${getStatusClass(
                            task.status
                          )}`}
                        >
                          {task.status}
                        </span>
                      </td>

                      <td>
                        {task.status === "COMPLETED" ? (
                          <button
                            className="report-button"
                            onClick={() => openReport(task.task_id)}
                            disabled={reportLoading}
                          >
                            View Report
                          </button>
                        ) : (
                          <span className="report-unavailable">
                            Not available
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {error && !loading && (
          <div className="dashboard-error">{error}</div>
        )}

      </div>

      {selectedReport && (
        <div className="report-modal-overlay">
          <div className="report-modal">

            <button
              className="report-close"
              onClick={() => setSelectedReport(null)}
            >
              ×
            </button>

            <p className="eyebrow">
              STOCKINTEL RESEARCH REPORT
            </p>

            <h2>Research Report</h2>

            <p className="report-summary">
              {selectedReport.summary}
            </p>

            <div className="report-content">
              {selectedReport.report_content}
            </div>

            {selectedReport.limitations && (
              <div className="report-limitations">
                <h4>Limitations</h4>
                <p>{selectedReport.limitations}</p>
              </div>
            )}

            <p className="report-date">
              Created: {formatDate(selectedReport.created_at)}
            </p>

          </div>
        </div>
      )}

    </DashboardLayout>
  );
}

export default History;
