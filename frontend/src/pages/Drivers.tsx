import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { logisticsApi } from '../services/logistics';
import { Driver, DriverStatus } from '../types';
import { useAuth } from '../context/AuthContext';
import { Toast } from '../components/Toast';

export const Drivers: React.FC = () => {
  const { hasRole } = useAuth();
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingDriver, setEditingDriver] = useState<Driver | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  // Form State
  const [licenseNumber, setLicenseNumber] = useState('');
  const [phone, setPhone] = useState('');
  const [statusVal, setStatusVal] = useState<DriverStatus>('AVAILABLE');
  const [lat, setLat] = useState('40.7128');
  const [lng, setLng] = useState('-74.0060');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchDrivers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await logisticsApi.getDrivers();
      setDrivers(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load drivers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDrivers();
  }, []);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      setSubmitting(true);
      await logisticsApi.createDriver({
        license_number: licenseNumber,
        phone,
        status: statusVal,
        current_latitude: parseFloat(lat),
        current_longitude: parseFloat(lng),
      });
      setShowCreateModal(false);
      setToastMessage('Driver profile registered successfully!');
      setLicenseNumber('');
      setPhone('');
      fetchDrivers();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to register driver');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingDriver) return;
    try {
      setSubmitting(true);
      await logisticsApi.updateDriver(editingDriver.id, {
        license_number: licenseNumber,
        phone,
        status: statusVal,
      });
      setEditingDriver(null);
      setToastMessage('Driver profile updated successfully!');
      fetchDrivers();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to update driver');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTargetId) return;
    try {
      await logisticsApi.deleteDriver(deleteTargetId);
      setToastMessage('Driver record deleted');
      setDeleteTargetId(null);
      fetchDrivers();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to delete driver');
    }
  };

  const openEditModal = (drv: Driver) => {
    setEditingDriver(drv);
    setLicenseNumber(drv.license_number);
    setPhone(drv.phone);
    setStatusVal(drv.status);
    setFormError(null);
  };

  const getStatusBadge = (st: DriverStatus) => {
    switch (st) {
      case 'AVAILABLE':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'ASSIGNED':
      case 'IN_TRANSIT':
        return 'bg-sky-500/10 text-sky-400 border-sky-500/30';
      case 'OFF_DUTY':
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
            <span>🧑‍✈️</span> Fleet Drivers Directory
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Managing certified driver credentials, availability, and active vehicle assignments.
          </p>
        </div>
        {hasRole(['ADMIN', 'LOGISTICS_MANAGER']) && (
          <button
            onClick={() => {
              setLicenseNumber('');
              setPhone('');
              setStatusVal('AVAILABLE');
              setFormError(null);
              setShowCreateModal(true);
            }}
            className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition-all flex items-center gap-2"
          >
            <span>+</span> Add New Driver
          </button>
        )}
      </div>

      {/* Drivers Table */}
      <div className="bg-slate-900/60 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        {loading ? (
          <div className="py-20 text-center text-slate-400">
            <div className="inline-block animate-spin text-3xl mb-3">⟳</div>
            <p className="text-sm">Loading driver profiles...</p>
          </div>
        ) : error ? (
          <div className="py-12 text-center text-rose-400">
            <p>{error}</p>
          </div>
        ) : drivers.length === 0 ? (
          <div className="py-16 text-center text-slate-400">
            <div className="text-4xl mb-2">🚗</div>
            <p className="text-base font-medium text-slate-300">No driver profiles found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/40 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Driver / Account</th>
                  <th className="py-3.5 px-4">License Number</th>
                  <th className="py-3.5 px-4">Phone Number</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Assigned Vehicle</th>
                  <th className="py-3.5 px-4">Current Coordinates</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-sm text-slate-300">
                {drivers.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-medium text-slate-200">
                      <Link to={`/drivers/${d.id}`} className="text-blue-400 hover:underline">
                        {d.user_name || `Driver (${d.id})`}
                      </Link>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-300">{d.license_number}</td>
                    <td className="py-3.5 px-4 text-slate-400">{d.phone}</td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs border font-medium ${getStatusBadge(d.status)}`}>
                        {d.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {d.assigned_vehicle_number ? (
                        <span className="text-xs bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                          🚛 {d.assigned_vehicle_number}
                        </span>
                      ) : (
                        <span className="text-slate-500 text-xs italic">None</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                      {d.current_latitude?.toFixed(4)}, {d.current_longitude?.toFixed(4)}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <Link
                        to={`/drivers/${d.id}`}
                        className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition-colors"
                      >
                        Profile
                      </Link>
                      {hasRole(['ADMIN', 'LOGISTICS_MANAGER']) && (
                        <>
                          <button
                            onClick={() => openEditModal(d)}
                            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setDeleteTargetId(d.id)}
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

      {/* Create / Edit Modal */}
      {(showCreateModal || editingDriver) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-100">
                {editingDriver ? `Edit Driver ${editingDriver.license_number}` : 'Register New Driver'}
              </h2>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingDriver(null);
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

            <form onSubmit={editingDriver ? handleEditSubmit : handleCreateSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Driver License Number *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. DL-NY-90218"
                  value={licenseNumber}
                  onChange={(e) => setLicenseNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Phone Number *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. +1-917-555-0199"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Status</label>
                <select
                  value={statusVal}
                  onChange={(e) => setStatusVal(e.target.value as DriverStatus)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                >
                  <option value="AVAILABLE">AVAILABLE</option>
                  <option value="ASSIGNED">ASSIGNED</option>
                  <option value="IN_TRANSIT">IN TRANSIT</option>
                  <option value="OFF_DUTY">OFF DUTY</option>
                  <option value="INACTIVE">INACTIVE</option>
                </select>
              </div>

              {!editingDriver && (
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-slate-400 mb-1">Initial Lat</label>
                    <input
                      type="number"
                      step="0.0001"
                      value={lat}
                      onChange={(e) => setLat(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Initial Lng</label>
                    <input
                      type="number"
                      step="0.0001"
                      value={lng}
                      onChange={(e) => setLng(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 text-xs"
                    />
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingDriver(null);
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
                  {submitting ? 'Saving...' : editingDriver ? 'Update Profile' : 'Register Driver'}
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
            <h3 className="text-base font-bold text-slate-100">Delete Driver Record</h3>
            <p className="text-xs text-slate-400">
              Are you sure you want to remove this driver profile from the system?
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
