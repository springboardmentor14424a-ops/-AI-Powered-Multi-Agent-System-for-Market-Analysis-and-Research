
import { useState, useRef, useEffect } from "react";
import "./FinancialAssistant.css";
import HistoricalCharts from "./HistoricalCharts";
const API_BASE_URL =
    import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const toDatasetName = (name) =>
  name
    .replace(/\blimited\b\.?/i, "LTD")
    .replace(/\bltd\b\.?/i, "LTD")
    .replace(/\s+/g, " ")
    .trim()
    .toUpperCase();
function FinancialAssistant({ dashboardCompany }) {
    const [isOpen, setIsOpen] = useState(false);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [activeCompany, setActiveCompany] = useState(null);
    const [suggestions, setSuggestions] = useState([]);
    const [latestAnalysis, setLatestAnalysis] = useState(null);
    const [pendingFollowUp, setPendingFollowUp] = useState(null);
    const [isMaximized, setIsMaximized] = useState(false);
    const [dashboardSuggestedCompany, setDashboardSuggestedCompany] = useState("");
    const [messages, setMessages] = useState([
        {
            role: "assistant",
            type: "text",
            content:
                "Hello! I'm Fundamental Analysis Agent, your financial analysis assistant. I can analyse company financials, profitability, debt and stock-market trends. What would you like to explore?"
        }
    ]);

    const messagesEndRef = useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({
            behavior: "smooth"
        });
    }, [messages, loading]);
    useEffect(() => {
        const search = input.trim();

        if (search.length < 2) {
            setSuggestions([]);
            return;
        }

        const controller = new AbortController();

        const timer = setTimeout(async () => {
            try {
                const response = await fetch(
                    `${API_BASE_URL}/fundamental/companies?search=${encodeURIComponent(search)}`,
                    { signal: controller.signal }
                );

                if (!response.ok) {
                    throw new Error("Company search failed");
                }

                const data = await response.json();
                setSuggestions(data.companies || []);

            } catch (error) {
                if (error.name !== "AbortError") {
                    console.error("Company suggestions error:", error);
                    setSuggestions([]);
                }
            }
        }, 300);

        return () => {
            clearTimeout(timer);
            controller.abort();
        };
    }, [input]);
 useEffect(() => {
  if (!dashboardCompany?.name) {
    setDashboardSuggestedCompany("");
    return;
  }

  const controller = new AbortController();
  const candidate = toDatasetName(dashboardCompany.name);

  (async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/fundamental/companies?search=${encodeURIComponent(candidate)}`,
        { signal: controller.signal }
      );
      const data = await response.json();
      const matches = data.companies || [];

      const exact = matches.find(
        (c) => c.toLowerCase() === candidate.toLowerCase()
      );
      // Use the dataset's own spelling; hide the chip if the company isn't in it
      setDashboardSuggestedCompany(exact || matches[0] || "");
    } catch (error) {
      if (error.name !== "AbortError") setDashboardSuggestedCompany("");
    }
  })();

  return () => controller.abort();
}, [dashboardCompany]);
const handleCompanySelect = async (company) => {
    setSuggestions([]);
    setInput("");

    addMessage({
        role: "user",
        type: "text",
        content: `Analyse ${company}`
    });

    await analyseCompany(company);
};
const addMessage = (message) => {
    setMessages((previous) => [...previous, message]);
};

const analyseCompany = async (companyName) => {
    setLoading(true);

    try {
        const response = await fetch(
            `${API_BASE_URL}/fundamental/analyze/${encodeURIComponent(companyName)}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to analyse this company.");
        }

        setActiveCompany(data.company);
        setLatestAnalysis(data);

        addMessage({
            role: "assistant",
            type: "analysis",
            data
        });
    } catch (error) {
        addMessage({
            role: "assistant",
            type: "text",
            content: `Sorry, I couldn't complete the analysis. ${error.message}`
        });
    } finally {
        setLoading(false);
    }
};

