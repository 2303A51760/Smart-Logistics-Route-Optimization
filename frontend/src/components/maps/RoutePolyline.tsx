import React from 'react';
import { Polyline } from 'react-leaflet';

export interface RoutePolylineProps {
  positions: [number, number][];
  color?: string;
  weight?: number;
  opacity?: number;
  dashArray?: string;
}

export const RoutePolyline: React.FC<RoutePolylineProps> = ({
  positions,
  color = '#3b82f6',
  weight = 3,
  opacity = 0.8,
  dashArray = '6, 8',
}) => {
  const validPositions = positions.filter(
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

  if (validPositions.length < 2) return null;

  return (
    <Polyline
      positions={validPositions}
      pathOptions={{
        color,
        weight,
        opacity,
        dashArray,
      }}
    />
  );
};
