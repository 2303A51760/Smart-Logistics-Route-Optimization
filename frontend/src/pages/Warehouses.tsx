import React, { useEffect, useState } from 'react';
import { logisticsApi } from '../services/logistics';
import { Warehouse } from '../types';
import { useAuth } from '../context/AuthContext';
import { Toast } from '../components/Toast';

export const Warehouses: React.FC = () => {
  const { hasRole } = useAuth();
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingWarehouse, setEditingWarehouse] = useState<Warehouse | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [latitude, setLatitude] = useState('40.7538');
  const [longitude, setLongitude] = useState('-74.0017');
  const [capacity, setCapacity] = useState('20000');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchWarehouses = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await logisticsApi.getWarehouses();
      setWarehouses(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load warehouses');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWarehouses();
  }, []);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    const latNum = parseFloat(latitude);
    const lngNum = parseFloat(longitude);
    const capNum = parseFloat(capacity);

    if (isNaN(capNum) || capNum <= 0) {
      setFormError('Capacity must be greater than 0');
      return;
    }
    if (isNaN(latNum) || latNum < -90 || latNum > 90) {
      setFormError('Latitude must be between -90 and 90');
      return;
    }
    if (isNaN(lngNum) || lngNum < -180 || lngNum > 180) {
      setFormError('Longitude must be between -180 and 180');
      return;
    }

    try {
      setSubmitting(true);
      await logisticsApi.createWarehouse({
        name,
        address,
        latitude: latNum,
        longitude: lngNum,
        capacity: capNum,
      });
      setShowCreateModal(false);
      setToastMessage('Warehouse created successfully!');
      setName('');
      setAddress('');
      fetchWarehouses();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create warehouse');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingWarehouse) return;
    const latNum = parseFloat(latitude);
    const lngNum = parseFloat(longitude);
    const capNum = parseFloat(capacity);

    if (isNaN(capNum) || capNum <= 0) {
      setFormError('Capacity must be greater than 0');
      return;
    }
    if (isNaN(latNum) || latNum < -90 || latNum > 90) {
      setFormError('Latitude must be between -90 and 90');
      return;
    }
    if (isNaN(lngNum) || lngNum < -180 || lngNum > 180) {
      setFormError('Longitude must be between -180 and 180');
      return;
    }

    try {
      setSubmitting(true);
      await logisticsApi.updateWarehouse(editingWarehouse.id, {
        name,
        address,
        latitude: latNum,
        longitude: lngNum,
        capacity: capNum,
      });
      setEditingWarehouse(null);
      setToastMessage('Warehouse updated successfully!');
      fetchWarehouses();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to update warehouse');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTargetId) return;
    try {
      await logisticsApi.deleteWarehouse(deleteTargetId);
      setToastMessage('Warehouse deleted');
      setDeleteTargetId(null);
      fetchWarehouses();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to delete warehouse');
    }
  };

  const openEditModal = (wh: Warehouse) => {
    setEditingWarehouse(wh);
    setName(wh.name);
    setAddress(wh.address);
    setLatitude(wh.latitude.toString());
    setLongitude(wh.longitude.toString());
    setCapacity(wh.capacity.toString());
    setFormError(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <span>🏬</span> Warehouses & Distribution Hubs
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Storage capacity, fulfillment depots, and central pickup points.
          </p>
        </div>
        {hasRole(['ADMIN', 'LOGISTICS_MANAGER']) && (
          <button
            onClick={() => {
              setName('');
              setAddress('');
              setLatitude('40.7538');
              setLongitude('-74.0017');
              setCapacity('20000');
              setFormError(null);
              setShowCreateModal(true);
            }}
            className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition-all flex items-center gap-2"
          >
            <span>+</span> Add New Warehouse
          </button>
        )}
      </div>

      {/* Warehouses Table */}
      <div className="bg-slate-900/60 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        {loading ? (
          <div className="py-20 text-center text-slate-400">
            <div className="inline-block animate-spin text-3xl mb-3">⟳</div>
            <p className="text-sm">Loading warehouses...</p>
          </div>
        ) : error ? (
          <div className="py-12 text-center text-rose-400">
            <p>{error}</p>
          </div>
        ) : warehouses.length === 0 ? (
          <div className="py-16 text-center text-slate-400">
            <div className="text-4xl mb-2">🏢</div>
            <p className="text-base font-medium text-slate-300">No warehouses registered</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/40 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Warehouse Name</th>
                  <th className="py-3.5 px-4">Physical Address</th>
                  <th className="py-3.5 px-4">Coordinates</th>
                  <th className="py-3.5 px-4">Capacity (kg)</th>
                  <th className="py-3.5 px-4">Active Orders</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-sm text-slate-300">
                {warehouses.map((w) => (
                  <tr key={w.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-200">
                      🏢 {w.name}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">{w.address}</td>
                    <td className="py-3.5 px-4 font-mono text-xs text-blue-400">
                      {w.latitude.toFixed(4)}, {w.longitude.toFixed(4)}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-300">
                      {w.capacity.toLocaleString()} kg
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2.5 py-0.5 rounded-full text-xs bg-blue-500/10 text-blue-400 border border-blue-500/30">
                        {w.active_orders_count || 0} orders
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      {hasRole(['ADMIN', 'LOGISTICS_MANAGER']) && (
                        <>
                          <button
                            onClick={() => openEditModal(w)}
                            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setDeleteTargetId(w.id)}
                            className="px-2.5 py-1 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-medium rounded-lg border border-rose-500/20 transition-colors"
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create / Edit Warehouse Modal */}
      {(showCreateModal || editingWarehouse) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-100">
                {editingWarehouse ? `Edit ${editingWarehouse.name}` : 'Create New Warehouse'}
              </h2>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingWarehouse(null);
                }}
                className="text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs rounded-xl">
                {formError}
              </div>
            )}

            <form onSubmit={editingWarehouse ? handleEditSubmit : handleCreateSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Warehouse Hub Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Central Depot"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Address *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 500 W 33rd St, New York, NY"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Capacity (kg) *</label>
                <input
                  type="number"
                  step="100"
                  required
                  value={capacity}
                  onChange={(e) => setCapacity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-400 mb-1">Latitude (-90 to 90) *</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Longitude (-180 to 180) *</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingWarehouse(null);
                  }}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/25"
                >
                  {submitting ? 'Saving...' : editingWarehouse ? 'Update Warehouse' : 'Create Warehouse'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {deleteTargetId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-sm w-full p-6 text-center space-y-4 shadow-2xl">
            <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto text-xl">
              🗑
            </div>
            <h3 className="text-base font-bold text-slate-100">Delete Warehouse Location</h3>
            <p className="text-xs text-slate-400">
              Are you sure you want to remove this warehouse location?
            </p>
            <div className="flex gap-3 justify-center pt-2">
              <button
                onClick={() => setDeleteTargetId(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-rose-500/25"
              >
                Yes, Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {toastMessage && <Toast message={toastMessage} onClose={() => setToastMessage(null)} />}
    </div>
  );
};
