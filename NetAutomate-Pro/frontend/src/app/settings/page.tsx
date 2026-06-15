'use client';
import { useState } from 'react';
import { Settings, Bell, Shield, Database, Palette, Save } from 'lucide-react';
import AppShell from '@/components/AppShell';
import { useAuth } from '@/context/AuthContext';

const SECTIONS = [
  { id: 'profile',       label: 'Profile',       icon: Settings },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'security',      label: 'Security',       icon: Shield },
  { id: 'system',        label: 'System',         icon: Database },
  { id: 'appearance',    label: 'Appearance',     icon: Palette },
];

export default function SettingsPage() {
  const { user } = useAuth();
  const [active, setActive] = useState('profile');
  const [saved, setSaved]   = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Manage your account and platform configuration</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: 24, alignItems: 'start' }}>
        {/* Side nav */}
        <div className="card" style={{ padding: 8 }}>
          {SECTIONS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActive(id)}
              className={`nav-item ${active === id ? 'active' : ''}`}
              style={{ width: '100%', background: 'transparent', border: 'none', cursor: 'pointer', fontFamily: 'inherit', justifyContent: 'flex-start' }}
            >
              <Icon className="nav-icon" />
              {label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="card">
          {active === 'profile' && (
            <>
              <h3 style={{ marginBottom: 20 }}>Profile Settings</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 28 }}>
                <div style={{
                  width: 72, height: 72, borderRadius: '50%',
                  background: 'var(--gradient-brand)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  fontSize: '1.75rem', fontWeight: 800, color: 'white',
                  boxShadow: 'var(--shadow-glow)',
                }}>
                  {user?.username?.[0]?.toUpperCase() ?? 'U'}
                </div>
                <div>
                  <p style={{ fontWeight: 700, fontSize: '1.1rem' }}>{user?.username}</p>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{user?.email}</p>
                  <span style={{
                    fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase',
                    letterSpacing: '0.08em', color: 'var(--brand-300)',
                    background: 'rgba(99,102,241,0.15)', border: '1px solid var(--border-default)',
                    borderRadius: 99, padding: '2px 8px', marginTop: 4, display: 'inline-block',
                  }}>{user?.role}</span>
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div className="form-group">
                  <label className="form-label">Display Name</label>
                  <input className="form-input" defaultValue={user?.username} />
                </div>
                <div className="form-group">
                  <label className="form-label">Email</label>
                  <input className="form-input" type="email" defaultValue={user?.email} />
                </div>
              </div>
            </>
          )}

          {active === 'notifications' && (
            <>
              <h3 style={{ marginBottom: 20 }}>Notification Preferences</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {[
                  ['Deployment Completed', 'Get notified when a deployment finishes'],
                  ['Deployment Failed',    'Alert when a deployment fails'],
                  ['Device Goes Offline',  'Alert when a device becomes unreachable'],
                  ['Backup Completed',     'Confirm when a backup succeeds'],
                  ['Scheduled Reports',    'Weekly network health digest'],
                ].map(([label, desc], i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 16px', background: 'var(--bg-muted)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                    <div>
                      <p style={{ fontWeight: 600, fontSize: '0.875rem' }}>{label}</p>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: 2 }}>{desc}</p>
                    </div>
                    <label style={{ cursor: 'pointer', position: 'relative', width: 40, height: 22 }}>
                      <input type="checkbox" defaultChecked={i < 3} style={{ opacity: 0, width: 0, height: 0 }} />
                      <span style={{
                        position: 'absolute', inset: 0, borderRadius: 99,
                        background: i < 3 ? 'var(--brand-500)' : 'var(--bg-hover)',
                        transition: 'background 0.2s', border: '1px solid var(--border-default)',
                      }} />
                    </label>
                  </div>
                ))}
              </div>
            </>
          )}

          {active === 'security' && (
            <>
              <h3 style={{ marginBottom: 20 }}>Security</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div className="form-group">
                  <label className="form-label">Current Password</label>
                  <input className="form-input" type="password" placeholder="••••••••" />
                </div>
                <div className="form-group">
                  <label className="form-label">New Password</label>
                  <input className="form-input" type="password" placeholder="••••••••" />
                </div>
                <div className="form-group">
                  <label className="form-label">Confirm New Password</label>
                  <input className="form-input" type="password" placeholder="••••••••" />
                </div>
                <div className="divider" />
                <div style={{ background: 'var(--bg-muted)', borderRadius: 'var(--radius-md)', padding: '14px 16px', border: '1px solid var(--border-subtle)' }}>
                  <p style={{ fontWeight: 600, marginBottom: 4 }}>Session Timeout</p>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 10 }}>Automatically log out after inactivity</p>
                  <select className="form-select" defaultValue="60">
                    <option value="15">15 minutes</option>
                    <option value="30">30 minutes</option>
                    <option value="60">1 hour</option>
                    <option value="480">8 hours</option>
                    <option value="never">Never</option>
                  </select>
                </div>
              </div>
            </>
          )}

          {active === 'system' && (
            <>
              <h3 style={{ marginBottom: 20 }}>System Configuration</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {[
                  { label: 'API Base URL',        key: 'api_url',     placeholder: 'http://localhost:8000', mono: true },
                  { label: 'Default SSH Timeout', key: 'ssh_timeout', placeholder: '30', mono: false },
                  { label: 'Max Parallel Tasks',  key: 'max_tasks',   placeholder: '10', mono: false },
                  { label: 'Backup Retention (days)', key: 'retention', placeholder: '90', mono: false },
                ].map(({ label, key, placeholder, mono }) => (
                  <div className="form-group" key={key}>
                    <label className="form-label">{label}</label>
                    <input
                      className="form-input"
                      placeholder={placeholder}
                      style={mono ? { fontFamily: 'monospace' } : undefined}
                    />
                  </div>
                ))}
                <div style={{ padding: '12px 16px', background: 'rgba(250,204,21,0.08)', border: '1px solid rgba(250,204,21,0.2)', borderRadius: 'var(--radius-md)', fontSize: '0.82rem', color: '#fde68a' }}>
                  ⚠ System settings take effect after restarting the API server.
                </div>
              </div>
            </>
          )}

          {active === 'appearance' && (
            <>
              <h3 style={{ marginBottom: 20 }}>Appearance</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div className="form-group">
                  <label className="form-label">Theme</label>
                  <div style={{ display: 'flex', gap: 10 }}>
                    {['Dark (Default)', 'System', 'Light'].map((t) => (
                      <label key={t} style={{ flex: 1 }}>
                        <div style={{
                          padding: '14px', borderRadius: 'var(--radius-md)', textAlign: 'center',
                          border: t === 'Dark (Default)' ? '2px solid var(--brand-500)' : '1px solid var(--border-subtle)',
                          background: t === 'Dark (Default)' ? 'rgba(99,102,241,0.1)' : 'var(--bg-muted)',
                          cursor: 'pointer', fontSize: '0.82rem', fontWeight: 500,
                          color: t === 'Dark (Default)' ? 'var(--brand-300)' : 'var(--text-secondary)',
                        }}>
                          {t === 'Dark (Default)' ? '🌑' : t === 'System' ? '💻' : '☀️'} {t}
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Accent Color</label>
                  <div style={{ display: 'flex', gap: 10 }}>
                    {['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'].map((c) => (
                      <button key={c} style={{
                        width: 36, height: 36, borderRadius: '50%', background: c, border: '3px solid',
                        borderColor: c === '#6366f1' ? 'white' : 'transparent', cursor: 'pointer',
                      }} />
                    ))}
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Sidebar Width</label>
                  <select className="form-select" defaultValue="260">
                    <option value="220">Compact (220px)</option>
                    <option value="260">Default (260px)</option>
                    <option value="300">Wide (300px)</option>
                  </select>
                </div>
              </div>
            </>
          )}

          {/* Save button */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 28, paddingTop: 20, borderTop: '1px solid var(--border-subtle)' }}>
            {saved && <span style={{ color: 'var(--status-online)', fontSize: '0.875rem', marginRight: 12, alignSelf: 'center' }}>✓ Settings saved</span>}
            <button id="settings-save-btn" className="btn btn-primary" onClick={handleSave}>
              <Save size={14} /> Save Changes
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
