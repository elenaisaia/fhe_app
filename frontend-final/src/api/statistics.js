// Central place for statistics API calls.
// Override the base URL via the REACT_APP_API_BASE_URL environment variable.
const API_BASE = process.env.REACT_APP_API_BASE_URL || '/api';

// Per-metric endpoints. Each metric generates from a different endpoint.
export const STATISTICS_ENDPOINTS = {
  averageLengthOfStay: '/statistics/average-length-of-stay',
  costsPerPatient: '/statistics/costs-per-patient',
  hospitalExpenses: '/statistics/hospital-expenses',
  mortalityRate: '/statistics/mortality-rate',
};

// Trigger generation of statistics for a given metric endpoint.
export async function generateStatistics(endpoint) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Request to ${endpoint} failed with status ${response.status}`);
  }

  // Some endpoints may return no body; tolerate that.
  return response.json().catch(() => ({}));
}

