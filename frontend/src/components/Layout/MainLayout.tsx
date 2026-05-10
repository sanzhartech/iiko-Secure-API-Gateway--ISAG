import React from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import '../../styles/theme.css';

import { Menu } from 'lucide-react';

import { apiClient } from '../../services/apiClient';

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('admin_access_token');
  const location = useLocation();

  React.useEffect(() => {
    if (token) {
      // Check token validity on mount
      apiClient.get('/auth/me').catch(() => {
        // Interceptor will handle 401 redirect
      });
    }
  }, [token]);

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export const MainLayout: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);

  return (
    <div className="app-layout">
      {/* Mobile Header */}
      <div className="mobile-header">
        <button className="hamburger-btn" onClick={() => setIsSidebarOpen(true)}>
          <Menu size={24} color="var(--text-primary)" />
        </button>
        <span style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>ISAG Admin</span>
      </div>

      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      
      {/* Overlay for mobile */}
      {isSidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setIsSidebarOpen(false)} />
      )}

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};
