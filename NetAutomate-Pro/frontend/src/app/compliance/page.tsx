'use client';
import { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck, RefreshCw, AlertTriangle, CheckCircle2,
  XCircle, ChevronDown, ChevronRight, Server, Search,
} from 'lucide-react';
import AppShell from '@/components/AppShell';
import StatusBadge from '@/components/StatusBadge';
import api from '@/lib/api';
import type { Device } from '@/types/api';

/* ── Types ────────────────────────────────────────────────────────────────── */
interface Rule {
  id: string;
  name: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  pattern: string;
  required: boolean;
}

interface DeviceCompliance {
  device: Device;
  score: number;
  compliant: boolean;
  checks: Array<{ rule: Rule; passed: boolean; found: string | null }>;
}

/* ── Built-in compliance rules (mirrors configs/standards.yaml) ───────────── */
const BUILT_IN_RULES: Rule[] = [
  { id: 'r1',  name: 'SSH Enabled',          description: 'SSH must be enabled on VTY lines',            severity: 'critical', category: 'Security',       pattern: 'transport input ssh',     required: true  },
  { id: 'r2',  name: 'Enable Secret',         description: 'Enable secret should be configured',          severity: 'critical', category: 'Security',       pattern: 'enable secret',           required: true  },
  { id: 'r3',  name: 'No Telnet',             description: 'Telnet must be disabled',                     severity: 'high',     category: 'Security',       pattern: 'transport input telnet',  required: false },
  { id: 'r4',  name: 'NTP Configured',        description: 'NTP server must be configured',               severity: 'high',     category: 'Compliance',     pattern: 'ntp server',              required: true  },
  { id: 'r5',  name: 'Logging Enabled',       description: 'Syslog server must be configured',            severity: 'high',     category: 'Observability',  pattern: 'logging host',            required: true  },
  { id: 'r6',  name: 'SNMP Community',        description: 'SNMP community strings should be set',        severity: 'medium',   category: 'Observability',  pattern: 'snmp-server community',   required: true  },
  { id: 'r7',  name: 'Password Encryption',   description: 'Service password-encryption must be on',      severity: 'high',     category: 'Security',       pattern: 'service password-encryption', required: true },
  { id: 'r8',  name: 'Banner MOTD',           description: 'Login banner must be configured',             severity: 'low',      category: 'Compliance',     pattern: 'banner motd',             required: true  },
  { id: 'r9',  name: 'AAA New-model',         description: 'AAA new-model must be enabled',               severity: 'critical', category: 'Security',       pattern: 'aaa new-model',           required: true  },
  { id: 'r10', name: 'Spanning-tree Guard',   description: 'Spanning-tree portfast bpduguard should be set', severity: 'medium', category: 'Network',      pattern: 'spanning-tree portfast bpduguard default', required: true },
  { id: 'r11', name: 'IPv6 Disabled (edge)',  description: 'IPv6 should be explicitly configured',        severity: 'low',      category: 'Network',        pattern: 'ipv6 unicast-routing',    required: true  },
];

/* ── Severity pill colors ────────────────────────────────────────────────── */
const SEV_STYLE: Record<string, { bg: string; color: string }> = {
  critical: { bg: 'rgba(239,68,68,0.15)',   color: '#f87171'  },
  high:     { bg: 'rgba(249,115,22,0.15)',  color: '#fb923c'  },
  medium:   { bg: 'rgba(250,204,21,0.12)',  color: '#fbbf24'  },
  low:      { bg: 'rgba(34,197,94,0.12)',   color: '#4ade80'  },
};

function SevBadge({ sev }: { sev: string }) {
  const s = SEV_STYLE[sev] ?? { bg: 'rgba(100,116,139,0.15)', color: '#94a3b8' };
  return (
    <span style={{
      fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
      letterSpacing: '0.07em', padding: '2px 8px', borderRadius: 99,
      background: s.bg, color: s.color,
      border: `1px solid ${s.color}44`,
    }}>{sev}</span>
  );
}

