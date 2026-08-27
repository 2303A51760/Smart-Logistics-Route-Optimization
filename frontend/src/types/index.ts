export type UserRole = 'ADMIN' | 'LOGISTICS_MANAGER' | 'DRIVER';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export type DriverStatus = 'AVAILABLE' | 'ASSIGNED' | 'IN_TRANSIT' | 'OFF_DUTY' | 'INACTIVE';

export interface Driver {
  id: string;
  user_id?: string | null;
  license_number: string;
  phone: string;
  status: DriverStatus;
  current_latitude?: number | null;
  current_longitude?: number | null;
  created_at: string;
  updated_at: string;
  user_name?: string | null;
  assigned_vehicle_number?: string | null;
}

export type VehicleStatus = 'AVAILABLE' | 'ASSIGNED' | 'IN_TRANSIT' | 'MAINTENANCE' | 'INACTIVE' | 'IDLE' | 'EN_ROUTE' | 'OFFLINE';

export interface Vehicle {
  id: string;
  vehicle_number: string;
  vehicle_type: string;
  capacity: number;
  fuel_type: string;
  mileage: number;
  status: VehicleStatus;
  driver_id?: string | null;
  created_at: string;
  updated_at: string;
  // Backwards compatibility aliases
  name?: string;
  license_plate?: string;
  capacity_kg?: number;
  current_lat?: number;
  current_lng?: number;
  fuel_level_percent?: number;
  is_active?: boolean;
  assigned_driver_name?: string | null;
}

export interface Warehouse {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  capacity: number;
  created_at: string;
  updated_at: string;
  active_orders_count?: number;
}

export interface Customer {
  id: string;
  name: string;
  phone: string;
  email: string;
  address: string;
  latitude: number;
  longitude: number;
  created_at: string;
  updated_at: string;
  total_orders_count?: number;
}

export type OrderStatus =
  | 'PENDING'
  | 'ASSIGNED'
  | 'OUT_FOR_DELIVERY'
  | 'ARRIVED'
  | 'DELIVERED'
  | 'FAILED'
  | 'CANCELLED'
  | 'RESCHEDULED';

export type OrderPriority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

export interface Order {
  id: string;
  order_number: string;
  customer_id: string;
  warehouse_id: string;
  pickup_latitude: number;
  pickup_longitude: number;
  delivery_latitude: number;
  delivery_longitude: number;
  package_weight: number;
  priority: OrderPriority;
  delivery_window_start?: string | null;
  delivery_window_end?: string | null;
  status: OrderStatus;
  assigned_driver_id?: string | null;
  created_at: string;
  updated_at: string;
  customer_name?: string;
  warehouse_name?: string;
  assigned_driver_name?: string | null;
}

export interface OrderListResponse {
  items: Order[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}

export interface DeliveryPoint {
  id: string;
  order_id: string;
  customer_name: string;
  address: string;
  lat: number;
  lng: number;
  demand_weight_kg: number;
  status: 'PENDING' | 'ASSIGNED' | 'IN_TRANSIT' | 'DELIVERED' | 'FAILED';
  priority: number;
  route_id?: string | null;
}

export interface Waypoint {
  stop_number: number;
  id?: string;
  name?: string;
  lat: number;
  lng: number;
  demand_kg?: number;
}

export interface Route {
  id: string;
  name: string;
  vehicle_id?: string;
  total_distance_km: number;
  estimated_duration_min: number;
  start_lat: number;
  start_lng: number;
  waypoints_json?: Waypoint[];
  is_optimized: boolean;
  status: string;
}

export interface ServiceStatus {
  status: 'healthy' | 'degraded' | 'unreachable';
  latency_ms?: number;
  details?: string;
}

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  services: {
    database: ServiceStatus;
    redis: ServiceStatus;
    websockets: ServiceStatus;
  };
  timestamp: string;
}

export interface OptimizationResult {
  job_id: string;
  status: string;
  num_vehicles: number;
  num_stops: number;
  total_distance_km: number;
  estimated_total_time_min: number;
  routes: Array<{
    vehicle_id: string;
    distance_km: number;
    estimated_time_min: number;
    stops: Waypoint[];
  }>;
}

export type MaintenanceType =
  | 'OIL_CHANGE'
  | 'TIRE_ROTATION'
  | 'BRAKE_INSPECTION'
  | 'ENGINE_SERVICE'
  | 'BATTERY_CHECK'
  | 'TRANSMISSION_SERVICE'
  | 'GENERAL_INSPECTION'
  | 'OTHER';

export type MaintenanceStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export interface VehicleMaintenance {
  id: string;
  vehicle_id: string;
  maintenance_type: MaintenanceType;
  maintenance_date: string;
  mileage: number;
  notes?: string | null;
  next_maintenance_mileage: number;
  cost: number;
  status: MaintenanceStatus;
  created_at: string;
  updated_at: string;
  vehicle_number?: string;
  vehicle_type?: string;
}

export interface MaintenanceVehicleDue {
  vehicle_id: string;
  vehicle_number: string;
  vehicle_type: string;
  current_mileage: number;
  last_maintenance_date?: string | null;
  last_maintenance_mileage?: number | null;
  next_maintenance_mileage: number;
  mileage_overdue: number;
  is_overdue: boolean;
  status: string;
  assigned_driver_id?: string | null;
  assigned_driver_name?: string | null;
}

export interface MaintenanceDashboardSummary {
  total_records: number;
  completed_services: number;
  scheduled_services: number;
  total_maintenance_cost: number;
  vehicles_overdue_count: number;
  vehicles_due_soon_count: number;
  fleet_health_score: number;
  by_type: Record<string, number>;
}

export type AlertType =
  | 'MAINTENANCE_DUE'
  | 'VEHICLE_OVERLOADED'
  | 'DRIVER_UNAVAILABLE'
  | 'DELIVERY_DELAYED'
  | 'ROUTE_EXCEEDS_MAX_DISTANCE'
  | 'URGENT_ORDER_UNASSIGNED'
  | 'SYSTEM_ALERT';

export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL' | 'ERROR';

export interface Notification {
  id: string;
  recipient_user_id?: string | null;
  recipient_role?: string | null;
  driver_id?: string | null;
  vehicle_id?: string | null;
  route_id?: string | null;
  order_id?: string | null;
  title: string;
  message: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  unread_count: number;
}

export interface NotificationSummary {
  total_notifications: number;
  unread_count: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
}

// Phase 12: Security & Enterprise Audit Logging
export interface AuditLog {
  id: string;
  user_id?: string | null;
  user_email?: string | null;
  user_role?: string | null;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
  timestamp: string;
  success: boolean;
  details?: string | null;
}

export interface AuditLogListResponse {
  total: number;
  page: number;
  limit: number;
  items: AuditLog[];
}

export interface AuditLogSummary {
  total_events: number;
  successful_events: number;
  failed_events: number;
  unauthorized_attempts: number;
  actions_by_role: Record<string, number>;
  top_actions: Array<{ action: string; count: number }>;
  recent_security_events: AuditLog[];
  generated_at: string;
}

export interface AuditLogFilterParams {
  user_id?: string;
  action?: string;
  resource_type?: string;
  success?: boolean;
  search?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  limit?: number;
}
