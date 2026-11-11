import { useEffect, useState } from "react";
import axios from "axios";

function Dashboard({ token, onLogout }) {

    const [user, setUser] = useState(null);
    const [error, setError] = useState("");

    useEffect(() => {

        const fetchProfile = async () => {

            try {

                const response = await axios.get(
                    "http://127.0.0.1:8000/auth/me",
                    {
                        headers: {
                            Authorization: `Bearer ${token}`
                        }
                    }
                );

                setUser(response.data);

            } catch (err) {

                setError("Session expired. Please log in again.");

                onLogout();

            }

        };

        fetchProfile();

    }, [token, onLogout]);

    if (error) {
        return <p className="error">{error}</p>;
    }

    if (!user) {
        return <p>Loading dashboard...</p>;
    }

    return (

        <div className="auth-container">

            <h2>Welcome, {user.full_name}!</h2>

            <p>Email: {user.email}</p>

            <p>You have successfully accessed your dashboard.</p>

            <button onClick={onLogout}>
                Logout
            </button>

        </div>

    );

}

export default Dashboard;