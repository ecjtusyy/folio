export async function apiFetch(path: string, options: RequestInit = {}) {
  return fetch(path, { ...options, credentials: 'include', headers: { ...(options.headers || {}) } });
}
export async function apiJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await apiFetch(path, options);
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return (await res.json()) as T;
}
