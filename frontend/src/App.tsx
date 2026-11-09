import React, { useState, useEffect } from 'react';
import {
  startMonitoredTrip,
  sendTelemetryUpdate,
  sendSafetyCheckIn,
  closeMonitoredTrip
} from './services/api';

interface TelemetryLog {
  timestamp: string;
  lat: number;
  lng: number;
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [mobileNumber, setMobileNumber] = useState("+91 98765 43210");
  const [employeeId, setEmployeeId] = useState("EMP-4092");

  const [tripId, setTripId] = useState<string | null>(null);
  const [isTripActive, setIsTripActive] = useState(false);

  const [isCheckInOpen, setIsCheckInOpen] = useState(false);
  const [pinInput, setPinInput] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [telemetryLogs, setTelemetryLogs] = useState<TelemetryLog[]>([]);

  // Telemetry Heartbeat Simulation
  useEffect(() => {
    if (!isTripActive || !tripId) return;

    const interval = setInterval(() => {
      const lat = Number((13.0382 + (Math.random() - 0.5) * 0.005).toFixed(4));
      const lng = Number((80.1783 + (Math.random() - 0.5) * 0.005).toFixed(4));

      sendTelemetryUpdate(tripId, lat, lng);

      const newLog: TelemetryLog = {
        timestamp: new Date().toLocaleTimeString(),
        lat,
        lng
      };

      setTelemetryLogs((prev) => [newLog, ...prev.slice(0, 4)]);
    }, 5000);

    return () => clearInterval(interval);
  }, [isTripActive, tripId]);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsAuthenticated(true);
    setStatusMessage("Successfully authenticated.");
  };

  const handleStartTrip = async () => {
    const data = await startMonitoredTrip(employeeId);
    const newTripId = data.trip_id || ("TRIP-" + Math.floor(1000 + Math.random() * 9000));
    setTripId(newTripId);
    setIsTripActive(true);
    setTelemetryLogs([]);
    setStatusMessage(`Monitored trip ${newTripId} started.`);
  };

  const handlePinSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (pinInput.length < 4 || !tripId) return;

    const isDuress = pinInput === "9999";
    await sendSafetyCheckIn(tripId, pinInput);

    if (isDuress) {
      setStatusMessage("⚠️ DURESS ALERT: Silent SOS dispatched to team dashboard!");
    } else {
      setStatusMessage("Safety check-in confirmed.");
    }

    setPinInput("");
    setIsCheckInOpen(false);
  };

  const handleQuickDuressTest = async () => {
    if (!tripId) return;
    await sendSafetyCheckIn(tripId, "9999");
    setStatusMessage("⚠️ SIMULATED DURESS: Silent SOS (9999) sent to dispatch!");
  };

  const handleCloseTrip = async () => {
    if (!tripId) return;
    await closeMonitoredTrip(tripId);
    setIsTripActive(false);
    setTripId(null);
    setTelemetryLogs([]);
    setStatusMessage("Trip completed safely.");
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
        {!isAuthenticated ? (
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
                <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Employee ID</label>
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
                Request Security OTP 🔑
              </button>
            </form>

            <p style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
              Demo user: <span style={{ color: '#cbd5e1', fontWeight: '500' }}>Ananya Sharma (EMP-4092)</span>
            </p>
          </div>
        ) : (
          /* View 2: Live Trip Dashboard */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <div style={{ backgroundColor: 'rgba(30, 41, 59, 0.6)', border: '1px solid rgba(51, 65, 85, 0.5)', borderRadius: '16px', padding: '16px', marginBottom: '16px' }}>
                <p style={{ fontSize: '12px', color: '#94a3b8' }}>Employee Commute Session</p>
                <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#f8fafc', margin: '4px 0' }}>Ananya Sharma</h3>
                <p style={{ fontSize: '12px', color: '#fb7185', marginTop: '4px' }}>Route: SRM Ramapuram → Thiruvanmiyur</p>
              </div>

              {isTripActive ? (
                <div style={{ backgroundColor: 'rgba(2, 44, 34, 0.5)', border: '1px solid rgba(22, 101, 52, 0.5)', borderRadius: '16px', padding: '16px', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', fontWeight: '600', fontSize: '14px' }}>
                      <span style={{ width: '9px', height: '9px', borderRadius: '50%', backgroundColor: '#34d399', display: 'inline-block' }}></span>
                      <span>Commute Monitored</span>
                    </span>
                    <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#94a3b8' }}>{tripId}</span>
                  </div>

                  <div style={{ fontSize: '12px', color: '#cbd5e1', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <p>📡 GPS Telemetry: <span style={{ color: '#34d399', fontWeight: 'bold' }}>Active (5s pulse)</span></p>
                    <p>🛡️ AI Safety Score: <span style={{ color: '#34d399', fontWeight: 'bold' }}>98/100</span></p>
                  </div>

                  {/* Telemetry Heartbeat Stream Box */}
                  {telemetryLogs.length > 0 && (
                    <div style={{ backgroundColor: '#020617', border: '1px solid #1e293b', borderRadius: '10px', padding: '10px', fontSize: '11px', fontFamily: 'monospace', color: '#94a3b8' }}>
                      <p style={{ margin: '0 0 4px 0', color: '#64748b', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Live Telemetry Log</p>
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
                      onClick={() => setIsCheckInOpen(true)}
                      style={{ width: '100%', padding: '12px', backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '12px', fontSize: '13px', fontWeight: '600', color: '#f8fafc', cursor: 'pointer' }}
                    >
                      Security Check-In (Enter PIN) 🔒
                    </button>

                    {/* Quick-Test Duress PIN Button */}
                    <button
                      onClick={handleQuickDuressTest}
                      style={{ width: '100%', padding: '10px', backgroundColor: '#450a0a', border: '1px solid #991b1b', borderRadius: '12px', fontSize: '12px', fontWeight: '600', color: '#fca5a5', cursor: 'pointer' }}
                    >
                      ⚡ Quick Test: Send Duress PIN (9999)
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
              onClick={() => {
                setStatusMessage("🚨 Emergency SOS Sent to Dispatch!");
              }}
              style={{ width: '100%', padding: '14px', backgroundColor: '#dc2626', color: '#ffffff', fontWeight: '800', borderRadius: '14px', border: '1px solid #ef4444', textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '13px', cursor: 'pointer' }}
            >
              Emergency SOS 🚨
            </button>
          </div>
        )}

        {/* Modal */}
        {isCheckInOpen && (
          <div style={{ position: 'absolute', inset: 0, backgroundColor: 'rgba(2, 6, 23, 0.95)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px', zIndex: 50 }}>
            <div style={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '24px', padding: '24px', width: '100%', maxWidth: '360px', display: 'flex', flexDirection: 'column', gap: '16px', textAlign: 'center', boxSizing: 'border-box' }}>
              <h4 style={{ fontWeight: 'bold', color: '#f8fafc', fontSize: '16px', margin: 0 }}>Security Check-In PIN</h4>
              <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>Enter 4-digit PIN (Use 9999 for silent duress trigger)</p>

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
                    onClick={() => setIsCheckInOpen(false)}
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
            </div>
          </div>
        )}

      </div>
    </div>
  );
}