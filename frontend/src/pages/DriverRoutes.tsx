import React, { useState, useEffect } from 'react';
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
} from 'lucide-react';
import { routesApi, RouteItem } from '../services/routes';
import { useAuth } from '../context/AuthContext';
import { Toast } from '../components/Toast';

export const DriverRoutes: React.FC = () => {
  const { user } = useAuth();
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fetchRoutes = async () => {
    try {
      setLoading(true);
      const res = await routesApi.listRoutes();
      setRoutes(res.items || []);
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to load assigned routes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoutes();
  }, []);

  const filteredRoutes = routes.filter((r) => {
    if (filterStatus === 'ALL') return true;
    return r.status === filterStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'IN_PROGRESS':
      case 'STARTED':
        return <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-bold animate-pulse">IN PROGRESS</span>;
      case 'COMPLETED':
        return <span className="px-2.5 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-lg text-xs font-bold">COMPLETED</span>;
      case 'CANCELLED':
        return <span className="px-2.5 py-1 bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-lg text-xs font-bold">CANCELLED</span>;
      default:
        return <span className="px-2.5 py-1 bg-slate-800 text-slate-300 border border-slate-700 rounded-lg text-xs font-bold">PLANNED</span>;
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link to="/dashboard" className="hover:text-blue-400">
              Operations
            </Link>
            <span>/</span>
            <span className="text-emerald-400 font-semibold">Delivery Manifest</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <span className="p-2 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-glow">
              <Navigation className="w-5 h-5" />
            </span>
            Driver Routes & Manifests
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Execute scheduled routes, log live stop arrivals, deliver packages, and record delivery events.
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          {['ALL', 'PLANNED', 'IN_PROGRESS', 'COMPLETED'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg font-medium transition ${
                filterStatus === st ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Route Cards */}
      {loading ? (
        <div className="py-24 text-center text-slate-400">
          <div className="inline-block animate-spin text-3xl mb-3 text-blue-400">⟳</div>
          <p className="text-sm">Loading Assigned Routes...</p>
        </div>
      ) : filteredRoutes.length === 0 ? (
        <div className="bg-slate-900/40 p-12 text-center rounded-2xl border border-slate-800">
          <Truck className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-300">No Routes Found</h3>
          <p className="text-xs text-slate-500 mt-1">There are currently no routes matching this status filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredRoutes.map((route) => {
            const progress = route.stops_count > 0 ? Math.round((route.completed_stops_count / route.stops_count) * 100) : 0;

            return (
              <div
                key={route.id}
                className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between space-y-4 shadow-sm"
              >
                <div className="space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[11px] font-mono text-slate-500 block uppercase tracking-wider">{route.id}</span>
                      <h3 className="text-base font-bold text-slate-100">{route.name || `Route #${route.id}`}</h3>
                    </div>
                    {getStatusBadge(route.status)}
                  </div>

                  {/* Details */}
                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
                    <div className="flex items-center gap-2">
                      <Truck className="w-3.5 h-3.5 text-indigo-400" />
                      <span>{route.vehicle_number || 'Fleet Vehicle'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                      <span>{route.warehouse_name || 'Depot Hub'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-3.5 h-3.5 text-blue-400" />
                      <span>{route.total_distance} km</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5 text-amber-400" />
                      <span>{route.estimated_duration} min</span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Delivery Stops</span>
                      <span className="font-mono font-semibold text-slate-200">
                        {route.completed_stops_count} / {route.stops_count} ({progress}%)
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-emerald-400 transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Open Cockpit Button */}
                <Link
                  to={`/driver/routes/${route.id}`}
                  className="flex items-center justify-center gap-2 w-full py-2.5 bg-blue-600/90 hover:bg-blue-600 text-white font-bold text-xs rounded-xl shadow-md transition"
                >
                  <span>Open Route Cockpit</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            );
          })}
        </div>
      )}

      {toastMessage && <Toast message={toastMessage} onClose={() => setToastMessage(null)} />}
    </div>
  );
};
