import React from 'react';
import { Link } from 'react-router-dom';
import { MapDriver, MapWarehouse, MapOrder } from '../../services/map';

export type SelectedEntity =
  | { type: 'DRIVER'; data: MapDriver }
  | { type: 'WAREHOUSE'; data: MapWarehouse }
  | { type: 'ORDER'; data: MapOrder }
  | null;

export const SelectedEntityCard: React.FC<{
  entity: SelectedEntity;
  onClose: () => void;
}> = ({ entity, onClose }) => {
  if (!entity) return null;

  return (
    <div className="bg-slate-900/95 border border-blue-500/40 p-4 rounded-2xl backdrop-blur-xl shadow-2xl space-y-3 relative text-xs">
      <button
        onClick={onClose}
        className="absolute top-3 right-3 text-slate-400 hover:text-white text-sm"
      >
        ✕
      </button>

      {entity.type === 'DRIVER' && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xl">🧑‍✈️</span>
            <div>
              <h3 className="font-bold text-slate-100 text-sm">{entity.data.name}</h3>
              <p className="text-[11px] text-slate-400">
                License: <strong className="font-mono text-slate-300">{entity.data.license_number}</strong>
              </p>
            </div>
            <span className="ml-auto mr-6 px-2 py-0.5 rounded-full text-[10px] bg-blue-500/20 text-blue-300 border border-blue-500/40 font-bold">
              {entity.data.status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-2 border-t border-slate-800">
            <div>Phone: <strong className="text-slate-200">{entity.data.phone}</strong></div>
            <div>Vehicle: <strong className="text-emerald-400">{entity.data.vehicle_number || 'None'}</strong></div>
            <div className="col-span-2 font-mono text-[10px]">
              Coords: {entity.data.latitude.toFixed(4)}, {entity.data.longitude.toFixed(4)}
            </div>
          </div>

          <div className="pt-1 flex justify-end">
            <Link
              to={`/drivers/${entity.data.id}`}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg text-xs"
            >
              View Full Profile &rarr;
            </Link>
          </div>
        </div>
      )}

      {entity.type === 'WAREHOUSE' && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xl">🏢</span>
            <div>
              <h3 className="font-bold text-slate-100 text-sm">{entity.data.name}</h3>
              <p className="text-[11px] text-slate-400">{entity.data.address}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-2 border-t border-slate-800">
            <div>Storage Capacity: <strong className="text-indigo-300">{entity.data.capacity.toLocaleString()} kg</strong></div>
            <div className="font-mono text-[10px]">
              Coords: {entity.data.latitude.toFixed(4)}, {entity.data.longitude.toFixed(4)}
            </div>
          </div>

          <div className="pt-1 flex justify-end">
            <Link
              to="/warehouses"
              className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg text-xs"
            >
              Manage Warehouses &rarr;
            </Link>
          </div>
        </div>
      )}

      {entity.type === 'ORDER' && (
        <div className="space-y-2">
          <div className="flex items-center justify-between mr-6">
            <div className="flex items-center gap-2">
              <span className="text-xl">📦</span>
              <div>
                <h3 className="font-bold text-slate-100 text-sm">#{entity.data.order_number}</h3>
                <p className="text-[11px] text-slate-400">{entity.data.customer_name}</p>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-blue-500/20 text-blue-300 border border-blue-500/40 font-bold">
              {entity.data.status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-2 border-t border-slate-800">
            <div>Weight: <strong className="text-slate-200">{entity.data.package_weight} kg</strong></div>
            <div>Priority: <strong className="text-amber-400">{entity.data.priority}</strong></div>
            <div className="col-span-2">
              Driver: <strong className="text-emerald-400">{entity.data.assigned_driver_name || 'Unassigned'}</strong>
            </div>
            {entity.data.delivery_address && (
              <div className="col-span-2 text-slate-400 text-[10px]">
                📍 {entity.data.delivery_address}
              </div>
            )}
          </div>

          <div className="pt-1 flex justify-end">
            <Link
              to={`/orders/${entity.data.id}`}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg text-xs"
            >
              Open Order Detail &rarr;
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
