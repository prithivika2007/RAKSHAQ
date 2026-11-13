import React from 'react';

export default function OperationsOverview({
  trips,
  employees,
  drivers,
  incidents,
  selectedTripId,
  onSelectTrip
}) {
  const activeTrips = trips.filter((trip) => ['ACTIVE', 'ALERT'].includes(trip.status));
  const scheduledTrips = trips.filter((trip) => trip.status === 'SCHEDULED');
  const completedTrips = trips.filter((trip) => trip.status === 'COMPLETED');
  const openIncidents = incidents.filter((incident) =>
    ['OPEN', 'ACKNOWLEDGED'].includes(incident.status)
  );
  const configuredPins = employees.filter((employee) => employee.pin_configured).length;
  const nightEligibleDrivers = drivers.filter((driver) => driver.night_duty_eligible).length;
  const selectableTrips = [...trips].sort((a, b) => {
      const statusOrder = { ALERT: 0, ACTIVE: 1, SCHEDULED: 2, COMPLETED: 3, CANCELLED: 4 };
      return statusOrder[a.status] - statusOrder[b.status] || b.id - a.id;
    });

  const employeeNames = new Map(employees.map((employee) => [employee.id, employee.name]));

  return (
    <>
      <section className="operations-overview" aria-label="Live operations summary">
        <div className="operation-stat">
          <span className="operation-stat-label">EMPLOYEES</span>
          <strong>{employees.length}</strong>
          <span>{configuredPins} with safety PINs</span>
        </div>
        <div className="operation-stat">
          <span className="operation-stat-label">DRIVERS</span>
          <strong>{drivers.length}</strong>
          <span>{nightEligibleDrivers} night-duty eligible</span>
        </div>
        <div className="operation-stat">
          <span className="operation-stat-label">ACTIVE TRIPS</span>
          <strong>{activeTrips.length}</strong>
          <span>Active or alerting</span>
        </div>
        <div className="operation-stat">
          <span className="operation-stat-label">SCHEDULED</span>
          <strong>{scheduledTrips.length}</strong>
          <span>Awaiting pickup</span>
        </div>
        <div className="operation-stat">
          <span className="operation-stat-label">COMPLETED</span>
          <strong>{completedTrips.length}</strong>
          <span>In recent trip records</span>
        </div>
        <div className="operation-stat operation-stat-alerts">
          <span className="operation-stat-label">OPEN INCIDENTS</span>
          <strong>{openIncidents.length}</strong>
          <span>Open or acknowledged</span>
        </div>
      </section>

      <section className="operations-toolbar" aria-label="Trip and roster controls">
        <label className="trip-selector">
          <span>TRIP DETAILS</span>
          <select
            value={selectedTripId ?? ''}
            onChange={(event) => onSelectTrip(event.target.value ? Number(event.target.value) : null)}
            disabled={selectableTrips.length === 0}
          >
            {selectableTrips.length === 0 && <option value="">No trip records</option>}
            {selectableTrips.map((trip) => (
              <option key={trip.id} value={trip.id}>
                #{trip.id} - {trip.status} - {employeeNames.get(trip.employee_id) || `Employee #${trip.employee_id}`}
              </option>
            ))}
          </select>
        </label>

        <details className="roster-details">
          <summary>EMPLOYEE &amp; DRIVER RECORDS ({employees.length + drivers.length})</summary>
          <div className="roster-content">
            <section>
              <h3>Employees ({employees.length})</h3>
              {employees.length === 0 ? (
                <p className="roster-empty">No employee records returned by the backend.</p>
              ) : (
                <div className="roster-table-wrap">
                  <table>
                    <thead>
                      <tr><th>Employee</th><th>Contact</th><th>Record</th><th>Safety PINs</th></tr>
                    </thead>
                    <tbody>
                      {employees.map((employee) => (
                        <tr key={employee.id}>
                          <td>{employee.name} <span>#{employee.id}</span></td>
                          <td>{employee.phone}</td>
                          <td>Registered</td>
                          <td>{employee.pin_configured ? 'Configured' : 'Not configured'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
            <section>
              <h3>Drivers ({drivers.length})</h3>
              {drivers.length === 0 ? (
                <p className="roster-empty">No driver records returned by the backend.</p>
              ) : (
                <div className="roster-table-wrap">
                  <table>
                    <thead>
                      <tr><th>Driver</th><th>Contact</th><th>Trust</th><th>Night duty</th></tr>
                    </thead>
                    <tbody>
                      {drivers.map((driver) => (
                        <tr key={driver.id}>
                          <td>{driver.name} <span>#{driver.id}</span></td>
                          <td>{driver.phone}</td>
                          <td>{driver.trust_score}/100</td>
                          <td>{driver.night_duty_eligible ? 'Eligible' : 'Restricted'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
            <p className="roster-note">
              Employee verification is performed during login and is not stored as a persistent status. PIN readiness is shown instead.
            </p>
          </div>
        </details>
      </section>
    </>
  );
}
