import React, { useState, useEffect } from 'react';
import { formatHeartbeatAge, formatTime } from '../utils/formatters';

export default function ActiveTripCard({ trip }) {
  // Local ticker to keep relative seconds ("X seconds ago") updating live every 1000ms
  const [, setTick] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setTick((t) => t + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Requirement 3: If no active trip, show "No active trip" empty state
  if (!trip) {
    return (
      <div className="card active-trip-card card-empty-state">
        <div className="card-header">
          <div className="card-header-left">
            <span className="card-title">ACTIVE COMMUTE MONITOR</span>
          </div>
          <div className="card-header-right">
            <span className="status-pill pill-idle">
              <span className="pill-dot dot-idle"></span>
              NO ACTIVE TRIP
            </span>
          </div>
        </div>
        <div className="empty-trip-body">
          <div className="empty-icon-shield">
            <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="1.8">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
          </div>
          <h4 className="empty-title">NO ACTIVE TRIP</h4>
          <p className="empty-desc">
            No night-shift cab commutes are currently active on the Chennai corridor.
            Telemetry monitoring is standing by and will automatically engage when a trip is dispatched.
          </p>
        </div>
      </div>
    );
  }

  // Requirement 4: Heartbeat age comes from last_employee_heartbeat_at and last_driver_heartbeat_at
  const employeeHeartbeat = formatHeartbeatAge(trip.last_employee_heartbeat_at);
  const driverHeartbeat = formatHeartbeatAge(trip.last_driver_heartbeat_at);

  // Turn card red above 60 seconds
  const isHeartbeatStale = employeeHeartbeat.seconds > 60;
  const isTripAlert = trip.status === 'ALERT';

  return (
    <div className={`card active-trip-card ${isHeartbeatStale ? 'card-red-alert' : isTripAlert ? 'card-alert-state' : ''}`}>
      {/* Red Alert Banner if heartbeat lost for > 60s */}
      {isHeartbeatStale && (
        <div className="heartbeat-critical-banner">
          <div className="banner-icon-pulse">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div className="banner-text">
            <strong>CRITICAL TELEMETRY LOSS:</strong> No heartbeat received for {employeeHeartbeat.seconds}s (&gt; 60s threshold). Possible signal jam or phone disconnection!
          </div>
        </div>
      )}

      <div className="card-header">
        <div className="card-header-left">
          <span className="card-title">ACTIVE COMMUTE MONITOR</span>
          <span className="trip-id-tag">TRIP #{trip.id}</span>
        </div>
        <div className="card-header-right">
          <span className={`status-pill ${trip.status === 'ALERT' ? 'pill-alert' : 'pill-active'}`}>
            <span className="pill-dot"></span>
            {trip.status}
          </span>
        </div>
      </div>

      <div className="trip-body">
        {/* Route Terminals */}
        <div className="route-terminals">
          <div className="terminal-node">
            <div className="terminal-dot pickup-dot"></div>
            <div className="terminal-info">
              <span className="terminal-label">PICKUP</span>
              <span className="terminal-value" title={trip.pickup_location}>{trip.pickup_location}</span>
            </div>
          </div>

          <div className="route-connector-line">
            <div className="connector-arrow">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <polyline points="19 12 12 19 5 12"/>
              </svg>
            </div>
          </div>

          <div className="terminal-node">
            <div className="terminal-dot dropoff-dot"></div>
            <div className="terminal-info">
              <span className="terminal-label">DESTINATION</span>
              <span className="terminal-value" title={trip.destination}>{trip.destination}</span>
            </div>
          </div>
        </div>

        {/* Heartbeat Status Box */}
        <div className="heartbeat-grid">
          <div className={`heartbeat-box ${isHeartbeatStale ? 'heartbeat-box-stale' : ''}`}>
            <div className="heartbeat-header">
              <span className="heartbeat-label">EMPLOYEE HEARTBEAT</span>
              <span className={`heartbeat-indicator-dot ${isHeartbeatStale ? 'stale-pulse' : 'fresh-pulse'}`}></span>
            </div>
            <div className="heartbeat-metric">
              <span className={`heartbeat-age ${isHeartbeatStale ? 'text-stale' : 'text-fresh'}`}>
                {employeeHeartbeat.text}
              </span>
              <span className="heartbeat-threshold">
                {isHeartbeatStale ? '(CRITICAL > 60s)' : '(Target < 30s)'}
              </span>
            </div>
            <div className="heartbeat-sub">
              Last ping: {formatTime(trip.last_employee_heartbeat_at)}
            </div>
          </div>

          <div className="heartbeat-box">
            <div className="heartbeat-header">
              <span className="heartbeat-label">DRIVER CAB HEARTBEAT</span>
              <span className="heartbeat-indicator-dot fresh-pulse"></span>
            </div>
            <div className="heartbeat-metric">
              <span className="heartbeat-age text-fresh">
                {driverHeartbeat.text}
              </span>
              <span className="heartbeat-threshold">(Active telemetry)</span>
            </div>
            <div className="heartbeat-sub">
              Last ping: {formatTime(trip.last_driver_heartbeat_at)}
            </div>
          </div>
        </div>

        {/* Rider & Cab Quick Specs */}
        <div className="trip-specs-strip">
          <div className="spec-item">
            <span className="spec-label">RIDER</span>
            <span className="spec-val">
              {trip.employee?.name || `Employee #${trip.employee_id}`}
            </span>
          </div>
          <div className="spec-divider"></div>
          <div className="spec-item">
            <span className="spec-label">VEHICLE</span>
            <span className="spec-val">
              {trip.vehicle?.plate_number || 'TN 09 BZ 4412'} ({trip.vehicle?.model || 'Dzire'})
            </span>
          </div>
          <div className="spec-divider"></div>
          <div className="spec-item">
            <span className="spec-label">DRIVER</span>
            <span className="spec-val">
              {trip.driver?.name || `Driver #${trip.driver_id}`}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
