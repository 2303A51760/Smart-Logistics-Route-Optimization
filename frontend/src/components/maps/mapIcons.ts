import L from 'leaflet';

// Create a custom styled HTML marker pin
export const createCustomPin = (
  emoji: string,
  bgColor: string,
  borderColor: string,
  pulse: boolean = false
) => {
  return L.divIcon({
    className: 'custom-map-pin',
    html: `
      <div style="
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        background: ${bgColor};
        border: 2px solid ${borderColor};
        border-radius: 50%;
        box-shadow: 0 4px 14px rgba(0,0,0,0.5);
        font-size: 16px;
        transform: translate(-50%, -50%);
        cursor: pointer;
        transition: transform 0.2s ease;
      ">
        ${emoji}
        ${
          pulse
            ? `<span style="
                position: absolute;
                inset: -4px;
                border-radius: 50%;
                border: 2px solid ${borderColor};
                opacity: 0.75;
                animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
              "></span>`
            : ''
        }
      </div>
    `,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -18],
  });
};

export const warehouseIcon = createCustomPin('🏢', '#312e81', '#6366f1');

export const getDriverIcon = (status: string) => {
  switch (status.toUpperCase()) {
    case 'AVAILABLE':
      return createCustomPin('🧑‍✈️', '#064e3b', '#10b981', true);
    case 'ASSIGNED':
    case 'IN_TRANSIT':
      return createCustomPin('🚚', '#0c4a6e', '#0284c7', true);
    case 'OFF_DUTY':
      return createCustomPin('🧑‍✈️', '#78350f', '#f59e0b');
    case 'INACTIVE':
    default:
      return createCustomPin('🔴', '#881337', '#f43f5e');
  }
};

export const getOrderIcon = (status: string, priority: string) => {
  const isUrgent = priority === 'URGENT' || priority === 'HIGH';
  switch (status.toUpperCase()) {
    case 'DELIVERED':
    case 'ARRIVED':
      return createCustomPin('✅', '#064e3b', '#10b981');
    case 'OUT_FOR_DELIVERY':
      return createCustomPin('📦', '#312e81', '#818cf8', true);
    case 'ASSIGNED':
      return createCustomPin('📦', '#0c4a6e', '#38bdf8');
    case 'FAILED':
    case 'CANCELLED':
      return createCustomPin('❌', '#881337', '#f43f5e');
    case 'PENDING':
    default:
      return createCustomPin(isUrgent ? '⚡' : '📍', isUrgent ? '#7f1d1d' : '#78350f', isUrgent ? '#ef4444' : '#f59e0b', isUrgent);
  }
};