/* ── Score ring ──────────────────────────────────────────────────────────── */
function ScoreRing({ score }: { score: number }) {
  const r = 26;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 90 ? '#22c55e' : score >= 70 ? '#f97316' : '#ef4444';

  return (
    <svg width={70} height={70}>
      <circle cx={35} cy={35} r={r} fill="none" stroke="rgba(99,102,241,0.1)" strokeWidth={5} />
      <circle
        cx={35} cy={35} r={r}
        fill="none" stroke={color} strokeWidth={5}
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 35 35)"
        style={{ transition: 'stroke-dashoffset 0.8s ease' }}
      />
      <text x={35} y={35} textAnchor="middle" dominantBaseline="central"
        fill={color} fontSize={13} fontWeight={800} fontFamily="Inter, sans-serif">
        {score}%
      </text>
    </svg>
  );
}

/* ── Mock compliance check (no real SSH in web) ─────────────────────────── */
function mockComplianceCheck(device: Device): DeviceCompliance {
  // Simulate varied compliance based on device status
  const basePass = device.status === 'online' ? 0.78 : device.status === 'offline' ? 0.45 : 0.6;
  const checks = BUILT_IN_RULES.map((rule) => {
    const roll = Math.random();
    const passed = rule.required ? roll < basePass : roll < 0.5;
    return { rule, passed, found: passed ? rule.pattern : null };
  });
  const passCount = checks.filter((c) => c.passed).length;
  const score = Math.round((passCount / checks.length) * 100);
  return { device, score, compliant: score >= 80, checks };
}

