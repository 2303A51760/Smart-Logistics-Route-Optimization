import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Truck,
  Package,
  Building2,
  Users,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  MapPin,
  Clock,
  Zap,
} from 'lucide-react';
import { logisticsApi } from '../services/logistics';
import { optimizationApi, OptimizationResultResponse, VehicleRouteItem } from '../services/optimization';
import { Warehouse, Order, Driver, Vehicle } from '../types';
import { MapView } from '../components/maps/MapView';
import { WarehouseMarker } from '../components/maps/WarehouseMarker';
import { RoutePolyline } from '../components/maps/RoutePolyline';
import { Toast } from '../components/Toast';
import L from 'leaflet';
import { Marker, Popup } from 'react-leaflet';

const ROUTE_COLORS = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#f43f5e', '#06b6d4'];

const createNumberedIcon = (sequence: number, color: string) => {
  return L.divIcon({
    className: 'custom-numbered-pin',
    html: `
      <div style="
        background-color: ${color};
        width: 26px;
        height: 26px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 11px;
        font-weight: bold;
        font-family: monospace;
      ">
        ${sequence}
      </div>
    `,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
};

export const OptimizationConsole: React.FC = () => {
  const navigate = useNavigate();
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);

  // Selections
  const [selectedWarehouseId, setSelectedWarehouseId] = useState<string>('');
  const [selectedOrderIds, setSelectedOrderIds] = useState<string[]>([]);
  const [selectedDriverIds, setSelectedDriverIds] = useState<string[]>([]);
  const [selectedVehicleIds, setSelectedVehicleIds] = useState<string[]>([]);
  const [maxDistanceKm, setMaxDistanceKm] = useState<number>(200);

  // Solver State
  const [solving, setSolving] = useState(false);
  const [result, setResult] = useState<OptimizationResultResponse | null>(null);
  const [committing, setCommitting] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [whs, ordsRes, drvs, vehs] = await Promise.all([
        logisticsApi.getWarehouses(),
        logisticsApi.getOrders({ size: 50 }),
        logisticsApi.getDrivers(),
        logisticsApi.getVehicles(),
      ]);

      setWarehouses(whs);
      if (whs.length > 0) {
        setSelectedWarehouseId(whs[0].id);
      }

      const pending = (ordsRes.items || []).filter((o) => o.status === 'PENDING' || o.status === 'ASSIGNED');
      setOrders(pending);
      setSelectedOrderIds(pending.map((o) => o.id));

      setDrivers(drvs);
      setSelectedDriverIds(drvs.map((d) => d.id));

      setVehicles(vehs);
      setSelectedVehicleIds(vehs.map((v) => v.id));
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to load logistics assets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleOrder = (orderId: string) => {
    if (selectedOrderIds.includes(orderId)) {
      setSelectedOrderIds(selectedOrderIds.filter((id) => id !== orderId));
    } else {
      setSelectedOrderIds([...selectedOrderIds, orderId]);
    }
  };

  const handleSelectAllOrders = () => {
    if (selectedOrderIds.length === orders.length) {
      setSelectedOrderIds([]);
    } else {
      setSelectedOrderIds(orders.map((o) => o.id));
    }
  };

  const handleRunOptimization = async () => {
    if (!selectedWarehouseId) {
      setToastMessage('Please select a dispatch warehouse depot');
      return;
    }
    if (selectedOrderIds.length === 0) {
      setToastMessage('Please select at least one pending order to optimize');
      return;
    }

    try {
      setSolving(true);
      const res = await optimizationApi.optimize({
        warehouse_id: selectedWarehouseId,
        order_ids: selectedOrderIds,
        driver_ids: selectedDriverIds,
        vehicle_ids: selectedVehicleIds,
        max_route_distance_km: maxDistanceKm,
      });
      setResult(res);
      setToastMessage(`Optimization complete: ${res.orders_assigned} orders routed across ${res.vehicles_used} vehicles!`);
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Route optimization failed');
    } finally {
      setSolving(false);
    }
  };

  const handleCommitRoutes = async () => {
    if (!result) return;
    try {
      setCommitting(true);
      const res = await optimizationApi.createRoutes(result.job_id);
      setToastMessage(res.message || 'Routes generated and saved successfully!');
      setTimeout(() => {
        navigate('/manager/routes');
      }, 1200);
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to generate executable routes');
    } finally {
      setCommitting(false);
    }
  };

  const selectedWarehouse = warehouses.find((w) => w.id === selectedWarehouseId);

  // Map Coordinates Calculation
  const mapCoordinates: [number, number][] = [];
  if (selectedWarehouse) {
    mapCoordinates.push([selectedWarehouse.latitude, selectedWarehouse.longitude]);
  }
  if (result) {
    result.routes.forEach((r) => {
      r.stops.forEach((s) => {
        mapCoordinates.push([s.latitude, s.longitude]);
      });
    });
  } else {
    orders
      .filter((o) => selectedOrderIds.includes(o.id))
      .forEach((o) => {
        mapCoordinates.push([o.delivery_latitude, o.delivery_longitude]);
      });
  }

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-400">
        <div className="inline-block animate-spin text-3xl mb-3 text-emerald-400">⟳</div>
        <p className="text-sm">Loading Optimization Dispatch Hub...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link to="/dashboard" className="hover:text-blue-400">
              Operations
            </Link>
            <span>/</span>
            <span className="text-emerald-400 font-semibold">OR-Tools Route Optimization</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <span className="p-2 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-glow">
              <Zap className="w-5 h-5" />
            </span>
            Advanced Route Optimization Engine
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Google OR-Tools CVRP & VRPTW with vehicle capacity, time windows, and multi-fleet balancing.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            disabled={solving || selectedOrderIds.length === 0}
            onClick={handleRunOptimization}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-glow transition-all"
          >
            {solving ? (
              <>
                <span className="inline-block animate-spin">⟳</span> Solving Constraints...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" /> Run Route Optimization
              </>
            )}
          </button>
        </div>
      </div>

      {/* KPI Metrics Strip (If Result Ready) */}
      {result && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl">
            <span className="text-slate-400 text-xs flex items-center gap-1.5 mb-1">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Total Distance
            </span>
            <p className="text-xl font-bold text-slate-100">{result.total_distance_km} <span className="text-xs font-normal text-slate-400">km</span></p>
          </div>

          <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl">
            <span className="text-slate-400 text-xs flex items-center gap-1.5 mb-1">
              <Clock className="w-3.5 h-3.5 text-blue-400" /> Est. Duration
            </span>
            <p className="text-xl font-bold text-slate-100">{result.total_duration_min} <span className="text-xs font-normal text-slate-400">min</span></p>
          </div>

          <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl">
            <span className="text-slate-400 text-xs flex items-center gap-1.5 mb-1">
              <Truck className="w-3.5 h-3.5 text-indigo-400" /> Vehicles Used
            </span>
            <p className="text-xl font-bold text-slate-100">{result.vehicles_used}</p>
          </div>

          <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl">
            <span className="text-slate-400 text-xs flex items-center gap-1.5 mb-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Orders Routed
            </span>
            <p className="text-xl font-bold text-emerald-400">{result.orders_assigned}</p>
          </div>

          <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl">
            <span className="text-slate-400 text-xs flex items-center gap-1.5 mb-1">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Unassigned
            </span>
            <p className="text-xl font-bold text-amber-400">{result.orders_unassigned}</p>
          </div>

          <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl">
            <span className="text-slate-400 text-xs flex items-center gap-1.5 mb-1">
              <Zap className="w-3.5 h-3.5 text-purple-400" /> Opt. Score
            </span>
            <p className="text-xl font-bold text-purple-400">{result.optimization_score}%</p>
          </div>
        </div>
      )}

      {/* Main Grid: Left Controls & Right Map Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Asset Selection Form (4 Cols) */}
        <div className="lg:col-span-5 space-y-5">
          {/* 1. Warehouse Depot */}
          <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider">
              <Building2 className="w-4 h-4 text-indigo-400" /> 1. Select Warehouse Hub
            </div>
            <select
              value={selectedWarehouseId}
              onChange={(e) => setSelectedWarehouseId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name} ({w.capacity.toLocaleString()} kg capacity)
                </option>
              ))}
            </select>
          </div>

          {/* 2. Pending Orders Selection */}
          <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider">
                <Package className="w-4 h-4 text-emerald-400" /> 2. Select Orders ({selectedOrderIds.length}/{orders.length})
              </div>
              <button
                onClick={handleSelectAllOrders}
                className="text-[11px] text-blue-400 hover:underline font-semibold"
              >
                {selectedOrderIds.length === orders.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            <div className="max-h-56 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
              {orders.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-4 text-center">No pending orders available.</p>
              ) : (
                orders.map((ord) => {
                  const isChecked = selectedOrderIds.includes(ord.id);
                  return (
                    <div
                      key={ord.id}
                      onClick={() => handleToggleOrder(ord.id)}
                      className={`p-2.5 rounded-xl border text-xs cursor-pointer flex items-center justify-between transition-all ${
                        isChecked
                          ? 'bg-slate-800/80 border-emerald-500/50 text-slate-100'
                          : 'bg-slate-950/40 border-slate-800/80 text-slate-400 hover:bg-slate-800/40'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="rounded text-emerald-500 bg-slate-900 border-slate-700"
                        />
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="font-mono font-bold">{ord.order_number}</span>
                            <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                              ord.priority === 'URGENT' ? 'bg-rose-500/20 text-rose-300' :
                              ord.priority === 'HIGH' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-slate-300'
                            }`}>
                              {ord.priority}
                            </span>
                          </div>
                          <span className="text-[11px] text-slate-400">{ord.customer_name}</span>
                        </div>
                      </div>
                      <span className="font-mono text-slate-300 text-[11px]">{ord.package_weight} kg</span>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* 3. Fleet & Driver Resources */}
          <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider">
              <Truck className="w-4 h-4 text-purple-400" /> 3. Available Fleet & Drivers
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Active Vehicles:</span>
                <span className="font-bold text-slate-200">{vehicles.length} Vehicles</span>
              </div>
              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Active Drivers:</span>
                <span className="font-bold text-slate-200">{drivers.length} Drivers</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Multi-Route Interactive Leaflet Map & Details (7 Cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Leaflet Multi-Route Map */}
          <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex justify-between items-center">
              <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-400" /> Sequenced Multi-Route Map
              </h2>
              {result && (
                <span className="text-[11px] text-emerald-400 font-semibold">
                  ✓ {result.routes.length} vehicle routes computed
                </span>
              )}
            </div>

            <MapView height="420px" bounds={mapCoordinates.length > 0 ? mapCoordinates : undefined} autoFit={true}>
              {/* Warehouse Depot Marker */}
              {selectedWarehouse && (
                <WarehouseMarker warehouse={selectedWarehouse} />
              )}

              {/* Solved Route Polylines and Numbered Waypoints */}
              {result &&
                result.routes.map((r, rIdx) => {
                  const color = ROUTE_COLORS[rIdx % ROUTE_COLORS.length];
                  const polylineCoords: [number, number][] = r.stops.map((s) => [s.latitude, s.longitude]);

                  return (
                    <React.Fragment key={`route-poly-${rIdx}`}>
                      <RoutePolyline positions={polylineCoords} color={color} weight={4} opacity={0.85} />
                      {r.stops.map((s, sIdx) => {
                        if (s.stop_type === 'DEPOT') return null;
                        return (
                          <Marker
                            key={`stop-${rIdx}-${sIdx}`}
                            position={[s.latitude, s.longitude]}
                            icon={createNumberedIcon(s.sequence, color)}
                          >
                            <Popup>
                              <div className="text-xs space-y-1">
                                <span className="font-bold text-blue-600 block">Stop #{s.sequence}</span>
                                <p className="font-semibold">{s.name}</p>
                                <p>Weight: {s.demand_kg} kg | Priority: {s.priority}</p>
                                <p className="text-[11px] text-gray-500">ETA: {s.estimated_arrival_minutes} min</p>
                              </div>
                            </Popup>
                          </Marker>
                        );
                      })}
                    </React.Fragment>
                  );
                })}
            </MapView>

            {/* Route Color Legend */}
            {result && result.routes.length > 0 && (
              <div className="flex flex-wrap gap-3 pt-2 text-xs border-t border-slate-800">
                {result.routes.map((r, rIdx) => {
                  const color = ROUTE_COLORS[rIdx % ROUTE_COLORS.length];
                  return (
                    <div key={`legend-${rIdx}`} className="flex items-center gap-2 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                      <span className="text-slate-200 font-semibold">{r.vehicle_name}</span>
                      <span className="text-slate-400 text-[11px]">({r.total_distance_km} km &bull; {r.stops_count} stops)</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Solved Route Itinerary Breakdown */}
          {result && (
            <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Generated Route Itineraries
                </h3>
                <button
                  disabled={committing}
                  onClick={handleCommitRoutes}
                  className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-blue-500/25 transition"
                >
                  {committing ? 'Generating...' : 'Confirm & Deploy Routes →'}
                </button>
              </div>

              <div className="space-y-3">
                {result.routes.map((r, rIdx) => (
                  <div key={`itin-${rIdx}`} className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-100">{r.vehicle_name}</span>
                        {r.driver_name && (
                          <span className="text-[11px] text-slate-400">({r.driver_name})</span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-slate-400 font-mono text-[11px]">
                        <span>Load: {r.total_load_kg}/{r.capacity_kg} kg</span>
                        <span>{r.total_distance_km} km</span>
                        <span>{r.estimated_duration_min} min</span>
                      </div>
                    </div>

                    {/* Sequence list */}
                    <div className="flex items-center gap-2 overflow-x-auto py-1 custom-scrollbar text-[11px]">
                      {r.stops.map((s, sIdx) => (
                        <React.Fragment key={`step-${sIdx}`}>
                          <div className={`px-2.5 py-1 rounded-lg shrink-0 border ${
                            s.stop_type === 'DEPOT' ? 'bg-indigo-950/60 border-indigo-800/80 text-indigo-300' : 'bg-slate-900 border-slate-700 text-slate-200'
                          }`}>
                            <span className="font-bold mr-1">#{s.sequence}</span>
                            {s.name}
                          </div>
                          {sIdx < r.stops.length - 1 && <span className="text-slate-600 shrink-0">→</span>}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {toastMessage && <Toast message={toastMessage} onClose={() => setToastMessage(null)} />}
    </div>
  );
};
