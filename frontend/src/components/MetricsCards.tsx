import React from 'react';
import { Truck, MapPin, Route as RouteIcon, Clock } from 'lucide-react';
import { Vehicle, Route, DeliveryPoint } from '../types';

interface MetricsCardsProps {
  vehicles: Vehicle[];
  routes: Route[];
  deliveries: DeliveryPoint[];
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ vehicles, routes, deliveries }) => {
  const activeVehicles = vehicles.filter((v) => v.status === 'EN_ROUTE' || v.status === 'IDLE').length;
  const totalDistance = routes.reduce((acc, r) => acc + (r.total_distance_km || 0), 0);
  const pendingDeliveries = deliveries.filter((d) => d.status === 'PENDING' || d.status === 'ASSIGNED').length;
  const avgDuration = routes.length ? Math.round(routes.reduce((acc, r) => acc + (r.estimated_duration_min || 0), 0) / routes.length) : 0;

  const cards = [
    {
      title: 'Active Fleet Vehicles',
      value: `${activeVehicles} / ${vehicles.length}`,
      subtext: `${vehicles.filter((v) => v.status === 'EN_ROUTE').length} en route`,
      icon: <Truck className="w-5 h-5 text-emerald-400" />,
      color: 'border-emerald-500/20 bg-emerald-950/10',
    },
    {
      title: 'Pending Deliveries',
      value: pendingDeliveries,
      subtext: `${deliveries.length} total orders registered`,
      icon: <MapPin className="w-5 h-5 text-amber-400" />,
      color: 'border-amber-500/20 bg-amber-950/10',
    },
    {
      title: 'Total Optimized Distance',
      value: `${totalDistance.toFixed(1)} km`,
      subtext: `${routes.length} active routes dispatched`,
      icon: <RouteIcon className="w-5 h-5 text-blue-400" />,
      color: 'border-blue-500/20 bg-blue-950/10',
    },
    {
      title: 'Avg Route ETA (ML)',
      value: `${avgDuration} min`,
      subtext: 'Incorporates real-time traffic index',
      icon: <Clock className="w-5 h-5 text-purple-400" />,
      color: 'border-purple-500/20 bg-purple-950/10',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => (
        <div
          key={idx}
          className={`p-4 rounded-2xl border ${card.color} bg-slate-900/60 backdrop-blur-sm flex flex-col justify-between hover:border-slate-700 transition-all`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-slate-400">{card.title}</span>
            <div className="p-2 rounded-xl bg-slate-800 border border-slate-700/50">{card.icon}</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white tracking-tight">{card.value}</div>
            <div className="text-[11px] text-slate-400 mt-1">{card.subtext}</div>
          </div>
        </div>
      ))}
    </div>
  );
};
