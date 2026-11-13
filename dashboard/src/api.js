/**
 * RAKSHAQ Dashboard API Layer
 * Connects to FastAPI backend (at VITE_API_URL) or runs in interactive mock/replay mode.
 */

import tripMock from './mock/trip.json';
import locationsNormal from './mock/locations_normal.json';
import locationsDeviation from './mock/locations_deviation.json';
import locationsStop from './mock/locations_stop.json';
import locationsMismatch from './mock/locations_gps_mismatch.json';
import locationsUnavailable from './mock/locations_unavailable.json';

import analysisNormal from './mock/analysis_normal.json';
import analysisDeviation from './mock/analysis_deviation.json';
import analysisStop from './mock/analysis_stop.json';
import analysisDuress from './mock/analysis_duress.json';
import analysisMissedCheckin from './mock/analysis_missed_checkin.json';
import analysisUnavailable from './mock/analysis_unavailable.json';
import analysisMismatch from './mock/analysis_gps_mismatch.json';

import initialIncidents from './mock/incidents.json';

// Support VITE_API_URL (default http://localhost:8000) with fallback to VITE_API_BASE_URL
export const API_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const PREVIEW_MODE = new URLSearchParams(window.location.search).get('mode') === 'preview';
export const USE_MOCK = PREVIEW_MODE || String(import.meta.env.VITE_USE_MOCK).toLowerCase() === 'true';

// ---------------------------------------------------------------------------
// Normalisation Layer (Requirement 2)
// Normalises backend/mock responses in one place:
// Converts latitude/longitude & ISO datetimes to { lat, lng, ts } and splits by source.
// ---------------------------------------------------------------------------

export function normalizeLocation(loc) {
  if (!loc) return null;
  const lat = Number(loc.latitude ?? loc.lat);
  const lng = Number(loc.longitude ?? loc.lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    throw new Error('Trip location response is missing valid coordinates.');
  }
  const ts = loc.recorded_at ?? loc.ts;
  if (!ts) throw new Error('Trip location response is missing its recorded timestamp.');
  const speed = Number(loc.speed ?? 0);
  const source = loc.source ? String(loc.source).toUpperCase() : 'EMPLOYEE';

  return {
    id: loc.id,
    trip_id: loc.trip_id,
    source,
    lat,
    lng,
    speed,
    ts,
    // Keep aliases for full component compatibility
    latitude: lat,
    longitude: lng,
    recorded_at: ts
  };
}

export function splitLocations(locations = []) {
  const employeeTrail = [];
  const driverTrail = [];

  for (const item of locations) {
    const norm = normalizeLocation(item);
    if (!norm) continue;
    if (norm.source === 'EMPLOYEE') {
      employeeTrail.push(norm);
    } else if (norm.source === 'DRIVER') {
      driverTrail.push(norm);
    }
  }

  return { employeeTrail, driverTrail };
}

export function normalizeIncident(inc) {
  if (!inc) return null;
  const lat = inc.latitude != null ? Number(inc.latitude) : inc.lat != null ? Number(inc.lat) : null;
  const lng = inc.longitude != null ? Number(inc.longitude) : inc.lng != null ? Number(inc.lng) : null;
  const ts = inc.created_at ?? inc.ts;
  if (!ts) throw new Error('Incident response is missing its created timestamp.');

  return {
    id: inc.id,
    trip_id: inc.trip_id,
    incident_type: inc.incident_type,
    severity: inc.severity,
    status: inc.status,
    description: inc.description,
    lat,
    lng,
    ts,
    // Keep aliases for map popups and timeline
    latitude: lat,
    longitude: lng,
    created_at: ts
  };
}

export function normalizeTrip(trip) {
  if (!trip) return null;
  return {
    ...trip,
    id: trip.id,
    employee_id: trip.employee_id,
    driver_id: trip.driver_id,
    vehicle_id: trip.vehicle_id,
    pickup_location: trip.pickup_location,
    destination: trip.destination,
    status: trip.status,
    planned_route: trip.planned_route || [],
    started_at: trip.started_at,
    ended_at: trip.ended_at,
    last_employee_heartbeat_at: trip.last_employee_heartbeat_at,
    last_driver_heartbeat_at: trip.last_driver_heartbeat_at,
    last_checkin_at: trip.last_checkin_at
  };
}

