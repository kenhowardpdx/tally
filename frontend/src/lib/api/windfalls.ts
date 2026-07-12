import { apiJson } from '$lib/api';
import type { Windfall, WindfallInput } from '$lib/api/types';

export function listWindfalls(accountId: number): Promise<Windfall[]> {
	return apiJson(`/api/v1/accounts/${accountId}/windfalls`);
}

export function createWindfall(accountId: number, input: WindfallInput): Promise<Windfall> {
	return apiJson(`/api/v1/accounts/${accountId}/windfalls`, {
		method: 'POST',
		body: JSON.stringify(input)
	});
}

export function deleteWindfall(accountId: number, windfallId: number): Promise<void> {
	return apiJson(`/api/v1/accounts/${accountId}/windfalls/${windfallId}`, {
		method: 'DELETE'
	});
}
