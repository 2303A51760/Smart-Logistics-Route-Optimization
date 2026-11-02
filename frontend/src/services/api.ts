import { Vehicle, Route, DeliveryPoint, SystemHealth, OptimizationResult } from '../types';
import { authStorage } from './auth';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface ApiResponse<T = any> {
  data: T;
  status: number;
}

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

export async function refreshAuthToken(): Promise<string | null> {
  const refreshToken = authStorage.getRefreshToken();
  if (!refreshToken) return null;

  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.access_token) {
          localStorage.setItem('access_token', data.access_token);
          if (data.refresh_token) {
            localStorage.setItem('refresh_token', data.refresh_token);
          }
          return data.access_token;
        }
      }
    } catch (e) {
      console.warn('Token refresh error:', e);
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }

    authStorage.clearSession();
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    return null;
  })();

  return refreshPromise;
}

async function request<T>(
  endpoint: string,
  options?: RequestInit & { params?: Record<string, any> }
): Promise<ApiResponse<T>> {
  let token = authStorage.getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options?.headers as Record<string, string>),
  };

  let url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  if (options?.params) {
    const searchParams = new URLSearchParams();
    Object.entries(options.params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        searchParams.append(key, String(val));
      }
    });
    const qs = searchParams.toString();
    if (qs) {
      url += `${url.includes('?') ? '&' : '?'}${qs}`;
    }
  }

  let res = await fetch(url, {
    ...options,
    headers,
  });

  // Handle 401 Unauthorized: attempt token refresh then retry
  if (res.status === 401 && !url.includes('/auth/login') && !url.includes('/auth/refresh') && !url.includes('/auth/register')) {
    const newToken = await refreshAuthToken();
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`;
      res = await fetch(url, {
        ...options,
        headers,
      });
    }
  }

  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      // ignore json parse error
    }
    const err = new Error(errorDetail) as any;
    err.response = { data: { detail: errorDetail }, status: res.status };
    throw err;
  }

  const data = await res.json().catch(() => ({}));
  return { data, status: res.status };
}

export const api = {
  get: <T = any>(url: string, config?: { params?: Record<string, any>; headers?: Record<string, string> }): Promise<ApiResponse<T>> =>
    request<T>(url, { method: 'GET', ...config }),

  post: <T = any>(url: string, data?: any, config?: { params?: Record<string, any>; headers?: Record<string, string> }): Promise<ApiResponse<T>> =>
    request<T>(url, {
      method: 'POST',
      body: data !== undefined ? JSON.stringify(data) : undefined,
      ...config,
    }),

  put: <T = any>(url: string, data?: any, config?: { params?: Record<string, any>; headers?: Record<string, string> }): Promise<ApiResponse<T>> =>
    request<T>(url, {
      method: 'PUT',
      body: data !== undefined ? JSON.stringify(data) : undefined,
      ...config,
    }),

  patch: <T = any>(url: string, data?: any, config?: { params?: Record<string, any>; headers?: Record<string, string> }): Promise<ApiResponse<T>> =>
    request<T>(url, {
      method: 'PATCH',
      body: data !== undefined ? JSON.stringify(data) : undefined,
      ...config,
    }),

  delete: <T = any>(url: string, config?: { params?: Record<string, any>; headers?: Record<string, string> }): Promise<ApiResponse<T>> =>
    request<T>(url, { method: 'DELETE', ...config }),

  // System Health
  getHealth: async (): Promise<SystemHealth> => {
    const res = await api.get<SystemHealth>('/health');
    return res.data;
  },

  // Vehicles
  getVehicles: async (): Promise<Vehicle[]> => {
    const res = await api.get<Vehicle[]>('/vehicles');
    return res.data;
  },
  getVehicle: async (id: string): Promise<Vehicle> => {
    const res = await api.get<Vehicle>(`/vehicles/${id}`);
    return res.data;
  },

  // Routes & Deliveries
  getRoutes: async (): Promise<Route[]> => {
    const res = await api.get<Route[]>('/routes');
    return res.data;
  },
  getDeliveries: async (): Promise<DeliveryPoint[]> => {
    const res = await api.get<DeliveryPoint[]>('/routes/deliveries');
    return res.data;
  },

  // Optimization
  solveOptimization: async (payload: {
    vehicle_ids: string[];
    delivery_ids: string[];
    depot_lat?: number;
    depot_lng?: number;
  }): Promise<OptimizationResult> => {
    const res = await api.post<OptimizationResult>('/optimization/solve', payload);
    return res.data;
  },
};

export default api;
