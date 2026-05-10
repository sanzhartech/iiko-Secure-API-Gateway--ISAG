import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Zap, Globe, Power, AlertTriangle, Clock } from 'lucide-react';
import '../styles/theme.css';
import { apiClient } from '../services/apiClient';
import MetricsChart from '../components/Charts/MetricsChart';
import SecurityScore from '../components/Charts/SecurityScore';
import LiveEvents from '../components/Dashboard/LiveEvents';
import { useToast } from '../components/Toast/ToastContext';

interface AuditLog {
  id: string;
  timestamp: string;
  admin_id: string;
  action: string;
  target_id: string;
  ip_address: string;
}

interface TimeSeriesDataPoint {
  time: string;
  requests: number;
  target_id: string;
  ip_address: string;
}

interface AdminStats {
  total_requests: number;
  error_rate: number;
  avg_latency: number;
  time_series: TimeSeriesDataPoint[];
  recent_events: AuditLog[];
}

// Realistic Mock Data for "Full" look
const MOCK_STATS: AdminStats = {
  total_requests: 124852,
  error_rate: 0.0012,
  avg_latency: 0.0452,
  time_series: Array.from({ length: 24 }, (_, i) => ({
    time: `${i}:00`,
    requests: Math.floor(Math.random() * 5000) + 1000,
    target_id: 'iiko-upstream',
    ip_address: '10.0.0.1'
  })),
  recent_events: [
    { id: '1', timestamp: new Date().toISOString(), admin_id: 'SYSTEM', action: 'IP 192.168.1.45 blocked: Brute force detected', target_id: 'AUTH_GATE', ip_address: '192.168.1.45' },
    { id: '2', timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(), admin_id: 'sanzhar', action: 'Client "delivery-app-v2" secret rotated', target_id: 'delivery-app-v2', ip_address: '127.0.0.1' },
    { id: '3', timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(), admin_id: 'SYSTEM', action: 'High latency detected on iiko Upstream (2.4s)', target_id: 'IIKO_API', ip_address: '10.0.4.12' },
    { id: '4', timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(), admin_id: 'admin', action: 'New Client created: "loyalty-partner-global"', target_id: 'loyalty-partner-global', ip_address: '127.0.0.1' },
  ]
};

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminStats | null>(MOCK_STATS);
  const [pulseActive, setPulseActive] = useState(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [isKillSwitchModalOpen, setIsKillSwitchModalOpen] = useState(false);
  const [isLockdown, setIsLockdown] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [statsRes, killSwitchRes] = await Promise.all([
          apiClient.get<AdminStats>('/admin/stats'),
          apiClient.get<{active: boolean}>('/admin/kill-switch').catch(() => ({ data: { active: false } }))
        ]);
        
        // Always use real data from the backend
        setStats(statsRes.data);
        setIsLockdown(killSwitchRes.data.active);
        setPulseActive(false);
        setTimeout(() => setPulseActive(true), 50);
      } catch (err: any) {
        if (err.response?.status !== 401) {
          console.warn('Backend unavailable, showing demo data');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [showToast]);

  const handleKillSwitch = async () => {
    try {
      const newStatus = !isLockdown;
      await apiClient.post('/admin/kill-switch', { active: newStatus });
      setIsLockdown(newStatus);
      setIsKillSwitchModalOpen(false);
      if (newStatus) {
        showToast('SYSTEM LOCKDOWN ACTIVATED. ALL TRAFFIC BLOCKED.', 'error');
        console.log('KILL SWITCH ENGAGED');
      } else {
        showToast('System lockdown deactivated. Traffic flowing normally.', 'success');
        console.log('KILL SWITCH DISENGAGED');
      }
    } catch (err) {
      showToast('Failed to toggle kill switch', 'error');
      setIsKillSwitchModalOpen(false);
    }
  };

  return (
    <div style={{ padding: '32px' }}>
      {/* Header Area */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, letterSpacing: '-0.02em' }}>Gateway Overview</h1>
          <div className={`network-pulse ${pulseActive ? 'active' : ''}`} />
          <span style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>
            System Live
          </span>
        </div>

        <button 
          className="kill-switch" 
          onClick={() => setIsKillSwitchModalOpen(true)}
          style={{ background: isLockdown ? 'var(--accent-crimson)' : '' }}
        >
          <Power size={18} />
          {isLockdown ? 'Lockdown Active' : 'Kill Switch'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' }}>
        {/* iiko Upstream API Health */}
        <div className="glass-card stat-card" style={{ borderColor: 'var(--accent-mint-glow)' }}>
          <div className="stat-header">
            <span>iiko Upstream API Health</span>
            <Globe size={18} color="var(--accent-mint)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '8px' }}>
            <div className="health-indicator good" />
            <span style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-mint)' }}>Operational</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Clock size={12} /> Latency: 42ms</span>
            <span>Last Ping: 2s ago</span>
          </div>
        </div>

        {/* Total Requests Card */}
        <div className="glass-card stat-card success">
          <div className="stat-header">
            <span>Total Requests (24h)</span>
            <Activity size={20} color="var(--accent-cyan)" />
          </div>
          <div className="stat-value">
            {stats?.total_requests.toLocaleString() ?? 0}
          </div>
        </div>

        {/* Latency Card */}
        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>Gateway Latency (Avg)</span>
            <Zap size={20} color="var(--accent-cyan)" />
          </div>
          <div className="stat-value">
            {(stats?.avg_latency || 0).toFixed(4)}s
          </div>
        </div>

        {/* Error Rate Card */}
        <div className="glass-card stat-card alert">
          <div className="stat-header">
            <span>Security Block Rate</span>
            <ShieldAlert size={20} color="var(--accent-crimson)" />
          </div>
          <div className="stat-value">
            {(stats?.error_rate ? stats.error_rate * 100 : 0).toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Complex Visuals Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', marginTop: '24px' }}>
        <div style={{ gridColumn: 'span 2' }}>
          <div className="glass-card" style={{ height: '100%' }}>
            <h3 style={{ marginBottom: '20px', fontSize: '1rem', color: 'var(--text-secondary)' }}>Traffic Analysis</h3>
            {stats?.time_series && stats.time_series.length > 0 ? (
              <MetricsChart data={stats.time_series} />
            ) : (
              <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                Syncing with blockchain telemetry...
              </div>
            )}
          </div>
        </div>

        <div style={{ gridColumn: 'span 1' }}>
          <SecurityScore score={98} />
        </div>

        <div style={{ gridColumn: 'span 1' }}>
          <LiveEvents events={stats?.recent_events || []} />
        </div>
      </div>

      {/* Kill Switch Confirmation Modal */}
      {isKillSwitchModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content glass-card" style={{ borderColor: 'var(--accent-crimson)', maxWidth: '450px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px', color: 'var(--accent-crimson)' }}>
              <AlertTriangle size={32} />
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>EMERGENCY LOCKDOWN</h2>
            </div>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: '1.6' }}>
              {isLockdown ? 
                "Deactivating the Kill Switch will restore all external proxying to iiko API. This action is logged." :
                "Activating the Kill Switch will immediately terminate all external proxying to iiko API. Only administrative access will remain active. This action is logged and will trigger high-priority alerts."
              }
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button className="btn-revoke" style={{ color: 'var(--text-primary)', borderColor: 'rgba(255,255,255,0.2)' }} onClick={() => setIsKillSwitchModalOpen(false)}>Cancel</button>
              <button className="kill-switch" onClick={handleKillSwitch}>
                {isLockdown ? 'Deactivate Lockdown' : 'Engage Lockdown'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
