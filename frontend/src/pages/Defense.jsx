
import { useEffect, useState } from 'react';
import { Play, Square, ArrowRight, Waves, Zap } from 'lucide-react';
import {
  PageHeading, Panel, Badge, MetricCards,
  DetectionCard, MitigationCard
} from '../components/UI';

export default function Defense() {
  const [mode, setMode] = useState('normal');
  const [simulation, setSimulation] = useState({
    running: false,
    mode: null
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  async function fetchStatus() {
    try {
      const response = await fetch('/api/simulation/status');
      if (!response.ok) throw new Error('Status unavailable');
      setSimulation(await response.json());
    } catch {
      // Keep last known status if polling fails.
    }
  }

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  async function controlSimulation(action) {
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch(`/api/simulation/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        ...(action === 'start'
          ? { body: JSON.stringify({ mode }) }
          : {})
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Request failed');
      }

      setSimulation(data);
      setMessage(
        action === 'start'
          ? `${mode.toUpperCase()} simulation started (30 seconds max).`
          : 'Simulation stopped.'
      );

      await fetchStatus();
    } catch (error) {
      setMessage(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function toggleMitigation(enabled) {
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch(
        `/api/mitigation/${enabled ? 'enable' : 'disable'}`,
        { method: 'POST' }
      );

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      setMessage(data.message);
      window.dispatchEvent(new Event('mitigation-updated'));
    } catch (error) {
      setMessage(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="RESPOND / 02"
        title="Attack & defense"
        description="Observe detection and adaptive mitigation as separate decisions."
      />

      <div className="workflow">
        <span>01 <b>Observe traffic</b></span>
        <ArrowRight size={16}/>
        <span>02 <b>Detect anomalies</b></span>
        <ArrowRight size={16}/>
        <span>03 <b>Apply mitigation</b></span>
      </div>

      <Panel
        title="Traffic simulation"
        subtitle="Run controlled traffic against your local backend."
        extra={
          <Badge tone={simulation.running ? 'warning' : 'neutral'}>
            {simulation.running
              ? `${simulation.mode?.toUpperCase()} running`
              : 'Stopped'}
          </Badge>
        }
      >
        <div className="simulation-layout">
          <div className="traffic-options">
            {[
              ['normal', 'Normal traffic', 'Baseline service workload', Waves],
              ['ddos', 'DDoS traffic', 'Controlled load experiment', Zap]
            ].map(([value, label, desc, Icon]) => (
              <button
                key={value}
                className={`traffic-option ${mode === value ? 'selected' : ''}`}
                onClick={() => setMode(value)}
                disabled={simulation.running || loading}
                aria-pressed={mode === value}
              >
                <Icon size={22}/>
                <span>
                  <strong>{label}</strong>
                  <small>{desc}</small>
                </span>
                <span className="radio-mark"/>
              </button>
            ))}
          </div>

          <div className="simulation-actions">
            <div className="button-row">
              <button
                className="primary"
                disabled={simulation.running || loading}
                onClick={() => controlSimulation('start')}
              >
                <Play size={15}/>Start simulation
              </button>

              <button
                disabled={!simulation.running || loading}
                onClick={() => controlSimulation('stop')}
              >
                <Square size={14}/>Stop
              </button>
            </div>

            <small>
              One simulated user · Maximum 30 seconds · Local testing only
            </small>
          </div>
        </div>
      </Panel>

      <div className="section-label">CURRENT OBSERVATIONS</div>
      <MetricCards/>

      <div className="two-columns">
        <DetectionCard detailed/>
        <MitigationCard detailed/>
      </div>

      <Panel
        title="Mitigation controls"
        subtitle="Manually enable or disable adaptive protection."
      >
        <div className="button-row">
          <button
            className="primary"
            disabled={loading}
            onClick={() => toggleMitigation(true)}
          >
            Enable Mitigation
          </button>

          <button
            disabled={loading}
            onClick={() => toggleMitigation(false)}
          >
            Disable Mitigation
          </button>
        </div>

        {message && <p role="status">{message}</p>}
      </Panel>
    </>
  );
}
