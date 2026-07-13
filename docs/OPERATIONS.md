# Operations

Production hardening reference for Tally: observability, backup/DR, cost, security posture,
a deployment audit, the DNS decision, and a runbook for routine ops tasks. Written for a solo
developer coming back after weeks-long gaps — assume you've forgotten everything below.

This is the detail behind [docs/ROADMAP.md](ROADMAP.md)'s Phase 5 checklist; check there first
for current status, then come here for the how/why.

## Observability

**Structured logging**: the backend logs JSON lines (`backend/src/core/logging.py`) - one
`{"logger": "tally.access", "message": "request", "method", "path", "status_code",
"duration_ms"}` line per request, plus any application log calls, all going to stdout, which
Lambda ships to CloudWatch Logs automatically (`AWSLambdaBasicExecutionRole`, attached in
`infra/modules/lambda/main.tf`). Level is `LOG_LEVEL` (default `INFO`; see
`backend/.env.example`). JSON (not plain text) so CloudWatch Logs Insights can query fields
directly, e.g.:

```
fields @timestamp, method, path, status_code, duration_ms
| filter status_code >= 500
| sort @timestamp desc
```

**What's deliberately not done**: no custom CloudWatch metrics/dashboards or alarms yet -
every custom metric and every alarm has a per-metric cost, and at solo-developer traffic
volumes the log-based visibility above is enough to debug an incident after the fact. If usage
grows enough that "check the logs when something looks wrong" stops being viable, the next
step is a couple of alarms on Lambda's free built-in metrics (`Errors`, `Duration`,
`Throttles` - no custom metrics needed) with an SNS topic emailing you, not a dashboard.

**Known gap - CloudWatch log group retention**: `AWSLambdaBasicExecutionRole` lets the Lambda
service auto-create its log group (`/aws/lambda/tally-backend`) on first invocation, and an
auto-created group defaults to **Never Expire** retention - logs (and their storage cost)
accumulate forever. This wasn't fixed via Terraform in this pass: managing that log group as
an `aws_cloudwatch_log_group` resource requires either importing the already-existing group
into state first or Terraform's `apply` fails with "already exists". Since this session's AWS
SSO session was expired and a fresh login is an interactive step only Ken can do, the safe fix
is a one-time manual command rather than a Terraform change that could break the next
`terraform-apply.yml` run:

```bash
aws logs put-retention-policy --log-group-name /aws/lambda/tally-backend --retention-in-days 30
```

Run this once (after `make aws-login`), then it's set permanently - no recurring action
needed. Revisit bringing it under Terraform (via `terraform import`) if the log group is ever
recreated (e.g. after a `terraform destroy`).

**API Gateway access logging** is not enabled either (the REST API stage has no
`access_log_settings`). Enabling it requires an account-level CloudWatch role
(`aws_api_gateway_account`) which is a singleton per AWS account - adding it via Terraform
without first checking whether one already exists (can't verify without live credentials this
session) risks clobbering an unrelated existing setting. Lambda's own request logs (above)
already cover per-request visibility; API Gateway access logs would mainly add gateway-level
4xx/5xx counts that aren't currently needed. Low priority - revisit if debugging ever needs the
API Gateway hop specifically distinguished from the Lambda's own logs.

## Backup / Disaster Recovery

