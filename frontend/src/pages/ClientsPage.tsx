import React, { useEffect, useState } from 'react';
import { Shield, ShieldAlert, Plus, Search, Check, Copy, RefreshCw, Slash, Settings2 } from 'lucide-react';
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
  const [editingRateLimit, setEditingRateLimit] = useState<Client | null>(null);

  const fetchClients = async () => {
    try {
      const res = await apiClient.get<Client[]>('/admin/clients');
      setClients(res.data);
    } catch (_err: unknown) {
      showToast('Unable to load clients', 'error');
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
      showToast('Unable to update client status', 'error');
    }
  };

  const handleUpdateRateLimit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRateLimit) return;
    try {
      await apiClient.patch(`/admin/clients/${editingRateLimit.id}`, { rate_limit: editingRateLimit.rate_limit });
      showToast('Rate limit updated', 'success');
      setEditingRateLimit(null);
      fetchClients();
    } catch (_err: unknown) {
      showToast('Unable to update rate limit', 'error');
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
      showToast('Unable to create client', 'error');
    }
  };

  const handleRotateSecret = async (id: string) => {
    try {
      const res = await apiClient.post(`/admin/clients/${id}/rotate-secret`);
      setNewClientSecret({ id: res.data.client_id, secret: res.data.client_secret });
      setConfirmRotate(null);
      showToast('Client secret rotated successfully', 'success');
    } catch (_err: unknown) {
      showToast('Unable to rotate secret', 'error');
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
          placeholder="Search by Client ID or Role..." 
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
                <td style={{ fontWeight: 600 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {client.client_id}
                    <button onClick={() => copyToClipboard(client.client_id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                      <Copy size={12} />
                    </button>
                  </div>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                    {client.roles.map(role => (
                      <span key={role} style={{ fontSize: '0.7rem', padding: '2px 6px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', color: 'var(--accent-cyan)' }}>
                        {role}
                      </span>
                    ))}
                  </div>
                </td>
                <td>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {client.scopes.length > 0 ? client.scopes.join(', ') : 'none'}
                  </span>
                </td>
                <td>
                  <button 
                    onClick={() => setEditingRateLimit(client)}
                    style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                    className="hover-cyan"
                  >
                    {client.rate_limit} / min
                    <Settings2 size={12} color="var(--text-muted)" />
                  </button>
                </td>
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
                      className="btn-primary" 
                      style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)', border: '1px solid rgba(255,255,255,0.1)' }}
                      onClick={() => setConfirmRotate(client.id)}
                      title="Rotate Secret"
                    >
                      <RefreshCw size={14} />
                    </button>
                    <button 
                      className="btn-revoke" 
                      style={{ padding: '6px 12px', borderColor: client.is_active ? 'var(--accent-crimson)' : 'var(--accent-mint)', color: client.is_active ? 'var(--accent-crimson)' : 'var(--accent-mint)' }}
                      onClick={() => setConfirmRevoke({ id: client.id, currentStatus: client.is_active })}
                    >
                      {client.is_active ? <Slash size={14} /> : <Check size={14} />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Rate Limit Edit Modal */}
      {editingRateLimit && (
        <div className="modal-overlay">
          <div className="modal-content glass-card" style={{ maxWidth: '400px' }}>
            <h2 style={{ marginBottom: '16px' }}>Adjust Rate Limit</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>Set request quota for <strong>{editingRateLimit.client_id}</strong></p>
            <form onSubmit={handleUpdateRateLimit}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                <input 
                  type="number" 
                  className="glass-input" 
                  style={{ flex: 1, fontSize: '1.2rem' }}
                  value={editingRateLimit.rate_limit}
                  onChange={(e) => setEditingRateLimit({...editingRateLimit, rate_limit: parseInt(e.target.value)})}
                />
                <span style={{ color: 'var(--text-secondary)' }}>req / min</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button type="button" className="btn-revoke" style={{ color: 'var(--text-primary)', borderColor: 'var(--text-muted)' }} onClick={() => setEditingRateLimit(null)}>Cancel</button>
                <button type="submit" className="btn-primary">Apply Limit</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Client Modal */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card">
            <h2 style={{ marginBottom: '16px' }}>Create New Client</h2>
            <form onSubmit={handleCreateClient} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <input name="clientId" className="glass-input" placeholder="Client ID (e.g., pos-terminal-1)" required />
              <input name="roles" className="glass-input" placeholder="Roles (e.g., delivery_app, operator)" />
              <input name="scopes" className="glass-input" placeholder="Scopes (e.g., orders:write, menu:read)" />
              <input name="rateLimit" type="number" className="glass-input" placeholder="Rate Limit (req/min)" defaultValue={10} min={1} required />
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
                <button type="button" className="btn-revoke" style={{ color: 'var(--text-primary)', borderColor: 'var(--text-muted)' }} onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Create Client</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* One-Time Secret Modal */}
      {newClientSecret && (
        <div className="modal-overlay">
          <div className="modal-content glass-card" style={{ borderColor: 'var(--accent-cyan)' }}>
            <h2 style={{ marginBottom: '16px', color: 'var(--accent-cyan)' }}>Client Secret Generated</h2>
            <p style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>
              Copy the secret now. For security reasons, it will <strong>never</strong> be shown again.
            </p>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
              <code style={{ flex: 1, padding: '12px', background: '#000', borderRadius: '8px', wordBreak: 'break-all', color: 'var(--accent-mint)' }}>
                {newClientSecret.secret}
              </code>
              <button className="btn-primary" onClick={() => copyToClipboard(newClientSecret.secret)}>
                <Copy size={18} />
              </button>
            </div>
            <button className="btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setNewClientSecret(null)}>
              I have securely stored the secret
            </button>
          </div>
        </div>
      )}

      {/* Confirmation Guard Modal */}
      {confirmRevoke && (
        <div className="modal-overlay">
          <div className="modal-content glass-card" style={{ borderColor: confirmRevoke.currentStatus ? 'var(--accent-crimson)' : 'var(--accent-mint)' }}>
            <h2 style={{ marginBottom: '16px' }}>Confirm Action</h2>
            <p style={{ marginBottom: '24px' }}>
              Are you sure you want to <strong>{confirmRevoke.currentStatus ? 'revoke access' : 'restore access'}</strong> for this client?
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button className="btn-revoke" style={{ color: 'var(--text-primary)', borderColor: 'var(--text-muted)' }} onClick={() => setConfirmRevoke(null)}>Cancel</button>
              <button 
                className="btn-primary" 
                style={{ background: confirmRevoke.currentStatus ? 'var(--accent-crimson)' : 'var(--accent-mint)', color: confirmRevoke.currentStatus ? '#fff' : '#000' }}
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
            <h2 style={{ marginBottom: '16px' }}>Rotate Client Secret?</h2>
            <p style={{ marginBottom: '24px' }}>
              Rotating the secret will immediately invalidate the current one. <strong>Any services using the old secret will fail.</strong>
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button className="btn-revoke" style={{ color: 'var(--text-primary)', borderColor: 'var(--text-muted)' }} onClick={() => setConfirmRotate(null)}>Cancel</button>
              <button className="btn-primary" onClick={() => handleRotateSecret(confirmRotate)}>Yes, Rotate Secret</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientsPage;
