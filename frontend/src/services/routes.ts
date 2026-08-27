import api from './api';

export type RouteStatus = 'PLANNED' | 'STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type RouteStopStatus = 'PENDING' | 'ARRIVED' | 'IN_PROGRESS' | 'DELIVERED' | 'FAILED' | 'SKIPPED';

export interface RouteStop {
  id: string;
  route_id: string;
  order_id: string | null;
  sequence: number;
  estimated_arrival?: string | null;
  actual_arrival?: string | null;
  status: RouteStopStatus;
  created_at?: string;
  completed_at?: string | null;
  order_number?: string | null;
  customer_name?: string | null;
  delivery_address?: string | null;
  delivery_latitude?: number | null;
  delivery_longitude?: number | null;
  package_weight?: number | null;
  priority?: string | null;
}

export interface RouteItem {
  id: string;
  name?: string | null;
  driver_id?: string | null;
  driver_name?: string | null;
  vehicle_id?: string | null;
  vehicle_number?: string | null;
  warehouse_id?: string | null;
  warehouse_name?: string | null;
  total_distance: number;
  estimated_duration: number;
  optimization_score: number;
  status: RouteStatus;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  stops_count: number;
  completed_stops_count: number;
  stops: RouteStop[];
}

export interface RouteListResponse {
  total: number;
  items: RouteItem[];
}

export interface RouteStopListResponse {
  total: number;
  items: RouteStop[];
}

export interface DriverActionPayload {
  latitude?: number;
  longitude?: number;
  notes?: string;
  reason?: string;
}

export const routesApi = {
  listRoutes: async (params?: { status?: string; driver_id?: string; skip?: number; limit?: number }): Promise<RouteListResponse> => {
    const res = await api.get('/routes', { params });
    return res.data;
  },

  getRoute: async (routeId: string): Promise<RouteItem> => {
    const res = await api.get(`/routes/${routeId}`);
    return res.data;
  },

  getRouteStops: async (routeId: string): Promise<RouteStopListResponse> => {
    const res = await api.get(`/routes/${routeId}/stops`);
    return res.data;
  },

  startRoute: async (routeId: string, payload?: DriverActionPayload): Promise<RouteItem> => {
    const res = await api.post(`/routes/${routeId}/start`, payload);
    return res.data;
  },

  cancelRoute: async (routeId: string, payload?: DriverActionPayload): Promise<RouteItem> => {
    const res = await api.post(`/routes/${routeId}/cancel`, payload);
    return res.data;
  },

  arriveAtStop: async (routeId: string, stopId: string, payload?: DriverActionPayload): Promise<RouteItem> => {
    const res = await api.post(`/routes/${routeId}/stops/${stopId}/arrive`, payload);
    return res.data;
  },

  startDelivery: async (routeId: string, stopId: string, payload?: DriverActionPayload): Promise<RouteItem> => {
    const res = await api.post(`/routes/${routeId}/stops/${stopId}/start-delivery`, payload);
    return res.data;
  },

  deliverStop: async (routeId: string, stopId: string, payload?: DriverActionPayload): Promise<RouteItem> => {
    const res = await api.post(`/routes/${routeId}/stops/${stopId}/deliver`, payload);
    return res.data;
  },

  failStop: async (routeId: string, stopId: string, payload?: DriverActionPayload): Promise<RouteItem> => {
    const res = await api.post(`/routes/${routeId}/stops/${stopId}/fail`, payload);
    return res.data;
  },

  skipStop: async (routeId: string, stopId: string, payload?: DriverActionPayload): Promise<RouteItem> => {
    const res = await api.post(`/routes/${routeId}/stops/${stopId}/skip`, payload);
    return res.data;
  },

  completeRoute: async (routeId: string, payload?: DriverActionPayload): Promise<RouteItem> => {
    const res = await api.post(`/routes/${routeId}/complete`, payload);
    return res.data;
  },
};