const fetchCompleteReport = async () => {
    if (!activeCompany) return;

    setLoading(true);

    try {
        const response = await fetch(
            `${API_BASE_URL}/fundamental/report/${encodeURIComponent(activeCompany)}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to retrieve report.");
        }

        addMessage({
            role: "assistant",
            type: "report",
            data
        });

    } catch (error) {
        addMessage({
            role: "assistant",
            type: "text",
            content: `Report error: ${error.message}`
        });
    } finally {
        setLoading(false);
    }
};


const compareCompanies = async (peerName) => {
    if (!activeCompany || !peerName.trim()) return;

    setLoading(true);

    try {
        const response = await fetch(
            `${API_BASE_URL}/fundamental/peer-compare/${encodeURIComponent(activeCompany)}?peer_name=${encodeURIComponent(peerName)}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to compare companies.");
        }

        addMessage({
            role: "assistant",
            type: "peer",
            data
        });

    } catch (error) {
        addMessage({
            role: "assistant",
            type: "text",
            content: `Peer comparison error: ${error.message}`
        });
    } finally {
        setLoading(false);
    }
};

const sendDebtAnalysis = () => {
    if (!latestAnalysis) {
        addMessage({
            role: "assistant",
            type: "text",
            content: "Please analyse a company first. Then I can provide its debt and financial stability analysis."
        });
        return;
    }

    const metrics = latestAnalysis.financial_metrics || {};

    addMessage({
        role: "assistant",
        type: "text",
        content:
            `Debt and Financial Stability Analysis — ${latestAnalysis.company} (FY ${latestAnalysis.financial_year})\n\n` +
            `Borrowings: ${metrics["Borrowings"] ?? "N/A"}\n` +
            `Debt-to-Equity: ${metrics["Debt_to_Equity"] ?? "N/A"}\n` +
            `Interest Coverage: ${metrics["Interest_Coverage"] ?? "N/A"}\n` +
            `Cash and Bank: ${metrics["Cash & Bank"] ?? "N/A"}\n` +
            `Operating Cash Flow: ${metrics["Cash from Operating Activity"] ?? "N/A"}\n\n` +
            `Interpretation:\n` +
            `• Debt-to-equity indicates the company's borrowings relative to its equity.\n` +
            `• Interest coverage indicates its ability to meet interest expenses from operating earnings.\n` +
            `• Operating cash flow helps assess whether its operations generate cash.\n\n` +
            `These indicators should be assessed together and compared across multiple years before drawing a conclusion about financial stability.`
    });
};

const VALUATION_REGEX =
  /(\bp\/?e\b|pe ratio|price to earnings|\bp\/?b\b|pb ratio|price to book|\broe\b|return on equity|valuation|financial ratios?)/i;

const extractCompanyFromQuestion = (message) => {
  // "P/E ratio of Infosys?" / "Show the P/B and ROE of TCS"
  const match = message.match(/\b(?:of|for)\s+(.+?)[?.!]*$/i);
  if (match) return match[1].trim();
  // "Infosys P/E" fallback: strip ratio words
  return message
    .replace(VALUATION_REGEX, "")
    .replace(/\b(what|is|the|show|give|me|current|and|explain|ratios?)\b/gi, "")
    .replace(/[?.!,]+/g, "")
    .trim();
};

