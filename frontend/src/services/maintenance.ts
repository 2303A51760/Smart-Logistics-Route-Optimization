import { api } from './api';
import {
  VehicleMaintenance,
  MaintenanceVehicleDue,
  MaintenanceDashboardSummary,
} from '../types';

export const maintenanceApi = {
  async listMaintenance(params?: {
    vehicle_id?: string;
    maintenance_type?: string;
    status?: string;
  }): Promise<VehicleMaintenance[]> {
    const res = await api.get<VehicleMaintenance[]>('/maintenance', { params });
    return res.data;
  },

  async getMaintenance(id: string): Promise<VehicleMaintenance> {
    const res = await api.get<VehicleMaintenance>(`/maintenance/${id}`);
    return res.data;
  },

  async createMaintenance(data: {
    vehicle_id: string;
    maintenance_type: string;
    maintenance_date?: string;
    mileage: number;
    notes?: string;
    next_maintenance_mileage: number;
    cost: number;
    status?: string;
  }): Promise<VehicleMaintenance> {
    const res = await api.post<VehicleMaintenance>('/maintenance', data);
    return res.data;
  },

  async updateMaintenance(
    id: string,
    data: Partial<VehicleMaintenance>
  ): Promise<VehicleMaintenance> {
    const res = await api.put<VehicleMaintenance>(`/maintenance/${id}`, data);
    return res.data;
  },

  async deleteMaintenance(id: string): Promise<{ status: string; message: string }> {
    const res = await api.delete(`/maintenance/${id}`);
    return res.data;
  },

  async getDashboardSummary(): Promise<MaintenanceDashboardSummary> {
    const res = await api.get<MaintenanceDashboardSummary>('/maintenance/dashboard/summary');
    return res.data;
  },

  async getVehiclesDue(): Promise<MaintenanceVehicleDue[]> {
    const res = await api.get<MaintenanceVehicleDue[]>('/maintenance/due');
    return res.data;
  },
};
