import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  ShieldAlert, 
  LogOut, 
  Shield, 
  Network, 
  Lock, 
  Bell 
} from 'lucide-react';
import { useToast } from '../Toast/ToastContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const handleLogout = () => {
    localStorage.removeItem('admin_access_token');
    showToast('Logged out successfully', 'success');
    navigate('/login');
  };

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <Shield size={24} color="var(--accent-cyan)" />
        <span>ISAG Admin</span>
      </div>

      <nav className="sidebar-nav">
        <NavLink 
          to="/dashboard" 
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          onClick={() => onClose()}
        >
          <LayoutDashboard size={18} />
          Dashboard
        </NavLink>
        <NavLink 
          to="/clients" 
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          onClick={() => onClose()}
        >
          <Users size={18} />
          Clients
        </NavLink>
        <NavLink 
          to="/integrations" 
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          onClick={() => onClose()}
        >
          <Network size={18} />
          Integrations
        </NavLink>
        <NavLink 
          to="/security-rules" 
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          onClick={() => onClose()}
        >
          <Lock size={18} />
          Security Rules
        </NavLink>
        <NavLink 
          to="/logs" 
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          onClick={() => onClose()}
        >
          <ShieldAlert size={18} />
          Audit Logs
        </NavLink>
        <NavLink 
          to="/alerting" 
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          onClick={() => onClose()}
        >
          <Bell size={18} />
          Alerting
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <button onClick={handleLogout} className="logout-btn">
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </aside>
  );
};