const fetchValuation = async (companyQuery) => {
  setLoading(true);
  try {
    const response = await fetch(
      `${API_BASE_URL}/fundamental/valuation?company=${encodeURIComponent(companyQuery)}`
    );
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Unable to retrieve valuation ratios.");
    addMessage({ role: "assistant", type: "valuation", data });
  } catch (error) {
    addMessage({
      role: "assistant",
      type: "text",
      content: `Valuation error: ${error.message}`
    });
  } finally {
    setLoading(false);
  }
};
const handleSend = async (customMessage) => {
    const message = (customMessage ?? input).trim();

    if (!message || loading) return;

    addMessage({
        role: "user",
        type: "text",
        content: message
    });

    setInput("");
    setSuggestions([]);

    const lowerMessage = message.toLowerCase();

    // Complete report request
    if (
        lowerMessage.includes("complete report") ||
        lowerMessage.includes("historical") ||
        lowerMessage.includes("financial report") ||
        lowerMessage.includes("data quality")
    ) {
        if (!activeCompany) {
            addMessage({
                role: "assistant",
                type: "text",
                content: "Please analyse a company first."
            });
            return;
        }

        await fetchCompleteReport();
        return;
    }

    // Peer comparison request
    if (
        lowerMessage.startsWith("compare with ") ||
        lowerMessage.startsWith("compare against ")
    ) {
        const peerName = message.replace(
            /^compare (with|against)\s+/i,
            ""
        ).trim();

        if (!activeCompany) {
            addMessage({
                role: "assistant",
                type: "text",
                content: "Please analyse a company before comparing it."
            });
            return;
        }

        if (peerName) {
            await compareCompanies(peerName);
            return;
        }
    }


    // 1. Handle confirmation such as "okay", "yes", or "give"
    if (
        pendingFollowUp &&
        /^(okay|ok|yes|yeah|sure|please|give|go ahead|okay give)(\s+.*)?$/i.test(message)
    ) {
        const action = pendingFollowUp;
        setPendingFollowUp(null);

        if (action === "debt") {
            sendDebtAnalysis();
            return;
        }
    }
    if (VALUATION_REGEX.test(message)) {
  const company =
    extractCompanyFromQuestion(message) ||
    activeCompany ||
    dashboardCompany?.name;

  if (!company) {
    addMessage({
      role: "assistant",
      type: "text",
      content: "Which company? For example: \"What is the P/E ratio of Infosys?\""
    });
    return;
  }
  await fetchValuation(company);
  return;
}
    // 2. Handle debt and financial stability questions
    if (
        lowerMessage.includes("debt") ||
        lowerMessage.includes("financial stability") ||
        lowerMessage.includes("stability") ||
        lowerMessage.includes("borrowings")
    ) {
        setPendingFollowUp("debt");
        sendDebtAnalysis();
        return;
    }

    // 3. Handle profitability questions
    if (
        lowerMessage.includes("profitability") ||
        lowerMessage.includes("profit margin") ||
        lowerMessage.includes("revenue analysis") ||
        lowerMessage === "profit analysis"
    ) {
        if (!latestAnalysis) {
            addMessage({
                role: "assistant",
                type: "text",
                content: "Please analyse a company first so I can retrieve its profitability metrics."
            });
            return;
        }

        const metrics = latestAnalysis.financial_metrics || {};

        addMessage({
            role: "assistant",
            type: "text",
            content:
                `Profitability Analysis — ${latestAnalysis.company} (FY ${latestAnalysis.financial_year})\n\n` +
                `Sales: ${metrics["Sales"] ?? "N/A"}\n` +
                `Net Profit: ${metrics["Net profit"] ?? "N/A"}\n` +
                `Profit Margin: ${metrics["Profit_Margin"] == null ? "N/A" : (metrics["Profit_Margin"] * 100).toFixed(2) + "%"}\n` +
                `Operating Margin: ${metrics["Operating_Margin"] == null ? "N/A" : (metrics["Operating_Margin"] * 100).toFixed(2) + "%"}\n` +
                `ROE: ${metrics["ROE"] == null ? "N/A" : (metrics["ROE"] * 100).toFixed(2) + "%"}\n` +
                `ROA: ${metrics["ROA"] == null ? "N/A" : (metrics["ROA"] * 100).toFixed(2) + "%"}`
        });
        return;
    }

    // 4. Extract the company name from analysis commands
    const companyName = message
        .replace(
            /^(please\s+)?(analyse|analyze|check|research|show|evaluate)\s+(the\s+)?(financials?\s+of\s+)?/i,
            ""
        )
        .replace(/[?.!]+$/, "")
        .trim();

    // 5. Search both full company names and names entered directly
    const searchCompany = async (name) => {
        setLoading(true);

        try {
            const response = await fetch(
                `${API_BASE_URL}/fundamental/companies?search=${encodeURIComponent(name)}`
            );

            if (!response.ok) {
                throw new Error("Company search failed.");
            }

            const data = await response.json();
            const matches = data.companies || [];

            const exactMatch = matches.find(
                (company) => company.toLowerCase() === name.toLowerCase()
            );

            if (exactMatch) {
                await analyseCompany(exactMatch);
                return;
            }

            if (matches.length === 1) {
                await analyseCompany(matches[0]);
                return;
            }

            if (matches.length > 1) {
                setSuggestions(matches);

                addMessage({
                    role: "assistant",
                    type: "text",
                    content: `I found several companies matching "${name}". Please select the correct company from the suggestions.`
                });
                return;
            }

            addMessage({
                role: "assistant",
                type: "text",
                content: `I couldn't find "${name}" in the financial dataset. Please check the company name or try its full registered name.`
            });

        } catch (error) {
            addMessage({
                role: "assistant",
                type: "text",
                content: `Company search failed: ${error.message}`
            });
        } finally {
            setLoading(false);
        }
    };

    // 6. Recognise analysis commands and direct company-name input
    const isAnalysisRequest =
        /^(please\s+)?(analyse|analyze|check|research|show|evaluate)\b/i.test(message);

    if (isAnalysisRequest || /^[a-zA-Z0-9&.\- ]+$/.test(companyName)) {
        if (companyName) {
            await searchCompany(companyName);
            return;
        }
    }

    // 7. Fallback response
    addMessage({
        role: "assistant",
        type: "text",
        content:
            "I can analyse company financials, profitability and debt. Enter a company name or ask a question about the latest company analysed."
    });
};


