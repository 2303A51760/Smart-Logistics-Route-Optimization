import React, { useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

export interface MapViewProps {
  center?: [number, number];
  zoom?: number;
  bounds?: [number, number][];
  children?: React.ReactNode;
  height?: string;
  className?: string;
  autoFit?: boolean;
}

// Sub-component to dynamically adjust map view bounds
const AutoFitBounds: React.FC<{ bounds?: [number, number][]; center?: [number, number]; zoom?: number }> = ({
  bounds,
  center,
  zoom,
}) => {
  const map = useMap();

  useEffect(() => {
    if (bounds && bounds.length > 1) {
      const validBounds = bounds.filter(
        ([lat, lng]) =>
          typeof lat === 'number' &&
          typeof lng === 'number' &&
          !isNaN(lat) &&
          !isNaN(lng) &&
          lat >= -90 &&
          lat <= 90 &&
          lng >= -180 &&
          lng <= 180
      );
      if (validBounds.length > 1) {
        const leafletBounds = L.latLngBounds(validBounds.map(([lat, lng]) => [lat, lng]));
        map.fitBounds(leafletBounds, { padding: [40, 40], maxZoom: 15 });
      } else if (validBounds.length === 1) {
        map.setView(validBounds[0], zoom || 13);
      }
    } else if (center) {
      map.setView(center, zoom || 13);
    }
  }, [bounds, center, zoom, map]);

  return null;
};

export const MapView: React.FC<MapViewProps> = ({
  center = [40.73061, -73.935242], // Default NYC
  zoom = 12,
  bounds,
  children,
  height = '500px',
  className = '',
  autoFit = true,
}) => {
  // Validate center
  const safeCenter: [number, number] =
    typeof center[0] === 'number' &&
    typeof center[1] === 'number' &&
    !isNaN(center[0]) &&
    !isNaN(center[1]) &&
    center[0] >= -90 &&
    center[0] <= 90 &&
    center[1] >= -180 &&
    center[1] <= 180
      ? center
      : [40.73061, -73.935242];

  return (
    <div
      style={{ height, width: '100%' }}
      className={`rounded-2xl overflow-hidden border border-slate-800 shadow-2xl relative z-0 ${className}`}
    >
      <MapContainer
        center={safeCenter}
        zoom={zoom}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%', backgroundColor: '#0f172a' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        {autoFit && <AutoFitBounds bounds={bounds} center={safeCenter} zoom={zoom} />}

        {children}
      </MapContainer>
    </div>
  );
};
