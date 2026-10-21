import { PageHeading, MetricCards, DetectionCard, MitigationCard } from '../components/UI';
import TelemetryChart from '../components/TelemetryChart';
import { useMonitoring } from '../hooks/useMonitoring';
import { normalizeMetrics, pretty } from '../utils/data';
export default function Overview() {
  const { endpoints } = useMonitoring(); const m = normalizeMetrics(endpoints.metrics.data || {});
  return <><PageHeading eyebrow="MONITOR / 01" title="System overview" description="A clear view of traffic, resources and your defense posture."><div className="sampling"><span className="dot"/> Polling every ~2 seconds</div></PageHeading><MetricCards/><div className="two-columns charts-grid"><TelemetryChart/><TelemetryChart resources/></div><div className="two-columns"><DetectionCard/><MitigationCard/></div><div className="telemetry-footer"><span>Error rate <b>{pretty(m.error_rate == null ? null : m.error_rate * 100, 2)}%</b></span><span>Network total <b>{pretty(m.network_bytes, 0)} bytes</b><small>Cumulative counter</small></span><span>Sample timestamp <b>{m.timestamp || '—'}{m.timestamp && !/Z|[+-]\d\d:\d\d$/.test(m.timestamp) ? ' UTC' : ''}</b></span></div></>;
}
