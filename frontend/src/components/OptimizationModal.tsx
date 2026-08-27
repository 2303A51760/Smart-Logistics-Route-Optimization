import React, { useState } from 'react';
import { X, Sparkles, Check, Loader2, ArrowRight } from 'lucide-react';
import { api } from '../services/api';
import { Vehicle, DeliveryPoint, OptimizationResult } from '../types';

interface OptimizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  vehicles: Vehicle[];
  deliveries: DeliveryPoint[];
  onOptimizationComplete: (result: OptimizationResult) => void;
}

export const OptimizationModal: React.FC<OptimizationModalProps> = ({
  isOpen,
  onClose,
  vehicles,
  deliveries,
  onOptimizationComplete,
}) => {
  const [selectedVehicles, setSelectedVehicles] = useState<string[]>(vehicles.map((v) => v.id));
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);

  if (!isOpen) return null;

  const handleRunOptimization = async () => {
    setLoading(true);
    try {
      const res = await api.solveOptimization({
        vehicle_ids: selectedVehicles.length ? selectedVehicles : ['veh-101', 'veh-102'],
        delivery_ids: deliveries.map((d) => d.id),
        depot_lat: 40.7128,
        depot_lng: -74.0060,
      });
      setResult(res);
      onOptimizationComplete(res);
    } catch (e) {
      console.error('Optimization failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const toggleVehicle = (id: string) => {
    if (selectedVehicles.includes(id)) {
      setSelectedVehicles(selectedVehicles.filter((v) => v !== id));
    } else {
      setSelectedVehicles([...selectedVehicles, id]);
    }
  };

  return (
    <div className="fixed inset-0 z-[1100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-2xl rounded-2xl p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Route Optimization Engine (OR-Tools)</h2>
            <p className="text-xs text-slate-400">Multi-Vehicle Capacitated Routing Problem Solver</p>
          </div>
        </div>

        {/* Fleet Selection */}
        <div className="mb-5">
          <label className="text-xs font-semibold text-slate-300 mb-2 block uppercase tracking-wider">
            Select Fleet Units to Dispatch
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {vehicles.map((v) => {
              const isSelected = selectedVehicles.includes(v.id);
              return (
                <div
                  key={v.id}
                  onClick={() => toggleVehicle(v.id)}
                  className={`p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                    isSelected
                      ? 'bg-emerald-950/40 border-emerald-500/60 text-white'
                      : 'bg-slate-850 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="text-xs">
                    <div className="font-medium text-white">{v.name}</div>
                    <div className="text-[10px] text-slate-400">{v.capacity_kg}kg cap</div>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-emerald-400" />}
                </div>
              );
            })}
          </div>
        </div>

        {/* Result View */}
        {result && (
          <div className="mb-5 p-4 rounded-xl bg-slate-850 border border-emerald-500/30">
            <div className="text-xs font-bold text-emerald-400 mb-2 flex items-center gap-1.5">
              <Check className="w-4 h-4" /> Optimization Result ({result.status})
            </div>
            <div className="grid grid-cols-3 gap-2 text-center py-2 bg-slate-900/80 rounded-lg mb-3">
              <div>
                <div className="text-xs text-slate-400">Total Distance</div>
                <div className="text-sm font-bold text-white">{result.total_distance_km} km</div>
              </div>
              <div>
                <div className="text-xs text-slate-400">Estimated Duration</div>
                <div className="text-sm font-bold text-white">{result.estimated_total_time_min} min</div>
              </div>
              <div>
                <div className="text-xs text-slate-400">Vehicles Used</div>
                <div className="text-sm font-bold text-white">{result.num_vehicles}</div>
              </div>
            </div>
            <div className="text-xs text-slate-300 max-h-32 overflow-y-auto space-y-1">
              {result.routes.map((r, i) => (
                <div key={i} className="flex items-center justify-between text-[11px] py-1 border-b border-slate-800">
                  <span className="font-mono text-emerald-300">{r.vehicle_id}</span>
                  <span>{r.stops.length} Stops ({r.distance_km} km)</span>
                  <span className="text-slate-400">{r.estimated_time_min} min ETA</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Modal Actions */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            Close
          </button>
          <button
            onClick={handleRunOptimization}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-medium text-xs transition shadow-glow disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {loading ? 'Computing VRP Solution...' : 'Run OR-Tools Solver'}
          </button>
        </div>
      </div>
    </div>
  );
};
