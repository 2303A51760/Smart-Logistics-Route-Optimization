import React from 'react';
import { Truck, MapPin, Battery, Gauge, ArrowRight } from 'lucide-react';
import { Vehicle, DeliveryPoint } from '../types';

interface FleetListProps {
  vehicles: Vehicle[];
  deliveries: DeliveryPoint[];
}

export const FleetList: React.FC<FleetListProps> = ({ vehicles, deliveries }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Fleet Vehicles Card */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Truck className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-semibold text-white">Active Fleet Telemetry</h3>
          </div>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
            {vehicles.length} Units
          </span>
        </div>

        <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
          {vehicles.map((v) => (
            <div
              key={v.id}
              className="p-3.5 rounded-xl bg-slate-850 border border-slate-800/80 hover:border-slate-700 transition flex items-center justify-between gap-4"
            >
              <div className="flex items-center gap-3">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></div>
                <div>
                  <div className="text-sm font-medium text-white">{v.name}</div>
                  <div className="text-xs text-slate-400 font-mono">
                    {v.license_plate} &bull; Cap: {v.capacity_kg}kg
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs text-slate-300">
                <div className="flex items-center gap-1">
                  <Battery className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{v.fuel_level_percent}%</span>
                </div>
                {v.speed_kmh && (
                  <div className="flex items-center gap-1">
                    <Gauge className="w-3.5 h-3.5 text-blue-400" />
                    <span>{v.speed_kmh} km/h</span>
                  </div>
                )}
                <span className="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 font-semibold text-[10px]">
                  {v.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Delivery Points Queue Card */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-semibold text-white">Delivery Order Queue</h3>
          </div>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
            {deliveries.length} Stops
          </span>
        </div>

        <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
          {deliveries.map((d) => (
            <div
              key={d.id}
              className="p-3.5 rounded-xl bg-slate-850 border border-slate-800/80 hover:border-slate-700 transition flex items-center justify-between gap-4"
            >
              <div>
                <div className="text-sm font-medium text-white flex items-center gap-2">
                  {d.customer_name}
                  <span className="text-[10px] font-mono text-slate-400">({d.order_id})</span>
                </div>
                <div className="text-xs text-slate-400 truncate max-w-[280px]">{d.address}</div>
              </div>

              <div className="flex items-center gap-3 text-xs">
                <span className="text-slate-300">{d.demand_weight_kg} kg</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                    d.priority === 3
                      ? 'bg-rose-950/80 text-rose-300 border-rose-800/60'
                      : d.priority === 2
                      ? 'bg-amber-950/80 text-amber-300 border-amber-800/60'
                      : 'bg-cyan-950/80 text-cyan-300 border-cyan-800/60'
                  }`}
                >
                  {d.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
