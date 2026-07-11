import { apiJson } from '$lib/api';
import type { BankAccount, BankAccountInput } from '$lib/api/types';

export function listAccounts(): Promise<BankAccount[]> {
	return apiJson('/api/v1/accounts');
}

export function createAccount(input: BankAccountInput): Promise<BankAccount> {
	return apiJson('/api/v1/accounts', { method: 'POST', body: JSON.stringify(input) });
}

export function updateAccount(
	id: number,
	input: Partial<BankAccountInput>
): Promise<BankAccount> {
	return apiJson(`/api/v1/accounts/${id}`, { method: 'PATCH', body: JSON.stringify(input) });
}

export function deleteAccount(id: number): Promise<void> {
	return apiJson(`/api/v1/accounts/${id}`, { method: 'DELETE' });
}
