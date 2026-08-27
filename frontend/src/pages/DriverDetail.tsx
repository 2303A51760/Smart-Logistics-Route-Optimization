import React, { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { logisticsApi } from '../services/logistics';
import { Driver, DriverStatus, Order } from '../types';
import { useAuth } from '../context/AuthContext';
import { Toast } from '../components/Toast';
import { MapView } from '../components/maps/MapView';
import { DriverMarker } from '../components/maps/DriverMarker';
import { OrderMarker } from '../components/maps/OrderMarker';

export const DriverDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { hasRole } = useAuth();
  const [driver, setDriver] = useState<Driver | null>(null);
  const [assignedOrders, setAssignedOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const fetchDriverData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const [drv, ordsRes] = await Promise.all([
        logisticsApi.getDriver(id),
        logisticsApi.getOrders({ driver_id: id }),
      ]);
      setDriver(drv);
      setAssignedOrders(ordsRes.items || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load driver profile');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDriverData();
  }, [id]);

  const handleStatusChange = async (newStatus: DriverStatus) => {
    if (!id) return;
    try {
      setUpdatingStatus(true);
      const updated = await logisticsApi.updateDriver(id, { status: newStatus });
      setDriver(updated);
      setToastMessage(`Driver status changed to ${newStatus.replace(/_/g, ' ')}`);
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to update status');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const mapBounds: [number, number][] = useMemo(() => {
    const coords: [number, number][] = [];
    if (driver?.current_latitude && driver?.current_longitude) {
      coords.push([driver.current_latitude, driver.current_longitude]);
    }
    assignedOrders.forEach((o) => {
      coords.push([o.delivery_latitude, o.delivery_longitude]);
    });
    return coords;
  }, [driver, assignedOrders]);

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-400">
        <div className="inline-block animate-spin text-3xl mb-3">⟳</div>
        <p className="text-sm">Loading driver profile...</p>
      </div>
    );
  }

  if (error || !driver) {
    return (
      <div className="bg-slate-900/60 p-8 rounded-2xl border border-slate-800 text-center max-w-lg mx-auto">
        <div className="text-4xl mb-3">⚠️</div>
        <h2 className="text-lg font-bold text-slate-100 mb-2">Driver Record Not Found</h2>
        <p className="text-sm text-slate-400 mb-6">{error || 'Unable to retrieve driver profile.'}</p>
        <Link
          to="/drivers"
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-xl"
        >
          ← Back to Drivers Directory
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link to="/drivers" className="hover:text-blue-400">
              Drivers Directory
            </Link>
            <span>/</span>
            <span className="font-mono text-slate-200">{driver.license_number}</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <span>🧑‍✈️</span> {driver.user_name || `Driver ${driver.license_number}`}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 font-semibold">Duty Status:</label>
          <select
            disabled={updatingStatus}
            value={driver.status}
            onChange={(e) => handleStatusChange(e.target.value as DriverStatus)}
            className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-semibold"
          >
            <option value="AVAILABLE">🟢 AVAILABLE</option>
            <option value="ASSIGNED">🔵 ASSIGNED</option>
            <option value="IN_TRANSIT">🚚 IN TRANSIT</option>
            <option value="OFF_DUTY">🟡 OFF DUTY</option>
            <option value="INACTIVE">🔴 INACTIVE</option>
          </select>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Profile Card & Info */}
        <div className="space-y-6">
          <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-4 text-xs">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Driver Credentials</h2>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">License #:</span>
              <span className="font-mono font-bold text-slate-200">{driver.license_number}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Direct Phone:</span>
              <span className="text-slate-200">{driver.phone}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Assigned Vehicle:</span>
              <span className="text-emerald-400 font-semibold">
                {driver.assigned_vehicle_number ? `🚛 ${driver.assigned_vehicle_number}` : 'None'}
              </span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-400">Database GPS:</span>
              <span className="font-mono text-slate-300">
                {driver.current_latitude?.toFixed(4)}, {driver.current_longitude?.toFixed(4)}
              </span>
            </div>
          </div>
        </div>

        {/* Assigned Orders & Active Map Preview */}
        <div className="md:col-span-2 space-y-6">
          {/* Interactive Geographic Map View */}
          <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex justify-between items-center">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                Field Position & Assigned Delivery Stops
              </h2>
              <span className="text-[11px] text-slate-400 font-mono">
                Stored DB coordinates
              </span>
            </div>

            <MapView
              height="320px"
              bounds={mapBounds.length > 0 ? mapBounds : undefined}
              center={
                driver.current_latitude && driver.current_longitude
                  ? [driver.current_latitude, driver.current_longitude]
                  : undefined
              }
              autoFit={true}
            >
              {driver.current_latitude && driver.current_longitude && (
                <DriverMarker
                  driver={{
                    id: driver.id,
                    name: driver.user_name || `Driver ${driver.license_number}`,
                    license_number: driver.license_number,
                    phone: driver.phone,
                    status: driver.status,
                    latitude: driver.current_latitude,
                    longitude: driver.current_longitude,
                    vehicle_number: driver.assigned_vehicle_number,
                    vehicle_type: 'VAN',
                  }}
                />
              )}

              {assignedOrders.map((ord) => (
                <OrderMarker
                  key={`ord-${ord.id}`}
                  order={{
                    id: ord.id,
                    order_number: ord.order_number,
                    customer_name: ord.customer_name || 'Client',
                    pickup_latitude: ord.pickup_latitude,
                    pickup_longitude: ord.pickup_longitude,
                    delivery_latitude: ord.delivery_latitude,
                    delivery_longitude: ord.delivery_longitude,
                    priority: ord.priority,
                    status: ord.status,
                    package_weight: ord.package_weight,
                    assigned_driver_id: ord.assigned_driver_id,
                    assigned_driver_name: ord.assigned_driver_name,
                  }}
                />
              ))}
            </MapView>
          </div>

          {/* Assigned Orders List */}
          <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Assigned Delivery Manifest ({assignedOrders.length})
            </h2>

            {assignedOrders.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-6 text-center">
                No delivery orders currently dispatched to this driver.
              </p>
            ) : (
              <div className="space-y-3">
                {assignedOrders.map((ord) => (
                  <div
                    key={ord.id}
                    className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex justify-between items-center text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Link to={`/orders/${ord.id}`} className="font-mono font-bold text-blue-400 hover:underline">
                          #{ord.order_number}
                        </Link>
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                          {ord.priority}
                        </span>
                      </div>
                      <p className="text-slate-400">
                        Destination: <span className="text-slate-200">{ord.customer_name}</span> ({ord.package_weight} kg)
                      </p>
                    </div>
                    <span className="px-2.5 py-1 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-lg text-xs font-medium">
                      {ord.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {toastMessage && <Toast message={toastMessage} onClose={() => setToastMessage(null)} />}
    </div>
  );
};
