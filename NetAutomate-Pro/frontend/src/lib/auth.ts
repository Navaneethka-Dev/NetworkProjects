import { TokenResponse, User } from '@/types/api';

export const AUTH_KEYS = {
  ACCESS: 'access_token',
  REFRESH: 'refresh_token',
  USER: 'auth_user',
} as const;

export function saveTokens(tokens: TokenResponse): void {
  localStorage.setItem(AUTH_KEYS.ACCESS, tokens.access_token);
  localStorage.setItem(AUTH_KEYS.REFRESH, tokens.refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem(AUTH_KEYS.ACCESS);
  localStorage.removeItem(AUTH_KEYS.REFRESH);
  localStorage.removeItem(AUTH_KEYS.USER);
}

export function getAccessToken(): string | null {
  return typeof window !== 'undefined' ? localStorage.getItem(AUTH_KEYS.ACCESS) : null;
}

export function saveUser(user: User): void {
  localStorage.setItem(AUTH_KEYS.USER, JSON.stringify(user));
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem(AUTH_KEYS.USER);
  return raw ? JSON.parse(raw) : null;
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}
