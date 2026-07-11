# Tally Frontend

A [SvelteKit](https://svelte.dev/docs/kit) (Svelte 5) app that manages bank accounts and bills,
and (eventually) renders the cash-flow forecast. Deployed as a static SPA to S3/CloudFront in
prod (see `infra/modules/frontend_s3`); talks to the backend API and to Auth0 directly from the
browser.

## Getting Started

Requires Node >=20.19 (or >=22.12, or >=24) — check with `node -v`; `.nvmrc` floats to the
current LTS, so `nvm install` picks up a compatible version.

```bash
cp .env.example .env   # fill in PUBLIC_AUTH0_* from your Auth0 SPA application, and add
                        # http://localhost:5173 as an Allowed Callback/Logout/Web Origin URL
                        # in that application's settings
yarn install
yarn dev
```

The backend must be running separately (see `backend/README.md`, or `docker compose up` from
the repo root to run everything together) — `PUBLIC_API_BASE_URL` in `.env` points at it.

## Type Checking

```bash
yarn run check
```

(`yarn check` runs Yarn's own built-in command, not the `check` script — use `yarn run check`.)

## Building

```bash
yarn build
```

Produces a static export via `@sveltejs/adapter-static` (`fallback: 'index.html'`, full
client-side routing) into `build/`. Preview it locally with `yarn preview`.
