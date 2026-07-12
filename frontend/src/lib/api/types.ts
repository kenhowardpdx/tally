export type RecurrenceType =
	| 'weekly'
	| 'biweekly'
	| 'semimonthly'
	| 'monthly'
	| 'annually'
	| 'custom_days';

// Pay-period cadence for forecasting - distinct from RecurrenceType (how
// often a given bill recurs). Not persisted independently; lives only as
// the account's last-used forecast setting (see BankAccount.forecast_*).
export type CycleType = 'weekly' | 'biweekly' | 'monthly' | 'semimonthly';

export interface BankAccount {
	id: number;
	name: string;
	institution: string | null;
	created_at: string;
	forecast_starting_balance_cents: number | null;
	forecast_income_per_cycle_cents: number | null;
	forecast_cycle_type: CycleType | null;
	forecast_start_date: string | null;
	forecast_end_date: string | null;
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

export interface Transaction {
	id: number;
	account_id: number;
	bill_id: number | null;
	// Signed: positive credits the balance, negative debits it.
	amount_cents: number;
	date: string;
	description: string | null;
	created_at: string;
}

export interface TransactionInput {
	amount_cents: number;
	date: string;
	description?: string | null;
	bill_id?: number | null;
}

export interface Windfall {
	id: number;
	account_id: number;
	name: string;
	// Always positive - a windfall is income by definition.
	amount_cents: number;
	expected_date: string;
	created_at: string;
}

export interface WindfallInput {
	name: string;
	amount_cents: number;
	expected_date: string;
}

export interface ForecastRequest {
	start_date: string;
	end_date: string;
	starting_balance_cents: number;
	income_per_cycle_cents: number;
	cycle_type: CycleType;
}

export interface ForecastBillLine {
	bill_id: number;
	name: string;
	amount_cents: number;
	due_date: string;
}

export interface ForecastTransactionLine {
	transaction_id: number;
	amount_cents: number;
	date: string;
	description: string | null;
}

export interface ForecastWindfallLine {
	windfall_id: number;
	name: string;
	amount_cents: number;
	expected_date: string;
}

export interface ForecastCycle {
	start_date: string;
	end_date: string;
	bills: ForecastBillLine[];
	transactions: ForecastTransactionLine[];
	windfalls: ForecastWindfallLine[];
	net_cents: number;
	running_balance_cents: number;
}

export interface UnscheduledBill {
	bill_id: number;
	name: string;
	reason: string;
}

export interface ForecastResponse {
	cycles: ForecastCycle[];
	starting_balance_cents: number;
	ending_balance_cents: number;
	unscheduled_bills: UnscheduledBill[];
}
