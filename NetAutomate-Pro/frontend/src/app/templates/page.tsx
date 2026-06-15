'use client';
import { useState, useEffect, useCallback } from 'react';
import { Plus, Search, RefreshCw, FileCode2, Eye, Edit2, Trash2, Copy } from 'lucide-react';
import AppShell from '@/components/AppShell';
import api from '@/lib/api';
import type { TemplateSummary, Template } from '@/types/api';

/* ── Template View/Edit Modal ───────────────────────────────────────────── */
function TemplateModal({
  template, onClose, onSave,
}: {
  template?: TemplateSummary;
  onClose: () => void;
  onSave: () => void;
}) {
  const isEdit = !!template;
  const [full, setFull] = useState<Template | null>(null);
  const [form, setForm] = useState({
    name: template?.name ?? '',
    description: template?.description ?? '',
    vendor: template?.vendor ?? 'cisco',
    template_content: '',
    variables_schema: '{}',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isEdit && template) {
      api.get<Template>(`/api/templates/${template.id}`).then(({ data }) => {
        setFull(data);
        setForm({
          name: data.name,
          description: data.description ?? '',
          vendor: data.vendor,
          template_content: data.template_content,
          variables_schema: JSON.stringify(data.variables_schema, null, 2),
        });
      }).catch(() => {});
    }
  }, [isEdit, template]);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSave = async () => {
    if (!form.name || !form.template_content) { setError('Name and content are required.'); return; }
    setSaving(true);
    setError('');
    try {
      let schema = {};
      try { schema = JSON.parse(form.variables_schema); } catch { schema = {}; }
      const payload = { ...form, variables_schema: schema };
      if (isEdit) {
        await api.put(`/api/templates/${template!.id}`, payload);
      } else {
        await api.post('/api/templates/', payload);
      }
      onSave();
      onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Failed to save template.');
    } finally {
      setSaving(false);
    }
  };

  const copyContent = () => {
    navigator.clipboard.writeText(form.template_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 720 }}>
        <div className="modal-header">
          <h3 className="modal-title">{isEdit ? 'Edit Template' : 'New Template'}</h3>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>✕</button>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: 16 }}>{error}</div>}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <div className="form-group">
              <label className="form-label">Template Name *</label>
              <input className="form-input" value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="BGP Neighbor Config" />
            </div>
            <div className="form-group">
              <label className="form-label">Vendor</label>
              <select className="form-select" value={form.vendor} onChange={(e) => set('vendor', e.target.value)}>
                <option value="cisco">Cisco</option>
                <option value="juniper">Juniper</option>
                <option value="arista">Arista</option>
              </select>
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Description</label>
            <input className="form-input" value={form.description} onChange={(e) => set('description', e.target.value)} placeholder="Optional description" />
          </div>
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <label className="form-label" style={{ marginBottom: 0 }}>Jinja2 Template Content *</label>
              <button className="btn btn-ghost btn-sm" onClick={copyContent}>
                <Copy size={12} />{copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <textarea
              className="form-textarea"
              value={form.template_content}
              onChange={(e) => set('template_content', e.target.value)}
              style={{ minHeight: 200, fontSize: '0.8rem' }}
              placeholder={'router bgp {{ asn }}\n  neighbor {{ peer_ip }} remote-as {{ peer_asn }}\n  description {{ description }}'}
              spellCheck={false}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Variables Schema (JSON)</label>
            <textarea
              className="form-textarea"
              value={form.variables_schema}
              onChange={(e) => set('variables_schema', e.target.value)}
              style={{ minHeight: 80, fontSize: '0.8rem' }}
              spellCheck={false}
              placeholder={'{"asn": {"type": "integer"}, "peer_ip": {"type": "string"}}'}
            />
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button id="template-save-btn" className="btn btn-primary" onClick={handleSave} disabled={saving || (isEdit && !full)}>
            {saving ? 'Saving…' : (isEdit ? 'Update Template' : 'Create Template')}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Main Page ──────────────────────────────────────────────────────────── */
export default function TemplatesPage() {
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [loading, setLoading]     = useState(true);
  const [search, setSearch]       = useState('');
  const [filterVendor, setFilterVendor] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editTpl, setEditTpl]     = useState<TemplateSummary | undefined>();

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get<TemplateSummary[]>('/api/templates');
      setTemplates(data);
    } catch { /* keep empty */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this template?')) return;
    try { await api.delete(`/api/templates/${id}`); fetchAll(); } catch { /* ignore */ }
  };

  const VENDOR_COLORS: Record<string, string> = { cisco: '#049fd9', juniper: '#84cc16', arista: '#a855f7' };

  const filtered = templates.filter((t) => {
    const q = search.toLowerCase();
    const matchQ = !q || t.name.toLowerCase().includes(q) || (t.description ?? '').toLowerCase().includes(q);
    const matchV = !filterVendor || t.vendor === filterVendor;
    return matchQ && matchV;
  });

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1 className="page-title">Templates</h1>
          <p className="page-subtitle">{templates.length} Jinja2 config templates</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={fetchAll} disabled={loading}>
            <RefreshCw size={13} style={{ animation: loading ? 'spin 0.7s linear infinite' : 'none' }} /> Refresh
          </button>
          <button id="add-template-btn" className="btn btn-primary btn-sm" onClick={() => { setEditTpl(undefined); setShowModal(true); }}>
            <Plus size={14} /> New Template
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <div className="search-wrap">
          <Search className="search-icon" />
          <input id="template-search" className="search-input" placeholder="Search templates…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <select className="form-select" style={{ width: 140 }} value={filterVendor} onChange={(e) => setFilterVendor(e.target.value)}>
          <option value="">All Vendors</option>
          <option value="cisco">Cisco</option>
          <option value="juniper">Juniper</option>
          <option value="arista">Arista</option>
        </select>
      </div>

      {/* Cards Grid */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 64 }}><div className="spinner" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><FileCode2 size={22} /></div>
          <h3>No templates found</h3>
          <p>Create your first Jinja2 configuration template.</p>
          <button className="btn btn-primary btn-sm" onClick={() => { setEditTpl(undefined); setShowModal(true); }}><Plus size={13} /> New Template</button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 18 }}>
          {filtered.map((t) => (
            <div key={t.id} className="card" style={{ cursor: 'default' }}>
              {/* Vendor bar */}
              <div style={{ height: 3, borderRadius: '4px 4px 0 0', background: VENDOR_COLORS[t.vendor] ?? 'var(--brand-500)', margin: '-24px -24px 20px', width: 'calc(100% + 48px)' }} />

              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 10 }}>
                <div>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>{t.name}</h3>
                  {t.description && (
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: 3 }}>{t.description}</p>
                  )}
                </div>
                <span style={{
                  fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
                  letterSpacing: '0.08em', padding: '2px 8px', borderRadius: 99,
                  background: `${VENDOR_COLORS[t.vendor] ?? 'var(--brand-500)'}22`,
                  color: VENDOR_COLORS[t.vendor] ?? 'var(--brand-400)',
                  border: `1px solid ${VENDOR_COLORS[t.vendor] ?? 'var(--brand-500)'}44`,
                  flexShrink: 0,
                }}>{t.vendor}</span>
              </div>

              {/* Variable pills */}
              {Object.keys(t.variables_schema ?? {}).length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 14 }}>
                  {Object.keys(t.variables_schema).map((k) => (
                    <span key={k} style={{
                      fontSize: '0.7rem', fontFamily: 'var(--font-mono, monospace)',
                      background: 'var(--bg-muted)', border: '1px solid var(--border-subtle)',
                      color: 'var(--cyan-400)', padding: '1px 7px', borderRadius: 4,
                    }}>
                      {`{{ ${k} }}`}
                    </span>
                  ))}
                </div>
              )}

              <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 16 }}>
                Created {new Date(t.created_at).toLocaleDateString()}
              </p>

              <div style={{ display: 'flex', gap: 8, borderTop: '1px solid var(--border-subtle)', paddingTop: 14 }}>
                <button className="btn btn-ghost btn-sm" style={{ flex: 1 }} onClick={() => { setEditTpl(t); setShowModal(true); }}>
                  <Eye size={13} /> View / Edit
                </button>
                <button className="btn btn-ghost btn-icon btn-sm" onClick={() => handleDelete(t.id)} style={{ color: 'var(--status-offline)' }} data-tooltip="Delete">
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <TemplateModal template={editTpl} onClose={() => setShowModal(false)} onSave={fetchAll} />
      )}
    </AppShell>
  );
}
