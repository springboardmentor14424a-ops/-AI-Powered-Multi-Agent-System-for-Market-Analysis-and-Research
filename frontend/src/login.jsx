
import React, { useState } from "react";
import "./Login.css";
import Dashboard from "./dashboard";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            email: email.trim(),
            password: password
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      const accessToken = data.access_token;

      const profileResponse = await fetch(
        "http://127.0.0.1:8000/me",
        {
          method: "GET",
          headers: {
            "Authorization": `Bearer ${accessToken}`
          }
        }
      );

      const profileData = await profileResponse.json();

      if (!profileResponse.ok) {
        throw new Error(
          profileData.detail || "Unable to load dashboard"
        );
      }

      setToken(accessToken);
      setUser(profileData);
      setPassword("");

    } catch (err) {
      setError(err.message || "Unable to connect to server");
    } finally {
      setLoading(false);
    }
  };

  // Google login redirect
  const handleGoogleLogin = () => {
    window.location.href =
      "http://127.0.0.1:8000/auth/google/login";
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    setEmail("");
    setPassword("");
    setError("");
  };

  // Dashboard after successful login
  if (user && token) {
    return (
        <Dashboard
            user={user}
            token={token}
            onLogout={handleLogout}
        />
    );
 }

  // Login form
  return (
    <div className="login-container">
      <div className="login-card">

        <h1>Stock Research Analyst</h1>

        <h2>User Login</h2>

        <p className="subtitle">
          Login to access your personal dashboard
        </p>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin}>

          <label>Email Address</label>

          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label>Password</label>

          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? "Logging in..." : "Login"}
          </button>

        </form>

        {/* OR separator */}
        <div className="login-divider">
          <span>OR</span>
        </div>

        {/* Google login button */}
        <button
          type="button"
          className="google-login-button"
          onClick={handleGoogleLogin}
        >
          <svg
            className="google-icon"
            viewBox="0 0 48 48"
            aria-hidden="true"
          >
            <path
              fill="#EA4335"
              d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5Z"
            />
            <path
              fill="#4285F4"
              d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.73 7.18l7.65 5.94c4.47-4.13 7.12-10.2 7.12-17.59Z"
            />
            <path
              fill="#FBBC05"
              d="M10.53 28.59a14.4 14.4 0 0 1 0-9.18l-7.98-6.19a24 24 0 0 0 0 21.56l7.98-6.19Z"
            />
            <path
              fill="#34A853"
              d="M24 48c6.48 0 11.93-2.13 15.9-5.86l-7.65-5.94c-2.13 1.44-4.86 2.3-8.25 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48Z"
            />
          </svg>

          Continue with Google
        </button>

      </div>
    </div>
  );
}

export default Login;
