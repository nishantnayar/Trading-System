"""
Pairs Trading Strategy API Endpoints

Real implementations backed by the strategy_engine DB schema.
All endpoints read from PairRegistry, PairTrade, PairPerformance,
PairSpread and PairSignal tables.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...services.risk_management.portfolio_risk_manager import PortfolioRiskManager
from ...shared.database.base import db_readonly_session
from ...shared.database.models.strategy_models import (
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
                    days_held = (datetime.now(timezone.utc) - trade.entry_time).days
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
            is_active=PortfolioRiskManager().is_strategy_enabled() and active > 0,
            last_update=last_update,
            total_pairs=total,
            active_pairs=active,
            total_pnl=total_pnl,
        )

    except Exception as e:
        logger.error(f"Error getting strategy status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get strategy status")


@router.post("/start")
async def start_strategy() -> Dict[str, str]:
    """Enable the pairs strategy. Per-pair is_active flags are not touched."""
    try:
        PortfolioRiskManager().set_strategy_enabled(True)
        return {"message": "Strategy started successfully", "status": "active"}
    except Exception as e:
        logger.error(f"Error starting strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to start strategy")


@router.post("/stop")
async def stop_strategy() -> Dict[str, str]:
    """Disable the pairs strategy. Per-pair is_active flags are not touched."""
    try:
        PortfolioRiskManager().set_strategy_enabled(False)
        return {"message": "Strategy stopped successfully", "status": "inactive"}
    except Exception as e:
        logger.error(f"Error stopping strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop strategy")


@router.post("/emergency-stop")
async def emergency_stop() -> Dict[str, str]:
    """Close all open trades via Alpaca and disable the strategy."""
    try:
        from src.services.alpaca.client import AlpacaClient
        from src.services.strategy_engine.pairs.pair_executor import PairExecutor

        alpaca = AlpacaClient()

        with db_readonly_session() as session:
            pairs = (
                session.query(PairRegistry)
                .filter(PairRegistry.is_active.is_(True))
                .all()
            )
            for p in pairs:
                session.expunge(p)

        for pair in pairs:
            executor = PairExecutor(pair, alpaca)
            await executor.emergency_stop()

        PortfolioRiskManager().set_strategy_enabled(False)

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


@router.get("/pnl/trades")
async def get_trade_history(
    pair_id: Optional[int] = None,
    status: Optional[str] = None,
    days: int = 90,
) -> Dict[str, Any]:
    """Return closed trade history with optional filters."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with db_readonly_session() as session:
            q = session.query(PairTrade, PairRegistry).join(
                PairRegistry, PairTrade.pair_id == PairRegistry.id
            )
            if pair_id is not None:
                q = q.filter(PairTrade.pair_id == pair_id)
            if status:
                q = q.filter(PairTrade.status == status.upper())
            else:
                q = q.filter(PairTrade.status.in_(["CLOSED", "STOPPED"]))
            q = q.filter(PairTrade.entry_time >= cutoff)
            rows = q.order_by(PairTrade.entry_time.desc()).all()

        trades = []
        for trade, pair in rows:
            hold_hours = None
            if trade.entry_time and trade.exit_time:
                delta = trade.exit_time - trade.entry_time
                hold_hours = round(delta.total_seconds() / 3600, 1)
            trades.append(
                {
                    "id": trade.id,
                    "pair_id": trade.pair_id,
                    "pair_name": f"{pair.symbol1}/{pair.symbol2}",
                    "symbol1": pair.symbol1,
                    "symbol2": pair.symbol2,
                    "side": trade.side,
                    "status": trade.status,
                    "entry_time": trade.entry_time.isoformat(),
                    "exit_time": (
                        trade.exit_time.isoformat() if trade.exit_time else None
                    ),
                    "entry_z_score": (
                        float(trade.entry_z_score) if trade.entry_z_score else None
                    ),
                    "exit_z_score": (
                        float(trade.exit_z_score) if trade.exit_z_score else None
                    ),
                    "qty1": trade.qty1,
                    "qty2": trade.qty2,
                    "entry_price1": (
                        float(trade.entry_price1) if trade.entry_price1 else None
                    ),
                    "entry_price2": (
                        float(trade.entry_price2) if trade.entry_price2 else None
                    ),
                    "exit_price1": (
                        float(trade.exit_price1) if trade.exit_price1 else None
                    ),
                    "exit_price2": (
                        float(trade.exit_price2) if trade.exit_price2 else None
                    ),
                    "pnl": float(trade.pnl) if trade.pnl is not None else None,
                    "pnl_pct": (
                        float(trade.pnl_pct) if trade.pnl_pct is not None else None
                    ),
                    "exit_reason": trade.exit_reason,
                    "hold_hours": hold_hours,
                }
            )
        return {"trades": trades, "count": len(trades)}
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trade history")


