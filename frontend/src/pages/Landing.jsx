import { Link } from "react-router-dom";
import { useAuth } from "../auth";
import Logo from "../components/Logo";

const AGENTS = [
  { name: "Fundamentals agent", text: "Reads financial statements and key ratios to judge the health of a business." },
  { name: "Technical agent", text: "Studies price action, trends and momentum indicators." },
  { name: "Sentiment agent", text: "Scans news and commentary to gauge how the market feels." },
  { name: "Risk agent", text: "Challenges the thesis and flags what could go wrong." },
];

const STEPS = [
  ["Create your account", "Sign up in under a minute."],
  ["Ask about a stock", "Pick a company you want researched."],
  ["Get a combined report", "The agents compare notes and you keep the history."],
];

export default function Landing() {
  const { user, loading } = useAuth();

  return (
    <div className="landing">
      <header className="nav">
        <Logo />
        <nav className="nav-actions" aria-label="Account">
          {loading ? null : user ? (
            <Link className="btn btn-primary" to="/dashboard">
              Go to dashboard
            </Link>
          ) : (
            <>
              <Link className="btn btn-ghost" to="/login">
                Sign in
              </Link>
              <Link className="btn btn-primary" to="/register">
                Sign up
              </Link>
            </>
          )}
        </nav>
      </header>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">AI-powered equity research</p>
            <h1>
              A team of AI agents researching stocks <span className="accent">together.</span>
            </h1>
            <p className="lead">
              Each agent looks at a company from a different angle: fundamentals, price action,
              sentiment and risk. Then they combine their findings into one clear report you can
              come back to.
            </p>
            <div className="hero-cta">
              {user ? (
                <Link className="btn btn-primary btn-lg" to="/dashboard">
                  Open your dashboard
                </Link>
              ) : (
                <>
                  <Link className="btn btn-primary btn-lg" to="/register">
                    Get started, it's free
                  </Link>
                  <Link className="btn btn-ghost btn-lg" to="/login">
                    I already have an account
                  </Link>
                </>
              )}
            </div>
          </div>

          <div className="hero-visual" aria-hidden="true">
            <div className="mock">
              <div className="mock-head">
                <span>Sample research run</span>
                <span className="pill">Illustration</span>
              </div>
              <svg viewBox="0 0 320 110" className="spark">
                <defs>
                  <linearGradient id="g" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0" stopColor="var(--accent)" stopOpacity=".35" />
                    <stop offset="1" stopColor="var(--accent)" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path d="M0 85 L40 70 L80 78 L120 52 L160 60 L200 34 L240 42 L280 18 L320 24 L320 110 L0 110Z" fill="url(#g)" />
                <path d="M0 85 L40 70 L80 78 L120 52 L160 60 L200 34 L240 42 L280 18 L320 24" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinejoin="round" />
              </svg>
              {AGENTS.map((a, i) => (
                <div className="mock-row" key={a.name}>
                  <span className="dot" style={{ animationDelay: `${i * 0.4}s` }} />
                  {a.name}
                  <span className="mock-done">done</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="section" aria-labelledby="agents-h">
          <h2 id="agents-h">Four specialists, one report</h2>
          <div className="grid-4">
            {AGENTS.map((a) => (
              <article className="card tile" key={a.name}>
                <h3>{a.name}</h3>
                <p className="muted">{a.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section" aria-labelledby="how-h">
          <h2 id="how-h">How it works</h2>
          <ol className="steps">
            {STEPS.map(([title, text], i) => (
              <li className="card tile" key={title}>
                <span className="step-n">{i + 1}</span>
                <h3>{title}</h3>
                <p className="muted">{text}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className="footer">
        <p className="muted small">
          For research and education only. Nothing here is financial advice.
        </p>
      </footer>
    </div>
  );
}
