'use client';
import { useState, useEffect, useCallback } from 'react';
import {
  Users, Plus, Search, RefreshCw, Shield, Edit2, UserX, UserCheck, Eye, EyeOff,
} from 'lucide-react';
import AppShell from '@/components/AppShell';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import type { User, Role } from '@/types/api';

/* ── Role badge helper ───────────────────────────────────────────────────── */
const ROLE_STYLE: Record<Role, { bg: string; color: string; border: string }> = {
  admin:    { bg: 'rgba(239,68,68,0.12)',   color: '#f87171',  border: 'rgba(239,68,68,0.25)' },
  operator: { bg: 'rgba(99,102,241,0.12)',  color: '#818cf8',  border: 'rgba(99,102,241,0.25)' },
  viewer:   { bg: 'rgba(100,116,139,0.12)', color: '#94a3b8',  border: 'rgba(100,116,139,0.25)' },
};

function RoleBadge({ role }: { role: Role }) {
  const s = ROLE_STYLE[role];
  return (
    <span style={{
      fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em',
      padding: '2px 9px', borderRadius: 99, background: s.bg, color: s.color,
      border: `1px solid ${s.border}`,
    }}>
      {role}
    </span>
  );
}

/* ── Create / Edit User Modal ────────────────────────────────────────────── */
interface UserForm { username: string; email: string; password: string; role: Role; }

function UserModal({
  user, onClose, onSave,
}: { user?: User; onClose: () => void; onSave: () => void }) {
  const isEdit = !!user;
  const [form, setForm] = useState<UserForm>({
    username: user?.username ?? '',
    email:    user?.email    ?? '',
    password: '',
    role:     user?.role     ?? 'viewer',
  });
  const [showPass, setShowPass] = useState(false);
  const [saving, setSaving]     = useState(false);
  const [error, setError]       = useState('');

  const set = (k: keyof UserForm, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSave = async () => {
    if (!form.username || !form.email) { setError('Username and email are required.'); return; }
    if (!isEdit && form.password.length < 8) { setError('Password must be at least 8 characters.'); return; }
    setSaving(true); setError('');
    try {
      if (isEdit) {
        const payload: Record<string, unknown> = { email: form.email, role: form.role };
        if (form.password) payload.password = form.password;
        await api.put(`/api/users/${user!.id}`, payload);
      } else {
        await api.post('/api/auth/register', form);
      }
      onSave(); onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Failed to save user.');
    } finally { setSaving(false); }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3 className="modal-title">{isEdit ? `Edit — ${user!.username}` : 'Create New User'}</h3>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>✕</button>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: 16 }}>{error}</div>}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <div className="form-group">
              <label className="form-label">Username *</label>
              <input
                id="user-username"
                className="form-input"
                value={form.username}
                onChange={(e) => set('username', e.target.value)}
                disabled={isEdit}
                placeholder="johndoe"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Role</label>
              <select id="user-role" className="form-select" value={form.role} onChange={(e) => set('role', e.target.value as Role)}>
                <option value="viewer">Viewer</option>
                <option value="operator">Operator</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Email *</label>
            <input
              id="user-email"
              className="form-input"
              type="email"
              value={form.email}
              onChange={(e) => set('email', e.target.value)}
              placeholder="john@example.com"
            />
          </div>

          <div className="form-group">
            <label className="form-label">{isEdit ? 'New Password (leave blank to keep current)' : 'Password *'}</label>
            <div style={{ position: 'relative' }}>
              <input
                id="user-password"
                className="form-input"
                type={showPass ? 'text' : 'password'}
                value={form.password}
                onChange={(e) => set('password', e.target.value)}
                placeholder={isEdit ? '••••••••' : 'min 8 characters'}
                style={{ paddingRight: 44 }}
              />
              <button
                type="button"
                onClick={() => setShowPass(!showPass)}
                style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)',
                  display: 'flex', alignItems: 'center',
                }}
              >
                {showPass ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button id="user-save-btn" className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Saving…</> : (isEdit ? 'Update User' : 'Create User')}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Main Page ───────────────────────────────────────────────────────────── */
