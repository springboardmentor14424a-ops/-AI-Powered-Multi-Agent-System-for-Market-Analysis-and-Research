
import { Link } from "react-router-dom";
import { TrendingUp, BrainCircuit, ShieldCheck } from "lucide-react";

function Landing() {
  return (
    <div className="landing-page">
      <nav className="navbar">
        <h2 className="brand">Stock<span>Intel</span></h2>

        <div className="nav-links">
          <Link to="/login">Sign In</Link>
          <Link to="/signup" className="nav-button">
            Get Started
          </Link>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-content">
          <p className="eyebrow">AI-POWERED MARKET INTELLIGENCE</p>

          <h1>
            Smarter Stock Research.
            <span> Powered by AI.</span>
          </h1>

          <p className="hero-description">
            Research stocks with specialised AI agents.
            Understand financial performance, market trends,
            news sentiment and investment risks in one workspace.
          </p>

          <div className="hero-actions">
            <Link to="/signup" className="primary-button">
              Create Account
            </Link>

            <Link to="/login" className="secondary-button">
              Sign In
            </Link>
          </div>
        </div>

        <div className="hero-visual">
          <div className="chart-card">
            <TrendingUp size={42} />
            <h3>Intelligent Analysis</h3>
            <p>Fundamentals · Technicals · News · Risk</p>
            <div className="chart-bars">
              {[35, 55, 42, 75, 60, 90, 72, 100].map((height, i) => (
                <div
                  key={i}
                  style={{ height: `${height}%` }}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="features">
        <div>
          <BrainCircuit />
          <h3>Multi-Agent Research</h3>
          <p>Specialised agents analyse different market aspects.</p>
        </div>

        <div>
          <TrendingUp />
          <h3>Market Intelligence</h3>
          <p>Understand stock performance and market trends.</p>
        </div>

        <div>
          <ShieldCheck />
          <h3>Risk Assessment</h3>
          <p>Explore potential risks with structured analysis.</p>
        </div>
      </section>
    </div>
  );
}

export default Landing;
