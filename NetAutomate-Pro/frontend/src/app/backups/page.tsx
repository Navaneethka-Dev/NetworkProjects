'use client';
import { useState, useEffect, useCallback } from 'react';
import { HardDrive, RefreshCw, Download, GitCompare, Search, Play, Eye, Trash2, ChevronDown } from 'lucide-react';
import AppShell from '@/components/AppShell';
import StatusBadge from '@/components/StatusBadge';
import api from '@/lib/api';
import type { Backup, BackupDetail, BackupDiff, Device } from '@/types/api';

/* ── Backup Content Modal ───────────────────────────────────────────────── */
function BackupViewModal({ backup, onClose }: { backup: BackupDetail; onClose: () => void }) {
  const downloadConfig = () => {
    const blob = new Blob([backup.config_content], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${backup.device_hostname ?? backup.device_id}_${backup.version_tag}.txt`;
    a.click();
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 720 }}>
        <div className="modal-header">
          <div>
            <h3 className="modal-title">{backup.device_hostname ?? backup.device_id}</h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 2 }}>
              {backup.version_tag} · {new Date(backup.created_at).toLocaleString()}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary btn-sm" onClick={downloadConfig}>
              <Download size={13} /> Download
            </button>
            <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>✕</button>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          {[
            ['Type',     backup.backup_type],
            ['Size',     `${(backup.config_size / 1024).toFixed(1)} KB`],
            ['Checksum', backup.checksum.slice(0, 16) + '…'],
          ].map(([k, v]) => (
            <div key={k} style={{ background: 'var(--bg-muted)', borderRadius: 'var(--radius-sm)', padding: '7px 12px', fontSize: '0.78rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>{k}: </span>
              <span style={{ fontWeight: 600 }}>{v}</span>
            </div>
          ))}
          <StatusBadge status={backup.backup_type} />
        </div>
        <pre className="code-block" style={{ maxHeight: 400, overflow: 'auto' }}>{backup.config_content}</pre>
      </div>
    </div>
  );
}

/* ── Diff Modal ─────────────────────────────────────────────────────────── */
function DiffModal({ diff, onClose }: { diff: BackupDiff; onClose: () => void }) {
  const lines = diff.unified_diff.split('\n');
  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 780 }}>
        <div className="modal-header">
          <div>
            <h3 className="modal-title">Config Diff</h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 2 }}>
              {diff.backup_a_tag} → {diff.backup_b_tag}
            </p>
          </div>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>✕</button>
        </div>
        <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
          {[
            { label: `+${diff.lines_added} added`, color: 'var(--status-online)' },
            { label: `-${diff.lines_removed} removed`, color: 'var(--status-offline)' },
            { label: `${diff.lines_unchanged} unchanged`, color: 'var(--text-muted)' },
          ].map(({ label, color }) => (
            <span key={label} style={{
              fontSize: '0.78rem', fontWeight: 600, color,
              background: `${color}18`, border: `1px solid ${color}30`,
              padding: '3px 10px', borderRadius: 99,
            }}>{label}</span>
          ))}
        </div>
        <div className="code-block" style={{ maxHeight: 420, overflow: 'auto', fontSize: '0.78rem' }}>
          {lines.map((line, i) => (
            <div key={i} style={{
              color: line.startsWith('+') ? 'var(--status-online)'
                : line.startsWith('-') ? 'var(--status-offline)'
                : line.startsWith('@@') ? 'var(--cyan-400)'
                : undefined,
              background: line.startsWith('+') ? 'rgba(34,197,94,0.07)'
                : line.startsWith('-') ? 'rgba(239,68,68,0.07)'
                : undefined,
              padding: '1px 0',
            }}>{line || '\u00A0'}</div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── Trigger Backup Modal ───────────────────────────────────────────────── */
function TriggerModal({ devices, onClose, onDone }: { devices: Device[]; onClose: () => void; onDone: () => void }) {
  const [selected, setSelected] = useState<string[]>([]);
  const [running, setRunning]   = useState(false);
  const [error, setError]       = useState('');

  const toggle = (id: string) => setSelected((p) => p.includes(id) ? p.filter((d) => d !== id) : [...p, id]);

  const handleRun = async () => {
    if (selected.length === 0) { setError('Select at least one device.'); return; }
    setRunning(true); setError('');
    try {
      await Promise.all(selected.map((id) => api.post(`/api/backups/trigger/${id}`)));
      onDone(); onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Failed to trigger backup.');
    } finally { setRunning(false); }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3 className="modal-title">Trigger Manual Backup</h3>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>✕</button>
        </div>
        {error && <div className="alert alert-error" style={{ marginBottom: 14 }}>{error}</div>}
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: 14 }}>
          Select devices to back up immediately:
        </p>
        <div style={{ background: 'var(--bg-muted)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', maxHeight: 240, overflowY: 'auto' }}>
          {devices.map((d, i) => (
            <label key={d.id} style={{
              display: 'flex', alignItems: 'center', gap: 10, padding: '9px 14px', cursor: 'pointer',
              borderBottom: i < devices.length - 1 ? '1px solid rgba(99,102,241,0.06)' : 'none',
            }}>
              <input type="checkbox" checked={selected.includes(d.id)} onChange={() => toggle(d.id)} style={{ accentColor: 'var(--brand-500)', width: 14, height: 14 }} />
              <span style={{ fontWeight: 500, flex: 1, fontSize: '0.875rem' }}>{d.hostname}</span>
              <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{d.ip_address}</span>
              <StatusBadge status={d.status} />
            </label>
          ))}
        </div>
        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button id="trigger-backup-btn" className="btn btn-primary" onClick={handleRun} disabled={running || selected.length === 0}>
            {running ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Running…</> : <><Play size={13} /> Backup ({selected.length})</>}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Main Page ──────────────────────────────────────────────────────────── */
export default function BackupsPage() {
  const [backups, setBackups]   = useState<Backup[]>([]);
  const [devices, setDevices]   = useState<Device[]>([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState('');
  const [filterDevice, setFilterDevice] = useState('');
  const [showTrigger, setShowTrigger]   = useState(false);
  const [viewBackup, setViewBackup]     = useState<BackupDetail | null>(null);
  const [diff, setDiff]                 = useState<BackupDiff | null>(null);
  const [compareA, setCompareA]         = useState<string | null>(null);
  const [loadingView, setLoadingView]   = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [bRes, dRes] = await Promise.all([
        api.get<Backup[]>('/api/backups'),
        api.get<Device[]>('/api/devices'),
      ]);
      setBackups(bRes.data);
      setDevices(dRes.data);
    } catch { /* keep empty */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleView = async (id: string) => {
    setLoadingView(id);
    try {
      const { data } = await api.get<BackupDetail>(`/api/backups/${id}`);
      setViewBackup(data);
    } catch { /* ignore */ }
    finally { setLoadingView(null); }
  };

  const handleCompare = async (id: string) => {
    if (!compareA) {
      setCompareA(id);
    } else if (compareA === id) {
      setCompareA(null);
    } else {
      try {
        const { data } = await api.get<BackupDiff>(`/api/backups/diff?backup_a_id=${compareA}&backup_b_id=${id}`);
        setDiff(data);
        setCompareA(null);
      } catch { setCompareA(null); }
    }
  };

  const filtered = backups.filter((b) => {
    const q = search.toLowerCase();
    const matchQ = !q || (b.device_hostname ?? '').toLowerCase().includes(q) || b.version_tag.toLowerCase().includes(q);
    const matchD = !filterDevice || b.device_id === filterDevice;
    return matchQ && matchD;
  });

  const totalSize = backups.reduce((s, b) => s + b.config_size, 0);

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1 className="page-title">Backups</h1>
          <p className="page-subtitle">
            {backups.length} versions · {(totalSize / 1024 / 1024).toFixed(2)} MB stored
            {compareA && <span style={{ color: 'var(--cyan-400)', marginLeft: 12 }}>· Select a second backup to compare</span>}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={fetchAll} disabled={loading}>
            <RefreshCw size={13} style={{ animation: loading ? 'spin 0.7s linear infinite' : 'none' }} /> Refresh
          </button>
          <button id="trigger-backup-open-btn" className="btn btn-primary btn-sm" onClick={() => setShowTrigger(true)}>
            <Play size={13} /> Trigger Backup
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <div className="search-wrap">
          <Search className="search-icon" />
          <input id="backup-search" className="search-input" placeholder="Search hostname or tag…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <select className="form-select" style={{ width: 200 }} value={filterDevice} onChange={(e) => setFilterDevice(e.target.value)}>
          <option value="">All Devices</option>
          {devices.map((d) => <option key={d.id} value={d.id}>{d.hostname}</option>)}
        </select>
        {compareA && (
          <div className="alert alert-info" style={{ padding: '6px 12px', fontSize: '0.78rem' }}>
            <GitCompare size={13} />
            Comparing: <strong style={{ marginLeft: 4 }}>{backups.find((b) => b.id === compareA)?.version_tag}</strong>
            <button className="btn btn-ghost btn-sm" style={{ marginLeft: 8, padding: '2px 6px' }} onClick={() => setCompareA(null)}>Cancel</button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ padding: 48, display: 'flex', justifyContent: 'center' }}><div className="spinner" /></div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><HardDrive size={22} /></div>
            <h3>No backups found</h3>
            <p>Trigger a manual backup or configure scheduled backups.</p>
            <button className="btn btn-primary btn-sm" onClick={() => setShowTrigger(true)}><Play size={13} /> Trigger Backup</button>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Device</th>
                  <th>Version Tag</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Checksum</th>
                  <th>Created</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((b) => (
                  <tr key={b.id} style={compareA === b.id ? { background: 'rgba(34,211,238,0.07)' } : undefined}>
                    <td>
                      <span style={{ fontWeight: 600 }}>{b.device_hostname ?? b.device_id.slice(0, 8)}</span>
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--brand-300)' }}>{b.version_tag}</span>
                    </td>
                    <td><StatusBadge status={b.backup_type} /></td>
                    <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                      {b.config_size >= 1024 ? `${(b.config_size / 1024).toFixed(1)} KB` : `${b.config_size} B`}
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{b.checksum.slice(0, 12)}…</span>
                    </td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {new Date(b.created_at).toLocaleString()}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                        <button
                          className="btn btn-ghost btn-icon btn-sm"
                          onClick={() => handleView(b.id)}
                          disabled={loadingView === b.id}
                          data-tooltip="View Config"
                        >
                          {loadingView === b.id ? <div className="spinner" style={{ width: 13, height: 13 }} /> : <Eye size={13} />}
                        </button>
                        <button
                          className={`btn btn-icon btn-sm ${compareA === b.id ? 'btn-primary' : 'btn-ghost'}`}
                          onClick={() => handleCompare(b.id)}
                          data-tooltip={compareA && compareA !== b.id ? 'Compare with selected' : 'Select for diff'}
                        >
                          <GitCompare size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showTrigger && <TriggerModal devices={devices} onClose={() => setShowTrigger(false)} onDone={fetchAll} />}
      {viewBackup  && <BackupViewModal backup={viewBackup} onClose={() => setViewBackup(null)} />}
      {diff        && <DiffModal diff={diff} onClose={() => setDiff(null)} />}
    </AppShell>
  );
}
