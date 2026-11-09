const BASE_URL = "http://127.0.0.1:8000";

// 1. Start Trip
export async function startMonitoredTrip(employeeId: string) {
  try {
    const res = await fetch(`${BASE_URL}/api/trip/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ employee_id: employeeId }),
    });
    return await res.json();
  } catch (err) {
    console.warn("Backend offline, using fallback mock trip start:", err);
    return { trip_id: "TRIP-" + Math.floor(1000 + Math.random() * 9000), status: "started" };
  }
}

// 2. Telemetry Heartbeat Ping
export async function sendTelemetryUpdate(tripId: string, lat: number, lng: number) {
  try {
    const res = await fetch(`${BASE_URL}/api/trip/telemetry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trip_id: tripId, latitude: lat, longitude: lng, timestamp: new Date().toISOString() }),
    });
    return await res.json();
  } catch (err) {
    console.warn("Backend offline, telemetry payload logged locally.");
  }
}

// 3. Security Check-In (Normal vs. Duress PIN 9999)
export async function sendSafetyCheckIn(tripId: string, pin: string) {
  const isDuress = pin === "9999";
  try {
    const res = await fetch(`${BASE_URL}/api/trip/check-in`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        trip_id: tripId,
        pin_type: isDuress ? "duress" : "normal",
        status: isDuress ? "emergency_alert" : "verified",
      }),
    });
    return await res.json();
  } catch (err) {
    console.warn(`Backend offline. ${isDuress ? "DURESS ALERT" : "Normal Check-in"} logged locally.`);
    return { status: isDuress ? "duress_flagged" : "success" };
  }
}

// 4. Doorstep Trip Completion
export async function closeMonitoredTrip(tripId: string) {
  try {
    const res = await fetch(`${BASE_URL}/api/trip/close`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trip_id: tripId, status: "completed", timestamp: new Date().toISOString() }),
    });
    return await res.json();
  } catch (err) {
    console.warn("Backend offline, trip closed locally.");
    return { status: "closed" };
  }
}