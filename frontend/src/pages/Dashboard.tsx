import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Zap } from 'lucide-react';
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
  const [error, setError] = useState<string | null>(null);
  const { showToast } = useToast();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await apiClient.get<AdminStats>('/admin/stats');
        setStats(res.data);

        // Trigger pulse animation
        setPulseActive(false);
        setTimeout(() => setPulseActive(true), 50);
        setError(null);
      } catch (err: any) {
        // If it's a 401, the interceptor will handle it.
        // For other errors, we just show a toast and keep existing data.
        if (err.response?.status !== 401) {
          showToast('Failed to refresh metrics. Retrying...', 'error');
          setError('Data sync error');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    // Real-time polling every 5 seconds
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [showToast]);

  if (loading && !stats) return <div className="glass-card" style={{ padding: '32px' }}>Loading gateway status...</div>;

  return (
    <div style={{ padding: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700, letterSpacing: '-0.02em' }}>Gateway Overview</h1>
        <div
          className={`network-pulse ${pulseActive ? 'active' : ''}`}
          title="Live Connection"
        />
        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Live
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px' }}>
        {/* Total Requests Card */}
        <div className="glass-card stat-card success">
          <div className="stat-header">
            <span>Total Requests</span>
            <Activity size={20} color="var(--accent-cyan)" />
          </div>
          <div className="stat-value">
            {stats?.total_requests.toLocaleString() ?? 0}
          </div>
        </div>

        {/* Latency Card */}
        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>Avg Latency (s)</span>
            <Zap size={20} color="var(--text-secondary)" />
          </div>
          <div className="stat-value" style={{ color: 'var(--text-primary)' }}>
            {stats?.avg_latency.toFixed(4) ?? '0.0000'}
          </div>
        </div>

        {/* Error Rate Card */}
        <div className="glass-card stat-card alert">
          <div className="stat-header">
            <span>Error / Block Rate</span>
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
          {stats?.time_series && stats.time_series.length > 0 ? (
            <MetricsChart data={stats.time_series} />
          ) : (
            <div className="glass-card" style={{ height: '350px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
              Loading metrics...
            </div>
          )}
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
