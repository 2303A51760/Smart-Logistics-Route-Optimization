import React from 'react';
import { Link } from 'react-router-dom';
import { Order } from '../../types';
import { StatusBadge } from './StatusBadge';

export interface RecentOrdersTableProps {
  orders: Order[];
}

export const RecentOrdersTable: React.FC<RecentOrdersTableProps> = ({ orders }) => {
  if (orders.length === 0) {
    return (
      <div className="py-8 text-center text-slate-400 text-xs italic">
        No recent orders recorded.
      </div>
    );
  }

  const getPriorityStyle = (p: string) => {
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
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-800 bg-slate-950/40 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            <th className="py-2.5 px-3">Order #</th>
            <th className="py-2.5 px-3">Customer</th>
            <th className="py-2.5 px-3">Priority</th>
            <th className="py-2.5 px-3">Driver</th>
            <th className="py-2.5 px-3">Status</th>
            <th className="py-2.5 px-3 text-right">Created</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 text-xs text-slate-300">
          {orders.map((o) => (
            <tr key={o.id} className="hover:bg-slate-800/40 transition-colors">
              <td className="py-2.5 px-3">
                <Link
                  to={`/orders/${o.id}`}
                  className="font-mono font-bold text-blue-400 hover:underline"
                >
                  #{o.order_number}
                </Link>
              </td>
              <td className="py-2.5 px-3 font-medium text-slate-200">{o.customer_name}</td>
              <td className="py-2.5 px-3">
                <span className={`px-2 py-0.5 rounded text-[10px] border font-bold ${getPriorityStyle(o.priority)}`}>
                  {o.priority}
                </span>
              </td>
              <td className="py-2.5 px-3 text-slate-400">
                {o.assigned_driver_name ? (
                  <span className="text-emerald-400">🚗 {o.assigned_driver_name}</span>
                ) : (
                  <span className="text-slate-600 italic">Unassigned</span>
                )}
              </td>
              <td className="py-2.5 px-3">
                <StatusBadge status={o.status} size="sm" />
              </td>
              <td className="py-2.5 px-3 text-right text-slate-500 font-mono text-[11px]">
                {new Date(o.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
