import React from 'react';
import { Marker, Popup } from 'react-leaflet';
import { MapDriver } from '../../services/map';
import { getDriverIcon } from './mapIcons';

export interface DriverMarkerProps {
  driver: MapDriver;
  onSelect?: (driver: MapDriver) => void;
}

export const DriverMarker: React.FC<DriverMarkerProps> = ({ driver, onSelect }) => {
  // Coordinate bounds verification
  if (
    typeof driver.latitude !== 'number' ||
    typeof driver.longitude !== 'number' ||
    isNaN(driver.latitude) ||
    isNaN(driver.longitude) ||
    driver.latitude < -90 ||
    driver.latitude > 90 ||
    driver.longitude < -180 ||
    driver.longitude > 180
  ) {
    return null;
  }

  const icon = getDriverIcon(driver.status);

  return (
    <Marker
      position={[driver.latitude, driver.longitude]}
      icon={icon}
      eventHandlers={{
        click: () => onSelect && onSelect(driver),
      }}
    >
      <Popup className="custom-leaflet-popup">
        <div className="p-2 space-y-1.5 min-w-[210px] text-xs text-slate-800">
          <div className="flex justify-between items-center border-b pb-1">
            <strong className="text-sm text-slate-900 font-bold">🧑‍✈️ {driver.name}</strong>
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 font-mono font-bold">
              {driver.status}
            </span>
          </div>
          <div>
            <span className="text-slate-500">License:</span>{' '}
            <strong className="font-mono">{driver.license_number}</strong>
          </div>
          <div>
            <span className="text-slate-500">Phone:</span> {driver.phone}
          </div>
          <div>
            <span className="text-slate-500">Vehicle:</span>{' '}
            <span className="text-emerald-700 font-semibold">
              {driver.vehicle_number ? `🚛 ${driver.vehicle_number} (${driver.vehicle_type || 'VAN'})` : 'Assigned Fleet'}
            </span>
          </div>
          {driver.speed !== undefined && driver.speed !== null && (
            <div className="flex justify-between items-center text-slate-600 bg-slate-50 px-1.5 py-0.5 rounded">
              <span>Speed: <strong>{driver.speed} km/h</strong></span>
              {driver.heading !== undefined && driver.heading !== null && (
                <span>Heading: <strong>{Math.round(driver.heading)}°</strong></span>
              )}
            </div>
          )}
          <div className="text-[10px] text-slate-400 font-mono pt-1 border-t flex justify-between">
            <span>GPS: {driver.latitude.toFixed(4)}, {driver.longitude.toFixed(4)}</span>
            {driver.last_updated && (
              <span>{new Date(driver.last_updated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
            )}
          </div>
        </div>
      </Popup>
    </Marker>
  );
};

