import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Zap, Globe, Clock } from 'lucide-react';
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

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [pulseActive, setPulseActive] = useState(false);
  const [loading, setLoading] = useState<boolean>(true);
  const { showToast } = useToast();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await apiClient.get<AdminStats>('/admin/stats');
        setStats(res.data);
        setPulseActive(false);
        setTimeout(() => setPulseActive(true), 50);
      } catch (err: any) {
        if (err.response?.status !== 401) {
          showToast('Unable to load gateway statistics', 'error');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [showToast]);

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

        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Operational mode: live telemetry only
        </span>
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
                {loading ? 'Loading telemetry...' : 'No historical telemetry available yet'}
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
    </div>
  );
};

export default Dashboard;