// ---------------------------------------------------------------------------
// Scenario Definitions & Configurations (Used in MOCK mode)
// ---------------------------------------------------------------------------
export const SCENARIOS = {
  NORMAL: {
    key: 'NORMAL',
    label: 'Normal',
    locations: locationsNormal,
    analysis: analysisNormal,
    activeIncidentType: null,
    tripStatus: 'ACTIVE',
    advancesHeartbeat: true
  },
  DEVIATION: {
    key: 'DEVIATION',
    label: 'Deviation',
    locations: locationsDeviation,
    analysis: analysisDeviation,
    activeIncidentType: 'ROUTE_DEVIATION',
    tripStatus: 'ALERT',
    advancesHeartbeat: true
  },
  STOP: {
    key: 'STOP',
    label: 'Stop',
    locations: locationsStop,
    analysis: analysisStop,
    activeIncidentType: 'UNEXPECTED_STOP',
    tripStatus: 'ALERT',
    advancesHeartbeat: true
  },
  DURESS: {
    key: 'DURESS',
    label: 'Duress',
    locations: locationsDeviation,
    analysis: analysisDuress,
    activeIncidentType: 'DURESS_PIN',
    tripStatus: 'ALERT',
    advancesHeartbeat: true
  },
  MISSED_CHECKIN: {
    key: 'MISSED_CHECKIN',
    label: 'Missed check-in',
    locations: locationsNormal,
    analysis: analysisMissedCheckin,
    activeIncidentType: 'MISSED_CHECKIN',
    tripStatus: 'ALERT',
    advancesHeartbeat: true
  },
  PHONE_SHUTDOWN: {
    key: 'PHONE_SHUTDOWN',
    label: 'Phone shutdown',
    locations: locationsNormal,
    analysis: {
      trip_id: '1',
      flags: ['MISSED_CHECKIN'],
      trust_score: 65,
      reasons: [
        'CRITICAL: Employee telemetry heartbeat terminated mid-corridor (> 60s timeout)',
        'Independent cab telemetry stream active'
      ],
      gps_status: 'OK'
    },
    activeIncidentType: 'MISSED_CHECKIN',
    tripStatus: 'ALERT',
    advancesHeartbeat: false
  }
};

// ---------------------------------------------------------------------------
// Mock Replay State (Simulates real-time telemetry streaming)
// ---------------------------------------------------------------------------
const state = {
  scenario: 'NORMAL',
  step: 8,
  isPlaying: true,
  lastStepTimestamp: Date.now(),
  lastEmployeePing: Date.now() - 3000,
  lastDriverPing: Date.now() - 2000,
  forcedHeartbeatStaleSeconds: null,
  forcedGpsStatus: null,
  restrictedNightDuty: false,
  incidents: JSON.parse(JSON.stringify(initialIncidents))
};

const replayListeners = new Set();
function notifyListeners() {
  replayListeners.forEach((fn) => {
    try {
      fn({ ...state, scenarioConfig: SCENARIOS[state.scenario] });
    } catch (e) {
      console.error('Listener notification error:', e);
    }
  });
}

export function subscribeReplayState(fn) {
  replayListeners.add(fn);
  fn({ ...state, scenarioConfig: SCENARIOS[state.scenario] });
  return () => replayListeners.delete(fn);
}

