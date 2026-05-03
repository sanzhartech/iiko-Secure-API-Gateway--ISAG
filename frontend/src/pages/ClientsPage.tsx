import React, { useEffect, useState } from 'react';
import { Shield, ShieldAlert, Plus, Search, Check, Copy } from 'lucide-react';
import { apiClient } from '../services/apiClient';
import { useToast } from '../components/Toast/ToastContext';
import '../styles/theme.css';

interface Client {
  id: string;
  client_id: string;
  roles: string[];
  scopes: string[];
  rate_limit: number;
  is_active: boolean;
}

export const ClientsPage: React.FC = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newClientSecret, setNewClientSecret] = useState<{ id: string; secret: string } | null>(null);

  const [confirmRevoke, setConfirmRevoke] = useState<{ id: string; currentStatus: boolean } | null>(null);
  const [confirmRotate, setConfirmRotate] = useState<string | null>(null);

  const fetchClients = async () => {
    try {
      const res = await apiClient.get<Client[]>('/admin/clients');
      setClients(res.data);
    } catch (_err: unknown) {
      showToast('Failed to load clients', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const handleToggleStatus = async (id: string, currentStatus: boolean) => {
    try {
      await apiClient.patch(`/admin/clients/${id}/status`, { is_active: !currentStatus });
      showToast(`Client ${!currentStatus ? 'activated' : 'revoked'} successfully`, 'success');
      setConfirmRevoke(null);
      fetchClients();
    } catch (_err: unknown) {
      showToast('Failed to update client status', 'error');
    }
  };

  const handleCreateClient = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const clientId = formData.get('clientId') as string;
    const roles = (formData.get('roles') as string).split(',').map((r) => r.trim()).filter(Boolean);
    const scopes = (formData.get('scopes') as string).split(',').map((s) => s.trim()).filter(Boolean);
    const rate_limit = parseInt(formData.get('rateLimit') as string) || 10;

    try {
      const res = await apiClient.post('/admin/clients', { 
        client_id: clientId, 
        roles,
        scopes,
        rate_limit
      });
      setNewClientSecret({ id: res.data.client_id, secret: res.data.client_secret });
      setShowCreateModal(false);
      fetchClients();
      showToast('Client created successfully', 'success');
    } catch (_err: unknown) {
      showToast('Failed to create client. ID might exist.', 'error');
    }
  };

  const handleRotateSecret = async (id: string) => {
    try {
      const res = await apiClient.post(`/admin/clients/${id}/rotate-secret`);
      setNewClientSecret({ id: res.data.client_id, secret: res.data.client_secret });
      setConfirmRotate(null);
      showToast('Client secret rotated successfully', 'success');
    } catch (_err: unknown) {
      showToast('Failed to rotate client secret', 'error');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    showToast('Copied to clipboard', 'success');
  };

  const filteredClients = clients.filter(c => c.client_id.toLowerCase().includes(search.toLowerCase()));

  return (
    <div style={{ padding: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Shield size={28} color="var(--accent-cyan)" />
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Gateway Clients</h1>
        </div>
        <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
          <Plus size={18} /> New Client
        </button>
      </div>

      <div className="glass-card" style={{ marginBottom: '24px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <Search size={18} color="var(--text-secondary)" />
        <input 
          type="text" 
          placeholder="Search by Client ID..." 
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
              <th>Client ID</th>
              <th>Roles</th>
              <th>Scopes</th>
              <th>Rate Limit</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ textAlign: 'center' }}>Loading...</td></tr>
            ) : filteredClients.map((client) => (
              <tr key={client.id}>
                <td style={{ fontWeight: 500, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {client.client_id}
                  <button 
                    onClick={() => copyToClipboard(client.client_id)} 
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}
                    title="Copy ID"
                  >
                    <Copy size={14} />
                  </button>
                </td>
                <td>{client.roles.join(', ')}</td>
                <td>{client.scopes.length > 0 ? client.scopes.join(', ') : 'none'}</td>
                <td>{client.rate_limit} / min</td>
                <td>
                  {client.is_active ? (
                    <span className="badge active"><Check size={12} /> Active</span>
                  ) : (
                    <span className="badge revoked"><ShieldAlert size={12} /> Revoked</span>
                  )}
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button 
                      className="btn-revoke" 
                      style={{ borderColor: client.is_active ? 'var(--accent-crimson)' : 'var(--accent-cyan)', color: client.is_active ? 'var(--accent-crimson)' : 'var(--accent-cyan)' }}
                      onClick={() => setConfirmRevoke({ id: client.id, currentStatus: client.is_active })}
                    >
                      {client.is_active ? 'Revoke' : 'Activate'}
                    </button>
                    <button 
                      className="btn-revoke"
                      style={{ borderColor: 'var(--text-secondary)', color: 'var(--text-secondary)' }}
                      onClick={() => setConfirmRotate(client.id)}
                      title="Rotate Secret"
                    >
                      Rotate
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Client Modal */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card">
            <h2 style={{ marginBottom: '16px' }}>Create New Client</h2>
            <form onSubmit={handleCreateClient} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <input name="clientId" className="glass-input" placeholder="Client ID (e.g., pos-terminal-1)" required />
              <input name="roles" className="glass-input" placeholder="Roles (comma separated, e.g., operator, proxy:read)" />
              <input name="scopes" className="glass-input" placeholder="Scopes (comma separated, e.g., orders:write, menu:read)" />
              <input name="rateLimit" type="number" className="glass-input" placeholder="Rate Limit (req/min)" defaultValue={10} min={1} required />
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
                <button type="button" className="btn-revoke" style={{ color: 'var(--text-primary)', borderColor: 'var(--text-secondary)' }} onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* One-Time Secret Modal */}
      {newClientSecret && (
        <div className="modal-overlay">
          <div className="modal-content glass-card" style={{ borderColor: 'var(--accent-cyan)' }}>
            <h2 style={{ marginBottom: '16px', color: 'var(--accent-cyan)' }}>Client Created Successfully!</h2>
            <p style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>
              Please copy the Client Secret now. You will <strong>not</strong> be able to see it again.
            </p>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
              <code style={{ flex: 1, padding: '12px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', wordBreak: 'break-all' }}>
                {newClientSecret.secret}
              </code>
              <button className="btn-primary" onClick={() => copyToClipboard(newClientSecret.secret)}>
                <Copy size={18} />
              </button>
            </div>
            <button className="btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setNewClientSecret(null)}>
              I have copied the secret
            </button>
          </div>
        </div>
      )}

      {/* Confirmation Guard Modal */}
      {confirmRevoke && (
        <div className="modal-overlay">
          <div className="modal-content glass-card" style={{ borderColor: confirmRevoke.currentStatus ? 'var(--accent-crimson)' : 'var(--accent-cyan)' }}>
            <h2 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldAlert size={24} color={confirmRevoke.currentStatus ? 'var(--accent-crimson)' : 'var(--accent-cyan)'} />
              Confirm Action
            </h2>
            <p style={{ marginBottom: '24px' }}>
              Are you sure you want to <strong>{confirmRevoke.currentStatus ? 'revoke' : 'activate'}</strong> this client?
              {confirmRevoke.currentStatus && ' They will immediately lose access to the Gateway.'}
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button className="btn-revoke" style={{ color: 'var(--text-primary)', borderColor: 'var(--text-secondary)' }} onClick={() => setConfirmRevoke(null)}>Cancel</button>
              <button 
                className="btn-primary" 
                style={{ background: confirmRevoke.currentStatus ? 'var(--accent-crimson)' : 'var(--accent-cyan)' }}
                onClick={() => handleToggleStatus(confirmRevoke.id, confirmRevoke.currentStatus)}
              >
                Yes, {confirmRevoke.currentStatus ? 'Revoke' : 'Activate'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Rotate Modal */}
      {confirmRotate && (
        <div className="modal-overlay">
          <div className="modal-content glass-card" style={{ borderColor: 'var(--accent-cyan)' }}>
            <h2 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldAlert size={24} color="var(--accent-cyan)" />
              Confirm Secret Rotation
            </h2>
            <p style={{ marginBottom: '24px' }}>
              Are you sure you want to rotate the secret for this client? 
              <strong> The current secret will immediately become invalid.</strong>
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button className="btn-revoke" style={{ color: 'var(--text-primary)', borderColor: 'var(--text-secondary)' }} onClick={() => setConfirmRotate(null)}>Cancel</button>
              <button 
                className="btn-primary" 
                onClick={() => handleRotateSecret(confirmRotate)}
              >
                Yes, Rotate Secret
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientsPage;
