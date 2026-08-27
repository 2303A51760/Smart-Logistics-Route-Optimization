import React from 'react';
import { Marker, Popup } from 'react-leaflet';
import { MapWarehouse } from '../../services/map';
import { warehouseIcon } from './mapIcons';

export interface WarehouseMarkerProps {
  warehouse: MapWarehouse;
  onSelect?: (warehouse: MapWarehouse) => void;
}

export const WarehouseMarker: React.FC<WarehouseMarkerProps> = ({ warehouse, onSelect }) => {
  // Coordinate bounds verification
  if (
    typeof warehouse.latitude !== 'number' ||
    typeof warehouse.longitude !== 'number' ||
    isNaN(warehouse.latitude) ||
    isNaN(warehouse.longitude) ||
    warehouse.latitude < -90 ||
    warehouse.latitude > 90 ||
    warehouse.longitude < -180 ||
    warehouse.longitude > 180
  ) {
    return null;
  }

  return (
    <Marker
      position={[warehouse.latitude, warehouse.longitude]}
      icon={warehouseIcon}
      eventHandlers={{
        click: () => onSelect && onSelect(warehouse),
      }}
    >
      <Popup className="custom-leaflet-popup">
        <div className="p-2 space-y-1.5 min-w-[200px] text-xs text-slate-800">
          <div className="border-b pb-1">
            <strong className="text-sm text-indigo-900 font-bold flex items-center gap-1">
              🏢 {warehouse.name}
            </strong>
          </div>
          <div>
            <span className="text-slate-500">Address:</span> {warehouse.address}
          </div>
          <div>
            <span className="text-slate-500">Storage Capacity:</span>{' '}
            <strong className="text-indigo-700">{warehouse.capacity.toLocaleString()} kg</strong>
          </div>
          <div className="text-[10px] text-slate-400 font-mono pt-1 border-t">
            Coords: {warehouse.latitude.toFixed(4)}, {warehouse.longitude.toFixed(4)}
          </div>
        </div>
      </Popup>
    </Marker>
  );
};
