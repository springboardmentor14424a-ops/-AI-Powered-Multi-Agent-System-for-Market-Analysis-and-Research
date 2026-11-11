
import { useState } from "react";
import axios from "axios";

function Login({ onLogin }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const response = await axios.post(
                "http://127.0.0.1:8000/auth/login",
                {
                    email,
                    password
                }
            );

            onLogin(
                response.data.access_token,
                response.data.user
            );

        } catch (err) {
            setError(
                err.response?.data?.detail || "Login failed. Please try again."
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">

            <div className="login-container">

                {/* Left Side Design */}
                <div className="login-visual">

                    <div className="login-decoration"></div>

                    <h1>
                        Welcome to <br />
                        Market Research AI
                    </h1>

                    <p>
                        Your intelligent workspace for market insights,
                        stock research, and AI-powered analysis.
                        Sign in to continue your journey.
                    </p>

                </div>

                {/* Right Side Login Form */}
                <div className="login-form-section">

                    <h2>Welcome Back!</h2>

                    <p className="login-subtitle">
                        Sign in to access your research dashboard.
                    </p>

                    <form
                        className="login-form"
                        onSubmit={handleSubmit}
                    >

                        <div className="form-group">
                            <label>Email Address</label>

                            <input
                                type="email"
                                placeholder="Enter your email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Password</label>

                            <input
                                type="password"
                                placeholder="Enter your password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            className="login-button"
                            disabled={loading}
                        >
                            {loading ? "Signing in..." : "Sign In"}
                        </button>

                    </form>

                    {error && (
                        <p className="error-message">
                            {error}
                        </p>
                    )}

                    <p className="login-footer">
                        AI-Powered Multi-Agent System
                        <br />
                        Market Analysis and Research
                    </p>

                </div>

            </div>

        </div>
    );
}

export default Login;
