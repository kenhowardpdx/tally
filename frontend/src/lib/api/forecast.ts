import { apiJson } from '$lib/api';
import type { ForecastRequest, ForecastResponse } from '$lib/api/types';

export function computeForecast(
	accountId: number,
	input: ForecastRequest
): Promise<ForecastResponse> {
	return apiJson(`/api/v1/accounts/${accountId}/forecast`, {
		method: 'POST',
		body: JSON.stringify(input)
	});
}
