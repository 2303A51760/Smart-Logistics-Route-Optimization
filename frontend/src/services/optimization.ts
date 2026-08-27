import api from './api';

export interface RouteStopItem {
  sequence: number;
  stop_type: 'DEPOT' | 'DELIVERY';
  order_id: string | null;
  name: string;
  latitude: number;
  longitude: number;
  demand_kg: number;
  priority: string;
  estimated_arrival_minutes: number;
}

export interface VehicleRouteItem {
  vehicle_id: string;
  vehicle_name?: string;
  driver_id?: string | null;
  driver_name?: string | null;
  total_distance_km: number;
  estimated_duration_min: number;
  capacity_kg: number;
  total_load_kg: number;
  stops_count: number;
  stops: RouteStopItem[];
}

export interface UnassignedOrderItem {
  order_id: string;
  name: string;
  latitude: number;
  longitude: number;
  demand_kg: number;
  priority: string;
  reason: string;
}

export interface OptimizationResultResponse {
  job_id: string;
  status: string;
  solver?: string;
  total_distance_km: number;
  total_duration_min: number;
  vehicles_used: number;
  orders_assigned: number;
  orders_unassigned: number;
  optimization_score: number;
  routes: VehicleRouteItem[];
  unassigned_orders: UnassignedOrderItem[];
}

export interface OptimizeRequest {
  warehouse_id: string;
  order_ids: string[];
  driver_ids?: string[];
  vehicle_ids?: string[];
  max_route_distance_km?: number;
  average_speed_kmh?: number;
  time_limit_seconds?: number;
}

export interface OptimizationJobResponse {
  id: string;
  status: string;
  optimization_score: number;
  total_distance_km: number;
  total_duration_min: number;
  created_at: string;
  updated_at: string;
  result?: OptimizationResultResponse;
}

export const optimizationApi = {
  optimize: async (req: OptimizeRequest): Promise<OptimizationResultResponse> => {
    const res = await api.post('/optimization/optimize', req);
    return res.data;
  },

  getJob: async (jobId: string): Promise<OptimizationJobResponse> => {
    const res = await api.get(`/optimization/jobs/${jobId}`);
    return res.data;
  },

  createRoutes: async (jobId: string, selectedVehicleIds?: string[]): Promise<{ message: string; route_ids: string[] }> => {
    const res = await api.post(`/optimization/jobs/${jobId}/create-routes`, {
      job_id: jobId,
      selected_vehicle_ids: selectedVehicleIds,
    });
    return res.data;
  },
};
