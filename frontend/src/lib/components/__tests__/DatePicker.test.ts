import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import DatePicker from '../DatePicker.svelte';

// The trigger's accessible name comes from its associated <label>
// ("Start date"), not its visible value text - same reasoning as Select's
// getTrigger() helper.
function getTrigger() {
	return screen.getByRole('button', { name: 'Start date' });
}

describe('DatePicker', () => {
	it('shows a placeholder until a value is set', () => {
		render(DatePicker, { label: 'Start date', value: '' });
		expect(getTrigger()).toHaveTextContent('Select date');
	});

	it('opens a calendar dialog showing the selected date highlighted', async () => {
		render(DatePicker, { label: 'Start date', value: '2024-06-15' });

		await fireEvent.click(getTrigger());

		expect(screen.getByRole('dialog', { name: 'Choose date' })).toBeInTheDocument();
		expect(screen.getByText('June 2024')).toBeInTheDocument();
		expect(screen.getByRole('button', { name: '15' }).className).toContain('bg-primary');
	});

	it('picking a day updates the bound value and closes the calendar', async () => {
		render(DatePicker, { label: 'Start date', value: '2024-06-15' });

		await fireEvent.click(getTrigger());
		await fireEvent.click(screen.getByRole('button', { name: '20' }));

		expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
		expect(getTrigger()).toHaveTextContent('2024-06-20');
	});

	it('closes on Escape without changing the value', async () => {
		render(DatePicker, { label: 'Start date', value: '2024-06-15' });

		await fireEvent.click(getTrigger());
		await fireEvent.keyDown(window, { key: 'Escape' });

		expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
		expect(getTrigger()).toHaveTextContent('2024-06-15');
	});

	it('right-anchors the popover when the trigger sits right of the viewport midpoint', async () => {
		render(DatePicker, { label: 'Start date', value: '2024-06-15' });
		const trigger = getTrigger();

		// jsdom lays out everything at (0,0) with zero size by default, so
		// getBoundingClientRect has to be stubbed directly - this is testing
		// DatePicker's edge-detection branch, not real browser layout (that's
		// covered by the manual/browser verification for 4.2's overflow fix).
		trigger.getBoundingClientRect = () =>
			({ left: 900, right: 950, top: 0, bottom: 0, width: 50, height: 30 }) as DOMRect;
		Object.defineProperty(window, 'innerWidth', { value: 1000, configurable: true });

		await fireEvent.click(trigger);

		const dialog = screen.getByRole('dialog', { name: 'Choose date' });
		expect(dialog.className).toContain('right-0');
		expect(dialog.className).not.toContain('left-0');
	});
});
