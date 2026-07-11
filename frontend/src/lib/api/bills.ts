import { apiJson } from '$lib/api';
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
