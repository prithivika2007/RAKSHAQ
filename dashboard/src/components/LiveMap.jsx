import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import {
  pickupIcon,
  dropoffIcon,
  createLiveVehicleIcon,
  createIncidentMarkerIcon
} from '../utils/mapIcons';
import { formatTime, getSeverityStyle } from '../utils/formatters';

// Helper component to center map when centerTarget changes
function MapViewController({ centerTarget, zoom = 13 }) {
  const map = useMap();

  useEffect(() => {
    if (centerTarget && centerTarget[0] && centerTarget[1]) {
      map.flyTo(centerTarget, zoom, {
        animate: true,
        duration: 0.8
      });
    }
  }, [centerTarget, map, zoom]);

  return null;
}

export default function LiveMap({
  plannedRoute = [],
  locations = [],
  incidents = [],
  focusedCoords = null,
  onResolveIncident,
  onAcknowledgeIncident
}) {
  // Chennai corridor center (between Pallavaram and Sholinganallur ELCOT)
  const defaultCenter = [12.935, 80.205];
  const defaultZoom = 12;

  // Separate employee and driver GPS trails (using normalised {lat, lng, ts})
  const empList = locations?.employeeTrail || (Array.isArray(locations) ? locations.filter((l) => l.source === 'EMPLOYEE') : []);
  const drvList = locations?.driverTrail || (Array.isArray(locations) ? locations.filter((l) => l.source === 'DRIVER') : []);

  const employeeTrail = empList
    .map((loc) => [loc.lat ?? loc.latitude, loc.lng ?? loc.longitude])
    .filter(([lat, lng]) => lat != null && lng != null && !isNaN(lat) && !isNaN(lng));

  const driverTrail = drvList
    .map((loc) => [loc.lat ?? loc.latitude, loc.lng ?? loc.longitude])
    .filter(([lat, lng]) => lat != null && lng != null && !isNaN(lat) && !isNaN(lng));

  // Last known location
  const latestLocation = empList.length > 0 ? empList[empList.length - 1] : null;
  const currentCoords = latestLocation
    ? [latestLocation.lat ?? latestLocation.latitude, latestLocation.lng ?? latestLocation.longitude]
    : defaultCenter;

  const currentSpeed = latestLocation?.speed ?? 38.0;

  // Pickup and drop-off coordinates
  const pickupCoord = plannedRoute.length > 0 ? plannedRoute[0] : [12.9680, 80.1500];
  const dropoffCoord = plannedRoute.length > 0 ? plannedRoute[plannedRoute.length - 1] : [12.9060, 80.2510];

  return (
    <div className="card live-map-card">
      <div className="map-card-header">
        <div className="map-header-left">
          <span className="card-title">LIVE TELEMETRY RADAR & CORRIDOR MAP</span>
          <span className="map-subtitle font-mono">
            {latestLocation ? `${(latestLocation.lat ?? latestLocation.latitude).toFixed(5)}°N, ${(latestLocation.lng ?? latestLocation.longitude).toFixed(5)}°E` : '12.9350°N, 80.2050°E'}
          </span>
        </div>
        <div className="map-header-right">
          <div className="map-trail-stats">
            <span className="stat-tag trail-emp">
              <span className="dot dot-green"></span>
              Rider Pings: {employeeTrail.length}
            </span>
            <span className="stat-tag trail-drv">
              <span className="dot dot-orange"></span>
              Cab Pings: {driverTrail.length}
            </span>
          </div>
        </div>
      </div>

      <div className="map-container-wrapper">
        <MapContainer
          center={defaultCenter}
          zoom={defaultZoom}
          scrollWheelZoom={true}
          style={{ height: '100%', width: '100%', minHeight: '440px' }}
        >
          {/* CartoDB Dark Matter tiles - matches high-security night operations theme */}
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          />

          <MapViewController
            centerTarget={focusedCoords || currentCoords}
            zoom={focusedCoords ? 14 : defaultZoom}
          />

          {/* 1. Planned Route (Blue Polyline) */}
          {plannedRoute.length > 0 && (
            <Polyline
              positions={plannedRoute}
              pathOptions={{
                color: '#2563eb',
                weight: 5,
                opacity: 0.85,
                lineCap: 'round',
                lineJoin: 'round'
              }}
            />
          )}

          {/* 2. Employee Trail (Green Polyline) */}
          {employeeTrail.length > 1 && (
            <Polyline
              positions={employeeTrail}
              pathOptions={{
                color: '#16a34a',
                weight: 4,
                opacity: 0.95,
                lineCap: 'round'
              }}
            />
          )}

          {/* 3. Driver Trail (Orange Polyline) */}
          {driverTrail.length > 1 && (
            <Polyline
              positions={driverTrail}
              pathOptions={{
                color: '#ea580c',
                weight: 3,
                dashArray: '6, 6',
                opacity: 0.85
              }}
            />
          )}

          {/* Pickup Marker */}
          <Marker position={pickupCoord} icon={pickupIcon}>
            <Popup>
              <div className="map-popup-card">
                <div className="popup-title">PICKUP POINT</div>
                <div className="popup-desc">Pallavaram Railway Station, GST Road, Chennai</div>
                <div className="popup-sub">Scheduled: 22:30 IST</div>
              </div>
            </Popup>
          </Marker>

          {/* Drop-off Marker */}
          <Marker position={dropoffCoord} icon={dropoffIcon}>
            <Popup>
              <div className="map-popup-card">
                <div className="popup-title">DESTINATION</div>
                <div className="popup-desc">ELCOT SEZ, Sholinganallur, Chennai</div>
                <div className="popup-sub">Tech Park Gate 2 Secure Drop-off</div>
              </div>
            </Popup>
          </Marker>

          {/* Last Known Location Marker (Live Vehicle & Rider) */}
          {latestLocation && (
            <Marker
              position={[latestLocation.lat ?? latestLocation.latitude, latestLocation.lng ?? latestLocation.longitude]}
              icon={createLiveVehicleIcon(currentSpeed)}
            >
              <Popup>
                <div className="map-popup-card">
                  <div className="popup-title font-bold">LATEST COMMUTE POSITION</div>
                  <div className="popup-field">
                    <span>Speed:</span> <strong>{Math.round(currentSpeed)} km/h</strong>
                  </div>
                  <div className="popup-field">
                    <span>Coordinates:</span>{' '}
                    <span className="font-mono">
                      {(latestLocation.lat ?? latestLocation.latitude).toFixed(6)}, {(latestLocation.lng ?? latestLocation.longitude).toFixed(6)}
                    </span>
                  </div>
                  <div className="popup-field">
                    <span>Recorded:</span> {formatTime(latestLocation.ts ?? latestLocation.recorded_at)}
                  </div>
                  <div className="popup-status">
                    Dual GPS Stream: Active & Tracking
                  </div>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Incident Markers (Red Beacon with Pulse) */}
          {incidents
            .filter((inc) => (inc.lat != null || inc.latitude != null) && (inc.lng != null || inc.longitude != null))
            .map((inc) => {
              const sev = getSeverityStyle(inc.severity);
              const incLat = inc.lat ?? inc.latitude;
              const incLng = inc.lng ?? inc.longitude;
              const incTs = inc.ts ?? inc.created_at;
              return (
                <Marker
                  key={`marker-inc-${inc.id}`}
                  position={[incLat, incLng]}
                  icon={createIncidentMarkerIcon(inc.severity, inc.incident_type, inc.status)}
                >
                  <Popup>
                    <div className="map-popup-card incident-popup">
                      <div className="incident-popup-header">
                        <span
                          className="popup-sev-badge"
                          style={{ backgroundColor: sev.badgeBg, color: sev.badgeText }}
                        >
                          {inc.severity}
                        </span>
                        <span className="popup-type">{inc.incident_type}</span>
                      </div>
                      <div className="popup-incident-desc">{inc.description}</div>
                      <div className="popup-time-row">
                        <span>Reported: {formatTime(incTs)}</span>
                        <span className="popup-status-text">Status: {inc.status}</span>
                      </div>
                      <div className="popup-action-row">
                        {inc.status === 'OPEN' && onAcknowledgeIncident && (
                          <button
                            className="btn-popup-ack"
                            onClick={() => onAcknowledgeIncident(inc.id)}
                          >
                            Acknowledge
                          </button>
                        )}
                        {inc.status !== 'RESOLVED' && onResolveIncident && (
                          <button
                            className="btn-popup-resolve"
                            onClick={() => onResolveIncident(inc.id)}
                          >
                            Resolve Threat
                          </button>
                        )}
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
        </MapContainer>

        {/* Map Overlay Legend */}
        <div className="map-legend-overlay">
          <div className="legend-title">CORRIDOR LEGEND</div>
          <div className="legend-item">
            <span className="legend-line line-planned"></span>
            <span>Planned Route (Radial Rd)</span>
          </div>
          <div className="legend-item">
            <span className="legend-line line-emp"></span>
            <span>Employee Mobile Stream</span>
          </div>
          <div className="legend-item">
            <span className="legend-line line-drv"></span>
            <span>Driver Device Telemetry</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot dot-incident"></span>
            <span>Incident Threat Marker</span>
          </div>
        </div>
      </div>
    </div>
  );
}

