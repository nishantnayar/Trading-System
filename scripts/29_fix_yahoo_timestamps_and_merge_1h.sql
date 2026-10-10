-- Migration 29: fix Yahoo bar timestamps, merge yahoo_adjusted_1h, basket pnl_pct units
--
-- 1. YahooClient.get_historical_data() used .replace(tzinfo=utc) on yfinance's
--    America/New_York index, so every 'yahoo' / 'yahoo_adjusted' bar was stored
--    with its ET wall-clock time labelled as UTC (4h early in EDT, 5h in EST).
--    Real session bars open 09:30-15:30 ET = 13:30-20:30 UTC; mislabelled rows
--    sit at 09:30-15:30 UTC. A day is "old-style" if it has any :30 row at
--    09:30-12:30 UTC (impossible for a correctly stored bar). Every :30 row
--    09:30-15:30 UTC on an old-style day is re-stamped as
--    (wall clock) AT TIME ZONE 'America/New_York' - DST aware.
--    Rows are deleted and re-inserted (an in-place UPDATE would trip the
--    (symbol, timestamp, data_source) unique index mid-statement as bars move
--    onto slots other bars are vacating). If a re-stamped bar lands on a slot
--    that already holds a correctly stored bar, the existing row is kept.
--    Daily (midnight) rows and correctly stored days are not touched.
--
-- 2. yahoo_adjusted_1h duplicated yahoo_adjusted for active pair symbols
--    (99.8% identical closes once timestamps are aligned). Copy any bars that
--    only exist there into yahoo_adjusted, then delete the label's rows.
--    The CHECK constraint still allows the value; nothing writes it any more.
--
-- 3. basket_trade.pnl_pct was stored as a fraction; pair_trade stores a
--    percentage. Convert rows closed before this migration to percentages.
--
-- Prerequisites: migration 28, a fresh pg_dump, and no Prefect flow running.
-- Run outside market hours. Follow with: VACUUM ANALYZE data_ingestion.market_data;

BEGIN;

-- ---------------------------------------------------------------- 1. timestamps
CREATE TEMP TABLE md_shift ON COMMIT DROP AS
WITH r AS (
    SELECT m.*, (m.timestamp AT TIME ZONE 'UTC') AS wall
    FROM data_ingestion.market_data m
    WHERE m.data_source IN ('yahoo', 'yahoo_adjusted')
),
old_days AS (
    SELECT DISTINCT symbol, data_source, wall::date AS d
    FROM r
    WHERE extract(minute FROM wall) = 30
      AND wall::time BETWEEN '09:30' AND '12:30'
)
SELECT r.id, r.symbol, r.data_source, r.open, r.high, r.low, r.close, r.volume,
       r.created_at,
       (r.wall AT TIME ZONE 'America/New_York') AS new_ts
FROM r
JOIN old_days o
  ON o.symbol = r.symbol AND o.data_source = r.data_source AND o.d = r.wall::date
WHERE extract(minute FROM r.wall) = 30
  AND r.wall::time BETWEEN '09:30' AND '15:30';

DELETE FROM data_ingestion.market_data m
USING md_shift s
WHERE m.id = s.id;

INSERT INTO data_ingestion.market_data
    (id, symbol, timestamp, open, high, low, close, volume, created_at, data_source)
SELECT id, symbol, new_ts, open, high, low, close, volume, created_at, data_source
FROM md_shift
ON CONFLICT (symbol, timestamp, data_source) DO NOTHING;

-- ------------------------------------------------------ 2. merge yahoo_adjusted_1h
INSERT INTO data_ingestion.market_data
    (symbol, timestamp, open, high, low, close, volume, created_at, data_source)
SELECT symbol, timestamp, open, high, low, close, volume, created_at, 'yahoo_adjusted'
FROM data_ingestion.market_data
WHERE data_source = 'yahoo_adjusted_1h'
ON CONFLICT (symbol, timestamp, data_source) DO NOTHING;

DELETE FROM data_ingestion.market_data WHERE data_source = 'yahoo_adjusted_1h';

-- -------------------------------------------------- 3. basket pnl_pct -> percent
UPDATE strategy_engine.basket_trade
SET pnl_pct = pnl_pct * 100
WHERE pnl_pct IS NOT NULL
  AND exit_time < TIMESTAMPTZ '2026-10-10 00:00:00+00';

COMMIT;
