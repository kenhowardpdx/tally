export type RecurrenceType =
	| 'weekly'
	| 'biweekly'
	| 'semimonthly'
	| 'monthly'
	| 'annually'
	| 'custom_days';

export interface BankAccount {
	id: number;
	name: string;
	institution: string | null;
	created_at: string;
}

export interface BankAccountInput {
	name: string;
	institution?: string | null;
}

export interface Bill {
	id: number;
	account_id: number;
	name: string;
	amount_cents: number;
	recurrence_type: RecurrenceType;
	recurrence_config: Record<string, unknown>;
	start_date: string;
	end_date: string | null;
	enabled: boolean;
	created_at: string;
	updated_at: string;
}

export interface BillInput {
	name: string;
	amount_cents: number;
	recurrence_type: RecurrenceType;
	recurrence_config?: Record<string, unknown>;
	start_date: string;
	end_date?: string | null;
	enabled?: boolean;
}
