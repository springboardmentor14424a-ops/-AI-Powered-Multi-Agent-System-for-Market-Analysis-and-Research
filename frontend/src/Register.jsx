import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

function Register() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          confirm_password: confirmPassword
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Registration successful! Redirecting to login...');
        setTimeout(() => navigate('/'), 1500);
      } else {
        setError(data.detail || 'Registration failed.');
      }
    } catch (err) {
      setError('Error connecting to the server.');
    }
  };

  return (
    <div style={{
      minHeight: '100vh', backgroundColor: '#f3f4f6',
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      fontFamily: '"Inter", "Segoe UI", sans-serif', padding: '20px'
    }}>
      <div style={{
        width: '100%', maxWidth: '400px', backgroundColor: 'white',
        padding: '32px', borderRadius: '12px', boxShadow: '0 10px 25px rgba(0, 0, 0, 0.05)'
      }}>
        <h2 style={{ margin: '0 0 20px 0', color: '#111827', textAlign: 'center' }}>
          Create Account
        </h2>

        {error && (
          <div style={{ backgroundColor: '#fef2f2', color: '#b91c1c', padding: '10px', borderRadius: '6px', fontSize: '13px', marginBottom: '16px' }}>
            {error}
          </div>
        )}
        {success && (
          <div style={{ backgroundColor: '#ecfdf5', color: '#065f46', padding: '10px', borderRadius: '6px', fontSize: '13px', marginBottom: '16px' }}>
            {success}
          </div>
        )}

        <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <input
            type="text"
            placeholder="Full Name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            style={{ padding: '10px 12px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '14px' }}
          />
          <input
            type="email"
            placeholder="Email Address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ padding: '10px 12px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '14px' }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ padding: '10px 12px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '14px' }}
          />
          <input
            type="password"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            style={{ padding: '10px 12px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '14px' }}
          />
          <button
            type="submit"
            style={{
              backgroundColor: '#2563eb', color: 'white', border: 'none',
              padding: '10px', borderRadius: '6px', fontSize: '14px', fontWeight: '600', cursor: 'pointer'
            }}
          >
            Register
          </button>
        </form>

        <p style={{ marginTop: '18px', textAlign: 'center', fontSize: '13px', color: '#6b7280' }}>
          Already have an account? <Link to="/" style={{ color: '#2563eb', fontWeight: '600', textDecoration: 'none' }}>Log In</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;