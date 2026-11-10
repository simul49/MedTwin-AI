/**
 * Thin fetch wrapper for the MedTwin AI API.
 *
 * Requests go to the same origin (the Vite dev server proxies /api to Django),
 * so the session cookie is first-party and CSRF works normally.
 */

const CSRF_COOKIE = 'medtwin_csrf';

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

let csrfToken: string | null = null;

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

/** Fetch and cache the CSRF token. Called again after login (Django rotates it). */
export async function refreshCsrf(): Promise<string | null> {
  await fetch('/api/v1/auth/csrf/', { credentials: 'same-origin' });
  csrfToken = readCookie(CSRF_COOKIE);
  return csrfToken;
}

async function ensureCsrf(): Promise<string | null> {
  if (!csrfToken) csrfToken = readCookie(CSRF_COOKIE);
  if (!csrfToken) await refreshCsrf();
  return csrfToken;
}

type Options = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE' | 'PUT';
  body?: unknown;
  signal?: AbortSignal;
};

async function request<T>(path: string, options: Options = {}, retried = false): Promise<T> {
  const method = options.method ?? 'GET';
  const headers: Record<string, string> = { Accept: 'application/json' };

  if (method !== 'GET') {
    const token = await ensureCsrf();
    if (token) headers['X-CSRFToken'] = token;
  }
  if (options.body !== undefined && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`/api/v1${path}`, {
    method,
    credentials: 'same-origin',
    headers,
    body:
      options.body === undefined
        ? undefined
        : options.body instanceof FormData
          ? options.body
          : JSON.stringify(options.body),
    signal: options.signal,
  });

  if (response.status === 403 && !retried) {
    // Django rotates the CSRF token on login — refresh once and retry.
    await refreshCsrf();
    return request<T>(path, options, true);
  }

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const message =
      (payload && typeof payload === 'object' && 'error' in payload && (payload as { error: string }).error) ||
      (payload && typeof payload === 'object' && 'detail' in payload && (payload as { detail: string }).detail) ||
      response.statusText;
    throw new ApiError(response.status, String(message), payload);
  }
  return payload as T;
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { method: 'GET', signal }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  upload: <T>(path: string, form: FormData) => request<T>(path, { method: 'POST', body: form }),
};

/** URL for an authorised file download (session cookie is sent automatically). */
export function fileUrl(path: string): string {
  return `/api/v1${path}`;
}
