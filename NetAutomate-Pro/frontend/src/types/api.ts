// TypeScript interfaces matching the FastAPI response schemas

export type Role = 'admin' | 'operator' | 'viewer';

export interface User {
  id: string;
  username: string;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export type DeviceStatus = 'online' | 'offline' | 'unreachable' | 'maintenance' | 'unknown';
export type Vendor = 'cisco' | 'juniper' | 'arista';

export interface DeviceGroup {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Device {
  id: string;
  hostname: string;
  ip_address: string;
  device_type: string;
  vendor: string;
  model: string | null;
  ssh_port: number;
  username: string;
  status: DeviceStatus;
  group_id: string | null;
  last_checked: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface DevicePingResponse {
  device_id: string;
  hostname: string;
  reachable: boolean;
  message: string;
  latency_ms: number | null;
}

export interface TemplateSummary {
  id: string;
  name: string;
  description: string | null;
  vendor: string;
  variables_schema: Record<string, unknown>;
  created_at: string;
}

export interface Template extends TemplateSummary {
  template_content: string;
  created_by: string | null;
  updated_at: string;
}

export interface TemplatePreviewResponse {
  rendered_config: string;
  variables_used: Record<string, unknown>;
  template_name: string;
}

export type DeploymentStatus = 'pending' | 'running' | 'completed' | 'failed' | 'rolled_back';
export type DeploymentType = 'single' | 'bulk' | 'scheduled';

export interface DeploymentLog {
  id: string;
  deployment_id: string;
  device_id: string;
  device_hostname: string | null;
  status: 'success' | 'failed' | 'skipped';
  output: string | null;
  error_message: string | null;
  duration_seconds: number | null;
  created_at: string;
}

export interface Deployment {
  id: string;
  template_id: string | null;
  template_name: string | null;
  deployment_type: DeploymentType;
  target_devices: string[];
  rendered_config: string | null;
  variables_used: Record<string, unknown>;
  status: DeploymentStatus;
  deployed_by: string | null;
  celery_task_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  logs: DeploymentLog[];
}

export interface DeploymentSummary {
  id: string;
  template_id: string | null;
  template_name: string | null;
  deployment_type: DeploymentType;
  status: DeploymentStatus;
  device_count: number;
  deployed_by: string | null;
  created_at: string;
}

export type BackupType = 'manual' | 'scheduled' | 'pre_deployment';

export interface Backup {
  id: string;
  device_id: string;
  device_hostname: string | null;
  backup_type: BackupType;
  version_tag: string;
  checksum: string;
  config_size: number;
  created_by: string | null;
  created_at: string;
}

export interface BackupDetail extends Backup {
  config_content: string;
}

export interface BackupDiff {
  backup_a_id: string;
  backup_b_id: string;
  backup_a_tag: string;
  backup_b_tag: string;
  unified_diff: string;
  lines_added: number;
  lines_removed: number;
  lines_unchanged: number;
}

export interface DashboardStats {
  total_devices: number;
  online_devices: number;
  offline_devices: number;
  total_deployments: number;
  successful_deployments: number;
  failed_deployments: number;
  total_backups: number;
  deployment_success_rate: number;
}

export interface DeviceHealth {
  online: number;
  offline: number;
  unreachable: number;
  maintenance: number;
  unknown: number;
}

export interface ApiError {
  detail: string;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  username: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export interface AuditSummary {
  total_events: number;
  events_today: number;
  events_this_week: number;
  active_users_this_week: number;
}

export interface ComplianceRule {
  id: string;
  name: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  pattern: string;
  required: boolean;
}

export interface ComplianceCheck {
  rule: ComplianceRule;
  passed: boolean;
  found: string | null;
}

export interface ComplianceDeviceResult {
  device_id: string;
  hostname: string;
  ip_address: string;
  vendor: string;
  device_type: string;
  status: DeviceStatus;
  score: number;
  compliant: boolean;
  passed_checks: number;
  total_checks: number;
  error: string | null;
  checks: ComplianceCheck[];
}

export interface ComplianceSummary {
  total_devices: number;
  compliant_devices: number;
  non_compliant_devices: number;
  avg_score: number;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  critical_failures: number;
  mock_mode: boolean;
}

export interface ComplianceRunResponse {
  summary: ComplianceSummary;
  results: ComplianceDeviceResult[];
}
