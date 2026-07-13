import type { BillEvent, BillEventType, RecurrenceType } from '$lib/api/types';
import { recurrenceLabels } from '$lib/recurrence';

export const billEventLabels: Record<BillEventType, string> = {
	created: 'Bill created',
	updated: 'Bill updated',
	notes_changed: 'Notes changed',
	enabled: 'Bill enabled',
	disabled: 'Bill disabled',
	cycle_marked_paid: 'Marked paid',
	cycle_marked_unpaid: 'Marked unpaid',
	cycle_amount_changed: 'Cycle amount changed',
	cycle_notes_changed: 'Cycle notes changed'
};

const fieldLabels: Record<string, string> = {
	name: 'Name',
	amount_cents: 'Amount',
	recurrence_type: 'Frequency',
	recurrence_config: 'Recurrence details',
	start_date: 'Start date',
	end_date: 'End date',
	account_id: 'Account',
	notes: 'Notes',
	override_amount_cents: 'Cycle amount'
};

const AMOUNT_FIELDS = new Set(['amount_cents', 'override_amount_cents']);

function formatFieldValue(field: string, value: unknown, formatAmount: (cents: number) => string): string {
	if (value === null || value === undefined) return 'none';
	if (AMOUNT_FIELDS.has(field)) return formatAmount(value as number);
	if (field === 'recurrence_type') return recurrenceLabels[value as RecurrenceType] ?? String(value);
	if (field === 'recurrence_config') return JSON.stringify(value);
	return String(value);
}

/** A single-line summary plus zero or more "field: old → new" detail lines,
 * suitable for a timeline entry. `created` events (a flat value snapshot,
 * not old/new pairs) get a compact one-line summary instead of a diff. */
export function describeBillEvent(
	event: BillEvent,
	formatAmount: (cents: number) => string
): { label: string; details: string[] } {
	const label = billEventLabels[event.event_type];
	const changes = event.changes ?? {};

	if (event.event_type === 'created') {
		const name = changes.name as string | undefined;
		const amount = changes.amount_cents as number | undefined;
		const recurrence = changes.recurrence_type as RecurrenceType | undefined;
		const parts = [
			name,
			amount != null ? formatAmount(amount) : null,
			recurrence ? recurrenceLabels[recurrence] : null
		].filter((part): part is string => Boolean(part));
		return { label, details: parts.length ? [parts.join(' · ')] : [] };
	}

	const details = Object.entries(changes).map(([field, value]) => {
		const { old: oldValue, new: newValue } = value as { old: unknown; new: unknown };
		const fieldLabel = fieldLabels[field] ?? field;
		return `${fieldLabel}: ${formatFieldValue(field, oldValue, formatAmount)} → ${formatFieldValue(field, newValue, formatAmount)}`;
	});
	return { label, details };
}
