"""
Pairs Trading Strategy API Endpoints

Real implementations backed by the strategy_engine DB schema.
All endpoints read from PairRegistry, PairTrade, PairPerformance,
PairSpread, PairSignal, and BacktestRun tables.
"""

import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import yaml  # type: ignore
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...services.risk_management.portfolio_risk_manager import PortfolioRiskManager
from ...shared.database.base import db_readonly_session, db_transaction
from ...shared.database.models.strategy_models import (
    BacktestRun,
    PairPerformance,
    PairRegistry,
    PairSignal,
    PairSpread,
    PairTrade,
)
from ...shared.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/strategies/pairs", tags=["pairs-trading"])


# ---------------------------------------------------------------------------
# Pydantic models (kept compatible with existing Streamlit client)
# ---------------------------------------------------------------------------


class DrawdownThresholdRequest(BaseModel):
    threshold: float


class PairConfig(BaseModel):
    entry_threshold: float = 2.0
    exit_threshold: float = 0.5
    stop_loss_threshold: float = 3.0
    position_size: float = 0.05
    lookback_period: int = 252
    max_active_pairs: int = 6
    max_drawdown_limit: float = 0.08
    max_daily_loss: float = 0.03
    max_sector_exposure: float = 0.4
    rebalance_frequency: str = "daily"


class BacktestConfig(BaseModel):
    pair_id: int
    start_date: str
    end_date: str
    initial_capital: float = 100_000
    entry_threshold: float = 2.0
    exit_threshold: float = 0.5
    stop_loss_threshold: float = 3.0


class PairData(BaseModel):
    id: str
    name: str
    symbol1: str
    symbol2: str
    status: str
    z_score: Optional[float]
    pnl: float
    correlation: float
    days_held: Optional[int]
    entry_price1: Optional[float] = None
    entry_price2: Optional[float] = None
    current_price1: Optional[float] = None
    current_price2: Optional[float] = None


class PerformanceData(BaseModel):
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    active_pairs: int
    avg_hold_time: float
    performance_history: Optional[List[Dict]] = None
    drawdown_history: Optional[List[Dict]] = None
    monthly_returns: Optional[List[Dict]] = None


class StrategyStatus(BaseModel):
    is_active: bool
    last_update: datetime
    total_pairs: int
    active_pairs: int
    total_pnl: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_strategy_config() -> Dict[str, Any]:
    config_path = os.path.join(
        os.path.dirname(__file__), "../../../config/strategies.yaml"
    )
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _latest_z_score(pair_id: int) -> Optional[float]:
    """Return the most recent z-score for a pair."""
    with db_readonly_session() as session:
        row = (
            session.query(PairSpread.z_score)
            .filter(PairSpread.pair_id == pair_id)
            .order_by(PairSpread.timestamp.desc())
            .first()
        )
    return float(row[0]) if row and row[0] is not None else None


def _open_trade(pair_id: int) -> Optional[PairTrade]:
    with db_readonly_session() as session:
        trade = (
            session.query(PairTrade)
            .filter(PairTrade.pair_id == pair_id, PairTrade.status == "OPEN")
            .order_by(PairTrade.entry_time.desc())
            .first()
        )
        if trade:
            session.expunge(trade)
        return trade


def _latest_prices(pair_id: int) -> Tuple[Optional[float], Optional[float]]:
    """Return (price1, price2) from the most recent PairSpread row."""
    with db_readonly_session() as session:
        row = (
            session.query(PairSpread.price1, PairSpread.price2)
            .filter(PairSpread.pair_id == pair_id)
            .order_by(PairSpread.timestamp.desc())
            .first()
        )
    if row:
        return (
            float(row[0]) if row[0] is not None else None,
            float(row[1]) if row[1] is not None else None,
        )
    return None, None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/active", response_model=Dict[str, List[PairData]])
