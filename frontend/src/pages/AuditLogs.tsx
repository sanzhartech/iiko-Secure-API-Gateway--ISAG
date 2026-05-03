import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, Settings, Terminal, Clock, Download } from 'lucide-react';
import { apiClient } from '../services/apiClient';
import { useToast } from '../components/Toast/ToastContext';
import '../styles/theme.css';

interface AuditLog {
  id: string;
  timestamp: string;
  admin_id: string;
  action: string;
  target_id: string;
  ip_address: string;
}

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await apiClient.get<AuditLog[]>('/admin/logs?limit=100');
        setLogs(res.data);
      } catch (_err: unknown) {
        showToast('Failed to load audit logs', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, [showToast]);

  const getActionIcon = (action: string) => {
    if (action.includes('REVOKED')) return <ShieldAlert size={16} color="var(--accent-crimson)" />;
    if (action.includes('CREATED') || action.includes('ACTIVATED')) return <Activity size={16} color="var(--accent-cyan)" />;
    if (action.includes('LOGIN')) return <Terminal size={16} color="var(--text-secondary)" />;
    return <Settings size={16} color="var(--text-secondary)" />;
  };

  const exportToCSV = () => {
    if (logs.length === 0) {
      showToast('No logs to export', 'error');
      return;
    }

    const headers = ['Timestamp', 'Action', 'Admin ID', 'Target Client', 'IP Address'];
    const csvRows = [headers.join(',')];

    logs.forEach(log => {
      const row = [
        new Date(log.timestamp).toISOString(),
        log.action,
        log.admin_id,
        log.target_id,
        log.ip_address || 'unknown'
      ];
      // Escape commas and quotes for CSV
      csvRows.push(row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(','));
    });

    const csvString = csvRows.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `isag_audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    showToast('Export started', 'success');
  };

  return (
    <div style={{ padding: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Clock size={28} color="var(--text-primary)" />
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>System Audit Logs</h1>
        </div>
        <button className="btn-primary" onClick={exportToCSV} disabled={logs.length === 0}>
          <Download size={18} /> Export CSV
        </button>
      </div>

      <div className="glass-table-container">
        <table className="glass-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>Admin ID</th>
              <th>Target Client</th>
              <th>IP Address</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={{ textAlign: 'center' }}>Loading logs...</td></tr>
            ) : logs.map((log) => (
              <tr key={log.id}>
                <td style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 500 }}>
                    {getActionIcon(log.action)}
                    {log.action}
                  </div>
                </td>
                <td>{log.admin_id}</td>
                <td style={{ fontFamily: 'monospace' }}>{log.target_id}</td>
                <td style={{ color: 'var(--text-secondary)' }}>{log.ip_address || 'unknown'}</td>
              </tr>
            ))}
            {!loading && logs.length === 0 && (
              <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No audit logs found.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AuditLogs;
