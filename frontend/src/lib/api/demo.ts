import { PUBLIC_API_BASE_URL } from '$env/static/public';
import { ApiError } from '$lib/api';
import type { DemoForecastRequest, ForecastResponse } from '$lib/api/types';

// Deliberately bypasses apiFetch/apiJson - those attach an Auth0 access
// token via getAccessToken(), which throws for a logged-out visitor. The
// demo endpoint is public by design (see backend/src/api/demo.py) so the
// homepage can run it with no login at all.
export async function computeDemoForecast(input: DemoForecastRequest): Promise<ForecastResponse> {
	const res = await fetch(`${PUBLIC_API_BASE_URL}/api/v1/demo/forecast`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(input)
	});
	if (!res.ok) {
		const body = await res.json().catch(() => null);
		throw new ApiError(res.status, body);
	}
	return res.json() as Promise<ForecastResponse>;
}