async def get_active_pairs() -> Dict[str, List[PairData]]:
    """Return active pairs with latest z-score and open trade info."""
    try:
        with db_readonly_session() as session:
            pairs = (
                session.query(PairRegistry)
                .filter(PairRegistry.is_active.is_(True))
                .all()
            )
            for p in pairs:
                session.expunge(p)

        result = []
        for pair in pairs:
            z = _latest_z_score(pair.id)
            trade = _open_trade(pair.id)
            p1, p2 = _latest_prices(pair.id)

            days_held = None
            entry_p1 = entry_p2 = None
            pnl = 0.0

            if trade:
                if trade.entry_time:
                    days_held = (datetime.utcnow() - trade.entry_time).days
                entry_p1 = float(trade.entry_price1) if trade.entry_price1 else None
                entry_p2 = float(trade.entry_price2) if trade.entry_price2 else None
                pnl = float(trade.pnl) if trade.pnl else 0.0

            result.append(
                PairData(
                    id=str(pair.id),
                    name=f"{pair.symbol1}/{pair.symbol2}",
                    symbol1=pair.symbol1,
                    symbol2=pair.symbol2,
                    status="in_trade" if trade else "watching",
                    z_score=z,
                    pnl=pnl,
                    correlation=float(pair.correlation) if pair.correlation else 0.0,
                    days_held=days_held,
                    entry_price1=entry_p1,
                    entry_price2=entry_p2,
                    current_price1=p1,
                    current_price2=p2,
                )
            )

        return {"pairs": result}

    except Exception as e:
        logger.error(f"Error getting active pairs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active pairs")


@router.get("/performance", response_model=PerformanceData)
async def get_performance_data() -> PerformanceData:
    """Aggregate performance across all pairs from PairPerformance table."""
    try:
        today = date.today()

        with db_readonly_session() as session:
            perf_rows = (
                session.query(PairPerformance)
                .filter(PairPerformance.date == today)
                .all()
            )
            for r in perf_rows:
                session.expunge(r)

            # Count active pairs
            active_count = (
                session.query(PairRegistry)
                .filter(PairRegistry.is_active.is_(True))
                .count()
            )

        if not perf_rows:
            return PerformanceData(
                total_pnl=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                active_pairs=active_count,
                avg_hold_time=0.0,
            )

        total_pnl = sum(float(r.total_pnl or 0) for r in perf_rows)
        avg_sharpe = sum(float(r.sharpe or 0) for r in perf_rows) / len(perf_rows)
        avg_dd = sum(float(r.max_drawdown or 0) for r in perf_rows) / len(perf_rows)
        win_rates = [float(r.win_rate or 0) for r in perf_rows if r.win_rate]
        avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0.0
        hold_times = [
            float(r.avg_hold_hours or 0) for r in perf_rows if r.avg_hold_hours
        ]
        avg_hold = sum(hold_times) / len(hold_times) if hold_times else 0.0

        return PerformanceData(
            total_pnl=total_pnl,
            sharpe_ratio=avg_sharpe,
            max_drawdown=avg_dd,
            win_rate=avg_win_rate,
            active_pairs=active_count,
            avg_hold_time=avg_hold,
        )

    except Exception as e:
        logger.error(f"Error getting performance data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance data")


@router.get("/status", response_model=StrategyStatus)
async def get_strategy_status() -> StrategyStatus:
    """Return strategy status from PairRegistry."""
    try:
        with db_readonly_session() as session:
            total = session.query(PairRegistry).count()
            active = (
                session.query(PairRegistry)
                .filter(PairRegistry.is_active.is_(True))
                .count()
            )
            perf = (
                session.query(PairPerformance)
                .filter(PairPerformance.date == date.today())
                .all()
            )

        total_pnl = sum(float(r.total_pnl or 0) for r in perf)
        last_update = datetime.utcnow()

        return StrategyStatus(
            is_active=active > 0,
            last_update=last_update,
            total_pairs=total,
            active_pairs=active,
            total_pnl=total_pnl,
        )

    except Exception as e:
        logger.error(f"Error getting strategy status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get strategy status")


