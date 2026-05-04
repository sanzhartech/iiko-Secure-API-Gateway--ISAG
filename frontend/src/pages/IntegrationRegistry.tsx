import React, { useState } from 'react';
import { Network, Plus, Search, ExternalLink, ShieldCheck, Globe, Trash2 } from 'lucide-react';
import { useToast } from '../components/Toast/ToastContext';
import '../styles/theme.css';

interface Integration {
  id: string;
  name: string;
  endpoints: number;
  auth_method: string;
  target_url: string;
  mapping: string;
  status: 'Active' | 'Offline';
}

const MOCK_INTEGRATIONS: Integration[] = [
  { id: '1', name: 'Doodoll Delivery API', endpoints: 12, auth_method: 'Bearer JWT', target_url: 'https://api.doodoll.io/v2', mapping: '/proxy/delivery', status: 'Active' },
  { id: '2', name: 'MyLoyaltyPartner', endpoints: 5, auth_method: 'API-Key', target_url: 'https://loyalty.ext.com/v1', mapping: '/proxy/loyalty', status: 'Active' },
  { id: '3', name: 'GlobalPayment Gateway', endpoints: 8, auth_method: 'mTLS + OAuth2', target_url: 'https://pay.global.net', mapping: '/proxy/payments', status: 'Offline' },
];

export const IntegrationRegistry: React.FC = () => {
  const [integrations] = useState<Integration[]>(MOCK_INTEGRATIONS);
  const [search, setSearch] = useState('');
  const { showToast } = useToast();

  return (
    <div style={{ padding: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Network size={28} color="var(--accent-cyan)" />
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Integration Registry</h1>
        </div>
        <button className="btn-primary" onClick={() => showToast('Registry is in Read-Only mode for this demo', 'info')}>
          <Plus size={18} /> Register Service
        </button>
      </div>

      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', maxWidth: '800px' }}>
        Manage external service connections. The Gateway acts as a secure bridge, handling authentication, 
        rate limiting, and protocol translation between external APIs and internal iiko systems.
      </p>

      <div className="glass-card" style={{ marginBottom: '24px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <Search size={18} color="var(--text-muted)" />
        <input 
          type="text" 
          placeholder="Search by service name or endpoint..." 
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
              <th>Service Name</th>
              <th>Endpoints</th>
              <th>Auth Method</th>
              <th>Mapping Path</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {integrations.filter(i => i.name.toLowerCase().includes(search.toLowerCase())).map((item) => (
              <tr key={item.id}>
                <td>
                  <div style={{ fontWeight: 600 }}>{item.name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Globe size={10} /> {item.target_url}
                  </div>
                </td>
                <td>
                  <span style={{ background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '4px' }}>
                    {item.endpoints}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-mint)', fontSize: '0.85rem' }}>
                    <ShieldCheck size={14} />
                    {item.auth_method}
                  </div>
                </td>
                <td>
                  <code style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>{item.mapping}</code>
                </td>
                <td>
                  <span className={`badge ${item.status === 'Active' ? 'active' : 'revoked'}`}>
                    {item.status}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="btn-primary" style={{ padding: '6px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)' }} title="Edit Mapping">
                      <ExternalLink size={14} />
                    </button>
                    <button className="btn-revoke" style={{ padding: '6px' }} title="Delete Integration">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default IntegrationRegistry;
