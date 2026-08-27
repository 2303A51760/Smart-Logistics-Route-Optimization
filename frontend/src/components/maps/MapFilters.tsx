import React from 'react';

export interface MapFiltersState {
  entityType: 'ALL' | 'DRIVERS' | 'WAREHOUSES' | 'ORDERS';
  driverStatus: string;
  orderStatus: string;
  priority: string;
}

export interface MapFiltersProps {
  filters: MapFiltersState;
  onChange: (filters: MapFiltersState) => void;
  counts: {
    drivers: number;
    warehouses: number;
    orders: number;
  };
}

export const MapFilters: React.FC<MapFiltersProps> = ({ filters, onChange, counts }) => {
  return (
    <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800/80 backdrop-blur-xl space-y-3 text-xs shadow-xl">
      {/* Top Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Entity Tabs */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => onChange({ ...filters, entityType: 'ALL' })}
            className={`px-3 py-1.5 rounded-lg font-semibold transition ${
              filters.entityType === 'ALL'
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All Entities ({counts.drivers + counts.warehouses + counts.orders})
          </button>
          <button
            onClick={() => onChange({ ...filters, entityType: 'DRIVERS' })}
            className={`px-3 py-1.5 rounded-lg font-semibold transition ${
              filters.entityType === 'DRIVERS'
                ? 'bg-emerald-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            🧑‍✈️ Drivers ({counts.drivers})
          </button>
          <button
            onClick={() => onChange({ ...filters, entityType: 'WAREHOUSES' })}
            className={`px-3 py-1.5 rounded-lg font-semibold transition ${
              filters.entityType === 'WAREHOUSES'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            🏢 Warehouses ({counts.warehouses})
          </button>
          <button
            onClick={() => onChange({ ...filters, entityType: 'ORDERS' })}
            className={`px-3 py-1.5 rounded-lg font-semibold transition ${
              filters.entityType === 'ORDERS'
                ? 'bg-sky-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            📦 Orders ({counts.orders})
          </button>
        </div>

        {/* Dropdowns row */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Driver status filter */}
          {(filters.entityType === 'ALL' || filters.entityType === 'DRIVERS') && (
            <div>
              <select
                value={filters.driverStatus}
                onChange={(e) => onChange({ ...filters, driverStatus: e.target.value })}
                className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-slate-300 text-xs focus:outline-none focus:border-blue-500"
              >
                <option value="ALL">All Driver Statuses</option>
                <option value="AVAILABLE">🟢 Available</option>
                <option value="ASSIGNED">🔵 Assigned</option>
                <option value="IN_TRANSIT">🚚 In Transit</option>
                <option value="OFF_DUTY">🟡 Off Duty</option>
                <option value="INACTIVE">🔴 Inactive</option>
              </select>
            </div>
          )}

          {/* Order status filter */}
          {(filters.entityType === 'ALL' || filters.entityType === 'ORDERS') && (
            <div>
              <select
                value={filters.orderStatus}
                onChange={(e) => onChange({ ...filters, orderStatus: e.target.value })}
                className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-slate-300 text-xs focus:outline-none focus:border-blue-500"
              >
                <option value="ALL">All Order Statuses</option>
                <option value="PENDING">Pending</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="OUT_FOR_DELIVERY">Out For Delivery</option>
                <option value="ARRIVED">Arrived</option>
                <option value="DELIVERED">Delivered</option>
                <option value="FAILED">Failed</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
          )}

          {/* Priority filter */}
          {(filters.entityType === 'ALL' || filters.entityType === 'ORDERS') && (
            <div>
              <select
                value={filters.priority}
                onChange={(e) => onChange({ ...filters, priority: e.target.value })}
                className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-slate-300 text-xs focus:outline-none focus:border-blue-500"
              >
                <option value="ALL">All Priorities</option>
                <option value="LOW">Low</option>
                <option value="NORMAL">Normal</option>
                <option value="HIGH">High</option>
                <option value="URGENT">⚡ Urgent</option>
              </select>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
