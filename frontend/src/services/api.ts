/**
 * Telemetry, Trip, Auth & Safety Check-In API Service for RAKSHAQ.
 * Communicates with FastAPI backend at http://127.0.0.1:8000.
 * Supports dual property mapping (tripId and trip_id) and offline fallback generation.
 */

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export interface AuthVerifyResponse {
  status: string;
  employee?: {
    id: number | string;
    name: string;
    employee_id?: string;
    phone?: string;
  };
  token?: string;
  fallback?: boolean;
  [key: string]: any;
}

export interface TripStartResponse {
  trip_id: string | number;
  tripId: string | number;
  status: string;
  started_at?: string;
  employee_id?: number;
  fallback?: boolean;
  [key: string]: any;
}

export interface TelemetryResponse {
  status: string;
  trip_id?: string | number;
  tripId?: string | number;
  latitude?: number;
  longitude?: number;
  trust_score?: number;
  trustScore?: number;
  flags?: string[];
  fallback?: boolean;
  [key: string]: any;
}

export interface CheckInResponse {
  status: string;
  message?: string;
  trip_id?: string | number;
  tripId?: string | number;
  timestamp?: string;
  duress_triggered?: boolean;
  fallback?: boolean;
  [key: string]: any;
}

export interface TripCloseResponse {
  status: string;
  trip_id?: string | number;
  tripId?: string | number;
  ended_at?: string;
  doorstep_confirmed?: boolean;
  fallback?: boolean;
  [key: string]: any;
}

export interface SOSResponse {
  status: string;
  trip_id?: string | number;
  tripId?: string | number;
  incident_id?: string | number;
  incidentId?: string | number;
  trip_status?: string;
  timestamp: string;
  fallback?: boolean;
  [key: string]: any;
}

/**
 * Verifies employee mobile authentication.
 * POST http://127.0.0.1:8000/api/auth/verify
 */
export async function verifyEmployeeAuth(
  mobileNumber: string = '+91 98765 43210',
  employeeId: string = 'EMP-4092'
): Promise<AuthVerifyResponse> {
  const url = `${API_BASE_URL}/api/auth/verify`;
  const payload = {
    mobileNumber,
    mobile_number: mobileNumber,
    employeeId,
    employee_id: employeeId,
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.warn(`[RAKSHAQ API] Auth verify fallback at ${url}:`, error);
    return {
      status: 'VERIFIED',
      employee: {
        id: 1,
        name: 'Ananya Sharma',
        employee_id: employeeId,
        phone: mobileNumber,
      },
      token: 'mock-jwt-auth-session',
      fallback: true,
    };
  }
}

/**
 * Initiates a new monitored commute trip.
 * POST http://127.0.0.1:8000/api/trip/start
 */
export async function startMonitoredTrip(
  userId: string | number = 1,
  metadata?: Record<string, any>
): Promise<TripStartResponse> {
  const url = `${API_BASE_URL}/api/trip/start`;
  const payload = {
    userId,
    user_id: userId,
    pickup_location: metadata?.pickup_location || 'Cyber Gateway Tech Park',
    destination: metadata?.destination || 'Sarjapur Safe Corridor',
    metadata: metadata || {},
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}: ${response.statusText}`);
    }

    const data: TripStartResponse = await response.json();
    const resolvedId = data.tripId || data.trip_id;
    return {
      ...data,
      trip_id: resolvedId,
      tripId: resolvedId,
    };
  } catch (error) {
    console.warn(`[RAKSHAQ API] Backend unavailable at ${url}. Operating in offline mock mode.`, error);
    const mockId = `mock-${Date.now().toString().slice(-6)}`;
    return {
      trip_id: mockId,
      tripId: mockId,
      status: 'ACTIVE',
      started_at: new Date().toISOString(),
      fallback: true,
    };
  }
}

/**
 * Streams live GPS coordinates and telemetry.
 * POST http://127.0.0.1:8000/api/trip/telemetry
 */
export async function sendTelemetryUpdate(
  tripId: string | number,
  latitude: number,
  longitude: number,
  speed: number = 32.0
): Promise<TelemetryResponse> {
  const url = `${API_BASE_URL}/api/trip/telemetry`;
  const payload = {
    tripId,
    trip_id: tripId,
    latitude,
    longitude,
    speed,
    source: 'EMPLOYEE',
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`);
    }

    const data: TelemetryResponse = await response.json();
    const resolvedScore = data.trustScore ?? data.trust_score ?? 98;
    return {
      ...data,
      trip_id: data.tripId || data.trip_id || tripId,
      tripId: data.tripId || data.trip_id || tripId,
      trustScore: resolvedScore,
      trust_score: resolvedScore,
    };
  } catch (error) {
    console.warn(`[RAKSHAQ API] Telemetry sync offline at ${url}. Using simulated score.`, error);
    const simulatedScore = Math.floor(96 + Math.random() * 4);
    return {
      status: 'fallback',
      trip_id: tripId,
      tripId: tripId,
      latitude,
      longitude,
      trustScore: simulatedScore,
      trust_score: simulatedScore,
      flags: [],
      fallback: true,
    };
  }
}

