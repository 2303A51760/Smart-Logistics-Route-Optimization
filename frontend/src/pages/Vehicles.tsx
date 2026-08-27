import React, { useEffect, useState } from 'react';
import { logisticsApi } from '../services/logistics';
import { Vehicle, VehicleStatus, Driver } from '../types';
import { useAuth } from '../context/AuthContext';
import { Toast } from '../components/Toast';

export const Vehicles: React.FC = () => {
  const { hasRole } = useAuth();
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  // Form State
  const [vehicleNumber, setVehicleNumber] = useState('');
  const [vehicleType, setVehicleType] = useState('VAN');
  const [capacity, setCapacity] = useState('1200');
  const [fuelType, setFuelType] = useState('DIESEL');
  const [mileage, setMileage] = useState('0');
  const [statusVal, setStatusVal] = useState<VehicleStatus>('AVAILABLE');
  const [driverId, setDriverId] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchVehicles = async () => {
    try {
      setLoading(true);
      setError(null);
      const [vList, dList] = await Promise.all([
        logisticsApi.getVehicles(),
        logisticsApi.getDrivers(),
      ]);
      setVehicles(vList);
      setDrivers(dList);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load fleet vehicles');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVehicles();
  }, []);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    const capNum = parseFloat(capacity);
    const milNum = parseFloat(mileage);

    if (isNaN(capNum) || capNum <= 0) {
      setFormError('Capacity must be greater than 0');
      return;
    }
    if (isNaN(milNum) || milNum < 0) {
      setFormError('Mileage cannot be negative');
      return;
    }

    try {
      setSubmitting(true);
      await logisticsApi.createVehicle({
        vehicle_number: vehicleNumber,
        vehicle_type: vehicleType,
        capacity: capNum,
        fuel_type: fuelType,
        mileage: milNum,
        status: statusVal,
        driver_id: driverId || null,
      });
      setShowCreateModal(false);
      setToastMessage('Vehicle registered successfully!');
      setVehicleNumber('');
      fetchVehicles();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create vehicle');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingVehicle) return;
    const capNum = parseFloat(capacity);
    const milNum = parseFloat(mileage);

    if (isNaN(capNum) || capNum <= 0) {
      setFormError('Capacity must be greater than 0');
      return;
    }
    if (isNaN(milNum) || milNum < 0) {
      setFormError('Mileage cannot be negative');
      return;
    }

    try {
      setSubmitting(true);
      await logisticsApi.updateVehicle(editingVehicle.id, {
        vehicle_number: vehicleNumber,
        vehicle_type: vehicleType,
        capacity: capNum,
        fuel_type: fuelType,
        mileage: milNum,
        status: statusVal,
        driver_id: driverId || null,
      });
      setEditingVehicle(null);
      setToastMessage('Vehicle updated successfully!');
      fetchVehicles();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to update vehicle');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTargetId) return;
    try {
      await logisticsApi.deleteVehicle(deleteTargetId);
      setToastMessage('Vehicle removed from fleet');
      setDeleteTargetId(null);
      fetchVehicles();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to delete vehicle');
    }
  };

  const openEditModal = (v: Vehicle) => {
    setEditingVehicle(v);
    setVehicleNumber(v.vehicle_number);
    setVehicleType(v.vehicle_type);
    setCapacity(v.capacity.toString());
    setFuelType(v.fuel_type);
    setMileage(v.mileage.toString());
    setStatusVal(v.status);
    setDriverId(v.driver_id || '');
    setFormError(null);
  };

  const getStatusBadge = (st: VehicleStatus) => {
    switch (st) {
      case 'AVAILABLE':
      case 'IDLE':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'ASSIGNED':
      case 'IN_TRANSIT':
      case 'EN_ROUTE':
        return 'bg-sky-500/10 text-sky-400 border-sky-500/30';
      case 'MAINTENANCE':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <span>🚛</span> Fleet Vehicles Management
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Tracking vehicle specs, load capacity, fuel types, mileage, and driver allocations.
          </p>
        </div>
        {hasRole(['ADMIN', 'LOGISTICS_MANAGER']) && (
          <button
            onClick={() => {
              setVehicleNumber('');
              setVehicleType('VAN');
              setCapacity('1200');
              setFuelType('DIESEL');
              setMileage('0');
              setStatusVal('AVAILABLE');
              setDriverId('');
              setFormError(null);
              setShowCreateModal(true);
            }}
            className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition-all flex items-center gap-2"
          >
            <span>+</span> Register New Vehicle
          </button>
        )}
      </div>

      {/* Vehicles Table */}
      <div className="bg-slate-900/60 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        {loading ? (
          <div className="py-20 text-center text-slate-400">
            <div className="inline-block animate-spin text-3xl mb-3">⟳</div>
            <p className="text-sm">Loading fleet vehicles...</p>
          </div>
        ) : error ? (
          <div className="py-12 text-center text-rose-400">
            <p>{error}</p>
          </div>
        ) : vehicles.length === 0 ? (
          <div className="py-16 text-center text-slate-400">
            <div className="text-4xl mb-2">🚚</div>
            <p className="text-base font-medium text-slate-300">No vehicles registered in fleet</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/40 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Vehicle #</th>
                  <th className="py-3.5 px-4">Type</th>
                  <th className="py-3.5 px-4">Capacity (kg)</th>
                  <th className="py-3.5 px-4">Fuel Type</th>
                  <th className="py-3.5 px-4">Mileage (km)</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Assigned Driver</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-sm text-slate-300">
                {vehicles.map((v) => (
                  <tr key={v.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-blue-400">
                      {v.vehicle_number}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-200">{v.vehicle_type}</td>
                    <td className="py-3.5 px-4">{v.capacity} kg</td>
                    <td className="py-3.5 px-4 text-xs font-semibold text-slate-400">
                      <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                        {v.fuel_type}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300 font-mono text-xs">
                      {v.mileage.toLocaleString()} km
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs border font-medium ${getStatusBadge(v.status)}`}>
                        {v.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-xs">
                      {v.assigned_driver_name ? (
                        <span className="text-emerald-400 font-semibold">
                          🚗 {v.assigned_driver_name}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      {hasRole(['ADMIN', 'LOGISTICS_MANAGER']) && (
                        <>
                          <a
                            href="/maintenance"
                            className="px-2.5 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-xs font-medium rounded-lg border border-amber-500/20 transition-colors inline-block"
                          >
                            🔧 Maintenance
                          </a>
                          <button
                            onClick={() => openEditModal(v)}
                            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setDeleteTargetId(v.id)}
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

      {/* Create / Edit Vehicle Modal */}
      {(showCreateModal || editingVehicle) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-100">
                {editingVehicle ? `Edit Vehicle ${editingVehicle.vehicle_number}` : 'Register New Vehicle'}
              </h2>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingVehicle(null);
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

            <form onSubmit={editingVehicle ? handleEditSubmit : handleCreateSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Vehicle License / Tag Number *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. VH-981-TR"
                  value={vehicleNumber}
                  onChange={(e) => setVehicleNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-400 mb-1">Vehicle Type</label>
                  <select
                    value={vehicleType}
                    onChange={(e) => setVehicleType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                  >
                    <option value="VAN">VAN</option>
                    <option value="TRUCK">TRUCK</option>
                    <option value="EV_VAN">EV VAN</option>
                    <option value="BIKE">CARGO BIKE</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Fuel Type</label>
                  <select
                    value={fuelType}
                    onChange={(e) => setFuelType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                  >
                    <option value="DIESEL">DIESEL</option>
                    <option value="ELECTRIC">ELECTRIC</option>
                    <option value="PETROL">PETROL</option>
                    <option value="HYBRID">HYBRID</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-400 mb-1">Capacity (kg) *</label>
                  <input
                    type="number"
                    step="10"
                    required
                    value={capacity}
                    onChange={(e) => setCapacity(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Mileage (km) *</label>
                  <input
                    type="number"
                    step="10"
                    required
                    value={mileage}
                    onChange={(e) => setMileage(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-400 mb-1">Status</label>
                  <select
                    value={statusVal}
                    onChange={(e) => setStatusVal(e.target.value as VehicleStatus)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                  >
                    <option value="AVAILABLE">AVAILABLE</option>
                    <option value="ASSIGNED">ASSIGNED</option>
                    <option value="IN_TRANSIT">IN TRANSIT</option>
                    <option value="MAINTENANCE">MAINTENANCE</option>
                    <option value="INACTIVE">INACTIVE</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Assign Driver</label>
                  <select
                    value={driverId}
                    onChange={(e) => setDriverId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                  >
                    <option value="">-- None --</option>
                    {drivers.map((d) => (
                      <option key={d.id} value={d.id}>
                        Driver {d.license_number}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingVehicle(null);
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
                  {submitting ? 'Saving...' : editingVehicle ? 'Update Vehicle' : 'Register Vehicle'}
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
            <h3 className="text-base font-bold text-slate-100">Delete Vehicle</h3>
            <p className="text-xs text-slate-400">
              Are you sure you want to remove this vehicle from the active fleet directory?
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
