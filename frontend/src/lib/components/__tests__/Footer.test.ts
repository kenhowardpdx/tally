import { render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Footer from '../Footer.svelte';

describe('Footer', () => {
	it('shows the current year in the copyright line', () => {
		render(Footer);
		const year = new Date().getFullYear().toString();
		expect(screen.getByText(new RegExp(`© ${year} Tally`))).toBeInTheDocument();
	});

	it('links to the privacy and terms pages', () => {
		render(Footer);
		expect(screen.getByRole('link', { name: 'Privacy Policy' })).toHaveAttribute('href', '/privacy');
		expect(screen.getByRole('link', { name: 'Terms and Conditions' })).toHaveAttribute(
			'href',
			'/terms'
		);
	});
});