const renderReport = (data) => {
  const history = data.historical_performance;
  const stability = data.financial_stability;
  const quality = data.data_quality;
  const a = data.analysis;
  const m = a?.financial_metrics || {};
  const mv = data.market_valuation;
  const pct = (v) => (v == null ? "N/A" : `${(v * 100).toFixed(2)}%`);

  return (
    <div className="finsight-analysis">
      <strong>Complete Fundamental Report</strong>

      <h4 className="finsight-section-heading">1. Company overview</h4>
      <p>{history.company} · Latest financial year in dataset: FY {history.latest_year}</p>

      <h4 className="finsight-section-heading">2. Revenue and earnings (FY {a?.financial_year})</h4>
      <div className="finsight-metrics">
        <div className="finsight-metric"><span>Sales</span><strong>{m["Sales"] ?? "N/A"}</strong></div>
        <div className="finsight-metric"><span>Net profit</span><strong>{m["Net profit"] ?? "N/A"}</strong></div>
      </div>

      <h4 className="finsight-section-heading">3. Profitability (FY {a?.financial_year}, historical dataset)</h4>
      <div className="finsight-metrics">
        <div className="finsight-metric"><span>Profit margin</span><strong>{pct(m["Profit_Margin"])}</strong></div>
        <div className="finsight-metric"><span>Operating margin</span><strong>{pct(m["Operating_Margin"])}</strong></div>
        <div className="finsight-metric"><span>ROE (dataset)</span><strong>{pct(m["ROE"])}</strong></div>
        <div className="finsight-metric"><span>ROA (dataset)</span><strong>{pct(m["ROA"])}</strong></div>
      </div>

      <h4 className="finsight-section-heading">4. Debt and financial stability</h4>
      <div className="finsight-metrics">
        {Object.entries(stability.indicators || {}).map(([key, value]) => (
          <div className="finsight-metric" key={key}>
            <span>{key.replaceAll("_", " ")}</span>
            <strong>{value ?? "N/A"}</strong>
          </div>
        ))}
      </div>
      <ul>{stability.observations.map((o, i) => <li key={i}>{o}</li>)}</ul>

      <h4 className="finsight-section-heading">5. Current market ratios (Yahoo Finance)</h4>
      {mv && !mv.error ? (
        <>
          <div className="finsight-metrics">
            <div className="finsight-metric"><span>P/E</span><strong>{fmt(mv.pe_ratio)}</strong></div>
            <div className="finsight-metric"><span>P/B</span><strong>{fmt(mv.pb_ratio)}</strong></div>
            <div className="finsight-metric"><span>ROE (current)</span><strong>{fmt(mv.roe_percent, "%")}</strong></div>
          </div>
          <p className="finsight-disclaimer">
            Current reported values for {mv.ticker}, retrieved {new Date(mv.retrieved_at).toLocaleString("en-IN")}.
            Yahoo's ROE can differ from the historical dataset ROE above.
          </p>
        </>
      ) : (
        <p>Current market ratios unavailable{mv?.error ? `: ${mv.error}` : "."}</p>
      )}

      <h4 className="finsight-section-heading">6. Historical performance</h4>
      <HistoricalCharts history={history.history} growth={history.year_over_year_growth_percent} />

      <h4 className="finsight-section-heading">7. ML profit-decline prediction (experimental)</h4>
      <p>
        <strong className={a?.prediction_class === 1 ? "decline" : "no-decline"}>{a?.prediction}</strong>
        {" "}(decline probability {a?.decline_probability}%)
      </p>
      <p className="finsight-disclaimer">
        This is a model estimate based on historical financials, not a guaranteed outcome.
      </p>

      <h4 className="finsight-section-heading">8. Data quality</h4>
      <strong>{quality.status}</strong>
      <p>Records checked: {quality.records_checked}</p>
      {quality.warnings?.map((w, i) => <p key={i}>⚠ {w}</p>)}
    </div>
  );
};


