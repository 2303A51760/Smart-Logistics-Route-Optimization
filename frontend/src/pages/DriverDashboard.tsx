import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Navigation,
  CheckCircle2,
  Clock,
  MapPin,
  Truck,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  Package,
  Compass,
} from 'lucide-react';
import { dashboardApi, DriverMeDashboardData } from '../services/dashboard';
import { routesApi, RouteItem } from '../services/routes';
import { logisticsApi } from '../services/logistics';
import { StatCard } from '../components/dashboard/StatCard';
import { DashboardCard } from '../components/dashboard/DashboardCard';
import { DriverDeliveryCard } from '../components/dashboard/DriverDeliveryCard';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/dashboard/FeedbackStates';
import { DriverStatus } from '../types';
import { Toast } from '../components/Toast';

export const DriverDashboard: React.FC = () => {
  const [data, setData] = useState<DriverMeDashboardData | null>(null);
  const [activeRoute, setActiveRoute] = useState<RouteItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const fetchDriverDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const [dashRes, routesRes] = await Promise.all([
        dashboardApi.getDriverMeDashboard(),
        routesApi.listRoutes({ limit: 10 }),
      ]);
      setData(dashRes);

      // Find today's primary active or planned route
      const foundRoute =
        routesRes.items.find((r) => r.status === 'IN_PROGRESS' || r.status === 'STARTED') ||
        routesRes.items.find((r) => r.status === 'PLANNED') ||
        routesRes.items[0] ||
        null;
      setActiveRoute(foundRoute);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load your driver dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDriverDashboard();
  }, []);

  const handleStatusUpdate = async (newStatus: DriverStatus) => {
    if (!data?.driver?.id) return;
    try {
      setUpdatingStatus(true);
      const updated = await logisticsApi.updateDriver(data.driver.id, { status: newStatus });
      setData({
        ...data,
        driver: updated,
      });
      setToastMessage(`Duty status updated to ${newStatus.replace(/_/g, ' ')}`);
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to update duty status');
    } finally {
      setUpdatingStatus(false);
    }
  };

  if (loading && !data) {
    return <LoadingSkeleton />;
  }

  if (error && !data) {
    return <ErrorState message={error} onRetry={fetchDriverDashboard} />;
  }

  if (!data) return null;

  // Calculate remaining and current stops from activeRoute
  const stops = activeRoute?.stops || [];
  const completedCount = activeRoute?.completed_stops_count ?? 0;
  const totalStops = activeRoute?.stops_count ?? stops.length;
  const remainingStops = Math.max(0, totalStops - completedCount);

  const currentStop = stops.find((s) => s.status === 'ARRIVED' || s.status === 'IN_PROGRESS') ||
    stops.find((s) => s.status === 'PENDING') ||
    null;

  const nextStop = currentStop
    ? stops.find((s) => s.sequence > currentStop.sequence && s.status === 'PENDING') || null
    : null;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Welcome & Duty Status Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-gradient-to-r from-blue-950/40 via-slate-900 to-slate-900 p-6 rounded-2xl border border-blue-500/20 backdrop-blur-xl shadow-xl">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-3xl shadow-inner">
            🧑‍✈️
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
              Driver Cockpit
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              License: <span className="font-mono text-slate-300 font-bold">{data.driver.license_number}</span> &bull;
              Vehicle: <span className="text-emerald-400 font-semibold">{data.driver.assigned_vehicle_number ? `🚛 ${data.driver.assigned_vehicle_number}` : (activeRoute?.vehicle_number ? `🚛 ${activeRoute.vehicle_number}` : 'None')}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 font-semibold">Duty Status:</label>
          <select
            disabled={updatingStatus}
            value={data.driver.status}
            onChange={(e) => handleStatusUpdate(e.target.value as DriverStatus)}
            className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-bold"
          >
            <option value="AVAILABLE">🟢 AVAILABLE</option>
            <option value="ASSIGNED">🔵 ASSIGNED</option>
            <option value="IN_TRANSIT">🚚 IN TRANSIT</option>
            <option value="OFF_DUTY">🟡 OFF DUTY</option>
          </select>
        </div>
      </div>

      {/* Section 8: Today's Route Card */}
      {activeRoute ? (
        <div className="bg-gradient-to-br from-slate-900/90 via-slate-900 to-indigo-950/30 p-6 rounded-2xl border border-indigo-500/30 backdrop-blur-xl shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-slate-800 pb-3">
            <div>
              <span className="text-[11px] font-mono text-indigo-400 uppercase tracking-wider font-semibold">Today's Assigned Route</span>
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Navigation className="w-5 h-5 text-blue-400" />
                {activeRoute.name || `Route Execution #${activeRoute.id}`}
              </h2>
            </div>

            <div className="flex items-center gap-3">
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold ${
                  activeRoute.status === 'IN_PROGRESS' || activeRoute.status === 'STARTED'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 animate-pulse'
                    : activeRoute.status === 'COMPLETED'
                    ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                    : 'bg-slate-800 text-slate-300 border border-slate-700'
                }`}
              >
                {activeRoute.status}
              </span>
              <Link
                to={`/driver/routes/${activeRoute.id}`}
                className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-glow transition"
              >
                <span>Open Route Cockpit</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Route Overview Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <span className="text-slate-400 flex items-center gap-1 mb-1">
                <Truck className="w-3.5 h-3.5 text-indigo-400" /> Assigned Vehicle
              </span>
              <p className="font-bold text-slate-200 text-sm">{activeRoute.vehicle_number || 'Fleet Van'}</p>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <span className="text-slate-400 flex items-center gap-1 mb-1">
                <TrendingUp className="w-3.5 h-3.5 text-blue-400" /> Total Distance
              </span>
              <p className="font-bold text-slate-200 text-sm">{activeRoute.total_distance} km</p>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <span className="text-slate-400 flex items-center gap-1 mb-1">
                <Clock className="w-3.5 h-3.5 text-amber-400" /> Est. Duration
              </span>
              <p className="font-bold text-slate-200 text-sm">{activeRoute.estimated_duration} min</p>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <span className="text-slate-400 flex items-center gap-1 mb-1">
                <Package className="w-3.5 h-3.5 text-emerald-400" /> Completed / Remaining
              </span>
              <p className="font-bold text-slate-200 text-sm">
                <span className="text-emerald-400">{completedCount}</span> / <span className="text-amber-400">{remainingStops} left</span>
              </p>
            </div>
          </div>

          {/* Current and Next Stop Display */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/30">
              <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wider block mb-1">
                📍 Current Active Stop
              </span>
              {currentStop ? (
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-100 text-sm">
                      #{currentStop.sequence} {currentStop.customer_name || 'Client Delivery'}
                    </span>
                    <span className="text-xs font-mono text-slate-400">({currentStop.order_number})</span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-amber-400" />
                    {currentStop.delivery_address || 'Delivery Address'}
                  </p>
                </div>
              ) : (
                <p className="text-xs text-slate-400">No active stops remaining.</p>
              )}
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                🎯 Next Stop in Queue
              </span>
              {nextStop ? (
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200 text-sm">
                      #{nextStop.sequence} {nextStop.customer_name || 'Upcoming Delivery'}
                    </span>
                    <span className="text-xs font-mono text-slate-400">({nextStop.order_number})</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-slate-500" />
                    {nextStop.delivery_address || 'Destination'}
                  </p>
                </div>
              ) : (
                <p className="text-xs text-slate-500">Route finale / Return to depot.</p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <Compass className="w-8 h-8 text-blue-400" />
            <div>
              <h3 className="text-base font-bold text-slate-200">No Active Route Assigned Today</h3>
              <p className="text-xs text-slate-400">New optimized routes will appear here as soon as dispatch assigns them.</p>
            </div>
          </div>
          <Link
            to="/driver/routes"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            View Route History
          </Link>
        </div>
      )}

      {/* Driver Performance Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Today's Deliveries"
          value={data.stats.today_deliveries}
          subtitle="Total assigned stops"
          icon="📦"
          color="blue"
        />
        <StatCard
          title="Completed"
          value={data.stats.completed_deliveries}
          subtitle="Successful drop-offs"
          icon="✅"
          color="emerald"
        />
        <StatCard
          title="Pending Stops"
          value={data.stats.pending_deliveries}
          subtitle="Remaining on route"
          icon="⏳"
          color="amber"
        />
        <StatCard
          title="Failed / Returned"
          value={data.stats.failed_deliveries}
          subtitle="Undelivered parcels"
          icon="⚠️"
          color="rose"
        />
        <StatCard
          title="Fulfillment Rate"
          value={`${data.stats.completion_rate}%`}
          subtitle="Personal score"
          icon="🎯"
          color="cyan"
        />
      </div>

      {/* Assigned Deliveries Manifest */}
      <DashboardCard
        title={`Assigned Deliveries Manifest (${data.assigned_orders.length})`}
        subtitle="All scheduled pickup and drop-off orders assigned to your route"
        action={
          <button
            onClick={fetchDriverDashboard}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition flex items-center gap-1.5"
          >
            <span>⟳</span> Refresh Manifest
          </button>
        }
      >
        {data.assigned_orders.length === 0 ? (
          <EmptyState
            title="No Deliveries Scheduled"
            description="You do not have any pending delivery orders dispatched at this time. Check back once new routes are optimized."
            icon="🚚"
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.assigned_orders.map((order) => (
              <DriverDeliveryCard
                key={order.id}
                order={order}
                isNext={data.next_delivery?.id === order.id}
              />
            ))}
          </div>
        )}
      </DashboardCard>

      {toastMessage && <Toast message={toastMessage} onClose={() => setToastMessage(null)} />}
    </div>
  );
};
