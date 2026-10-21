import { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../services/api';
import { normalizeMetrics } from '../utils/data';
export const MonitoringContext = createContext(null);
export const useMonitoring = () => useContext(MonitoringContext);
const initial = Object.fromEntries(Object.keys(api).map(key => [key, { data: null, error: null, loading: true, updatedAt: null }]));
export function useMonitoringState() {
  const [endpoints, setEndpoints] = useState(initial);
  const [history, setHistory] = useState([]);
  useEffect(() => {
    let disposed = false, timer, controller;
    async function poll() {
      controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      await Promise.all(Object.entries(api).map(async ([key, request]) => {
        try {
          const data = await request(controller.signal);
          if (disposed) return;
          const now = Date.now();
          setEndpoints(prev => ({ ...prev, [key]: { data, error: null, loading: false, updatedAt: now } }));
          if (key === 'metrics') setHistory(prev => [...prev, { ...normalizeMetrics(data), receivedAt: now }].slice(-90));
        } catch (error) {
          if (disposed) return;
          setEndpoints(prev => ({ ...prev, [key]: { ...prev[key], data: null, loading: false, error: error.name === 'AbortError' ? 'Request timed out' : error.message } }));
          if (key === 'metrics') setHistory(prev => [...prev, { receivedAt: Date.now(), rps: null, cpu_percent: null, ram_percent: null }].slice(-90));
        }
      }));
      clearTimeout(timeout);
      if (!disposed) timer = setTimeout(poll, 2000); // No overlapping polling cycles.
    }
    poll();
    return () => { disposed = true; clearTimeout(timer); controller?.abort(); };
  }, []);
  return { endpoints, history };
}
