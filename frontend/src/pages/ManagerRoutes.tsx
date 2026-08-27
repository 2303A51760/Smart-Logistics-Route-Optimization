import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Truck,
  Navigation,
  CheckCircle2,
  Clock,
  MapPin,
  TrendingUp,
  ArrowRight,
  Filter,
  Plus,
} from 'lucide-react';
import { routesApi, RouteItem } from '../services/routes';
import { Toast } from '../components/Toast';

export const ManagerRoutes: React.FC = () => {
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
      setToastMessage(err.response?.data?.detail || 'Failed to load route tracking console');
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

  const inProgressCount = routes.filter((r) => r.status === 'IN_PROGRESS' || r.status === 'STARTED').length;
  const plannedCount = routes.filter((r) => r.status === 'PLANNED').length;
  const completedCount = routes.filter((r) => r.status === 'COMPLETED').length;

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
            <span className="text-emerald-400 font-semibold">Fleet Route Control</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <span className="p-2 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-glow">
              <Truck className="w-5 h-5" />
            </span>
            Fleet Route Dispatch & Execution Console
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Monitor real-time driver routes, stop completions, vehicle assignments, and route execution states.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/optimization"
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-xl shadow-glow transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Optimize New Routes</span>
          </Link>
        </div>
      </div>

      {/* Stats Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl">
          <span className="text-slate-400 text-xs flex items-center gap-1.5 mb-1">
            <TrendingUp className="w-3.5 h-3.5 text-blue-400" /> Total Active Routes
          </span>
          <p className="text-2xl font-bold text-slate-100">{routes.length}</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl">
          <span className="text-slate-400 text-xs flex items-center gap-1.5 mb-1">
            <Truck className="w-3.5 h-3.5 text-emerald-400" /> In-Progress Routes
          </span>
          <p className="text-2xl font-bold text-emerald-400">{inProgressCount}</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl">
          <span className="text-slate-400 text-xs flex items-center gap-1.5 mb-1">
            <Clock className="w-3.5 h-3.5 text-amber-400" /> Planned / Pending
          </span>
          <p className="text-2xl font-bold text-amber-400">{plannedCount}</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl">
          <span className="text-slate-400 text-xs flex items-center gap-1.5 mb-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" /> Completed
          </span>
          <p className="text-2xl font-bold text-indigo-400">{completedCount}</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs w-fit">
        {['ALL', 'IN_PROGRESS', 'PLANNED', 'COMPLETED'].map((st) => (
          <button
            key={st}
            onClick={() => setFilterStatus(st)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filterStatus === st ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {st.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Routes List Table / Cards */}
      {loading ? (
        <div className="py-24 text-center text-slate-400">
          <div className="inline-block animate-spin text-3xl mb-3 text-emerald-400">⟳</div>
          <p className="text-sm">Loading Fleet Routes...</p>
        </div>
      ) : filteredRoutes.length === 0 ? (
        <div className="bg-slate-900/40 p-12 text-center rounded-2xl border border-slate-800">
          <Truck className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-300">No Routes Found</h3>
          <p className="text-xs text-slate-500 mt-1">There are currently no routes matching this filter.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredRoutes.map((r) => {
            const progress = r.stops_count > 0 ? Math.round((r.completed_stops_count / r.stops_count) * 100) : 0;

            return (
              <div
                key={r.id}
                className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 hover:border-slate-700 transition flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] font-mono text-slate-500 uppercase">{r.id}</span>
                    <h3 className="text-sm font-bold text-slate-100">{r.name || `Route #${r.id}`}</h3>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        r.status === 'IN_PROGRESS'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 animate-pulse'
                          : r.status === 'COMPLETED'
                          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {r.status}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <Truck className="w-3.5 h-3.5 text-indigo-400" />
                      {r.vehicle_number || 'Fleet Vehicle'}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                      {r.warehouse_name || 'Depot Hub'}
                    </span>
                    <span>&bull;</span>
                    <span>{r.total_distance} km</span>
                    <span>&bull;</span>
                    <span>{r.estimated_duration} min</span>
                    <span>&bull;</span>
                    <span className="text-slate-300 font-medium">Driver: {r.driver_name || 'Unassigned'}</span>
                  </div>
                </div>

                {/* Progress & Action */}
                <div className="flex items-center gap-6 w-full md:w-auto justify-between md:justify-end">
                  <div className="w-40 space-y-1">
                    <div className="flex justify-between text-[11px] text-slate-400">
                      <span>Stops:</span>
                      <span className="font-mono font-bold text-slate-200">
                        {r.completed_stops_count} / {r.stops_count} ({progress}%)
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  <Link
                    to={`/driver/routes/${r.id}`}
                    className="flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold rounded-xl border border-slate-700 transition"
                  >
                    <span>View Manifest</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {toastMessage && <Toast message={toastMessage} onClose={() => setToastMessage(null)} />}
    </div>
  );
};
