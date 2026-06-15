'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, Server, FileCode2, Rocket, HardDrive,
  Network, LogOut, ChevronRight, Settings, Bell, GitBranch,
  ShieldCheck, ClipboardList, Users,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

const NAV_ITEMS = [
  {
    section: 'Overview',
    items: [
      { href: '/', label: 'Dashboard', icon: LayoutDashboard, roles: null },
    ],
  },
  {
    section: 'Network',
    items: [
      { href: '/devices',     label: 'Devices',     icon: Server,       roles: null },
      { href: '/topology',    label: 'Topology',    icon: GitBranch,    roles: null },
      { href: '/templates',   label: 'Templates',   icon: FileCode2,    roles: null },
      { href: '/deployments', label: 'Deployments', icon: Rocket,       roles: null },
      { href: '/backups',     label: 'Backups',     icon: HardDrive,    roles: null },
      { href: '/compliance',  label: 'Compliance',  icon: ShieldCheck,  roles: null },
    ],
  },
  {
    section: 'System',
    items: [
      { href: '/logs',     label: 'Activity Log', icon: ClipboardList, roles: null },
      { href: '/users',    label: 'Users',         icon: Users,         roles: ['admin'] as string[] },
      { href: '/settings', label: 'Settings',      icon: Settings,      roles: null },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href);

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <Network size={18} color="white" strokeWidth={2.5} />
        </div>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-name">NetAutomate</span>
          <span className="sidebar-logo-tag">Pro Platform</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((section) => {
          const visibleItems = section.items.filter(({ roles }) => {
            if (!roles) return true;
            return user?.role && roles.includes(user.role);
          });
          if (visibleItems.length === 0) return null;

          return (
            <div key={section.section}>
              <p className="nav-section-label">{section.section}</p>
              {visibleItems.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className={`nav-item ${isActive(href) ? 'active' : ''}`}
                >
                  <Icon className="nav-icon" />
                  <span>{label}</span>
                  {isActive(href) && (
                    <ChevronRight size={13} style={{ marginLeft: 'auto', opacity: 0.5 }} />
                  )}
                </Link>
              ))}
            </div>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <button
          onClick={() => {}}
          className="nav-item"
          style={{ width: '100%', marginBottom: 4, background: 'transparent', border: 'none', cursor: 'pointer', fontFamily: 'inherit' }}
        >
          <Bell className="nav-icon" />
          <span>Notifications</span>
          <span className="nav-badge">3</span>
        </button>

        <div className="user-info">
          <div className="user-avatar">
            {user?.username?.[0]?.toUpperCase() ?? 'U'}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="user-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.username ?? 'User'}
            </div>
            <div className="user-role">{user?.role ?? 'viewer'}</div>
          </div>
          <button
            onClick={logout}
            className="btn btn-ghost btn-icon btn-sm"
            data-tooltip="Sign out"
            style={{ flexShrink: 0 }}
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </aside>
  );
}