export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers]       = useState<User[]>([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [showModal, setShowModal]   = useState(false);
  const [editUser, setEditUser]     = useState<User | undefined>();

  // Redirect non-admins
  const isAdmin = currentUser?.role === 'admin';

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get<User[]>('/api/users');
      setUsers(data);
    } catch { /* keep empty */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleToggleActive = async (u: User) => {
    const action = u.is_active ? 'deactivate' : 'reactivate';
    if (!confirm(`Are you sure you want to ${action} user "${u.username}"?`)) return;
    try {
      if (u.is_active) {
        await api.delete(`/api/users/${u.id}`);
      } else {
        await api.put(`/api/users/${u.id}`, { is_active: true });
      }
      fetchAll();
    } catch { /* ignore */ }
  };

  const filtered = users.filter((u) => {
    const q = search.toLowerCase();
    const matchQ = !q || u.username.toLowerCase().includes(q) || u.email.toLowerCase().includes(q);
    const matchR = !filterRole || u.role === filterRole;
    return matchQ && matchR;
  });

  const roleCounts = {
    admin:    users.filter((u) => u.role === 'admin').length,
    operator: users.filter((u) => u.role === 'operator').length,
    viewer:   users.filter((u) => u.role === 'viewer').length,
    active:   users.filter((u) => u.is_active).length,
  };

  if (!isAdmin) {
    return (
      <AppShell>
        <div className="empty-state" style={{ paddingTop: 80 }}>
          <div className="empty-state-icon"><Shield size={22} /></div>
          <h3>Admin Access Required</h3>
          <p>You need administrator privileges to manage users.</p>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Users</h1>
          <p className="page-subtitle">
            {users.length} total · {roleCounts.active} active · {roleCounts.admin} admin · {roleCounts.operator} operator · {roleCounts.viewer} viewer
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={fetchAll} disabled={loading}>
            <RefreshCw size={13} style={{ animation: loading ? 'spin 0.7s linear infinite' : 'none' }} />
            Refresh
          </button>
          <button id="add-user-btn" className="btn btn-primary btn-sm" onClick={() => { setEditUser(undefined); setShowModal(true); }}>
            <Plus size={14} /> New User
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        {[
          { label: 'Total Users',  value: users.length,         color: 'var(--brand-500)' },
          { label: 'Admins',       value: roleCounts.admin,     color: '#ef4444' },
          { label: 'Operators',    value: roleCounts.operator,  color: 'var(--brand-400)' },
          { label: 'Viewers',      value: roleCounts.viewer,    color: '#64748b' },
        ].map(({ label, value, color }) => (
          <div key={label} className="card" style={{ padding: '18px 22px', display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{
              width: 42, height: 42, borderRadius: 'var(--radius-md)',
              background: `${color}18`, border: `1px solid ${color}30`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Users size={18} color={color} />
            </div>
            <div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text-primary)' }}>{value}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <div className="search-wrap">
          <Search className="search-icon" />
          <input
            id="user-search"
            className="search-input"
            placeholder="Search users…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select className="form-select" style={{ width: 140 }} value={filterRole} onChange={(e) => setFilterRole(e.target.value)}>
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="operator">Operator</option>
          <option value="viewer">Viewer</option>
        </select>
        {filterRole && <button className="btn btn-ghost btn-sm" onClick={() => setFilterRole('')}>Clear</button>}
      </div>

      {/* Users Table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ padding: 48, display: 'flex', justifyContent: 'center' }}><div className="spinner" /></div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><Users size={22} /></div>
            <h3>No users found</h3>
            <p>Create the first user or adjust your search.</p>
            <button className="btn btn-primary btn-sm" onClick={() => { setEditUser(undefined); setShowModal(true); }}>
              <Plus size={13} /> New User
            </button>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                          width: 36, height: 36, borderRadius: '50%',
                          background: u.role === 'admin'
                            ? 'linear-gradient(135deg,#ef4444,#f97316)'
                            : u.role === 'operator'
                            ? 'var(--gradient-brand)'
                            : 'linear-gradient(135deg,#475569,#64748b)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '0.875rem', fontWeight: 700, color: 'white', flexShrink: 0,
                        }}>
                          {u.username[0].toUpperCase()}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                            {u.username}
                            {u.id === currentUser?.id && (
                              <span style={{ fontSize: '0.65rem', color: 'var(--brand-400)', background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 99, padding: '1px 6px' }}>
                                You
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 1 }}>{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td><RoleBadge role={u.role} /></td>
                    <td>
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: 5,
                        fontSize: '0.72rem', fontWeight: 600,
                        color: u.is_active ? 'var(--status-online)' : 'var(--status-offline)',
                      }}>
                        <span style={{
                          width: 7, height: 7, borderRadius: '50%',
                          background: u.is_active ? 'var(--status-online)' : 'var(--status-offline)',
                          animation: u.is_active ? 'dotPulse 1.4s infinite' : 'none',
                        }} />
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={() => { setEditUser(u); setShowModal(true); }}
                          data-tooltip="Edit user"
                          disabled={u.id === currentUser?.id && u.role !== 'admin'}
                        >
                          <Edit2 size={13} /> Edit
                        </button>
                        <button
                          className="btn btn-ghost btn-icon btn-sm"
                          onClick={() => handleToggleActive(u)}
                          disabled={u.id === currentUser?.id}
                          data-tooltip={u.is_active ? 'Deactivate' : 'Reactivate'}
                          style={{ color: u.is_active ? 'var(--status-offline)' : 'var(--status-online)' }}
                        >
                          {u.is_active ? <UserX size={13} /> : <UserCheck size={13} />}
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

      {showModal && (
        <UserModal
          user={editUser}
          onClose={() => { setShowModal(false); setEditUser(undefined); }}
          onSave={fetchAll}
        />
      )}
    </AppShell>
  );
}
