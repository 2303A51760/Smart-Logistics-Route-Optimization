import { api } from './api';

export interface ForecastItem {
  date: string;
  predicted_orders: number;
  lower_bound?: number | null;
  upper_bound?: number | null;
}

export interface DemandForecastResponse {
  forecast: ForecastItem[];
  model_version: string;
  selected_model?: string | null;
  source: 'ML' | 'FALLBACK';
  reason?: string | null;
  horizon_days: number;
  warehouse_id?: string | null;
}

export interface CapacityPlanningResponse {
  horizon_days: number;
  forecasted_total_demand: number;
  daily_average_demand: number;
  peak_daily_demand: number;
  available_capacity: number;
  capacity_utilization_percent: number;
  capacity_gap: number;
  status: 'UNDER_UTILIZED' | 'NORMAL' | 'HIGH_UTILIZATION' | 'OVER_CAPACITY';
  active_drivers: number;
  active_vehicles: number;
  required_drivers: number;
  required_vehicles: number;
  warehouse_capacity_kg?: number | null;
  assumptions: {
    average_orders_per_driver_per_day: number;
    average_package_weight_kg: number;
  };
}

export interface WarehouseComparisonItem {
  warehouse_id: string;
  warehouse_name: string;
  forecasted_demand: number;
  capacity: number;
  utilization_percent: number;
  status: string;
}

export interface WarehouseComparisonResponse {
  horizon_days: number;
  warehouses: WarehouseComparisonItem[];
}

export interface DemandAnalyticsResponse {
  model_version: string;
  selected_model: string;
  trained_at?: string | null;
  training_samples: number;
  features: string[];
  selected_metrics: {
    mae: number;
    rmse: number;
    mape: number;
  };
  models_evaluated?: Record<
    string,
    {
      mae: number;
      rmse: number;
      mape: number;
    }
  >;
  status?: string;
}

export const forecastApi = {
  async getDemandForecast(horizon: number = 7, warehouseId?: string): Promise<DemandForecastResponse> {
    const params = new URLSearchParams({ horizon: horizon.toString() });
    if (warehouseId) params.append('warehouse_id', warehouseId);
    const res = await api.get<DemandForecastResponse>(`/forecast/demand?${params.toString()}`);
    return res.data;
  },

  async getCapacityPlanning(horizon: number = 7, warehouseId?: string): Promise<CapacityPlanningResponse> {
    const params = new URLSearchParams({ horizon: horizon.toString() });
    if (warehouseId) params.append('warehouse_id', warehouseId);
    const res = await api.get<CapacityPlanningResponse>(`/forecast/capacity?${params.toString()}`);
    return res.data;
  },

  async getWarehouseComparison(horizon: number = 7): Promise<WarehouseComparisonResponse> {
    const res = await api.get<WarehouseComparisonResponse>(`/forecast/warehouses/comparison?horizon=${horizon}`);
    return res.data;
  },

  async getDemandAnalytics(): Promise<DemandAnalyticsResponse> {
    const res = await api.get<DemandAnalyticsResponse>('/forecast/analytics');
    return res.data;
  },

  async retrainDemandModel(): Promise<DemandAnalyticsResponse> {
    const res = await api.post<DemandAnalyticsResponse>('/forecast/demand/retrain');
    return res.data;
  },
};
