import React from 'react';
import { Activity, ShieldAlert, Terminal, Settings } from 'lucide-react';

interface AuditLog {
  id: string;
  timestamp: string;
  admin_id: string;
  action: string;
  target_id: string;
  ip_address: string;
}

interface LiveEventsProps {
  events: AuditLog[];
}

export const LiveEvents: React.FC<LiveEventsProps> = ({ events }) => {
  const getActionIcon = (action: string) => {
    if (action.includes('REVOKED')) return <ShieldAlert size={16} color="var(--accent-crimson)" />;
    if (action.includes('CREATED') || action.includes('ACTIVATED')) return <Activity size={16} color="var(--accent-cyan)" />;
    if (action.includes('LOGIN')) return <Terminal size={16} color="var(--text-secondary)" />;
    return <Settings size={16} color="var(--text-secondary)" />;
  };

  return (
    <div className="glass-card" style={{ height: '350px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Live Threat Feed
      </h3>
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {events && events.length > 0 ? (
          events.map((event) => {
            const isError = event.action.includes('REVOKED') || event.action.includes('RATE_LIMIT');
            return (
              <div 
                key={event.id} 
                className="live-event-enter"
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '12px',
                  background: 'rgba(0, 0, 0, 0.2)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  boxShadow: isError ? '0 0 12px rgba(255, 77, 77, 0.15)' : 'none'
                }}
              >
                <div style={{ marginTop: '2px' }}>
                  {getActionIcon(event.action)}
                </div>
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 500, color: isError ? 'var(--accent-crimson)' : 'var(--text-primary)' }}>
                    {event.action}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    Target: {event.target_id} | IP: {event.ip_address}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)', marginTop: '4px' }}>
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '24px' }}>
            No recent events
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveEvents;
