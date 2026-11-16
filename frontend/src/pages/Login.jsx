import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";
import { colors, typography } from "../theme";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login", { email, password });
      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("user", JSON.stringify(response.data.user));
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logoRow}>
          <img src="/logo.jpg" alt="R-AIstock Logo" style={styles.logoImg} />
          <span style={styles.brand}>
            R-<span style={{ color: colors.goldBright }}>AI</span>stock
          </span>
        </div>
        <h2 style={styles.title}>Welcome Back</h2>
        <p style={styles.subtitle}>Sign in to your multi-agent research terminal</p>

        {error && <div style={styles.errorBox}>{error}</div>}

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>Email Address</label>
          <input
            type="email"
            placeholder="analyst@raistock.ai"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={styles.input}
          />

          <label style={styles.label}>Password</label>
          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={styles.input}
          />

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? "Authenticating..." : "Sign In"}
          </button>
        </form>

        <p style={styles.footerText}>
          New to R-AIstock?{" "}
          <Link to="/register" style={styles.link}>
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.bgCanvas,
    color: colors.textPrimary,
    fontFamily: typography.fontFamily,
  },
  card: {
    width: "100%",
    maxWidth: "400px",
    backgroundColor: colors.bgSurface,
    padding: "36px",
    borderRadius: "16px",
    border: `1px solid rgba(230, 194, 122, 0.35)`,
    boxShadow: `0 20px 50px rgba(0, 0, 0, 0.65), 0 0 25px ${colors.goldGlow}`,
  },
  logoRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "12px",
    marginBottom: "16px",
  },
  logoImg: {
    width: "40px",
    height: "40px",
    borderRadius: "10px",
    objectFit: "cover",
    border: `1px solid ${colors.gold}`,
  },
  brand: {
    fontSize: "23px",
    fontWeight: "700",
    letterSpacing: "0.4px",
    color: colors.textPrimary,
  },
  title: { margin: "0 0 4px 0", fontSize: typography.subHeading, fontWeight: "600", textAlign: "center" },
  subtitle: { margin: "0 0 24px 0", fontSize: typography.caption, color: colors.textMuted, textAlign: "center" },
  form: { display: "flex", flexDirection: "column", gap: "12px" },
  label: { fontSize: typography.caption, fontWeight: "500", color: colors.textMuted },
  input: {
    padding: "11px 14px",
    borderRadius: "10px",
    border: `1px solid ${colors.borderSubtle}`,
    backgroundColor: colors.bgCanvas,
    color: colors.textPrimary,
    fontSize: typography.body,
    fontFamily: typography.fontFamily,
    outline: "none",
  },
  button: {
    marginTop: "12px",
    padding: "12px",
    borderRadius: "10px",
    border: `1px solid ${colors.gold}`,
    background: `linear-gradient(135deg, ${colors.violet}, #4F1FA3)`,
    color: colors.textPrimary,
    fontWeight: "600",
    fontSize: "14px",
    fontFamily: typography.fontFamily,
    cursor: "pointer",
    boxShadow: `0 6px 20px ${colors.violetGlow}`,
  },
  errorBox: {
    backgroundColor: "rgba(239, 68, 68, 0.15)",
    border: `1px solid ${colors.danger}`,
    color: colors.textPrimary,
    padding: "10px 12px",
    borderRadius: "10px",
    fontSize: typography.caption,
    marginBottom: "14px",
  },
  footerText: { marginTop: "20px", textAlign: "center", fontSize: typography.caption, color: colors.textMuted },
  link: { color: colors.goldBright, textDecoration: "none", fontWeight: "600" },
};