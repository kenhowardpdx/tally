import { PUBLIC_API_BASE_URL } from '$env/static/public';
import { getAccessToken } from '$lib/auth';

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
	const token = await getAccessToken();
	const headers = new Headers(init.headers);
	headers.set('Authorization', `Bearer ${token}`);

	return fetch(`${PUBLIC_API_BASE_URL}${path}`, { ...init, headers });
}
