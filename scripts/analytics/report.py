#!/usr/bin/env python3
"""Prints a terminal summary of Tally usage metrics.

The "local process reading from the remote db" option: reads
TF_VAR_database_url_readonly (or DATABASE_URL_READONLY) from the environment
and runs the named queries in queries.sql against it directly (no app/ORM
dependency).

Usage:
    make analytics-report

    # Equivalent manual form (set -a is required: .secrets uses plain,
    # non-exported shell assignments, so a plain `source .secrets` never
    # makes the variable visible to this script's subprocess - see
    # infra/Makefile's targets for the same pattern):
    set -a && source .secrets && set +a
    poetry -C backend run python scripts/analytics/report.py
"""
import asyncio
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import asyncpg

QUERIES_PATH = Path(__file__).parent / "queries.sql"


def _load_named_queries() -> dict[str, str]:
    text = QUERIES_PATH.read_text()
    blocks = re.split(r"^-- name: (\S+)\n", text, flags=re.MULTILINE)[1:]
    queries = {}
    for name, body in zip(blocks[0::2], blocks[1::2]):
        sql = "\n".join(
            line for line in body.splitlines() if not line.strip().startswith("--")
        ).strip()
        if sql:
            queries[name] = sql.rstrip(";")
    return queries


def _normalize_dsn(dsn: str) -> str:
    # asyncpg's DSN parser doesn't recognize libpq-only params - Neon's
    # connection strings include channel_binding for psycopg clients, and
    # passing it through makes Postgres reject the connection with
    # "unrecognized configuration parameter". Safe to drop: TLS already
    # covers the transport; channel binding is an additional SCRAM
    # enhancement asyncpg doesn't implement.
    parts = urlsplit(dsn)
    params = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    return urlunsplit(parts._replace(query=urlencode(params)))


async def _run(dsn: str) -> None:
    queries = _load_named_queries()
    conn = await asyncpg.connect(_normalize_dsn(dsn))
    try:
        total_users = await conn.fetchval(queries["total_users"])
        dau = await conn.fetchval(queries["dau"])
        wau = await conn.fetchval(queries["wau"])
        mau = await conn.fetchval(queries["mau"])
        stickiness = await conn.fetchval(queries["stickiness"])

        print("Tally usage summary")
        print("====================")
        print(f"Total registered users : {total_users}")
        print(f"DAU                    : {dau}")
        print(f"WAU                    : {wau}")
        print(f"MAU                    : {mau}")
        stickiness_str = f"{stickiness:.1%}" if stickiness is not None else "n/a"
        print(f"Stickiness (DAU/MAU)   : {stickiness_str}")

        print("\nSignups per week (last 8)")
        print("-------------------------")
        for row in (await conn.fetch(queries["signup_trend"]))[:8]:
            print(f"  {row['week'].date()}  {row['signups']:>4}")

        print("\nStale accounts")
        print("--------------")
        for row in await conn.fetch(queries["stale_accounts"]):
            print(f"  {row['bucket']:<18} {row['user_count']:>4}")
    finally:
        await conn.close()


def main() -> None:
    # .secrets sets TF_VAR_database_url_readonly (Terraform's env-var naming
    # convention for auto-loading tfvars) - DATABASE_URL_READONLY is only the
    # name Terraform maps it to as the Lambda's runtime env var, so it's
    # never actually set by `source .secrets`. Check both so this also works
    # if someone exports DATABASE_URL_READONLY directly.
    dsn = os.environ.get("TF_VAR_database_url_readonly") or os.environ.get(
        "DATABASE_URL_READONLY"
    )
    if not dsn:
        print(
            "Neither TF_VAR_database_url_readonly nor DATABASE_URL_READONLY is set - "
            "run `set -a && source .secrets && set +a` first (a plain `source .secrets` "
            "doesn't export it - see .secrets.example).",
            file=sys.stderr,
        )
        sys.exit(1)
    asyncio.run(_run(dsn))


if __name__ == "__main__":
    main()
