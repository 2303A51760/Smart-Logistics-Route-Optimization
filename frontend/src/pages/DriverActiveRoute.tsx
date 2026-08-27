import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Navigation,
  CheckCircle2,
  XCircle,
  Clock,
  MapPin,
  Truck,
  Play,
  Check,
  AlertOctagon,
  ChevronRight,
  Package,
  ArrowLeft,
  FastForward,
  Building2,
  ShieldAlert,
  Radio,
  Wifi,
  WifiOff,
  Gauge,
  Compass,
  BrainCircuit,
  Sparkles,
} from 'lucide-react';
import { routesApi, RouteItem, RouteStop } from '../services/routes';
import { etaApi, RouteCumulativeETA } from '../services/eta';
import { wsClient } from '../services/websocket';
import { MapView } from '../components/maps/MapView';
import { RoutePolyline } from '../components/maps/RoutePolyline';
import { Toast } from '../components/Toast';

import L from 'leaflet';
import { Marker, Popup } from 'react-leaflet';

const createNumberedIcon = (sequence: number, status: string) => {
  let color = '#3b82f6';
  if (status === 'DELIVERED') color = '#10b981';
  if (status === 'FAILED') color = '#ef4444';
  if (status === 'ARRIVED') color = '#f59e0b';
  if (status === 'IN_PROGRESS') color = '#8b5cf6';
  if (status === 'SKIPPED') color = '#64748b';

  return L.divIcon({
    className: 'custom-driver-pin',
    html: `
      <div style="
        background-color: ${color};
        width: 30px;
        height: 30px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 11px;
        font-weight: bold;
        font-family: monospace;
      ">
        ${sequence}
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
};

const createLiveDriverGpsIcon = (heading: number = 0) => {
  return L.divIcon({
    className: 'custom-live-gps-pin',
    html: `
      <div style="
        position: relative;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          position: absolute;
          width: 36px;
          height: 36px;
          background: rgba(16, 185, 129, 0.4);
          border-radius: 50%;
          animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        "></div>
        <div style="
          position: relative;
          width: 26px;
          height: 26px;
          background: #10b981;
          border: 2.5px solid white;
          border-radius: 50%;
          box-shadow: 0 4px 8px rgba(0,0,0,0.6);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 12px;
          font-weight: bold;
          transform: rotate(${heading}deg);
        ">
          ▲
        </div>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
};

export const DriverActiveRoute: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [route, setRoute] = useState<RouteItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Failure Modal state
  const [failingStopId, setFailingStopId] = useState<string | null>(null);
  const [failureReason, setFailureReason] = useState<string>('CUSTOMER_UNAVAILABLE');
  const [failureNotes, setFailureNotes] = useState<string>('');

  // GPS Tracking & Telemetry State
  const [trackingActive, setTrackingActive] = useState<boolean>(false);
  const [gpsStatus, setGpsStatus] = useState<
    'CONNECTED' | 'DISCONNECTED' | 'SEARCHING' | 'PERMISSION_DENIED' | 'UNSUPPORTED' | 'ERROR'
  >('DISCONNECTED');
  const [wsStatus, setWsStatus] = useState<'CONNECTED' | 'CONNECTING' | 'DISCONNECTED'>('DISCONNECTED');
  const [currentGps, setCurrentGps] = useState<{
    latitude: number;
    longitude: number;
    accuracy?: number;
    speed?: number;
    heading?: number;
  } | null>(null);
  const [lastUpdateSeconds, setLastUpdateSeconds] = useState<number | null>(null);
  const [gpsErrorDetail, setGpsErrorDetail] = useState<string | null>(null);
  const [routeEta, setRouteEta] = useState<RouteCumulativeETA | null>(null);

  const watchIdRef = useRef<number | null>(null);
  const lastSentTimeRef = useRef<number>(0);
  const lastCoordsRef = useRef<{ lat: number; lng: number } | null>(null);
  const lastUpdateTimestampRef = useRef<Date | null>(null);

  const fetchRouteDetail = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const res = await routesApi.getRoute(id);
      setRoute(res);

      // Fetch ML Cumulative Route ETA
      try {
        const etaData = await etaApi.getRouteETA(id);
        setRouteEta(etaData);
      } catch {
        // non-critical
      }
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to load route details');
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    fetchRouteDetail();
  }, [id]);

  // WebSocket lifecycle & status tracking
  useEffect(() => {
    wsClient.connect();
    const unsubStatus = wsClient.onStatusChange((status) => {
      setWsStatus(status);
    });

    const unsubMsg = wsClient.subscribe((data) => {
      if (data.type === 'LOCATION_ACKNOWLEDGED') {
        lastUpdateTimestampRef.current = new Date();
        setLastUpdateSeconds(0);
      }
    });

    return () => {
      unsubStatus();
      unsubMsg();
    };
  }, []);

  // Timer for "Last updated X seconds ago"
  useEffect(() => {
    const timer = setInterval(() => {
      if (lastUpdateTimestampRef.current) {
        const diffSec = Math.floor((Date.now() - lastUpdateTimestampRef.current.getTime()) / 1000);
        setLastUpdateSeconds(diffSec);
      }
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Browser GPS Geolocation Watcher
  const startGpsTracking = () => {
    if (!('geolocation' in navigator)) {
      setGpsStatus('UNSUPPORTED');
      setGpsErrorDetail('Geolocation is not supported by your browser.');
      setToastMessage('Geolocation is not supported by your browser.');
      return;
    }

    setGpsStatus('SEARCHING');
    setGpsErrorDetail(null);
    setTrackingActive(true);

    const options: PositionOptions = {
      enableHighAccuracy: true,
      timeout: 12000,
      maximumAge: 2000,
    };

    const handleSuccess = (pos: GeolocationPosition) => {
      const { latitude, longitude, accuracy, speed, heading } = pos.coords;
      const speedKmh = speed ? Math.round(speed * 3.6 * 10) / 10 : 0;
      const roundedLat = Math.round(latitude * 100000) / 100000;
      const roundedLng = Math.round(longitude * 100000) / 100000;

      setCurrentGps({
        latitude: roundedLat,
        longitude: roundedLng,
        accuracy: accuracy ? Math.round(accuracy * 10) / 10 : undefined,
        speed: speedKmh,
        heading: heading || 0,
      });
      setGpsStatus('CONNECTED');
      setGpsErrorDetail(null);

      // Throttling: Send at most once every 3 seconds or if moved > 5 meters
      const now = Date.now();
      const timeSinceLastSent = now - lastSentTimeRef.current;
      let hasSignificantMovement = true;

      if (lastCoordsRef.current) {
        const dLat = Math.abs(roundedLat - lastCoordsRef.current.lat);
        const dLng = Math.abs(roundedLng - lastCoordsRef.current.lng);
        // ~0.00005 deg is approx 5 meters
        if (dLat < 0.00005 && dLng < 0.00005 && timeSinceLastSent < 5000) {
          hasSignificantMovement = false;
        }
      }

      if (timeSinceLastSent >= 3000 || hasSignificantMovement) {
        lastSentTimeRef.current = now;
        lastCoordsRef.current = { lat: roundedLat, lng: roundedLng };
        lastUpdateTimestampRef.current = new Date();
        setLastUpdateSeconds(0);

        // Transmit real-time location payload over WebSocket
        wsClient.send({
          type: 'location_update',
          latitude: roundedLat,
          longitude: roundedLng,
          accuracy: accuracy ? Math.round(accuracy * 10) / 10 : null,
          speed: speedKmh,
          heading: heading || 0,
        });
      }
    };

    const handleError = (err: GeolocationPositionError) => {
      console.warn('[Geolocation] Error:', err);
      if (err.code === err.PERMISSION_DENIED) {
        setGpsStatus('PERMISSION_DENIED');
        setGpsErrorDetail('Location permission was denied. Please allow browser location access.');
        setToastMessage('GPS Permission Denied. Please enable location permissions in your browser.');
      } else if (err.code === err.POSITION_UNAVAILABLE) {
        setGpsStatus('ERROR');
        setGpsErrorDetail('Location position unavailable. Check device GPS signal.');
      } else if (err.code === err.TIMEOUT) {
        setGpsStatus('ERROR');
        setGpsErrorDetail('Location request timed out. Retrying GPS lock...');
      } else {
        setGpsStatus('ERROR');
        setGpsErrorDetail(err.message || 'GPS location error.');
      }
    };

    try {
      const id = navigator.geolocation.watchPosition(handleSuccess, handleError, options);
      watchIdRef.current = id;
    } catch (e: any) {
      setGpsStatus('ERROR');
      setGpsErrorDetail(e.message || 'Failed to start GPS watcher.');
    }
  };

  const stopGpsTracking = () => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setTrackingActive(false);
    setGpsStatus('DISCONNECTED');
  };

  // Clean up GPS watcher on unmount
  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  const handleStartRoute = async () => {
    if (!route) return;
    try {
      setActing(true);
      const updated = await routesApi.startRoute(route.id, {
        notes: 'Driver initiated route from cockpit',
      });
      setRoute(updated);
      setToastMessage('Route started successfully! Orders are now Out for Delivery.');
      // Auto-start GPS tracking on route start if not already active
      if (!trackingActive) {
        startGpsTracking();
      }
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to start route');
    } finally {
      setActing(false);
    }
  };

  const handleArriveAtStop = async (stopId: string) => {
    if (!route) return;
    try {
      setActing(true);
      const updated = await routesApi.arriveAtStop(route.id, stopId);
      setRoute(updated);
      setToastMessage('Stop arrival recorded: Customer order marked as ARRIVED.');
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to record stop arrival');
    } finally {
      setActing(false);
    }
  };

  const handleStartDelivery = async (stopId: string) => {
    if (!route) return;
    try {
      setActing(true);
      const updated = await routesApi.startDelivery(route.id, stopId);
      setRoute(updated);
      setToastMessage('Delivery hand-off process started.');
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to start delivery');
    } finally {
      setActing(false);
    }
  };

  const handleDeliverStop = async (stopId: string) => {
    if (!route) return;
    try {
      setActing(true);
      const updated = await routesApi.deliverStop(route.id, stopId, {
        notes: 'Package handed directly to customer',
      });
      setRoute(updated);
      setToastMessage('Delivery confirmed successfully! Order marked as DELIVERED.');
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to confirm delivery');
    } finally {
      setActing(false);
    }
  };

  const submitStopFailure = async () => {
    if (!route || !failingStopId) return;
    try {
      setActing(true);
      const updated = await routesApi.failStop(route.id, failingStopId, {
        reason: failureReason,
        notes: failureNotes || undefined,
      });
      setRoute(updated);
      setFailingStopId(null);
      setFailureNotes('');
      setToastMessage(`Delivery marked as FAILED (${failureReason.replace(/_/g, ' ')}).`);
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to mark stop as failed');
    } finally {
      setActing(false);
    }
  };

  const handleSkipStop = async (stopId: string) => {
    if (!route) return;
    if (!window.confirm('Are you sure you want to skip this stop? You will proceed to the next stop.')) return;

    try {
      setActing(true);
      const updated = await routesApi.skipStop(route.id, stopId, { reason: 'Skipped by driver' });
      setRoute(updated);
      setToastMessage('Stop skipped.');
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to skip stop');
    } finally {
      setActing(false);
    }
  };

  const handleCompleteRoute = async () => {
    if (!route) return;
    if (!window.confirm('Complete this route and return to depot?')) return;

    try {
      setActing(true);
      const updated = await routesApi.completeRoute(route.id, { notes: 'Route completed by driver' });
      setRoute(updated);
      setToastMessage('Route execution successfully completed! Driver is now AVAILABLE.');
      stopGpsTracking();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to complete route');
    } finally {
      setActing(false);
    }
  };

  if (loading || !route) {
    return (
      <div className="py-24 text-center text-slate-400">
        <div className="inline-block animate-spin text-3xl mb-3 text-blue-400">⟳</div>
        <p className="text-sm">Loading Route Cockpit...</p>
      </div>
    );
  }

  // Calculate coordinates for Map (Depot -> Stops -> Live Driver GPS)
  const mapCoordinates: [number, number][] = [];
  if (currentGps) {
    mapCoordinates.push([currentGps.latitude, currentGps.longitude]);
  }
  route.stops.forEach((s) => {
    if (s.delivery_latitude && s.delivery_longitude) {
      mapCoordinates.push([s.delivery_latitude, s.delivery_longitude]);
    }
  });

  const isPlanned = route.status === 'PLANNED';
  const isInProgress = route.status === 'IN_PROGRESS' || route.status === 'STARTED';
  const isCompleted = route.status === 'COMPLETED';

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link to="/driver/routes" className="hover:text-blue-400 flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Routes
            </Link>
            <span>/</span>
            <span className="text-emerald-400 font-semibold font-mono">{route.id}</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <span className="p-2 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-glow">
              <Navigation className="w-5 h-5" />
            </span>
            {route.name || `Route Execution #${route.id}`}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Preserved OR-Tools Optimized Sequence &bull; {route.stops_count} Delivery Stops
          </p>
        </div>

        {/* Global Route Controls */}
        <div className="flex items-center gap-3">
          {isPlanned && (
            <button
              disabled={acting}
              onClick={handleStartRoute}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-xl shadow-glow transition-all"
            >
              <Play className="w-4 h-4 fill-white" />
              <span>START ROUTE</span>
            </button>
          )}

          {isInProgress && (
            <button
              disabled={acting}
              onClick={handleCompleteRoute}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl shadow-md transition-all"
            >
              <Check className="w-4 h-4" />
              <span>FINISH & COMPLETE ROUTE</span>
            </button>
          )}

          {isCompleted && (
            <div className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-xl text-xs font-bold">
              <CheckCircle2 className="w-4 h-4" />
              <span>ROUTE COMPLETED</span>
            </div>
          )}
        </div>
      </div>

      {/* PHASE 7: REAL-TIME GPS TRACKING & TELEMETRY PANEL */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900/90 to-indigo-950/40 p-5 rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl ${trackingActive ? 'bg-emerald-500/20 text-emerald-400 ring-2 ring-emerald-500/40' : 'bg-slate-800 text-slate-400'}`}>
              <Radio className={`w-5 h-5 ${trackingActive ? 'animate-pulse' : ''}`} />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wide">Real-Time Driver GPS Tracking</h2>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    gpsStatus === 'CONNECTED'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 animate-pulse'
                      : gpsStatus === 'SEARCHING'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-bounce'
                      : gpsStatus === 'PERMISSION_DENIED'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}
                >
                  GPS: {gpsStatus}
                </span>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    wsStatus === 'CONNECTED'
                      ? 'bg-blue-500/20 text-blue-400 border border-blue-500/40'
                      : wsStatus === 'CONNECTING'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}
                >
                  WS: {wsStatus}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Streams browser GPS coordinates to backend Redis Pub/Sub for live dispatcher monitoring.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {trackingActive ? (
              <button
                type="button"
                onClick={stopGpsTracking}
                className="px-4 py-2 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 text-xs font-bold rounded-xl transition-all shadow"
              >
                Disable GPS Tracking
              </button>
            ) : (
              <button
                type="button"
                onClick={startGpsTracking}
                className="px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-xl shadow-glow transition-all flex items-center gap-2"
              >
                <Radio className="w-4 h-4" />
                <span>ENABLE GPS TRACKING</span>
              </button>
            )}
          </div>
        </div>

        {/* Live GPS Telemetry Bar */}
        {trackingActive && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-800/80 text-xs">
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[11px] block">Live Coordinates</span>
              <p className="font-mono font-bold text-slate-200 mt-0.5">
                {currentGps ? `${currentGps.latitude.toFixed(5)}, ${currentGps.longitude.toFixed(5)}` : 'Acquiring lock...'}
              </p>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[11px] block flex items-center gap-1">
                <Gauge className="w-3 h-3 text-indigo-400" /> Current Speed
              </span>
              <p className="font-mono font-bold text-slate-200 mt-0.5">
                {currentGps?.speed !== undefined ? `${currentGps.speed} km/h` : '--'}
              </p>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[11px] block flex items-center gap-1">
                <Compass className="w-3 h-3 text-cyan-400" /> Accuracy & Heading
              </span>
              <p className="font-mono font-bold text-slate-200 mt-0.5">
                {currentGps?.accuracy ? `±${currentGps.accuracy}m` : '--'} &bull; {currentGps?.heading ? `${Math.round(currentGps.heading)}°` : '0°'}
              </p>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[11px] block flex items-center gap-1">
                <Clock className="w-3 h-3 text-emerald-400" /> Telemetry Ping
              </span>
              <p className="font-mono font-bold text-emerald-400 mt-0.5">
                {lastUpdateSeconds !== null ? `Updated ${lastUpdateSeconds}s ago` : 'Waiting for ping...'}
              </p>
            </div>
          </div>
        )}

        {gpsErrorDetail && (
          <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 flex-shrink-0 text-rose-400" />
            <span>{gpsErrorDetail}</span>
          </div>
        )}
      </div>

      {/* Section 10: Route Summary Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
        <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
          <span className="text-slate-400 flex items-center gap-1.5 mb-1">
            <Truck className="w-3.5 h-3.5 text-indigo-400" /> Driver
          </span>
          <p className="font-bold text-slate-100 text-sm truncate">{route.driver_name || 'Assigned Driver'}</p>
        </div>
        <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
          <span className="text-slate-400 flex items-center gap-1.5 mb-1">
            <Truck className="w-3.5 h-3.5 text-blue-400" /> Vehicle
          </span>
          <p className="font-bold text-slate-100 text-sm truncate">{route.vehicle_number || 'Fleet Vehicle'}</p>
        </div>
        <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
          <span className="text-slate-400 flex items-center gap-1.5 mb-1">
            <Building2 className="w-3.5 h-3.5 text-emerald-400" /> Warehouse
          </span>
          <p className="font-bold text-slate-100 text-sm truncate">{route.warehouse_name || 'Depot Hub'}</p>
        </div>
        <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
          <span className="text-slate-400 flex items-center gap-1.5 mb-1">
            <Navigation className="w-3.5 h-3.5 text-cyan-400" /> Distance
          </span>
          <p className="font-bold text-slate-100 text-sm">{route.total_distance} km</p>
        </div>
        <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
          <span className="text-slate-400 flex items-center gap-1.5 mb-1">
            <Clock className="w-3.5 h-3.5 text-amber-400" /> Duration
          </span>
          <p className="font-bold text-slate-100 text-sm">{route.estimated_duration} min</p>
        </div>
        <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
          <span className="text-slate-400 flex items-center gap-1.5 mb-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Status
          </span>
          <p
            className={`font-bold text-sm ${
              route.status === 'IN_PROGRESS' || route.status === 'STARTED'
                ? 'text-emerald-400 animate-pulse'
                : route.status === 'COMPLETED'
                ? 'text-blue-400'
                : 'text-slate-200'
            }`}
          >
            {route.status}
          </p>
        </div>
      </div>

      {/* PHASE 8: AI-POWERED ROUTE ETA PREDICTION BANNER */}
      {routeEta && (
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-purple-950/30 p-4 rounded-2xl border border-indigo-500/40 shadow-lg flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-100 uppercase tracking-wide">
                  AI Dynamic Route Duration & ETA
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                  {routeEta.source === 'ML' ? 'AI PREDICTED' : 'FALLBACK ESTIMATE'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Predicted Route Duration: <strong className="text-indigo-300 font-mono">{routeEta.total_predicted_duration_minutes} min</strong> ({routeEta.total_distance_km} km) • Est. Completion: <strong className="text-slate-200">{new Date(routeEta.route_estimated_completion).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</strong>
              </p>
            </div>
          </div>
          <div className="text-right text-[11px] font-mono text-slate-400">
            <span>Model: {routeEta.model_version}</span>
          </div>
        </div>
      )}

      {/* Main Grid: Left Turn-by-Turn Manifest & Right Live Route Map */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left: Stops List (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Package className="w-4 h-4 text-emerald-400" /> Ordered Stop Manifest ({route.completed_stops_count}/{route.stops_count} Completed)
              </h2>
              <span className="text-[11px] font-mono text-slate-400">Score: {route.optimization_score}%</span>
            </div>

            <div className="space-y-3">
              {route.stops.map((stop) => {
                const isPending = stop.status === 'PENDING';
                const isArrived = stop.status === 'ARRIVED';
                const isDelivering = stop.status === 'IN_PROGRESS';
                const isDelivered = stop.status === 'DELIVERED';
                const isFailed = stop.status === 'FAILED';
                const isSkipped = stop.status === 'SKIPPED';

                return (
                  <div
                    key={stop.id}
                    className={`p-4 rounded-xl border transition-all space-y-3 ${
                      isArrived || isDelivering
                        ? 'bg-amber-950/20 border-amber-500/50 shadow-md ring-1 ring-amber-500/30'
                        : isDelivered
                        ? 'bg-slate-950/40 border-slate-800/80 opacity-80'
                        : isFailed
                        ? 'bg-rose-950/20 border-rose-900/40 opacity-80'
                        : isSkipped
                        ? 'bg-slate-950/30 border-slate-800 opacity-60'
                        : 'bg-slate-950/60 border-slate-800 text-slate-200'
                    }`}
                  >
                    {/* Header */}
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-2.5">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs font-mono shadow ${
                            isDelivered
                              ? 'bg-emerald-500 text-white'
                              : isFailed
                              ? 'bg-rose-500 text-white'
                              : isArrived
                              ? 'bg-amber-500 text-white animate-bounce'
                              : isDelivering
                              ? 'bg-purple-600 text-white animate-pulse'
                              : 'bg-blue-600 text-white'
                          }`}
                        >
                          {stop.sequence}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-100 text-sm">{stop.customer_name || 'Client Delivery'}</span>
                            <span className="text-xs font-mono text-slate-400 font-semibold">{stop.order_number}</span>
                            <span
                              className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                stop.priority === 'URGENT'
                                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                                  : stop.priority === 'HIGH'
                                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                                  : 'bg-slate-800 text-slate-400'
                              }`}
                            >
                              {stop.priority || 'NORMAL'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-300 flex items-center gap-1 mt-0.5">
                            <MapPin className="w-3.5 h-3.5 text-slate-400" />
                            {stop.delivery_address || 'Delivery Location'}
                          </p>
                          {(() => {
                            const matchedEta = routeEta?.stops?.find((s) => s.stop_id === stop.id);
                            const displayEta = matchedEta?.estimated_arrival || stop.estimated_arrival;
                            return displayEta ? (
                              <p className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5 font-mono">
                                <Clock className="w-3 h-3 text-indigo-400" />
                                <span>ETA: {new Date(displayEta).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                {matchedEta && (
                                  <span className="text-[10px] text-indigo-300 bg-indigo-500/10 px-1.5 py-0.2 rounded border border-indigo-500/20">
                                    ~{matchedEta.predicted_duration_minutes}m leg
                                  </span>
                                )}
                              </p>
                            ) : null;
                          })()}
                        </div>
                      </div>


                      {/* Status Tag */}
                      <div>
                        {isDelivered && (
                          <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg text-[10px] font-bold flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> DELIVERED
                          </span>
                        )}
                        {isFailed && (
                          <span className="px-2.5 py-1 bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-lg text-[10px] font-bold flex items-center gap-1">
                            <XCircle className="w-3 h-3" /> FAILED
                          </span>
                        )}
                        {isSkipped && (
                          <span className="px-2.5 py-1 bg-slate-800 text-slate-400 border border-slate-700 rounded-lg text-[10px] font-bold">
                            SKIPPED
                          </span>
                        )}
                        {isArrived && (
                          <span className="px-2.5 py-1 bg-amber-500/20 text-amber-400 border border-amber-500/40 rounded-lg text-[10px] font-bold animate-pulse">
                            ARRIVED AT STOP
                          </span>
                        )}
                        {isDelivering && (
                          <span className="px-2.5 py-1 bg-purple-500/20 text-purple-300 border border-purple-500/40 rounded-lg text-[10px] font-bold animate-pulse">
                            DELIVERY IN PROGRESS
                          </span>
                        )}
                        {isPending && (
                          <span className="px-2.5 py-1 bg-slate-800 text-slate-400 rounded-lg text-[10px] font-bold">
                            PENDING
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Section 11: Interactive Driver Actions per strict state */}
                    {isInProgress && (
                      <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
                        {isPending && (
                          <>
                            <button
                              disabled={acting}
                              onClick={() => handleArriveAtStop(stop.id)}
                              className="flex items-center gap-1.5 px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl shadow transition"
                            >
                              <MapPin className="w-3.5 h-3.5" />
                              <span>ARRIVED</span>
                            </button>
                            <button
                              disabled={acting}
                              onClick={() => handleSkipStop(stop.id)}
                              className="text-xs text-slate-400 hover:text-slate-200 px-3 py-1.5 flex items-center gap-1"
                            >
                              <FastForward className="w-3 h-3" /> Skip Stop
                            </button>
                          </>
                        )}

                        {isArrived && (
                          <>
                            <div className="flex items-center gap-2">
                              <button
                                disabled={acting}
                                onClick={() => handleStartDelivery(stop.id)}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs rounded-xl shadow transition"
                              >
                                <Play className="w-3.5 h-3.5 fill-white" />
                                <span>START DELIVERY</span>
                              </button>
                              <button
                                disabled={acting}
                                onClick={() => handleDeliverStop(stop.id)}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow transition"
                              >
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>MARK DELIVERED</span>
                              </button>
                              <button
                                disabled={acting}
                                onClick={() => setFailingStopId(stop.id)}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600/80 hover:bg-rose-600 text-white font-bold text-xs rounded-xl transition"
                              >
                                <AlertOctagon className="w-3.5 h-3.5" />
                                <span>MARK FAILED</span>
                              </button>
                            </div>
                            <button
                              disabled={acting}
                              onClick={() => handleSkipStop(stop.id)}
                              className="text-xs text-slate-400 hover:text-slate-200 px-2 py-1 flex items-center gap-1"
                            >
                              <FastForward className="w-3 h-3" /> Skip
                            </button>
                          </>
                        )}

                        {isDelivering && (
                          <div className="flex items-center gap-2">
                            <button
                              disabled={acting}
                              onClick={() => handleDeliverStop(stop.id)}
                              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow transition"
                            >
                              <CheckCircle2 className="w-4 h-4" />
                              <span>MARK DELIVERED</span>
                            </button>
                            <button
                              disabled={acting}
                              onClick={() => setFailingStopId(stop.id)}
                              className="flex items-center gap-1.5 px-4 py-2 bg-rose-600/80 hover:bg-rose-600 text-white font-bold text-xs rounded-xl transition"
                            >
                              <AlertOctagon className="w-4 h-4" />
                              <span>MARK FAILED</span>
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right: Section 15: Map Integration (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 space-y-3 sticky top-6">
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Navigation className="w-4 h-4 text-blue-400" /> Route Navigation Visualizer
              </h3>
              {currentGps && (
                <span className="text-[10px] text-emerald-400 font-mono font-semibold flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span> Live GPS Active
                </span>
              )}
            </div>

            <MapView height="440px" bounds={mapCoordinates.length > 0 ? mapCoordinates : undefined} autoFit={true}>
              {mapCoordinates.length >= 2 && (
                <RoutePolyline positions={mapCoordinates} color="#3b82f6" weight={5} opacity={0.85} />
              )}

              {/* Real-time Driver GPS Marker */}
              {currentGps && (
                <Marker
                  position={[currentGps.latitude, currentGps.longitude]}
                  icon={createLiveDriverGpsIcon(currentGps.heading)}
                >
                  <Popup>
                    <div className="text-xs space-y-1">
                      <span className="font-bold text-emerald-600 block flex items-center gap-1">
                        📍 Your Live GPS Position
                      </span>
                      <p className="font-semibold text-slate-900">Driver in Motion</p>
                      <p className="text-slate-600">Speed: {currentGps.speed || 0} km/h</p>
                      <p className="text-slate-500 font-mono text-[10px]">
                        {currentGps.latitude.toFixed(5)}, {currentGps.longitude.toFixed(5)}
                      </p>
                    </div>
                  </Popup>
                </Marker>
              )}

              {/* Stop Markers */}
              {route.stops.map((s) => {
                if (!s.delivery_latitude || !s.delivery_longitude) return null;
                return (
                  <Marker
                    key={s.id}
                    position={[s.delivery_latitude, s.delivery_longitude]}
                    icon={createNumberedIcon(s.sequence, s.status)}
                  >
                    <Popup>
                      <div className="text-xs space-y-1">
                        <span className="font-bold text-blue-600 block">Stop #{s.sequence} &bull; {s.status}</span>
                        <p className="font-semibold text-slate-900">{s.customer_name}</p>
                        <p className="text-slate-600">{s.delivery_address}</p>
                        <p className="text-slate-500 font-mono text-[10px]">{s.order_number}</p>
                      </div>
                    </Popup>
                  </Marker>
                );
              })}
            </MapView>
          </div>
        </div>
      </div>

      {/* Section 12: Delivery Failure Reason Modal */}
      {failingStopId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-rose-500/40 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center gap-3 text-rose-400">
              <ShieldAlert className="w-6 h-6" />
              <h3 className="text-base font-bold text-slate-100">Log Delivery Failure</h3>
            </div>
            <p className="text-xs text-slate-300">
              Please specify the operational reason for undelivered package. This will be recorded into the delivery audit log.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 font-bold block mb-1">Failure Reason:</label>
                <select
                  value={failureReason}
                  onChange={(e) => setFailureReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-rose-500 font-medium"
                >
                  <option value="CUSTOMER_UNAVAILABLE">Customer Unavailable</option>
                  <option value="WRONG_ADDRESS">Wrong Address</option>
                  <option value="DAMAGED_PACKAGE">Damaged Package</option>
                  <option value="REFUSED_DELIVERY">Refused Delivery</option>
                  <option value="OTHER">Other / Access Restricted</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 font-bold block mb-1">Additional Notes (Optional):</label>
                <textarea
                  value={failureNotes}
                  onChange={(e) => setFailureNotes(e.target.value)}
                  placeholder="e.g. Ring doorbell 3 times, gate locked..."
                  rows={3}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-rose-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setFailingStopId(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={acting}
                onClick={submitStopFailure}
                className="px-5 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl shadow-md transition"
              >
                Confirm Failure
              </button>
            </div>
          </div>
        </div>
      )}

      {toastMessage && <Toast message={toastMessage} onClose={() => setToastMessage(null)} />}
    </div>
  );
};
