import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth";

function Loading() {
  return (
    <div className="center-screen">
      <div className="spinner" role="status" aria-label="Loading" />
    </div>
  );
}

// Only signed-in users may see these pages; others are sent to /login.
export function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}

// Login/register pages: signed-in users are sent on to the dashboard
// (or to the page they originally tried to open).
export function GuestRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Loading />;
  if (user) return <Navigate to={location.state?.from?.pathname ?? "/dashboard"} replace />;
  return children;
}