/**
 * Submits periodic safety check-in PIN.
 * POST http://127.0.0.1:8000/api/trip/check-in
 * Normal PIN (1234) safely confirms.
 * Duress PIN (9999) silently escalates to CRITICAL incident.
 */
export async function submitSafetyCheckIn(
  tripId: string | number,
  pin: string,
  pinType?: 'NORMAL' | 'DURESS',
  latitude: number = 12.9716,
  longitude: number = 77.5946
): Promise<CheckInResponse> {
  const url = `${API_BASE_URL}/api/trip/check-in`;
  const isDuress = pin === '9999' || pinType === 'DURESS';
  const payload = {
    tripId,
    trip_id: tripId,
    pin,
    pin_type: isDuress ? 'DURESS' : 'NORMAL',
    status: 'ACKNOWLEDGED',
    latitude,
    longitude,
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`);
    }

    const data: CheckInResponse = await response.json();
    return {
      ...data,
      trip_id: data.tripId || data.trip_id || tripId,
      tripId: data.tripId || data.trip_id || tripId,
      duress_triggered: data.duress_triggered ?? isDuress,
    };
  } catch (error) {
    console.warn(`[RAKSHAQ API] Safety check-in fallback at ${url}:`, error);
    return {
      status: 'ACKNOWLEDGED',
      message: 'Check-in verified successfully (offline fallback)',
      trip_id: tripId,
      tripId: tripId,
      timestamp: new Date().toISOString(),
      duress_triggered: isDuress,
      fallback: true,
    };
  }
}

/**
 * Closes monitored trip with doorstep confirmation.
 * POST http://127.0.0.1:8000/api/trip/close
 */
export async function closeTrip(
  tripId: string | number,
  confirmationMethod: string = 'DOORSTEP_CONFIRM'
): Promise<TripCloseResponse> {
  const url = `${API_BASE_URL}/api/trip/close`;
  const payload = {
    tripId,
    trip_id: tripId,
    confirmation_method: confirmationMethod,
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const data: TripCloseResponse = await response.json();
    return {
      ...data,
      trip_id: data.tripId || data.trip_id || tripId,
      tripId: data.tripId || data.trip_id || tripId,
    };
  } catch (error) {
    console.warn(`[RAKSHAQ API] Close trip fallback at ${url}:`, error);
    return {
      status: 'COMPLETED',
      trip_id: tripId,
      tripId: tripId,
      ended_at: new Date().toISOString(),
      doorstep_confirmed: true,
      fallback: true,
    };
  }
}

/**
 * Triggers instant emergency SOS alert.
 * POST http://127.0.0.1:8000/api/trip/sos
 */
export async function triggerEmergencySOS(
  tripId: string | number | null,
  latitude: number = 12.9716,
  longitude: number = 77.5946
): Promise<SOSResponse> {
  const url = `${API_BASE_URL}/api/trip/sos`;
  const payload = {
    tripId: tripId || 0,
    trip_id: tripId || 0,
    latitude,
    longitude,
    message: 'EMERGENCY SOS: Immediate passenger distress signal triggered',
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`);
    }

    const data: SOSResponse = await response.json();
    const resolvedIncidentId = data.incidentId || data.incident_id || 'INC-SOS-01';
    return {
      ...data,
      trip_id: data.tripId || data.trip_id || tripId || '0',
      tripId: data.tripId || data.trip_id || tripId || '0',
      incident_id: resolvedIncidentId,
      incidentId: resolvedIncidentId,
    };
  } catch (error) {
    console.warn(`[RAKSHAQ API] SOS dispatch offline fallback at ${url}:`, error);
    return {
      status: 'EMERGENCY_DISPATCHED_LOCAL',
      trip_id: tripId || '0',
      tripId: tripId || '0',
      incident_id: `offline-sos-${Date.now()}`,
      incidentId: `offline-sos-${Date.now()}`,
      trip_status: 'ALERT',
      timestamp: new Date().toISOString(),
      fallback: true,
    };
  }
}
