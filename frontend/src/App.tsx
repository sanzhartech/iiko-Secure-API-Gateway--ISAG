import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './components/Toast/ToastContext';
import { MainLayout, ProtectedRoute } from './components/Layout/MainLayout';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ClientsPage from './pages/ClientsPage';
import AuditLogs from './pages/AuditLogs';
import IntegrationRegistry from './pages/IntegrationRegistry';
import SecurityRules from './pages/SecurityRules';
import Alerting from './pages/Alerting';

const App: React.FC = () => {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected Routes */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="clients" element={<ClientsPage />} />
            <Route path="integrations" element={<IntegrationRegistry />} />
            <Route path="security-rules" element={<SecurityRules />} />
            <Route path="logs" element={<AuditLogs />} />
            <Route path="alerting" element={<Alerting />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
};

export default App;
