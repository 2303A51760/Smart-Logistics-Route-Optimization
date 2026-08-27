import React, { useState, useEffect } from 'react';
import {
  Wrench,
  AlertTriangle,
  CheckCircle2,
  Clock,
  DollarSign,
  Plus,
  Search,
  Filter,
  Trash2,
  Edit,
  ShieldCheck,
  Activity,
  CarFront,
  ArrowUpRight,
  RefreshCw,
} from 'lucide-react';
import { maintenanceApi } from '../services/maintenance';
import { logisticsApi } from '../services/logistics';
import {
  VehicleMaintenance,
  MaintenanceVehicleDue,
  MaintenanceDashboardSummary,
  Vehicle,
  MaintenanceType,
  MaintenanceStatus,
} from '../types';
import { Toast, ToastType } from '../components/Toast';

export const MaintenanceDashboard: React.FC = () => {
  const [summary, setSummary] = useState<MaintenanceDashboardSummary | null>(null);
  const [records, setRecords] = useState<VehicleMaintenance[]>([]);
  const [vehiclesDue, setVehiclesDue] = useState<MaintenanceVehicleDue[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedVehicle, setSelectedVehicle] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  // Modal State
  const [showModal, setShowModal] = useState<boolean>(false);
  const [editingRecord, setEditingRecord] = useState<VehicleMaintenance | null>(null);
  const [formData, setFormData] = useState({
    vehicle_id: '',
    maintenance_type: 'GENERAL_INSPECTION' as MaintenanceType,
    maintenance_date: new Date().toISOString().slice(0, 10),
    mileage: 0,
    next_maintenance_mileage: 5000,
    cost: 0,
    status: 'COMPLETED' as MaintenanceStatus,
    notes: '',
  });

  const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sumData, recData, dueData, vehData] = await Promise.all([
        maintenanceApi.getDashboardSummary(),
        maintenanceApi.listMaintenance(),
        maintenanceApi.getVehiclesDue(),
        logisticsApi.getVehicles(),
      ]);
      setSummary(sumData);
      setRecords(recData);
      setVehiclesDue(dueData);
      setVehicles(vehData);
    } catch (err: any) {
      setToast({
        message: err?.response?.data?.detail || 'Failed to load maintenance records',
        type: 'error',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenAddModal = (prefillVehicleId?: string) => {
    setEditingRecord(null);
    let defaultMileage = 0;
    if (prefillVehicleId) {
      const v = vehicles.find((item) => item.id === prefillVehicleId);
      if (v) defaultMileage = v.mileage;
    }
    setFormData({
      vehicle_id: prefillVehicleId || (vehicles[0]?.id || ''),
      maintenance_type: 'OIL_CHANGE',
      maintenance_date: new Date().toISOString().slice(0, 10),
      mileage: defaultMileage,
      next_maintenance_mileage: defaultMileage + 5000,
      cost: 150,
      status: 'COMPLETED',
      notes: '',
    });
    setShowModal(true);
  };

  const handleOpenEditModal = (rec: VehicleMaintenance) => {
    setEditingRecord(rec);
    setFormData({
      vehicle_id: rec.vehicle_id,
      maintenance_type: rec.maintenance_type,
      maintenance_date: new Date(rec.maintenance_date).toISOString().slice(0, 10),
      mileage: rec.mileage,
      next_maintenance_mileage: rec.next_maintenance_mileage,
      cost: rec.cost,
      status: rec.status,
      notes: rec.notes || '',
    });
    setShowModal(true);
  };

  const handleVehicleChange = (vehId: string) => {
    const v = vehicles.find((item) => item.id === vehId);
    const currMil = v ? v.mileage : 0;
    setFormData((prev) => ({
      ...prev,
      vehicle_id: vehId,
      mileage: currMil,
      next_maintenance_mileage: currMil + 5000,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.vehicle_id) {
      setToast({ message: 'Please select a vehicle', type: 'error' });
      return;
    }
    if (formData.next_maintenance_mileage <= formData.mileage) {
      setToast({
        message: 'Next maintenance mileage must be greater than current service mileage',
        type: 'error',
      });
      return;
    }

    try {
      if (editingRecord) {
        await maintenanceApi.updateMaintenance(editingRecord.id, {
          maintenance_type: formData.maintenance_type,
          maintenance_date: new Date(formData.maintenance_date).toISOString(),
          mileage: Number(formData.mileage),
          next_maintenance_mileage: Number(formData.next_maintenance_mileage),
          cost: Number(formData.cost),
          status: formData.status,
          notes: formData.notes,
        });
        setToast({ message: 'Maintenance record updated successfully', type: 'success' });
      } else {
        await maintenanceApi.createMaintenance({
          vehicle_id: formData.vehicle_id,
          maintenance_type: formData.maintenance_type,
          maintenance_date: new Date(formData.maintenance_date).toISOString(),
          mileage: Number(formData.mileage),
          next_maintenance_mileage: Number(formData.next_maintenance_mileage),
          cost: Number(formData.cost),
          status: formData.status,
          notes: formData.notes,
        });
        setToast({ message: 'Maintenance record logged successfully', type: 'success' });
      }
      setShowModal(false);
      fetchData();
    } catch (err: any) {
      setToast({
        message: err?.response?.data?.detail || 'Failed to save maintenance record',
        type: 'error',
      });
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this maintenance record?')) return;
    try {
      await maintenanceApi.deleteMaintenance(id);
      setToast({ message: 'Maintenance record deleted', type: 'success' });
      fetchData();
    } catch (err: any) {
      setToast({ message: 'Failed to delete record', type: 'error' });
    }
  };

  // Filter records
  const filteredRecords = records.filter((r) => {
    const v = vehicles.find((item) => item.id === r.vehicle_id);
    const vNum = v ? v.vehicle_number : r.vehicle_number || '';
    const matchSearch =
      vNum.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (r.notes && r.notes.toLowerCase().includes(searchTerm.toLowerCase())) ||
      r.maintenance_type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchType = !selectedType || r.maintenance_type === selectedType;
    const matchVeh = !selectedVehicle || r.vehicle_id === selectedVehicle;
    const matchStatus = !selectedStatus || r.status === selectedStatus;
    return matchSearch && matchType && matchVeh && matchStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-emerald-950/70 text-emerald-400 border-emerald-800/60';
      case 'IN_PROGRESS':
        return 'bg-amber-950/70 text-amber-400 border-amber-800/60 animate-pulse';
      case 'SCHEDULED':
        return 'bg-blue-950/70 text-blue-400 border-blue-800/60';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'OIL_CHANGE':
        return 'bg-amber-950/50 text-amber-300 border-amber-800/40';
      case 'BRAKE_INSPECTION':
        return 'bg-rose-950/50 text-rose-300 border-rose-800/40';
      case 'ENGINE_SERVICE':
        return 'bg-purple-950/50 text-purple-300 border-purple-800/40';
      case 'BATTERY_CHECK':
        return 'bg-emerald-950/50 text-emerald-300 border-emerald-800/40';
      case 'TIRE_ROTATION':
        return 'bg-cyan-950/50 text-cyan-300 border-cyan-800/40';
      default:
        return 'bg-slate-800/80 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-amber-600 to-orange-500 text-white shadow-glow">
              <Wrench className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Vehicle Maintenance & Fleet Health
              </h1>
              <p className="text-sm text-slate-400">
                Track service intervals, mileage thresholds, preventive repairs, and health analytics
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setRefreshing(true);
              fetchData();
            }}
            className="px-3.5 py-2 rounded-xl bg-slate-850 hover:bg-slate-800 border border-slate-800 text-slate-300 text-sm font-medium flex items-center gap-2 transition"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <button
            onClick={() => handleOpenAddModal()}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-600 to-orange-500 hover:from-amber-500 hover:to-orange-400 text-white text-sm font-semibold flex items-center gap-2 shadow-glow transition transform hover:scale-[1.02]"
          >
            <Plus className="w-4 h-4" />
            Log Maintenance
          </button>
        </div>
      </div>

      {/* Overview Analytics Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Fleet Health Score */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Fleet Health Score
              </span>
              <div className="p-2 rounded-xl bg-emerald-950/60 border border-emerald-800/40 text-emerald-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                {summary.fleet_health_score}%
              </span>
              <span className="text-xs text-emerald-400 font-medium">Optimal</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full"
                style={{ width: `${summary.fleet_health_score}%` }}
              />
            </div>
          </div>

          {/* Overdue / Due Soon */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Maintenance Required
              </span>
              <div className="p-2 rounded-xl bg-rose-950/60 border border-rose-800/40 text-rose-400">
                <AlertTriangle className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-rose-400">
                {summary.vehicles_overdue_count}
              </span>
              <span className="text-xs text-slate-400">overdue</span>
              <span className="text-sm font-semibold text-amber-400 ml-2">
                +{summary.vehicles_due_soon_count}
              </span>
              <span className="text-xs text-slate-400">due soon</span>
            </div>
            <p className="text-xs text-slate-500 mt-2">Requires immediate dispatch review</p>
          </div>

          {/* Total Spend */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Maintenance Spend
              </span>
              <div className="p-2 rounded-xl bg-purple-950/60 border border-purple-800/40 text-purple-400">
                <DollarSign className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                ${summary.total_maintenance_cost.toLocaleString()}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-2">Across all recorded services</p>
          </div>

          {/* Services Logged */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Completed Services
              </span>
              <div className="p-2 rounded-xl bg-blue-950/60 border border-blue-800/40 text-blue-400">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                {summary.completed_services}
              </span>
              <span className="text-xs text-slate-400">/ {summary.total_records} total</span>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              {summary.scheduled_services} currently scheduled/in progress
            </p>
          </div>
        </div>
      )}

      {/* Overdue / Due Vehicles Alert Section */}
      {vehiclesDue.some((v) => v.is_overdue) && (
        <div className="bg-gradient-to-r from-rose-950/40 via-slate-900 to-slate-900 border border-rose-800/40 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-rose-400 animate-bounce" />
            <h2 className="text-lg font-bold text-white">
              Vehicles Exceeding Maintenance Mileage Interval
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {vehiclesDue
              .filter((v) => v.is_overdue)
              .map((due) => (
                <div
                  key={due.vehicle_id}
                  className="bg-slate-850/90 border border-rose-800/50 rounded-xl p-4 flex flex-col justify-between hover:border-rose-600 transition"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white flex items-center gap-2">
                        <CarFront className="w-4 h-4 text-rose-400" />
                        {due.vehicle_number}
                      </span>
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">
                        +{due.mileage_overdue.toFixed(0)} km OVERDUE
                      </span>
                    </div>

                    <div className="mt-3 text-xs text-slate-400 space-y-1">
                      <div className="flex justify-between">
                        <span>Current Odometer:</span>
                        <span className="font-semibold text-slate-200">
                          {due.current_mileage.toLocaleString()} km
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Service Due Threshold:</span>
                        <span className="font-semibold text-slate-200">
                          {due.next_maintenance_mileage.toLocaleString()} km
                        </span>
                      </div>
                      {due.assigned_driver_name && (
                        <div className="flex justify-between text-slate-400">
                          <span>Driver:</span>
                          <span className="text-slate-300">{due.assigned_driver_name}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => handleOpenAddModal(due.vehicle_id)}
                    className="mt-4 w-full py-1.5 px-3 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                  >
                    <Wrench className="w-3.5 h-3.5" />
                    Schedule Service Now
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Filter and Records Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        {/* Table Controls */}
        <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
          <div className="relative w-full md:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search vehicle, note, type..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-500"
            />
          </div>

          <div className="flex items-center gap-2 flex-wrap w-full md:w-auto">
            <select
              value={selectedVehicle}
              onChange={(e) => setSelectedVehicle(e.target.value)}
              className="px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-xs text-slate-300 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Vehicles</option>
              {vehicles.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.vehicle_number} ({v.vehicle_type})
                </option>
              ))}
            </select>

            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-xs text-slate-300 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Service Types</option>
              <option value="OIL_CHANGE">Oil Change</option>
              <option value="TIRE_ROTATION">Tire Rotation</option>
              <option value="BRAKE_INSPECTION">Brake Inspection</option>
              <option value="ENGINE_SERVICE">Engine Service</option>
              <option value="BATTERY_CHECK">Battery Check</option>
              <option value="TRANSMISSION_SERVICE">Transmission</option>
              <option value="GENERAL_INSPECTION">General Inspection</option>
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-xs text-slate-300 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Statuses</option>
              <option value="COMPLETED">Completed</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="SCHEDULED">Scheduled</option>
            </select>
          </div>
        </div>

        {/* Records Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Vehicle</th>
                <th className="py-3 px-4">Service Type</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Mileage</th>
                <th className="py-3 px-4">Next Due</th>
                <th className="py-3 px-4">Cost</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Notes</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-amber-500 mb-2" />
                    Loading maintenance logs...
                  </td>
                </tr>
              ) : filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    No maintenance logs found matching the selected filters.
                  </td>
                </tr>
              ) : (
                filteredRecords.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-4 font-semibold text-white">
                      <div className="flex items-center gap-2">
                        <CarFront className="w-4 h-4 text-slate-400" />
                        <div>
                          <span>{r.vehicle_number || r.vehicle_id}</span>
                          <span className="text-[10px] text-slate-500 block">
                            {r.vehicle_type || 'VAN'}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded-md border text-[11px] font-medium ${getTypeBadge(
                          r.maintenance_type
                        )}`}
                      >
                        {r.maintenance_type.replace('_', ' ')}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 font-mono text-slate-400">
                      {new Date(r.maintenance_date).toLocaleDateString()}
                    </td>

                    <td className="py-3.5 px-4 font-mono font-medium text-slate-200">
                      {r.mileage.toLocaleString()} km
                    </td>

                    <td className="py-3.5 px-4 font-mono text-amber-400 font-semibold">
                      {r.next_maintenance_mileage.toLocaleString()} km
                    </td>

                    <td className="py-3.5 px-4 font-mono text-emerald-400 font-semibold">
                      ${r.cost.toFixed(2)}
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2.5 py-0.5 rounded-full border text-[10px] font-bold ${getStatusBadge(
                          r.status
                        )}`}
                      >
                        {r.status}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 max-w-xs truncate text-slate-400" title={r.notes || ''}>
                      {r.notes || '—'}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenEditModal(r)}
                          title="Edit"
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(r.id)}
                          title="Delete"
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 transition"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Log / Edit Maintenance Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 relative animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Wrench className="w-5 h-5 text-amber-500" />
                {editingRecord ? 'Edit Maintenance Record' : 'Log Maintenance Event'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Vehicle Select */}
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">
                  Fleet Vehicle *
                </label>
                <select
                  value={formData.vehicle_id}
                  onChange={(e) => handleVehicleChange(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-500"
                >
                  <option value="">Select vehicle</option>
                  {vehicles.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.vehicle_number} ({v.vehicle_type} - {v.mileage} km)
                    </option>
                  ))}
                </select>
              </div>

              {/* Maintenance Type & Status */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Service Type *
                  </label>
                  <select
                    value={formData.maintenance_type}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        maintenance_type: e.target.value as MaintenanceType,
                      })
                    }
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-500"
                  >
                    <option value="OIL_CHANGE">Oil Change</option>
                    <option value="TIRE_ROTATION">Tire Rotation</option>
                    <option value="BRAKE_INSPECTION">Brake Inspection</option>
                    <option value="ENGINE_SERVICE">Engine Service</option>
                    <option value="BATTERY_CHECK">Battery Check</option>
                    <option value="TRANSMISSION_SERVICE">Transmission</option>
                    <option value="GENERAL_INSPECTION">General Inspection</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Status *</label>
                  <select
                    value={formData.status}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        status: e.target.value as MaintenanceStatus,
                      })
                    }
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-500"
                  >
                    <option value="COMPLETED">Completed</option>
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="SCHEDULED">Scheduled</option>
                    <option value="CANCELLED">Cancelled</option>
                  </select>
                </div>
              </div>

              {/* Date & Cost */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Service Date *
                  </label>
                  <input
                    type="date"
                    value={formData.maintenance_date}
                    onChange={(e) =>
                      setFormData({ ...formData, maintenance_date: e.target.value })
                    }
                    required
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Cost ($) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.cost}
                    onChange={(e) => setFormData({ ...formData, cost: Number(e.target.value) })}
                    required
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              {/* Current Mileage & Next Service Mileage */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Current Mileage (km) *
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.mileage}
                    onChange={(e) => setFormData({ ...formData, mileage: Number(e.target.value) })}
                    required
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Next Due Mileage (km) *
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.next_maintenance_mileage}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        next_maintenance_mileage: Number(e.target.value),
                      })
                    }
                    required
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">
                  Mechanic / Service Notes
                </label>
                <textarea
                  rows={2}
                  placeholder="Details of parts replaced, inspection findings..."
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-500"
                />
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-amber-600 to-orange-500 hover:from-amber-500 hover:to-orange-400 text-white text-sm font-semibold shadow-glow transition"
                >
                  {editingRecord ? 'Update Record' : 'Save Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
