
import {
  createContext,
  useContext,
  useEffect,
  useState,
} from 'react'

import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)

  const [token, setToken] = useState(
    () => localStorage.getItem('access_token')
  )

  const [loading, setLoading] = useState(true)

  // Load logged-in user when the application starts
  useEffect(() => {
    let active = true

    const loadUser = async () => {
      if (!token) {
        if (active) {
          setUser(null)
          setLoading(false)
        }
        return
      }

      try {
        const response = await api.get('/auth/me', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (active) {
          setUser(response.data)
        }
      } catch (error) {
        console.error('Authentication verification failed:', error)

        if (active) {
          // Clear the token only when the server rejects authentication
          if (error.response?.status === 401 ||
              error.response?.status === 403) {
            localStorage.removeItem('access_token')
            setToken(null)
            setUser(null)
          } else {
            // Keep the token if the server is temporarily unavailable
            setUser(null)
          }
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    setLoading(true)
    loadUser()

    return () => {
      active = false
    }
  }, [token])

  // Register user
  const register = async (fullName, email, password) => {
    const response = await api.post('/auth/register', {
      full_name: fullName,
      email,
      password,
    })

    return response.data
  }

  // Login user
  const login = async (email, password) => {
    const response = await api.post('/auth/login', {
      email,
      password,
    })

    const accessToken = response.data.access_token

    if (!accessToken) {
      throw new Error('Access token was not received.')
    }

    // Verify the token before saving the authenticated session
    const userResponse = await api.get('/auth/me', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })

    // Save session after successful verification
    localStorage.setItem('access_token', accessToken)

    setToken(accessToken)
    setUser(userResponse.data)

    return userResponse.data
  }

  // Logout user
  const logout = () => {
    localStorage.removeItem('access_token')

    setToken(null)
    setUser(null)
    setLoading(false)
  }

  const isAuthenticated = Boolean(token && user)

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        register,
        login,
        logout,
        isAuthenticated,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error(
      'useAuth must be used inside AuthProvider'
    )
  }

  return context
}
