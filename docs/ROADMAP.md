# Tally Roadmap

This is the living plan for building out Tally into a full bill-tracking and cash-flow
forecasting app. It's written to survive long gaps between sessions (~6 weeks apart,
~3 hours per session) — read this file first in any new session to see what's done and
what's next. Check off items as they land, and update the "Status" line at the top of
each phase.

This roadmap is now the planning source of truth. The original GitHub Project / bootstrap
issue set can be closed once each item is either reflected here, marked shipped, or called out
as superseded by the architecture decisions below.

## Vision

A multi-user bill-tracking and forecasting app, evolved from
[kenhowardpdx/bank](https://github.com/kenhowardpdx/bank) with:

1. Real authentication (Auth0)
2. Multiple bank accounts per user
3. Postgres (Neon) instead of local storage
4. A better UI, built in Svelte instead of React
5. Enable/disable control on individual bills
6. Finer-grained due-date interval control than "day of month" or "annual"
7. Ability to add one-off transactions within the current cycle
8. Ability to forecast a future windfall (bonus, tax refund, etc.)
9. Human-readable CSV import/export of all bills for a bank account, editable in Excel
   or Numbers, with amounts formatted in the account/user-selected currency (default
   USD)

## What to reuse from `kenhowardpdx/bank`

The reference repo (cloned for research, not vendored) has real substance worth
porting rather than re-deriving from scratch:

- **`packages/forecast`** — a mature, tested cycle/due-date engine (`Bill`, `Cycle`,
  `Amount`, `getForecast`). Supports bi-weekly, monthly, semi-monthly ("10th & 25th"),
  and annual bills; computes which bills fall in a pay cycle and a running balance.
  Port the *logic*, not the code as-is — see Architecture Decisions below for the two
  changes to make while porting.
- **`apps/clientv0`** — the older, local-storage React UI (`Bills.tsx`, `Forecast.tsx`,
  `BillRow.tsx`). Not the codebase to reuse, but the *UX* is proven: an editable bill
  table, and a forecast table of pay-cycle rows (date range → running total, expandable
  to show which bills hit that cycle). Good starting point for the Svelte equivalent.
- **`apps/server` + `apps/client`** — a newer, partially-migrated Postgres + Auth0
  version. The migration to this architecture was never finished (bills CRUD/forecast
  UI never got ported over), but `AuthProvider.tsx` shows the working Auth0 SPA
  integration pattern, and `init.sql` shows a first-pass schema — both reference points
  for Tally's equivalents, not something to copy directly (Tally's schema goes further
  per the data model below).

## Architecture decisions

- **Data layer**: SQLAlchemy (async, via `asyncpg`) + Alembic migrations. More setup
  than raw SQL, but the schema lives in Python and migrations autogenerate — worth it
  across 6-week gaps where re-deriving the schema from scratch `.sql` files would cost
  real time.
- **Money**: integer cents (`amount_cents`, `BigInteger`) in Postgres, `Decimal` in
  Python — never float. The reference app's `Amount` class uses `parseFloat` on
  currency strings, a real precision bug worth not repeating. For UI and CSV
  import/export, format and parse amounts using the selected display currency
  (default USD) while persisting normalized cents.
- **Recurrence model**: an extended enum (`weekly`, `biweekly`, `semimonthly`,
  `monthly`, `annually`, `custom_days`) plus a small JSONB `recurrence_config` column
  for the type-specific bits (weekday, day-of-month, interval-in-days, etc.). Covers
  real-world bills without taking on full iCal RRULE complexity.
- **Auth**: Auth0. Backend validates JWTs via a FastAPI dependency (JWKS-based
  signature check, no session state). Frontend uses Auth0's SPA pattern (same shape as
  the reference app's `AuthProvider.tsx`, adapted for SvelteKit).
- **Local dev**: docker-compose Postgres for local development; Neon for prod (already
  provisioned — `TF_VAR_neon_org_id`/`NEON_API_KEY` exist in `.secrets`, but the actual
  database/schema isn't Terraform-managed yet, just manually created. Formalizing that
  is a Phase 0 task, not required before it).

## Data model

Implemented in `backend/src/models/` (SQLAlchemy 2.0, `Mapped`/`mapped_column` style) and
codified in the Alembic migration at `backend/alembic/versions/9f979f5fb842_initial_schema.py`.

