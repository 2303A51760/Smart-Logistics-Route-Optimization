import React from 'react';

export interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status.toUpperCase().replace(/\s+/g, '_');

  const getStyle = () => {
    switch (normalized) {
      case 'DELIVERED':
      case 'COMPLETED':
      case 'AVAILABLE':
      case 'IDLE':
      case 'HEALTHY':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'OUT_FOR_DELIVERY':
      case 'IN_TRANSIT':
      case 'EN_ROUTE':
      case 'ASSIGNED':
        return 'bg-sky-500/10 text-sky-400 border-sky-500/30';
      case 'PENDING':
      case 'ARRIVED':
      case 'OFF_DUTY':
      case 'MAINTENANCE':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'FAILED':
      case 'CANCELLED':
      case 'INACTIVE':
      case 'OFFLINE':
      case 'DEGRADED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  const pad = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-0.5 text-xs';

  return (
    <span className={`inline-flex items-center font-medium rounded-full border ${pad} ${getStyle()}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
};
