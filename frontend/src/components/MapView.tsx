import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { Vehicle, Route, DeliveryPoint } from '../types';

interface MapViewProps {
  vehicles: Vehicle[];
  routes: Route[];
  deliveries: DeliveryPoint[];
}

// Custom vehicle SVG icon
const createVehicleIcon = (status: string) => {
  const color = status === 'EN_ROUTE' ? '#22c55e' : status === 'IDLE' ? '#3b82f6' : '#94a3b8';
  return L.divIcon({
    className: 'custom-vehicle-marker',
    html: `
      <div style="background-color: ${color}; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px ${color}; border: 2px solid white;">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <rect width="16" height="12" x="1" y="3" rx="2"/><path d="M17 8h4l3 5v6h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>
        </svg>
      </div>
    `,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
};

// Custom delivery stop SVG icon
const createDeliveryIcon = (priority: number) => {
  const color = priority === 3 ? '#ef4444' : priority === 2 ? '#f59e0b' : '#06b6d4';
  return L.divIcon({
    className: 'custom-delivery-marker',
    html: `
      <div style="background-color: ${color}; width: 22px; height: 22px; border-radius: 6px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 8px ${color}; border: 2px solid white;">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>
        </svg>
      </div>
    `,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
};

export const MapView: React.FC<MapViewProps> = ({ vehicles, routes, deliveries }) => {
  const centerLat = vehicles.length ? vehicles[0].current_lat : 40.7128;
  const centerLng = vehicles.length ? vehicles[0].current_lng : -74.0060;

  return (
    <div className="h-[480px] w-full rounded-2xl overflow-hidden border border-slate-800 relative bg-slate-900">
      <MapContainer
        center={[centerLat, centerLng]}
        zoom={13}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        {/* OpenStreetMap Tile Layer */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Vehicle Markers */}
        {vehicles.map((v) => (
          <Marker
            key={v.id}
            position={[v.current_lat, v.current_lng]}
            icon={createVehicleIcon(v.status)}
          >
            <Popup>
              <div className="p-1 text-slate-100 text-xs">
                <div className="font-bold text-sm text-emerald-400 mb-1">{v.name}</div>
                <div className="text-slate-300">Plate: <span className="font-mono text-white">{v.license_plate}</span></div>
                <div className="text-slate-300">Status: <span className="font-semibold text-emerald-300">{v.status}</span></div>
                <div className="text-slate-300">Capacity: {v.capacity_kg} kg</div>
                <div className="text-slate-300">Fuel/Battery: {v.fuel_level_percent}%</div>
                {v.speed_kmh && <div className="text-slate-300">Speed: {v.speed_kmh} km/h</div>}
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Delivery Points */}
        {deliveries.map((d) => (
          <Marker
            key={d.id}
            position={[d.lat, d.lng]}
            icon={createDeliveryIcon(d.priority)}
          >
            <Popup>
              <div className="p-1 text-slate-100 text-xs">
                <div className="font-bold text-sm text-amber-400 mb-1">{d.customer_name}</div>
                <div className="text-slate-300">Order: <span className="font-mono text-white">{d.order_id}</span></div>
                <div className="text-slate-300">Address: {d.address}</div>
                <div className="text-slate-300">Weight: {d.demand_weight_kg} kg</div>
                <div className="text-slate-300">Priority: {d.priority === 3 ? 'Urgent' : d.priority === 2 ? 'High' : 'Normal'}</div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Route Polylines */}
        {routes.map((r) => {
          if (!r.waypoints_json || r.waypoints_json.length < 2) return null;
          const positions: [number, number][] = r.waypoints_json.map((w) => [w.lat, w.lng]);
          return (
            <Polyline
              key={r.id}
              positions={positions}
              pathOptions={{
                color: '#10b981',
                weight: 4,
                opacity: 0.8,
                dashArray: '6, 8',
              }}
            />
          );
        })}
      </MapContainer>

      {/* Map Overlay Badge */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-xl border border-slate-800 text-xs flex items-center gap-4 text-slate-300 shadow-xl">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
          <span>Vehicles ({vehicles.length})</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded bg-amber-400"></span>
          <span>Delivery Stops ({deliveries.length})</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 border-b-2 border-dashed border-emerald-400"></span>
          <span>Optimized Path</span>
        </div>
      </div>
    </div>
  );
};
