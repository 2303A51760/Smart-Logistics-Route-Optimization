import { api } from './api';

export interface DriverLocation {
  driver_id: string;
  name?: string | null;
  latitude: number;
  longitude: number;
  accuracy?: number | null;
  speed?: number | null;
  heading?: number | null;
  status?: string | null;
  last_updated?: string | null;
}

export interface LocationHistoryItem {
  id: string;
  driver_id: string;
  latitude: number;
  longitude: number;
  accuracy?: number | null;
  speed?: number | null;
  heading?: number | null;
  timestamp: string;
}

export interface DriverLocationHistory {
  driver_id: string;
  total_points: number;
  locations: LocationHistoryItem[];
}

export const trackingApi = {
  async getDrivers(): Promise<{ drivers: DriverLocation[] }> {
    const res = await api.get<{ drivers: DriverLocation[] }>('/tracking/drivers');
    return res.data;
  },

  async getDriverHistory(
    driverId: string,
    params?: { start_time?: string; end_time?: string; limit?: number }
  ): Promise<DriverLocationHistory> {
    const res = await api.get<DriverLocationHistory>(`/tracking/drivers/${driverId}/history`, {
      params,
    });
    return res.data;
  },
};