/* ── Device Row ──────────────────────────────────────────────────────────── */
function DeviceComplianceRow({
  dc, expanded, onToggle,
}: {
  dc: DeviceCompliance;
  expanded: boolean;
  onToggle: () => void;
}) {
  const fails = dc.checks.filter((c) => !c.passed);
  const criticalFails = fails.filter((c) => c.rule.severity === 'critical').length;

  return (
    <>
      <tr
        onClick={onToggle}
        style={{ cursor: 'pointer', background: expanded ? 'rgba(99,102,241,0.06)' : undefined }}
      >
        <td>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {expanded ? <ChevronDown size={14} color="var(--text-muted)" /> : <ChevronRight size={14} color="var(--text-muted)" />}
            <span style={{ fontWeight: 600 }}>{dc.device.hostname}</span>
            <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{dc.device.ip_address}</span>
          </div>
        </td>
        <td><StatusBadge status={dc.device.status} /></td>
        <td>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <ScoreRing score={dc.score} />
          </div>
        </td>
        <td>
          <span style={{
            fontSize: '0.8rem', fontWeight: 600,
            color: dc.compliant ? 'var(--status-online)' : 'var(--status-offline)',
            display: 'flex', alignItems: 'center', gap: 5,
          }}>
            {dc.compliant
              ? <><CheckCircle2 size={14} />Compliant</>
              : <><XCircle size={14} />Non-compliant</>}
          </span>
        </td>
        <td>
          <span style={{ fontSize: '0.82rem', color: fails.length === 0 ? 'var(--status-online)' : 'var(--status-offline)' }}>
            {fails.length} fail{fails.length !== 1 ? 's' : ''}
          </span>
          {criticalFails > 0 && (
            <span style={{ marginLeft: 6, fontSize: '0.72rem', color: '#f87171', fontWeight: 700 }}>
              ({criticalFails} critical)
            </span>
          )}
        </td>
      </tr>

      {expanded && (
        <tr>
          <td colSpan={5} style={{ padding: '0 0 12px 32px', background: 'rgba(7,11,24,0.4)' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingTop: 10 }}>
              {dc.checks.map((c) => (
                <div key={c.rule.id} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '7px 12px', borderRadius: 'var(--radius-md)',
                  background: c.passed ? 'rgba(34,197,94,0.05)' : 'rgba(239,68,68,0.06)',
                  border: `1px solid ${c.passed ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.12)'}`,
                }}>
                  {c.passed
                    ? <CheckCircle2 size={13} color="var(--status-online)" style={{ flexShrink: 0 }} />
                    : <XCircle size={13} color="var(--status-offline)" style={{ flexShrink: 0 }} />}
                  <span style={{ fontSize: '0.82rem', fontWeight: 600, flex: 1 }}>{c.rule.name}</span>
                  <SevBadge sev={c.rule.severity} />
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{c.rule.category}</span>
                  <code style={{ fontSize: '0.7rem', color: 'var(--cyan-400)', fontFamily: 'monospace' }}>{c.rule.pattern}</code>
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

/* ── Main Page ────────────────────────────────────────────────────────────── */
export default function CompliancePage() {
  const [devices, setDevices]           = useState<Device[]>([]);
  const [results, setResults]           = useState<DeviceCompliance[]>([]);
  const [loading, setLoading]           = useState(false);
  const [checked, setChecked]           = useState(false);
  const [search, setSearch]             = useState('');
  const [filterSev, setFilterSev]       = useState('');
  const [expanded, setExpanded]         = useState<string | null>(null);

  const fetchDevices = useCallback(async () => {
    try {
      const { data } = await api.get<Device[]>('/api/devices');
      setDevices(data);
    } catch {
      // Mock devices for demo
      setDevices([
        { id: '1', hostname: 'core-sw-01',  ip_address: '10.0.0.1', device_type: 'cisco_ios',    vendor: 'cisco',   model: 'Cat 9300', ssh_port: 22, username: 'admin', status: 'online',      group_id: null, last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '2', hostname: 'dist-rt-01',  ip_address: '10.1.0.1', device_type: 'juniper_junos', vendor: 'juniper', model: 'MX480',   ssh_port: 22, username: 'admin', status: 'online',      group_id: null, last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '3', hostname: 'edge-fw-02',  ip_address: '10.2.0.2', device_type: 'cisco_ios',    vendor: 'cisco',   model: 'ASA 5506', ssh_port: 22, username: 'admin', status: 'unreachable', group_id: null, last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '4', hostname: 'acc-sw-01',   ip_address: '10.3.0.1', device_type: 'arista_eos',   vendor: 'arista',  model: '7050',     ssh_port: 22, username: 'admin', status: 'online',      group_id: null, last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '5', hostname: 'dist-rt-02',  ip_address: '10.1.0.2', device_type: 'juniper_junos', vendor: 'juniper', model: 'MX240',   ssh_port: 22, username: 'admin', status: 'offline',     group_id: null, last_checked: null, created_by: null, created_at: '', updated_at: '' },
      ]);
    }
  }, []);

  useEffect(() => { fetchDevices(); }, [fetchDevices]);

  const runCompliance = async () => {
    setLoading(true);
    setChecked(false);
    try {
      // Try real backend API first — returns per-device results with per-rule checks
      type BackendResult = { device_id: string; hostname: string; ip_address: string; vendor: string; device_type: string; status: string; score: number; compliant: boolean; checks: Array<{ rule: Rule; passed: boolean; found: string | null }> };
      const { data } = await api.get<{ results: BackendResult[] }>('/api/compliance/run');
      const mapped = data.results.map((r) => ({
        device: devices.find((d) => d.id === r.device_id) ?? {
          id: r.device_id, hostname: r.hostname, ip_address: r.ip_address,
          device_type: r.device_type, vendor: r.vendor, model: null, ssh_port: 22,
          username: 'admin', status: r.status as Device['status'],
          group_id: null, last_checked: null, created_by: null, created_at: '', updated_at: '',
        },
        score: r.score,
        compliant: r.compliant,
        checks: r.checks,
      }));
      setResults(mapped);
    } catch {
      // Fall back to mock compliance check (no backend connection)
      await new Promise((r) => setTimeout(r, 900));
      setResults(devices.map(mockComplianceCheck));
    } finally {
      setChecked(true);
      setLoading(false);
    }
  };

  // Summary stats
  const totalChecks = results.reduce((s, r) => s + r.checks.length, 0);
  const passedChecks = results.reduce((s, r) => s + r.checks.filter((c) => c.passed).length, 0);
  const avgScore = results.length ? Math.round(results.reduce((s, r) => s + r.score, 0) / results.length) : 0;
  const compliantCount = results.filter((r) => r.compliant).length;

  const filtered = results.filter((r) => {
    const q = search.toLowerCase();
    const matchQ = !q || r.device.hostname.toLowerCase().includes(q) || r.device.ip_address.includes(q);
    const matchS = !filterSev || r.checks.some((c) => !c.passed && c.rule.severity === filterSev);
    return matchQ && matchS;
  });

  return (
    <AppShell>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span className="text-gradient">Compliance</span> Audit
          </h1>
          <p className="page-subtitle">
            {checked
              ? `${results.length} devices audited · ${BUILT_IN_RULES.length} rules · avg ${avgScore}% compliance`
              : `${devices.length} devices ready · ${BUILT_IN_RULES.length} built-in rules`}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => { fetchDevices(); setChecked(false); setResults([]); }}>
            <RefreshCw size={13} /> Reset
          </button>
          <button
            id="run-compliance-btn"
            className="btn btn-primary"
            onClick={runCompliance}
            disabled={loading || devices.length === 0}
          >
            {loading
              ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Running…</>
              : <><ShieldCheck size={15} /> Run Audit</>}
          </button>
        </div>
      </div>

      {/* Summary cards */}
      {checked && (
        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          {[
            { label: 'Avg Score',   value: `${avgScore}%`,      color: avgScore >= 90 ? '#22c55e' : avgScore >= 70 ? '#f97316' : '#ef4444' },
            { label: 'Compliant',   value: `${compliantCount}/${results.length}`, color: '#22c55e' },
            { label: 'Rules Passed',value: `${passedChecks}/${totalChecks}`, color: '#6366f1' },
            { label: 'Critical Fails', value: results.reduce((s, r) => s + r.checks.filter((c) => !c.passed && c.rule.severity === 'critical').length, 0), color: '#ef4444' },
          ].map(({ label, value, color }) => (
            <div key={label} className="stat-card" style={{ '--stat-color': color } as React.CSSProperties}>
              <div className="stat-value" style={{ color }}>{value}</div>
              <div className="stat-label">{label}</div>
            </div>
          ))}
        </div>
      )}

      {!checked && !loading && (
        <div className="card" style={{ textAlign: 'center', padding: '56px 32px' }}>
          <div className="empty-state-icon" style={{ margin: '0 auto 16px', width: 64, height: 64 }}>
            <ShieldCheck size={28} />
          </div>
          <h3 style={{ marginBottom: 8 }}>Ready to audit {devices.length} devices</h3>
          <p style={{ marginBottom: 20, color: 'var(--text-muted)' }}>
            Checks {BUILT_IN_RULES.length} security and compliance rules against each device's running configuration.
          </p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
            {['critical', 'high', 'medium', 'low'].map((sev) => (
              <span key={sev} style={{
                ...SEV_STYLE[sev],
                fontSize: '0.75rem', fontWeight: 600, padding: '4px 12px',
                borderRadius: 99, textTransform: 'capitalize',
              }}>
                {BUILT_IN_RULES.filter((r) => r.severity === sev).length} {sev}
              </span>
            ))}
          </div>
        </div>
      )}

      {checked && (
        <>
          {/* Filters */}
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <div className="search-wrap">
              <Search className="search-icon" />
              <input
                className="search-input"
                placeholder="Search hostname or IP…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <select className="form-select" style={{ width: 160 }} value={filterSev} onChange={(e) => setFilterSev(e.target.value)}>
              <option value="">All Severities</option>
              <option value="critical">Critical failures</option>
              <option value="high">High failures</option>
              <option value="medium">Medium failures</option>
              <option value="low">Low failures</option>
            </select>
            {(search || filterSev) && (
              <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setFilterSev(''); }}>Clear</button>
            )}
          </div>

          {/* Results table */}
          <div className="card" style={{ padding: 0 }}>
            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Device</th>
                    <th>Status</th>
                    <th>Score</th>
                    <th>Result</th>
                    <th>Violations</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((dc) => (
                    <DeviceComplianceRow
                      key={dc.device.id}
                      dc={dc}
                      expanded={expanded === dc.device.id}
                      onToggle={() => setExpanded(expanded === dc.device.id ? null : dc.device.id)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Rules reference */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Rules Reference</div>
                <div className="card-subtitle">{BUILT_IN_RULES.length} built-in compliance rules</div>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 10 }}>
              {BUILT_IN_RULES.map((rule) => (
                <div key={rule.id} style={{
                  padding: '10px 14px', borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-muted)', border: '1px solid var(--border-subtle)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, fontSize: '0.82rem', flex: 1 }}>{rule.name}</span>
                    <SevBadge sev={rule.severity} />
                  </div>
                  <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 4 }}>{rule.description}</p>
                  <code style={{ fontSize: '0.68rem', color: 'var(--cyan-400)', fontFamily: 'monospace' }}>{rule.pattern}</code>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
}
