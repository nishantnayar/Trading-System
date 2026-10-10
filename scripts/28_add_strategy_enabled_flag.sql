-- Migration 28: global pairs-strategy on/off switch
-- Start/Stop in the Strategy Monitor used to flip pair_registry.is_active on
-- EVERY pair, which re-enabled auto-deactivated pairs on Start and lost the
-- curated active set on Stop. They now toggle this flag instead; per-pair
-- is_active is only changed by discovery, Pair Lab and auto-deactivation.
-- Run once against trading_system DB (idempotent).

ALTER TABLE strategy_engine.portfolio_risk_state
    ADD COLUMN IF NOT EXISTS strategy_enabled BOOLEAN NOT NULL DEFAULT TRUE;

COMMENT ON COLUMN strategy_engine.portfolio_risk_state.strategy_enabled IS
    'Global pairs-strategy switch. FALSE = intraday flow skips the pairs cycle.';
