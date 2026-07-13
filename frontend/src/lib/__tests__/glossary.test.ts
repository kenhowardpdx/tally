import { describe, expect, it } from 'vitest';
import { glossaryTerms } from '../glossary';

describe('glossaryTerms', () => {
	it('has no duplicate or empty terms/definitions', () => {
		const terms = glossaryTerms.map((t) => t.term);
		expect(new Set(terms).size).toBe(terms.length);

		for (const { term, definition } of glossaryTerms) {
			expect(term.trim().length).toBeGreaterThan(0);
			expect(definition.trim().length).toBeGreaterThan(0);
		}
	});

	it('defines the terms surfaced as inline field tooltips', () => {
		// Tooltip.svelte call sites look these up by exact term string
		// (glossaryTerms.find(...)!.definition) - a rename here without
		// updating those call sites would fail at runtime with a null
		// dereference, so pin the terms that must keep existing.
		const terms = new Set(glossaryTerms.map((t) => t.term));
		expect(terms.has('Frequency')).toBe(true);
		expect(terms.has('Cycle type')).toBe(true);
		expect(terms.has('Windfall')).toBe(true);
	});
});
