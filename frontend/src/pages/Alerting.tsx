import React from 'react';
import { Bell, Send, Mail, Zap, MessageSquare } from 'lucide-react';
import '../styles/theme.css';

export const Alerting: React.FC = () => {
  return (
    <div style={{ padding: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <Bell size={28} color="var(--accent-cyan)" />
        <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Real-time Alerting</h1>
      </div>

      <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
        Configure how you receive critical security and performance alerts. 
        Notifications are triggered by the 9-Stage Security Pipeline.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' }}>
        <div className="glass-card stat-card success">
          <div className="stat-header">
            <span>Telegram Bot</span>
            <Send size={18} />
          </div>
          <div style={{ marginTop: '12px' }}>
            <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>Connected</span>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Chat ID: @ISAG_Security_SOC
            </div>
          </div>
        </div>

        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>Email Gateway</span>
            <Mail size={18} />
          </div>
          <div style={{ marginTop: '12px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Not Configured</span>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Requires SMTP settings
            </div>
          </div>
        </div>

        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>Slack Webhook</span>
            <MessageSquare size={18} />
          </div>
          <div style={{ marginTop: '12px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Not Configured</span>
          </div>
        </div>
      </div>

      <div className="glass-card" style={{ marginTop: '24px' }}>
        <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Zap size={18} color="var(--accent-cyan)" /> Alert Triggers
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
            <span>Brute Force (5+ attempts/min)</span>
            <span style={{ color: 'var(--accent-mint)' }}>Critical</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
            <span>iiko Upstream Offline</span>
            <span style={{ color: 'var(--accent-crimson)' }}>High</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
            <span>Secret Rotation Required</span>
            <span style={{ color: 'var(--text-secondary)' }}>Info</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Alerting;
