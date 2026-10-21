import { Activity, Cpu, MemoryStick, Timer, CircleHelp, Radio } from 'lucide-react';
import { pretty, normalizeMetrics, enumValue, normalizeMitigation, title, reasonText } from '../utils/data';
import { useMonitoring } from '../hooks/useMonitoring';
export function Badge({ children, tone = 'neutral' }) { return <span className={`badge ${tone}`}><i/>{children}</span>; }
export function PageHeading({ eyebrow, title: heading, description, children }) { return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{heading}</h1><p>{description}</p></div>{children}</div>; }
export function Panel({ title: heading, subtitle, children, extra, className = '' }) { return <section className={`panel ${className}`}><div className="panel-heading"><div><h2>{heading}</h2>{subtitle && <p>{subtitle}</p>}</div>{extra}</div>{children}</section>; }
export function Empty({ title: heading, children, icon: Icon = Radio }) { return <div className="empty"><div className="empty-icon"><Icon size={25}/></div><h3>{heading}</h3><p>{children}</p></div>; }
export function MetricCards() {
  const { endpoints } = useMonitoring(); const resource = endpoints.metrics;
  const metrics = resource.data ? normalizeMetrics(resource.data) : {};
  return <div className="kpi-grid">{[
    ['rps', 'Requests per second', 'req/s', Activity], ['cpu_percent', 'CPU utilization', '%', Cpu],
    ['ram_percent', 'RAM utilization', '%', MemoryStick], ['response_time_ms', 'Avg. response time', 'ms', Timer],
  ].map(([key, label, unit, Icon]) => <section className="kpi" key={key}><div className="kpi-top"><span>{label}</span><Icon size={17}/></div><div className="metric">{pretty(metrics[key])}<small>{unit}</small></div><div className="metric-caption">{resource.loading ? 'Waiting for first sample' : resource.error ? 'Telemetry unavailable' : metrics[key] == null ? 'Field not supplied' : 'Latest backend sample'}</div></section>)}</div>;
}
export function DetectionCard({ detailed = false }) {
  const { endpoints: { detection } } = useMonitoring(); const raw = detection.data;
  const status = enumValue(raw?.status, ['normal', 'attack']); const severity = enumValue(raw?.severity, ['low', 'medium', 'high']);
  return <Panel title="Attack detection" subtitle="Classification from the detection engine" extra={<Activity size={19} className="muted"/>}><div className="status-line"><Badge tone={status === 'attack' ? 'danger' : status === 'normal' ? 'success' : 'neutral'}>{detection.loading ? 'Loading' : title(status)}</Badge><span className="small">Severity <b className={severity === 'high' ? 'danger-text' : ''}>{title(severity)}</b></span></div><p className="reason">{detection.error || (raw ? reasonText(raw.reason) : 'Waiting for detection data.')}</p>{detailed && <div className="panel-note"><CircleHelp size={15}/>Detection is a classification, not confirmation of active mitigation.</div>}</Panel>;
}
export function MitigationCard({ detailed = false }) {
  const { endpoints: { mitigation } } = useMonitoring(); const data = normalizeMitigation(mitigation.data || {});
  return <Panel title="Adaptive mitigation" subtitle="Enforcement reported independently" extra={<Radio size={19} className="muted"/>}><div className="status-line"><Badge tone={data.level && data.level !== 'none' ? 'warning' : 'neutral'}>{mitigation.loading ? 'Loading' : title(data.level)}</Badge><span className="small">Enabled <b>{data.enabled === null ? 'Unknown' : data.enabled ? 'Yes' : 'No'}</b></span></div><p className="reason">{mitigation.error || (mitigation.data ? data.reason : 'Waiting for mitigation data.')}</p>{detailed && <><div className="button-row"><button disabled>Enable mitigation</button><button disabled>Disable mitigation</button></div><div className="panel-note">Backend control API not connected.</div>{mitigation.data && (data.enabled === null || data.level === null) && <details><summary>Inspect response · fields unavailable</summary><pre>{JSON.stringify(mitigation.data, null, 2)}</pre></details>}</>}</Panel>;
}
