'use client';
import { useState, useEffect, useCallback, useRef } from 'react';
import { RefreshCw, Network, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import AppShell from '@/components/AppShell';
import StatusBadge from '@/components/StatusBadge';
import api from '@/lib/api';
import type { Device, DeviceGroup } from '@/types/api';

/* ── Types ────────────────────────────────────────────────────────────────── */
interface NodePos { x: number; y: number; }
interface NodeData extends Device { pos: NodePos; }

/* ── Constants ────────────────────────────────────────────────────────────── */
const STATUS_COLOR: Record<string, string> = {
  online:      '#22c55e',
  offline:     '#ef4444',
  unreachable: '#f97316',
  maintenance: '#a855f7',
  unknown:     '#64748b',
};

const VENDOR_ICON: Record<string, string> = {
  cisco:   'C',
  juniper: 'J',
  arista:  'A',
};

/* ── Layout: arrange nodes in concentric rings by group ─────────────────── */
function layoutNodes(devices: Device[], groups: DeviceGroup[]): NodeData[] {
  const W = 880, H = 560, cx = W / 2, cy = H / 2;
  const byGroup: Record<string, Device[]> = { '__none': [] };
  groups.forEach((g) => { byGroup[g.id] = []; });
  devices.forEach((d) => {
    const key = d.group_id && byGroup[d.group_id] ? d.group_id : '__none';
    byGroup[key].push(d);
  });

  const groupKeys = Object.keys(byGroup).filter((k) => byGroup[k].length > 0);
  const result: NodeData[] = [];

  groupKeys.forEach((gk, gi) => {
    const devs = byGroup[gk];
    const radius = gi === 0 ? 0 : 80 + gi * 110;
    devs.forEach((d, di) => {
      const angle = (2 * Math.PI * di) / devs.length - Math.PI / 2;
      result.push({
        ...d,
        pos: {
          x: devs.length === 1 ? cx : cx + radius * Math.cos(angle),
          y: devs.length === 1 ? cy : cy + radius * Math.sin(angle),
        },
      });
    });
  });

  // If no groups, arrange all in a circle
  if (groupKeys.length === 1) {
    const devs = devices;
    return devs.map((d, di) => {
      const angle = (2 * Math.PI * di) / devs.length - Math.PI / 2;
      const r = Math.min(200, 60 + devs.length * 20);
      return { ...d, pos: { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) } };
    });
  }

  return result;
}

/* ── Animated Link between two nodes ──────────────────────────────────────── */
function AnimatedLink({ x1, y1, x2, y2, active }: { x1: number; y1: number; x2: number; y2: number; active: boolean }) {
  const len = Math.hypot(x2 - x1, y2 - y1);
  return (
    <g>
      <line
        x1={x1} y1={y1} x2={x2} y2={y2}
        stroke={active ? 'rgba(99,102,241,0.25)' : 'rgba(100,116,139,0.12)'}
        strokeWidth={active ? 1.5 : 1}
      />
      {active && (
        <circle r={3} fill="#6366f1" opacity={0.7}>
          <animateMotion dur={`${(len / 120).toFixed(1)}s`} repeatCount="indefinite">
            <mpath href={`#link-${x1.toFixed(0)}-${y1.toFixed(0)}-${x2.toFixed(0)}-${y2.toFixed(0)}`} />
          </animateMotion>
        </circle>
      )}
      <path
        id={`link-${x1.toFixed(0)}-${y1.toFixed(0)}-${x2.toFixed(0)}-${y2.toFixed(0)}`}
        d={`M ${x1} ${y1} L ${x2} ${y2}`}
        fill="none"
        stroke="none"
      />
    </g>
  );
}

