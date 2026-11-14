import { Link } from "react-router-dom";

export default function Logo() {
  return (
    <Link to="/" className="logo" aria-label="Multi-Agent Stock Research Analyst home">
      <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
        <rect width="28" height="28" rx="8" fill="var(--accent)" />
        <path
          d="M6 19l5-6 4 3 7-8"
          fill="none"
          stroke="#04120c"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span>
        Stock Research Analyst <em>Multi-Agent</em>
      </span>
    </Link>
  );
}
