// All HTTP traffic stays behind Vite's /api proxy. No control endpoints are called.
export async function getJSON(path, signal) {
  const response = await fetch(`/api${path}`, { signal, headers: { Accept: 'application/json' }, cache: 'no-store' });
  if (!response.ok) throw new Error(response.status === 404 ? 'Endpoint unavailable (404)' : `API error (${response.status})`);
  const data = await response.json();
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('Expected a JSON object');
  return data;
}
export const api = {
  metrics: (signal) => getJSON('/metrics', signal),
  detection: (signal) => getJSON('/detection', signal),
  mitigation: (signal) => getJSON('/mitigation/status', signal),
  health: (signal) => getJSON('/health', signal),
};
