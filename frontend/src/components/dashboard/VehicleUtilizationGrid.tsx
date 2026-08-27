import React from 'react';
import { VehicleUtilizationData } from '../../services/dashboard';
import { StatusBadge } from './StatusBadge';

export interface VehicleUtilizationGridProps {
  data: VehicleUtilizationData;
}

export const VehicleUtilizationGrid: React.FC<VehicleUtilizationGridProps> = ({ data }) => {
  const summary = data.status_summary || {};

  return (
    <div className="space-y-4">
      {/* Status Capsules */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 text-center">
          <span className="text-slate-400 block text-[10px] uppercase">Available</span>
          <span className="text-lg font-bold text-emerald-400">{summary.AVAILABLE || 0}</span>
        </div>
        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 text-center">
          <span className="text-slate-400 block text-[10px] uppercase">Assigned</span>
          <span className="text-lg font-bold text-sky-400">{summary.ASSIGNED || 0}</span>
        </div>
        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 text-center">
          <span className="text-slate-400 block text-[10px] uppercase">In Transit</span>
          <span className="text-lg font-bold text-indigo-400">{summary.IN_TRANSIT || 0}</span>
        </div>
        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 text-center">
          <span className="text-slate-400 block text-[10px] uppercase">Maintenance</span>
          <span className="text-lg font-bold text-amber-400">{summary.MAINTENANCE || 0}</span>
        </div>
        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 text-center">
          <span className="text-slate-400 block text-[10px] uppercase">Inactive</span>
          <span className="text-lg font-bold text-rose-400">{summary.INACTIVE || 0}</span>
        </div>
      </div>

      {/* Fleet List */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/40 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              <th className="py-2.5 px-3">Vehicle #</th>
              <th className="py-2.5 px-3">Type</th>
              <th className="py-2.5 px-3">Driver</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3">Capacity</th>
              <th className="py-2.5 px-3">Utilization</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-xs text-slate-300">
            {data.items.map((v) => (
              <tr key={v.vehicle_id} className="hover:bg-slate-800/40 transition-colors">
                <td className="py-2.5 px-3 font-mono font-bold text-blue-400">{v.vehicle_number}</td>
                <td className="py-2.5 px-3 text-slate-200">{v.vehicle_type}</td>
                <td className="py-2.5 px-3 text-slate-400">
                  {v.assigned_driver_name || <span className="text-slate-600">Unassigned</span>}
                </td>
                <td className="py-2.5 px-3">
                  <StatusBadge status={v.status} size="sm" />
                </td>
                <td className="py-2.5 px-3 font-mono text-slate-300">{v.capacity} kg</td>
                <td className="py-2.5 px-3 min-w-[120px]">
                  <div className="flex items-center gap-2">
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-blue-500 h-full rounded-full"
                        style={{ width: `${Math.min(100, v.utilization_rate)}%` }}
                      />
                    </div>
                    <span className="font-mono text-[11px] text-slate-400">{v.utilization_rate}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
