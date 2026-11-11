import { Link } from "react-router-dom";

const agents = [
  ["Fundamental", "Revenue, profit, debt and key ratios."],
  ["Technical", "Price trends and indicators like RSI and MACD."],
  ["News & Sentiment", "Latest headlines, with sources and dates."],
  ["Risk", "Volatility, drawdowns and conflicting evidence."],
];

export default function Landing() {
  return (
    <div className="page">
      <nav className="nav">
        <span className="brand">Stock Research Analyst</span>
        <div className="nav-actions">
          <Link className="btn btn-ghost" to="/signin">Sign In</Link>
          <Link className="btn" to="/signup">Sign Up</Link>
        </div>
      </nav>

      <header className="hero">
        <h1>Research any stock with a team of AI analysts</h1>
        <p>
          Enter a company or ticker. Four specialised agents study the numbers,
          the charts, the news and the risks, then a supervisor combines
          everything into one clear report.
        </p>
        <div className="hero-actions">
          <Link className="btn btn-big" to="/signup">Get started free</Link>
          <Link className="btn btn-big btn-ghost" to="/signin">I already have an account</Link>
        </div>
      </header>

      <section className="grid">
        {agents.map(([title, text]) => (
          <div className="card" key={title}>
            <h3>{title} Agent</h3>
            <p>{text}</p>
          </div>
        ))}
      </section>

      <footer className="footer">
        For learning and research only. Not financial advice.
      </footer>
    </div>
  );
}
