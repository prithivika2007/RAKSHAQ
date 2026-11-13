const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

interface Employee {
  id: number;
  name: string;
  phone: string;
  email: string;
}

interface Trip {
  id: number;
  employee_id: number;
  driver_id: number | null;
  vehicle_id: number | null;
  pickup_location: string;
  destination: string;
  planned_route: number[][] | null;
  status: string;
}

interface TripLocation {
  id: number;
  trip_id: number;
  source: string;
  latitude: number;
  longitude: number;
  speed: number | null;
}

interface Incident {
  id: number;
  trip_id: number;
  incident_type: string;
  severity: string;
  status: string;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, init);
  const responseText = await response.text();
  let data: unknown;

  if (responseText) {
    try {
      data = JSON.parse(responseText);
    } catch {
      throw new Error(`Backend returned an invalid response (${response.status}).`);
    }
  }

  if (!response.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? String(data.detail)
        : response.statusText;
    throw new Error(detail || `Request failed (${response.status}).`);
  }

  return data as T;
}

function jsonRequest(body: object): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export async function verifyEmployee(employeeId: number, phone: string) {
  return requestJson<Employee>(
    "/employees/verify",
    jsonRequest({ employee_id: employeeId, phone }),
  );
}

export async function startMonitoredTrip(employeeId: number) {
  const activeTrips = await requestJson<Trip[]>("/trips/active");
  const activeTrip = activeTrips.find((trip) => trip.employee_id === employeeId);
  if (activeTrip) {
    return { trip: activeTrip, resumed: true };
  }

  const scheduledTrips = await requestJson<Trip[]>(
    `/trips/scheduled?employee_id=${employeeId}`,
  );

  let trip = scheduledTrips[0];
  if (!trip) {
    trip = await requestJson<Trip>(
      "/trips",
      jsonRequest({
        employee_id: employeeId,
        pickup_location: "Old Mahabalipuram Road, Perungudi, Chennai",
        destination: "Sholinganallur, Chennai",
        planned_route: [
          [12.9279, 80.208],
          [12.922, 80.213],
          [12.912, 80.22],
          [12.9004, 80.2275],
        ],
      }),
    );
  }

  const startedTrip = await requestJson<Trip>(`/trips/${trip.id}/start`, {
    method: "POST",
  });
  return { trip: startedTrip, resumed: false };
}

export async function sendTelemetryUpdate(
  tripId: number,
  latitude: number,
  longitude: number,
) {
  return requestJson<TripLocation>(
    `/trips/${tripId}/locations`,
    jsonRequest({
      trip_id: tripId,
      source: "EMPLOYEE",
      latitude,
      longitude,
      speed: 30,
    }),
  );
}

export async function sendSafetyCheckIn(
  tripId: number,
  pin: string,
  latitude?: number,
  longitude?: number,
) {
  return requestJson<{ trip_id: number; status: string; message: string }>(
    `/trips/${tripId}/check-in`,
    jsonRequest({ trip_id: tripId, pin, latitude, longitude }),
  );
}

export async function sendEmergencySOS(
  tripId: number,
  latitude?: number,
  longitude?: number,
) {
  return requestJson<Incident>(
    "/incidents",
    jsonRequest({
      trip_id: tripId,
      incident_type: "SOS",
      severity: "CRITICAL",
      description: "Employee initiated an emergency SOS.",
      latitude,
      longitude,
    }),
  );
}

export async function closeMonitoredTrip(tripId: number) {
  return requestJson<Trip>(`/trips/${tripId}/complete`, { method: "POST" });
}
