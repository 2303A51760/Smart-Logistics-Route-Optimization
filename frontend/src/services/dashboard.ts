import { api } from './api';
import {
  OrderMetrics,
  DriverMetrics,
  VehicleMetrics,
  DeliveryPerformanceMetrics,
  Driver,
  Order,
} from '../types';

export interface DashboardOverviewData {
  orders: OrderMetrics;
  drivers: DriverMetrics;
  vehicles: VehicleMetrics;
  delivery: DeliveryPerformanceMetrics;
  timestamp: string;
}

export interface OrderTrendData {
  date: string;
  total: number;
  completed: number;
  failed: number;
  pending: number;
}

export interface DriverPerformanceData {
  driver_id: string;
  driver_name: string;
  license_number: string;
  phone: string;
  assigned_deliveries: int;
  completed_deliveries: int;
  failed_deliveries: int;
  completion_rate: number;
  average_delivery_time_min: number;
  current_status: string;
  assigned_vehicle?: string | null;
  current_latitude?: number | null;
  current_longitude?: number | null;
}

export interface VehicleUtilizationData {
  items: Array<{
    vehicle_id: string;
    vehicle_number: string;
    vehicle_type: string;
    capacity: number;
    mileage: number;
    status: string;
    assigned_driver_name?: string | null;
    utilization_rate: number;
  }>;
  status_summary: Record<string, number>;
}

export interface DriverMeDashboardData {
  driver: Driver;
  stats: {
    today_deliveries: number;
    assigned_deliveries: number;
    completed_deliveries: number;
    pending_deliveries: number;
    failed_deliveries: number;
    completion_rate: number;
  };
  assigned_orders: Order[];
  next_delivery?: Order | null;
  current_route?: {
    stops_count: number;
    estimated_time_min: number;
    total_weight_kg: number;
  } | null;
}

export const dashboardApi = {
  async getOverview(): Promise<DashboardOverviewData> {
    const res = await api.get<DashboardOverviewData>('/dashboard/overview');
    return res.data;
  },

  async getOrderTrends(days: number = 7): Promise<OrderTrendData[]> {
    const res = await api.get<OrderTrendData[]>('/dashboard/orders', { params: { days } });
    return res.data;
  },

  async getDriverPerformance(): Promise<DriverPerformanceData[]> {
    const res = await api.get<DriverPerformanceData[]>('/dashboard/driver-performance');
    return res.data;
  },

  async getVehicleUtilization(): Promise<VehicleUtilizationData> {
    const res = await api.get<VehicleUtilizationData>('/dashboard/vehicle-utilization');
    return res.data;
  },

  async getDriverMeDashboard(): Promise<DriverMeDashboardData> {
    const res = await api.get<DriverMeDashboardData>('/dashboard/driver-me');
    return res.data;
  },
};