const renderPeerComparison = (data) => (
    <div className="finsight-analysis">
        <strong>Peer Comparison</strong>

        <p>
            {data.company_1} vs {data.company_2}
        </p>

        {Object.entries(data.comparison || {}).map(([metric, values]) => (
            <div className="finsight-metric" key={metric}>
                <strong>{metric.replaceAll("_", " ")}</strong>

                <span>
                    {data.company_1}:{" "}
                    {values[data.company_1] ?? "N/A"}
                </span>

                <span>
                    {data.company_2}:{" "}
                    {values[data.company_2] ?? "N/A"}
                </span>
            </div>
        ))}

        <p>{data.note}</p>
    </div>
);
const fmt = (v, suffix = "") => (v == null ? "N/A" : `${Number(v).toFixed(2)}${suffix}`);

const renderValuation = (data) => (
  <div className="finsight-analysis">
    <div className="finsight-company-heading">
      <strong>{data.company}</strong>
      <span>{data.ticker} · {data.sector || "Sector N/A"}</span>
    </div>

    <div className="finsight-metrics">
      <div className="finsight-metric"><span>P/E Ratio</span><strong>{fmt(data.pe_ratio)}</strong></div>
      <div className="finsight-metric"><span>P/B Ratio</span><strong>{fmt(data.pb_ratio)}</strong></div>
      <div className="finsight-metric"><span>ROE (Yahoo, current)</span><strong>{fmt(data.roe_percent, "%")}</strong></div>
    </div>

    <p className="finsight-note">
      <b>P/E</b>: market price relative to earnings per share. <b>P/B</b>: market price
      relative to book value per share. <b>ROE</b>: profit generated from shareholders' equity.
      This ROE is Yahoo Finance's current reported figure and can differ from the
      historical ROE calculated from the financial dataset.
    </p>
    <p className="finsight-disclaimer">
      Source: {data.source} · Retrieved {new Date(data.retrieved_at).toLocaleString("en-IN")}
    </p>
  </div>
);
const renderAnalysis = (data) => (
    <div className="finsight-analysis">
        <div className="finsight-company-heading">
            <strong>{data.company}</strong>
            <span>FY {data.financial_year}</span>
        </div>

        <div className="finsight-prediction">
            <span>Next-year profit prediction</span>
            <strong className={data.prediction_class === 1 ? "decline" : "no-decline"}>
                {data.prediction}
            </strong>
            <div className="finsight-probabilities">
                <div>
                    <span>No decline</span>
                    <strong>{data.no_decline_probability}%</strong>
                </div>
                <div>
                    <span>Decline</span>
                    <strong>{data.decline_probability}%</strong>
                </div>
            </div>
            <div className="finsight-progress">
                <div style={{ width: `${data.no_decline_probability}%` }} />
            </div>
        </div>

        <strong className="finsight-section-title">
            Financial indicators
        </strong>

        <div className="finsight-metrics">
            {Object.entries(data.financial_metrics || {}).map(([key, value]) => (
                <div className="finsight-metric" key={key}>
                    <span>{key}</span>
                    <strong>{value === null ? "N/A" : value}</strong>
                </div>
            ))}
        </div>
    </div>
);

