import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";

function syncTokenFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get("token") || params.get("access_token");

  if (urlToken) {
    localStorage.setItem("token", urlToken);
    localStorage.setItem("access_token", urlToken);
    window.history.replaceState({}, document.title, window.location.pathname);
  }
}

function ProtectedRoute({ children }) {
  syncTokenFromUrl();
  const token =
    localStorage.getItem("token") || localStorage.getItem("access_token");
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  syncTokenFromUrl();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}