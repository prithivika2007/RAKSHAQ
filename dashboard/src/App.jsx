import React, { useState, useEffect, useCallback, useRef } from 'react';
import Navbar from './components/Navbar';
import ReplayControlBar from './components/ReplayControlBar';
import OperationsOverview from './components/OperationsOverview';
import ActiveTripCard from './components/ActiveTripCard';
import DriverTrustCard from './components/DriverTrustCard';
import LiveMap from './components/LiveMap';
import AlertsTimeline from './components/AlertsTimeline';
import {
  getTrips,
  getEmployees,
  getDrivers,
  getTripLocations,
  getIncidents,
  getTripAnalysis,
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
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [selectedTripId, setSelectedTripId] = useState(null);
  const selectedTripIdRef = useRef(null);
  const [trips, setTrips] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [locations, setLocations] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [hasLoadedDashboardData, setHasLoadedDashboardData] = useState(false);
  
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
  const fetchAllData = useCallback(async (preferredTripId = selectedTripIdRef.current) => {
    try {
      const [tripData, employeeData, driverData, incidentData] = await Promise.all([
        getTrips(),
        getEmployees(),
        getDrivers(),
        getIncidents()
      ]);
      const preferredTrip = tripData.find((trip) => trip.id === preferredTripId);
      const chosenTrip = preferredTrip || tripData.find((trip) => ['ALERT', 'ACTIVE'].includes(trip.status)) || tripData.find((trip) => trip.status === 'SCHEDULED') || tripData[0] || null;
      const trip = chosenTrip
        ? {
            ...chosenTrip,
            employee: employeeData.find((employee) => employee.id === chosenTrip.employee_id) || null,
            driver: driverData.find((driver) => driver.id === chosenTrip.driver_id) || null
          }
        : null;

      let locationsData = [];
      let analysisData = null;
      if (trip && trip.status !== 'SCHEDULED') {
        locationsData = await getTripLocations(trip.id);
      }
      if (trip && ['ACTIVE', 'ALERT'].includes(trip.status)) {
        analysisData = await getTripAnalysis(trip.id);
      }

      setTrips(tripData);
      setEmployees(employeeData);
      setDrivers(driverData);
      setIncidents(incidentData);
      setSelectedTrip(trip);
      setSelectedTripId(trip?.id ?? null);
      selectedTripIdRef.current = trip?.id ?? null;
      setLocations(locationsData);
      setAnalysis(analysisData);
      setHasLoadedDashboardData(true);

      // Backend healthy
      setIsBackendOffline(false);
      setLastError(null);
      setLastUpdated(Date.now());
    } catch (err) {
      console.error('Data polling error:', err);
      // Requirement 5: Keep last data instead of crashing if backend is offline
      if (!USE_MOCK) {
        setIsBackendOffline(true);
        setLastError(err instanceof Error ? err.message : 'Network error');
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
      await fetchAllData();
    } catch (err) {
      console.error(`Failed to update incident ${incidentId}:`, err);
      alert(`Could not update incident: ${err.message}`);
    }
  };

  // Handle Driver Night Duty toggle (Requirement 1: PATCH /drivers/{id})
  const handleToggleNightDuty = async (isRestricted) => {
    try {
      const driverId = selectedTrip?.driver?.id || selectedTrip?.driver_id;
      if (!driverId) {
        throw new Error('There is no assigned driver to update.');
      }
      const updatedDriver = await updateDriver(driverId, { night_duty_eligible: !isRestricted });
      setDrivers((prev) =>
        prev.map((driver) => (driver.id === driverId ? updatedDriver : driver))
      );
      setSelectedTrip((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          driver: updatedDriver
        };
      });
    } catch (err) {
      console.error('Failed to update driver night duty:', err);
      alert(`Driver update failed: ${err.message}`);
    }
  };

  const handleSelectTrip = (tripId) => {
    selectedTripIdRef.current = tripId;
    setSelectedTripId(tripId);
    fetchAllData(tripId);
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
          <span className="offline-badge">API ERROR</span>
          <span className="offline-msg">
            Could not load dashboard data from <code>{API_URL}</code> ({lastError || 'Request failed'}). Displaying the last successfully loaded data. Retrying every 3s...
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

      {hasLoadedDashboardData && (
        <OperationsOverview
          trips={trips}
          employees={employees}
          drivers={drivers}
          incidents={incidents}
          selectedTripId={selectedTripId}
          onSelectTrip={handleSelectTrip}
        />
      )}

      {/* Main Dashboard Grid */}
      <main className="dashboard-grid">
        {/* Left Column: Active Trip & Driver Trust Cards */}
        <section className="dashboard-col col-sidebar">
          {/* Requirement 3 & 4: Active trip card & empty state */}
          <ActiveTripCard trip={selectedTrip} />

          {/* Driver Trust Score card */}
          <DriverTrustCard
            analysis={analysis}
            driver={selectedTrip?.driver}
            onToggleNightDutyOverride={handleToggleNightDuty}
          />
        </section>

        {/* Center / Primary Column: Live Map */}
        <section className="dashboard-col col-map">
          {/* Live map */}
          <LiveMap
            isLiveTrip={['ACTIVE', 'ALERT'].includes(selectedTrip?.status)}
            plannedRoute={selectedTrip?.planned_route || []}
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