export function setScenario(scenarioKey) {
  const normalizedKey = scenarioKey.toUpperCase().replace(/[\s-]/g, '_');
  const targetScenario = SCENARIOS[normalizedKey] || SCENARIOS.NORMAL;
  
  state.scenario = targetScenario.key;
  state.step = targetScenario.key === 'STOP' ? 14 : targetScenario.key === 'DEVIATION' || targetScenario.key === 'DURESS' ? 18 : 8;
  state.lastStepTimestamp = Date.now();

  state.incidents = JSON.parse(JSON.stringify(initialIncidents));

  if (targetScenario.key === 'NORMAL') {
    state.incidents.forEach((inc) => {
      inc.status = 'RESOLVED';
    });
    state.lastEmployeePing = Date.now() - 3000;
  } else if (targetScenario.key === 'PHONE_SHUTDOWN') {
    state.lastEmployeePing = Date.now() - 52000;
    const targetInc = state.incidents.find((i) => i.incident_type === 'MISSED_CHECKIN');
    if (targetInc) targetInc.status = 'OPEN';
  } else {
    state.incidents.forEach((inc) => {
      if (inc.incident_type === targetScenario.activeIncidentType) {
        inc.status = 'OPEN';
      } else {
        inc.status = 'RESOLVED';
      }
    });
    if (targetScenario.key === 'DURESS') {
      const devInc = state.incidents.find((i) => i.incident_type === 'ROUTE_DEVIATION');
      if (devInc) devInc.status = 'OPEN';
    }
    state.lastEmployeePing = Date.now() - 3000;
  }

  state.lastDriverPing = Date.now() - 2000;
  notifyListeners();
}

export function getScenario() {
  return state.scenario;
}

export function advanceReplayStep() {
  if (!state.isPlaying) return;

  const currentCfg = SCENARIOS[state.scenario] || SCENARIOS.NORMAL;
  const maxPairs = Math.floor(currentCfg.locations.length / 2);

  if (state.step < maxPairs - 1) {
    state.step += 1;
    state.lastStepTimestamp = Date.now();

    if (currentCfg.advancesHeartbeat) {
      state.lastEmployeePing = Date.now();
    }
    state.lastDriverPing = Date.now();

    notifyListeners();
  }
}

export function setReplayStep(stepNumber) {
  state.step = Math.max(0, stepNumber);
  notifyListeners();
}

export function resetReplay() {
  const currentCfg = SCENARIOS[state.scenario] || SCENARIOS.NORMAL;
  state.step = 2;
  state.isPlaying = true;
  state.forcedHeartbeatStaleSeconds = null;
  state.forcedGpsStatus = null;
  
  if (currentCfg.advancesHeartbeat) {
    state.lastEmployeePing = Date.now() - 3000;
  } else {
    state.lastEmployeePing = Date.now() - 52000;
  }
  state.lastDriverPing = Date.now() - 2000;
  notifyListeners();
}

export function toggleReplayPlayPause() {
  state.isPlaying = !state.isPlaying;
  notifyListeners();
  return state.isPlaying;
}

export function setForcedHeartbeatStale(secondsOrNull) {
  state.forcedHeartbeatStaleSeconds = secondsOrNull;
  if (secondsOrNull !== null) {
    state.lastEmployeePing = Date.now() - (secondsOrNull * 1000);
  } else {
    state.lastEmployeePing = Date.now() - 2000;
  }
  notifyListeners();
}

export function toggleMockGpsStatus() {
  if (state.forcedGpsStatus === 'UNAVAILABLE') {
    state.forcedGpsStatus = 'OK';
  } else {
    state.forcedGpsStatus = 'UNAVAILABLE';
  }
  notifyListeners();
  return state.forcedGpsStatus;
}

// ---------------------------------------------------------------------------
// ENDPOINTS IMPLEMENTATION
// ---------------------------------------------------------------------------

/**
 * GET /trips
 * Returns recent trips across lifecycle states for dashboard totals and selection.
 */
export async function getTrips() {
  if (USE_MOCK) {
    const activeTrip = await getActiveTrip();
    return activeTrip ? [activeTrip] : [];
  }

  const res = await fetch(`${API_URL}/trips?limit=500`);
  if (!res.ok) {
    throw new Error(`Failed to fetch trips (${res.status}): ${res.statusText}`);
  }
  const data = await res.json();
  if (!Array.isArray(data)) {
    throw new Error('Invalid trips response: expected an array.');
  }
  return data.map(normalizeTrip);
}

/**
 * GET /employees
 * PIN hashes are never returned; pin_configured is readiness metadata only.
 */
