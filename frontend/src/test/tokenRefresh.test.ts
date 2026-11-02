import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api, refreshAuthToken } from '../services/api';
import { authStorage } from '../services/auth';

describe('API Service Token Refresh on 401', () => {
  beforeEach(() => {
    localStorage.clear();
    authStorage.setSession({
      access_token: 'expired-access-token',
      refresh_token: 'valid-refresh-token',
      token_type: 'bearer',
      user: {
        id: 'usr-1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'LOGISTICS_MANAGER',
        is_active: true,
        created_at: '2026-11-01T00:00:00Z',
      },
    });
    vi.restoreAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('transparently refreshes access token and retries request on 401', async () => {
    let callCount = 0;

    // Mock fetch for initial 401 -> refresh endpoint 200 -> retry 200
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url: string) => {
      if (url.includes('/auth/refresh')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            access_token: 'fresh-new-access-token-999',
            refresh_token: 'fresh-new-refresh-token-888',
          }),
        };
      }

      if (url.includes('/vehicles')) {
        callCount++;
        if (callCount === 1) {
          // First call returns 401 Unauthorized
          return {
            ok: false,
            status: 401,
            statusText: 'Unauthorized',
            json: async () => ({ detail: 'Token has expired' }),
          };
        } else {
          // Retry call with refreshed token returns 200 OK
          return {
            ok: true,
            status: 200,
            json: async () => ([{ id: 'veh-001', plate_number: 'VAN-101' }]),
          };
        }
      }

      return { ok: true, status: 200, json: async () => ({}) };
    }));

    const result = await api.get('/vehicles');

    expect(result.status).toBe(200);
    expect(result.data).toEqual([{ id: 'veh-001', plate_number: 'VAN-101' }]);
    expect(localStorage.getItem('access_token')).toBe('fresh-new-access-token-999');
    expect(callCount).toBe(2);
  });

  it('clears session when token refresh endpoint fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url: string) => {
      if (url.includes('/auth/refresh')) {
        return {
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
          json: async () => ({ detail: 'Refresh token invalid' }),
        };
      }

      return {
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ detail: 'Token expired' }),
      };
    }));

    const token = await refreshAuthToken();

    expect(token).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });
});
