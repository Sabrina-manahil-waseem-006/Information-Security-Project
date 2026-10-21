import { useState } from 'react';
import { NavLink, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Shield, LayoutDashboard, ShieldAlert, ChartNoAxesCombined, ArrowUpRight, CircleAlert } from 'lucide-react';
import { MonitoringContext, useMonitoringState } from './hooks/useMonitoring';
import { Badge } from './components/UI';
import Overview from './pages/Overview';
import Defense from './pages/Defense';
import Results from './pages/Results';
const links = [['/', 'Overview', LayoutDashboard], ['/defense', 'Attack & Defense', ShieldAlert], ['/results', 'Results & Analysis', ChartNoAxesCombined]];
export default function App() {
  const monitor = useMonitoringState(); const { endpoints } = monitor; const location = useLocation();
  const [experiment, setExperiment] = useState({ rows: [], files: {} });
  const loading = Object.values(endpoints).every(e => e.loading);
  const count = Object.values(endpoints).filter(e => e.data).length;
  const status = loading ? 'Connecting' : count === 4 ? 'Connected' : count ? 'Partial connection' : 'Disconnected';
  const issues = Object.entries(endpoints).filter(([, e]) => e.error);
  return <MonitoringContext.Provider value={monitor}><div className="app-shell"><aside className="sidebar"><a className="brand" href="#/"><div className="brand-mark"><Shield size={24} strokeWidth={1.6}/></div><div>SENTINEL<small>DDoS Defense Console</small></div></a><div className="nav-label">WORKSPACE</div><nav aria-label="Main navigation">{links.map(([path, label, Icon], index) => <NavLink key={path} to={path} end={path === '/'}><Icon size={18}/><span>{label}</span><small>0{index + 1}</small></NavLink>)}</nav><div className="sidebar-bottom"><div className="project-label"><Shield size={16}/> RESOURCE-AWARE</div><p>DDoS mitigation for<br/>containerized services</p><span className="small">Information Security Project</span></div></aside><div className="main-shell"><header className="topbar"><div className="breadcrumb">Defense console <span>/</span><b>{links.find(([p]) => p === location.pathname)?.[1] || 'Overview'}</b></div><Badge tone={count === 4 ? 'success' : count ? 'warning' : 'neutral'}>{status}</Badge></header><main id="main"><a className="skip-link" href="#content">Skip to content</a><div id="content">{issues.length > 0 && <div className="connection-banner" role="status"><CircleAlert size={17}/><div><strong>{count ? 'Some monitoring endpoints are unavailable.' : 'Backend disconnected or unavailable.'}</strong><p>{issues.map(([key, e]) => `${key}: ${e.error}`).join(' · ')}</p><small>Retrying automatically. Current values are hidden when a request fails.</small></div></div>}<Routes><Route path="/" element={<Overview/>}/><Route path="/defense" element={<Defense/>}/><Route path="/results" element={<Results experiment={experiment} setExperiment={setExperiment}/>}/><Route path="*" element={<Navigate to="/" replace/>}/></Routes></div><footer><span>SENTINEL <span className="footer-separator">/</span> Resource-aware defense</span><span>Observe. Detect. Adapt.<ArrowUpRight size={12}/></span></footer></main></div></div></MonitoringContext.Provider>;
}
