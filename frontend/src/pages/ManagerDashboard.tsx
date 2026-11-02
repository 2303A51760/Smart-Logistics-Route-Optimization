import React, { useState, useEffect } from 'react';
import { SlidersHorizontal, BarChart3, Map, Sparkles } from 'lucide-react';
import { MetricsCards } from '../components/MetricsCards';
import { MapView } from '../components/maps/MapView';
import { FleetList } from '../components/FleetList';
import { HealthStatus } from '../components/HealthStatus';
import { OptimizationModal } from '../components/OptimizationModal';
import { OperationsDashboard } from './OperationsDashboard';
import { api } from '../services/api';
import { wsClient } from '../services/websocket';
import { Vehicle, Route, DeliveryPoint, SystemHealth, OptimizationResult } from '../types';

interface ManagerDashboardProps {
  isOptimizeOpen: boolean;
  setIsOptimizeOpen: (open: boolean) => void;
}

export const ManagerDashboard: React.FC<ManagerDashboardProps> = ({
  isOptimizeOpen,
  setIsOptimizeOpen,
}) => {
  const [activeTab, setActiveTab] = useState<'analytics' | 'map'>('analytics');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(false);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [deliveries, setDeliveries] = useState<DeliveryPoint[]>([]);

  const loadData = async () => {
    try {
      setHealthLoading(true);
      const [healthData, vehiclesData, routesData, deliveriesData] = await Promise.allSettled([
        api.getHealth(),
        api.getVehicles(),
        api.getRoutes(),
        api.getDeliveries(),
      ]);

      if (healthData.status === 'fulfilled') setHealth(healthData.value);
      if (vehiclesData.status === 'fulfilled') setVehicles(vehiclesData.value);
      if (routesData.status === 'fulfilled') setRoutes(routesData.value);
      if (deliveriesData.status === 'fulfilled') setDeliveries(deliveriesData.value);
    } catch (e) {
      console.warn('Manager data load error:', e);
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    const unsubscribe = wsClient.subscribe((msg) => {
      if (msg.type === 'TELEMETRY_HEARTBEAT' || msg.type === 'FLEET_UPDATE') {
        setVehicles((prev) =>
          prev.map((v) =>
            v.id === msg.vehicle_id
              ? {
                  ...v,
                  current_lat: msg.lat || v.current_lat,
                  current_lng: msg.lng || v.current_lng,
                  speed_kmh: msg.speed_kmh || v.speed_kmh,
                  fuel_level_percent: msg.battery_fuel || v.fuel_level_percent,
                  status: 'EN_ROUTE',
                }
              : v
          )
        );
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const handleOptimizationComplete = (result: OptimizationResult) => {
    const newRoutes: Route[] = result.routes.map((r, i) => ({
      id: `opt-route-${i}`,
      name: `Optimized Route ${i + 1}`,
      vehicle_id: r.vehicle_id,
      total_distance_km: r.distance_km,
      estimated_duration_min: r.estimated_time_min,
      start_lat: r.stops[0]?.lat || 40.7128,
      start_lng: r.stops[0]?.lng || -74.0060,
      waypoints_json: r.stops,
      is_optimized: true,
      status: 'DISPATCHED',
    }));
    setRoutes(newRoutes);
  };

  return (
    <div className="space-y-6">
      {/* View Switcher Tabs */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2 bg-slate-900/60 p-1.5 rounded-2xl border border-slate-800 backdrop-blur-xl">
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-2 ${
              activeTab === 'analytics'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Operations Analytics & KPIs
          </button>
          <button
            onClick={() => setActiveTab('map')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-2 ${
              activeTab === 'map'
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/25'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Map className="w-4 h-4" />
            Live Map & Dispatch Hub
          </button>
        </div>

        {activeTab === 'map' && (
          <button
            onClick={() => setIsOptimizeOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold shadow-glow transition"
          >
            <Sparkles className="w-4 h-4" />
            <span>Launch OR-Tools Optimizer</span>
          </button>
        )}
      </div>

      {activeTab === 'analytics' ? (
        <OperationsDashboard />
      ) : (
        <div className="space-y-6">
          {/* KPI Metrics */}
          <MetricsCards vehicles={vehicles} routes={routes} deliveries={deliveries} />

          {/* Map View */}
          <MapView vehicles={vehicles} routes={routes} deliveries={deliveries} />

          {/* Fleet & Delivery Queues */}
          <FleetList vehicles={vehicles} deliveries={deliveries} />

          {/* Health Status */}
          <HealthStatus health={health} loading={healthLoading} onRefresh={loadData} />
        </div>
      )}

      {/* Optimization Modal */}
      <OptimizationModal
        isOpen={isOptimizeOpen}
        onClose={() => setIsOptimizeOpen(false)}
        vehicles={vehicles}
        deliveries={deliveries}
        onOptimizationComplete={handleOptimizationComplete}
      />
    </div>
  );
};
