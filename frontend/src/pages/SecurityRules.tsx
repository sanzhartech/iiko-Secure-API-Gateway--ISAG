import React from 'react';
import { Lock, Shield, CheckCircle, AlertOctagon } from 'lucide-react';
import '../styles/theme.css';

export const SecurityRules: React.FC = () => {
  return (
    <div style={{ padding: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <Lock size={28} color="var(--accent-cyan)" />
        <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Security Rules & Policies</h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <Shield size={20} color="var(--accent-mint)" />
            <h3 style={{ fontSize: '1.1rem' }}>Global Rate Limiting</h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px' }}>
            Current state: <strong>Active</strong>. 
            Burst limit: 1000 req/s. 
            Sustained: 200 req/s.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-mint)' }}>
            <CheckCircle size={16} />
            <span style={{ fontSize: '0.8rem' }}>DDoS Protection Active</span>
          </div>
        </div>

        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <AlertOctagon size={20} color="var(--accent-crimson)" />
            <h3 style={{ fontSize: '1.1rem' }}>IP Whitelist / Blacklist</h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px' }}>
            Manage trusted source IPs and ranges. 
            Blacklisted: 1,242 IPs. 
            Whitelisted: 48 ranges.
          </p>
          <button className="btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
            Modify Rules
          </button>
        </div>
      </div>

      <div className="glass-card" style={{ marginTop: '24px', opacity: 0.6 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <Shield size={20} color="var(--text-muted)" />
          <h3 style={{ fontSize: '1.1rem' }}>Advanced JWT Policy (Coming Soon)</h3>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Configurable claim validation (iss, aud, sub) and automated public key rotation via JWKS.
        </p>
      </div>
    </div>
  );
};

export default SecurityRules;
