import type { RecurrenceType } from '$lib/api/types';

export const recurrenceLabels: Record<RecurrenceType, string> = {
	weekly: 'Weekly',
	biweekly: 'Biweekly',
	semimonthly: 'Semimonthly',
	monthly: 'Monthly',
	annually: 'Annually',
	custom_days: 'Custom (days)'
};
