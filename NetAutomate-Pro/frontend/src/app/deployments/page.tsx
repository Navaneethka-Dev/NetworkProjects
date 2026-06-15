'use client';
import { useState, useEffect, useCallback } from 'react';
import { Rocket, RefreshCw, Plus, ChevronDown, ChevronRight, TerminalSquare, AlertCircle } from 'lucide-react';
import AppShell from '@/components/AppShell';
import StatusBadge from '@/components/StatusBadge';
import api from '@/lib/api';
import type { DeploymentSummary, Deployment, Device, TemplateSummary } from '@/types/api';

/* ── Deploy Modal ───────────────────────────────────────────────────────── */
function DeployModal({
  devices, templates, onClose, onDone,
}: {
  devices: Device[];
  templates: TemplateSummary[];
  onClose: () => void;
  onDone: () => void;
}) {
  const [templateId, setTemplateId] = useState('');
  const [selectedDevices, setSelectedDevices] = useState<string[]>([]);
  const [variables, setVariables] = useState('{}');
  const [error, setError] = useState('');
  const [deploying, setDeploying] = useState(false);
  const [preview, setPreview] = useState('');

  const selectedTpl = templates.find((t) => t.id === templateId);

  const toggleDevice = (id: string) =>
    setSelectedDevices((prev) => prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]);

  const handlePreview = async () => {
    if (!templateId) return;
    try {
      let vars: Record<string, unknown> = {};
      try { vars = JSON.parse(variables); } catch { vars = {}; }
      const { data } = await api.post(`/api/templates/${templateId}/preview`, { variables: vars });
      setPreview(data.rendered_config ?? '');
    } catch { setPreview('Preview unavailable.'); }
  };

  const handleDeploy = async () => {
    if (!templateId || selectedDevices.length === 0) {
      setError('Select a template and at least one device.'); return;
    }
    setDeploying(true); setError('');
    try {
      let vars: Record<string, unknown> = {};
      try { vars = JSON.parse(variables); } catch { vars = {}; }
      await api.post('/api/deployments/', {
        template_id: templateId,
        device_ids: selectedDevices,
        variables: vars,
        deployment_type: selectedDevices.length > 1 ? 'bulk' : 'single',
      });
      onDone(); onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Deployment failed to start.');
    } finally { setDeploying(false); }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 660 }}>
        <div className="modal-header">
          <h3 className="modal-title">New Deployment</h3>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>✕</button>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: 16 }}><AlertCircle size={14} />{error}</div>}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Template */}
          <div className="form-group">
            <label className="form-label">Configuration Template *</label>
            <select className="form-select" value={templateId} onChange={(e) => { setTemplateId(e.target.value); setPreview(''); }}>
              <option value="">Select a template…</option>
              {templates.map((t) => <option key={t.id} value={t.id}>{t.name} ({t.vendor})</option>)}
            </select>
          </div>

          {/* Variables */}
          {selectedTpl && Object.keys(selectedTpl.variables_schema ?? {}).length > 0 && (
            <div className="form-group">
              <label className="form-label">Template Variables (JSON)</label>
              <textarea
                className="form-textarea"
                value={variables}
                onChange={(e) => setVariables(e.target.value)}
                style={{ minHeight: 90, fontSize: '0.8rem' }}
                spellCheck={false}
                placeholder={JSON.stringify(
                  Object.fromEntries(Object.keys(selectedTpl.variables_schema).map((k) => [k, ''])),
                  null, 2
                )}
              />
              <button className="btn btn-ghost btn-sm" style={{ alignSelf: 'flex-start', marginTop: 4 }} onClick={handlePreview}>
                <TerminalSquare size={12} /> Preview Config
              </button>
            </div>
          )}

          {preview && (
            <div>
              <p className="form-label" style={{ marginBottom: 6 }}>Preview</p>
              <pre className="code-block" style={{ maxHeight: 160, overflow: 'auto' }}>{preview}</pre>
            </div>
          )}

          {/* Target devices */}
          <div className="form-group">
            <label className="form-label">Target Devices * ({selectedDevices.length} selected)</label>
            <div style={{
              background: 'var(--bg-muted)', border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)', maxHeight: 200, overflowY: 'auto',
            }}>
              {devices.map((d, i) => (
                <label key={d.id} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '9px 14px', cursor: 'pointer',
                  borderBottom: i < devices.length - 1 ? '1px solid rgba(99,102,241,0.06)' : 'none',
                  transition: 'background 0.12s',
                }}
                  className="device-checkbox-row"
                >
                  <input
                    type="checkbox"
                    checked={selectedDevices.includes(d.id)}
                    onChange={() => toggleDevice(d.id)}
                    style={{ accentColor: 'var(--brand-500)', width: 14, height: 14 }}
                  />
                  <span style={{ fontSize: '0.875rem', fontWeight: 500, flex: 1 }}>{d.hostname}</span>
                  <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{d.ip_address}</span>
                  <StatusBadge status={d.status} />
                </label>
              ))}
              {devices.length === 0 && (
                <p style={{ padding: 16, color: 'var(--text-muted)', fontSize: '0.875rem', textAlign: 'center' }}>
                  No devices available.
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button
            id="deploy-btn"
            className="btn btn-primary"
            onClick={handleDeploy}
            disabled={deploying || !templateId || selectedDevices.length === 0}
          >
            {deploying ? (
              <><div className="spinner" style={{ width: 14, height: 14 }} /> Deploying…</>
            ) : (
              <><Rocket size={14} /> Deploy ({selectedDevices.length} devices)</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Deployment Log Drawer ──────────────────────────────────────────────── */
function DeploymentDetail({ id, onClose }: { id: string; onClose: () => void }) {
  const [data, setData] = useState<Deployment | null>(null);

  useEffect(() => {
    api.get<Deployment>(`/api/deployments/${id}`)
      .then(({ data: d }) => setData(d))
      .catch(() => {});
  }, [id]);

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 700 }}>
        <div className="modal-header">
          <h3 className="modal-title">Deployment Detail</h3>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>✕</button>
        </div>
        {!data ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><div className="spinner" /></div>
        ) : (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
              {[
                ['Template',  data.template_name ?? '—'],
                ['Type',      data.deployment_type],
                ['Status',    null],
                ['Devices',   data.target_devices.length],
                ['Started',   data.started_at ? new Date(data.started_at).toLocaleString() : '—'],
                ['Completed', data.completed_at ? new Date(data.completed_at).toLocaleString() : '—'],
              ].map(([k, v]) => (
                <div key={k as string} style={{ background: 'var(--bg-muted)', borderRadius: 'var(--radius-sm)', padding: '10px 14px' }}>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{k}</p>
                  {k === 'Status'
                    ? <StatusBadge status={data.status} />
                    : <p style={{ fontWeight: 600, fontSize: '0.875rem' }}>{v as string | number}</p>}
                </div>
              ))}
            </div>

            {data.rendered_config && (
              <div style={{ marginBottom: 20 }}>
                <p className="form-label" style={{ marginBottom: 6 }}>Rendered Config</p>
                <pre className="code-block" style={{ maxHeight: 160, overflow: 'auto' }}>{data.rendered_config}</pre>
              </div>
            )}

            <div>
              <p className="form-label" style={{ marginBottom: 8 }}>Device Logs ({data.logs.length})</p>
              {data.logs.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No logs yet.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {data.logs.map((log) => (
                    <div key={log.id} style={{ background: 'var(--bg-muted)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '12px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: log.output ? 8 : 0 }}>
                        <StatusBadge status={log.status} />
                        <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{log.device_hostname ?? log.device_id}</span>
                        {log.duration_seconds && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>{log.duration_seconds}s</span>
                        )}
                      </div>
                      {log.output && <pre className="code-block" style={{ marginTop: 8, maxHeight: 100 }}>{log.output}</pre>}
                      {log.error_message && <p style={{ marginTop: 6, fontSize: '0.8rem', color: 'var(--status-offline)' }}>{log.error_message}</p>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ── Main Page ──────────────────────────────────────────────────────────── */
export default function DeploymentsPage() {
  const [deployments, setDeployments] = useState<DeploymentSummary[]>([]);
  const [devices, setDevices]         = useState<Device[]>([]);
  const [templates, setTemplates]     = useState<TemplateSummary[]>([]);
  const [loading, setLoading]         = useState(true);
  const [showDeploy, setShowDeploy]   = useState(false);
  const [detailId, setDetailId]       = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState('');

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [dRes, devRes, tplRes] = await Promise.all([
        api.get<DeploymentSummary[]>('/api/deployments'),
        api.get<Device[]>('/api/devices'),
        api.get<TemplateSummary[]>('/api/templates'),
      ]);
      setDeployments(dRes.data);
      setDevices(devRes.data);
      setTemplates(tplRes.data);
    } catch { /* keep empty */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const STATUS_COLORS: Record<string, string> = {
    pending: '#facc15', running: 'var(--cyan-400)', completed: 'var(--status-online)',
    failed: 'var(--status-offline)', rolled_back: 'var(--status-unreachable)',
  };

  const filtered = deployments.filter((d) => !filterStatus || d.status === filterStatus);

  const counts = {
    total:     deployments.length,
    running:   deployments.filter((d) => d.status === 'running').length,
    success:   deployments.filter((d) => d.status === 'completed').length,
    failed:    deployments.filter((d) => d.status === 'failed').length,
  };

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1 className="page-title">Deployments</h1>
          <p className="page-subtitle">
            {counts.total} total · {counts.running} running · {counts.success} succeeded · {counts.failed} failed
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={fetchAll} disabled={loading}>
            <RefreshCw size={13} style={{ animation: loading ? 'spin 0.7s linear infinite' : 'none' }} /> Refresh
          </button>
          <button id="new-deployment-btn" className="btn btn-primary btn-sm" onClick={() => setShowDeploy(true)}>
            <Plus size={14} /> New Deployment
          </button>
        </div>
      </div>

      {/* Filter row */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <select className="form-select" style={{ width: 160 }} value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">All Statuses</option>
          {['pending','running','completed','failed','rolled_back'].map((s) => (
            <option key={s} value={s}>{s.replace('_', ' ')}</option>
          ))}
        </select>
        {filterStatus && <button className="btn btn-ghost btn-sm" onClick={() => setFilterStatus('')}>Clear</button>}
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ padding: 48, display: 'flex', justifyContent: 'center' }}><div className="spinner" /></div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><Rocket size={22} /></div>
            <h3>No deployments yet</h3>
            <p>Push your first configuration to the network.</p>
            <button className="btn btn-primary btn-sm" onClick={() => setShowDeploy(true)}><Plus size={13} /> New Deployment</button>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Template</th>
                  <th>Type</th>
                  <th>Devices</th>
                  <th>Status</th>
                  <th>Deployed By</th>
                  <th>Created</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((d) => (
                  <tr key={d.id}>
                    <td>
                      <span style={{ fontWeight: 600 }}>{d.template_name ?? '—'}</span>
                    </td>
                    <td>
                      <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{d.deployment_type}</span>
                    </td>
                    <td>
                      <span style={{
                        background: 'rgba(99,102,241,0.15)', color: 'var(--brand-300)',
                        border: '1px solid var(--border-default)', borderRadius: 99,
                        padding: '2px 9px', fontSize: '0.78rem', fontWeight: 600,
                      }}>{d.device_count}</span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        {d.status === 'running' && (
                          <div style={{ width: 6, height: 6, borderRadius: '50%', background: STATUS_COLORS.running, animation: 'dotPulse 1.4s infinite' }} />
                        )}
                        <StatusBadge status={d.status} />
                      </div>
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{d.deployed_by ?? '—'}</td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {new Date(d.created_at).toLocaleString()}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button className="btn btn-ghost btn-sm" onClick={() => setDetailId(d.id)}>
                        <ChevronRight size={13} /> Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showDeploy && (
        <DeployModal devices={devices} templates={templates} onClose={() => setShowDeploy(false)} onDone={fetchAll} />
      )}
      {detailId && (
        <DeploymentDetail id={detailId} onClose={() => setDetailId(null)} />
      )}
    </AppShell>
  );
}