export async function getEmployees() {
  if (USE_MOCK) {
    return [{
      ...tripMock.employee,
      id: tripMock.employee?.id ?? tripMock.employee_id,
      email: null,
      pin_configured: true
    }];
  }

  const res = await fetch(`${API_URL}/employees`);
  if (!res.ok) {
    throw new Error(`Failed to fetch employees (${res.status}): ${res.statusText}`);
  }
  const data = await res.json();
  if (!Array.isArray(data)) {
    throw new Error('Invalid employees response: expected an array.');
  }
  return data;
}

/**
 * GET /drivers
 */
export async function getDrivers() {
  if (USE_MOCK) {
    return [await getDriver(tripMock.driver?.id ?? tripMock.driver_id)];
  }

  const res = await fetch(`${API_URL}/drivers`);
  if (!res.ok) {
    throw new Error(`Failed to fetch drivers (${res.status}): ${res.statusText}`);
  }
  const data = await res.json();
  if (!Array.isArray(data)) {
    throw new Error('Invalid drivers response: expected an array.');
  }
  return data;
}

/**
 * GET /trips/active
 * Automatically picks the first active trip from the backend list, or null if none.
 */
export async function getActiveTrip() {
  if (USE_MOCK) {
    advanceReplayStep();

    const currentCfg = SCENARIOS[state.scenario] || SCENARIOS.NORMAL;
    const hasActiveIncidents = state.incidents.some(
      (inc) => inc.status === 'OPEN' || inc.status === 'ACKNOWLEDGED'
    );
    const tripStatus = hasActiveIncidents ? 'ALERT' : 'ACTIVE';

    const empHeartbeatIso = new Date(state.lastEmployeePing).toISOString();
    const drvHeartbeatIso = new Date(state.lastDriverPing).toISOString();

    return normalizeTrip({
      ...tripMock,
      status: tripStatus,
      last_employee_heartbeat_at: empHeartbeatIso,
      last_driver_heartbeat_at: drvHeartbeatIso,
      current_step: state.step,
      scenario: state.scenario,
      driver: {
        ...tripMock.driver,
        night_duty_eligible: !state.restrictedNightDuty
      }
    });
  }

  const res = await fetch(`${API_URL}/trips/active`);
  if (!res.ok) {
    throw new Error(`Failed to fetch active trips (${res.status}): ${res.statusText}`);
  }
  const data = await res.json();
  if (!Array.isArray(data)) {
    throw new Error('Invalid active trips response: expected an array.');
  }
  const firstActive = data[0] || null;
  if (!firstActive) return null;

  return normalizeTrip(firstActive);
}

/**
 * GET /trips/{id}
 */
export async function getTrip(tripId) {
  if (USE_MOCK) {
    return normalizeTrip(tripMock);
  }

  const res = await fetch(`${API_URL}/trips/${tripId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch trip ${tripId} (${res.status}): ${res.statusText}`);
  }
  const data = await res.json();
  return normalizeTrip(data);
}

/**
 * GET /trips/{id}/locations
 * Returns normalised GPS pings with { lat, lng, ts } and splits by source into employeeTrail & driverTrail.
 */
export async function getTripLocations(tripId) {
  if (USE_MOCK) {
    const currentCfg = SCENARIOS[state.scenario] || SCENARIOS.NORMAL;
    const allLocs = currentCfg.locations;

    const pointsCount = Math.min((state.step + 1) * 2, allLocs.length);
    const sliced = allLocs.slice(0, pointsCount);

    let filtered = sliced;
    if (state.forcedGpsStatus === 'UNAVAILABLE') {
      filtered = sliced.filter((l) => l.source === 'EMPLOYEE');
    }

    const normalized = filtered.map(normalizeLocation);
    const { employeeTrail, driverTrail } = splitLocations(normalized);

    const result = normalized;
    result.employeeTrail = employeeTrail;
    result.driverTrail = driverTrail;
    return result;
  }

  const res = await fetch(`${API_URL}/trips/${tripId}/locations`);
  if (!res.ok) {
    throw new Error(`Failed to fetch trip locations (${res.status}): ${res.statusText}`);
  }
  const raw = await res.json();
  if (!Array.isArray(raw)) {
    throw new Error(`Invalid locations response for trip ${tripId}: expected an array.`);
  }
  const list = raw;
  const normalized = list.map(normalizeLocation);
  const { employeeTrail, driverTrail } = splitLocations(normalized);

  const result = normalized;
  result.employeeTrail = employeeTrail;
  result.driverTrail = driverTrail;
  return result;
}

