import { apiJson } from '$lib/api';
import type { CycleOverride, CycleOverrideInput } from '$lib/api/types';

export function upsertCycleOverride(input: CycleOverrideInput): Promise<CycleOverride> {
	return apiJson(`/api/v1/cycle-overrides`, {
		method: 'PUT',
		body: JSON.stringify(input)
	});
}

export function listCycleOverrides(
	accountId: number,
	cycleStart: string
): Promise<CycleOverride[]> {
	return apiJson(
		`/api/v1/accounts/${accountId}/cycle-overrides?cycle_start=${encodeURIComponent(cycleStart)}`
	);
}
