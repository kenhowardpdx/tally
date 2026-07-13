import { render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Badge from '../Badge.svelte';

describe('Badge', () => {
	it('renders "Enabled" when enabled is true', () => {
		render(Badge, { enabled: true });
		expect(screen.getByText('Enabled')).toBeInTheDocument();
		expect(screen.queryByText('Disabled')).not.toBeInTheDocument();
	});

	it('renders "Disabled" when enabled is false', () => {
		render(Badge, { enabled: false });
		expect(screen.getByText('Disabled')).toBeInTheDocument();
		expect(screen.queryByText('Enabled')).not.toBeInTheDocument();
	});
});
