import { apiFetch, apiJson, ApiError } from '$lib/api';
import type { Bill, BillInput } from '$lib/api/types';

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
	const body = await res.json();
	if (!res.ok) throw new ApiError(res.status, body);
	return body;
}
