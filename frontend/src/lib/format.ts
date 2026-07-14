import type { BankAccount } from '$lib/api/types';

// Returns e.g. " (Checking - Chase)", built as a single expression rather
// than static template text so the leading/interstitial spaces survive -
// Svelte trims whitespace that sits as the first/last child of a block.
export function accountSuffix(account: BankAccount | null): string {
	if (!account) return '';
	return ` (${account.name}${account.institution ? ` - ${account.institution}` : ''})`;
}
