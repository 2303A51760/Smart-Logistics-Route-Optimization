import React from 'react';
import { Link } from 'react-router-dom';
import { DriverPerformanceData } from '../../services/dashboard';
import { StatusBadge } from './StatusBadge';

export interface ActiveDriversListProps {
  drivers: DriverPerformanceData[];
}

export const ActiveDriversList: React.FC<ActiveDriversListProps> = ({ drivers }) => {
  const activeList = drivers.filter((d) => d.current_status !== 'INACTIVE' && d.current_status !== 'OFF_DUTY');
  const displayList = activeList.length > 0 ? activeList : drivers;

  return (
    <div className="space-y-3">
      {displayList.map((d) => (
        <div
          key={d.driver_id}
          className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800 flex items-center justify-between gap-3 text-xs hover:border-slate-700 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-sm">
              🧑‍✈️
            </div>
            <div>
              <Link
                to={`/drivers/${d.driver_id}`}
                className="font-bold text-slate-100 hover:text-blue-400 block"
              >
                {d.driver_name}
              </Link>
              <span className="text-[10px] text-slate-400 font-mono">
                {d.assigned_vehicle ? `🚛 ${d.assigned_vehicle}` : 'No vehicle'} &bull;{' '}
                {d.current_latitude && d.current_longitude
                  ? `${d.current_latitude.toFixed(2)}, ${d.current_longitude.toFixed(2)}`
                  : 'GPS Idle'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-emerald-400 font-bold block">{d.completed_deliveries} Done</span>
              <span className="text-[10px] text-slate-500">{d.assigned_deliveries} Assigned</span>
            </div>
            <StatusBadge status={d.current_status} size="sm" />
          </div>
        </div>
      ))}
    </div>
  );
};
