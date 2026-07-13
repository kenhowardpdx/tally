import { apiJson } from '$lib/api';
import type { DashboardResponse } from '$lib/api/types';

export function getDashboard(): Promise<DashboardResponse> {
	return apiJson('/api/v1/dashboard');
}
