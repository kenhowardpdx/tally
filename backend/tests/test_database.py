from src.core.database import engine


def test_engine_pre_pings_connections_before_reuse():
    # Without this, a pooled connection that Neon closed server-side while a
    # Lambda container sat idle between invocations gets handed back out
    # as-is, and the next query fails with asyncpg's InterfaceError instead
    # of transparently reconnecting.
    assert engine.pool._pre_ping is True


def test_engine_recycles_connections_before_neon_idle_timeout():
    # Must stay under whatever idle-connection timeout Neon enforces so a
    # pooled connection is proactively replaced before Neon closes it first.
    assert 0 < engine.pool._recycle <= 270