@router.get("/config", response_model=PairConfig)
async def get_configuration() -> PairConfig:
    """Return strategy config from YAML (unchanged from original)."""
    try:
        cfg = _load_strategy_config()
        pairs_strategy = next(
            (
                s
                for s in cfg.get("strategies", [])
                if s.get("name") == "pairs_trading_strategy"
            ),
            None,
        )
        if not pairs_strategy:
            return PairConfig()

        params = pairs_strategy.get("parameters", {})
        risk = pairs_strategy.get("risk_limits", {})
        return PairConfig(
            entry_threshold=params.get("entry_threshold", 2.0),
            exit_threshold=params.get("exit_threshold", 0.5),
            stop_loss_threshold=params.get("stop_loss_threshold", 3.0),
            position_size=params.get("position_size", 0.05),
            lookback_period=params.get("lookback_period", 252),
            max_active_pairs=risk.get("max_positions", 6),
            max_drawdown_limit=risk.get("max_drawdown", 0.08),
            max_daily_loss=risk.get("max_daily_loss", 0.03),
            max_sector_exposure=risk.get("max_sector_exposure", 0.4),
            rebalance_frequency=params.get("rebalance_frequency", "daily"),
        )
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to get configuration")


@router.post("/config")
async def save_configuration(config: PairConfig) -> Dict[str, str]:
    """Save strategy configuration to YAML (unchanged from original)."""
    try:
        cfg = _load_strategy_config()
        for strategy in cfg.get("strategies", []):
            if strategy.get("name") == "pairs_trading_strategy":
                strategy.setdefault("parameters", {}).update(
                    {
                        "entry_threshold": config.entry_threshold,
                        "exit_threshold": config.exit_threshold,
                        "stop_loss_threshold": config.stop_loss_threshold,
                        "position_size": config.position_size,
                        "lookback_period": config.lookback_period,
                        "rebalance_frequency": config.rebalance_frequency,
                    }
                )
                strategy.setdefault("risk_limits", {}).update(
                    {
                        "max_positions": config.max_active_pairs,
                        "max_drawdown": config.max_drawdown_limit,
                        "max_daily_loss": config.max_daily_loss,
                        "max_sector_exposure": config.max_sector_exposure,
                    }
                )
                break

        config_path = os.path.join(
            os.path.dirname(__file__), "../../../config/strategies.yaml"
        )
        with open(config_path, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False)

        return {"message": "Configuration saved successfully"}
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to save configuration")


@router.post("/start")
async def start_strategy() -> Dict[str, str]:
    """Mark all registered pairs as active."""
    try:
        with db_transaction() as session:
            session.query(PairRegistry).update({"is_active": True})
        logger.info("Pairs trading strategy activated")
        return {"message": "Strategy started successfully", "status": "active"}
    except Exception as e:
        logger.error(f"Error starting strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to start strategy")


@router.post("/stop")
async def stop_strategy() -> Dict[str, str]:
    """Mark all pairs as inactive."""
    try:
        with db_transaction() as session:
            session.query(PairRegistry).update({"is_active": False})
        logger.info("Pairs trading strategy deactivated")
        return {"message": "Strategy stopped successfully", "status": "inactive"}
    except Exception as e:
        logger.error(f"Error stopping strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop strategy")


@router.post("/emergency-stop")
async def emergency_stop() -> Dict[str, str]:
    """Close all open trades via Alpaca and mark pairs inactive."""
    try:
        from src.services.alpaca.client import AlpacaClient
        from src.services.strategy_engine.pairs.pair_executor import PairExecutor

        alpaca = AlpacaClient(is_paper=True)

        with db_readonly_session() as session:
            pairs = (
                session.query(PairRegistry)
                .filter(PairRegistry.is_active.is_(True))
                .all()
            )
            for p in pairs:
                session.expunge(p)

        import asyncio

        for pair in pairs:
            executor = PairExecutor(pair, alpaca)
            await executor.emergency_stop()

        with db_transaction() as session:
            session.query(PairRegistry).update({"is_active": False})

        logger.warning("Emergency stop executed for all pairs")
        return {"message": "Emergency stop executed successfully"}

    except Exception as e:
        logger.error(f"Error executing emergency stop: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute emergency stop")


