import { api } from './api';
import {
  Driver,
  Vehicle,
  Warehouse,
  Customer,
  Order,
  OrderListResponse,
} from '../types';

export const logisticsApi = {
  // === Drivers ===
  async getDrivers(status?: string): Promise<Driver[]> {
    const res = await api.get<Driver[]>('/drivers', { params: status ? { status } : {} });
    return res.data;
  },

  async getDriver(id: string): Promise<Driver> {
    const res = await api.get<Driver>(`/drivers/${id}`);
    return res.data;
  },

  async createDriver(data: Partial<Driver>): Promise<Driver> {
    const res = await api.post<Driver>('/drivers', data);
    return res.data;
  },

  async updateDriver(id: string, data: Partial<Driver>): Promise<Driver> {
    const res = await api.put<Driver>(`/drivers/${id}`, data);
    return res.data;
  },

  async deleteDriver(id: string): Promise<{ status: string; message: string }> {
    const res = await api.delete(`/drivers/${id}`);
    return res.data;
  },

  // === Vehicles ===
  async getVehicles(status?: string): Promise<Vehicle[]> {
    const res = await api.get<Vehicle[]>('/vehicles', { params: status ? { status } : {} });
    return res.data;
  },

  async getVehicle(id: string): Promise<Vehicle> {
    const res = await api.get<Vehicle>(`/vehicles/${id}`);
    return res.data;
  },

  async createVehicle(data: Partial<Vehicle>): Promise<Vehicle> {
    const res = await api.post<Vehicle>('/vehicles', data);
    return res.data;
  },

  async updateVehicle(id: string, data: Partial<Vehicle>): Promise<Vehicle> {
    const res = await api.put<Vehicle>(`/vehicles/${id}`, data);
    return res.data;
  },

  async deleteVehicle(id: string): Promise<{ status: string; message: string }> {
    const res = await api.delete(`/vehicles/${id}`);
    return res.data;
  },

  // === Warehouses ===
  async getWarehouses(): Promise<Warehouse[]> {
    const res = await api.get<Warehouse[]>('/warehouses');
    return res.data;
  },

  async getWarehouse(id: string): Promise<Warehouse> {
    const res = await api.get<Warehouse>(`/warehouses/${id}`);
    return res.data;
  },

  async createWarehouse(data: Partial<Warehouse>): Promise<Warehouse> {
    const res = await api.post<Warehouse>('/warehouses', data);
    return res.data;
  },

  async updateWarehouse(id: string, data: Partial<Warehouse>): Promise<Warehouse> {
    const res = await api.put<Warehouse>(`/warehouses/${id}`, data);
    return res.data;
  },

  async deleteWarehouse(id: string): Promise<{ status: string; message: string }> {
    const res = await api.delete(`/warehouses/${id}`);
    return res.data;
  },

  // === Customers ===
  async getCustomers(): Promise<Customer[]> {
    const res = await api.get<Customer[]>('/customers');
    return res.data;
  },

  async getCustomer(id: string): Promise<Customer> {
    const res = await api.get<Customer>(`/customers/${id}`);
    return res.data;
  },

  async createCustomer(data: Partial<Customer>): Promise<Customer> {
    const res = await api.post<Customer>('/customers', data);
    return res.data;
  },

  async updateCustomer(id: string, data: Partial<Customer>): Promise<Customer> {
    const res = await api.put<Customer>(`/customers/${id}`, data);
    return res.data;
  },

  async deleteCustomer(id: string): Promise<{ status: string; message: string }> {
    const res = await api.delete(`/customers/${id}`);
    return res.data;
  },

  // === Orders ===
  async getOrders(params?: {
    search?: string;
    status?: string;
    priority?: string;
    driver_id?: string;
    warehouse_id?: string;
    page?: number;
    size?: number;
  }): Promise<OrderListResponse> {
    const res = await api.get<OrderListResponse>('/orders', { params });
    return res.data;
  },

  async getOrder(id: string): Promise<Order> {
    const res = await api.get<Order>(`/orders/${id}`);
    return res.data;
  },

  async createOrder(data: Partial<Order>): Promise<Order> {
    const res = await api.post<Order>('/orders', data);
    return res.data;
  },

  async updateOrder(id: string, data: Partial<Order>): Promise<Order> {
    const res = await api.put<Order>(`/orders/${id}`, data);
    return res.data;
  },

  async deleteOrder(id: string): Promise<{ status: string; message: string }> {
    const res = await api.delete(`/orders/${id}`);
    return res.data;
  },
};
