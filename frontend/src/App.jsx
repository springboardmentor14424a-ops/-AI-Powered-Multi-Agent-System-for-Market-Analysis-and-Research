import { Link, Route, Routes } from "react-router-dom";
import { GuestRoute, ProtectedRoute } from "./components/RouteGuards";
import Dashboard from "./pages/Dashboard";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ReportPage from "./pages/ReportPage";

function NotFound() {
  return (
    <div className="center-screen">
      <div className="card narrow center-text">
        <h1>Page not found</h1>
        <p className="muted">The page you're looking for doesn't exist.</p>
        <Link className="btn btn-primary" to="/">
          Back to home
        </Link>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route
        path="/login"
        element={
          <GuestRoute>
            <Login />
          </GuestRoute>
        }
      />
      <Route
        path="/register"
        element={
          <GuestRoute>
            <Register />
          </GuestRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/research/:id"
        element={
          <ProtectedRoute>
            <ReportPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
