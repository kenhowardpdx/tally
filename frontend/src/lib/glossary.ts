export interface GlossaryTerm {
	term: string;
	definition: string;
}

// Shared source of truth for both the /glossary page and inline field
// tooltips (Tooltip.svelte) - a short version of each definition is reused
// as tooltip text so the two never drift apart.
export const glossaryTerms: GlossaryTerm[] = [
	{
		term: 'Frequency',
		definition:
			"How often a bill recurs: weekly, biweekly (every 2 weeks), semimonthly (the 10th & 25th of each month), monthly, annually, or a custom number of days between occurrences. This is a property of the bill itself, independent of your pay cycle."
	},
	{
		term: 'Cycle type',
		definition:
			'The pay-cycle cadence a forecast is calculated against - weekly, biweekly, monthly, or semimonthly. Distinct from a bill\'s own frequency: a monthly bill can still fall inside a biweekly forecast cycle, possibly recurring in more than one cycle.'
	},
	{
		term: 'Semimonthly (10th & 25th)',
		definition:
			"A cycle or bill that recurs twice a month, anchored to fixed calendar boundaries - the 1st-9th, 10th-24th, and 25th-end-of-month. Unlike other cycle types, semimonthly boundaries don't shift based on when you started forecasting."
	},
	{
		term: 'Windfall',
		definition:
			'A one-time or irregular expected deposit - a bonus, tax refund, or gift - that adds to a forecast cycle\'s balance on a specific expected date. Unlike a bill, a windfall is always a credit, never an expense.'
	},
	{
		term: 'Transaction',
		definition:
			'A one-off entry in a forecast cycle that is neither a recurring bill nor a windfall - can be a credit or a debit (e.g. a refund or an unplanned purchase), entered once rather than on a recurring schedule.'
	},
	{
		term: 'Starting balance',
		definition:
			"The bank balance you expect to have on a forecast's start date - the baseline every later cycle's running balance is calculated forward from."
	},
	{
		term: 'Income per cycle',
		definition:
			'A flat amount added to the running balance at the start of every forecast cycle - for regular paycheck income that repeats every cycle, separate from one-off windfalls.'
	},
	{
		term: 'Cycle reconciliation',
		definition:
			"Marking a bill or windfall paid/received for a specific cycle, and optionally recording its actual amount if it differs from the usual one (e.g. a seasonal utility bill). This never changes the bill's or windfall's normal amount - only that one cycle's record."
	},
	{
		term: 'Bill history',
		definition:
			"A cycle-by-cycle log of a single bill's expected vs. actual amounts, completion, and notes over time - useful for spotting bills that consistently run over their usual amount."
	},
	{
		term: 'One-time bill',
		definition:
			'A bill whose start date and end date are the same day only ever occurs once - functionally identical to a one-off Transaction, but modeled as a recurring Bill. Consider deleting it and recording the expense as a Transaction instead, since Bills are meant for things that repeat.'
	},
	{
		term: 'Ended bill',
		definition:
			"A bill whose end date has passed - it no longer applies to any forecast cycle. Tally automatically disables it so it's easy to review and delete during cleanup, rather than leaving it enabled but functionally dead."
	}
];
