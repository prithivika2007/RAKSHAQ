import React, { useState } from 'react';
import { formatTime, getSeverityStyle, getStatusStyle } from '../utils/formatters';

export default function AlertsTimeline({
  incidents = [],
  onUpdateStatus,
  onSelectIncident
}) {
  const [filter, setFilter] = useState('ALL');

  // Sorted newest first
  const sortedIncidents = [...incidents].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const filteredIncidents = sortedIncidents.filter((inc) => {
    if (filter === 'ALL') return true;
    return inc.status?.toUpperCase() === filter;
  });

  const openCount = incidents.filter((i) => i.status === 'OPEN').length;
  const ackCount = incidents.filter((i) => i.status === 'ACKNOWLEDGED').length;
  const resolvedCount = incidents.filter((i) => i.status === 'RESOLVED').length;

  return (
    <div className="card alerts-timeline-card">
      <div className="card-header">
        <div className="card-header-left">
          <span className="card-title">INCIDENT TIMELINE & ALERTS</span>
          {openCount > 0 && (
            <span className="badge-critical-count">
              {openCount} ACTIVE
            </span>
          )}
        </div>
        <div className="timeline-filter-tabs">
          <button
            className={`filter-tab ${filter === 'ALL' ? 'active' : ''}`}
            onClick={() => setFilter('ALL')}
          >
            All ({incidents.length})
          </button>
          <button
            className={`filter-tab ${filter === 'OPEN' ? 'active' : ''}`}
            onClick={() => setFilter('OPEN')}
          >
            Open ({openCount})
          </button>
          <button
            className={`filter-tab ${filter === 'ACKNOWLEDGED' ? 'active' : ''}`}
            onClick={() => setFilter('ACKNOWLEDGED')}
          >
            Ack ({ackCount})
          </button>
          <button
            className={`filter-tab ${filter === 'RESOLVED' ? 'active' : ''}`}
            onClick={() => setFilter('RESOLVED')}
          >
            Resolved ({resolvedCount})
          </button>
        </div>
      </div>

      <div className="timeline-body">
        {filteredIncidents.length === 0 ? (
          <div className="empty-alerts">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="1.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
            <div className="empty-text">No incidents in this view. Corridor status nominal.</div>
          </div>
        ) : (
          <div className="timeline-track">
            {filteredIncidents.map((inc) => {
              const sev = getSeverityStyle(inc.severity);
              const sta = getStatusStyle(inc.status);
              const isDuress = inc.incident_type === 'DURESS_PIN';
              const isOpen = inc.status === 'OPEN';
              const isAcknowledged = inc.status === 'ACKNOWLEDGED';

              return (
                <div
                  key={inc.id}
                  className={`timeline-item ${isDuress ? 'item-duress' : ''} ${isOpen ? 'item-open' : ''}`}
                  onClick={() => onSelectIncident && onSelectIncident(inc)}
                >
                  <div
                    className="timeline-marker"
                    style={{ backgroundColor: sev.badgeBg }}
                  >
                    {isDuress ? (
                      <span className="duress-icon-ping">!</span>
                    ) : (
                      <span className="dot-inner"></span>
                    )}
                  </div>

                  <div className="timeline-content" style={{ borderColor: sev.border }}>
                    <div className="item-header-row">
                      <div className="item-title-cluster">
                        <span
                          className="severity-badge"
                          style={{
                            backgroundColor: sev.badgeBg,
                            color: sev.badgeText
                          }}
                        >
                          {inc.severity}
                        </span>
                        <span className="incident-type-tag">
                          {inc.incident_type?.replace('_', ' ')}
                        </span>
                        <span
                          className="status-pill-small"
                          style={{
                            backgroundColor: sta.bg,
                            color: sta.text,
                            borderColor: sta.border
                          }}
                        >
                          {inc.status}
                        </span>
                      </div>
                      <div className="item-timestamp">
                        {formatTime(inc.ts ?? inc.created_at)}
                      </div>
                    </div>

                    <div className="item-description">
                      {inc.description}
                    </div>

                    {(inc.lat != null || inc.latitude != null) && (inc.lng != null || inc.longitude != null) && (
                      <div className="item-coords font-mono">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                        <span>{(inc.lat ?? inc.latitude).toFixed(4)}, {(inc.lng ?? inc.longitude).toFixed(4)}</span>
                        <span className="coords-hint">(Click to center map)</span>
                      </div>
                    )}

                    {/* Requirement 3: Acknowledge and Resolve buttons */}
                    <div className="item-actions-row">
                      {isOpen && (
                        <button
                          className="btn-incident-action btn-ack"
                          onClick={(e) => {
                            e.stopPropagation();
                            onUpdateStatus(inc.id, 'ACKNOWLEDGED');
                          }}
                        >
                          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                          <span>Acknowledge</span>
                        </button>
                      )}

                      {(isOpen || isAcknowledged) && (
                        <button
                          className="btn-incident-action btn-resolve"
                          onClick={(e) => {
                            e.stopPropagation();
                            onUpdateStatus(inc.id, 'RESOLVED');
                          }}
                        >
                          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                          <span>Resolve</span>
                        </button>
                      )}

                      {inc.status === 'RESOLVED' && (
                        <span className="resolved-checkmark">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                          <span>Resolved</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

