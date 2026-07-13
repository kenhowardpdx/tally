import { PUBLIC_API_BASE_URL } from '$env/static/public';
import { getAccessToken } from '$lib/auth';

// API Gateway surfaces a Lambda cold start that overruns its execution
// window as one of these, rather than a normal error response - the app
// has no provisioned concurrency (cost-first, see infra/modules/lambda), so
// the first request after a period of inactivity (both Lambda's own cold
// start and Neon's compute waking from scale-to-zero suspend) occasionally
// hits this. A couple of short retries turns that into added latency
// instead of a broken page. Request bodies here are always a string,
// FormData, or undefined - none of which are consumed by being handed to
// fetch(), so the same `init` can be reused across attempts.
const RETRYABLE_STATUSES = new Set([502, 503, 504]);
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 750;

function delay(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
	const token = await getAccessToken();
	const headers = new Headers(init.headers);
	headers.set('Authorization', `Bearer ${token}`);

	let res: Response;
	for (let attempt = 0; ; attempt++) {
		res = await fetch(`${PUBLIC_API_BASE_URL}${path}`, { ...init, headers });
		if (res.ok || !RETRYABLE_STATUSES.has(res.status) || attempt >= MAX_RETRIES) break;
		await delay(RETRY_DELAY_MS * (attempt + 1));
	}
	return res;
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
