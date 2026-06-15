'use client';
import { useState, useEffect, useCallback } from 'react';
import {
  Activity, RefreshCw, Search, Filter,
  User, Server, Rocket, HardDrive, ShieldCheck, FileCode2, Trash2,
  LogIn, LogOut as LogOutIcon, Settings, AlertCircle,
} from 'lucide-react';
import AppShell from '@/components/AppShell';
import api from '@/lib/api';

/* ── Types ────────────────────────────────────────────────────────────────── */
interface AuditLogEntry {
  id: string;
  user_id: string | null;
  username: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

interface AuditSummary {
  total_events: number;
  events_today: number;
  events_this_week: number;
  active_users_this_week: number;
}

/* ── Action icon + color map ─────────────────────────────────────────────── */
const ACTION_META: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  login:            { color: '#22c55e', icon: <LogIn size={13} />,      label: 'Login' },
  logout:           { color: '#64748b', icon: <LogOutIcon size={13} />, label: 'Logout' },
  device_created:   { color: '#6366f1', icon: <Server size={13} />,    label: 'Device Added' },
  device_updated:   { color: '#22d3ee', icon: <Server size={13} />,    label: 'Device Updated' },
  device_deleted:   { color: '#ef4444', icon: <Trash2 size={13} />,    label: 'Device Deleted' },
  device_pinged:    { color: '#a855f7', icon: <Server size={13} />,    label: 'Device Pinged' },
  deployment_created: { color: '#6366f1', icon: <Rocket size={13} />,  label: 'Deployment Started' },
  deployment_rollback: { color: '#f97316', icon: <Rocket size={13} />, label: 'Deployment Rolled Back' },
  backup_created:   { color: '#22c55e', icon: <HardDrive size={13} />, label: 'Backup Created' },
  backup_restored:  { color: '#f97316', icon: <HardDrive size={13} />, label: 'Backup Restored' },
  template_created: { color: '#6366f1', icon: <FileCode2 size={13} />, label: 'Template Created' },
  template_updated: { color: '#22d3ee', icon: <FileCode2 size={13} />, label: 'Template Updated' },
  template_deleted: { color: '#ef4444', icon: <FileCode2 size={13} />, label: 'Template Deleted' },
  compliance_run:   { color: '#22c55e', icon: <ShieldCheck size={13} />, label: 'Compliance Run' },
  user_created:     { color: '#a855f7', icon: <User size={13} />,      label: 'User Created' },
  user_updated:     { color: '#22d3ee', icon: <User size={13} />,      label: 'User Updated' },
  settings_changed: { color: '#f97316', icon: <Settings size={13} />,  label: 'Settings Changed' },
};

function getActionMeta(action: string) {
  const key = action.toLowerCase().replace(/\s+/g, '_');
  return ACTION_META[key] ?? { color: '#64748b', icon: <Activity size={13} />, label: action };
}

/* ── Time formatting ──────────────────────────────────────────────────────── */
function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const secs  = Math.floor(diff / 1000);
  const mins  = Math.floor(secs / 60);
  const hours = Math.floor(mins / 60);
  const days  = Math.floor(hours / 24);
  if (secs  < 60)  return `${secs}s ago`;
  if (mins  < 60)  return `${mins}m ago`;
  if (hours < 24)  return `${hours}h ago`;
  return `${days}d ago`;
}

/* ── Mock data generator ─────────────────────────────────────────────────── */
function generateMockLogs(): AuditLogEntry[] {
  const actions = [
    'device_created', 'backup_created', 'deployment_created', 'device_pinged',
    'login', 'template_created', 'compliance_run', 'device_updated',
    'backup_restored', 'deployment_rollback', 'device_deleted', 'template_updated',
  ];
  const users = [
    { id: 'u1', username: 'admin' },
    { id: 'u2', username: 'netops1' },
    { id: 'u3', username: 'readonly' },
  ];
  const resources = ['device', 'backup', 'deployment', 'template', 'compliance'];

  return Array.from({ length: 40 }, (_, i) => {
    const action = actions[i % actions.length];
    const user = users[i % users.length];
    const meta = getActionMeta(action);
    const msAgo = i * (Math.floor(Math.random() * 5 + 1) * 60000) + i * 30000;
    return {
      id: `log-${i}`,
      user_id: user.id,
      username: user.username,
      action,
      resource_type: resources[i % resources.length],
      resource_id: `${i + 100}`,
      details: { note: meta.label },
      ip_address: `10.${(i % 5) + 1}.0.${(i % 20) + 1}`,
      created_at: new Date(Date.now() - msAgo).toISOString(),
    };
  });
}

