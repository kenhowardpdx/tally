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
	notes: string | null;
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
	notes?: string | null;
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
	// The amount actually used in the running balance - the cycle override's
	// amount if one is set, else the same as forecasted_amount_cents.
	amount_cents: number;
	// The bill's own configured amount, regardless of any override.
	forecasted_amount_cents: number;
	due_date: string;
	completed: boolean;
	notes: string | null;
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
	forecasted_amount_cents: number;
	expected_date: string;
	completed: boolean;
	notes: string | null;
}

export interface CycleOverrideInput {
	account_id: number;
	bill_id?: number | null;
	windfall_id?: number | null;
	cycle_start_date: string;
	completed: boolean;
	override_amount_cents?: number | null;
	notes?: string | null;
}

export interface BillHistoryEntry {
	cycle_start_date: string;
	cycle_end_date: string;
	due_date: string;
	expected_amount_cents: number;
	actual_amount_cents: number;
	completed: boolean;
	notes: string | null;
	variance_cents: number;
}

// Append-only audit trail, distinct from BillHistoryEntry above (which is
// forecasted-vs-actual per cycle, derived from cycle_overrides state, not a
// change log). cycle_start_date/changes' shape both vary by event_type:
// - created: changes is a flat {field: value} snapshot, cycle_start_date null
// - updated: changes is {field: {old, new}} for whichever fields changed,
//   cycle_start_date null
// - notes_changed: changes is {notes: {old, new}}, cycle_start_date null
// - enabled / disabled: changes null, cycle_start_date null
// - cycle_marked_paid / cycle_marked_unpaid: changes null, cycle_start_date set
// - cycle_amount_changed: changes is {override_amount_cents: {old, new}}, cycle_start_date set
// - cycle_notes_changed: changes is {notes: {old, new}}, cycle_start_date set
export type BillEventType =
	| 'created'
	| 'updated'
	| 'notes_changed'
	| 'enabled'
	| 'disabled'
	| 'cycle_marked_paid'
	| 'cycle_marked_unpaid'
	| 'cycle_amount_changed'
	| 'cycle_notes_changed';

export interface BillEvent {
	id: number;
	bill_id: number;
	event_type: BillEventType;
	cycle_start_date: string | null;
	changes: Record<string, unknown> | null;
	created_at: string;
}

export interface BillEventListResponse {
	bill_id: number;
	total: number;
	events: BillEvent[];
}

export interface BillEventCycleCount {
	cycle_start_date: string;
	count: number;
}

export interface BillEventCycleCountsResponse {
	bill_id: number;
	counts: BillEventCycleCount[];
}

export interface BillHistoryResponse {
	bill_id: number;
	total: number;
	entries: BillHistoryEntry[];
}

export interface CycleOverride {
	id: number;
	account_id: number;
	bill_id: number | null;
	windfall_id: number | null;
	cycle_start_date: string;
	completed: boolean;
	override_amount_cents: number | null;
	notes: string | null;
	created_at: string;
	updated_at: string;
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

export interface DashboardAccountSummary {
	account_id: number;
	account_name: string;
	institution: string | null;
	// False if the account has never had a forecast run - every field below
	// is null/empty in that case.
	configured: boolean;
	cycle_type: CycleType | null;
	cycle_start_date: string | null;
	cycle_end_date: string | null;
	// True if today is before the account's saved forecast_start_date - this
	// is the first upcoming cycle, not one actually in progress.
	is_upcoming: boolean;
	starting_balance_cents: number | null;
	ending_balance_cents: number | null;
	bills: ForecastBillLine[];
	transactions: ForecastTransactionLine[];
	windfalls: ForecastWindfallLine[];
	net_cents: number | null;
}

export interface DashboardResponse {
	accounts: DashboardAccountSummary[];
	combined_ending_balance_cents: number;
}

export interface DemoBill {
	id: number;
	name: string;
	amount_cents: number;
	recurrence_type: RecurrenceType;
	recurrence_config?: Record<string, unknown>;
	start_date: string;
	end_date?: string | null;
}

export interface DemoForecastRequest {
	bills: DemoBill[];
	cycle_type: CycleType;
	start_date: string;
	end_date: string;
	starting_balance_cents: number;
	income_per_cycle_cents: number;
}

export interface ConsentStatus {
	terms_accepted: boolean;
	terms_accepted_at: string | null;
}
