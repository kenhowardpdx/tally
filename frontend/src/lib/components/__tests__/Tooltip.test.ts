import { render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Tooltip from '../Tooltip.svelte';

describe('Tooltip', () => {
	it('links the trigger to its tooltip text via aria-describedby', () => {
		render(Tooltip, { text: 'Explains a thing' });

		const trigger = screen.getByRole('button');
		const describedBy = trigger.getAttribute('aria-describedby');
		expect(describedBy).toBeTruthy();

		const tooltip = document.getElementById(describedBy!);
		expect(tooltip).not.toBeNull();
		expect(tooltip).toHaveTextContent('Explains a thing');
	});

	it('is reachable by keyboard (a real focusable button, not a hover-only div)', async () => {
		render(Tooltip, { text: 'Keyboard accessible' });

		const trigger = screen.getByRole('button');
		expect(trigger.tagName).toBe('BUTTON');

		trigger.focus();
		expect(trigger).toHaveFocus();
	});

	it('generates a stable id when none is provided, and honors an explicit one', () => {
		const { unmount } = render(Tooltip, { text: 'One' });
		const firstId = screen.getByRole('button').getAttribute('aria-describedby');
		unmount();

		render(Tooltip, { text: 'Two', id: 'custom-tip-id' });
		const secondButton = screen.getByRole('button');
		expect(secondButton.getAttribute('aria-describedby')).toBe('custom-tip-id');
		expect(firstId).not.toBe('custom-tip-id');
	});
});