```mermaid
erDiagram
    USERS ||--o{ BANK_ACCOUNTS : owns
    BANK_ACCOUNTS ||--o{ BILLS : has
    BANK_ACCOUNTS ||--o{ TRANSACTIONS : has
    BANK_ACCOUNTS ||--o{ WINDFALLS : has
    BILLS ||--o{ TRANSACTIONS : "generates (optional)"

    USERS {
        int id PK
        string auth0_sub
        string email
        datetime created_at
    }
    BANK_ACCOUNTS {
        int id PK
        int user_id FK
        string name
        string institution
        datetime created_at
    }
    BILLS {
        int id PK
        int account_id FK
        string name
        bigint amount_cents
        enum recurrence_type
        jsonb recurrence_config
        date start_date
        date end_date
        bool enabled
        datetime created_at
        datetime updated_at
    }
    TRANSACTIONS {
        int id PK
        int account_id FK
        int bill_id FK "nullable"
        bigint amount_cents
        date date
        string description
        datetime created_at
    }
    WINDFALLS {
        int id PK
        int account_id FK
        bigint amount_cents
        date expected_date
        string name
        datetime created_at
    }
```

Maps directly to the 8 differences: `users.auth0_sub` → auth; `bank_accounts` → multi-account;
whole schema → Postgres; `bills.enabled` → enable/disable; `recurrence_type`/`recurrence_config`
→ finer intervals; `transactions` → one-off entries; `windfalls` → future windfalls.

`recurrence_type` is a Postgres enum (`weekly`, `biweekly`, `semimonthly`, `monthly`, `annually`,
`custom_days`); `recurrence_config` holds the type-specific shape (e.g. `{"day_of_month": 15}`,
`{"days": [10, 25]}` for semimonthly, `{"interval_days": 45}` for custom_days) — validated by the
forecast engine in Phase 2, not by a DB constraint.

### Neon: manual vs. Terraform-managed (Phase 0.2 decision)

**Decision: keep the Neon project/database manual for now.** The connection strings already flow
into the Lambda's environment via `TF_VAR_database_url_readwrite`/`readonly` (see
`infra/variables.tf`), and Alembic now owns schema evolution independently of Terraform — so
bringing Neon itself under the Terraform Neon provider would manage project/branch creation but
wouldn't simplify anything currently painful. Revisit if/when multiple environments (e.g. a
per-PR preview branch) make manual Neon console clicks a recurring chore.

---

## Phase 0 — Foundations

**Status**: code complete

- [x] 0.1 Finalize data model (turn the sketch above into real SQLAlchemy models + an ER
      diagram in this doc)
- [x] 0.2 Alembic setup + initial migration creating all tables; formalize the Neon
      database connection (confirm whether to bring it under Terraform via the Neon
      provider, or keep it manual — decide and document here)
- [x] 0.3 Local dev: docker-compose Postgres for backend dev, `.env` pattern mirroring
      prod's Neon connection shape
- [x] 0.4 Backend JWT validation dependency (`get_current_user`, `backend/src/core/auth.py`)
      + protected test endpoint (`GET /api/v1/me`), tested against a locally-signed RSA
      token so it doesn't depend on a real tenant existing yet. Auth0 tenant + API created;
      `AUTH0_DOMAIN`/`AUTH0_AUDIENCE` filled in `backend/.env` (see `backend/.env.example`).
- [x] 0.5 Auth0 frontend integration in SvelteKit (`frontend/src/lib/auth.ts`):
      login/logout, protected route pattern (`frontend/src/routes/(app)/+layout.svelte`),
      token attached to API calls (`frontend/src/lib/api.ts`). `PUBLIC_AUTH0_DOMAIN`/
      `PUBLIC_AUTH0_CLIENT_ID`/`PUBLIC_AUTH0_AUDIENCE` filled in `frontend/.env` (see
      `frontend/.env.example`), and the dev URL (`http://localhost:5173`) added as an
      Allowed Callback/Logout/Web Origin URL in the Auth0 SPA application settings.

## Phase 1 — Accounts & Bills CRUD

**Status**: code complete; follow-up items below (1.7-1.8)

- [x] 1.1 Backend: `bank_accounts` CRUD API, scoped to the authenticated user
- [x] 1.2 Backend: `bills` CRUD API, scoped to an account, including the enable/disable
      toggle
