'use client';
import { useState, useEffect, useCallback } from 'react';
import { Plus, Search, RefreshCw, Wifi, WifiOff, Edit2, Trash2, Activity, ChevronDown } from 'lucide-react';
import AppShell from '@/components/AppShell';
import StatusBadge from '@/components/StatusBadge';
import api from '@/lib/api';
import type { Device, DeviceGroup } from '@/types/api';

const VENDORS = ['cisco', 'juniper', 'arista'];
const STATUSES = ['online', 'offline', 'unreachable', 'maintenance', 'unknown'];

/* ── Add/Edit Device Modal ──────────────────────────────────────────────── */
function DeviceModal({
  device, groups, onClose, onSave,
}: {
  device?: Device;
  groups: DeviceGroup[];
  onClose: () => void;
  onSave: () => void;
}) {
  const isEdit = !!device;
  const [form, setForm] = useState({
    hostname:    device?.hostname    ?? '',
    ip_address:  device?.ip_address  ?? '',
    device_type: device?.device_type ?? '',
    vendor:      device?.vendor      ?? 'cisco',
    model:       device?.model       ?? '',
    ssh_port:    device?.ssh_port    ?? 22,
    username:    device?.username    ?? '',
    password:    '',
    group_id:    device?.group_id    ?? '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError]   = useState('');

  const set = (k: string, v: string | number) => setForm((f) => ({ ...f, [k]: v }));

  const handleSave = async () => {
    if (!form.hostname || !form.ip_address) { setError('Hostname and IP are required.'); return; }
    setSaving(true);
    setError('');
    try {
      if (isEdit) {
        await api.put(`/api/devices/${device!.id}`, form);
      } else {
        await api.post('/api/devices', form);
      }
      onSave();
      onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Failed to save device.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3 className="modal-title">{isEdit ? 'Edit Device' : 'Add Device'}</h3>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>✕</button>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: 16 }}>{error}</div>}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <div className="form-group" style={{ gridColumn: '1/-1' }}>
            <label className="form-label">Hostname *</label>
            <input className="form-input" value={form.hostname} onChange={(e) => set('hostname', e.target.value)} placeholder="core-sw-01" />
          </div>
          <div className="form-group">
            <label className="form-label">IP Address *</label>
            <input className="form-input" value={form.ip_address} onChange={(e) => set('ip_address', e.target.value)} placeholder="10.0.0.1" />
          </div>
          <div className="form-group">
            <label className="form-label">SSH Port</label>
            <input className="form-input" type="number" value={form.ssh_port} onChange={(e) => set('ssh_port', parseInt(e.target.value) || 22)} />
          </div>
          <div className="form-group">
            <label className="form-label">Vendor</label>
            <select className="form-select" value={form.vendor} onChange={(e) => set('vendor', e.target.value)}>
              {VENDORS.map((v) => <option key={v} value={v}>{v.charAt(0).toUpperCase() + v.slice(1)}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Device Type</label>
            <input className="form-input" value={form.device_type} onChange={(e) => set('device_type', e.target.value)} placeholder="cisco_ios" />
          </div>
          <div className="form-group">
            <label className="form-label">Model</label>
            <input className="form-input" value={form.model} onChange={(e) => set('model', e.target.value)} placeholder="Catalyst 9300" />
          </div>
          <div className="form-group">
            <label className="form-label">SSH Username</label>
            <input className="form-input" value={form.username} onChange={(e) => set('username', e.target.value)} placeholder="netops" />
          </div>
          <div className="form-group">
            <label className="form-label">SSH Password</label>
            <input className="form-input" type="password" value={form.password} onChange={(e) => set('password', e.target.value)} placeholder={isEdit ? '(unchanged)' : 'secret'} />
          </div>
          <div className="form-group" style={{ gridColumn: '1/-1' }}>
            <label className="form-label">Device Group</label>
            <select className="form-select" value={form.group_id} onChange={(e) => set('group_id', e.target.value)}>
              <option value="">— None —</option>
              {groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
            </select>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button id="device-save-btn" className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : (isEdit ? 'Update Device' : 'Add Device')}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Main Page ──────────────────────────────────────────────────────────── */
export default function DevicesPage() {
  const [devices, setDevices]   = useState<Device[]>([]);
  const [groups, setGroups]     = useState<DeviceGroup[]>([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterVendor, setFilterVendor] = useState('');
  const [showModal, setShowModal]       = useState(false);
  const [editDevice, setEditDevice]     = useState<Device | undefined>();
  const [pinging, setPinging]           = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [devRes, grpRes] = await Promise.all([
        api.get<Device[]>('/api/devices'),
        api.get<DeviceGroup[]>('/api/devices/groups'),
      ]);
      setDevices(devRes.data);
      setGroups(grpRes.data);
    } catch {
      /* keep empty */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handlePing = async (id: string) => {
    setPinging(id);
    try {
      await api.post(`/api/devices/${id}/ping`);
      fetchAll();
    } catch { /* ignore */ }
    finally { setPinging(null); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this device?')) return;
    try { await api.delete(`/api/devices/${id}`); fetchAll(); } catch { /* ignore */ }
  };

  const filtered = devices.filter((d) => {
    const q = search.toLowerCase();
    const matchQ = !q || d.hostname.toLowerCase().includes(q) || d.ip_address.includes(q);
    const matchS  = !filterStatus || d.status === filterStatus;
    const matchV  = !filterVendor || d.vendor === filterVendor;
    return matchQ && matchS && matchV;
  });

  const online  = devices.filter((d) => d.status === 'online').length;
  const offline = devices.filter((d) => d.status === 'offline').length;

  return (
    <AppShell>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Devices</h1>
          <p className="page-subtitle">{devices.length} total · {online} online · {offline} offline</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={fetchAll} disabled={loading}>
            <RefreshCw size={13} style={{ animation: loading ? 'spin 0.7s linear infinite' : 'none' }} />
            Refresh
          </button>
          <button id="add-device-btn" className="btn btn-primary btn-sm" onClick={() => { setEditDevice(undefined); setShowModal(true); }}>
            <Plus size={14} /> Add Device
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <div className="search-wrap">
          <Search className="search-icon" />
          <input
            id="device-search"
            className="search-input"
            placeholder="Search hostname or IP…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select id="filter-status" className="form-select" style={{ width: 150 }} value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">All Statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
        </select>
        <select id="filter-vendor" className="form-select" style={{ width: 140 }} value={filterVendor} onChange={(e) => setFilterVendor(e.target.value)}>
          <option value="">All Vendors</option>
          {VENDORS.map((v) => <option key={v} value={v}>{v.charAt(0).toUpperCase() + v.slice(1)}</option>)}
        </select>
        {(search || filterStatus || filterVendor) && (
          <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setFilterStatus(''); setFilterVendor(''); }}>
            Clear filters
          </button>
        )}
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ padding: 48, display: 'flex', justifyContent: 'center' }}>
            <div className="spinner" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><WifiOff size={22} /></div>
            <h3>No devices found</h3>
            <p>Add your first device or adjust your filters.</p>
            <button className="btn btn-primary btn-sm" onClick={() => { setEditDevice(undefined); setShowModal(true); }}>
              <Plus size={13} /> Add Device
            </button>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Hostname</th>
                  <th>IP Address</th>
                  <th>Vendor</th>
                  <th>Type</th>
                  <th>Group</th>
                  <th>Status</th>
                  <th>Last Checked</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((d) => {
                  const group = groups.find((g) => g.id === d.group_id);
                  return (
                    <tr key={d.id}>
                      <td>
                        <span style={{ fontWeight: 600 }}>{d.hostname}</span>
                        {d.model && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>{d.model}</span>
                        )}
                      </td>
                      <td>
                        <span className="mono" style={{ fontSize: '0.82rem', color: 'var(--brand-300)' }}>
                          {d.ip_address}:{d.ssh_port}
                        </span>
                      </td>
                      <td>
                        <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>{d.vendor}</span>
                      </td>
                      <td>
                        <span className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{d.device_type}</span>
                      </td>
                      <td>
                        {group ? (
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', background: 'var(--bg-muted)', padding: '2px 8px', borderRadius: 99, border: '1px solid var(--border-subtle)' }}>
                            {group.name}
                          </span>
                        ) : <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>—</span>}
                      </td>
                      <td><StatusBadge status={d.status} /></td>
                      <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {d.last_checked ? new Date(d.last_checked).toLocaleString() : '—'}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                          <button
                            className="btn btn-ghost btn-icon btn-sm"
                            onClick={() => handlePing(d.id)}
                            disabled={pinging === d.id}
                            data-tooltip="Ping"
                          >
                            {pinging === d.id
                              ? <div className="spinner" style={{ width: 13, height: 13 }} />
                              : d.status === 'online' ? <Wifi size={13} /> : <Activity size={13} />}
                          </button>
                          <button
                            className="btn btn-ghost btn-icon btn-sm"
                            onClick={() => { setEditDevice(d); setShowModal(true); }}
                            data-tooltip="Edit"
                          >
                            <Edit2 size={13} />
                          </button>
                          <button
                            className="btn btn-ghost btn-icon btn-sm"
                            onClick={() => handleDelete(d.id)}
                            data-tooltip="Delete"
                            style={{ color: 'var(--status-offline)' }}
                          >
                            <Trash2 size={13} />
                          </button>
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

      {showModal && (
        <DeviceModal
          device={editDevice}
          groups={groups}
          onClose={() => setShowModal(false)}
          onSave={fetchAll}
        />
      )}
    </AppShell>
  );
}
