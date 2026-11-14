
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Landing from "./pages/Landing";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Research from "./pages/Research";
import Watchlist from "./pages/Watchlist";
import Markets from "./pages/Markets";
import Settings from "./pages/Settings";
import Preferences from "./pages/Preferences";

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/dashboard/research" element={<Research />} />
        <Route path="/dashboard/history" element={<History />} />
        <Route path="/dashboard/watchlist" element={<Watchlist />} />
        <Route path="/dashboard/markets" element={<Markets />} />
        <Route path="/dashboard/settings" element={<Settings />} />
        <Route path="/dashboard/preferences" element={<Preferences />} />
        <Route path="*" element={<Landing />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
