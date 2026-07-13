import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Select from '../Select.svelte';

const options = [
	{ value: 'weekly', label: 'Weekly' },
	{ value: 'semimonthly', label: 'Semimonthly (10th & 25th)' }
];

// The trigger's accessible name comes from its associated <label>
// ("Frequency"), not its visible value text - the label/for association
// takes precedence over content in the accessible-name algorithm.
function getTrigger() {
	return screen.getByRole('button', { name: 'Frequency' });
}

describe('Select', () => {
	it('shows a placeholder when nothing is selected, and the matching label once a value is bound', async () => {
		const { rerender } = render(Select, { label: 'Frequency', value: '', options });
		expect(getTrigger()).toHaveTextContent('Select…');

		await rerender({ label: 'Frequency', value: 'semimonthly', options });
		expect(getTrigger()).toHaveTextContent('Semimonthly (10th & 25th)');
	});

	it('opens a listbox of options on click, each rendering its label', async () => {
		render(Select, { label: 'Frequency', value: 'weekly', options });

		await fireEvent.click(getTrigger());

		expect(screen.getByRole('listbox')).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Weekly' })).toHaveAttribute('aria-selected', 'true');
		expect(screen.getByRole('option', { name: 'Semimonthly (10th & 25th)' })).toHaveAttribute(
			'aria-selected',
			'false'
		);
	});

	it('picking an option updates the trigger and closes the listbox', async () => {
		render(Select, { label: 'Frequency', value: 'weekly', options });

		await fireEvent.click(getTrigger());
		await fireEvent.click(screen.getByRole('option', { name: 'Semimonthly (10th & 25th)' }));

		expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
		expect(getTrigger()).toHaveTextContent('Semimonthly (10th & 25th)');
	});

	it('closes the listbox on Escape without changing the selected value', async () => {
		render(Select, { label: 'Frequency', value: 'weekly', options });

		await fireEvent.click(getTrigger());
		expect(screen.getByRole('listbox')).toBeInTheDocument();

		await fireEvent.keyDown(window, { key: 'Escape' });
		expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
		expect(getTrigger()).toHaveTextContent('Weekly');
	});

	it('renders an optional tooltip next to the label', () => {
		render(Select, { label: 'Frequency', value: 'weekly', options, tooltip: 'What is this?' });
		expect(screen.getByRole('button', { name: '?' })).toBeInTheDocument();
	});
});
