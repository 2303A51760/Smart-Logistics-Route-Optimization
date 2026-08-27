import { api } from './api';

export interface MapDriver {
  id: string;
  name: string;
  license_number: string;
  phone: string;
  status: string;
  latitude: number;
  longitude: number;
  vehicle_number?: string | null;
  vehicle_type?: string | null;
  speed?: number | null;
  heading?: number | null;
  last_updated?: string | null;
}


export interface MapWarehouse {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  capacity: number;
}

export interface MapOrder {
  id: string;
  order_number: string;
  customer_name: string;
  delivery_address?: string | null;
  pickup_latitude: number;
  pickup_longitude: number;
  delivery_latitude: number;
  delivery_longitude: number;
  priority: string;
  status: string;
  package_weight: number;
  assigned_driver_id?: string | null;
  assigned_driver_name?: string | null;
}

export interface MapOverviewData {
  drivers: MapDriver[];
  warehouses: MapWarehouse[];
  orders: MapOrder[];
}

export const mapApi = {
  async getMapOverview(): Promise<MapOverviewData> {
    const res = await api.get<MapOverviewData>('/map/overview');
    return res.data;
  },
};
