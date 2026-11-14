
import { useCallback, useState } from "react";

import Register from "./pages/register";
import Login from "./pages/login";
import Dashboard from "./pages/Dashboard";
import GoogleLoginButton from "./components/GoogleLogin";

function App() {
    const [token, setToken] = useState(null);
    const [user, setUser] = useState(null);
    const [page, setPage] = useState("welcome");

    const handleLogin = (accessToken, userData) => {
        setToken(accessToken);
        setUser(userData);
    };

    const handleLogout = useCallback(() => {
        setToken(null);
        setUser(null);
        setPage("welcome");
    }, []);

    // Show dashboard after successful login
    if (token && user) {
        return (
            <Dashboard
                token={token}
                onLogout={handleLogout}
            />
        );
    }

    // Login and registration navigation
    if (page === "login") {
        return (
            <Login
                onLogin={handleLogin}
                onBack={() => setPage("welcome")}
            />
        );
    }

    if (page === "register") {
        return (
            <Register
                onBack={() => setPage("welcome")}
            />
        );
    }

    // Initial welcome page
    return (
        <div className="welcome-page">
            <div className="welcome-card">

                <div className="welcome-icon">
                    <span>✦</span>
                </div>

                <p className="welcome-tagline">
                    AI-POWERED MARKET INTELLIGENCE
                </p>

                <h1>
                    Welcome to <br />
                    <span>Market Research AI</span>
                </h1>

                <p className="welcome-description">
                    Discover smarter insights, analyze market trends,
                    and explore the power of AI-driven research.
                    Your intelligent research journey starts here.
                </p>

                <div className="welcome-buttons">

                    <button
                        className="welcome-login-btn"
                        onClick={() => setPage("login")}
                    >
                        Login
                    </button>

                    <button
                        className="welcome-register-btn"
                        onClick={() => setPage("register")}
                    >
                        Create Account
                    </button>

                    <div className="welcome-divider">
                        <span>OR</span>
                    </div>

                    <GoogleLoginButton onLogin={handleLogin} />


                </div>

                <p className="welcome-footer">
                    AI-Powered Multi-Agent System
                    <br />
                    Market Analysis and Research
                </p>

            </div>
        </div>
    );
}

export default App;
