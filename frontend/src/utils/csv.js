import Papa from 'papaparse';
import { metricDefinitions } from './data.js';
const keys = metricDefinitions.map(m => m.key);
export function parseExperiment(text, phase) {
  const parsed = Papa.parse(text.replace(/^\uFEFF/, ''), { header: true, skipEmptyLines: 'greedy', transformHeader: h => h.trim() });
  if (parsed.errors.length) throw new Error(`Invalid CSV: ${parsed.errors[0].message}`);
  const headers = parsed.meta.fields || [];
  if (new Set(headers).size !== headers.length || parsed.meta.renamedHeaders && Object.keys(parsed.meta.renamedHeaders).length) throw new Error('Duplicate column names are not allowed.');
  const missing = keys.filter(key => !headers.includes(key));
  if (missing.length) throw new Error(`Missing columns: ${missing.join(', ')}. Import metrics CSV, not Locust statistics.`);
  if (!parsed.data.length) throw new Error('CSV contains no data rows.');
  if (parsed.data.length > 100000) throw new Error('Maximum 100,000 rows per import.');
  return parsed.data.map((row, i) => {
    const assigned = phase === 'combined' ? row.phase?.trim().toLowerCase() : phase;
    if (!['before', 'after'].includes(assigned)) throw new Error(`Row ${i + 2}: phase must be before or after.`);
    const result = { phase: assigned, timestamp: row.timestamp || '' };
    for (const key of keys) {
      const raw = row[key]?.trim();
      const n = raw && /^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(raw) ? Number(raw) : NaN;
      const max = key === 'error_rate' ? 1 : key.endsWith('_percent') ? 100 : Infinity;
      if (!Number.isFinite(n) || n < 0 || n > max) throw new Error(`Row ${i + 2}: invalid ${key}${key === 'error_rate' ? ' (use a fraction from 0 to 1)' : ''}.`);
      result[key] = n;
    }
    return result;
  });
}
export function summarize(rows) {
  return Object.fromEntries(['before', 'after'].map(phase => {
    const subset = rows.filter(row => row.phase === phase);
    return [phase, { count: subset.length, ...Object.fromEntries(keys.map(key => [key, subset.length ? subset.reduce((sum, row) => sum + row[key], 0) / subset.length : null])) }];
  }));
}
export function exportExperiment(rows) {
  return Papa.unparse(rows, { columns: ['phase', 'timestamp', ...keys], escapeFormulae: true });
}
export function downloadCSV(text, filename) {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8;' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
