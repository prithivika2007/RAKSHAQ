import React, { useState, useEffect, useRef } from 'react';
import {
  startMonitoredTrip,
  sendTelemetryUpdate,
  sendSafetyCheckIn,
  sendEmergencySOS,
  closeMonitoredTrip,
  verifyEmployee
} from './services/api';

interface Employee {
  id: number;
  name: string;
  phone: string;
  email: string;
}

interface TripInfo {
  id: number;
  pickup_location: string;
  destination: string;
  planned_route: number[][] | null;
}

interface TelemetryLog {
  timestamp: string;
  lat: number;
  lng: number;
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isPreview, setIsPreview] = useState(false);
  const [mobileNumber, setMobileNumber] = useState("+919840001234");
  const [employeeId, setEmployeeId] = useState("1");
  const [employee, setEmployee] = useState<Employee | null>(null);

  const [tripId, setTripId] = useState<number | null>(null);
  const [tripInfo, setTripInfo] = useState<TripInfo | null>(null);
  const [tripRoute, setTripRoute] = useState<number[][]>([]);
  const [isTripActive, setIsTripActive] = useState(false);

  const [isCheckInOpen, setIsCheckInOpen] = useState(false);
  const [pinInput, setPinInput] = useState("");
  const [checkInError, setCheckInError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [telemetryLogs, setTelemetryLogs] = useState<TelemetryLog[]>([]);
  const telemetryIndex = useRef(0);
  const lastLocation = useRef<{ lat: number; lng: number } | null>(null);

  // The demo portal streams points from the persisted trip's planned route.
  useEffect(() => {
    if (isPreview || !isTripActive || !tripId || tripRoute.length === 0) return;

    const interval = setInterval(async () => {
      const point = tripRoute[Math.min(telemetryIndex.current, tripRoute.length - 1)];
      telemetryIndex.current += 1;
      const [lat, lng] = point;

      try {
        await sendTelemetryUpdate(tripId, lat, lng);
        lastLocation.current = { lat, lng };
        setTelemetryLogs((prev) => [
          { timestamp: new Date().toLocaleTimeString(), lat, lng },
          ...prev.slice(0, 4)
        ]);
      } catch (error) {
        setStatusMessage(`GPS telemetry failed: ${error instanceof Error ? error.message : 'Request failed.'}`);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isPreview, isTripActive, tripId, tripRoute]);

  const handlePreview = () => {
    const dashboardUrl =
      import.meta.env.VITE_DASHBOARD_URL ||
      `${window.location.protocol}//${window.location.hostname}:5173/index.html?mode=preview`;
    window.location.assign(dashboardUrl);
  };

  const handleExitPreview = () => {
    setIsPreview(false);
    setIsTripActive(false);
    setEmployee(null);
    setTripId(null);
    setTripInfo(null);
    setTripRoute([]);
    setTelemetryLogs([]);
    setStatusMessage(null);
    lastLocation.current = null;
    telemetryIndex.current = 0;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMessage(null);
    const numericEmployeeId = Number(employeeId);
    if (!Number.isInteger(numericEmployeeId) || numericEmployeeId <= 0) {
      setStatusMessage("Enter the numeric employee ID shown by the Chennai seed script.");
      return;
    }

    try {
      const verifiedEmployee = await verifyEmployee(numericEmployeeId, mobileNumber);
      setEmployee(verifiedEmployee);
      setEmployeeId(String(verifiedEmployee.id));
      setIsAuthenticated(true);
      setStatusMessage("Employee verification successful.");
    } catch (error) {
      setStatusMessage(`Employee verification failed: ${error instanceof Error ? error.message : 'Request failed.'}`);
    }
  };

  const handleStartTrip = async () => {
    if (isPreview) {
      setStatusMessage("Demo-only preview. Starting trips is disabled.");
      return;
    }
    if (!employee) return;
    try {
      const { trip, resumed } = await startMonitoredTrip(employee.id);
      const route = trip.planned_route ?? [];
      setTripInfo(trip);
      setTripRoute(route);
      setTripId(trip.id);
      setIsTripActive(true);
      setTelemetryLogs([]);
      telemetryIndex.current = 0;
      lastLocation.current = null;
      setStatusMessage(
        resumed
          ? `Reconnected to active trip ${trip.id}.`
          : `Monitored trip ${trip.id} started.`
      );

      if (route.length > 0) {
        const [lat, lng] = route[0];
        try {
          await sendTelemetryUpdate(trip.id, lat, lng);
          lastLocation.current = { lat, lng };
          setTelemetryLogs([{ timestamp: new Date().toLocaleTimeString(), lat, lng }]);
          telemetryIndex.current = 1;
        } catch (error) {
          setStatusMessage(`Trip ${trip.id} started, but GPS telemetry failed: ${error instanceof Error ? error.message : 'Request failed.'}`);
        }
      } else {
        setStatusMessage(`Trip ${trip.id} started, but no planned route is available for demo GPS telemetry.`);
      }
    } catch (error) {
      setStatusMessage(`Could not start trip: ${error instanceof Error ? error.message : 'Request failed.'}`);
    }
  };

  const handlePinSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isPreview) {
      setCheckInError("Demo-only preview. Safety check-in is disabled.");
      return;
    }
    if (pinInput.length < 4 || !tripId) return;

    setCheckInError(null);
    try {
      await sendSafetyCheckIn(
        tripId,
        pinInput,
        lastLocation.current?.lat,
        lastLocation.current?.lng
      );
      setStatusMessage("Safety check-in confirmed.");
      setCheckInError(null);
      setPinInput("");
      setIsCheckInOpen(false);
    } catch (error) {
      setCheckInError(`Check-in failed: ${error instanceof Error ? error.message : 'Request failed.'}`);
    }
  };

  const handleCloseTrip = async () => {
    if (isPreview) {
      setStatusMessage("Demo-only preview. Trip completion is disabled.");
      return;
    }
    if (!tripId) return;
    try {
      const completedTrip = await closeMonitoredTrip(tripId);
      if (completedTrip.status !== "COMPLETED") {
        throw new Error("Backend did not confirm trip completion.");
      }
      setIsTripActive(false);
      setTripId(null);
      setTripInfo(null);
      setTripRoute([]);
      setTelemetryLogs([]);
      setStatusMessage("Trip completed safely.");
    } catch (error) {
      setStatusMessage(`Could not complete trip: ${error instanceof Error ? error.message : 'Request failed.'}`);
    }
  };

  const handleEmergencySOS = async () => {
    if (isPreview) {
      setStatusMessage("Demo-only preview. SOS is disabled and no alert was sent.");
      return;
    }
    if (!tripId) {
      setStatusMessage("Start a monitored trip before sending an SOS.");
      return;
    }
    try {
      await sendEmergencySOS(
        tripId,
        lastLocation.current?.lat,
        lastLocation.current?.lng
      );
      setStatusMessage("Emergency SOS acknowledged.");
    } catch (error) {
      setStatusMessage(`SOS failed: ${error instanceof Error ? error.message : 'Request failed.'}`);
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#020617', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif', padding: '24px' }}>

      {/* Full-Width Web Application Container */}
      <div style={{ width: '100%', maxWidth: '560px', backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '24px', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)', display: 'flex', flexDirection: 'column', overflow: 'hidden', color: '#f8fafc', padding: '32px', position: 'relative', gap: '24px' }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1e293b', paddingBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '24px' }}>🛡️</span>
            <span style={{ fontWeight: 'bold', fontSize: '18px', letterSpacing: '0.05em', color: '#f43f5e' }}>RAKSHAQ</span>
          </div>
          <span style={{ fontSize: '12px', backgroundColor: '#1e293b', color: '#94a3b8', padding: '4px 10px', borderRadius: '9999px', fontWeight: '500' }}>Web Portal</span>
        </div>

        {/* View 1: Login */}
        {!isAuthenticated && !isPreview ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', textAlign: 'center' }}>
            <div>
              <h2 style={{ fontSize: '22px', fontWeight: 'bold', color: '#f8fafc' }}>Employee Verification</h2>
              <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '6px' }}>Night-shift commute security portal.</p>
            </div>

            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px', textAlign: 'left' }}>
              <div>
                <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Registered Mobile Number</label>
                <input
                  type="text"
                  value={mobileNumber}
                  onChange={(e) => setMobileNumber(e.target.value)}
                  style={{ width: '100%', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '12px 14px', fontSize: '14px', color: '#f8fafc', outline: 'none', boxSizing: 'border-box' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Registered Employee ID</label>
                <input
                  type="text"
                  value={employeeId}
                  onChange={(e) => setEmployeeId(e.target.value)}
                  style={{ width: '100%', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '12px 14px', fontSize: '14px', color: '#f8fafc', outline: 'none', boxSizing: 'border-box' }}
                />
              </div>

              <button
                type="submit"
                style={{ width: '100%', padding: '14px', backgroundColor: '#e11d48', color: '#ffffff', fontWeight: '600', borderRadius: '12px', border: 'none', cursor: 'pointer', fontSize: '15px', marginTop: '8px' }}
              >
                Verify Employee 🔑
              </button>
            </form>

            {statusMessage && (
              <div role="alert" style={{ fontSize: '12px', color: '#fda4af', padding: '10px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}>
                {statusMessage}
              </div>
            )}

            <p style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
              Demo user: <span style={{ color: '#cbd5e1', fontWeight: '500' }}>Meera Subramaniam (run the Chennai seed script for the employee ID)</span>
            </p>
          </div>
        ) : (
          /* Existing employee dashboard for authenticated or preview mode */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {isPreview && (
              <div role="status" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', padding: '12px 14px', backgroundColor: '#422006', border: '1px solid #f59e0b', borderRadius: '12px' }}>
                <strong style={{ color: '#fcd34d', fontSize: '13px', letterSpacing: '0.04em' }}>DEMO PREVIEW MODE — SAMPLE DATA, READ-ONLY</strong>
                <button
                  type="button"
                  onClick={handleExitPreview}
                  style={{ padding: '8px 12px', backgroundColor: '#1e293b', color: '#f8fafc', border: '1px solid #64748b', borderRadius: '9px', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}
                >
                  Exit Preview
                </button>
              </div>
            )}
            <div>
              <div style={{ backgroundColor: 'rgba(30, 41, 59, 0.6)', border: '1px solid rgba(51, 65, 85, 0.5)', borderRadius: '16px', padding: '16px', marginBottom: '16px' }}>
                <p style={{ fontSize: '12px', color: '#94a3b8' }}>Employee Commute Session</p>
                <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#f8fafc', margin: '4px 0' }}>{employee?.name}</h3>
                <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>Employee ID: {employee?.id}</p>
                <p style={{ fontSize: '12px', color: '#fb7185', marginTop: '4px' }}>
                  Route: {tripInfo ? `${tripInfo.pickup_location} → ${tripInfo.destination}` : 'Chennai commute'}
                </p>
              </div>

              {isTripActive ? (
                <div style={{ backgroundColor: 'rgba(2, 44, 34, 0.5)', border: '1px solid rgba(22, 101, 52, 0.5)', borderRadius: '16px', padding: '16px', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', fontWeight: '600', fontSize: '14px' }}>
                      <span style={{ width: '9px', height: '9px', borderRadius: '50%', backgroundColor: '#34d399', display: 'inline-block' }}></span>
                      <span>Commute Monitored</span>
                    </span>
                    <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#94a3b8' }}>
                      {isPreview ? "DEMO-TRIP-001" : tripId}
                    </span>
                  </div>

                  <div style={{ fontSize: '12px', color: '#cbd5e1', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <p>📡 GPS Telemetry: <span style={{ color: '#34d399', fontWeight: 'bold' }}>{isPreview ? "Sample route data" : "Live backend stream (5s pulse)"}</span></p>
                    <p>🛡️ Safety Monitoring: <span style={{ color: '#34d399', fontWeight: 'bold' }}>{isPreview ? "Active — demo display only" : "Live backend monitoring"}</span></p>
                  </div>

                  {/* Telemetry Heartbeat Stream Box */}
                  {telemetryLogs.length > 0 && (
                    <div style={{ backgroundColor: '#020617', border: '1px solid #1e293b', borderRadius: '10px', padding: '10px', fontSize: '11px', fontFamily: 'monospace', color: '#94a3b8' }}>
                      <p style={{ margin: '0 0 4px 0', color: '#64748b', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{isPreview ? "Sample Telemetry Log" : "Live Telemetry Log"}</p>
                      {telemetryLogs.map((log, idx) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0' }}>
                          <span>[{log.timestamp}]</span>
                          <span style={{ color: '#38bdf8' }}>Lat: {log.lat}, Lng: {log.lng}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', paddingTop: '4px' }}>
                    <button
                      onClick={() => {
                        if (isPreview) {
                          setStatusMessage("Demo-only preview. Safety check-in is disabled.");
                          return;
                        }
                        setCheckInError(null);
                        setPinInput("");
                        setIsCheckInOpen(true);
                      }}
                      style={{ width: '100%', padding: '12px', backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '12px', fontSize: '13px', fontWeight: '600', color: '#f8fafc', cursor: 'pointer' }}
                    >
                      Security Check-In (Enter PIN) 🔒
                    </button>

                    <button
                      onClick={handleCloseTrip}
                      style={{ width: '100%', padding: '12px', backgroundColor: '#059669', color: '#ffffff', borderRadius: '12px', fontSize: '13px', fontWeight: '600', border: 'none', cursor: 'pointer' }}
                    >
                      Arrived at Doorstep / End Trip 🏡
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ backgroundColor: 'rgba(30, 41, 59, 0.4)', border: '1px solid rgba(51, 65, 85, 0.5)', borderRadius: '16px', padding: '28px', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <p style={{ fontSize: '13px', color: '#94a3b8' }}>Ready for night-shift commute.</p>
                  <button
                    onClick={handleStartTrip}
                    style={{ width: '100%', padding: '14px', backgroundColor: '#e11d48', color: '#ffffff', fontWeight: '600', borderRadius: '12px', border: 'none', cursor: 'pointer', fontSize: '15px' }}
                  >
                    Begin Monitored Trip 🚗
                  </button>
                </div>
              )}

              {statusMessage && (
                <div style={{ marginTop: '14px', textAlign: 'center', fontSize: '12px', padding: '10px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', color: '#cbd5e1' }}>
                  {statusMessage}
                </div>
              )}
            </div>

            <button
              onClick={handleEmergencySOS}
              style={{ width: '100%', padding: '14px', backgroundColor: '#dc2626', color: '#ffffff', fontWeight: '800', borderRadius: '14px', border: '1px solid #ef4444', textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '13px', cursor: 'pointer' }}
            >
              Emergency SOS 🚨
            </button>
          </div>
        )}

        <button
          type="button"
          onClick={handlePreview}
          style={{ width: '100%', padding: '12px', backgroundColor: '#1e293b', color: '#e2e8f0', fontWeight: '600', borderRadius: '12px', border: '1px solid #475569', cursor: 'pointer', fontSize: '14px' }}
        >
          Preview Dashboard
        </button>

        {/* Modal */}
        {isCheckInOpen && !isPreview && (
          <div style={{ position: 'absolute', inset: 0, backgroundColor: 'rgba(2, 6, 23, 0.95)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px', zIndex: 50 }}>
            <div style={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '24px', padding: '24px', width: '100%', maxWidth: '360px', display: 'flex', flexDirection: 'column', gap: '16px', textAlign: 'center', boxSizing: 'border-box' }}>
              <h4 style={{ fontWeight: 'bold', color: '#f8fafc', fontSize: '16px', margin: 0 }}>Security Check-In PIN</h4>
              <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>Enter your registered 4-digit safety PIN.</p>

              <form onSubmit={handlePinSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <input
                  type="password"
                  maxLength={4}
                  value={pinInput}
                  onChange={(e) => setPinInput(e.target.value)}
                  placeholder="****"
                  style={{ width: '140px', margin: '0 auto', textAlign: 'center', letterSpacing: '0.3em', fontSize: '20px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '10px', color: '#f8fafc', outline: 'none' }}
                />
                <div style={{ display: 'flex', gap: '10px', paddingTop: '6px' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setCheckInError(null);
                      setIsCheckInOpen(false);
                    }}
                    style={{ flex: 1, padding: '10px', backgroundColor: '#1e293b', color: '#94a3b8', fontSize: '13px', borderRadius: '12px', border: 'none', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{ flex: 1, padding: '10px', backgroundColor: '#e11d48', color: '#ffffff', fontSize: '13px', borderRadius: '12px', fontWeight: '600', border: 'none', cursor: 'pointer' }}
                  >
                    Submit PIN
                  </button>
                </div>
              </form>
              {checkInError && (
                <div role="alert" style={{ fontSize: '12px', color: '#fda4af' }}>
                  {checkInError}
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}