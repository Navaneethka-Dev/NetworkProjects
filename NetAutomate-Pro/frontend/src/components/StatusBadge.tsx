import type { DeviceStatus, DeploymentStatus } from '@/types/api';

type Status = DeviceStatus | DeploymentStatus | 'success' | 'skipped' | 'manual' | 'scheduled' | 'pre_deployment';

interface Props {
  status: Status;
  className?: string;
}

const LABEL_MAP: Record<string, string> = {
  online: 'Online',
  offline: 'Offline',
  unreachable: 'Unreachable',
  maintenance: 'Maintenance',
  unknown: 'Unknown',
  pending: 'Pending',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  rolled_back: 'Rolled Back',
  success: 'Success',
  skipped: 'Skipped',
  manual: 'Manual',
  scheduled: 'Scheduled',
  pre_deployment: 'Pre-Deploy',
};

export default function StatusBadge({ status, className = '' }: Props) {
  const label = LABEL_MAP[status] ?? status;
  const cls = `badge badge-${status} ${className}`;
  return <span className={cls}>{label}</span>;
}
