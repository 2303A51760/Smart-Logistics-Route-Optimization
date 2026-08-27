import React from 'react';
import { Marker, Popup } from 'react-leaflet';
import { Link } from 'react-router-dom';
import { MapOrder } from '../../services/map';
import { getOrderIcon } from './mapIcons';

export interface OrderMarkerProps {
  order: MapOrder;
  onSelect?: (order: MapOrder) => void;
}

export const OrderMarker: React.FC<OrderMarkerProps> = ({ order, onSelect }) => {
  // Coordinate bounds verification on delivery position
  if (
    typeof order.delivery_latitude !== 'number' ||
    typeof order.delivery_longitude !== 'number' ||
    isNaN(order.delivery_latitude) ||
    isNaN(order.delivery_longitude) ||
    order.delivery_latitude < -90 ||
    order.delivery_latitude > 90 ||
    order.delivery_longitude < -180 ||
    order.delivery_longitude > 180
  ) {
    return null;
  }

  const icon = getOrderIcon(order.status, order.priority);

  return (
    <Marker
      position={[order.delivery_latitude, order.delivery_longitude]}
      icon={icon}
      eventHandlers={{
        click: () => onSelect && onSelect(order),
      }}
    >
      <Popup className="custom-leaflet-popup">
        <div className="p-2 space-y-1.5 min-w-[210px] text-xs text-slate-800">
          <div className="flex justify-between items-center border-b pb-1">
            <strong className="text-sm text-blue-900 font-bold">#{order.order_number}</strong>
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 font-bold">
              {order.priority}
            </span>
          </div>
          <div>
            <span className="text-slate-500">Customer:</span>{' '}
            <strong className="text-slate-900">{order.customer_name}</strong>
          </div>
          {order.delivery_address && (
            <div>
              <span className="text-slate-500">Address:</span> {order.delivery_address}
            </div>
          )}
          <div>
            <span className="text-slate-500">Package Weight:</span>{' '}
            <strong>{order.package_weight} kg</strong>
          </div>
          <div>
            <span className="text-slate-500">Status:</span>{' '}
            <span className="font-semibold text-blue-700">{order.status.replace(/_/g, ' ')}</span>
          </div>
          <div>
            <span className="text-slate-500">Assigned Driver:</span>{' '}
            <span className="text-slate-700">
              {order.assigned_driver_name ? `🚗 ${order.assigned_driver_name}` : 'Unassigned'}
            </span>
          </div>
          <div className="pt-1 border-t flex justify-end">
            <Link
              to={`/orders/${order.id}`}
              className="text-blue-600 hover:text-blue-800 font-bold text-[11px]"
            >
              Open Full Order Details &rarr;
            </Link>
          </div>
        </div>
      </Popup>
    </Marker>
  );
};
