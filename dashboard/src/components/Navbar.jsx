import React from 'react';

export default function Navbar({
  isPolling,
  onTogglePolling,
  onRefresh,
  lastUpdated,
  useMock,
  selectedScenario = 'NORMAL',
  onScenarioChange
}) {
  return (
    <header className="navbar">
      <div className="navbar-left">
        <div className="brand-logo">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="m9 12 2 2 4-4"/>
          </svg>
          <div className="brand-titles">
            <div className="brand-main">RAKSHAQ</div>
            <div className="brand-sub">WOMEN'S NIGHT-SHIFT SAFETY & THREAT DISPATCH</div>
          </div>
        </div>

        {/* Requirement 6: Header badge showing MOCK or LIVE */}
        <div className={`env-mode-badge ${useMock ? 'badge-mock' : 'badge-live'}`}>
          <span className="mode-dot"></span>
          <span className="mode-text">{useMock ? 'MOCK' : 'LIVE'}</span>
        </div>
      </div>

      <div className="navbar-center">
        {/* Requirement 7: Hide the scenario dropdown in LIVE mode (only show in MOCK mode) */}
        {useMock && (
          <div className="scenario-switcher-box">
            <label htmlFor="scenario-select" className="scenario-switcher-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              <span>SCENARIO:</span>
            </label>
            <select
              id="scenario-select"
              className="scenario-select-dropdown"
              value={selectedScenario}
              onChange={(e) => onScenarioChange && onScenarioChange(e.target.value)}
              aria-label="Commute Simulation Scenario"
            >
              <option value="NORMAL">Normal</option>
              <option value="DEVIATION">Deviation</option>
              <option value="STOP">Stop</option>
              <option value="DURESS">Duress</option>
              <option value="MISSED_CHECKIN">Missed check-in</option>
              <option value="PHONE_SHUTDOWN">Phone shutdown</option>
            </select>
          </div>
        )}

        <div className="corridor-pill">
          <span className="dot dot-blue"></span>
          <span className="corridor-text">Pallavaram &rarr; ELCOT SEZ Sholinganallur</span>
        </div>
      </div>

      <div className="navbar-right">
        <div className="stream-badge">
          <span className={`live-pulse-dot ${isPolling ? 'active' : 'paused'}`}></span>
          <span className="stream-label">{isPolling ? 'STREAM: LIVE (3s)' : 'STREAM: PAUSED'}</span>
        </div>

        <button 
          className="btn-icon-action" 
          onClick={onRefresh} 
          title="Force poll refresh now"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"/>
          </svg>
          <span>Refresh</span>
        </button>

        <button 
          className={`btn-stream-toggle ${isPolling ? 'pause-btn' : 'play-btn'}`}
          onClick={onTogglePolling}
          title={isPolling ? 'Pause 3s polling' : 'Resume 3s polling'}
        >
          {isPolling ? (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
              <span>Pause</span>
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              <span>Resume</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
}
