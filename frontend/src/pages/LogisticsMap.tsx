import React, { useEffect, useState, useMemo } from 'react';
import { mapApi, MapOverviewData, MapDriver, MapWarehouse, MapOrder } from '../services/map';
import { wsClient } from '../services/websocket';
import { MapView } from '../components/maps/MapView';
import { DriverMarker } from '../components/maps/DriverMarker';
import { WarehouseMarker } from '../components/maps/WarehouseMarker';
import { OrderMarker } from '../components/maps/OrderMarker';
import { RoutePolyline } from '../components/maps/RoutePolyline';
import { MapFilters, MapFiltersState } from '../components/maps/MapFilters';
import { MapLegend } from '../components/maps/MapLegend';
import { SelectedEntityCard, SelectedEntity } from '../components/maps/SelectedEntityCard';
import { LoadingSkeleton, ErrorState } from '../components/dashboard/FeedbackStates';
import { Radio, Activity, Navigation2 } from 'lucide-react';

export const LogisticsMap: React.FC = () => {
  const [data, setData] = useState<MapOverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<SelectedEntity>(null);
  const [showPolylines, setShowPolylines] = useState(true);
  const [showTrails, setShowTrails] = useState(true);

  // Live Telemetry state
  const [wsStatus, setWsStatus] = useState<'CONNECTED' | 'CONNECTING' | 'DISCONNECTED'>('DISCONNECTED');
  const [driverTrails, setDriverTrails] = useState<Record<string, [number, number][]>>({});
  const [recentLiveUpdate, setRecentLiveUpdate] = useState<string | null>(null);

  const [filters, setFilters] = useState<MapFiltersState>({
    entityType: 'ALL',
    driverStatus: 'ALL',
    orderStatus: 'ALL',
    priority: 'ALL',
  });

  const fetchMapData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await mapApi.getMapOverview();
      setData(res);
      // Initialize driver trails with their current position
      const initialTrails: Record<string, [number, number][]> = {};
      res.drivers.forEach((d) => {
        if (d.latitude && d.longitude) {
          initialTrails[d.id] = [[d.latitude, d.longitude]];
        }
      });
      setDriverTrails(initialTrails);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load interactive logistics map.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMapData();
  }, []);

  // Connect to WebSocket and listen for driver telemetry
  useEffect(() => {
    wsClient.connect();
    const unsubStatus = wsClient.onStatusChange((status) => {
      setWsStatus(status);
    });

    const unsubMsg = wsClient.subscribe((msg) => {
      if (msg.type === 'driver_location_updated') {
        const { driver_id, driver_name, latitude, longitude, speed, heading, timestamp } = msg;

        setRecentLiveUpdate(`Driver ${driver_name || driver_id} moved to [${latitude.toFixed(4)}, ${longitude.toFixed(4)}]`);

        // Update driver position in data state in-place (no full refetch)
        setData((prev) => {
          if (!prev) return prev;
          const driverExists = prev.drivers.some((d) => d.id === driver_id);
          let updatedDrivers: MapDriver[];

          if (driverExists) {
            updatedDrivers = prev.drivers.map((d) => {
              if (d.id === driver_id) {
                return {
                  ...d,
                  latitude,
                  longitude,
                  speed: speed ?? d.speed,
                  heading: heading ?? d.heading,
                  last_updated: timestamp,
                };
              }
              return d;
            });
          } else {
            // If new driver seen in live broadcast
            const newDriver: MapDriver = {
              id: driver_id,
              name: driver_name || `Driver ${driver_id}`,
              license_number: 'LIVE-GPS',
              phone: 'Telemetry Live',
              status: 'IN_TRANSIT',
              latitude,
              longitude,
              speed,
              heading,
              last_updated: timestamp,
            };
            updatedDrivers = [...prev.drivers, newDriver];
          }

          return { ...prev, drivers: updatedDrivers };
        });

        // Append to driver recent trails (up to 15 points)
        setDriverTrails((prev) => {
          const currentTrail = prev[driver_id] || [];
          const updatedTrail = [...currentTrail, [latitude, longitude] as [number, number]].slice(-15);
          return { ...prev, [driver_id]: updatedTrail };
        });
      }
    });

    return () => {
      unsubStatus();
      unsubMsg();
    };
  }, []);

  // Filtered drivers
  const filteredDrivers = useMemo(() => {
    if (!data) return [];
    if (filters.entityType === 'WAREHOUSES' || filters.entityType === 'ORDERS') return [];
    return data.drivers.filter((d) => {
      if (filters.driverStatus !== 'ALL' && d.status !== filters.driverStatus) return false;
      return true;
    });
  }, [data, filters]);

  // Filtered warehouses
  const filteredWarehouses = useMemo(() => {
    if (!data) return [];
    if (filters.entityType === 'DRIVERS' || filters.entityType === 'ORDERS') return [];
    return data.warehouses;
  }, [data, filters]);

  // Filtered orders
  const filteredOrders = useMemo(() => {
    if (!data) return [];
    if (filters.entityType === 'DRIVERS' || filters.entityType === 'WAREHOUSES') return [];
    return data.orders.filter((o) => {
      if (filters.orderStatus !== 'ALL' && o.status !== filters.orderStatus) return false;
      if (filters.priority !== 'ALL' && o.priority !== filters.priority) return false;
      return true;
    });
  }, [data, filters]);

  // Calculate dynamic bounds initially
  const mapBounds = useMemo(() => {
    const coords: [number, number][] = [];
    filteredWarehouses.forEach((w) => coords.push([w.latitude, w.longitude]));
    filteredDrivers.forEach((d) => coords.push([d.latitude, d.longitude]));
    filteredOrders.forEach((o) => {
      coords.push([o.delivery_latitude, o.delivery_longitude]);
    });
    return coords.length > 0 ? coords : undefined;
  }, [filteredWarehouses, filteredDrivers, filteredOrders]);

  if (loading && !data) {
    return <LoadingSkeleton />;
  }

  if (error && !data) {
    return <ErrorState message={error} onRetry={fetchMapData} />;
  }

  return (
    <div className="space-y-4">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60 p-5 rounded-2xl border border-slate-800 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
              <span>🗺️</span> Interactive Logistics Map
            </h1>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-950 border border-slate-800 text-[11px] font-mono">
              <span
                className={`w-2 h-2 rounded-full ${
                  wsStatus === 'CONNECTED'
                    ? 'bg-emerald-400 animate-pulse'
                    : wsStatus === 'CONNECTING'
                    ? 'bg-amber-400 animate-bounce'
                    : 'bg-rose-400'
                }`}
              ></span>
              <span className="text-slate-300 font-bold">Live Telemetry: {wsStatus}</span>
            </div>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time geospatial overview of warehouses, drivers, live GPS coordinates, and delivery stop waypoints.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={showTrails}
              onChange={(e) => setShowTrails(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-emerald-600 focus:ring-0"
            />
            <span>Driver GPS Trails</span>
          </label>

          <label className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={showPolylines}
              onChange={(e) => setShowPolylines(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0"
            />
            <span>Vectors</span>
          </label>

          <button
            onClick={fetchMapData}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition flex items-center gap-1.5"
          >
            <span>⟳</span> Refresh Pins
          </button>
        </div>
      </div>

      {/* Live Stream Telemetry Banner */}
      {recentLiveUpdate && (
        <div className="px-4 py-2 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span>{recentLiveUpdate}</span>
          </span>
          <span className="text-[10px] text-emerald-500">Live Telemetry Feed</span>
        </div>
      )}

      {/* Filter Toolbar */}
      {data && (
        <MapFilters
          filters={filters}
          onChange={setFilters}
          counts={{
            drivers: data.drivers.length,
            warehouses: data.warehouses.length,
            orders: data.orders.length,
          }}
        />
      )}

      {/* Main Map Canvas */}
      <div className="relative">
        <MapView
          height="650px"
          bounds={mapBounds}
          autoFit={true}
          className="ring-1 ring-slate-800"
        >
          {/* Warehouses */}
          {filteredWarehouses.map((w) => (
            <WarehouseMarker
              key={`wh-${w.id}`}
              warehouse={w}
              onSelect={(wh) => setSelectedEntity({ type: 'WAREHOUSE', data: wh })}
            />
          ))}

          {/* Drivers & Recent GPS Trails */}
          {filteredDrivers.map((d) => (
            <React.Fragment key={`drv-${d.id}`}>
              <DriverMarker
                driver={d}
                onSelect={(drv) => setSelectedEntity({ type: 'DRIVER', data: drv })}
              />

              {/* Live Driver Trail Breadcrumbs */}
              {showTrails && driverTrails[d.id] && driverTrails[d.id].length >= 2 && (
                <RoutePolyline
                  positions={driverTrails[d.id]}
                  color="#10b981"
                  weight={3}
                  opacity={0.7}
                  dashArray="4, 6"
                />
              )}
            </React.Fragment>
          ))}

          {/* Orders */}
          {filteredOrders.map((o) => (
            <React.Fragment key={`ord-${o.id}`}>
              <OrderMarker
                order={o}
                onSelect={(ord) => setSelectedEntity({ type: 'ORDER', data: ord })}
              />

              {/* Draw simple straight line between pickup & delivery */}
              {showPolylines && (
                <RoutePolyline
                  positions={[
                    [o.pickup_latitude, o.pickup_longitude],
                    [o.delivery_latitude, o.delivery_longitude],
                  ]}
                  color={o.priority === 'URGENT' ? '#ef4444' : '#3b82f6'}
                  weight={2}
                  opacity={0.6}
                />
              )}
            </React.Fragment>
          ))}
        </MapView>

        {/* Floating Legend Top Right */}
        <div className="absolute top-4 right-4 z-[400] max-w-sm hidden sm:block">
          <MapLegend />
        </div>

        {/* Bottom Floating Drawer for Selected Entity */}
        {selectedEntity && (
          <div className="absolute bottom-6 left-6 right-6 sm:left-auto sm:right-6 sm:w-96 z-[400]">
            <SelectedEntityCard
              entity={selectedEntity}
              onClose={() => setSelectedEntity(null)}
            />
          </div>
        )}
      </div>
    </div>
  );
};
