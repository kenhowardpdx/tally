import { apiJson } from '$lib/api';
import type { ConsentStatus } from '$lib/api/types';

export function getConsentStatus(): Promise<ConsentStatus> {
	return apiJson('/api/v1/me/consent');
}

export function acceptConsent(): Promise<ConsentStatus> {
	return apiJson('/api/v1/me/consent', { method: 'POST' });
}
