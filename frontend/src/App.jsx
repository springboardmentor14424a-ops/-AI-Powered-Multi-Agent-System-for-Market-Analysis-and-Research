import { Navigate, Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing.jsx";
import SignUp from "./pages/SignUp.jsx";
import SignIn from "./pages/SignIn.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import { getToken } from "./api.js";

// Only signed-in users may open the dashboard.
function Protected({ children }) {
  return getToken() ? children : <Navigate to="/signin" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/signup" element={<SignUp />} />
      <Route path="/signin" element={<SignIn />} />
      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
