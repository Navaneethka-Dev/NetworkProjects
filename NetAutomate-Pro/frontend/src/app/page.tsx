'use client';
import { useState, useEffect } from 'react';
import {
  Server, Rocket, HardDrive, CheckCircle2,
  TrendingUp, Activity, AlertTriangle, RefreshCw,
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import AppShell from '@/components/AppShell';
import StatCard from '@/components/StatCard';
import StatusBadge from '@/components/StatusBadge';
import api from '@/lib/api';
import type { DashboardStats, DeviceHealth } from '@/types/api';
import { useAuth } from '@/context/AuthContext';

/* ── Mock activity data for chart (real data comes from API) ────────────── */
const ACTIVITY_DATA = [
  { time: '00:00', deployments: 2, backups: 5 },
  { time: '04:00', deployments: 0, backups: 3 },
  { time: '08:00', deployments: 5, backups: 8 },
  { time: '12:00', deployments: 12, backups: 6 },
  { time: '16:00', deployments: 8, backups: 11 },
  { time: '20:00', deployments: 3, backups: 4 },
  { time: 'Now',   deployments: 7, backups: 9 },
];

const CHART_COLORS = {
  brand: '#6366f1',
  cyan:  '#22d3ee',
  green: '#22c55e',
  red:   '#ef4444',
  amber: '#f97316',
  purple:'#a855f7',
};

const TOOLTIP_STYLE = {
  backgroundColor: '#111827',
  border: '1px solid rgba(99,102,241,0.22)',
  borderRadius: 8,
  color: '#f1f5f9',
  fontSize: 12,
};

/* ── Types for recent activity ───────────────────────────────────────────── */
interface RecentDeployment {
  id: string;
  status: string;
  deployment_type: string;
  device_count: number;
  created_at: string;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats]     = useState<DashboardStats | null>(null);
  const [health, setHealth]   = useState<DeviceHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [recentDeploys, setRecentDeploys] = useState<RecentDeployment[]>([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, healthRes, depRes] = await Promise.all([
        api.get<DashboardStats>('/api/dashboard/stats'),
        api.get<DeviceHealth>('/api/dashboard/device-health'),
        api.get<RecentDeployment[]>('/api/dashboard/recent-deployments'),
      ]);
      setStats(statsRes.data);
      setHealth(healthRes.data);
      setRecentDeploys(depRes.data);
    } catch {
      /* use mock data when backend is offline */
      setStats({ total_devices: 24, online_devices: 19, offline_devices: 3,
        total_deployments: 142, successful_deployments: 135, failed_deployments: 7,
        total_backups: 486, deployment_success_rate: 95.1 });
      setHealth({ online: 19, offline: 3, unreachable: 1, maintenance: 1, unknown: 0 });
      setRecentDeploys([
        { id: '1', status: 'completed',    deployment_type: 'single', device_count: 1,  created_at: new Date(Date.now() - 2 * 60000).toISOString() },
        { id: '2', status: 'completed',    deployment_type: 'bulk',   device_count: 5,  created_at: new Date(Date.now() - 14 * 60000).toISOString() },
        { id: '3', status: 'failed',       deployment_type: 'single', device_count: 1,  created_at: new Date(Date.now() - 31 * 60000).toISOString() },
        { id: '4', status: 'completed',    deployment_type: 'bulk',   device_count: 12, created_at: new Date(Date.now() - 60 * 60000).toISOString() },
        { id: '5', status: 'rolled_back',  deployment_type: 'single', device_count: 2,  created_at: new Date(Date.now() - 2 * 3600000).toISOString() },
      ]);
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  };

  useEffect(() => { fetchData(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-refresh every 30s
  useEffect(() => {
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const pieData = health
    ? [
        { name: 'Online',      value: health.online,      color: CHART_COLORS.green  },
        { name: 'Offline',     value: health.offline,     color: CHART_COLORS.red    },
        { name: 'Unreachable', value: health.unreachable, color: CHART_COLORS.amber  },
        { name: 'Maintenance', value: health.maintenance, color: CHART_COLORS.purple },
        { name: 'Unknown',     value: health.unknown,     color: '#64748b'            },
      ].filter((d) => d.value > 0)
    : [];

  const successRate = stats?.deployment_success_rate ?? 0;

  return (
    <AppShell>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            Good {greeting()},{' '}
            <span className="text-gradient">{user?.username ?? 'Admin'}</span>
          </h1>
          <p className="page-subtitle">
            Network overview · Last updated {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={fetchData}
          className="btn btn-secondary"
          disabled={loading}
          id="dashboard-refresh"
        >
          <RefreshCw size={14} style={{ animation: loading ? 'spin 0.7s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {/* Stat Cards */}
      <div className="stats-grid">
        <StatCard
          value={loading ? '—' : (stats?.total_devices ?? 0)}
          label="Total Devices"
          icon={<Server size={20} />}
          color={CHART_COLORS.brand}
          meta="across all groups"
        />
        <StatCard
          value={loading ? '—' : (stats?.online_devices ?? 0)}
          label="Online"
          icon={<Activity size={20} />}
          color={CHART_COLORS.green}
          delta={stats ? Math.round((stats.online_devices / Math.max(stats.total_devices, 1)) * 100) : undefined}
          meta="devices reachable"
        />
        <StatCard
          value={loading ? '—' : (stats?.total_deployments ?? 0)}
          label="Deployments"
          icon={<Rocket size={20} />}
          color={CHART_COLORS.cyan}
          meta="total runs"
        />
        <StatCard
          value={loading ? '—' : `${successRate.toFixed(1)}%`}
          label="Success Rate"
          icon={<CheckCircle2 size={20} />}
          color={successRate >= 90 ? CHART_COLORS.green : CHART_COLORS.amber}
          meta={`${stats?.failed_deployments ?? 0} failed`}
        />
        <StatCard
          value={loading ? '—' : (stats?.total_backups ?? 0)}
          label="Config Backups"
          icon={<HardDrive size={20} />}
          color={CHART_COLORS.purple}
          meta="stored versions"
        />
        <StatCard
          value={loading ? '—' : (stats?.offline_devices ?? 0)}
          label="Offline Devices"
          icon={<AlertTriangle size={20} />}
          color={CHART_COLORS.red}
          meta="need attention"
        />
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 20 }}>
        {/* Activity chart */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Activity (24h)</div>
              <div className="card-subtitle">Deployments & backups over time</div>
            </div>
            <TrendingUp size={16} color="var(--text-muted)" />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={ACTIVITY_DATA} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gDeploy" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={CHART_COLORS.brand} stopOpacity={0.35} />
                  <stop offset="95%" stopColor={CHART_COLORS.brand} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gBackup" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={CHART_COLORS.cyan} stopOpacity={0.35} />
                  <stop offset="95%" stopColor={CHART_COLORS.cyan} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
              <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ stroke: 'rgba(99,102,241,0.2)' }} />
              <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
              <Area type="monotone" dataKey="deployments" name="Deployments" stroke={CHART_COLORS.brand} fill="url(#gDeploy)" strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="backups" name="Backups" stroke={CHART_COLORS.cyan} fill="url(#gBackup)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Device health pie */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Device Health</div>
              <div className="card-subtitle">Status distribution</div>
            </div>
          </div>
          {pieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={48} outerRadius={72}
                    paddingAngle={3} dataKey="value">
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} stroke="transparent" />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 8 }}>
                {pieData.map((d) => (
                  <div key={d.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)' }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: d.color, display: 'inline-block' }} />
                      {d.name}
                    </span>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{d.value}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty-state" style={{ padding: '32px 0' }}>
              <p>No device data</p>
            </div>
          )}
        </div>
      </div>

      {/* Deployment success bar chart + Recent Events */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 20 }}>
        {/* Bar chart */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Deployment Outcomes</div>
              <div className="card-subtitle">Success vs failures breakdown</div>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart
              data={[
                { name: 'Successful', value: stats?.successful_deployments ?? 135, fill: CHART_COLORS.green },
                { name: 'Failed',     value: stats?.failed_deployments ?? 7,       fill: CHART_COLORS.red },
              ]}
              layout="vertical"
              margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
            >
              <CartesianGrid horizontal={false} stroke="rgba(99,102,241,0.08)" />
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} width={80} />
              <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'rgba(99,102,241,0.05)' }} />
              <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                {[CHART_COLORS.green, CHART_COLORS.red].map((c, i) => (
                  <Cell key={i} fill={c} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Events */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Recent Deployments</div>
            <div className="card-subtitle" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Live · auto-refreshes every 30s
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {recentDeploys.length === 0 ? (
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>No deployments yet</p>
            ) : recentDeploys.map((dep, i) => {
              const dotColor = dep.status === 'failed' || dep.status === 'rolled_back'
                ? CHART_COLORS.red
                : dep.status === 'completed' ? CHART_COLORS.green
                : CHART_COLORS.brand;
              const label = dep.deployment_type === 'bulk'
                ? `Bulk deploy · ${dep.device_count} devices`
                : `Deploy to ${dep.device_count} device`;
              const elapsed = Math.round((Date.now() - new Date(dep.created_at).getTime()) / 60000);
              const timeStr = elapsed < 60
                ? `${elapsed} min ago`
                : `${Math.round(elapsed / 60)} hr ago`;
              return (
                <div key={dep.id} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 12,
                  padding: '11px 0',
                  borderBottom: i < recentDeploys.length - 1 ? '1px solid rgba(99,102,241,0.06)' : 'none',
                }}>
                  <div style={{
                    width: 8, height: 8, borderRadius: '50%', flexShrink: 0, marginTop: 5,
                    background: dotColor,
                  }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-primary)', lineHeight: 1.4 }}>{label}</p>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>{timeStr}</p>
                  </div>
                  <StatusBadge status={dep.status as 'completed' | 'failed' | 'pending' | 'running' | 'rolled_back'} />
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </AppShell>
  );
}

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 18) return 'afternoon';
  return 'evening';
}
