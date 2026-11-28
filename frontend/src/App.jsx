
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import Dashboard from './pages/dashboard/Dashboard'
import StockDetails from './pages/dashboard/StockDetails'
import ProtectedRoute from './routes/ProtectedRoute'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<Navigate to="/login" replace />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/register"
          element={<Register />}
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        {/* Stock details route used by Dashboard */}
        <Route
          path="/stock/:symbol"
          element={
            <ProtectedRoute>
              <StockDetails />
            </ProtectedRoute>
          }
        />

        {/* Backward compatibility for older stock links */}
        <Route
          path="/stocks/:symbol"
          element={
            <ProtectedRoute>
              <StockDetails />
            </ProtectedRoute>
          }
        />

        <Route
          path="*"
          element={<Navigate to="/login" replace />}
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
