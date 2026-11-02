export interface OrderPriorityItem {
  order_id: string;
  order_number?: string;
  score: number;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  raw_priority?: string;
  factors: {
    base_priority_score: number;
    deadline_urgency_score: number;
    distance_score: number;
    distance_km: number;
    weight_load_score: number;
    status_backlog_score: number;
    deadline_factor_note?: string;
  };
  reasons: string[];
  recommendation: string;
  model_name: string;
  model_version: string;
}

export interface DispatchRecommendationItem {
  order_id: string;
  order_number?: string;
  driver_id: string;
  driver_name: string;
  driver_status?: string;
  vehicle_id: string;
  vehicle_name: string;
  vehicle_capacity_kg: number;
  score: number;
  reasons: string[];
  model_name: string;
  model_version: string;
}

export interface RouteReoptimizationOpportunity {
  route_id: string;
  reoptimization_required: boolean;
  reoptimization_beneficial: boolean;
  trigger_reason?: string;
  reasons: string[];
  original_distance_km: number;
  optimized_distance_km: number;
  estimated_distance_change_km: number;
  estimated_time_saved_minutes: number;
  estimated_fuel_saved_liters: number;
  estimated_cost_saved: number;
  new_proposed_route?: any;
  recommendation: string;
  model_name: string;
  model_version: string;
}

export interface DelayRiskItem {
  order_id: string;
  order_number?: string;
  delay_probability: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  predicted_delay_minutes: number;
  confidence?: number;
  factors: string[];
  recommendation: string;
}

export interface AIOperationsSummary {
  critical_orders_count: number;
  critical_orders: OrderPriorityItem[];
  high_delay_risk_count: number;
  high_delay_risk_orders: DelayRiskItem[];
  recommended_assignments_count: number;
  recommended_assignments: any[];
  routes_needing_reoptimization_count: number;
  route_reoptimization_opportunities: RouteReoptimizationOpportunity[];
  estimated_fleet_time_saved_minutes: number;
  estimated_fleet_distance_saved_km: number;
  estimated_fleet_fuel_saved_liters: number;
  estimated_fleet_cost_saved_usd: number;
  demand_forecast_glance: {
    horizon_days: number;
    total_predicted_orders: number;
    peak_day: string;
    trend: string;
  };
  system_status: string;
  timestamp: string;
}