@router.get("/{pair_id}/history")
async def get_pair_history(pair_id: int, days: int = 30) -> Dict[str, Any]:
    """Return PairSpread rows for the requested date range."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)

        with db_readonly_session() as session:
            pair = session.query(PairRegistry).filter_by(id=pair_id).first()
            if pair is None:
                raise HTTPException(status_code=404, detail="Pair not found")

            rows = (
                session.query(PairSpread)
                .filter(
                    PairSpread.pair_id == pair_id,
                    PairSpread.timestamp >= cutoff,
                )
                .order_by(PairSpread.timestamp)
                .all()
            )
            entry_thr = float(pair.entry_threshold)
            exit_thr = float(pair.exit_threshold)

        history = [
            {
                "timestamp": int(r.timestamp.timestamp() * 1000),
                "spread": float(r.spread) if r.spread is not None else None,
                "z_score": float(r.z_score) if r.z_score is not None else None,
                "price1": float(r.price1) if r.price1 is not None else None,
                "price2": float(r.price2) if r.price2 is not None else None,
            }
            for r in rows
        ]

        return {
            "pair_id": pair_id,
            "history": history,
            "entry_threshold": entry_thr,
            "exit_threshold": exit_thr,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pair history for {pair_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pair history")


@router.get("/{pair_id}/details")
async def get_pair_details(pair_id: int) -> Dict[str, Any]:
    """Return PairRegistry + latest signal for a pair."""
    try:
        with db_readonly_session() as session:
            pair = session.query(PairRegistry).filter_by(id=pair_id).first()
            if pair is None:
                raise HTTPException(status_code=404, detail="Pair not found")
            session.expunge(pair)

            latest_sig = (
                session.query(PairSignal)
                .filter(PairSignal.pair_id == pair_id)
                .order_by(PairSignal.timestamp.desc())
                .first()
            )
            if latest_sig:
                session.expunge(latest_sig)

        trade = _open_trade(pair_id)
        z = _latest_z_score(pair_id)

        return {
            "id": pair.id,
            "symbol1": pair.symbol1,
            "symbol2": pair.symbol2,
            "sector": pair.sector,
            "correlation": float(pair.correlation) if pair.correlation else None,
            "cointegration_pvalue": (
                float(pair.coint_pvalue) if pair.coint_pvalue else None
            ),
            "half_life": float(pair.half_life_hours) if pair.half_life_hours else None,
            "hedge_ratio": float(pair.hedge_ratio),
            "z_score_window": pair.z_score_window,
            "entry_threshold": float(pair.entry_threshold),
            "exit_threshold": float(pair.exit_threshold),
            "stop_loss_threshold": float(pair.stop_loss_threshold),
            "is_active": pair.is_active,
            "last_validated": (
                pair.last_validated.isoformat() if pair.last_validated else None
            ),
            "current_z_score": z,
            "open_trade": trade.to_dict() if trade else None,
            "last_signal": (
                {
                    "type": latest_sig.signal_type,
                    "z_score": (
                        float(latest_sig.z_score) if latest_sig.z_score else None
                    ),
                    "timestamp": latest_sig.timestamp.isoformat(),
                    "reason": latest_sig.reason,
                }
                if latest_sig
                else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pair details for {pair_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pair details")


@router.get("/{pair_id}/sparkline")
async def get_pair_sparkline(pair_id: int, points: int = 48) -> Dict[str, Any]:
    """Return last N z-score data points for sparkline rendering."""
    try:
        with db_readonly_session() as session:
            pair = session.query(PairRegistry).filter_by(id=pair_id).first()
            if pair is None:
                raise HTTPException(status_code=404, detail="Pair not found")
            rows = (
                session.query(PairSpread.timestamp, PairSpread.z_score)
                .filter(
                    PairSpread.pair_id == pair_id,
                    PairSpread.z_score.isnot(None),
                )
                .order_by(PairSpread.timestamp.desc())
                .limit(points)
                .all()
            )
        data = [
            {"t": int(r.timestamp.timestamp() * 1000), "z": float(r.z_score)}
            for r in reversed(rows)
        ]
        return {"pair_id": pair_id, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sparkline for pair {pair_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sparkline data")


@router.post("/{pair_id}/close")
async def close_pair(pair_id: int) -> Dict[str, str]:
    """Manually close an open trade for a pair."""
    try:
        trade = _open_trade(pair_id)
        if trade is None:
            return {"message": f"No open trade for pair {pair_id}"}

        from src.services.alpaca.client import AlpacaClient
        from src.services.strategy_engine.pairs.pair_executor import PairExecutor

        with db_readonly_session() as session:
            pair = session.query(PairRegistry).filter_by(id=pair_id).first()
            if pair is None:
                raise HTTPException(status_code=404, detail="Pair not found")
            session.expunge(pair)

        alpaca = AlpacaClient(is_paper=True)
        executor = PairExecutor(pair, alpaca)
        await executor.close_pair_trade(trade, exit_reason="MANUAL_CLOSE")

        return {"message": f"Pair {pair_id} closed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing pair {pair_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to close pair")


@router.post("/backtest")
async def run_backtest(config: BacktestConfig) -> Dict[str, Any]:
    """Run BacktestEngine and return metrics + equity curve."""
    try:
        from datetime import date as date_type

        from src.services.strategy_engine.backtesting.engine import BacktestEngine
        from src.services.strategy_engine.backtesting.metrics import MetricsCalculator
        from src.services.strategy_engine.backtesting.report import BacktestReport

        with db_readonly_session() as session:
            pair = session.query(PairRegistry).filter_by(id=config.pair_id).first()
            if pair is None:
                raise HTTPException(status_code=404, detail="Pair not found")
            # Override thresholds with request values
            pair.entry_threshold = config.entry_threshold
            pair.exit_threshold = config.exit_threshold
            pair.stop_loss_threshold = config.stop_loss_threshold
            session.expunge(pair)

        start = datetime.strptime(config.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(config.end_date, "%Y-%m-%d").date()

        engine = BacktestEngine(
            pair=pair,
            start_date=start,
            end_date=end,
            initial_capital=config.initial_capital,
        )
        result = engine.run()
        metrics = MetricsCalculator().compute(result)
        run_id = BacktestReport().save(result, metrics)

        return {
            "run_id": run_id,
            "passed_gate": metrics.passed_gate,
            **metrics.to_dict(),
            "equity_curve": result.equity_curve,
            "trade_log": [
                {
                    "side": t.side,
                    "entry_time": t.entry_time.isoformat() if t.entry_time else None,
                    "exit_time": t.exit_time.isoformat() if t.exit_time else None,
                    "pnl": t.pnl,
                    "pnl_pct": t.pnl_pct,
                    "hold_hours": t.hold_hours,
                    "exit_reason": t.exit_reason,
                }
                for t in result.trades
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {e}")


@router.get("/backtest/history")
async def get_backtest_history(pair_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return list of BacktestRun records."""
    try:
        with db_readonly_session() as session:
            q = session.query(BacktestRun)
            if pair_id is not None:
                q = q.filter(BacktestRun.pair_id == pair_id)
            runs = q.order_by(BacktestRun.run_date.desc()).limit(50).all()
            return [r.to_dict() for r in runs]
    except Exception as e:
        logger.error(f"Error getting backtest history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backtest history")


