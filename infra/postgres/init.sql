-- Postgres initialisation hook. Runs once on first container start
-- (because the data volume is empty). Subsequent starts skip this.
--
-- Phase 1 will add an alembic migration directory; this file only enables
-- the pgvector extension so the migration can create vector columns.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
