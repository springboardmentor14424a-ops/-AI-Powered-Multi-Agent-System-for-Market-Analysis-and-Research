import { useCallback, useState } from "react";

import Register from "./pages/register";
import Login from "./pages/login";
import Dashboard from "./pages/Dashboard";

function App() {

    const [token, setToken] = useState(null);
    const [user, setUser] = useState(null);

    const handleLogin = (accessToken, userData) => {

        setToken(accessToken);
        setUser(userData);

    };

    const handleLogout = useCallback(() => {

        setToken(null);
        setUser(null);

    }, []);

    if (token && user) {

        return (
            <Dashboard
                token={token}
                onLogout={handleLogout}
            />
        );

    }

    return (

        <div>

            <Register />

            <hr />

            <Login onLogin={handleLogin} />

        </div>

    );

}

export default App;