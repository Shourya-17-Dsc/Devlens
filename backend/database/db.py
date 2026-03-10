"""
Database Layer (Supabase / PostgreSQL)
========================================
Provides async helpers to persist and retrieve analysis results.

Uses supabase-py client. The SUPABASE_URL and SUPABASE_KEY
environment variables must be set.

Table schema (run in Supabase SQL editor):
  CREATE TABLE analyses (
      id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      username      TEXT NOT NULL,
      skill_score   FLOAT,
      feature_vector JSONB,
      result_json   JSONB,
      created_at    TIMESTAMPTZ DEFAULT now()
  );
  CREATE INDEX idx_analyses_username ON analyses(username);
"""

import os, logging, json
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)
CACHE_TTL_HOURS = 6   # re-analyse if last result is older than this

try:
    from supabase import create_client, Client
    _supabase: Client | None = create_client(
        os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    logger.info("Supabase client initialised")
except Exception as exc:
    _supabase = None
    logger.warning("Supabase not configured (%s) — running without DB", exc)


async def save_analysis(result: dict) -> None:
    """Upsert an analysis result into the analyses table."""
    if _supabase is None:
        return
    try:
        row = {
            "username":       result["username"],
            "skill_score":    result["skill_score"],
            "feature_vector": json.dumps(result.get("features", {})),
            "result_json":    json.dumps(result),
        }
        (_supabase.table("analyses").upsert(row, on_conflict="username").execute())
        logger.info("Saved analysis for '%s'", result["username"])
    except Exception as exc:
        logger.error("DB save failed: %s", exc)


async def get_cached_analysis(username: str) -> dict | None:
    """Return a cached result if it exists and is fresher than CACHE_TTL_HOURS."""
    if _supabase is None:
        return None
    try:
        resp = (
            _supabase.table("analyses")
            .select("result_json, created_at")
            .eq("username", username)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None

        row = resp.data[0]
        created = datetime.fromisoformat(row["created_at"])
        age = datetime.now(timezone.utc) - created.replace(tzinfo=timezone.utc)
        if age < timedelta(hours=CACHE_TTL_HOURS):
            return json.loads(row["result_json"])
        return None          # cache expired
    except Exception as exc:
        logger.error("DB read failed: %s", exc)
        return None