/* ── Device Node ─────────────────────────────────────────────────────────── */
function DeviceNode({
  node, selected, onClick,
}: {
  node: NodeData;
  selected: boolean;
  onClick: () => void;
}) {
  const color = STATUS_COLOR[node.status] ?? STATUS_COLOR.unknown;
  const label = VENDOR_ICON[node.vendor] ?? '?';
  const pulse = node.status === 'online';

  return (
    <g
      transform={`translate(${node.pos.x}, ${node.pos.y})`}
      onClick={onClick}
      style={{ cursor: 'pointer' }}
    >
      {/* Pulse ring for online devices */}
      {pulse && (
        <circle r={24} fill="none" stroke={color} strokeWidth={1.5} opacity={0}>
          <animate attributeName="r" from="18" to="30" dur="1.8s" repeatCount="indefinite" />
          <animate attributeName="opacity" from="0.6" to="0" dur="1.8s" repeatCount="indefinite" />
        </circle>
      )}

      {/* Selection ring */}
      {selected && (
        <circle r={22} fill="none" stroke="#6366f1" strokeWidth={2.5} strokeDasharray="4 3">
          <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="4s" repeatCount="indefinite" />
        </circle>
      )}

      {/* Node body */}
      <circle
        r={18}
        fill={selected ? 'rgba(99,102,241,0.25)' : 'rgba(17,24,39,0.9)'}
        stroke={color}
        strokeWidth={2}
        style={{ filter: selected ? `drop-shadow(0 0 8px ${color})` : `drop-shadow(0 0 3px ${color}55)` }}
      />

      {/* Vendor label */}
      <text
        textAnchor="middle"
        dominantBaseline="central"
        fill={color}
        fontSize={10}
        fontWeight={700}
        fontFamily="'JetBrains Mono', monospace"
      >
        {label}
      </text>

      {/* Hostname label below */}
      <text
        textAnchor="middle"
        dominantBaseline="hanging"
        y={22}
        fill="#94a3b8"
        fontSize={9}
        fontFamily="Inter, sans-serif"
      >
        {node.hostname.length > 12 ? node.hostname.slice(0, 12) + '…' : node.hostname}
      </text>
    </g>
  );
}

