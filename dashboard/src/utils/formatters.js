/**
 * Formatting helpers for RAKSHAQ Dashboard
 */

/**
 * Returns human-readable relative age from ISO string or timestamp
 * e.g. "4s ago", "45s ago", "2m 10s ago"
 */
export function formatHeartbeatAge(timestamp) {
  if (!timestamp) return { text: 'No signal', seconds: 9999 };
  const then = typeof timestamp === 'number' ? timestamp : new Date(timestamp).getTime();
  const now = Date.now();
  const diffSeconds = Math.max(0, Math.floor((now - then) / 1000));

  if (diffSeconds < 60) {
    return { text: `${diffSeconds}s ago`, seconds: diffSeconds };
  }
  const mins = Math.floor(diffSeconds / 60);
  const secs = diffSeconds % 60;
  return { text: `${mins}m ${secs}s ago`, seconds: diffSeconds };
}

/**
 * Format timestamp to 24-hr IST / local time HH:MM:SS
 */
export function formatTime(isoString) {
  if (!isoString) return '--:--:--';
  const d = new Date(isoString);
  return d.toLocaleTimeString('en-IN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

/**
 * Get color code for incident severity
 */
export function getSeverityStyle(severity) {
  switch (severity?.toUpperCase()) {
    case 'CRITICAL':
      return {
        bg: '#450a0a',
        border: '#dc2626',
        text: '#fecaca',
        badgeBg: '#ef4444',
        badgeText: '#ffffff'
      };
    case 'HIGH':
      return {
        bg: '#431407',
        border: '#ea580c',
        text: '#fed7aa',
        badgeBg: '#f97316',
        badgeText: '#ffffff'
      };
    case 'MEDIUM':
      return {
        bg: '#422006',
        border: '#d97706',
        text: '#fde68a',
        badgeBg: '#f59e0b',
        badgeText: '#000000'
      };
    case 'LOW':
    default:
      return {
        bg: '#0c2638',
        border: '#0284c7',
        text: '#bae6fd',
        badgeBg: '#0ea5e9',
        badgeText: '#ffffff'
      };
  }
}

/**
 * Get status badge style
 */
export function getStatusStyle(status) {
  switch (status?.toUpperCase()) {
    case 'OPEN':
      return { bg: '#991b1b', text: '#fee2e2', border: '#ef4444' };
    case 'ACKNOWLEDGED':
      return { bg: '#854d0e', text: '#fef3c7', border: '#eab308' };
    case 'RESOLVED':
      return { bg: '#14532d', text: '#dcfce7', border: '#22c55e' };
    case 'FALSE_ALARM':
      return { bg: '#27272a', text: '#e4e4e7', border: '#71717a' };
    default:
      return { bg: '#18181b', text: '#a1a1aa', border: '#3f3f46' };
  }
}

