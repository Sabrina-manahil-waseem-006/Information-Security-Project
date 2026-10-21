export const numeric = (value, max = Infinity) => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= max ? value : null;
export const pretty = (value, digits = 1) => value == null ? '—' : new Intl.NumberFormat('en-US', { maximumFractionDigits: digits }).format(value);
export const title = (value) => value ? value[0].toUpperCase() + value.slice(1) : 'Unknown';
export const enumValue = (value, allowed) => typeof value === 'string' && allowed.includes(value.toLowerCase()) ? value.toLowerCase() : null;
export const reasonText = (value) => typeof value === 'string' && value.trim() ? value : 'No reason supplied by backend.';
export function normalizeMetrics(raw) {
  return {
    timestamp: typeof raw.timestamp === 'string' ? raw.timestamp : null,
    rps: numeric(raw.rps), cpu_percent: numeric(raw.cpu_percent, 100), ram_percent: numeric(raw.ram_percent, 100),
    response_time_ms: numeric(raw.response_time_ms), error_rate: numeric(raw.error_rate, 1), network_bytes: numeric(raw.network_bytes),
  };
}
// Public repo has no status route to verify. Only explicit fields from the local API
// are read. Missing/unknown values remain null; detection never determines enabled.
export function normalizeMitigation(raw) {
  return { enabled: typeof raw.enabled === 'boolean' ? raw.enabled : null,
    level: enumValue(raw.level, ['none', 'light', 'moderate', 'aggressive']), reason: reasonText(raw.reason) };
}
export const metricDefinitions = [
  { key: 'rps', label: 'Requests per second', unit: 'req/s' },
  { key: 'cpu_percent', label: 'CPU utilization', unit: '%' },
  { key: 'ram_percent', label: 'RAM utilization', unit: '%' },
  { key: 'response_time_ms', label: 'Avg. response time', unit: 'ms' },
  { key: 'error_rate', label: 'Error rate', unit: '%' },
];
export const displayValue = (key, value) => value == null ? null : key === 'error_rate' ? value * 100 : value;
