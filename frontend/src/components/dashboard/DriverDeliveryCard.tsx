import React from 'react';
import { Link } from 'react-router-dom';
import { Order } from '../../types';
import { StatusBadge } from './StatusBadge';

export interface DriverDeliveryCardProps {
  order: Order;
  isNext?: boolean;
}

export const DriverDeliveryCard: React.FC<DriverDeliveryCardProps> = ({ order, isNext = false }) => {
  const getPriorityBadge = (p: string) => {
    switch (p) {
      case 'URGENT':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'HIGH':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'NORMAL':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div
      className={`p-4 rounded-2xl border transition-all ${
        isNext
          ? 'bg-gradient-to-br from-blue-950/40 via-slate-900 to-slate-900 border-blue-500/40 shadow-lg shadow-blue-500/10 ring-1 ring-blue-500/20'
          : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700'
      }`}
    >
      <div className="flex justify-between items-start gap-2 mb-3">
        <div className="flex items-center gap-2">
          {isNext && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-blue-500 text-white animate-pulse">
              NEXT STOP
            </span>
          )}
          <span className="font-mono font-bold text-sm text-slate-100">#{order.order_number}</span>
          <span className={`px-2 py-0.5 rounded text-[10px] border font-semibold ${getPriorityBadge(order.priority)}`}>
            {order.priority}
          </span>
        </div>
        <StatusBadge status={order.status} size="sm" />
      </div>

      <div className="space-y-1.5 text-xs">
        <div className="flex items-center gap-2 text-slate-200 font-semibold">
          <span>🏢</span>
          <span>{order.customer_name || 'Client Delivery'}</span>
        </div>
        <div className="flex items-start gap-2 text-slate-400">
          <span className="mt-0.5">📍</span>
          <span className="text-slate-300">
            {order.delivery_latitude.toFixed(4)}, {order.delivery_longitude.toFixed(4)}
          </span>
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
          <span>📦 Package: <strong className="text-slate-200">{order.package_weight} kg</strong></span>
          <span>Window: <strong className="text-emerald-400">Today &bull; Expedited</strong></span>
        </div>
      </div>

      <div className="mt-3 flex justify-end">
        <Link
          to={`/orders/${order.id}`}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-colors flex items-center gap-1.5"
        >
          <span>View Waypoint Details</span> &rarr;
        </Link>
      </div>
    </div>
  );
};
