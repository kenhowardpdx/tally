import { apiJson } from '$lib/api';
import type { Transaction, TransactionInput } from '$lib/api/types';

export function listTransactions(accountId: number): Promise<Transaction[]> {
	return apiJson(`/api/v1/accounts/${accountId}/transactions`);
}

export function createTransaction(
	accountId: number,
	input: TransactionInput
): Promise<Transaction> {
	return apiJson(`/api/v1/accounts/${accountId}/transactions`, {
		method: 'POST',
		body: JSON.stringify(input)
	});
}

export function deleteTransaction(accountId: number, transactionId: number): Promise<void> {
	return apiJson(`/api/v1/accounts/${accountId}/transactions/${transactionId}`, {
		method: 'DELETE'
	});
}
