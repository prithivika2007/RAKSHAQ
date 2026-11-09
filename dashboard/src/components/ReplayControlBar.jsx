import React from 'react';

export default function ReplayControlBar({
  replayState,
  onReset,
  onTogglePlay,
  onSelectScenario,
  onToggleGpsUnavailable
}) {
  const currentStep = replayState?.step ?? 0;
  const currentScenario = replayState?.scenario ?? 'NORMAL';
  const isPlaying = replayState?.isPlaying ?? true;
  const gpsStatus = replayState?.forcedGpsStatus ?? 'OK';
  const locationsLen = replayState?.scenarioConfig?.locations?.length ?? 96;
  const maxPairs = Math.floor(locationsLen / 2);

  return (
    <div className="replay-control-bar">
      <div className="replay-left">
        <div className="replay-pill-tag">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          <span>SIMULATED GPS STREAM</span>
        </div>
        <div className="replay-step-meter">
          <span className="step-label">REPLAY:</span>
          <span className="step-number">Ping {currentStep + 1} / {maxPairs}</span>
          <div className="step-bar">
            <div 
              className="step-bar-fill" 
              style={{ width: `${Math.min(100, Math.round(((currentStep + 1) / maxPairs) * 100))}%` }}
            />
          </div>
        </div>
      </div>

      <div className="replay-center">
        <span className="scenarios-title">QUICK SCENARIOS:</span>

        <button 
          className={`btn-scenario ${currentScenario === 'NORMAL' ? 'active' : ''}`}
          onClick={() => onSelectScenario('NORMAL')}
        >
          Normal
        </button>

        <button 
          className={`btn-scenario scenario-warning ${currentScenario === 'DEVIATION' ? 'active' : ''}`}
          onClick={() => onSelectScenario('DEVIATION')}
        >
          Deviation
        </button>

        <button 
          className={`btn-scenario scenario-warning ${currentScenario === 'STOP' ? 'active' : ''}`}
          onClick={() => onSelectScenario('STOP')}
        >
          Stop
        </button>

        <button 
          className={`btn-scenario scenario-danger ${currentScenario === 'DURESS' ? 'active' : ''}`}
          onClick={() => onSelectScenario('DURESS')}
        >
          Duress
        </button>

        <button 
          className={`btn-scenario scenario-warning ${currentScenario === 'MISSED_CHECKIN' ? 'active' : ''}`}
          onClick={() => onSelectScenario('MISSED_CHECKIN')}
        >
          Missed check-in
        </button>

        <button 
          className={`btn-scenario scenario-stale ${currentScenario === 'PHONE_SHUTDOWN' ? 'active' : ''}`}
          onClick={() => onSelectScenario('PHONE_SHUTDOWN')}
          title="Stops advancing heartbeats so trip card turns red after 60s"
        >
          Phone shutdown (&gt;60s red)
        </button>

        <button 
          className={`btn-scenario scenario-gps ${gpsStatus === 'UNAVAILABLE' ? 'active' : ''}`}
          onClick={onToggleGpsUnavailable}
          title="Toggle driver hardware GPS stream to UNAVAILABLE (grey badge test)"
        >
          {gpsStatus === 'UNAVAILABLE' ? 'GPS: Unavailable (Grey)' : 'Test GPS Unavailable'}
        </button>
      </div>

      <div className="replay-right">
        <button 
          className="btn-replay-action" 
          onClick={onTogglePlay}
          title={isPlaying ? 'Pause replay' : 'Resume replay'}
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <button 
          className="btn-replay-action btn-reset" 
          onClick={onReset}
          title="Restart scenario replay from beginning"
        >
          Reset Replay
        </button>
      </div>
    </div>
  );
}
