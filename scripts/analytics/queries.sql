-- Usage-analytics queries for Tally.
--
-- Run against DATABASE_URL_READONLY (see .secrets.example) - these are all
-- read-only. `scripts/analytics/report.py` runs the ones below programmatically
-- and prints a summary; copy any of these into `psql`, a notebook, or a BI
-- tool (e.g. a local Metabase pointed at the same read-only URL) directly.
--
-- Endpoint popularity / latency / time-of-day / region breakdowns are NOT
-- here - that data lives in CloudWatch (the JSON access log emitted by
-- backend/src/core/logging.py), not Postgres. See docs/ANALYTICS.md for the
-- companion CloudWatch Logs Insights queries.

-- name: total_users
-- Total registered users.
SELECT count(*) AS total_users FROM users;

-- name: dau
-- Distinct users active today (UTC).
SELECT count(DISTINCT user_id) AS dau
FROM user_daily_activity
WHERE activity_date = current_date;

-- name: wau
-- Distinct users active in the trailing 7 days (rolling window, not calendar week).
SELECT count(DISTINCT user_id) AS wau
FROM user_daily_activity
WHERE activity_date > current_date - interval '7 days';

-- name: mau
-- Distinct users active in the trailing 30 days (rolling window).
SELECT count(DISTINCT user_id) AS mau
FROM user_daily_activity
WHERE activity_date > current_date - interval '30 days';

-- name: stickiness
-- DAU/MAU ratio - the standard proxy for "daily habit" vs. "occasional use".
-- Multiply by 100 for a percentage; industry benchmarks for a healthy
-- consumer/finance app are often in the 10-25% range.
SELECT
    (SELECT count(DISTINCT user_id) FROM user_daily_activity
     WHERE activity_date = current_date)::numeric
    / NULLIF((SELECT count(DISTINCT user_id) FROM user_daily_activity
              WHERE activity_date > current_date - interval '30 days'), 0)
    AS stickiness_ratio;

-- name: signup_trend
-- New signups per week, most recent first.
SELECT date_trunc('week', created_at) AS week, count(*) AS signups
FROM users
GROUP BY 1
ORDER BY 1 DESC;

-- name: stale_accounts
-- Users bucketed by days since last activity (or never active at all).
-- "Stale" per Ken's definition = hasn't been used in > 90 days.
SELECT
    CASE
        WHEN last_active IS NULL THEN 'never_active'
        WHEN last_active > current_date - interval '30 days' THEN 'active_last_30d'
        WHEN last_active > current_date - interval '60 days' THEN 'stale_30_60d'
        WHEN last_active > current_date - interval '90 days' THEN 'stale_60_90d'
        ELSE 'stale_90d_plus'
    END AS bucket,
    count(*) AS user_count
FROM (
    SELECT u.id, max(a.activity_date) AS last_active
    FROM users u
    LEFT JOIN user_daily_activity a ON a.user_id = u.id
    GROUP BY u.id
) per_user
GROUP BY 1
ORDER BY 1;

-- name: cohort_retention
-- % of each signup-month cohort still active in each subsequent month.
-- month_offset 0 = signup month itself, 1 = next month, etc.
WITH cohorts AS (
    SELECT id AS user_id, date_trunc('month', created_at) AS cohort_month
    FROM users
),
activity_months AS (
    SELECT DISTINCT user_id, date_trunc('month', activity_date) AS active_month
    FROM user_daily_activity
)
SELECT
    c.cohort_month,
    (extract(year FROM am.active_month) - extract(year FROM c.cohort_month)) * 12
        + (extract(month FROM am.active_month) - extract(month FROM c.cohort_month))
        AS month_offset,
    count(DISTINCT c.user_id) AS active_users
FROM cohorts c
JOIN activity_months am ON am.user_id = c.user_id AND am.active_month >= c.cohort_month
GROUP BY 1, 2
ORDER BY 1, 2;

-- CloudWatch Logs Insights companions (run in the CloudWatch console against
-- the Lambda's log group, not here):
--
-- Endpoint popularity:
--   fields path, method
--   | stats count(*) as hits by path, method
--   | sort hits desc
--
-- Latency by endpoint (p50/p95):
--   fields path, duration_ms
--   | stats pct(duration_ms, 50) as p50, pct(duration_ms, 95) as p95, count(*) as hits by path
--   | sort hits desc
--
-- Region distribution:
--   fields viewer_country
--   | stats count(*) as hits by viewer_country
--   | sort hits desc
--
-- Time-of-day pattern (hour bucket, UTC):
--   fields @timestamp
--   | stats count(*) as hits by bin(1h)