/**
 * GET /incidents
 * Returns list of incidents ordered newest first, normalised to { lat, lng, ts }.
 */
export async function getIncidents() {
  if (USE_MOCK) {
    return [...state.incidents]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .map(normalizeIncident);
  }

  const res = await fetch(`${API_URL}/incidents`);
  if (!res.ok) {
    throw new Error(`Failed to fetch incidents (${res.status}): ${res.statusText}`);
  }
  const data = await res.json();
  if (!Array.isArray(data)) {
    throw new Error('Invalid incidents response: expected an array.');
  }
  const list = data;
  return list
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .map(normalizeIncident);
}

/**
 * GET /trips/{id}/analysis
 * ML output shape: { trip_id, flags, trust_score, reasons, gps_status }
 */
export async function getTripAnalysis(tripId) {
  if (USE_MOCK) {
    if (state.forcedGpsStatus === 'UNAVAILABLE') {
      return {
        ...analysisUnavailable,
        trip_id: String(tripId)
      };
    }

    const currentCfg = SCENARIOS[state.scenario] || SCENARIOS.NORMAL;
    return {
      ...currentCfg.analysis,
      trip_id: String(tripId)
    };
  }

  const res = await fetch(`${API_URL}/trips/${tripId}/analysis`);
  if (!res.ok) {
    throw new Error(`Failed to fetch trip analysis (${res.status}): ${res.statusText}`);
  }
  return res.json();
}

/**
 * GET /drivers/{id}
 */
export async function getDriver(driverId) {
  if (USE_MOCK) {
    return {
      id: driverId,
      name: tripMock.driver?.name || 'Rajesh Kumar',
      phone: tripMock.driver?.phone || '+91 98401 23456',
      license_no: tripMock.driver?.license_no || 'TN-07-20180004521',
      trust_score: 92.0,
      night_duty_eligible: !state.restrictedNightDuty
    };
  }

  const res = await fetch(`${API_URL}/drivers/${driverId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch driver ${driverId} (${res.status}): ${res.statusText}`);
  }
  return res.json();
}

/**
 * PATCH /incidents/{id}
 * Updates incident status (OPEN -> ACKNOWLEDGED -> RESOLVED -> FALSE_ALARM)
 */
export async function updateIncident(incidentId, updateData) {
  if (USE_MOCK) {
    const target = state.incidents.find((inc) => inc.id === incidentId);
    if (target) {
      if (updateData.status) target.status = updateData.status;
      if (updateData.severity) target.severity = updateData.severity;
      if (updateData.description) target.description = updateData.description;
      notifyListeners();
      return normalizeIncident({ ...target });
    }
    throw new Error(`Incident with id ${incidentId} not found`);
  }

  const res = await fetch(`${API_URL}/incidents/${incidentId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updateData)
  });
  if (!res.ok) {
    throw new Error(`Failed to update incident (${res.status}): ${res.statusText}`);
  }
  const updated = await res.json();
  return normalizeIncident(updated);
}

/**
 * PATCH /drivers/{id}
 * Updates driver profile or night_duty_eligible status.
 */
export async function updateDriver(driverId, updateData) {
  if (USE_MOCK) {
    if (updateData.night_duty_eligible !== undefined) {
      state.restrictedNightDuty = !updateData.night_duty_eligible;
    }
    notifyListeners();
    return {
      id: driverId,
      name: tripMock.driver?.name || 'Rajesh Kumar',
      phone: tripMock.driver?.phone || '+91 98401 23456',
      trust_score: 92.0,
      night_duty_eligible: !state.restrictedNightDuty,
      ...updateData
    };
  }

  const res = await fetch(`${API_URL}/drivers/${driverId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updateData)
  });
  if (!res.ok) {
    throw new Error(`Failed to update driver ${driverId} (${res.status}): ${res.statusText}`);
  }
  return res.json();
}