/* ── Main Page ────────────────────────────────────────────────────────────── */
export default function TopologyPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [groups, setGroups]   = useState<DeviceGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<NodeData | null>(null);
  const [zoom, setZoom] = useState(1);
  const svgRef = useRef<SVGSVGElement>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [dRes, gRes] = await Promise.all([
        api.get<Device[]>('/api/devices'),
        api.get<DeviceGroup[]>('/api/devices/groups'),
      ]);
      setDevices(dRes.data);
      setGroups(gRes.data);
    } catch {
      // Use mock data for demo
      setDevices([
        { id: '1', hostname: 'core-sw-01',  ip_address: '10.0.0.1', device_type: 'cisco_ios',    vendor: 'cisco',   model: 'Catalyst 9300', ssh_port: 22, username: 'admin', status: 'online',      group_id: 'g1', last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '2', hostname: 'core-sw-02',  ip_address: '10.0.0.2', device_type: 'cisco_ios',    vendor: 'cisco',   model: 'Catalyst 9300', ssh_port: 22, username: 'admin', status: 'online',      group_id: 'g1', last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '3', hostname: 'dist-rt-01',  ip_address: '10.1.0.1', device_type: 'juniper_junos', vendor: 'juniper', model: 'MX480',         ssh_port: 22, username: 'admin', status: 'online',      group_id: 'g2', last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '4', hostname: 'dist-rt-02',  ip_address: '10.1.0.2', device_type: 'juniper_junos', vendor: 'juniper', model: 'MX480',         ssh_port: 22, username: 'admin', status: 'online',      group_id: 'g2', last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '5', hostname: 'dist-rt-03',  ip_address: '10.1.0.3', device_type: 'juniper_junos', vendor: 'juniper', model: 'MX240',         ssh_port: 22, username: 'admin', status: 'offline',     group_id: 'g2', last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '6', hostname: 'edge-fw-01',  ip_address: '10.2.0.1', device_type: 'cisco_ios',    vendor: 'cisco',   model: 'ASA 5506',      ssh_port: 22, username: 'admin', status: 'online',      group_id: 'g3', last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '7', hostname: 'edge-fw-02',  ip_address: '10.2.0.2', device_type: 'cisco_ios',    vendor: 'cisco',   model: 'ASA 5506',      ssh_port: 22, username: 'admin', status: 'unreachable', group_id: 'g3', last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '8', hostname: 'acc-sw-01',   ip_address: '10.3.0.1', device_type: 'arista_eos',   vendor: 'arista',  model: '7050',          ssh_port: 22, username: 'admin', status: 'online',      group_id: 'g4', last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '9', hostname: 'acc-sw-02',   ip_address: '10.3.0.2', device_type: 'arista_eos',   vendor: 'arista',  model: '7050',          ssh_port: 22, username: 'admin', status: 'online',      group_id: 'g4', last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '10', hostname: 'acc-sw-03',  ip_address: '10.3.0.3', device_type: 'arista_eos',   vendor: 'arista',  model: '7050',          ssh_port: 22, username: 'admin', status: 'maintenance', group_id: 'g4', last_checked: null, created_by: null, created_at: '', updated_at: '' },
        { id: '11', hostname: 'mgmt-srv-01',ip_address: '10.4.0.1', device_type: 'cisco_ios',    vendor: 'cisco',   model: 'ISR 4451',      ssh_port: 22, username: 'admin', status: 'online',      group_id: null,  last_checked: null, created_by: null, created_at: '', updated_at: '' },
      ]);
      setGroups([
        { id: 'g1', name: 'Core',         description: null, created_at: '' },
        { id: 'g2', name: 'Distribution', description: null, created_at: '' },
        { id: 'g3', name: 'Edge',         description: null, created_at: '' },
        { id: 'g4', name: 'Access',       description: null, created_at: '' },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const nodes = layoutNodes(devices, groups);

  // Build links: connect devices in the same group to each other; connect group "hubs" together
  const links: Array<{ from: NodeData; to: NodeData }> = [];
  const groupHubs: Record<string, NodeData> = {};

  nodes.forEach((n) => {
    if (n.group_id && !groupHubs[n.group_id]) {
      groupHubs[n.group_id] = n;
    }
  });

  nodes.forEach((n) => {
    if (n.group_id) {
      const hub = groupHubs[n.group_id];
      if (hub && hub.id !== n.id) {
        links.push({ from: hub, to: n });
      }
    }
  });

  // Connect group hubs together
  const hubs = Object.values(groupHubs);
  for (let i = 0; i < hubs.length - 1; i++) {
    links.push({ from: hubs[i], to: hubs[i + 1] });
  }
  if (hubs.length > 2) {
    links.push({ from: hubs[hubs.length - 1], to: hubs[0] });
  }

  const online  = devices.filter((d) => d.status === 'online').length;
  const issues  = devices.filter((d) => d.status !== 'online' && d.status !== 'maintenance').length;

  return (
    <AppShell>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            Network <span className="text-gradient">Topology</span>
          </h1>
          <p className="page-subtitle">
            {devices.length} devices · {online} online
            {issues > 0 && <span style={{ color: 'var(--status-offline)', marginLeft: 8 }}>· {issues} issue{issues > 1 ? 's' : ''}</span>}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: 4 }}>
            <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setZoom((z) => Math.min(z + 0.2, 2))} data-tooltip="Zoom in">
              <ZoomIn size={15} />
            </button>
            <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setZoom((z) => Math.max(z - 0.2, 0.4))} data-tooltip="Zoom out">
              <ZoomOut size={15} />
            </button>
            <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setZoom(1)} data-tooltip="Reset zoom">
              <Maximize2 size={15} />
            </button>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={fetchAll} disabled={loading}>
            <RefreshCw size={13} style={{ animation: loading ? 'spin 0.7s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 20, alignItems: 'start' }}>
        {/* SVG Topology Canvas */}
        <div className="card" style={{ padding: 0, overflow: 'hidden', position: 'relative' }}>
          {/* Background grid pattern */}
          <div style={{
            position: 'absolute', inset: 0, pointerEvents: 'none',
            backgroundImage: 'radial-gradient(rgba(99,102,241,0.08) 1px, transparent 1px)',
            backgroundSize: '28px 28px',
          }} />

          {loading ? (
            <div style={{ padding: 80, display: 'flex', justifyContent: 'center' }}>
              <div className="spinner" style={{ width: 32, height: 32 }} />
            </div>
          ) : (
            <svg
              ref={svgRef}
              viewBox="0 0 880 560"
              style={{
                width: '100%',
                height: 'auto',
                minHeight: 420,
                transform: `scale(${zoom})`,
                transformOrigin: 'center center',
                transition: 'transform 0.2s ease',
              }}
            >
              {/* Links */}
              {links.map((l, i) => (
                <AnimatedLink
                  key={i}
                  x1={l.from.pos.x} y1={l.from.pos.y}
                  x2={l.to.pos.x}   y2={l.to.pos.y}
                  active={l.from.status === 'online' && l.to.status === 'online'}
                />
              ))}

              {/* Group labels */}
              {groups.map((g) => {
                const groupNodes = nodes.filter((n) => n.group_id === g.id);
                if (groupNodes.length === 0) return null;
                const avgX = groupNodes.reduce((s, n) => s + n.pos.x, 0) / groupNodes.length;
                const avgY = groupNodes.reduce((s, n) => s + n.pos.y, 0) / groupNodes.length;
                const maxR = Math.max(...groupNodes.map((n) => Math.hypot(n.pos.x - avgX, n.pos.y - avgY))) + 36;
                return (
                  <g key={g.id}>
                    <circle
                      cx={avgX} cy={avgY} r={maxR}
                      fill="rgba(99,102,241,0.04)"
                      stroke="rgba(99,102,241,0.12)"
                      strokeWidth={1}
                      strokeDasharray="6 4"
                    />
                    <text
                      x={avgX} y={avgY - maxR + 14}
                      textAnchor="middle"
                      fill="rgba(99,102,241,0.5)"
                      fontSize={9}
                      fontWeight={700}
                      textDecoration="none"
                      fontFamily="Inter, sans-serif"
                      letterSpacing="0.08em"
                      style={{ textTransform: 'uppercase' }}
                    >
                      {g.name}
                    </text>
                  </g>
                );
              })}

              {/* Nodes */}
              {nodes.map((n) => (
                <DeviceNode
                  key={n.id}
                  node={n}
                  selected={selected?.id === n.id}
                  onClick={() => setSelected(selected?.id === n.id ? null : n)}
                />
              ))}
            </svg>
          )}

          {/* Legend */}
          <div style={{
            position: 'absolute', bottom: 16, left: 16,
            display: 'flex', gap: 14, alignItems: 'center',
            background: 'rgba(7,11,24,0.75)', backdropFilter: 'blur(8px)',
            border: '1px solid rgba(99,102,241,0.12)', borderRadius: 8,
            padding: '7px 14px', fontSize: '0.72rem',
          }}>
            {Object.entries(STATUS_COLOR).filter(([k]) => k !== 'unknown').map(([status, color]) => (
              <span key={status} style={{ display: 'flex', alignItems: 'center', gap: 5, color: '#94a3b8' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block' }} />
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </span>
            ))}
          </div>
        </div>

        {/* Side panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Stats */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">Status Summary</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {Object.entries(STATUS_COLOR).map(([status, color]) => {
                const count = devices.filter((d) => d.status === status).length;
                if (count === 0) return null;
                return (
                  <div key={status} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
                    <span style={{ flex: 1, fontSize: '0.82rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{status}</span>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color }}>{count}</span>
                    <div style={{ width: 60, height: 4, borderRadius: 99, background: 'var(--bg-muted)', overflow: 'hidden' }}>
                      <div style={{ width: `${(count / devices.length) * 100}%`, height: '100%', background: color, borderRadius: 99 }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Selected device detail */}
          {selected ? (
            <div className="card animate-in">
              <div className="card-header">
                <div>
                  <div className="card-title">{selected.hostname}</div>
                  <div className="card-subtitle">{selected.vendor} · {selected.device_type}</div>
                </div>
                <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setSelected(null)}>✕</button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  ['IP Address',  <span className="mono" style={{ color: 'var(--brand-300)' }} key="ip">{selected.ip_address}:{selected.ssh_port}</span>],
                  ['Status',      <StatusBadge key="st" status={selected.status} />],
                  ['Model',       selected.model ?? '—'],
                  ['Group',       groups.find((g) => g.id === selected.group_id)?.name ?? '—'],
                  ['Last Seen',   selected.last_checked ? new Date(selected.last_checked).toLocaleString() : 'Never'],
                ].map(([k, v]) => (
                  <div key={k as string} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <span style={{ fontSize: '0.68rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>{k}</span>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-primary)' }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '28px 20px' }}>
              <Network size={28} color="var(--text-muted)" style={{ margin: '0 auto 10px' }} />
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Click a node to inspect the device</p>
            </div>
          )}

          {/* Groups */}
          {groups.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">Groups</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {groups.map((g) => {
                  const count = devices.filter((d) => d.group_id === g.id).length;
                  const onlineCount = devices.filter((d) => d.group_id === g.id && d.status === 'online').length;
                  return (
                    <div key={g.id} style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '8px 10px', borderRadius: 'var(--radius-md)',
                      background: 'var(--bg-muted)', border: '1px solid var(--border-subtle)',
                    }}>
                      <div style={{
                        width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                        background: onlineCount === count ? 'var(--status-online)' : onlineCount === 0 ? 'var(--status-offline)' : 'var(--status-unreachable)',
                      }} />
                      <span style={{ flex: 1, fontSize: '0.82rem', fontWeight: 600 }}>{g.name}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{onlineCount}/{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
