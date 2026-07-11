import { PUBLIC_API_BASE_URL } from '$env/static/public';
import { getAccessToken } from '$lib/auth';

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
	const token = await getAccessToken();
	const headers = new Headers(init.headers);
	headers.set('Authorization', `Bearer ${token}`);

	return fetch(`${PUBLIC_API_BASE_URL}${path}`, { ...init, headers });
}

export class ApiError extends Error {
	constructor(
		public status: number,
		public body: unknown
	) {
		super(`API request failed with status ${status}`);
	}
}

export async function apiJson<T>(path: string, init: RequestInit = {}): Promise<T> {
	const headers = new Headers(init.headers);
	const hasBody = init.body !== undefined;
	if (hasBody && !headers.has('Content-Type')) {
		headers.set('Content-Type', 'application/json');
	}

	const res = await apiFetch(path, { ...init, headers });
	if (!res.ok) {
		const body = await res.json().catch(() => null);
		throw new ApiError(res.status, body);
	}
	if (res.status === 204) {
		return undefined as T;
	}
	return res.json() as Promise<T>;
}
