-- Migration 29b: re-stamp mislabelled Yahoo bars on partial days missed by migration 29
--
-- Migration 29 identified mislabelled days by a :30 row at 09:30-12:30 UTC. Partial
-- days that only hold the last bars of a session (e.g. the first day of a 730-day
-- 1h backfill window, cut mid-session) have rows only at 13:30-15:30 UTC and were
-- left alone, although they are the same ET-wall-clock-as-UTC bug (in EST a correct
-- 13:30 UTC bar would be an impossible 08:30 ET bar).
--
-- Every such row was written before the client fix (all came from the 2026-02-07
-- backfill); neither correct writer (the 2026-04-03 batch, the yahoo_adjusted_1h
-- merge) produced rows on these days. Rows created after the fix are excluded.

BEGIN;

CREATE TEMP TABLE md_shift_partial ON COMMIT DROP AS
WITH r AS (
    SELECT m.*, (m.timestamp AT TIME ZONE 'UTC') AS wall
    FROM data_ingestion.market_data m
    WHERE m.data_source IN ('yahoo', 'yahoo_adjusted')
      AND extract(minute FROM m.timestamp AT TIME ZONE 'UTC') = 30
),
partial_days AS (
    SELECT symbol, data_source, wall::date AS d
    FROM r
    GROUP BY 1, 2, 3
    HAVING MIN(wall::time) >= '13:30' AND MAX(wall::time) < '16:00'
)
SELECT r.id, r.symbol, r.data_source, r.open, r.high, r.low, r.close, r.volume,
       r.created_at,
       (r.wall AT TIME ZONE 'America/New_York') AS new_ts
FROM r
JOIN partial_days p
  ON p.symbol = r.symbol AND p.data_source = r.data_source AND p.d = r.wall::date
WHERE r.created_at < TIMESTAMPTZ '2026-10-09 23:00:00+00';

DELETE FROM data_ingestion.market_data m
USING md_shift_partial s
WHERE m.id = s.id;

INSERT INTO data_ingestion.market_data
    (id, symbol, timestamp, open, high, low, close, volume, created_at, data_source)
SELECT id, symbol, new_ts, open, high, low, close, volume, created_at, data_source
FROM md_shift_partial
ON CONFLICT (symbol, timestamp, data_source) DO NOTHING;

COMMIT;
