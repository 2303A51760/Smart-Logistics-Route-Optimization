import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { logisticsApi } from '../services/logistics';
import { etaApi, ETAPredictResponse } from '../services/eta';
import { Order, OrderStatus, OrderPriority, Customer, Warehouse, Driver } from '../types';
import { useAuth } from '../context/AuthContext';
import { Toast } from '../components/Toast';
import { MapView } from '../components/maps/MapView';
import { WarehouseMarker } from '../components/maps/WarehouseMarker';
import { OrderMarker } from '../components/maps/OrderMarker';
import { RoutePolyline } from '../components/maps/RoutePolyline';
import { Sparkles, BrainCircuit, Clock, Zap } from 'lucide-react';

export const OrderDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { hasRole } = useAuth();

  const [order, setOrder] = useState<Order | null>(null);
  const [orderEta, setOrderEta] = useState<ETAPredictResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);


  // Edit Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [editWeight, setEditWeight] = useState('');
  const [editPriority, setEditPriority] = useState<OrderPriority>('NORMAL');
  const [editDriverId, setEditDriverId] = useState<string>('');
  const [editStatus, setEditStatus] = useState<OrderStatus>('PENDING');
  const [editSubmitting, setEditSubmitting] = useState(false);

  const fetchOrder = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const data = await logisticsApi.getOrder(id);
      setOrder(data);
      setEditWeight(data.package_weight.toString());
      setEditPriority(data.priority);
      setEditDriverId(data.assigned_driver_id || '');
      setEditStatus(data.status);

      // Fetch AI ETA
      try {
        const etaData = await etaApi.getOrderETA(id);
        setOrderEta(etaData);
      } catch {
        // non-critical
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load order details');
    } finally {
      setLoading(false);
    }
  };


  const loadAuxData = async () => {
    try {
      const [custs, whs, drvs] = await Promise.all([
        logisticsApi.getCustomers(),
        logisticsApi.getWarehouses(),
        logisticsApi.getDrivers(),
      ]);
      setCustomers(custs);
      setWarehouses(whs);
      setDrivers(drvs);
    } catch {
      // aux data load failure
    }
  };

  useEffect(() => {
    fetchOrder();
    if (hasRole(['ADMIN', 'LOGISTICS_MANAGER'])) {
      loadAuxData();
    }
  }, [id]);

  const handleStatusChange = async (newStatus: OrderStatus) => {
    if (!id) return;
    try {
      setUpdatingStatus(true);
      const updated = await logisticsApi.updateOrder(id, { status: newStatus });
      setOrder(updated);
      setToastMessage(`Order status updated to ${newStatus.replace(/_/g, ' ')}`);
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to update order status');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      setEditSubmitting(true);
      const updated = await logisticsApi.updateOrder(id, {
        package_weight: parseFloat(editWeight),
        priority: editPriority,
        assigned_driver_id: editDriverId || null,
        status: editStatus,
      });
      setOrder(updated);
      setShowEditModal(false);
      setToastMessage('Order details updated successfully!');
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to update order');
    } finally {
      setEditSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!id || !window.confirm('Are you sure you want to delete this order?')) return;
    try {
      await logisticsApi.deleteOrder(id);
      navigate('/orders');
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to delete order');
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-400">
        <div className="inline-block animate-spin text-3xl mb-3">⟳</div>
        <p className="text-sm">Loading order details...</p>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="bg-slate-900/60 p-8 rounded-2xl border border-slate-800 text-center max-w-lg mx-auto">
        <div className="text-4xl mb-3">⚠️</div>
        <h2 className="text-lg font-bold text-slate-100 mb-2">Order Not Available</h2>
        <p className="text-sm text-slate-400 mb-6">{error || 'Order record not found.'}</p>
        <Link
          to="/orders"
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-xl"
        >
          ← Back to Orders
        </Link>
      </div>
    );
  }

  const orderBounds: [number, number][] = [
    [order.pickup_latitude, order.pickup_longitude],
    [order.delivery_latitude, order.delivery_longitude],
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link to="/orders" className="hover:text-blue-400">
              Orders
            </Link>
            <span>/</span>
            <span className="font-mono text-slate-200">{order.order_number}</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <span>📦</span> Order #{order.order_number}
          </h1>
        </div>

        <div className="flex items-center gap-2">
          {hasRole(['ADMIN', 'LOGISTICS_MANAGER']) && (
            <>
              <button
                onClick={() => setShowEditModal(true)}
                className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-colors"
              >
                ✏️ Edit Order
              </button>
              <button
                onClick={handleDelete}
                className="px-3.5 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-semibold rounded-xl border border-rose-500/20 transition-colors"
              >
                🗑 Delete
              </button>
            </>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left 2 Cols: Order Details & Interactive Route Map */}
        <div className="md:col-span-2 space-y-6">
          {/* Status Timeline Card */}
          <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Delivery Status</h2>
              <span className="px-3 py-1 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-full text-xs font-semibold">
                {order.status.replace(/_/g, ' ')}
              </span>
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              {(['PENDING', 'ASSIGNED', 'OUT_FOR_DELIVERY', 'ARRIVED', 'DELIVERED', 'FAILED'] as OrderStatus[]).map(
                (st) => (
                  <button
                    key={st}
                    disabled={updatingStatus || order.status === st}
                    onClick={() => handleStatusChange(st)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border ${
                      order.status === st
                        ? 'bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-500/20'
                        : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                    }`}
                  >
                    {st.replace(/_/g, ' ')}
                  </button>
                )
              )}
            </div>
          </div>

          {/* Embedded Interactive Route Map */}
          <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex justify-between items-center">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                Geographic Waypoint Map
              </h2>
              <span className="text-[11px] text-slate-400 font-mono">
                Direct Leg Vector (Road routing enabled in Phase 5)
              </span>
            </div>

            <MapView height="320px" bounds={orderBounds} autoFit={true}>
              <WarehouseMarker
                warehouse={{
                  id: order.warehouse_id,
                  name: order.warehouse_name || 'Pickup Hub',
                  address: 'Warehouse Storage Hub',
                  latitude: order.pickup_latitude,
                  longitude: order.pickup_longitude,
                  capacity: 20000,
                }}
              />
              <OrderMarker
                order={{
                  id: order.id,
                  order_number: order.order_number,
                  customer_name: order.customer_name || 'Delivery Client',
                  pickup_latitude: order.pickup_latitude,
                  pickup_longitude: order.pickup_longitude,
                  delivery_latitude: order.delivery_latitude,
                  delivery_longitude: order.delivery_longitude,
                  priority: order.priority,
                  status: order.status,
                  package_weight: order.package_weight,
                  assigned_driver_id: order.assigned_driver_id,
                  assigned_driver_name: order.assigned_driver_name,
                }}
              />
              <RoutePolyline
                positions={[
                  [order.pickup_latitude, order.pickup_longitude],
                  [order.delivery_latitude, order.delivery_longitude],
                ]}
                color="#3b82f6"
                weight={3}
                dashArray="6, 8"
              />
            </MapView>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-2">
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                <span className="text-indigo-400 font-semibold block mb-0.5">🏢 Pickup Warehouse</span>
                <span className="text-slate-200 font-bold">{order.warehouse_name}</span>
                <p className="font-mono text-[10px] text-slate-500 mt-1">
                  {order.pickup_latitude.toFixed(4)}, {order.pickup_longitude.toFixed(4)}
                </p>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                <span className="text-emerald-400 font-semibold block mb-0.5">📍 Delivery Destination</span>
                <span className="text-slate-200 font-bold">{order.customer_name}</span>
                <p className="font-mono text-[10px] text-slate-500 mt-1">
                  {order.delivery_latitude.toFixed(4)}, {order.delivery_longitude.toFixed(4)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Specs & Participants */}
        <div className="space-y-6">
          {/* Phase 8: AI ETA Prediction Card */}
          {orderEta && (
            <div className="bg-gradient-to-r from-slate-900 via-indigo-950/30 to-purple-950/20 p-6 rounded-2xl border border-indigo-500/40 space-y-3 text-xs shadow-lg">
              <div className="flex justify-between items-center border-b border-indigo-500/20 pb-2">
                <span className="flex items-center gap-1.5 text-indigo-400 font-bold text-[11px] uppercase tracking-wider">
                  <BrainCircuit className="w-3.5 h-3.5" /> AI ETA Prediction
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                  {orderEta.source === 'ML' ? 'AI MODEL' : 'FALLBACK'}
                </span>
              </div>

              <div className="flex justify-between items-baseline">
                <span className="text-slate-400">Predicted Duration:</span>
                <span className="text-xl font-bold font-mono text-indigo-300">
                  {orderEta.predicted_duration_minutes} min
                </span>
              </div>

              <div className="flex justify-between items-baseline">
                <span className="text-slate-400">Estimated Arrival:</span>
                <span className="font-semibold text-slate-200">
                  {new Date(orderEta.estimated_arrival).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>

              <div className="pt-2 border-t border-indigo-500/20 flex justify-between text-[10px] text-slate-500 font-mono">
                <span>Confidence: ±{((orderEta.confidence_interval_max || orderEta.predicted_duration_minutes) - orderEta.predicted_duration_minutes).toFixed(1)}m</span>
                <span>{orderEta.model_version}</span>
              </div>
            </div>
          )}

          {/* Order Specs */}
          <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-3 text-xs">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3">Specifications</h2>

            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Package Weight:</span>
              <span className="font-semibold text-slate-200">{order.package_weight} kg</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Priority Level:</span>
              <span className="font-semibold text-amber-400">{order.priority}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Created At:</span>
              <span className="text-slate-300">{new Date(order.created_at).toLocaleString()}</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-400">Last Updated:</span>
              <span className="text-slate-300">{new Date(order.updated_at).toLocaleString()}</span>
            </div>
          </div>

          {/* Assigned Driver Card */}
          <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Assigned Driver</h2>
            {order.assigned_driver_name ? (
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 text-xs space-y-1">
                <p className="font-bold text-slate-200">🚗 {order.assigned_driver_name}</p>
                <p className="text-slate-400">ID: {order.assigned_driver_id}</p>
                {hasRole(['ADMIN', 'LOGISTICS_MANAGER']) && order.assigned_driver_id && (
                  <Link
                    to={`/drivers/${order.assigned_driver_id}`}
                    className="inline-block text-blue-400 hover:underline text-[11px] pt-1"
                  >
                    View Driver Profile →
                  </Link>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No driver assigned yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Edit Order Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-100">Edit Order #{order.order_number}</h2>
              <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Package Weight (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={editWeight}
                  onChange={(e) => setEditWeight(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Priority</label>
                <select
                  value={editPriority}
                  onChange={(e) => setEditPriority(e.target.value as OrderPriority)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                >
                  <option value="LOW">LOW</option>
                  <option value="NORMAL">NORMAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="URGENT">URGENT</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Status</label>
                <select
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value as OrderStatus)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                >
                  <option value="PENDING">PENDING</option>
                  <option value="ASSIGNED">ASSIGNED</option>
                  <option value="OUT_FOR_DELIVERY">OUT FOR DELIVERY</option>
                  <option value="ARRIVED">ARRIVED</option>
                  <option value="DELIVERED">DELIVERED</option>
                  <option value="FAILED">FAILED</option>
                  <option value="CANCELLED">CANCELLED</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Assigned Driver</label>
                <select
                  value={editDriverId}
                  onChange={(e) => setEditDriverId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                >
                  <option value="">-- Unassigned --</option>
                  {drivers.map((d) => (
                    <option key={d.id} value={d.id}>
                      Driver {d.license_number} ({d.status})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editSubmitting}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/25"
                >
                  {editSubmitting ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Toast */}
      {toastMessage && <Toast message={toastMessage} onClose={() => setToastMessage(null)} />}
    </div>
  );
};
