import type { CycleType } from '$lib/api/types';

export const cycleTypeLabels: Record<CycleType, string> = {
	weekly: 'Weekly',
	biweekly: 'Biweekly',
	monthly: 'Monthly',
	semimonthly: 'Semimonthly (10th & 25th)'
};
