import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import {
	PUBLIC_AUTH0_AUDIENCE,
	PUBLIC_AUTH0_CLIENT_ID,
	PUBLIC_AUTH0_DOMAIN
} from '$env/static/public';
import { Auth0Client, type User } from '@auth0/auth0-spa-js';
import { writable } from 'svelte/store';

export const isAuthenticated = writable(false);
export const isLoading = writable(true);
export const user = writable<User | undefined>(undefined);

let client: Auth0Client | undefined;

function getClient(): Auth0Client {
	if (!client) {
		client = new Auth0Client({
			domain: PUBLIC_AUTH0_DOMAIN,
			clientId: PUBLIC_AUTH0_CLIENT_ID,
			authorizationParams: {
				redirect_uri: window.location.origin,
				audience: PUBLIC_AUTH0_AUDIENCE
			}
		});
	}
	return client;
}

// Call once from the root layout's onMount. Handles the redirect-callback
// query params Auth0 appends after login, since there's no server to do it
// (this app is a static SPA — see svelte.config.js's adapter-static).
export async function initAuth(): Promise<void> {
	if (!browser) return;

	const auth0 = getClient();
	const params = new URLSearchParams(window.location.search);

	if (params.has('code') && params.has('state')) {
		const { appState } = await auth0.handleRedirectCallback();
		window.history.replaceState({}, document.title, window.location.pathname);
		if (appState?.redirectTo) await goto(appState.redirectTo);
	}

	const authenticated = await auth0.isAuthenticated();
	isAuthenticated.set(authenticated);
	user.set(authenticated ? await auth0.getUser() : undefined);
	isLoading.set(false);
}

export async function login(redirectTo = window.location.pathname): Promise<void> {
	await getClient().loginWithRedirect({
		authorizationParams: { redirect_uri: window.location.origin },
		appState: { redirectTo }
	});
}

export async function logout(): Promise<void> {
	await getClient().logout({ logoutParams: { returnTo: window.location.origin } });
}

export async function getAccessToken(): Promise<string> {
	return getClient().getTokenSilently();
}
