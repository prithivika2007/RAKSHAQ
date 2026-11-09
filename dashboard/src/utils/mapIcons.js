import L from 'leaflet';

/**
 * Custom SVG DivIcons to guarantee crisp rendering and zero broken image URLs
 */

export const pickupIcon = L.divIcon({
  className: 'custom-map-icon',
  html: `
    <div style="display:flex; flex-direction:column; align-items:center; transform: translate(-50%, -100%);">
      <div style="background:#2563eb; color:white; font-size:10px; font-weight:700; padding:2px 6px; border-radius:4px; white-space:nowrap; box-shadow:0 2px 4px rgba(0,0,0,0.4); margin-bottom:2px;">
        PICKUP
      </div>
      <div style="width:24px; height:24px; background:#1e40af; border:2px solid #60a5fa; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:0 0 10px rgba(59,130,246,0.6);">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
      </div>
    </div>
  `,
  iconSize: [0, 0]
});

export const dropoffIcon = L.divIcon({
  className: 'custom-map-icon',
  html: `
    <div style="display:flex; flex-direction:column; align-items:center; transform: translate(-50%, -100%);">
      <div style="background:#059669; color:white; font-size:10px; font-weight:700; padding:2px 6px; border-radius:4px; white-space:nowrap; box-shadow:0 2px 4px rgba(0,0,0,0.4); margin-bottom:2px;">
        DROP-OFF (ELCOT)
      </div>
      <div style="width:24px; height:24px; background:#065f46; border:2px solid #34d399; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:0 0 10px rgba(16,185,129,0.6);">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3" fill="white"/></svg>
      </div>
    </div>
  `,
  iconSize: [0, 0]
});

export const createLiveVehicleIcon = (speed = 0) => L.divIcon({
  className: 'custom-vehicle-icon',
  html: `
    <div class="vehicle-marker-wrapper">
      <div class="pulse-ring"></div>
      <div class="vehicle-pin">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
          <path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.85 7h10.29l1.08 3.11H5.77L6.85 7zM19 17H5v-4.66l.12-.34h13.77l.11.34V17z"/>
          <circle cx="7.5" cy="14.5" r="1.5"/>
          <circle cx="16.5" cy="14.5" r="1.5"/>
        </svg>
      </div>
      <div class="speed-badge">${Math.round(speed)} km/h</div>
    </div>
  `,
  iconSize: [36, 36],
  iconAnchor: [18, 18]
});

export const createIncidentMarkerIcon = (severity, type, status = 'OPEN') => {
  const isResolved = status === 'RESOLVED';
  const isCritical = severity === 'CRITICAL';
  const color = isResolved ? '#16a34a' : isCritical ? '#dc2626' : '#ea580c';
  const label = isResolved ? `${type || 'INCIDENT'} (RESOLVED)` : (type || 'INCIDENT');

  return L.divIcon({
    className: 'custom-incident-icon',
    html: `
      <div class="incident-marker-wrapper">
        ${!isResolved ? `<div class="incident-pulse-ring" style="border-color:${color}"></div>` : ''}
        <div class="incident-pin" style="background:${color}">
          ${isResolved ? `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          ` : `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          `}
        </div>
        <div class="incident-tag" style="background:${color}">${label}</div>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16]
  });
};

