# Production Readiness

A punch list for "is Tally actually ready for real, paying users" — distinct from
[docs/OPERATIONS.md](OPERATIONS.md) (which documents *how* the current infrastructure works)
and [docs/ROADMAP.md](ROADMAP.md) (which tracks *feature* work). This looks specifically at the
gap between "works for a solo developer and a handful of known users" and "safe to charge
strangers money for," referencing both of those docs plus a direct read of the current
codebase. Written 2026-07-17.

Three buckets: **Done** (genuinely solid, no action needed), **Gap — should fix before real
users** (would cause real pain, cost, or compliance exposure once there's actual customer money
or a larger unknown user base involved), and **Gap — can wait** (real gaps, but low-severity or
already-deferred-on-purpose at current scale).

## Done

- **Auth** — Auth0-backed JWT validation (JWKS, no session state), SPA login flow, dev-only
  bypass gated off in every deployed environment (`DEV_AUTH_BYPASS` unset anywhere in `infra/`).
- **Structured logging** — JSON access logs to CloudWatch, queryable via Logs Insights
  (`docs/OPERATIONS.md`'s Observability section).
- **Backup / DR** — Neon PITR documented with a tested restore-via-branching drill; the one
  open call (Free vs. Launch plan, i.e. 6-hour vs. 7-day recovery window) is correctly flagged
  in `docs/OPERATIONS.md` as Ken's decision, not guessed at.
- **Cost posture** — no NAT Gateway/Elastic IP spend, free-tier-conscious sizing throughout,
  a documented cost table with the one real free-tier cliff (API Gateway's 12-month clock)
  called out.
- **IAM least-privilege pass** — the Lambda role's unused account-wide S3 read access was
  removed; frontend bucket got an explicit public-access block. Reviewed and accepted:
  API Gateway auth-at-the-app-layer (not the gateway), CORS scope, OIDC-based CI/CD auth
  (no long-lived AWS keys).
- **Deploy automation** — both frontend and backend deploy on push to `main` via GitHub
  Actions, no manual "did I remember to run the script" step.
- **Cold-start reliability** — the intermittent-502 root cause (default 3s Lambda timeout)
  is fixed (`timeout=15s`, `memory_size=512MB`), with frontend-side retry on 502/503/504 as a
  second layer.
- **Consent tracking** — `User.terms_accepted_at`, enforced via an interstitial blocking every
  app route until accepted; the known timing tradeoff (JIT provisioning happens a moment before
  consent capture) was reviewed and explicitly accepted as low-risk, not left undocumented.
- **HTTPS everywhere** — CloudFront `viewer_protocol_policy = "redirect-to-https"` on both
  frontend and API behaviors; ACM-issued cert.
- **Basic input bounding on the one public unauthenticated endpoint** —
  `POST /api/v1/demo/forecast` caps bill count (25) and forecast window (366 days) at the
  schema-validation layer (`backend/src/schemas/demo.py`), bounding worst-case compute per
  request even before rate limiting exists (see below).
- **Empty states** — new users hitting an empty accounts list or dashboard get a clear "Add a
  bank account" prompt rather than a blank page (not a guided tutorial, but not nothing either
  — see the onboarding gap below for the distinction).

## Gap — should fix before real users

- **No rate limiting anywhere.** Neither the public `POST /api/v1/demo/forecast` endpoint nor
  any authenticated endpoint has request-rate limiting — `infra/modules/api_gateway/main.tf`
  has no usage plan / throttling configuration at all, so the only protection is API Gateway's
  default account-level burst/steady-state ceiling (shared across the *entire* AWS account, not
  scoped to Tally) and the demo endpoint's own per-request size caps. At solo-dev-known-users
  scale this has never mattered; once the app is reachable by the public internet with a reason
  to attack it (e.g. a payment flow, per `docs/MONETIZATION.md`), an unthrottled endpoint that
  fans out into Neon queries is a real cost/availability risk. Cheapest fix: an API Gateway
  usage plan with a per-IP or per-API-key throttle on the REST API stage — no new AWS service,
  no NAT/VPC implications, consistent with the cost-first architecture already in place.
- **No error alerting.** `docs/OPERATIONS.md` explicitly documents this as a deliberate
  deferral ("no custom CloudWatch metrics/dashboards or alarms yet... check the logs when
  something looks wrong"), reasonable for a solo developer's own known-user traffic where a bug
  report *is* the alert. That reasoning stops holding once there are paying users who won't
  necessarily tell you before they churn. Cheapest fix already scoped in `docs/OPERATIONS.md`:
  a couple of alarms on Lambda's free built-in metrics (`Errors`, `Throttles`, `Duration` —
  no custom metrics needed, so no added CloudWatch cost) wired to an SNS topic emailing Ken.
  Small, well-understood, not done.
- **No self-service data export/deletion, despite the Privacy Policy promising it.** The
  Privacy Policy (`frontend/src/routes/privacy/+page.svelte`) states: "To request a full export
  or deletion of your account and all associated data, contact us and we'll handle it
  promptly." Nothing in the codebase backs that today — `DELETE /api/v1/accounts/{id}`
  (`backend/src/api/accounts.py`) deletes one *bank account* (cascading its bills/transactions/
  etc.), but there is no endpoint that deletes a `User` row or exports a bundle covering all of
  a user's accounts at once; the only export is the existing per-account, per-type CSV
  (bills/transactions/windfalls separately, Phase 1.8). At current scale "contact us" means
  Ken manually querying/deleting in Neon, which is fine for a handful of people he already
  knows. It stops being fine — both as a support burden and as a compliance gap (GDPR/CCPA
  access and erasure rights, if any user is in a jurisdiction where those apply) — once
  "contact us" could mean an unknown stranger. Needs at minimum a documented internal runbook
  (a script, not necessarily a self-service UI) before onboarding users Ken doesn't personally
  know; a real self-service "delete my account" flow is the more durable fix.
- **Support-email domain doesn't match the production domain.** Both legal pages point at
  `@tally.dev` (`privacy@tally.dev`, `support@tally.dev` in `frontend/src/routes/privacy/` and
  `frontend/src/routes/terms/`), but the actual production site is `tally.kenhoward.dev` (per
  `docs/OPERATIONS.md`'s DNS section) — a different domain entirely. **Flagging for Ken**:
  confirm `tally.dev` is a domain that's actually owned and has a monitored inbox behind those
  addresses; if not, either register/redirect it or change the copy to a real, working address
  before anyone relies on it to reach a human.
- **Legal review still pending, and billing would raise the stakes.** Already flagged in
  `docs/ROADMAP.md` Phase 5 as blocked on an actual lawyer, not something to guess at — carried
  forward here because "real paying users" is exactly the condition that makes this urgent
  rather than a someday-item. If monetization per `docs/MONETIZATION.md` moves forward, the
  review needs to additionally cover billing terms (refund policy, auto-renewal disclosure,
  cancellation terms), which don't exist in any form today.
- **No security response headers.** No Content-Security-Policy, HSTS, X-Frame-Options, or
  similar are configured — `infra/modules/cloudfront/main.tf` sets `redirect-to-https` but no
  response headers policy, and nothing in `backend/src/main.py` adds them either. Low cost to
  fix (a CloudFront response headers policy is a native, free feature — no new service), and
  standard due diligence once the app is asking strangers to enter financial data.

## Gap — can wait

These are real, and some are already explicitly deferred in `docs/ROADMAP.md`/
`docs/OPERATIONS.md` — listed here for completeness, not as new findings, except where noted.

- **API Gateway access logging** — not enabled (`docs/OPERATIONS.md`'s Observability section);
  Lambda's own request logs already give per-request visibility, so this mainly adds
  gateway-level 4xx/5xx counts that aren't currently needed.
- **No fast rollback path** — reverting a commit and letting CI redeploy is the whole rollback
  story today (no Lambda versioning/aliases, no frontend bucket versioning). Acceptable at
  current traffic/incident frequency; worth revisiting if downtime during a bad deploy starts
  actually costing something.
- **No Terraform state locking (DynamoDB)** — mitigated today by CI's own
  `concurrency: group: terraform-apply-prod` serializing applies; a real gap only in the
  unlikely event of a concurrent local + CI apply.
- **Secrets as plain Lambda env vars, not Secrets Manager** — a documented, deliberate
  cost/benefit tradeoff ($0.40/secret/month for rotation + IAM-gated read that doesn't clearly
  pay for itself at this scale); revisit only if a compliance requirement forces it.
- **No WAF** — has its own fixed monthly cost ($5/web ACL + per-rule); not justified pre
  meaningful traffic or any actual observed abuse.
- **No admin-only analytics dashboard** — `docs/ROADMAP.md` Phase 6 already defers this
  explicitly ("local-first," revisit once it's clear which metrics get checked regularly).
- **Onboarding is minimal, not guided.** Empty states exist (see Done above) and the homepage's
  interactive demo (Phase 4.6) lets a visitor try the forecast concept before signing up, but
  there's no in-app first-run walkthrough once a real account is created — a new user has to
  intuit "add an account, then add bills, then run a forecast" from page structure alone. Not
  urgent (the glossary page and tooltips from Phase 4.5 already soften the app's specific
  vocabulary), but worth a look once there's a signup funnel worth optimizing, i.e. once
  monetization is live and drop-off actually matters financially.
- **No public status page / uptime commitment.** Reasonable to skip for a free tool; worth
  adding (even something as simple as a static page + a note in the pricing/terms about
  best-effort uptime, no formal SLA) around when a paid tier launches — paying users generally
  expect at least a status page to check, not a formal SLA at this scale.
- **Prod-unreachable interactive API docs** (`/docs`/`/redoc`) — FastAPI generates them, but
  API Gateway only routes `/api/v1/{proxy+}`, so they 404 in prod. Not needed today (no
  external API consumers); would matter if Tally ever exposed a public API.
- **SEO** (`docs/ROADMAP.md` Phase 9) and **forecast export for LLM analysis** (Phase 8) — both
  already tracked as deferred feature work, not reliability/compliance gaps.
- **DNS at Hover instead of Route 53** — a documented, deliberate cost decision
  (`docs/OPERATIONS.md`), not a gap.

## Summary

Nothing found here is a fire — Tally's infrastructure and code quality are in good shape for
what the app has been until now (a solo developer's own tool, used by people he knows). The
"should fix" list above is short and each item is cheap: throttling on the API Gateway stage,
two or three free CloudWatch alarms, a real support inbox, a data-export/deletion runbook, and
a CloudFront response headers policy. None of them require new AWS services or meaningfully
change the cost-first architecture. The one item that isn't a quick technical fix — legal
review of the Privacy Policy/Terms, especially once billing terms are added — is explicitly
Ken's to drive, not something to guess at in code.