Production Postgres is Neon (manual, not Terraform-managed - see
[docs/ROADMAP.md](ROADMAP.md)'s "Neon: manual vs. Terraform-managed" decision). Neon's backup
model, per [its docs](https://neon.com/docs/manage/backups):

- **Instant restore / point-in-time recovery (PITR)**: Neon retains a continuous history of
  storage changes and can restore (or branch) to any timestamp within that window, no
  traditional backup/restore process needed. The window depends on plan:
  - **Free plan: 6 hours**, capped at 1 GB-month of history.
  - **Launch plan: up to 7 days** (billed per GB-month beyond the plan's included storage).
  - **Scale plan: up to 30 days**.
- **Manual `pg_dump`**: a standard logical backup, independent of Neon's own retention -
  useful for an off-platform copy or before a risky migration.

**Confirm which plan prod is on** (Neon console → project settings → Billing) - this
determines the actual recovery window and is a real cost/risk tradeoff, not something to guess
at here. A 6-hour window (Free) means an issue noticed the next morning is already
unrecoverable via PITR; 7 days (Launch, ~$19/mo minimum) covers "came back from a long weekend
and noticed bad data." **Flagging for Ken**: decide whether Tally's current data
(user-entered bills/transactions, no real bank linkage - see the Privacy Policy) justifies the
Launch plan's cost for a longer PITR window, or whether Free's 6 hours plus the manual
`pg_dump` drill below is an acceptable risk for now.

### Restore drill (do this at least once, then whenever the Neon plan changes)

Neon's restore is done via **branching** - you create a new branch from a past point in time,
verify it, then either point the app at it or copy data back. Nothing here touches the
production branch unless you explicitly promote it.

1. In the Neon console, open the `tally` project → **Branches** → **Create branch**.
2. Choose **"From a specific time"** and pick a timestamp within the retention window (or
   "now" for a smoke test of the mechanism itself).
3. Once the branch is ready, grab its connection string (console → branch → Connection
   Details) and connect with `psql` (see `docs/DEVELOPING.md`'s "Accessing the Production
   Database" section for the connection-string shape).
4. Verify expected data is present (e.g. `select count(*) from bills;` and spot-check a
   recently-modified row against what you expect).
5. Delete the drill branch when done (branches aren't free-tier-unlimited on all plans).

If a real restore is ever needed: create the branch as above from the target timestamp, then
either (a) update `TF_VAR_database_url_readwrite`/`readonly` (GitHub repo secrets
`TALLY_DATABASE_URL_READWRITE`/`READONLY`) to point at the restored branch and redeploy, or
(b) use the branch as a source to copy specific rows back into the primary branch via
`pg_dump`/`pg_restore` for a targeted fix rather than a full cutover.

**Off-platform backup**: no automated `pg_dump`-to-S3 export is configured. Given the low
production data volume (solo project, no paying customers as of this writing) and Neon's PITR
already covering the "oops" case, this wasn't added this pass to avoid another moving part
(GitHub Actions schedule + S3 lifecycle policy + restore-tested-or-it-doesn't-count) for a risk
that's already mitigated. Revisit if/when real user data volume makes "the only copy is Neon's
own PITR" feel too thin.

## Cost Review

Estimated based on the resources in `infra/` and public pricing as of this writing - not a
live Cost Explorer pull (this session's AWS SSO token was expired; see the Deployment Audit
section for what that blocked). **Ken should confirm against the actual AWS Billing console
and Neon/Auth0 dashboards** - these are estimates, not verified spend.

| Resource | Free tier | Cost once past free tier |
|---|---|---|
| Lambda | 1M requests + 400,000 GB-s/month, **permanently free** | $0.20/M requests + $0.0000166667/GB-s - solo-dev traffic stays near $0 indefinitely |
| API Gateway (REST) | 1M calls/month for **12 months from account creation only** | $3.50/M requests after - low volume keeps this at cents/month even off free tier |
| CloudFront | 1TB out + 10M requests/month for 12 months | ~$0.085/GB after - a low-traffic static SPA stays well under $1/month |
| S3 (frontend + backend buckets) | 5GB storage for 12 months | Storage here is a few MB (SPA build + one Lambda zip with versioning) - negligible either way |
| ACM certificate | Always free | n/a |
| CloudWatch Logs | 5GB ingestion + 5GB storage, **always free** | $0.50/GB ingested past that - see the retention-policy gap noted above, since unbounded retention is what would eventually cross this line |
| Neon (Postgres) | Free: 0.5GB storage, ~191 compute-hours/month, 6h PITR | Launch starts ~$19/month for 7-day PITR + more storage/compute |
| Auth0 | Free: 25,000 MAU, 1-day log retention | Paid tiers add longer log retention, custom domains, MFA - not needed at current scale |
| Domain (Hover) | n/a | Already owned, renews annually outside AWS - not part of this cost review |
| Route 53 | not used | n/a - see DNS decision below |

**The one real free-tier cliff to watch**: API Gateway's REST API free tier is only for the
account's first 12 months, not "always free" like Lambda and CloudWatch Logs. Once past that
anniversary, every API call costs $3.50 per million - at solo-developer traffic this is still
pennies, but it's the one line item that goes from $0 to non-zero on a fixed date, not with
usage growth. **Action for Ken**: check the AWS account's creation date and note in this doc
whether Tally's prod traffic is still inside that window.

**Cost-first architecture already in place** (per `CLAUDE.md`'s philosophy, confirmed by this
review, no changes needed): no NAT Gateway or Elastic IPs (Lambda isn't in a VPC at all - see
the Deployment Audit's note on issue #8), no RDS (Neon instead), `PriceClass_100` on
CloudFront (US/EU/Asia edge locations only, not the pricier global set), S3 lifecycle/versioning
kept minimal (versioning only on the backend artifacts bucket, which needs rollback capability;
not on the frontend bucket, which doesn't).

**Recommendation**: no cost-driven changes needed right now. Revisit this table in ~6 months
or if traffic meaningfully grows, whichever comes first - add a line to the session log when
you do.

## Security Hardening Review

Changes made this pass (see the commit that shipped alongside this doc):

- **Removed the Lambda execution role's `AmazonS3ReadOnlyAccess` attachment**
  (`infra/modules/lambda/main.tf`) - account-wide read access to every S3 bucket in the
  account, unused by the app itself (confirmed via `grep` - no `boto3`/S3 calls anywhere in
  `backend/src`). The Lambda deployment package is fetched by AWS's own Lambda service using
  its own permissions, not by application code, so this was pure unnecessary blast radius.
  Only `AWSLambdaBasicExecutionRole` (CloudWatch Logs write) remains attached.
- **Added an explicit `aws_s3_bucket_public_access_block`** to the frontend S3 bucket
  (`infra/modules/frontend_s3/main.tf`), matching the backend artifacts bucket's existing
  posture. The bucket policy already only grants CloudFront's service principal access
  (scoped further by an `AWS:SourceArn` condition), which isn't "public" access in AWS's
  sense, so this doesn't change current behavior - it's a guard against a future accidental
  public grant, not a fix for an existing hole.

Reviewed, no change made (reasoning below):

- **API Gateway proxy method has `authorization = "NONE"`**
  (`infra/modules/api_gateway/main.tf`) - intentional. Auth is enforced in the FastAPI app
  itself (`get_current_user`, JWKS-based JWT validation against Auth0), not at the gateway
  layer. `/api/v1/demo/*` is deliberately public (no auth at all, by design - see
  `docs/ROADMAP.md` Phase 4.6). Adding a Lambda authorizer here would duplicate the app-layer
  check for no real gain, and would need to special-case the demo routes anyway.
- **CORS** (`backend/src/main.py`) only allows `localhost`/`127.0.0.1:5173` origins - correct,
  since prod frontend and API share an origin via CloudFront's routing and never need
  cross-origin requests in production. No wildcard, no prod domain even listed (not needed).
- **Terraform state**: S3 backend with `encrypt = true` (`infra/backend.conf`); state bucket
  access itself is IAM-gated (only reachable via the GitHub Actions OIDC role or Ken's own AWS
  SSO identity) - reasonable for a single-maintainer project. No state locking table (DynamoDB)
  configured; a concurrent `terraform apply` collision is a real but low-likelihood risk for a
  solo developer + one CI workflow with `concurrency: group: terraform-apply-prod` already
  serializing applies (`terraform-apply.yml`) - the concurrency group is the actual mitigation
  here, not S3 locking.
- **Secrets**: DB/Auth0 values reach the Lambda as plain environment variables, not AWS
  Secrets Manager (documented tradeoff already, see `infra/README.md` and `infra/main.tf`'s
  comments) - Secrets Manager costs $0.40/secret/month plus API calls, for a benefit (secret
  rotation, IAM-gated read) that doesn't clearly outweigh the cost at this scale. Revisit only
  if a compliance requirement forces it.
- **GitHub Actions → AWS auth**: already uses OIDC (`role-to-assume` via
  `aws-actions/configure-aws-credentials`), not long-lived access keys - no change needed,
  this is already the secure pattern.

Not reviewed live this session (blocked by the expired AWS SSO token - flagging for Ken rather
than guessing):

- Actual IAM policy documents attached to the GitHub Actions OIDC role
  (`tally-github-actions-role` per `CLAUDE.md`) - confirm it's scoped to what
  `terraform-apply.yml`/`deploy-frontend.yml` actually need (S3, Lambda, API Gateway,
  CloudFront, ACM, IAM-for-its-own-role) rather than broader `AdministratorAccess`-equivalent
  access reused from local dev convenience.
- Auth0 tenant security settings (MFA availability, brute-force protection, anomaly
  detection) - dashboard-only, not something this repo's code can verify or configure. Auth0's
  free tier includes basic attack protection by default; confirm it's turned on in the
  dashboard (Auth0 → Security → Attack Protection).
- CloudFront/API Gateway WAF - not configured, and not recommended to add at this traffic
  scale (WAF has a fixed monthly cost - $5/web ACL + per-rule - that isn't justified pre-
  meaningful-traffic; revisit if abuse/scraping actually shows up in logs).

## Production Deployment Audit

Reconciling the original bootstrap issues against what's actually live in `infra/` and
`.github/workflows/`:

| Issue | Original scope | Actual state |
|---|---|---|
| #8 (Lambda + VPC + Secrets Manager) | VPC, private subnets, Secrets Manager | **Superseded** - cost-first design keeps Lambda out of a VPC entirely (no NAT Gateway cost) and passes config as plain env vars (see Security review above). Deployed via `terraform-apply.yml`, not manually. Runtime is `python3.13` (not the issue's `python3.11` - keeps current). No X-Ray tracing (not needed - CloudWatch logs cover current debugging needs; X-Ray has its own per-trace cost). |
| #9 (API Gateway + CORS) | API Gateway with CORS configured on the gateway | **Done, differently** - `infra/modules/api_gateway/main.tf` has the `{proxy+}` → Lambda integration; CORS is handled in the FastAPI app instead of at the gateway (see Security review). API Gateway access logging is **not** enabled (see Observability's note - a real, acknowledged gap, low priority). Domain in the original issue (`tally.kenhowardpdx.com`) is stale - actual domain is `tally.kenhoward.dev`. |
| #10 (S3 + CloudFront OAI) | S3 + OAI, public access blocked, versioning | **Done, with an upgrade** - uses OAC (Origin Access Control), the modern replacement for the now-legacy OAI. Public access block was missing on the frontend bucket until this pass (now added, see Security review); backend bucket already had it. Versioning is only on the backend artifacts bucket (needed for Lambda zip rollback), not the frontend bucket (S3 sync + CloudFront invalidation is the frontend's own "redeploy the last good build" path - see Runbook below). |
| #12 (CloudFront + ACM) | ACM cert, CloudFront, SPA routing, compression | **Done** - `PriceClass_100`, DNS-validated ACM cert in us-east-1, `custom_error_response` blocks for SPA deep-links (403/404 → `/index.html`, a real bug fixed in an earlier session - see `docs/ROADMAP.md`'s 2026-07-12 log entry). CloudFront's default compression is on by default for compressible content types - no explicit config needed. |
| #17 (frontend deploy script) | Deployment script | **Done, as a GitHub Action** instead of a local script - `deploy-frontend.yml` builds, syncs to S3, invalidates CloudFront, on every push to `main` touching `frontend/**`. Arguably better than a local script for a solo dev (no "did I remember to run the script" risk). |
| #18 (backend deploy automation) | Lambda packaging + deploy script | **Done, as a GitHub Action** - `terraform-apply.yml` builds the zip (native pip install on the Linux runner, matching Lambda's `python3.13`/AL2023 runtime), stages it to S3, runs Alembic migrations, then plans/applies. **Gap**: no rollback capability beyond "revert the commit and let CI redeploy" - no Lambda versioning/aliases for instant rollback. See the Runbook's rollback procedure below for what "rollback" actually means today. |

**Overall**: every issue's *intent* shipped, mostly via GitHub Actions automation rather than
local scripts (an improvement on the original scope, and consistent with wanting deploys to
not depend on remembering to run something locally). The two real gaps worth tracking forward
are already captured above rather than re-listed here: API Gateway access logging
(Observability) and no fast Lambda rollback path (Runbook, below). Both are low-severity at
current scale.

## DNS / Domain Decision

**Decision: keep DNS at Hover, do not migrate to Route 53.**

`tally.kenhoward.dev` currently resolves via a CNAME/ALIAS at Hover pointing at the CloudFront
distribution's domain name - this already works today (verified in this session's E2E check
below) and has for multiple prior sessions. Issues #13/#14 proposed moving to Route 53; the
case for actually doing it:

- **Cost**: Route 53 hosted zones are $0.50/month each, plus per-query charges past the free
  tier - a pure added cost with no corresponding removed cost (Hover's registration fee is
  unchanged either way; DNS hosting is a separate, additional thing you'd be paying AWS for on
  top of what Hover already does for free as part of registration).
- **Operational benefit**: would mainly matter if Tally needed Route 53-specific features
  (health-check-based failover, latency-based routing, ACM DNS validation fully automated via
  Terraform's `aws_route53_record` instead of a manual DNS step) - none of which apply at
  Tally's current single-region, single-CloudFront-distribution scale. ACM validation already
  happened once, manually, and doesn't need to happen again unless the certificate is replaced
  (auto-renewal doesn't require re-validation for ACM-issued certs on the same domain).
- **Migration risk**: nameserver cutover has a real (if small) window of DNS propagation risk
  for zero functional gain here.

**If this changes**: revisit if Tally ever needs multi-region failover, or if enough other
domains/subdomains accumulate that centralizing DNS management in Terraform (rather than
Hover's UI) becomes worth the $0.50/month. Until then, the manual process is: log into Hover,
edit the CNAME for `tally` under `kenhoward.dev` if the CloudFront distribution's domain name
ever changes (it doesn't change on its own - only on distribution recreation, which normal
`terraform apply` updates don't trigger).

`infra/README.md`'s architecture diagram previously showed a Route 53 box that was never
actually built - fixed as part of this pass to reflect Hover instead (see the diff alongside
this doc).

## End-to-End Production Verification

Verified live against `https://tally.kenhoward.dev` in-browser this session (no AWS/Neon
credentials needed for any of this - all through the public site):

- Homepage loads, renders the marketing hero + feature cards + interactive demo widget.
- **Real API round-trip**: filled in the demo forecast form and submitted it - network log
  confirmed `POST https://tally.kenhoward.dev/api/v1/demo/forecast` → `200`, proving the full
  CloudFront → API Gateway → Lambda → FastAPI path is live and working end-to-end (this
  endpoint doesn't touch Neon, so it doesn't confirm the DB hop specifically - see below).
- `/privacy` and `/terms` both render their full real (placeholder) copy correctly.
- Clicking **Log in** redirects to the real Auth0 tenant's hosted login page
  (`dev-dsg2btrpxwa1gq1v.us.auth0.com`) with a working login form - confirms the Auth0
  integration is live and correctly configured (client ID, callback URL, tenant domain).
  Did not complete an actual login (no test credentials were entered - entering real
  credentials isn't something this session does automatically).

**Not verified this session** (would require completing a real login, which needs an actual
account/credentials): the authenticated app shell, the consent interstitial, and any endpoint
that hits Neon (accounts/bills/forecast/dashboard). Given `/api/v1/demo/forecast` round-tripped
successfully through the exact same Lambda that also serves the authenticated routes, and nothing
DB-specific in the deploy changed, this is a low-risk gap - but it's a real one. **Recommended
for Ken**: log in for real once after reading this, confirm the consent interstitial appears
for a fresh session and that a real account's dashboard loads with actual Neon-backed data.

## Runbook

### Deploying

Both frontend and backend deploy automatically on push to `main`:

- **Frontend** (`deploy-frontend.yml`): triggers on `frontend/**` changes. Builds, syncs to
  S3, invalidates CloudFront (`/*`). Live within a few minutes of merge.
- **Backend + infra** (`terraform-apply.yml`): triggers on `infra/**`, `backend/alembic/**`,
  `backend/src/**`, or Poetry lockfile changes. Packages the Lambda zip, uploads it, runs
  Alembic migrations against prod, then `terraform plan`/`apply`.
- **Manual trigger**: either workflow also supports `workflow_dispatch` from the GitHub
  Actions UI if you need to force a redeploy without a new commit (e.g. after fixing a
  transient CI failure).

### Rolling back

There's no one-click rollback today (a known gap - see the Deployment Audit's #18 note).
What actually works:

- **Frontend**: `git revert` the offending commit (or check out the last-good commit) and push
  to `main` - `deploy-frontend.yml` rebuilds and re-syncs from that ref. Since the frontend
  bucket isn't versioned, there's no "restore the previous S3 objects directly" shortcut;
  rebuilding from git is the actual rollback path, and it's fast (a few minutes).
- **Backend**: same pattern - revert the commit, push, let `terraform-apply.yml` redeploy the
  prior Lambda code. **Caveat**: if the bad deploy included an Alembic migration, reverting the
  *code* doesn't undo the *migration* - check `backend/alembic/versions/` for whether the
  problem commit added one, and write/run a manual `alembic downgrade` against prod if so
  (`DATABASE_URL_READWRITE=<prod URL> poetry run alembic downgrade -1` from `backend/`, after
  `source .secrets` or otherwise having the prod DB URL available - **treat this as a
  production-data-affecting action, confirm the downgrade is actually safe for a schema with
  live data before running it**).
- **Database**: see the Backup/DR restore drill above for point-in-time recovery via Neon
  branching, for data (not schema) problems.

### Checking prod health

- **Logs**: CloudWatch → Log groups → `/aws/lambda/tally-backend`. Structured JSON (see
  Observability above) - use Logs Insights for anything beyond eyeballing recent entries.
- **Quick smoke test**: hit `https://tally.kenhoward.dev` (frontend) and
  `https://tally.kenhoward.dev/api/v1/demo/forecast` (POST, any small JSON body per
  `backend/src/api/demo.py`'s schema) - both work without needing to log in, and together
  confirm CloudFront, S3, API Gateway, and Lambda are all up.
- **AWS access**: `make aws-login` (direct terraform/AWS CLI use) or `make aws-creds` (for
  `act`) from `infra/` - SSO session lasts ~8 hours, re-run when it expires (this is what
  blocked live AWS inspection during this session - see the Security/Cost sections' flagged
  gaps).

### Incident response (solo-developer scale)

No on-call rotation or paging needed at this scale - this section is "what do I do if I notice
something's wrong," not a formal incident process.

1. Check CloudWatch logs for the affected Lambda first (fastest signal for a 5xx spike or
   error pattern).
2. If it's a bad deploy: roll back per above.
3. If it's a Neon issue (connection errors, slow queries): check the Neon console's own
   monitoring/status page first - it's a managed service, so an outage there isn't something
   this app's infra can route around.
4. If it's an Auth0 issue: check Auth0's status page
   ([status.auth0.com](https://status.auth0.com)) - same reasoning.
5. Document what happened and the fix in this file's session-log-equivalent (or
   `docs/ROADMAP.md`'s session log, if it's roadmap-relevant) once resolved, so the next
   6-week-later session has context.

## API Documentation

FastAPI auto-generates interactive API docs from the route definitions already in
`backend/src/api/` - no separate doc-maintenance burden. Available at `/docs` (Swagger UI) and
`/redoc` by FastAPI's default, mounted at the app root rather than under `/api/v1`. **Not
reachable in prod as deployed**: the API Gateway REST API only defines a resource for
`/api/v1/{proxy+}` (`infra/modules/api_gateway/main.tf`) - there's no resource matching a bare
`/docs` path, so API Gateway itself would reject the request before it ever reaches the
Lambda. Browse the docs locally instead: `poetry run uvicorn src.main:app --reload` from
`backend/`, then open `http://localhost:8000/docs`. If prod-reachable docs are ever wanted,
that needs either an additional API Gateway resource for `/docs`+`/openapi.json`, or mounting
FastAPI's docs under the `/api/v1` prefix explicitly - not done here since interactive prod API
docs aren't currently a real need (no external API consumers yet). This still satisfies the
roadmap's "API documentation" ask without hand-maintained docs that would drift from the actual
routes.
