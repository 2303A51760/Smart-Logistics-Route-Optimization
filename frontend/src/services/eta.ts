import { api } from './api';

export interface ETAPredictRequest {
  distance_km: number;
  package_weight?: number;
  priority?: string;
  vehicle_type?: string;
  number_of_stops?: number;
  stop_sequence?: number;
  hour?: number;
  day_of_week?: number;
}

export interface ETAPredictResponse {
  predicted_duration_minutes: number;
  estimated_arrival: string;
  source: 'ML' | 'FALLBACK';
  model_version: string;
  confidence_interval_min?: number;
  confidence_interval_max?: number;
  reason?: string;
}

export interface RouteStopETA {
  stop_id: string;
  order_id?: string | null;
  order_number?: string | null;
  customer_name?: string | null;
  delivery_address?: string | null;
  sequence: number;
  distance_from_prev_km: number;
  predicted_duration_minutes: number;
  estimated_arrival: string;
  source: 'ML' | 'FALLBACK';
  status: string;
}

export interface RouteCumulativeETA {
  route_id: string;
  route_name?: string | null;
  total_distance_km: number;
  total_predicted_duration_minutes: number;
  route_estimated_completion: string;
  source: 'ML' | 'FALLBACK';
  model_version: string;
  stops: RouteStopETA[];
}

export interface MLAnalytics {
  model_version: string;
  selected_model: string;
  trained_at?: string | null;
  training_samples: number;
  features: string[];
  selected_metrics: {
    mae: number;
    rmse: number;
    r2: number;
  };
  models_evaluated?: Record<
    string,
    {
      mae: number;
      rmse: number;
      r2: number;
    }
  >;
  status?: string;
}

export const etaApi = {
  async predictETA(req: ETAPredictRequest): Promise<ETAPredictResponse> {
    const res = await api.post<ETAPredictResponse>('/eta/predict', req);
    return res.data;
  },

  async getOrderETA(orderId: string): Promise<ETAPredictResponse> {
    const res = await api.get<ETAPredictResponse>(`/eta/orders/${orderId}`);
    return res.data;
  },

  async getRouteETA(routeId: string): Promise<RouteCumulativeETA> {
    const res = await api.get<RouteCumulativeETA>(`/eta/routes/${routeId}`);
    return res.data;
  },

  async getMLAnalytics(): Promise<MLAnalytics> {
    const res = await api.get<MLAnalytics>('/eta/analytics');
    return res.data;
  },

  async retrainModel(): Promise<MLAnalytics> {
    const res = await api.post<MLAnalytics>('/eta/retrain');
    return res.data;
  },
};
