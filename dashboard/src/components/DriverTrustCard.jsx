import React, { useState, useEffect } from 'react';

export default function DriverTrustCard({
  analysis,
  driver,
  onToggleNightDutyOverride
}) {
  // Sync state with driver prop or local state
  const [isRestricted, setIsRestricted] = useState(
    driver?.night_duty_eligible !== undefined ? !driver.night_duty_eligible : false
  );

  useEffect(() => {
    if (driver?.night_duty_eligible !== undefined) {
      setIsRestricted(!driver.night_duty_eligible);
    }
  }, [driver?.night_duty_eligible]);

  const trustScore = analysis?.trust_score ?? 100;
  const flags = analysis?.flags ?? [];
  const reasons = analysis?.reasons ?? [];
  const gpsStatus = analysis?.gps_status ?? 'OK';

  const driverName = driver?.name || 'Rajesh Kumar';
  const driverPhone = driver?.phone || '+91 98401 23456';
  const licenseNo = driver?.license_no || 'TN-07-20180004521';

  // Determine score color
  let scoreColor = '#10b981'; // Green
  let scoreLabel = 'VERIFIED TRUST';
  let scoreBadgeClass = 'badge-trust-high';

  if (trustScore < 60) {
    scoreColor = '#ef4444'; // Red
    scoreLabel = 'CRITICAL RISK';
    scoreBadgeClass = 'badge-trust-low';
  } else if (trustScore < 85) {
    scoreColor = '#f59e0b'; // Amber
    scoreLabel = 'DEVIATION DETECTED';
    scoreBadgeClass = 'badge-trust-med';
  }

  // SVG circular gauge calculation
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (trustScore / 100) * circumference;

  const handleToggleNightDuty = () => {
    const nextState = !isRestricted;
    setIsRestricted(nextState);
    if (onToggleNightDutyOverride) {
      onToggleNightDutyOverride(nextState);
    }
  };

  return (
    <div className="card driver-trust-card">
      <div className="card-header">
        <div className="card-header-left">
          <span className="card-title">DRIVER INTEGRITY & TRUST</span>
          <span className="driver-id-badge">ID: DRV-007</span>
        </div>
        <div className="card-header-right">
          {/* Requirement 4: Show "GPS stream unavailable" in grey (not red) when gps_status is UNAVAILABLE */}
          {gpsStatus === 'UNAVAILABLE' ? (
            <span className="gps-status-badge gps-unavailable-grey" title="Hardware GPS stream offline; fallback to rider phone">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="1" y1="1" x2="23" y2="23"/>
                <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
                <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
                <path d="M10.71 5.05A16 16 0 0 1 22.58 9"/>
                <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
                <circle cx="12" cy="20" r="1"/>
              </svg>
              GPS stream unavailable
            </span>
          ) : (
            <span className="gps-status-badge gps-ok-green">
              <span className="gps-dot-green"></span>
              GPS Stream: Dual Synced
            </span>
          )}
        </div>
      </div>

      <div className="driver-trust-body">
        {/* Gauge & Driver Identity Grid */}
        <div className="trust-gauge-section">
          {/* Circular SVG Gauge */}
          <div className="gauge-wrapper">
            <svg className="gauge-svg" width="130" height="130" viewBox="0 0 130 130">
              <circle
                className="gauge-bg"
                cx="65"
                cy="65"
                r={radius}
                strokeWidth="10"
              />
              <circle
                className="gauge-progress"
                cx="65"
                cy="65"
                r={radius}
                strokeWidth="10"
                stroke={scoreColor}
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                transform="rotate(-90 65 65)"
              />
            </svg>
            <div className="gauge-content">
              <div className="gauge-value" style={{ color: scoreColor }}>
                {trustScore}
              </div>
              <div className="gauge-denom">/ 100</div>
            </div>
          </div>

          <div className="driver-profile-info">
            <div className="driver-name-row">
              <h3 className="driver-name">{driverName}</h3>
              <span className={`trust-status-pill ${scoreBadgeClass}`}>
                {scoreLabel}
              </span>
            </div>
            <div className="driver-meta-grid">
              <div className="meta-row">
                <span className="meta-lbl">Phone:</span>
                <span className="meta-val">{driverPhone}</span>
              </div>
              <div className="meta-row">
                <span className="meta-lbl">License:</span>
                <span className="meta-val font-mono">{licenseNo}</span>
              </div>
              <div className="meta-row">
                <span className="meta-lbl">Night Shift Status:</span>
                <span className={`meta-val ${isRestricted ? 'text-danger font-bold' : 'text-success'}`}>
                  {isRestricted ? 'RESTRICTED' : 'CLEARED & ELIGIBLE'}
                </span>
              </div>
            </div>

            {/* Requirement 5: Optional "Restrict night duty" button (local state only) */}
            <div className="night-duty-action-row">
              <button
                className={`btn-night-duty ${isRestricted ? 'btn-restore-duty' : 'btn-restrict-duty'}`}
                onClick={handleToggleNightDuty}
              >
                {isRestricted ? (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                    <span>Restore Night Duty</span>
                  </>
                ) : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                    <span>Restrict Night Duty</span>
                  </>
                )}
              </button>
              <span className="action-hint">(Local operator toggle)</span>
            </div>
          </div>
        </div>

        {/* Threat Flags Section */}
        <div className="flags-section">
          <div className="section-label">DETECTED ML THREAT FLAGS</div>
          {flags.length === 0 ? (
            <div className="flags-clean-pill">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
              <span>CLEAN COMMUTE — NO ACTIVE ANOMALY FLAGS</span>
            </div>
          ) : (
            <div className="flags-list">
              {flags.map((flag) => (
                <span key={flag} className="flag-badge">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>
                  {flag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Reasons as Evidence Section */}
        <div className="reasons-section">
          <div className="section-label">TELEMETRY EVIDENCE & EXPLAINABILITY</div>
          {reasons.length === 0 ? (
            <div className="reason-item text-muted">No telemetry deductions recorded.</div>
          ) : (
            <ul className="reasons-list">
              {reasons.map((reason, idx) => (
                <li key={idx} className="reason-item">
                  <span className="reason-bullet">&bull;</span>
                  <span className="reason-text">{reason}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

