import { type ReactNode } from 'react';

interface Props {
  value: string | number;
  label: string;
  icon: ReactNode;
  color: string;
  meta?: string;
  delta?: number;
}

export default function StatCard({ value, label, icon, color, meta, delta }: Props) {
  return (
    <div className="stat-card" style={{ '--stat-color': color } as React.CSSProperties}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div className="stat-icon-wrap" style={{ color }}>
          {icon}
        </div>
      </div>
      <div>
        <div className="stat-value">{value}</div>
        <div className="stat-label" style={{ marginTop: 4 }}>{label}</div>
      </div>
      {(meta || delta !== undefined) && (
        <div className="stat-meta">
          {delta !== undefined && (
            <span className={delta >= 0 ? 'stat-delta-pos' : 'stat-delta-neg'}>
              {delta >= 0 ? '↑' : '↓'} {Math.abs(delta)}%
            </span>
          )}
          {meta && <span>{meta}</span>}
        </div>
      )}
    </div>
  );
}
