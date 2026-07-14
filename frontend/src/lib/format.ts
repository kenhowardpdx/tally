import type { BankAccount } from '$lib/api/types';

// Returns e.g. " (Checking - Chase)", built as a single expression rather
// than static template text so the leading/interstitial spaces survive -
// Svelte trims whitespace that sits as the first/last child of a block.
export function accountSuffix(account: BankAccount | null): string {
	if (!account) return '';
	return ` (${account.name}${account.institution ? ` - ${account.institution}` : ''})`;
}

// Local date components, not toISOString() (which formats in UTC and can
// shift the day relative to the user's local time).
export function todayIso(): string {
	const now = new Date();
	const year = now.getFullYear();
	const month = String(now.getMonth() + 1).padStart(2, '0');
	const day = String(now.getDate()).padStart(2, '0');
	return `${year}-${month}-${day}`;
}