@router.get("/pnl/daily")
async def get_daily_pnl(days: int = 90) -> Dict[str, Any]:
    """Return daily realized P&L by aggregating closed trades per calendar date."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with db_readonly_session() as session:
            rows = (
                session.query(PairTrade)
                .filter(
                    PairTrade.status.in_(["CLOSED", "STOPPED"]),
                    PairTrade.exit_time >= cutoff,
                    PairTrade.pnl.isnot(None),
                )
                .order_by(PairTrade.exit_time)
                .all()
            )
            for r in rows:
                session.expunge(r)

        from collections import defaultdict

        daily: Dict[str, float] = defaultdict(float)
        for trade in rows:
            if trade.exit_time:
                day = trade.exit_time.strftime("%Y-%m-%d")
                daily[day] += float(trade.pnl or 0)

        # build cumulative series
        sorted_days = sorted(daily.keys())
        cumulative = 0.0
        series = []
        for day in sorted_days:
            cumulative += daily[day]
            series.append(
                {
                    "date": day,
                    "daily_pnl": round(daily[day], 4),
                    "cumulative_pnl": round(cumulative, 4),
                }
            )
        return {"series": series}
    except Exception as e:
        logger.error(f"Error getting daily P&L: {e}")
        raise HTTPException(status_code=500, detail="Failed to get daily P&L")


@router.get("/pnl/summary")
async def get_pnl_summary() -> Dict[str, Any]:
    """Return all-time P&L totals and per-pair attribution from closed trades."""
    try:
        with db_readonly_session() as session:
            closed = (
                session.query(PairTrade, PairRegistry)
                .join(PairRegistry, PairTrade.pair_id == PairRegistry.id)
                .filter(
                    PairTrade.status.in_(["CLOSED", "STOPPED"]),
                    PairTrade.pnl.isnot(None),
                )
                .all()
            )

        from collections import defaultdict

        pair_stats: Dict[str, Dict] = defaultdict(
            lambda: {
                "total_pnl": 0.0,
                "trade_count": 0,
                "winning": 0,
                "pnl_pcts": [],
                "hold_hours": [],
                "stop_losses": 0,
            }
        )
        total_pnl = 0.0
        total_trades = 0
        winning_trades = 0
        all_pnl_pcts = []

        for trade, pair in closed:
            key = f"{pair.symbol1}/{pair.symbol2}"
            pnl = float(trade.pnl)
            total_pnl += pnl
            total_trades += 1
            pair_stats[key]["total_pnl"] += pnl
            pair_stats[key]["trade_count"] += 1
            if pnl > 0:
                winning_trades += 1
                pair_stats[key]["winning"] += 1
            if trade.pnl_pct is not None:
                all_pnl_pcts.append(float(trade.pnl_pct))
                pair_stats[key]["pnl_pcts"].append(float(trade.pnl_pct))
            if trade.entry_time and trade.exit_time:
                h = (trade.exit_time - trade.entry_time).total_seconds() / 3600
                pair_stats[key]["hold_hours"].append(h)
            if trade.exit_reason in ("STOP_LOSS",):
                pair_stats[key]["stop_losses"] += 1

        per_pair = []
        for name, s in pair_stats.items():
            avg_pnl_pct = (
                sum(s["pnl_pcts"]) / len(s["pnl_pcts"]) if s["pnl_pcts"] else None
            )
            avg_hold = (
                round(sum(s["hold_hours"]) / len(s["hold_hours"]), 1)
                if s["hold_hours"]
                else None
            )
            per_pair.append(
                {
                    "pair": name,
                    "total_pnl": round(s["total_pnl"], 4),
                    "trade_count": s["trade_count"],
                    "win_rate": (
                        round(s["winning"] / s["trade_count"], 4)
                        if s["trade_count"]
                        else 0.0
                    ),
                    "avg_pnl_pct": round(avg_pnl_pct, 4) if avg_pnl_pct else None,
                    "avg_hold_hours": avg_hold,
                    "stop_losses": s["stop_losses"],
                }
            )
        per_pair.sort(key=lambda x: x["total_pnl"], reverse=True)

        win_rate = winning_trades / total_trades if total_trades else 0.0
        avg_pnl_pct = sum(all_pnl_pcts) / len(all_pnl_pcts) if all_pnl_pcts else 0.0
        profit_factor = None
        wins = [p for p in all_pnl_pcts if p > 0]
        losses = [p for p in all_pnl_pcts if p < 0]
        if losses:
            profit_factor = round(sum(wins) / abs(sum(losses)), 4) if wins else 0.0

        return {
            "total_pnl": round(total_pnl, 4),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate": round(win_rate, 4),
            "avg_pnl_pct": round(avg_pnl_pct, 4),
            "profit_factor": profit_factor,
            "per_pair": per_pair,
        }
    except Exception as e:
        logger.error(f"Error getting P&L summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get P&L summary")


@router.get("/pnl/monthly")
async def get_monthly_pnl() -> Dict[str, Any]:
    """Return month-over-month P&L breakdown from closed trades."""
    try:
        with db_readonly_session() as session:
            rows = (
                session.query(PairTrade, PairRegistry)
                .join(PairRegistry, PairTrade.pair_id == PairRegistry.id)
                .filter(
                    PairTrade.status.in_(["CLOSED", "STOPPED"]),
                    PairTrade.pnl.isnot(None),
                    PairTrade.exit_time.isnot(None),
                )
                .order_by(PairTrade.exit_time)
                .all()
            )

        from collections import defaultdict

        # month -> pair -> pnl list
        monthly: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        monthly_counts: Dict[str, int] = defaultdict(int)
        monthly_wins: Dict[str, int] = defaultdict(int)

        for trade, pair in rows:
            month = trade.exit_time.strftime("%Y-%m")
            key = f"{pair.symbol1}/{pair.symbol2}"
            pnl = float(trade.pnl)
            monthly[month][key] += pnl
            monthly_counts[month] += 1
            if pnl > 0:
                monthly_wins[month] += 1

        result = []
        for month in sorted(monthly.keys()):
            total = sum(monthly[month].values())
            result.append(
                {
                    "month": month,
                    "total_pnl": round(total, 4),
                    "trade_count": monthly_counts[month],
                    "win_rate": (
                        round(monthly_wins[month] / monthly_counts[month], 4)
                        if monthly_counts[month]
                        else 0.0
                    ),
                    "by_pair": {k: round(v, 4) for k, v in monthly[month].items()},
                }
            )
        return {"monthly": result}
    except Exception as e:
        logger.error(f"Error getting monthly P&L: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monthly P&L")


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
