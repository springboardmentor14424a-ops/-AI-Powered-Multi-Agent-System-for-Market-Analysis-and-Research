import { Link } from "react-router-dom";

export default function LandingPage() {
  const token = localStorage.getItem("token");

  const features = [
    {
      badge: "01 // MULTI-AGENT ENGINE",
      title: "Autonomous Research Pipeline",
      description:
        "Coordinated market, fundamental, and sentiment agents synthesize OHLCV trends, financial statements, and company profiles into structured research briefs.",
    },
    {
      badge: "02 // GLOBAL EXCHANGES",
      title: "NSE, BSE, NASDAQ & NYSE",
      description:
        "Seamless ticker normalization and validated historical data collection across Indian and U.S. equities with customizable 1M to 5Y horizons.",
    },
    {
      badge: "03 // PERSONAL WORKSPACE",
      title: "Persistent Watchlists & History",
      description:
        "Save high-conviction tickers, lock in your default exchange and analysis window, and revisit completed research reports anytime.",
    },
  ];

  const sampleTickers = [
    { symbol: "AAPL", market: "NASDAQ", name: "Apple Inc.", tag: "US Tech" },
    { symbol: "RELIANCE.NS", market: "NSE", name: "Reliance Industries", tag: "India Large Cap" },
    { symbol: "MSFT", market: "NASDAQ", name: "Microsoft Corp.", tag: "AI & Cloud" },
    { symbol: "TCS.NS", market: "NSE", name: "Tata Consultancy Services", tag: "IT Services" },
  ];

  return (
    <div className="min-h-screen bg-[#06071A] text-[#E0E1EE] relative overflow-hidden">
      {/* Ambient Radial Glows */}
      <div
        className="pointer-events-none absolute -top-40 -left-40 h-96 w-96 rounded-full opacity-25 blur-3xl"
        style={{ background: "radial-gradient(circle, #682EC7 0%, transparent 70%)" }}
      />
      <div
        className="pointer-events-none absolute top-1/3 -right-32 h-96 w-96 rounded-full opacity-15 blur-3xl"
        style={{ background: "radial-gradient(circle, #E6C27A 0%, transparent 70%)" }}
      />

      {/* Top Navigation Bar */}
      <header className="relative z-10 border-b border-white/10 bg-[#06071A]/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#E6C27A]/40 bg-gradient-to-br from-[#682EC7] to-[#23124B] shadow-lg shadow-[#682EC7]/30">
              <span className="text-lg font-bold tracking-wider text-[#F5D793]">R</span>
            </div>
            <div>
              <span className="text-lg font-bold tracking-wide text-white">
                R-<span className="text-[#E6C27A]">AI</span>stock
              </span>
              <p className="text-[11px] uppercase tracking-widest text-[#9496B8]">
                Multi-Agent Equity Intelligence
              </p>
            </div>
          </Link>

          <nav className="flex items-center gap-3">
            {token ? (
              <Link
                to="/dashboard"
                className="rounded-lg bg-gradient-to-r from-[#E6C27A] to-[#F5D793] px-5 py-2.5 text-sm font-semibold text-[#06071A] shadow-md shadow-[#E6C27A]/20 transition hover:brightness-105"
              >
                Open Dashboard →
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="rounded-lg border border-white/15 px-4 py-2 text-sm font-medium text-[#E0E1EE] transition hover:border-[#E6C27A]/50 hover:text-[#F5D793]"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="rounded-lg bg-gradient-to-r from-[#682EC7] to-[#8347E5] px-5 py-2 text-sm font-semibold text-white shadow-md shadow-[#682EC7]/30 transition hover:brightness-110"
                >
                  Sign Up
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 mx-auto max-w-6xl px-6 pt-16 pb-20">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-12">
          {/* Left Column: Value Proposition & CTAs */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#E6C27A]/30 bg-[#121432]/80 px-4 py-1.5 text-xs font-medium tracking-wide text-[#F5D793]">
              <span className="h-2 w-2 rounded-full bg-[#E6C27A] animate-pulse" />
              MULTI-AGENT STOCK RESEARCH WORKSPACE
            </div>

            <h1 className="text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl">
              Institutional-Grade Stock Research Powered by{" "}
              <span className="bg-gradient-to-r from-[#E6C27A] via-[#F5D793] to-[#C89B4B] bg-clip-text text-transparent">
                Autonomous AI Agents
              </span>
            </h1>

            <p className="max-w-2xl text-base leading-relaxed text-[#A8AAC9] sm:text-lg">
              Analyze live and historical market data across <strong className="text-white">NSE, BSE, NASDAQ, and NYSE</strong>.
              Build personalized watchlists, configure custom analysis horizons, and generate structured multi-agent equity reports in seconds.
            </p>

            {/* Primary CTA Buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                to={token ? "/dashboard" : "/register"}
                className="rounded-xl bg-gradient-to-r from-[#E6C27A] to-[#F5D793] px-7 py-3.5 text-sm font-bold tracking-wide text-[#06071A] shadow-lg shadow-[#E6C27A]/20 transition hover:scale-[1.01] hover:brightness-105"
              >
                {token ? "Go to Research Workspace" : "Create Free Account"}
              </Link>

              {!token && (
                <Link
                  to="/login"
                  className="rounded-xl border border-[#682EC7]/60 bg-[#121432]/70 px-7 py-3.5 text-sm font-semibold text-white transition hover:border-[#E6C27A]/60 hover:bg-[#191C45]"
                >
                  Sign In to Workspace
                </Link>
              )}
            </div>

            {/* Trust / Tech Badges */}
            <div className="flex flex-wrap items-center gap-6 pt-4 text-xs text-[#8D90B5]">
              <span>• JWT & OAuth 2.0 Secured</span>
              <span>• Validated OHLCV & Fundamentals</span>
              <span>• PostgreSQL Research History</span>
            </div>
          </div>

          {/* Right Column: Live Workspace Preview Card */}
          <div className="lg:col-span-5">
            <div className="rounded-2xl border border-[#E6C27A]/25 bg-[#0D0F2B]/90 p-6 shadow-2xl shadow-[#682EC7]/20 backdrop-blur-md">
              <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-[#E6C27A]">
                    Supported Markets Preview
                  </p>
                  <p className="text-sm font-medium text-white">Multi-Exchange Coverage</p>
                </div>
                <span className="rounded-md bg-[#682EC7]/30 px-2.5 py-1 text-xs font-medium text-[#D3BFFF]">
                  Live Ready
                </span>
              </div>

              <div className="space-y-3">
                {sampleTickers.map((item) => (
                  <div
                    key={item.symbol}
                    className="flex items-center justify-between rounded-xl border border-white/10 bg-[#06071A]/70 px-4 py-3 transition hover:border-[#E6C27A]/40"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">{item.symbol}</span>
                        <span className="rounded bg-[#682EC7]/30 px-2 py-0.5 text-[10px] font-semibold text-[#E6C27A]">
                          {item.market}
                        </span>
                      </div>
                      <p className="text-xs text-[#9496B8]">{item.name}</p>
                    </div>
                    <span className="text-xs font-medium text-[#F5D793]">{item.tag}</span>
                  </div>
                ))}
              </div>

              <div className="mt-5 rounded-xl border border-[#682EC7]/30 bg-[#14173D]/60 p-3.5 text-xs text-[#B8BAD8]">
                Sign in or create an account to add stocks to your personal watchlist and launch AI-driven equity analysis.
              </div>
            </div>
          </div>
        </div>

        {/* 3-Card Feature Grid */}
        <section className="mt-20 grid grid-cols-1 gap-6 md:grid-cols-3">
          {features.map((feat) => (
            <div
              key={feat.badge}
              className="rounded-2xl border border-white/10 bg-[#0D0F2B]/75 p-6 transition hover:border-[#E6C27A]/40"
            >
              <p className="text-xs font-semibold tracking-widest text-[#E6C27A]">{feat.badge}</p>
              <h3 className="mt-2 text-lg font-semibold text-white">{feat.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#9FA2C4]">{feat.description}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}