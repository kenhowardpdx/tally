import { apiFetch, apiJson, ApiError } from '$lib/api';
import type {
	Bill,
	BillEventCycleCountsResponse,
	BillEventListResponse,
	BillHistoryResponse,
	BillInput
} from '$lib/api/types';

export function listBills(accountId: number): Promise<Bill[]> {
	return apiJson(`/api/v1/accounts/${accountId}/bills`);
}

export function createBill(accountId: number, input: BillInput): Promise<Bill> {
	return apiJson(`/api/v1/accounts/${accountId}/bills`, {
		method: 'POST',
		body: JSON.stringify(input)
	});
}

export function updateBill(
	accountId: number,
	billId: number,
	input: Partial<BillInput> & { account_id?: number }
): Promise<Bill> {
	return apiJson(`/api/v1/accounts/${accountId}/bills/${billId}`, {
		method: 'PATCH',
		body: JSON.stringify(input)
	});
}

export function deleteBill(accountId: number, billId: number): Promise<void> {
	return apiJson(`/api/v1/accounts/${accountId}/bills/${billId}`, { method: 'DELETE' });
}

export function getBillHistory(
	accountId: number,
	billId: number,
	params: { limit?: number; offset?: number } = {}
): Promise<BillHistoryResponse> {
	const query = new URLSearchParams();
	if (params.limit != null) query.set('limit', String(params.limit));
	if (params.offset != null) query.set('offset', String(params.offset));
	const qs = query.toString();
	return apiJson(`/api/v1/accounts/${accountId}/bills/${billId}/history${qs ? `?${qs}` : ''}`);
}

export function getBillEvents(
	accountId: number,
	billId: number,
	params: { limit?: number; offset?: number; cycle_start_date?: string } = {}
): Promise<BillEventListResponse> {
	const query = new URLSearchParams();
	if (params.limit != null) query.set('limit', String(params.limit));
	if (params.offset != null) query.set('offset', String(params.offset));
	if (params.cycle_start_date != null) query.set('cycle_start_date', params.cycle_start_date);
	const qs = query.toString();
	return apiJson(`/api/v1/accounts/${accountId}/bills/${billId}/events${qs ? `?${qs}` : ''}`);
}

export function getBillEventCycleCounts(
	accountId: number,
	billId: number
): Promise<BillEventCycleCountsResponse> {
	return apiJson(`/api/v1/accounts/${accountId}/bills/${billId}/events/cycle-counts`);
}

export async function exportBillsCsv(accountId: number): Promise<Blob> {
	const res = await apiFetch(`/api/v1/accounts/${accountId}/bills/export`);
	if (!res.ok) throw new ApiError(res.status, await res.text());
	return res.blob();
}

export interface BillImportRowError {
	row: number;
	message: string;
}

export async function importBillsCsv(accountId: number, file: File): Promise<Bill[]> {
	const formData = new FormData();
	formData.append('file', file);
	// apiFetch, not apiJson - a FormData body must NOT have a Content-Type set
	// manually (the browser generates the multipart boundary itself); apiJson
	// would force Content-Type: application/json since none is passed here.
	const res = await apiFetch(`/api/v1/accounts/${accountId}/bills/import`, {
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
