# Usage Analytics

How Tally tracks usage and how to look at it. This is the detail behind
[docs/ROADMAP.md](ROADMAP.md)'s analytics checklist.

## What's tracked and where

Data is split by shape rather than sent to one place:

- **Per-user state (Postgres)** - `users.last_active_at` (a cheap write-throttle guard,
  updated at most once/hour) and `user_daily_activity` (one row per user per UTC day they
  were active - the durable history that MAU/DAU/retention queries read from). Both are
  written by `get_current_db_user` (`backend/src/api/deps.py`) on every authenticated
  request, so no separate instrumentation is needed per-endpoint.
- **Per-request detail (CloudWatch Logs)** - the existing JSON access log
  (`backend/src/core/logging.py`'s `log_requests` middleware) now also includes `user_id`
  (when authenticated) and `viewer_country` (from the `CloudFront-Viewer-Country` header
  CloudFront auto-injects on every request it forwards to the origin - absent in local
  dev, where requests don't go through CloudFront). This is where endpoint popularity,
  latency, and time-of-day patterns live - deliberately *not* duplicated into Postgres, to
  avoid a write on every single request.

This split keeps DB writes small (one upsert per user per hour, at most) while still
answering both "who's active and for how long" (Postgres) and "what are they doing and
when" (CloudWatch).

## Metrics glossary

Standard SaaS analytics framework (AARRR / "pirate metrics"), with Tally-specific notes:

- **DAU / WAU / MAU** - distinct active users in trailing 1/7/30-day windows. Rolling
  windows, not calendar day/week/month.
- **Stickiness (DAU/MAU)** - the standard proxy for "daily habit" vs. "occasional check-in
  tool". A consumer finance app that's checked a few times a week rather than daily can
  still be healthy - don't over-index on a low number alone.
- **Signup trend** - new registrations per week.
- **Stale accounts** - bucketed by days since last activity: active within 30 days,
  stale 30-60d, stale 60-90d, stale 90d+, or never active at all. Ken's definition of
  "stale" is >90 days.
- **Cohort retention** - of users who signed up in month N, what % were still active in
  month N+1, N+2, etc. More informative than a single MAU number because it shows whether
  newer cohorts stick better or worse than older ones.
- **Feature adoption** (not yet queried, easy to add later) - % of users who've ever used
  a given feature (windfalls, CSV import, forecast view) - distinguishes "built but
  ignored" from "core loop". Would need a join against the relevant table's `user_id`
  (via `bank_accounts`) rather than `user_daily_activity`.
- **Endpoint popularity / latency / region / time-of-day** - from CloudWatch, not
  Postgres; see the Logs Insights queries below.

## Running the local report

```bash
make analytics-report
```

Equivalent manual form, if you need to run the script outside `make` (e.g. with extra
args): `set -a` is required since `.secrets` uses plain (non-exported) shell assignments,
so a plain `source .secrets` won't make the variable visible to the script's subprocess -
same pattern `infra/Makefile`'s targets use.

```bash
set -a && source .secrets && set +a
poetry -C backend run python scripts/analytics/report.py
```

Prints total users, DAU/WAU/MAU, stickiness, recent signup trend, and the stale-account
breakdown. Reads `TF_VAR_database_url_readonly` (falling back to `DATABASE_URL_READONLY`,
the name Terraform maps it to as the Lambda's runtime env var) directly via `asyncpg`
(no app/ORM dependency) -
this is the "local process reading from the remote db" approach, reusing the read-only
Neon credential already provisioned in `.secrets` and `infra/modules/lambda/main.tf` (the
app itself doesn't consume this var; it's provisioned specifically for external
read-only reporting like this).

For anything not printed by the script - cohort retention, custom date ranges, ad hoc
digging - the named queries live in `scripts/analytics/queries.sql`; copy any of them
into `psql` or a notebook directly.

## CloudWatch Logs Insights companions

Run these in the CloudWatch console against the Lambda's log group
(`/aws/lambda/tally-backend`) for endpoint/latency/region/time-of-day breakdowns:

```
# Endpoint popularity
fields path, method
| stats count(*) as hits by path, method
| sort hits desc

# Latency by endpoint (p50/p95)
fields path, duration_ms
| stats pct(duration_ms, 50) as p50, pct(duration_ms, 95) as p95, count(*) as hits by path
| sort hits desc

# Region distribution
fields viewer_country
| stats count(*) as hits by viewer_country
| sort hits desc

# Time-of-day pattern (hour bucket, UTC)
fields @timestamp
| stats count(*) as hits by bin(1h)
```

## Deliberately deferred

- **A local Metabase container** - if the terminal report/raw SQL stops being enough and
  charts are worth the extra moving part, `docker compose` a `metabase/metabase` container
  pointed at the same `DATABASE_URL_READONLY`, connected via Metabase's own onboarding UI
  (no code - it stores its own dashboards/questions in its internal metadata DB). Zero AWS
  cost since nothing gets deployed; just an extra local container to run when you want to
  look.
- **An AWS-hosted, admin-only dashboard** - an IAM-authorizer-gated Lambda + API Gateway
  route, restricted to admin AWS accounts, so metrics are visible without your laptop.
  Free-tier cost (no always-on resource), but real setup - treated as a phase 2, not part
  of the initial build.
- **Per-request event storage in Postgres** - endpoint/geo/time-of-day intentionally stay
  in CloudWatch logs rather than a Postgres events table, to avoid a DB write on every
  request. Revisit only if CloudWatch Logs Insights query costs or retention become a
  problem at higher traffic than a solo-developer app sees.
