# Monetization

Planning document, not an implementation spec. Tally is currently 100% free with no pricing
model, no billing code, and no plan concept anywhere in the schema. This lays out realistic
options for a solo developer's personal-finance tool, a recommended approach, a rough pricing
sketch, and what would actually need to be built to support it. **No billing/payment code
should be written from this document without Ken making the calls flagged below** — pricing,
entity/tax setup, and legal terms are real business decisions, not engineering ones.

## Where Tally is today

Per [docs/ROADMAP.md](ROADMAP.md), Phases 0-6 are code-complete: Auth0 login, multi-account
dashboard, bill/transaction/windfall CRUD, a from-scratch forecast engine (weekly through
annual recurrence, semimonthly, custom intervals), cycle reconciliation with an audit trail,
CSV import/export, and a public no-login demo on the homepage. Nothing charges anyone anything,
and nothing in `backend/src/models/` or `backend/pyproject.toml` has a `plan`/`subscription`
concept or a billing SDK (no `stripe`, no `paddle`, nothing) — this really is starting from
zero on the monetization side.

The cost base is deliberately tiny (see [docs/OPERATIONS.md](OPERATIONS.md)'s Cost Review):
Lambda/CloudWatch/ACM are effectively free forever at this traffic, CloudFront/S3/API Gateway
are free for 12 months then pennies, Neon's free tier covers current usage, Auth0's free tier
covers up to 25,000 MAU. In other words, Tally has no monetization *pressure* from its own cost
structure today — any pricing decision is about wanting revenue, not about needing to cover a
bill.

## Options considered

**Subscription (freemium)** — a free tier plus a paid tier unlocking specific features, billed
monthly/annually. This is what the entire comparable-product category does: YNAB, Copilot,
Monarch Money, Tiller all charge $10-15/month or a discounted annual equivalent. Recurring
revenue matches a tool people use continuously (bills recur; so does the value of tracking
them), and a free tier keeps the existing homepage demo and low-friction signup funnel intact.
Downside: recurring billing is the most engineering-heavy option (subscription lifecycle,
webhooks, dunning/failed-payment handling, proration on plan changes).

**One-time / lifetime purchase** — pay once, keep access forever (or for a stated period).
Popular with indie-software buyers who are fatigued by subscriptions, and it's the simplest
possible billing integration (a single Checkout session, no recurring state machine, no
webhook-driven status sync). Downside: no recurring revenue to fund ongoing hosting/maintenance
indefinitely, and "lifetime" commitments age badly for a solo maintainer — if Tally is still
running in five years, lifetime purchasers still expect it to work.

**Usage-based limits without a paid tier (e.g. hard cap, no purchase)** — not really a
monetization strategy, just a free-tier gate. Included here only because it's the *mechanism*
underlying both options above (see Pricing tier sketch below), not an alternative to them.

**Donation / pay-what-you-want** — lowest engineering lift (a single "Buy Me a Coffee" or
GitHub Sponsors link, no plan gating in-app at all), but revenue is typically negligible and
uncorrelated with actual usage — doesn't fund ongoing hosting/maintenance in any predictable
way. Reasonable as a *supplement* (e.g. a "support this project" link for the free tier), not
as the primary model.

**Ad-supported** — a poor fit and inconsistent with what's already shipped: the Privacy Policy
(`frontend/src/routes/privacy/+page.svelte`) already states "we do not use it for advertising"
and that Tally has no tracking/advertising cookies. Reversing that for a handful of ad dollars
in a tool that displays someone's bills and account balances is a bad trade — ruled out.

## Recommendation

**Freemium subscription, one paid tier to start.** Reasoning:

- It matches the category (every comparable tool subscribes) and matches Tally's existing
  free-tier-first positioning (the public homepage demo already sells "try it free," see
  Phase 4.6 in the roadmap).
- One paid tier — not three — because a solo developer supporting multiple tiers' worth of
  gating logic, pricing-page complexity, and support questions ("what's the difference
  between Plus and Pro again?") is real, ongoing overhead for marginal benefit at Tally's
  likely scale. Add a second tier later only if a specific under-served segment shows up
  (e.g. a "Family" multi-user tier, which doesn't exist as a concept in the schema at all
  today — `bank_accounts.user_id` is a single owner, not shared).
- Recommend **also** offering a discounted annual plan (standard SaaS pattern, ~2 months free
  vs. monthly) once monthly billing works — it's a Stripe Price object, not new engineering.
- A **lifetime/founder's tier** is worth considering as a *launch-only* option (e.g. first 100
  buyers, one-time price) to get early cash flow and initial paying-user feedback without
  committing the whole product to one-time pricing — but this is a go-to-market call for Ken,
  not something to build reflexively.

## Pricing tier sketch

Illustrative, not final — actual numbers are Ken's call (see Open questions below).

| | **Free** | **Plus** (working name) |
|---|---|---|
| Bank accounts | 1 | Unlimited |
| Bills / transactions / windfalls | Unlimited | Unlimited |
| Forecast engine, cycle reconciliation, bill history/audit trail | Included | Included |
| CSV export | Included (already built, Phase 1.8) | Included |
| CSV import | Included (already built, Phase 1.8) | Included |
| Multi-account dashboard (Phase 4.1) | — (only meaningful with 2+ accounts) | Included |
| Forecast export for LLM analysis (Phase 8, not yet built) | — | Included |
| Price | $0 | ~$4-6/mo or ~$40-50/yr (indicative) |

Why gate on **account count** rather than bill count or forecast frequency: it's the one limit
that's already structurally meaningful in the data model (`bank_accounts.user_id`), doesn't
punish a light single-account user (the exact person the free tier should keep happy and using
the demo-to-signup funnel), and directly maps to the one already-built feature (the multi-account
dashboard, Phase 4.1) that has no value at all below 2 accounts — a natural, legible upsell
rather than an arbitrary cap on bills or forecast requests that would make the free tier feel
crippled. Gating CSV import instead was considered and rejected: it would make the free tier
worse at the exact "try it seriously" moment (a new user importing their real bills) that
determines whether they stick around long enough to ever consider paying.

## What would need to be built

Not being built now — this is the punch list for whenever Ken decides to move on this.

**Billing provider integration.** Recommend Stripe: Stripe Checkout (hosted payment page — no
PCI-scope card handling in Tally's own frontend) + the Stripe Customer Portal (hosted
subscription-management page — cancel/update card/view invoices — so Tally doesn't need to
build any of that UI itself) + Stripe Billing for the actual subscription lifecycle. This is
the standard low-engineering-lift path for a solo developer; a self-hosted card form or a
lower-level processor would be meaningfully more work for no real benefit at this scale.

**Data model.** New columns on `users` (or a new `subscriptions` table if the lifecycle state
gets complex enough to want its own audit trail, mirroring the `bill_events` precedent):
`stripe_customer_id`, `plan` (`free`/`plus`), `subscription_status`
(`active`/`past_due`/`canceled`/etc.), `current_period_end`. A new Alembic migration, same
pattern as every other schema change to date.

**Webhook endpoint.** `POST /api/v1/billing/webhook` (unauthenticated by definition — Stripe
calls it directly — but signature-verified using Stripe's webhook secret, not left open like
the demo endpoint). Handles `checkout.session.completed`, `customer.subscription.updated`,
`customer.subscription.deleted`, `invoice.payment_failed` at minimum, updating the
`subscription_status` columns above. This is the piece most worth getting right early —
webhook handling bugs are how "I paid but the app still says I'm on Free" support tickets
happen.

**Plan gating.** A FastAPI dependency (same shape as `get_owned_bank_account` in
`backend/src/api/deps.py`) checking account count against plan limit before
`POST /api/v1/accounts` succeeds, returning a clear `402`/`403` the frontend can turn into an
upsell prompt rather than a generic error. Keep gating logic in one place (a `require_plan`-style
dependency), not scattered per-endpoint checks that drift out of sync.

**Frontend.** A `/pricing` page (public, alongside the existing `/privacy`/`/terms`), an
upgrade flow (redirect to Stripe Checkout, handle the return URL), a billing settings page
(mostly just a link to the Stripe Customer Portal), and upsell UI at the point of friction
(e.g. the "Add account" button showing a paywall prompt once the free-tier limit is hit,
similar to how empty states already prompt "Add a bank account" on the dashboard today).

**Legal/compliance.** The Privacy Policy and Terms and Conditions already have a standing
"needs an actual lawyer" flag in [docs/ROADMAP.md](ROADMAP.md) Phase 5 — billing raises the
stakes on that review (auto-renewal disclosure requirements vary by US state, a stated refund
policy, cancellation terms) and shouldn't ship without it once real money is involved, more so
than the current placeholder-copy version covers.

**Analytics.** The existing local analytics pipeline
([docs/ANALYTICS.md](ANALYTICS.md)) tracks activity but has no revenue concept at all; MRR/churn
should be read from Stripe's own dashboard/reports rather than rebuilt in Tally — avoid
duplicating what the billing provider already tracks well.

## Open questions for Ken (not guessed at here)

- **Actual price point(s)** — the $4-6/mo sketch above is a category-comparison placeholder,
  not a researched number.
- **Business entity / tax setup** — accepting payments as a solo developer typically means an
  LLC (or equivalent) and a decision on sales-tax/VAT handling (Stripe Tax can automate
  collection but someone still has to register where required). Real legal/accounting
  question, not an engineering one.
- **Grandfathering** — do existing free users (however many there are today) get to keep full
  access, or do they get folded into the Free tier's limits at launch? Affects both goodwill
  and the gating logic's rollout.
- **Lifetime/founder's-tier launch pricing** — worth doing or not; if yes, at what price and
  for how many buyers.
- **Refund policy** — none exists today (nothing to refund yet); needs a stated policy before
  Checkout goes live.
