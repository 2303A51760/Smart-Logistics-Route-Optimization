import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { authStorage, authApi } from '../services/auth';

describe('ProtectedRoute Role Gating', () => {
  beforeEach(() => {
    authStorage.clearSession();
    vi.restoreAllMocks();
  });

  it('redirects unauthenticated user to /login', async () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<div>Login Page Screen</div>} />
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={['ADMIN']}>
                  <div>Admin Secret Dashboard</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Login Page Screen')).toBeInTheDocument();
    expect(screen.queryByText('Admin Secret Dashboard')).not.toBeInTheDocument();
  });

  it('allows access when user role matches allowedRoles', async () => {
    const adminUser = {
      id: 'usr-admin-001',
      name: 'System Admin',
      email: 'admin@example.com',
      role: 'ADMIN' as const,
      is_active: true,
      created_at: '2026-11-01T00:00:00Z',
    };

    authStorage.setSession({
      access_token: 'valid-token',
      refresh_token: 'valid-refresh',
      token_type: 'bearer',
      user: adminUser,
    });
    vi.spyOn(authApi, 'getMe').mockResolvedValue(adminUser);

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<div>Login Page Screen</div>} />
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={['ADMIN']}>
                  <div>Admin Secret Dashboard</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Admin Secret Dashboard')).toBeInTheDocument();
  });

  it('redirects to /unauthorized when user lacks required role', async () => {
    // Driver trying to access manager/admin area
    const driverUser = {
      id: 'usr-drv-003',
      name: 'Alex Driver',
      email: 'driver@example.com',
      role: 'DRIVER' as const,
      is_active: true,
      created_at: '2026-11-01T00:00:00Z',
    };

    authStorage.setSession({
      access_token: 'driver-token',
      refresh_token: 'driver-refresh',
      token_type: 'bearer',
      user: driverUser,
    });
    vi.spyOn(authApi, 'getMe').mockResolvedValue(driverUser);

    render(
      <MemoryRouter initialEntries={['/manager-zone']}>
        <AuthProvider>
          <Routes>
            <Route path="/unauthorized" element={<div>Access Denied Page</div>} />
            <Route
              path="/manager-zone"
              element={
                <ProtectedRoute allowedRoles={['LOGISTICS_MANAGER', 'ADMIN']}>
                  <div>Manager Restricted Area</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Access Denied Page')).toBeInTheDocument();
    expect(screen.queryByText('Manager Restricted Area')).not.toBeInTheDocument();
  });
});
