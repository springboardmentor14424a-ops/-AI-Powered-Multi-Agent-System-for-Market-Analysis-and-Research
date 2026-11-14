
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signupUser } from "../services/authService";

function Signup() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const [passwordFocused, setPasswordFocused] = useState(false);
  const [confirmTouched, setConfirmTouched] = useState(false);

  // Password validation rules
  const passwordRules = {
    length: form.password.length >= 8,
    uppercase: /[A-Z]/.test(form.password),
    lowercase: /[a-z]/.test(form.password),
    number: /[0-9]/.test(form.password),
    special: /[^A-Za-z0-9]/.test(form.password),
  };

  const passwordValid = Object.values(passwordRules).every(Boolean);

  // Check whether passwords match
  const passwordsMatch =
    form.password.length > 0 &&
    form.confirm_password.length > 0 &&
    form.password === form.confirm_password;

  // Handle input changes
  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setMessage("");

    if (!passwordValid) {
      setError("Please satisfy all password requirements.");
      return;
    }

    if (!passwordsMatch) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      await signupUser(form);

      setMessage("Account created successfully! Please sign in.");

      setTimeout(() => navigate("/login"), 1200);

    } catch (err) {
      setError(
        err.response?.data?.detail || "Registration failed."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>

        <Link to="/" className="back-link">
          ← Home
        </Link>

        <h1>Create Account</h1>

        <p>
          Join your AI-powered stock research workspace.
        </p>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {message && (
          <div className="success-message">
            {message}
          </div>
        )}

        {/* FULL NAME */}

        <label>Full Name</label>

        <input
          name="full_name"
          value={form.full_name}
          onChange={handleChange}
          placeholder="Enter your full name"
          required
        />

        {/* EMAIL */}

        <label>Email Address</label>

        <input
          name="email"
          type="email"
          value={form.email}
          onChange={handleChange}
          placeholder="Enter your email"
          required
        />

        {/* PASSWORD */}

        <label>Password</label>

        <input
          name="password"
          type="password"
          value={form.password}
          onChange={handleChange}
          onFocus={() => setPasswordFocused(true)}
          onBlur={() => setPasswordFocused(false)}
          placeholder="Create a strong password"
          maxLength={72}
          required
        />

        {/* PASSWORD REQUIREMENTS - VISIBLE ONLY ON FOCUS */}

        {passwordFocused && (
          <div className="password-requirements">

            <p>Password must contain:</p>

            <ul>
              <li className={passwordRules.length ? "valid" : "invalid"}>
                At least 8 characters
              </li>

              <li className={passwordRules.uppercase ? "valid" : "invalid"}>
                One uppercase letter (A-Z)
              </li>

              <li className={passwordRules.lowercase ? "valid" : "invalid"}>
                One lowercase letter (a-z)
              </li>

              <li className={passwordRules.number ? "valid" : "invalid"}>
                One number (0-9)
              </li>

              <li className={passwordRules.special ? "valid" : "invalid"}>
                One special character (@, #, !, etc.)
              </li>
            </ul>

          </div>
        )}

        {/* CONFIRM PASSWORD */}

        <label>Confirm Password</label>

        <input
          name="confirm_password"
          type="password"
          value={form.confirm_password}
          onChange={(e) => {
            setForm({
              ...form,
              confirm_password: e.target.value,
            });
            setConfirmTouched(true);
          }}
          onBlur={() => setConfirmTouched(true)}
          placeholder="Confirm your password"
          maxLength={72}
          required
        />

        {/* SHOW ONLY IF PASSWORDS DO NOT MATCH */}

        {confirmTouched &&
          form.confirm_password.length > 0 &&
          !passwordsMatch && (
            <p className="match-error">
              ✕ Passwords do not match
            </p>
          )}

        {/* SUBMIT */}

        <button type="submit" disabled={loading}>
          {loading ? "Creating account..." : "Sign Up"}
        </button>

        <p className="auth-footer">
          Already have an account?{" "}
          <Link to="/login">Sign In</Link>
        </p>

      </form>
    </div>
  );
}

export default Signup;
