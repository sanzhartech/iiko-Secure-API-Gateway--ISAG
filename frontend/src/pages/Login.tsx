import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, KeyRound, User } from 'lucide-react';
import { useToast } from '../components/Toast/ToastContext';
import { apiClient } from '../services/apiClient';
import '../styles/theme.css';

export const Login: React.FC = () => {
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { showToast } = useToast();

  useEffect(() => {
    // If already logged in, redirect to dashboard
    if (localStorage.getItem('admin_access_token')) {
      navigate('/dashboard');
    }
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await apiClient.post('/auth/token', {
        client_id: clientId,
        client_secret: clientSecret
      });

      const { access_token } = response.data;
      localStorage.setItem('admin_access_token', access_token);
      
      showToast('Login successful', 'success');
      navigate('/dashboard');
    } catch (err: any) {
      if (err.response?.status === 401) {
        showToast('Invalid credentials or insufficient permissions', 'error');
      } else if (err.response?.status === 422) {
        showToast('Validation error. Check if ID or Secret are too short.', 'error');
      } else {
        console.error('Login error:', err);
        showToast('Connection error. Is the gateway running on port 8000?', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="glass-card login-card">
        <div style={{ textAlign: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'inline-flex', padding: '16px', background: 'rgba(0, 242, 255, 0.1)', borderRadius: '50%', marginBottom: '16px' }}>
            <Shield size={48} color="var(--accent-cyan)" />
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.02em' }}>ISAG Admin</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Sign in to manage the gateway</p>
        </div>

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ position: 'relative' }}>
            <User size={20} color="var(--text-secondary)" style={{ position: 'absolute', top: '12px', left: '16px' }} />
            <input 
              type="text" 
              className="glass-input" 
              style={{ width: '100%', paddingLeft: '48px', height: '44px' }} 
              placeholder="Admin Client ID"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              required
            />
          </div>

          <div style={{ position: 'relative' }}>
            <KeyRound size={20} color="var(--text-secondary)" style={{ position: 'absolute', top: '12px', left: '16px' }} />
            <input 
              type="password" 
              className="glass-input" 
              style={{ width: '100%', paddingLeft: '48px', height: '44px' }} 
              placeholder="Admin Client Secret"
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              required
            />
          </div>

          <button 
            type="submit" 
            className="btn-primary" 
            style={{ width: '100%', justifyContent: 'center', height: '48px', marginTop: '8px' }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Secure Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
