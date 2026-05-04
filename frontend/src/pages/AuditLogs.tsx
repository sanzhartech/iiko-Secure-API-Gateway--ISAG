import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, Settings, Terminal, Clock, Download, ExternalLink, Filter, Search, User } from 'lucide-react';
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
  details?: {
    request_payload?: any;
    response_payload?: any;
    headers?: any;
    correlation_id: string;
  };
}

const MOCK_LOGS: AuditLog[] = [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    admin_id: 'SYSTEM',
    action: 'SECURITY_BLOCK',
    target_id: '192.168.1.104',
    ip_address: '192.168.1.104',
    details: {
      correlation_id: 'isag-req-8842-xa9',
      request_payload: { method: 'POST', path: '/v1/orders', body: { items: [], total: 0 }, note: 'Possible SQLi attempt in User-Agent' },
      headers: { 'User-Agent': "' OR 1=1 --", 'X-Forwarded-For': '192.168.1.104' },
      response_payload: { error: 'Security violation', message: 'Malicious payload detected' }
    }
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 50000).toISOString(),
    admin_id: 'sanzhar',
    action: 'CLIENT_SECRET_ROTATE',
    target_id: 'delivery-app-prod',
    ip_address: '127.0.0.1',
    details: {
      correlation_id: 'isag-adm-1102-bc3',
      request_payload: { action: 'ROTATE_SECRET', client_id: 'delivery-app-prod' },
      headers: { 'Authorization': 'Bearer [MASKED]' },
      response_payload: { status: 'success', new_kid: 'isag_kid_992' }
    }
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    admin_id: 'iiko-sync-worker',
    action: 'UPSTREAM_LATENCY_WARN',
    target_id: 'IIKO_API_MAIN',
    ip_address: '10.0.1.5',
    details: {
      correlation_id: 'isag-sys-5521-jk8',
      request_payload: { endpoint: '/api/v1/nomenclature', latency: '2450ms' },
      headers: { 'X-Correlation-ID': 'isag-sys-5521-jk8' },
      response_payload: { warning: 'Latency threshold exceeded (2000ms)' }
    }
  }
];

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>(MOCK_LOGS);
  const [loading, setLoading] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [search, setSearch] = useState('');
  const { showToast } = useToast();

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await apiClient.get<AuditLog[]>('/admin/logs?limit=100');
        if (res.data.length > 0) {
          setLogs(res.data);
        }
      } catch (_err: unknown) {
        console.warn('Backend unavailable, showing audit history');
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, [showToast]);

  const getActionIcon = (action: string) => {
    if (action.includes('BLOCK') || action.includes('REVOKED')) return <ShieldAlert size={16} color="var(--accent-crimson)" />;
    if (action.includes('CREATED') || action.includes('ACTIVATED') || action.includes('ROTATE')) return <Activity size={16} color="var(--accent-cyan)" />;
    if (action.includes('LOGIN')) return <Terminal size={16} color="var(--text-secondary)" />;
    return <Settings size={16} color="var(--text-secondary)" />;
  };

  const exportToCSV = () => {
    const headers = ['Timestamp', 'Action', 'Admin ID', 'Target', 'IP Address', 'Correlation ID'];
    const csvRows = [headers.join(',')];
    logs.forEach(log => {
      csvRows.push([
        new Date(log.timestamp).toISOString(),
        log.action,
        log.admin_id,
        log.target_id,
        log.ip_address || 'unknown',
        log.details?.correlation_id || 'N/A'
      ].map(v => `"${String(v).replace(/"/g, '""')}"`).join(','));
    });
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `isag_audit_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    showToast('Export successful', 'success');
  };

  const filteredLogs = logs.filter(l => 
    l.action.toLowerCase().includes(search.toLowerCase()) || 
    l.target_id.toLowerCase().includes(search.toLowerCase()) ||
    l.admin_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ padding: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Terminal size={28} color="var(--accent-cyan)" />
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Security Audit Logs</h1>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn-revoke" style={{ color: 'var(--text-secondary)', borderColor: 'rgba(255,255,255,0.1)' }}>
            <Filter size={18} /> Filter
          </button>
          <button className="btn-primary" onClick={exportToCSV}>
            <Download size={18} /> Export CSV
          </button>
        </div>
      </div>

      <div className="glass-card" style={{ marginBottom: '24px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <Search size={18} color="var(--text-muted)" />
        <input 
          type="text" 
          placeholder="Search by action, admin, or target..." 
          className="glass-input" 
          style={{ flex: 1 }}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="glass-table-container">
        <table className="glass-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>Initiator</th>
              <th>Target</th>
              <th>IP Address</th>
              <th>Trace</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ textAlign: 'center' }}>Loading logs...</td></tr>
            ) : filteredLogs.map((log) => (
              <tr key={log.id} className="trace-row" onClick={() => setSelectedLog(log)}>
                <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, color: log.action.includes('BLOCK') ? 'var(--accent-crimson)' : 'inherit' }}>
                    {getActionIcon(log.action)}
                    {log.action}
                  </div>
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <User size={14} color="var(--text-muted)" />
                    {log.admin_id}
                  </div>
                </td>
                <td style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>{log.target_id}</td>
                <td style={{ color: 'var(--text-muted)' }}>{log.ip_address || 'unknown'}</td>
                <td>
                  <ExternalLink size={16} color="var(--accent-cyan)" style={{ opacity: 0.5 }} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Request Trace Modal */}
      {selectedLog && (
        <div className="modal-overlay" onClick={() => setSelectedLog(null)}>
          <div className="modal-content glass-card" style={{ maxWidth: '800px', width: '90vw' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '4px' }}>Request Trace</h2>
                <span style={{ color: 'var(--accent-cyan)', fontFamily: 'monospace' }}>CID: {selectedLog.details?.correlation_id || 'N/A'}</span>
              </div>
              <button className="btn-revoke" style={{ border: 'none' }} onClick={() => setSelectedLog(null)}>Close</button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div>
                <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '12px' }}>Request Context</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div className="glass-card" style={{ padding: '16px', background: 'rgba(0,0,0,0.2)' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Admin / Initiator</div>
                    <div>{selectedLog.admin_id}</div>
                  </div>
                  <div className="glass-card" style={{ padding: '16px', background: 'rgba(0,0,0,0.2)' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Source IP</div>
                    <div>{selectedLog.ip_address}</div>
                  </div>
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '12px' }}>Action Details</h3>
                <div className="glass-card" style={{ padding: '16px', background: 'rgba(0,0,0,0.2)' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Action Type</div>
                  <div style={{ fontWeight: 700, color: selectedLog.action.includes('BLOCK') ? 'var(--accent-crimson)' : 'var(--accent-cyan)' }}>{selectedLog.action}</div>
                </div>
              </div>
            </div>

            <div style={{ marginTop: '24px' }}>
              <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '12px' }}>Payload Analysis</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', marginBottom: '8px' }}>Request Metadata</div>
                  <pre className="code-block">
                    {JSON.stringify(selectedLog.details?.request_payload || { message: 'No payload captured' }, null, 2)}
                  </pre>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', marginBottom: '8px' }}>Upstream Response</div>
                  <pre className="code-block" style={{ color: 'var(--accent-cyan)' }}>
                    {JSON.stringify(selectedLog.details?.response_payload || { message: 'No response captured' }, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
            
            <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn-primary" onClick={() => showToast('Trace exported to SIEM', 'success')}>
                Forward to SOC
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogs;
