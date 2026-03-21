const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ApiEnvelope<T> = {
  success: boolean;
  data?: T;
  error?: { code: string; message: string; details?: Record<string, unknown> };
  meta?: Record<string, unknown>;
};

/**
 * Perform a credentialed JSON request against the Orion API.
 *
 * @param path - Absolute path beginning with `/api/v1`.
 * @param init - Fetch init options.
 * @returns Parsed JSON envelope.
 */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<ApiEnvelope<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
  const payload = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || payload.success === false) {
    const message = payload.error?.message ?? response.statusText;
    throw new Error(message);
  }
  return payload;
}