return (
    <div className="finsight-widget">
        {isOpen && (
            <section className={`finsight-window ${isMaximized ? "maximized" : ""}`}>
                <header className="finsight-header">
                    <div className="finsight-brand">
                        <div className="finsight-avatar">
                            <span></span>
                        </div>
                        <div>
                            <h3>Fundamental Analysis Agent</h3>
                            <span>Financial Analysis Assistant</span>
                        </div>
                    </div>

                    <div className="finsight-header-actions">

                        <button
                            className="finsight-window-control"
                            onClick={() => setIsOpen(false)}
                            aria-label="Minimize assistant"
                            title="Minimize"
                        >
                            −
                        </button>

                        <button
                            className="finsight-window-control"
                            onClick={() => setIsMaximized(prev => !prev)}
                            aria-label={isMaximized ? "Restore assistant" : "Maximize assistant"}
                            title={isMaximized ? "Restore" : "Maximize"}
                        >
                            {isMaximized ? "❐" : "□"}
                        </button>

                        <button
                            className="finsight-close"
                            onClick={() => {
                                setIsOpen(false);
                                setIsMaximized(false);
                            }}
                            aria-label="Close assistant"
                            title="Close"
                        >
                            ×
                        </button>

                    </div>
                </header>

                <div className="finsight-messages">
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`finsight-message ${message.role}`}
                        >

                            {message.type === "analysis" ? (
                                renderAnalysis(message.data)
                            ) : message.type === "report" ? (
                                renderReport(message.data)
                            ) : message.type === "peer" ? (
                                renderPeerComparison(message.data)
                            ) : message.type === "valuation" ? (
                                 renderValuation(message.data)
                            ) : (
                                <div className="finsight-bubble">{message.content}</div>
                            )}

                        </div>
                    ))}

                    {loading && (
                        <div className="finsight-message assistant">
                            <div className="finsight-bubble finsight-loading">
                                Analysing company financials...
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
                {suggestions.length > 0 && (
                    <div className="finsight-autocomplete">
                        <div className="finsight-autocomplete-title">
                            Suggested Companies
                        </div>

                        {suggestions.map((company) => (
                            <button
                                key={company}
                                type="button"
                                className="finsight-company-option"
                                onClick={() => handleCompanySelect(company)}
                            >
                                <span className="finsight-search-icon">⌕</span>
                                {company}
                            </button>
                        ))}
                    </div>
                )}
                <div className="finsight-suggestions">
                    {dashboardSuggestedCompany && (
                        <button
                            className="finsight-dashboard-suggestion"
                            onClick={() => handleCompanySelect(dashboardSuggestedCompany)}
                            disabled={loading}
                        >
                            ✦ Analyse {dashboardSuggestedCompany}
                        </button>
                    )}
                    <button onClick={() => handleSend("Analyse 3M INDIA LTD")}>
                        Analyse 3M INDIA LTD
                    </button>
                    <button onClick={() => handleSend("Check debt and financial stability")}>
                        Debt analysis
                    </button>
                    <button
                        onClick={() => handleSend("Show complete report")}
                        disabled={!activeCompany || loading}
                    >
                        Complete Report
                    </button>

                    <button
                        onClick={() => {
                            setInput("Compare with ");
                        }}
                        disabled={!activeCompany || loading}
                    >
                        Compare with another company
                    </button>
                </div>

                <form
                    className="finsight-input-area"
                    onSubmit={(event) => {
                        event.preventDefault();
                        handleSend();
                    }}
                >
                    <input
                        value={input}
                        onChange={(event) => setInput(event.target.value)}
                        placeholder="Ask about a company..."
                        disabled={loading}
                    />
                    <button type="submit" disabled={loading || !input.trim()}>
                        ➤
                    </button>
                </form>
            </section>
        )}

        <button
            className={`finsight-launcher ${isOpen ? "active" : ""}`}
            onClick={() => setIsOpen((previous) => !previous)}
            aria-label={isOpen ? "Close FinSight AI" : "Open FinSight AI"}
        >
            {isOpen ? "×" : "✦"}
        </button>
    </div>
);
}

export default FinancialAssistant;