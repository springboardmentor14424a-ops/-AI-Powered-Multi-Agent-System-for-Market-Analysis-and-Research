
import { useState } from "react";
import axios from "axios";

function Register({ onBack }) {
    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setSuccess("");

        if (password !== confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        setLoading(true);

        try {
            await axios.post(
                "http://127.0.0.1:8000/auth/register",
                {
                    full_name: fullName,
                    email,
                    password,
                    confirm_password: confirmPassword
                }
            );

            setSuccess("Registration successful! You can now log in.");

            setFullName("");
            setEmail("");
            setPassword("");
            setConfirmPassword("");

        } catch (err) {
            setError(
                err.response?.data?.detail || "Registration failed."
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-container">

                {/* Left panel */}
                <div className="login-visual">
                    <div className="login-decoration"></div>

                    <h1>
                        Join Market<br />
                        Research AI
                    </h1>

                    <p>
                        Create your account and explore intelligent
                        market insights, stock research, and AI-powered
                        analysis.
                    </p>
                </div>

                {/* Registration form */}
                <div className="login-form-section">

                    <h2>Create Account</h2>

                    <p className="login-subtitle">
                        Sign up to get started with your research journey.
                    </p>

                    <form
                        className="login-form"
                        onSubmit={handleSubmit}
                    >

                        <div className="form-group">
                            <label>Full Name</label>
                            <input
                                type="text"
                                placeholder="Enter your full name"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                required
                            />
                        </div>

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
                                placeholder="Create a password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Confirm Password</label>
                            <input
                                type="password"
                                placeholder="Confirm your password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            className="login-button"
                            disabled={loading}
                        >
                            {loading ? "Creating Account..." : "Create Account"}
                        </button>
                        <button
                            type="button"
                            className="back-button"
                            onClick={onBack}
                        >
                            Back to Welcome
                        </button>

                    </form>

                    {error && (
                        <p className="error-message">{error}</p>
                    )}

                    {success && (
                        <p className="success-message">{success}</p>
                    )}

                    <p className="login-footer">
                        AI-Powered Multi-Agent System<br />
                        Market Analysis and Research
                    </p>

                </div>
            </div>
        </div>
    );
}

export default Register;
