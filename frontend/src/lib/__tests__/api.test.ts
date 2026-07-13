import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('$env/static/public', () => ({ PUBLIC_API_BASE_URL: 'http://api.test' }));
vi.mock('$lib/auth', () => ({ getAccessToken: vi.fn().mockResolvedValue('test-token') }));

import { apiFetch } from '../api';

function jsonResponse(status: number, body: unknown = {}): Response {
	return new Response(JSON.stringify(body), { status });
}

describe('apiFetch retry behavior', () => {
	afterEach(() => {
		vi.restoreAllMocks();
		vi.useRealTimers();
	});

	it('returns immediately on success without retrying', async () => {
		const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200));
		vi.stubGlobal('fetch', fetchMock);

		const res = await apiFetch('/api/v1/accounts');

		expect(res.status).toBe(200);
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});

	it('does not retry a non-retryable error status (e.g. 404)', async () => {
		const fetchMock = vi.fn().mockResolvedValue(jsonResponse(404));
		vi.stubGlobal('fetch', fetchMock);

		const res = await apiFetch('/api/v1/accounts/999');

		expect(res.status).toBe(404);
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});

	it('retries a 502 (Lambda cold-start symptom) and returns the eventual success', async () => {
		vi.useFakeTimers();
		const fetchMock = vi
			.fn()
			.mockResolvedValueOnce(jsonResponse(502))
			.mockResolvedValueOnce(jsonResponse(200));
		vi.stubGlobal('fetch', fetchMock);

		const resultPromise = apiFetch('/api/v1/accounts');
		await vi.runAllTimersAsync();
		const res = await resultPromise;

		expect(res.status).toBe(200);
		expect(fetchMock).toHaveBeenCalledTimes(2);
	});

	it('gives up after the max retry count and returns the last failing response', async () => {
		vi.useFakeTimers();
		const fetchMock = vi.fn().mockResolvedValue(jsonResponse(503));
		vi.stubGlobal('fetch', fetchMock);

		const resultPromise = apiFetch('/api/v1/accounts');
		await vi.runAllTimersAsync();
		const res = await resultPromise;

		expect(res.status).toBe(503);
		expect(fetchMock).toHaveBeenCalledTimes(3); // initial attempt + 2 retries
	});
});
