import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";
import { colors, typography } from "../theme";

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (formData.password !== formData.confirm_password) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/auth/register", formData);
      setSuccess("Account created! Redirecting to sign in...");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail[0]?.msg || "Validation error.");
      } else {
        setError(detail || "Registration failed. Please try again.");
      }
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
        <h2 style={styles.title}>Create Analyst Account</h2>
        <p style={styles.subtitle}>AI-powered equity intelligence & portfolio tracking</p>

        {error && <div style={styles.errorBox}>{error}</div>}
        {success && <div style={styles.successBox}>{success}</div>}

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>Full Name</label>
          <input
            type="text"
            name="full_name"
            placeholder="e.g. Kanan Sharma"
            value={formData.full_name}
            onChange={handleChange}
            required
            style={styles.input}
          />

          <label style={styles.label}>Email Address</label>
          <input
            type="email"
            name="email"
            placeholder="analyst@raistock.ai"
            value={formData.email}
            onChange={handleChange}
            required
            style={styles.input}
          />

          <label style={styles.label}>Password</label>
          <input
            type="password"
            name="password"
            placeholder="Minimum 6 characters"
            value={formData.password}
            onChange={handleChange}
            required
            style={styles.input}
          />

          <label style={styles.label}>Confirm Password</label>
          <input
            type="password"
            name="confirm_password"
            placeholder="Re-enter password"
            value={formData.confirm_password}
            onChange={handleChange}
            required
            style={styles.input}
          />

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? "Creating Account..." : "Create Account"}
          </button>
        </form>

        <p style={styles.footerText}>
          Already have an account?{" "}
          <Link to="/login" style={styles.link}>
            Sign in
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
  form: { display: "flex", flexDirection: "column", gap: "11px" },
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
  successBox: {
    backgroundColor: "rgba(125, 226, 96, 0.15)",
    border: `1px solid ${colors.greenBull}`,
    color: colors.greenBull,
    padding: "10px 12px",
    borderRadius: "10px",
    fontSize: typography.caption,
    marginBottom: "14px",
  },
  footerText: { marginTop: "20px", textAlign: "center", fontSize: typography.caption, color: colors.textMuted },
  link: { color: colors.goldBright, textDecoration: "none", fontWeight: "600" },
};