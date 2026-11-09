import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import ReplayControlBar from './components/ReplayControlBar';
import ActiveTripCard from './components/ActiveTripCard';
import DriverTrustCard from './components/DriverTrustCard';
import LiveMap from './components/LiveMap';
import AlertsTimeline from './components/AlertsTimeline';
import {
  getActiveTrip,
  getTrip,
  getTripLocations,
  getIncidents,
  getTripAnalysis,
  getDriver,
  updateIncident,
  updateDriver,
  USE_MOCK,
  API_URL,
  subscribeReplayState,
  resetReplay,
  toggleReplayPlayPause,
  setScenario,
  toggleMockGpsStatus
} from './api';
import './App.css';

export default function App() {
  const [activeTrip, setActiveTrip] = useState(null);
  const [locations, setLocations] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  
  // Loading state on first load (Requirement 5)
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  // Error handling: if backend is unreachable (Requirement 5)
  const [isBackendOffline, setIsBackendOffline] = useState(false);
  const [lastError, setLastError] = useState(null);

  // Scenario state: Normal, Deviation, Stop, Duress, Missed check-in, Phone shutdown
  const [selectedScenario, setSelectedScenario] = useState('NORMAL');

  // Polling state (every 3 seconds)
  const [isPolling, setIsPolling] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(Date.now());
  const [focusedCoords, setFocusedCoords] = useState(null);

  // Replay state for demo controls
  const [replayState, setReplayState] = useState(null);

  // Subscribe to mock replay state updates when in MOCK mode
  useEffect(() => {
    if (USE_MOCK) {
      const unsubscribe = subscribeReplayState((st) => {
        setReplayState(st);
        if (st.scenario && st.scenario !== selectedScenario) {
          setSelectedScenario(st.scenario);
        }
      });
      return unsubscribe;
    }
  }, [selectedScenario]);

  // Fetch all endpoints (Requirement 1, 2, 3, 5)
  const fetchAllData = useCallback(async () => {
    try {
      // Pick first active trip automatically (Requirement 3)
      const trip = await getActiveTrip();
      
      if (trip) {
        // If driver info is separate, fetch driver details
        if (trip.driver_id && !trip.driver?.name) {
          try {
            const driverInfo = await getDriver(trip.driver_id);
            trip.driver = { ...trip.driver, ...driverInfo };
          } catch (dErr) {
            console.warn('Driver fetch warning:', dErr);
          }
        }

        setActiveTrip(trip);

        const tripId = trip.id;
        const [locsData, incsData, analysisData] = await Promise.all([
          getTripLocations(tripId),
          getIncidents(),
          getTripAnalysis(tripId)
        ]);

        setLocations(locsData || []);
        setIncidents(incsData || []);
        setAnalysis(analysisData || null);
      } else {
        // No active trip found (Requirement 3: empty state)
        setActiveTrip(null);
        try {
          const incsData = await getIncidents();
          setIncidents(incsData || []);
        } catch (_) {}
      }

      // Backend healthy
      setIsBackendOffline(false);
      setLastError(null);
      setLastUpdated(Date.now());
    } catch (err) {
      console.error('Data polling error:', err);
      // Requirement 5: Keep last data instead of crashing if backend is offline
      if (!USE_MOCK) {
        setIsBackendOffline(true);
        setLastError(err.message || 'Network error');
      }
    } finally {
      setIsInitialLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Requirement: Auto-refresh by polling every 3 seconds
  useEffect(() => {
    if (!isPolling) return;

    const intervalId = setInterval(() => {
      fetchAllData();
    }, 3000);

    return () => clearInterval(intervalId);
  }, [isPolling, fetchAllData]);

  // Handle Scenario Switcher (Dropdown & Quick buttons in MOCK mode)
  const handleScenarioChange = (scenarioKey) => {
    setSelectedScenario(scenarioKey);
    setScenario(scenarioKey);
    fetchAllData();
  };

  // Handle Incident status updates (Acknowledge / Resolve)
  const handleUpdateIncidentStatus = async (incidentId, newStatus) => {
    try {
      await updateIncident(incidentId, { status: newStatus });
      setIncidents((prev) =>
        prev.map((inc) => (inc.id === incidentId ? { ...inc, status: newStatus } : inc))
      );
      // Re-fetch trip to update alert status
      const trip = await getActiveTrip();
      if (trip) setActiveTrip(trip);
    } catch (err) {
      console.error(`Failed to update incident ${incidentId}:`, err);
      alert(`Could not update incident: ${err.message}`);
    }
  };

  // Handle Driver Night Duty toggle (Requirement 1: PATCH /drivers/{id})
  const handleToggleNightDuty = async (isRestricted) => {
    try {
      const driverId = activeTrip?.driver?.id || activeTrip?.driver_id || 1;
      await updateDriver(driverId, { night_duty_eligible: !isRestricted });
      setActiveTrip((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          driver: {
            ...prev.driver,
            night_duty_eligible: !isRestricted
          }
        };
      });
    } catch (err) {
      console.error('Failed to update driver night duty:', err);
      alert(`Driver update failed: ${err.message}`);
    }
  };

  // Replay control handlers (Mock mode)
  const handleResetReplay = () => {
    resetReplay();
    fetchAllData();
  };

  const handleTogglePlay = () => {
    toggleReplayPlayPause();
  };

  const handleToggleGpsUnavailable = () => {
    toggleMockGpsStatus();
    fetchAllData();
  };

  const handleSelectIncident = (incident) => {
    const lat = incident?.lat ?? incident?.latitude;
    const lng = incident?.lng ?? incident?.longitude;
    if (lat != null && lng != null) {
      setFocusedCoords([lat, lng]);
      setTimeout(() => setFocusedCoords(null), 3000);
    }
  };

  // Requirement 5: Loading state on first load
  if (isInitialLoading) {
    return (
      <div className="app-container app-loading-screen">
        <Navbar
          isPolling={false}
          onTogglePolling={() => {}}
          onRefresh={() => {}}
          lastUpdated={Date.now()}
          useMock={USE_MOCK}
          selectedScenario="NORMAL"
        />
        <div className="initial-loading-body">
          <div className="loading-radar-ring"></div>
          <div className="loading-logo-box">
            <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
          </div>
          <h2 className="loading-heading">CONNECTING TO RAKSHAQ TELEMETRY SYSTEM...</h2>
          <p className="loading-subheading">
            {USE_MOCK
              ? 'Initializing simulated Chennai commute corridor...'
              : `Connecting to live FastAPI backend at ${API_URL}...`}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Top Navbar with MOCK/LIVE badge and scenario switcher (hidden in LIVE mode) */}
      <Navbar
        isPolling={isPolling}
        onTogglePolling={() => setIsPolling(!isPolling)}
        onRefresh={fetchAllData}
        lastUpdated={lastUpdated}
        useMock={USE_MOCK}
        selectedScenario={selectedScenario}
        onScenarioChange={handleScenarioChange}
      />

      {/* Requirement 5: Small "Backend offline" banner when backend is unreachable, keeping last data */}
      {isBackendOffline && !USE_MOCK && (
        <div className="backend-offline-banner">
          <div className="offline-pulse-dot"></div>
          <span className="offline-badge">BACKEND OFFLINE</span>
          <span className="offline-msg">
            Unable to connect to <code>{API_URL}</code> ({lastError || 'Connection refused'}). Displaying last known telemetry snapshot. Retrying every 3s...
          </span>
        </div>
      )}

      {/* Interactive Replay / Demo Toolbar (Only in MOCK mode) */}
      {USE_MOCK && (
        <ReplayControlBar
          replayState={replayState}
          onReset={handleResetReplay}
          onTogglePlay={handleTogglePlay}
          onSelectScenario={handleScenarioChange}
          onToggleGpsUnavailable={handleToggleGpsUnavailable}
        />
      )}

      {/* Main Dashboard Grid */}
      <main className="dashboard-grid">
        {/* Left Column: Active Trip & Driver Trust Cards */}
        <section className="dashboard-col col-sidebar">
          {/* Requirement 3 & 4: Active trip card & empty state */}
          <ActiveTripCard trip={activeTrip} />

          {/* Driver Trust Score card */}
          <DriverTrustCard
            analysis={analysis}
            driver={activeTrip?.driver}
            onToggleNightDutyOverride={handleToggleNightDuty}
          />
        </section>

        {/* Center / Primary Column: Live Map */}
        <section className="dashboard-col col-map">
          {/* Live map */}
          <LiveMap
            plannedRoute={activeTrip?.planned_route || []}
            locations={locations}
            incidents={incidents}
            focusedCoords={focusedCoords}
            onAcknowledgeIncident={(id) => handleUpdateIncidentStatus(id, 'ACKNOWLEDGED')}
            onResolveIncident={(id) => handleUpdateIncidentStatus(id, 'RESOLVED')}
          />
        </section>

        {/* Right Column: Alert list + Incident Timeline */}
        <section className="dashboard-col col-alerts">
          <AlertsTimeline
            incidents={incidents}
            onUpdateStatus={handleUpdateIncidentStatus}
            onSelectIncident={handleSelectIncident}
          />
        </section>
      </main>

      {/* Footer Info Strip */}
      <footer className="dashboard-footer">
        <div className="footer-left">
          <span>RAKSHAQ v1.0 &bull; Women's Night-Shift Commute Telemetry Security System</span>
        </div>
        <div className="footer-center">
          <span>Mode: <strong>{USE_MOCK ? `MOCK (${selectedScenario})` : `LIVE (${API_URL})`}</strong> &bull; Auto-refresh 3s</span>
        </div>
        <div className="footer-right">
          <span>Chennai Pallavaram-OMR Corridor</span>
        </div>
      </footer>
    </div>
  );
}
