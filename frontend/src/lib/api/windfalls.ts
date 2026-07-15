import { apiFetch, apiJson, ApiError } from '$lib/api';
import type {
	Windfall,
	WindfallImportCommitRequest,
	WindfallImportCommitResponse,
	WindfallImportPreview,
	WindfallInput
} from '$lib/api/types';

export function listWindfalls(accountId: number): Promise<Windfall[]> {
	return apiJson(`/api/v1/accounts/${accountId}/windfalls`);
}

export function createWindfall(accountId: number, input: WindfallInput): Promise<Windfall> {
	return apiJson(`/api/v1/accounts/${accountId}/windfalls`, {
		method: 'POST',
		body: JSON.stringify(input)
	});
}

export function updateWindfall(
	accountId: number,
	windfallId: number,
	input: Partial<WindfallInput> & { account_id?: number }
): Promise<Windfall> {
	return apiJson(`/api/v1/accounts/${accountId}/windfalls/${windfallId}`, {
		method: 'PATCH',
		body: JSON.stringify(input)
	});
}

export function deleteWindfall(accountId: number, windfallId: number): Promise<void> {
	return apiJson(`/api/v1/accounts/${accountId}/windfalls/${windfallId}`, {
		method: 'DELETE'
	});
}

export async function exportWindfallsCsv(accountId: number): Promise<Blob> {
	const res = await apiFetch(`/api/v1/accounts/${accountId}/windfalls/export`);
	if (!res.ok) throw new ApiError(res.status, await res.text());
	return res.blob();
}

export async function previewWindfallImportCsv(
	accountId: number,
	file: File
): Promise<WindfallImportPreview> {
	const formData = new FormData();
	formData.append('file', file);
	// apiFetch, not apiJson - a FormData body must NOT have a Content-Type set
	// manually (the browser generates the multipart boundary itself); apiJson
	// would force Content-Type: application/json since none is passed here.
	const res = await apiFetch(`/api/v1/accounts/${accountId}/windfalls/import/preview`, {
		method: 'POST',
		body: formData
	});
	if (!res.ok) {
		// Mirrors apiJson's error-body handling: an error response isn't
		// guaranteed to be JSON (e.g. a proxy's 502/504 page), so a raw
		// res.json() here could throw a parse error instead of a clean
		// ApiError.
		const body = await res.json().catch(() => null);
		throw new ApiError(res.status, body);
	}
	return res.json();
}

export function commitWindfallImportCsv(
	accountId: number,
	payload: WindfallImportCommitRequest
): Promise<WindfallImportCommitResponse> {
	return apiJson(`/api/v1/accounts/${accountId}/windfalls/import/commit`, {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}
