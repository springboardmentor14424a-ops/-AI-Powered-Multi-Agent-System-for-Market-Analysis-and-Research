
import { useState } from 'react'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('signup')

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: ''
  })

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (activeTab === 'signup') {
      try {
        const response = await fetch('http://127.0.0.1:8000/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(formData)
        })

        const data = await response.json()

        if (!response.ok) {
          alert(data.detail || 'Registration failed')
          return
        }

        alert('Account created successfully!')
        console.log(data)

        setFormData({
          full_name: '',
          email: '',
          password: '',
          confirm_password: ''
        })

      } catch (error) {
        alert('Unable to connect to the server')
        console.error(error)
      }
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">

        <h1>Stock Research Analyst</h1>
        <p className="subtitle">
          Your intelligent market research workspace
        </p>

        <div className="auth-tabs">
          <button
            type="button"
            className={activeTab === 'signin' ? 'active' : ''}
            onClick={() => setActiveTab('signin')}
          >
            Sign In
          </button>

          <button
            type="button"
            className={activeTab === 'signup' ? 'active' : ''}
            onClick={() => setActiveTab('signup')}
          >
            Sign Up
          </button>
        </div>

        {activeTab === 'signup' ? (
          <>
            <h2>Create Account</h2>

            <form onSubmit={handleSubmit}>
              <input
                type="text"
                name="full_name"
                placeholder="Full Name"
                value={formData.full_name}
                onChange={handleChange}
                required
              />

              <input
                type="email"
                name="email"
                placeholder="Email Address"
                value={formData.email}
                onChange={handleChange}
                required
              />

              <input
                type="password"
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                required
              />

              <input
                type="password"
                name="confirm_password"
                placeholder="Confirm Password"
                value={formData.confirm_password}
                onChange={handleChange}
                required
              />

              <button type="submit" className="submit-btn">
                Create Account
              </button>
            </form>
          </>
        ) : (
          <>
            <h2>Welcome Back</h2>

            <form onSubmit={handleSubmit}>
              <input
                type="email"
                name="email"
                placeholder="Email Address"
                value={formData.email}
                onChange={handleChange}
                required
              />

              <input
                type="password"
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                required
              />

              <button type="submit" className="submit-btn">
                Sign In
              </button>
            </form>
          </>
        )}

      </div>
    </div>
  )
}

export default App
