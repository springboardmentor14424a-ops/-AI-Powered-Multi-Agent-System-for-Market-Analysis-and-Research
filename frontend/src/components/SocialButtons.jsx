import { useEffect, useState } from "react";
import { api } from "../api";

const BASE = import.meta.env.VITE_API_URL ?? "";

const ICONS = {
  google: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#4285F4" d="M23.5 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.46a5.52 5.52 0 0 1-2.4 3.62v3h3.88c2.27-2.09 3.56-5.17 3.56-8.81z" />
      <path fill="#34A853" d="M12 24c3.24 0 5.96-1.07 7.94-2.91l-3.88-3c-1.07.72-2.45 1.15-4.06 1.15-3.12 0-5.77-2.11-6.71-4.94H1.28v3.09A12 12 0 0 0 12 24z" />
      <path fill="#FBBC05" d="M5.29 14.3a7.2 7.2 0 0 1 0-4.6V6.61H1.28a12 12 0 0 0 0 10.78l4.01-3.09z" />
      <path fill="#EA4335" d="M12 4.76c1.76 0 3.34.61 4.58 1.79l3.43-3.43C17.95 1.19 15.24 0 12 0A12 12 0 0 0 1.28 6.61L5.29 9.7C6.23 6.87 8.88 4.76 12 4.76z" />
    </svg>
  ),
  microsoft: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#F25022" d="M1 1h10.5v10.5H1z" />
      <path fill="#7FBA00" d="M12.5 1H23v10.5H12.5z" />
      <path fill="#00A4EF" d="M1 12.5h10.5V23H1z" />
      <path fill="#FFB900" d="M12.5 12.5H23V23H12.5z" />
    </svg>
  ),
  apple: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701" />
    </svg>
  ),
  x: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  ),
};

const FALLBACK = [
  { id: "google", label: "Google", enabled: false },
  { id: "microsoft", label: "Microsoft", enabled: false },
  { id: "apple", label: "Apple", enabled: false },
  { id: "x", label: "X", enabled: false },
];

export default function SocialButtons({ verb = "Continue", onNotice }) {
  const [providers, setProviders] = useState(FALLBACK);

  useEffect(() => {
    api("/auth/providers").then(setProviders).catch(() => {});
  }, []);

  const click = (p) => {
    if (!p.enabled) {
      onNotice?.(`${p.label} sign-in isn't set up on this server yet. Add its keys to backend/.env (see the README).`);
      return;
    }
    // A full-page navigation: the provider's login page can't be shown inside a fetch call.
    window.location.href = `${BASE}/api/auth/oauth/${p.id}/login`;
  };

  return (
    <div className="social">
      <div className="social-grid">
        {providers.map((p) => (
          <button
            key={p.id}
            type="button"
            className={`btn btn-ghost social-btn${p.enabled ? "" : " is-off"}`}
            onClick={() => click(p)}
            aria-label={`${verb} with ${p.label}`}
          >
            {ICONS[p.id]}
            <span>{p.label}</span>
          </button>
        ))}
      </div>
      <div className="divider"><span>or use your email</span></div>
    </div>
  );
}
