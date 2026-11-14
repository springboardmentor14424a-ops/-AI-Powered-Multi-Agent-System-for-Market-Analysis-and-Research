
import { useState } from "react";
import "./App.css";

function App() {
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: ""
  });

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setMessage("");
    setError("");

    if (formData.password !== formData.confirm_password) {
      setError("Passwords do not match!");
      return;
    }

    if (formData.password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/register",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(formData)
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Registration failed");
      }

      setMessage(
        `Registration successful! Welcome, ${data.full_name}.`
      );

      setFormData({
        full_name: "",
        email: "",
        password: "",
        confirm_password: ""
      });

    } catch (err) {
      setError(err.message || "Unable to connect to server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="register-card">

        <h1>Stock Research Analyst</h1>

        <p className="subtitle">
          Create your account to get started
        </p>

        <form onSubmit={handleSubmit}>

          <label>Full Name</label>
          <input
            type="text"
            name="full_name"
            placeholder="Enter your full name"
            value={formData.full_name}
            onChange={handleChange}
            required
            minLength={2}
            maxLength={100}
          />

          <label>Email Address</label>
          <input
            type="email"
            name="email"
            placeholder="Enter your email"
            value={formData.email}
            onChange={handleChange}
            required
          />

          <label>Password</label>
          <input
            type="password"
            name="password"
            placeholder="Create a password"
            value={formData.password}
            onChange={handleChange}
            minLength={8}
            maxLength={128}
            required
          />

          <label>Confirm Password</label>
          <input
            type="password"
            name="confirm_password"
            placeholder="Confirm your password"
            value={formData.confirm_password}
            onChange={handleChange}
            minLength={8}
            maxLength={128}
            required
          />

          {error && (
            <p className="error">{error}</p>
          )}

          {message && (
            <p className="success">{message}</p>
          )}

          <button type="submit" disabled={loading}>
            {loading ? "Registering..." : "Create Account"}
          </button>

        </form>

        <p className="footer">
          Multi-Agent Stock Research Analyst
        </p>

      </div>
    </div>
  );
}



import Login from "./login";
import Dashboard from "./Dashboard";

function App() {
    const path = window.location.pathname;

    if (path === "/dashboard") {
        return <Dashboard />;
    }

    return <Login />;
}

export default App;