/* ── Main Page ────────────────────────────────────────────────────────────── */
export default function AuditLogPage() {
  const [logs, setLogs]         = useState<AuditLogEntry[]>([]);
  const [summary, setSummary]   = useState<AuditSummary | null>(null);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [filterResource, setFilterResource] = useState('');
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [logsRes, summaryRes] = await Promise.all([
        api.get<AuditLogEntry[]>('/api/audit-logs?limit=50'),
        api.get<AuditSummary>('/api/audit-logs/summary'),
      ]);
      setLogs(logsRes.data);
      setSummary(summaryRes.data);
    } catch {
      // Use mock data when backend is offline
      setLogs(generateMockLogs());
      setSummary({
        total_events: 1284,
        events_today: 47,
        events_this_week: 312,
        active_users_this_week: 4,
      });
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Auto-refresh every 30s
  useEffect(() => {
    const t = setInterval(fetchData, 30000);
    return () => clearInterval(t);
  }, [fetchData]);

  const filtered = logs.filter((log) => {
    const q = search.toLowerCase();
    const matchQ = !q
      || log.action.toLowerCase().includes(q)
      || (log.username ?? '').toLowerCase().includes(q)
      || (log.resource_type ?? '').toLowerCase().includes(q)
      || (log.ip_address ?? '').includes(q);
    const matchA = !filterAction    || log.action === filterAction;
    const matchR = !filterResource  || log.resource_type === filterResource;
    return matchQ && matchA && matchR;
  });

  const uniqueActions   = Array.from(new Set(logs.map((l) => l.action))).sort();
  const uniqueResources = Array.from(new Set(logs.map((l) => l.resource_type).filter(Boolean))).sort() as string[];

  return (
    <AppShell>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span className="text-gradient">Activity</span> Log
          </h1>
          <p className="page-subtitle">
            Audit trail of all user actions · Last updated {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={fetchData}
          className="btn btn-secondary"
          disabled={loading}
          id="audit-refresh-btn"
        >
          <RefreshCw size={14} style={{ animation: loading ? 'spin 0.7s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {/* Summary stat cards */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        {[
          { label: 'Total Events',           value: summary?.total_events ?? '—',          color: '#6366f1', icon: <Activity size={18} /> },
          { label: 'Events Today',           value: summary?.events_today ?? '—',          color: '#22c55e', icon: <RefreshCw size={18} /> },
          { label: 'Events This Week',       value: summary?.events_this_week ?? '—',      color: '#22d3ee', icon: <Filter size={18} /> },
          { label: 'Active Users (7d)',      value: summary?.active_users_this_week ?? '—', color: '#a855f7', icon: <User size={18} /> },
        ].map(({ label, value, color, icon }) => (
          <div key={label} className="stat-card" style={{ '--stat-color': color } as React.CSSProperties}>
            <div className="stat-icon-wrap" style={{ color }}>{icon}</div>
            <div>
              <div className="stat-value" style={{ color }}>{loading ? '—' : value}</div>
              <div className="stat-label">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <div className="search-wrap">
          <Search className="search-icon" />
          <input
            id="audit-search"
            className="search-input"
            placeholder="Search action, user, IP…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select
          className="form-select"
          style={{ width: 200 }}
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
        >
          <option value="">All Actions</option>
          {uniqueActions.map((a) => (
            <option key={a} value={a}>{getActionMeta(a).label}</option>
          ))}
        </select>

        <select
          className="form-select"
          style={{ width: 180 }}
          value={filterResource}
          onChange={(e) => setFilterResource(e.target.value)}
        >
          <option value="">All Resources</option>
          {uniqueResources.map((r) => (
            <option key={r} value={r} style={{ textTransform: 'capitalize' }}>{r}</option>
          ))}
        </select>

        {(search || filterAction || filterResource) && (
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => { setSearch(''); setFilterAction(''); setFilterResource(''); }}
          >
            Clear
          </button>
        )}

        <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          {filtered.length} event{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Log table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
            <div className="spinner" style={{ width: 32, height: 32 }} />
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <AlertCircle size={24} />
            </div>
            <h3>No events found</h3>
            <p>Try adjusting your search or filters.</p>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Action</th>
                  <th>User</th>
                  <th>Resource</th>
                  <th>IP Address</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((log) => {
                  const meta = getActionMeta(log.action);
                  return (
                    <tr key={log.id}>
                      {/* Action */}
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{
                            width: 28, height: 28, borderRadius: 'var(--radius-sm)',
                            background: `${meta.color}22`,
                            border: `1px solid ${meta.color}44`,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: meta.color, flexShrink: 0,
                          }}>
                            {meta.icon}
                          </span>
                          <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{meta.label}</span>
                        </div>
                      </td>

                      {/* User */}
                      <td>
                        {log.username ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <div style={{
                              width: 22, height: 22, borderRadius: '50%',
                              background: 'var(--gradient-brand)',
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontSize: '0.6rem', fontWeight: 800, color: 'white', flexShrink: 0,
                            }}>
                              {log.username[0].toUpperCase()}
                            </div>
                            <span className="mono" style={{ fontSize: '0.8rem' }}>{log.username}</span>
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>system</span>
                        )}
                      </td>

                      {/* Resource */}
                      <td>
                        {log.resource_type ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            <span style={{
                              fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase',
                              letterSpacing: '0.07em', color: 'var(--brand-400)',
                            }}>
                              {log.resource_type}
                            </span>
                            {log.resource_id && (
                              <span className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                #{log.resource_id.slice(0, 8)}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </td>

                      {/* IP */}
                      <td>
                        <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          {log.ip_address ?? '—'}
                        </span>
                      </td>

                      {/* Time */}
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                          <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>{timeAgo(log.created_at)}</span>
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            {new Date(log.created_at).toLocaleString()}
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Timeline view (last 10 events as a visual feed) */}
      {!loading && filtered.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Recent Activity Timeline</div>
              <div className="card-subtitle">Last 10 events chronologically</div>
            </div>
            <Activity size={16} color="var(--text-muted)" />
          </div>
          <div style={{ position: 'relative' }}>
            {/* Vertical line */}
            <div style={{
              position: 'absolute', left: 20, top: 0, bottom: 0, width: 1,
              background: 'var(--border-subtle)',
            }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {filtered.slice(0, 10).map((log, i) => {
                const meta = getActionMeta(log.action);
                return (
                  <div key={log.id} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 16,
                    paddingBottom: i < 9 ? 20 : 0,
                    paddingLeft: 8,
                    animation: `slideIn 0.35s ease ${i * 0.04}s both`,
                  }}>
                    {/* Dot */}
                    <div style={{
                      width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
                      background: `${meta.color}22`,
                      border: `2px solid ${meta.color}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: meta.color, position: 'relative', zIndex: 1,
                      marginLeft: -4,
                    }}>
                      {meta.icon}
                    </div>
                    {/* Content */}
                    <div style={{ flex: 1, paddingTop: 2 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                        <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>{meta.label}</span>
                        {log.username && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            by <span style={{ color: 'var(--brand-300)' }}>{log.username}</span>
                          </span>
                        )}
                      </div>
                      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                        {log.resource_type && (
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                            {log.resource_type}{log.resource_id ? ` #${log.resource_id.slice(0, 8)}` : ''}
                          </span>
                        )}
                        {log.ip_address && (
                          <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            {log.ip_address}
                          </span>
                        )}
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                          {timeAgo(log.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
