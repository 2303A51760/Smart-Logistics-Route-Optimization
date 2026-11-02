import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { Login } from '../pages/Login';
import { authStorage, authApi } from '../services/auth';

describe('Login Flow & Authentication', () => {
  beforeEach(() => {
    authStorage.clearSession();
    vi.restoreAllMocks();
  });

  it('renders login form elements properly', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByPlaceholderText(/name@company.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('stores access and refresh tokens upon successful login', async () => {
    const mockAuthResponse = {
      access_token: 'fake-jwt-access-token-12345',
      refresh_token: 'fake-jwt-refresh-token-67890',
      token_type: 'bearer',
      user: {
        id: 'usr-mgr-002',
        name: 'Manager Bob',
        email: 'manager@example.com',
        role: 'LOGISTICS_MANAGER' as const,
        is_active: true,
        created_at: '2026-11-01T00:00:00Z',
      },
    };

    vi.spyOn(authApi, 'login').mockImplementation(async () => {
      authStorage.setSession(mockAuthResponse);
      return mockAuthResponse;
    });

    render(
      <BrowserRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </BrowserRouter>
    );

    fireEvent.change(screen.getByPlaceholderText(/name@company.com/i), {
      target: { value: 'manager@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText(/••••••••/i), {
      target: { value: 'Manager@123456' },
    });

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(authStorage.getAccessToken()).toBe('fake-jwt-access-token-12345');
      expect(authStorage.getRefreshToken()).toBe('fake-jwt-refresh-token-67890');
      expect(authStorage.getUser()?.email).toBe('manager@example.com');
    });
  });

  it('displays error feedback when login fails', async () => {
    vi.spyOn(authApi, 'login').mockRejectedValueOnce(new Error('Invalid email or password'));

    render(
      <BrowserRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </BrowserRouter>
    );

    fireEvent.change(screen.getByPlaceholderText(/name@company.com/i), {
      target: { value: 'wrong@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText(/••••••••/i), {
      target: { value: 'WrongPass' },
    });

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/Invalid email or password/i)).toBeInTheDocument();
    });
  });
});