# ---------------------------------------------------------------------------
# Risk controls
# ---------------------------------------------------------------------------


@router.get("/risk")
async def get_risk_state() -> Dict[str, Any]:
    """Return current portfolio risk state (circuit breaker, drawdown, peak equity)."""
    try:
        state = PortfolioRiskManager().get_state()
        if state is None:
            return {
                "peak_equity": None,
                "circuit_breaker_active": False,
                "circuit_breaker_triggered_at": None,
                "drawdown_threshold": 0.05,
                "updated_at": None,
            }
        return state
    except Exception as e:
        logger.error(f"Error getting risk state: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk state")


@router.post("/risk/reset-circuit-breaker")
async def reset_circuit_breaker() -> Dict[str, str]:
    """Manually reset the portfolio drawdown circuit breaker."""
    try:
        PortfolioRiskManager().reset_circuit_breaker()
        return {"message": "Circuit breaker reset"}
    except Exception as e:
        logger.error(f"Error resetting circuit breaker: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset circuit breaker")


@router.put("/risk/threshold")
async def update_drawdown_threshold(
    body: DrawdownThresholdRequest,
) -> Dict[str, Any]:
    """Update the portfolio drawdown threshold (0 < threshold < 1)."""
    try:
        PortfolioRiskManager().update_drawdown_threshold(body.threshold)
        return {"message": "Threshold updated", "threshold": body.threshold}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating drawdown threshold: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update drawdown threshold"
        )