- [x] 1.3 Frontend: accounts list/management page
- [x] 1.4 Frontend: bills list/management page per account (Svelte equivalent of
      `clientv0`'s `Bills.tsx` editable table UX)
- [x] 1.5 Bills page header always reads "Bills" regardless of which account you're on —
      should read `Bills (<Name> - <Bank>)`. Backend already exposes
      `GET /api/v1/accounts/{id}`; frontend just needs a `getAccount` call added to
      `frontend/src/lib/api/accounts.ts` and used in
      `frontend/src/routes/(app)/accounts/[id]/+page.svelte`.
- [x] 1.6 Move a bill to a different bank account. Backend: extend `BillUpdate`/
      `PATCH .../bills/{id}` (`backend/src/schemas/bill.py`, `backend/src/api/bills.py`) to
      accept a target `account_id`, verifying the target account also belongs to the
      current user (same ownership check pattern as `get_owned_bank_account`). Frontend: an
      pop-up modal where the user can select an account to move the bill to; once applied
      the bills list is updated to show the current list of bills sans the bill that was
      moved.
- [ ] 1.7 Recurrence-specific config UI for the bill form — **not yet designed, scope
      before starting**. Today `createBill` never sends `recurrence_config`
      (`frontend/src/routes/(app)/accounts/[id]/+page.svelte`), so every bill gets created
      with an empty `{}` regardless of type, even though the model needs type-specific data:
      `{"interval_days": N}` (custom_days), `{"days": [10, 25]}` (semimonthly),
      `{"day_of_month": N}` (monthly), and likely a weekday (weekly/biweekly) or month+day
      (annually). Needs per-type conditional form fields on both create and edit. Blocks
      exercising Phase 2's forecast engine end-to-end against real user-created bills of
      non-trivial recurrence types.
- [ ] 1.8 Bills CSV import/export per bank account. Backend: add account-scoped export and
      import endpoints for the full bills list, with validation/error reporting granular
      enough for a user-edited CSV. Frontend: add import/export actions on the bills page
      for the current account, with a downloadable template/example. CSV should stay
human-readable and spreadsheet-friendly (Excel/Numbers), especially for money:
amounts should be rendered and accepted in the selected display currency (default
USD), while the backend continues storing normalized cents.

## Phase 2 — Forecast Engine

**Status**: not started

- [ ] 2.1 Port `Amount`/`Bill`/`Cycle`/`getForecast` to Python with `Decimal` math;
      port the existing test cases (`packages/forecast/src/__tests__/*`) to pytest as
      the correctness baseline
- [ ] 2.2 Extend the engine for the new recurrence types beyond monthly/annual (weekly,
      semimonthly, custom-interval-days)
- [ ] 2.3 Backend forecast endpoint (account, date range, starting balance, income per
      cycle → cycle-by-cycle breakdown)
- [ ] 2.4 Frontend forecast view (Svelte equivalent of `clientv0`'s `Forecast.tsx`:
      cycle rows with running total, expandable to show which bills/transactions hit
      that cycle)

## Phase 3 — Transactions & Windfalls

**Status**: not started

- [ ] 3.1 Backend: one-off `transactions` CRUD, folded into the forecast calculation
      alongside recurring bills
- [ ] 3.2 Frontend: add/manage one-off transactions UI
- [ ] 3.3 Backend: `windfalls` CRUD (future one-time income), folded into forecast
- [ ] 3.4 Frontend: windfall entry UI, forecast visualization highlighting windfall
      impact on the running balance

## Phase 4 — Multi-account dashboard & polish

**Status**: not started

- [ ] 4.1 Dashboard aggregating all of a user's accounts (combined + per-account views)
- [ ] 4.2 UI/design pass — consistent Svelte component system, responsive layout. Still open:
      general responsive layout pass, plus whatever else turns up. Done so far:
      - [x] a real date-picker component (`frontend/src/lib/components/DatePicker.svelte`,
        a popover calendar) replacing the native `<input type="date">` in the bill form
      - [x] a `Select` component styled to match `Input`
        (`frontend/src/lib/components/Select.svelte`), used for the bill form's Frequency
        field and the move-bill account picker
      - [x] renamed the "Recurrence" label to "Frequency" in the bill form
      - [x] human-readable labels for recurrence values (`frontend/src/lib/recurrence.ts`),
        used in both the dropdown and the bills table
- [ ] 4.3 Error handling, loading states, empty states throughout
- [ ] 4.4 Test coverage: forecast engine (pytest), key frontend components

## Phase 5 — Production hardening (ongoing, lower priority)

- [ ] Structured logging / basic observability within free-tier limits (#19)
- [ ] Confirm Neon's backup/retention behavior meets expectations, plus a documented
      restore drill / disaster-recovery path (#20)
- [ ] Periodic cost review (matches CLAUDE.md's cost-first philosophy)
- [ ] Security hardening review for IAM/Auth0/API/storage settings, keeping the current
      cost-first architecture in mind (#21)
- [ ] Production deployment audit: reconcile the older infra/bootstrap issues with the
      current Terraform + GitHub Actions reality, document what is already live, and split
      any remaining gaps into smaller concrete follow-ups (#8, #9, #10, #12, #17, #18)
- [ ] DNS/domain decision: either move DNS to Route 53 and cut over from Hover, or
      explicitly keep DNS outside AWS and document the manual process/rollback (#13, #14)
- [ ] End-to-end production verification across Auth0, CloudFront, API Gateway, Lambda,
      and Neon (#22)
- [ ] System / ops / API documentation pass, including deployment/runbook coverage (#23)

## Legacy GitHub Project issue crosswalk

Use this when closing the old project-management issues so their intent stays visible here:

- **Already shipped and represented above**
  - #6 → Phase 0.1-0.2
  - #7 → Phase 0.4, 1.1, 1.2
  - #11 → Phase 0.5, 1.3, 1.4, 4.2
  - #15, #16 → Phase 0.4-0.5
- **Superseded in original form**
  - #8 assumed VPC/private-subnet + Secrets Manager plumbing. The current cost-first
    design instead keeps Lambda out of a VPC and passes Auth0/Neon values as Terraform
    variables/environment config; track any remaining deployment hardening under Phase 5.
- **Still relevant, now consolidated into roadmap items above**
  - #9, #10, #12, #17, #18 → Phase 5 production deployment audit
  - #13, #14 → Phase 5 DNS/domain decision
  - #19 → Phase 5 observability
  - #20 → Phase 5 backup / disaster recovery
  - #21 → Phase 5 security hardening review
  - #22 → Phase 5 end-to-end production verification
  - #23 → Phase 5 documentation pass

---

## Session log

Keep this brief — one line per session, what shipped, what's next. Helps a fresh
session (or a fresh Claude Code instance) orient in under a minute.

- 2026-07-10: Roadmap created. No app code yet — `backend/` and `frontend/` are both
  bare scaffolds (from the earlier prod-outage recovery work). Next: Phase 0.1.
- 2026-07-10: Phase 0 built out end-to-end: SQLAlchemy models + ER diagram (0.1), Alembic
  wired up with a verified initial migration — upgrade/downgrade round-trip tested against
  real Postgres, including a fix for the Postgres-enum-survives-drop-table gotcha (0.2),
  docker-compose Postgres for local dev on host port 5433 (5432 was taken by an unrelated
  `bank` project container) (0.3), JWT validation dependency + `GET /api/v1/me` tested with
  a locally-signed RSA token (0.4), and SvelteKit Auth0 SPA integration — login/logout,
  protected `/dashboard` route, token-attaching `apiFetch` helper, verified via
  `svelte-check` and a full static build (0.5). **Not done**: the actual Auth0 tenant/API
  doesn't exist yet — that's a manual console step (see 0.4/0.5 notes above) before the
  frontend↔backend auth flow can be exercised for real. Next: create the Auth0 tenant, then
  start Phase 1 (accounts & bills CRUD).
- 2026-07-11: Phase 1 shipped and merged (PR #82) — Auth0 tenant created and verified via a
  real login; backend accounts/bills CRUD with JIT user provisioning; frontend Tailwind +
  accounts/bills pages behind an auth-guarded route group; whole stack now runs via
  `docker compose up`; docs/READMEs/`.example` files reconciled with reality. Follow-ups
  logged rather than fixed this session: bills page header doesn't show the account
  name/bank (1.5), no way to move a bill between accounts (1.6), and the native date picker
  needs replacing (folded into 4.2). Next: pick up Phase 1.5/1.6, or start Phase 2
  (forecast engine).
- 2026-07-11: Picked up 1.5, 1.6, and part of 4.2. Bills page header now shows
  `Bills (<Name> - <Bank>)`; bills can be moved between accounts via a modal (backend
  ownership-checks the target account); new `Select`, `Modal`, and `DatePicker` (custom
  popover calendar, no new dependency) components; "Recurrence" renamed to "Frequency" with
  human-readable value labels everywhere. Left 1.7 alone (recurrence-config UI) per its own
  "not yet designed" flag. Next: scope 1.7, or start Phase 2.
- 2026-07-12: Roadmap expanded with a new bills CSV import/export follow-up (1.8): per
  account, human-readable spreadsheet-friendly CSVs, with amounts formatted/parsing in the
  selected currency (default USD) while storage remains normalized cents. Next: decide when
  to slot 1.8 relative to 1.7 vs. Phase 2.
