import React from 'react';
import { Link } from 'react-router-dom';
import { DriverPerformanceData } from '../../services/dashboard';
import { StatusBadge } from './StatusBadge';

export interface DriverPerformanceTableProps {
  drivers: DriverPerformanceData[];
}

export const DriverPerformanceTable: React.FC<DriverPerformanceTableProps> = ({ drivers }) => {
  if (drivers.length === 0) {
    return (
      <div className="py-8 text-center text-slate-400 text-xs italic">
        No driver performance records available.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-800 bg-slate-950/40 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            <th className="py-3 px-4">Driver</th>
            <th className="py-3 px-4">Status</th>
            <th className="py-3 px-4">Assigned Vehicle</th>
            <th className="py-3 px-4 text-center">Assigned / Done</th>
            <th className="py-3 px-4">Completion Rate</th>
            <th className="py-3 px-4 text-right">Avg Time</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 text-xs text-slate-300">
          {drivers.map((d) => (
            <tr key={d.driver_id} className="hover:bg-slate-800/40 transition-colors">
              <td className="py-3 px-4">
                <Link
                  to={`/drivers/${d.driver_id}`}
                  className="font-semibold text-slate-100 hover:text-blue-400 transition"
                >
                  🧑‍✈️ {d.driver_name}
                </Link>
                <span className="block text-[10px] font-mono text-slate-500">{d.license_number}</span>
              </td>
              <td className="py-3 px-4">
                <StatusBadge status={d.current_status} size="sm" />
              </td>
              <td className="py-3 px-4 text-slate-400 font-mono text-xs">
                {d.assigned_vehicle ? `🚛 ${d.assigned_vehicle}` : <span className="text-slate-600">Unassigned</span>}
              </td>
              <td className="py-3 px-4 text-center font-mono">
                <span className="text-emerald-400 font-bold">{d.completed_deliveries}</span> /{' '}
                <span className="text-slate-400">{d.assigned_deliveries}</span>
              </td>
              <td className="py-3 px-4 min-w-[140px]">
                <div className="flex items-center gap-2">
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        d.completion_rate >= 90
                          ? 'bg-emerald-500'
                          : d.completion_rate >= 70
                          ? 'bg-blue-500'
                          : 'bg-amber-500'
                      }`}
                      style={{ width: `${d.completion_rate}%` }}
                    />
                  </div>
                  <span className="font-mono text-xs font-bold text-slate-200">
                    {d.completion_rate}%
                  </span>
                </div>
              </td>
              <td className="py-3 px-4 text-right font-mono text-slate-400">
                {d.average_delivery_time_min}m
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
