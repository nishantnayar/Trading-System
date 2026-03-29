"""
Strategy Engine Database Models

SQLAlchemy models for the pairs trading strategy engine.
All models live in the 'strategy_engine' schema.

Models:
    PairRegistry         — validated pair definitions
    PairSpread           — hourly spread/z-score time series
    PairSignal           — generated trading signals
    PairTrade            — open and closed trades
    PairPerformance      — daily cumulative metrics
    BacktestRun          — historical backtest results
    PortfolioRiskState   — single-row portfolio risk state (circuit breaker, peak equity)
"""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.database.base import Base

if TYPE_CHECKING:
    pass


class PairRegistry(Base):
    """
    Validated pair definitions for the pairs trading strategy.

    Populated by scripts/discover_pairs.py after statistical validation.
    Updated periodically to re-validate cointegration relationships.
    """

    __tablename__ = "pair_registry"
    __table_args__ = (
        UniqueConstraint("symbol1", "symbol2", name="uq_pair_registry_symbols"),
        Index("idx_pair_registry_active", "is_active"),
        {"schema": "strategy_engine"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Pair definition
    symbol1: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("data_ingestion.symbols.symbol", ondelete="CASCADE"),
        nullable=False,
    )
    symbol2: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("data_ingestion.symbols.symbol", ondelete="CASCADE"),
        nullable=False,
    )
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    name: Mapped[Optional[str]] = mapped_column(String(100))  # e.g. "AAPL/MSFT"

    # Statistical validation results
    hedge_ratio: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    half_life_hours: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    correlation: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    coint_pvalue: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)

    # Strategy parameters (can be tuned after backtesting)
    z_score_window: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_threshold: Mapped[float] = mapped_column(
        Numeric(5, 2), default=2.0, nullable=False
    )
    exit_threshold: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0.5, nullable=False
    )
    stop_loss_threshold: Mapped[float] = mapped_column(
        Numeric(5, 2), default=3.0, nullable=False
    )
    max_hold_hours: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2)
    )  # 3 × half_life_hours

    # Discovery rank — composite score: (1 - coint_pvalue) × liquidity × |correlation|
    rank_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))

    # Risk controls
    max_allocation_pct: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        comment="Optional per-pair max fraction of portfolio per leg. "
        "Overrides Kelly if lower. NULL = use system default.",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_validated: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    spreads: Mapped[list["PairSpread"]] = relationship(
        "PairSpread", back_populates="pair", cascade="all, delete-orphan"
    )
    signals: Mapped[list["PairSignal"]] = relationship(
        "PairSignal", back_populates="pair", cascade="all, delete-orphan"
    )
    trades: Mapped[list["PairTrade"]] = relationship(
        "PairTrade", back_populates="pair", cascade="all, delete-orphan"
    )
    performance: Mapped[list["PairPerformance"]] = relationship(
        "PairPerformance", back_populates="pair", cascade="all, delete-orphan"
    )
    backtest_runs: Mapped[list["BacktestRun"]] = relationship(
        "BacktestRun", back_populates="pair", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<PairRegistry(id={self.id}, pair={self.symbol1}/{self.symbol2}, "
            f"active={self.is_active}, half_life={self.half_life_hours}h)>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol1": self.symbol1,
            "symbol2": self.symbol2,
            "name": self.name or f"{self.symbol1}/{self.symbol2}",
            "sector": self.sector,
            "hedge_ratio": float(self.hedge_ratio),
            "half_life_hours": float(self.half_life_hours),
            "correlation": float(self.correlation),
            "coint_pvalue": float(self.coint_pvalue),
            "z_score_window": self.z_score_window,
            "entry_threshold": float(self.entry_threshold),
            "exit_threshold": float(self.exit_threshold),
            "stop_loss_threshold": float(self.stop_loss_threshold),
            "max_hold_hours": (
                float(self.max_hold_hours) if self.max_hold_hours else None
            ),
            "max_allocation_pct": (
                float(self.max_allocation_pct) if self.max_allocation_pct else None
            ),
            "is_active": self.is_active,
            "last_validated": (
                self.last_validated.isoformat() if self.last_validated else None
            ),
            "notes": self.notes,
        }


class PairSpread(Base):
    """
    Hourly spread and z-score time series for each pair.

    Written by SpreadCalculator after each live cycle and by BacktestEngine
    during in-memory backtest (not stored for backtests).
    """

    __tablename__ = "pair_spread"
    __table_args__ = (
        Index("idx_pair_spread_pair_timestamp", "pair_id", "timestamp"),
        Index("idx_pair_spread_timestamp", "timestamp"),
        {"schema": "strategy_engine"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pair_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("strategy_engine.pair_registry.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )

    # Prices used
    price1: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))
    price2: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))

    # Spread metrics
    spread: Mapped[Optional[float]] = mapped_column(
        Numeric(15, 8)
    )  # log(P1) - β*log(P2)
    z_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))  # rolling z-score
    hedge_ratio: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))  # β used

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False
    )

    pair: Mapped["PairRegistry"] = relationship(
        "PairRegistry", back_populates="spreads"
    )

    def __repr__(self) -> str:
        return f"<PairSpread(pair_id={self.pair_id}, ts={self.timestamp}, z={self.z_score})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pair_id": self.pair_id,
            "timestamp": self.timestamp.isoformat(),
            "price1": float(self.price1) if self.price1 else None,
            "price2": float(self.price2) if self.price2 else None,
            "spread": float(self.spread) if self.spread else None,
            "z_score": float(self.z_score) if self.z_score else None,
            "hedge_ratio": float(self.hedge_ratio) if self.hedge_ratio else None,
        }


class PairSignal(Base):
    """
    Trading signals generated by SignalGenerator.

    Signal types:
        LONG_SPREAD   — z < -entry_threshold: long symbol1, short symbol2
        SHORT_SPREAD  — z > +entry_threshold: short symbol1, long symbol2
        EXIT          — abs(z) < exit_threshold: close position
        STOP_LOSS     — abs(z) > stop_loss_threshold: emergency close
        EXPIRE        — max hold period exceeded: force close
    """

    __tablename__ = "pair_signal"
    __table_args__ = (
        Index("idx_pair_signal_pair_timestamp", "pair_id", "timestamp"),
        Index("idx_pair_signal_type", "signal_type"),
        {"schema": "strategy_engine"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pair_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("strategy_engine.pair_registry.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )

    signal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    z_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    reason: Mapped[Optional[str]] = mapped_column(String(200))
    acted_on: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False
    )

    pair: Mapped["PairRegistry"] = relationship(
        "PairRegistry", back_populates="signals"
    )

    def __repr__(self) -> str:
        return (
            f"<PairSignal(pair_id={self.pair_id}, type={self.signal_type}, "
            f"z={self.z_score}, ts={self.timestamp})>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pair_id": self.pair_id,
            "timestamp": self.timestamp.isoformat(),
            "signal_type": self.signal_type,
            "z_score": float(self.z_score) if self.z_score else None,
            "reason": self.reason,
            "acted_on": self.acted_on,
        }


class PairTrade(Base):
    """
    Open and closed pairs trades.

    side: 'LONG_SPREAD' or 'SHORT_SPREAD'
    status: 'OPEN', 'CLOSED', 'STOPPED'

    For LONG_SPREAD:  long qty1 shares of symbol1, short qty2 shares of symbol2
    For SHORT_SPREAD: short qty1 shares of symbol1, long qty2 shares of symbol2
    """

    __tablename__ = "pair_trade"
    __table_args__ = (
        Index("idx_pair_trade_pair_status", "pair_id", "status"),
        Index("idx_pair_trade_entry_time", "entry_time"),
        {"schema": "strategy_engine"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pair_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("strategy_engine.pair_registry.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Entry
    entry_time: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    entry_z_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    side: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # LONG_SPREAD / SHORT_SPREAD
    qty1: Mapped[int] = mapped_column(Integer, nullable=False)  # shares of symbol1
    qty2: Mapped[int] = mapped_column(Integer, nullable=False)  # shares of symbol2
    entry_price1: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))
    entry_price2: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))

    # Alpaca order IDs for tracking fills
    order_id1: Mapped[Optional[str]] = mapped_column(String(50))
    order_id2: Mapped[Optional[str]] = mapped_column(String(50))

    # Exit
    exit_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    exit_z_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    exit_price1: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))
    exit_price2: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))
    exit_reason: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # EXIT / STOP_LOSS / EXPIRE

    # P&L (calculated on close)
    pnl: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))
    pnl_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))  # % return

    status: Mapped[str] = mapped_column(String(10), default="OPEN", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    pair: Mapped["PairRegistry"] = relationship("PairRegistry", back_populates="trades")

    def __repr__(self) -> str:
        return (
            f"<PairTrade(id={self.id}, pair_id={self.pair_id}, side={self.side}, "
            f"status={self.status}, pnl={self.pnl})>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pair_id": self.pair_id,
            "entry_time": self.entry_time.isoformat(),
            "entry_z_score": float(self.entry_z_score) if self.entry_z_score else None,
            "side": self.side,
            "qty1": self.qty1,
            "qty2": self.qty2,
            "entry_price1": float(self.entry_price1) if self.entry_price1 else None,
            "entry_price2": float(self.entry_price2) if self.entry_price2 else None,
            "order_id1": self.order_id1,
            "order_id2": self.order_id2,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_z_score": float(self.exit_z_score) if self.exit_z_score else None,
            "exit_price1": float(self.exit_price1) if self.exit_price1 else None,
            "exit_price2": float(self.exit_price2) if self.exit_price2 else None,
            "exit_reason": self.exit_reason,
            "pnl": float(self.pnl) if self.pnl else None,
            "pnl_pct": float(self.pnl_pct) if self.pnl_pct else None,
            "status": self.status,
        }


class PairPerformance(Base):
    """
    Daily cumulative performance metrics per pair.

    Updated at end of each trading day by the strategy engine.
    Used by the monitoring UI and API.
    """

    __tablename__ = "pair_performance"
    __table_args__ = (
        UniqueConstraint("pair_id", "date", name="uq_pair_performance_pair_date"),
        Index("idx_pair_performance_pair_date", "pair_id", "date"),
        {"schema": "strategy_engine"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pair_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("strategy_engine.pair_registry.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Cumulative metrics
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))  # 0–1
    avg_pnl: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))
    total_pnl: Mapped[Optional[float]] = mapped_column(Numeric(15, 4))
    sharpe: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    max_drawdown: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))  # 0–1
    avg_hold_hours: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    kelly_fraction: Mapped[Optional[float]] = mapped_column(Numeric(6, 4))  # half-Kelly

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False
    )

    pair: Mapped["PairRegistry"] = relationship(
        "PairRegistry", back_populates="performance"
    )

    def __repr__(self) -> str:
        return (
            f"<PairPerformance(pair_id={self.pair_id}, date={self.date}, "
            f"win_rate={self.win_rate}, sharpe={self.sharpe})>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pair_id": self.pair_id,
            "date": self.date.isoformat(),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": float(self.win_rate) if self.win_rate else None,
            "avg_pnl": float(self.avg_pnl) if self.avg_pnl else None,
            "total_pnl": float(self.total_pnl) if self.total_pnl else None,
            "sharpe": float(self.sharpe) if self.sharpe else None,
            "max_drawdown": float(self.max_drawdown) if self.max_drawdown else None,
            "avg_hold_hours": (
                float(self.avg_hold_hours) if self.avg_hold_hours else None
            ),
            "kelly_fraction": (
                float(self.kelly_fraction) if self.kelly_fraction else None
            ),
        }


class BacktestRun(Base):
    """
    Historical backtest run results.

    Saved by BacktestReport after each run.
    Stores full equity curve and trade log as JSON for UI rendering.
    passed_gate indicates whether the run met the deployment thresholds.
    """

    __tablename__ = "backtest_run"
    __table_args__ = (
        Index("idx_backtest_run_pair_date", "pair_id", "run_date"),
        Index("idx_backtest_run_passed", "passed_gate"),
        {"schema": "strategy_engine"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pair_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("strategy_engine.pair_registry.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Run metadata
    run_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Parameters used
    entry_threshold: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    exit_threshold: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    stop_loss_threshold: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    z_score_window: Mapped[int] = mapped_column(Integer, nullable=False)
    initial_capital: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    slippage_bps: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), default=5.0)
    commission_per_trade: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2), default=0.0
    )

    # Performance metrics
    total_return: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    annualized_return: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    max_drawdown: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    win_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    profit_factor: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_hold_time_hours: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    kelly_fraction: Mapped[Optional[float]] = mapped_column(Numeric(6, 4))

    # Gate result
    passed_gate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Full results (JSON)
    equity_curve: Mapped[Optional[dict]] = mapped_column(
        JSON
    )  # list of {timestamp, value}
    trade_log: Mapped[Optional[dict]] = mapped_column(JSON)  # list of trade dicts

    notes: Mapped[Optional[str]] = mapped_column(Text)

    pair: Mapped["PairRegistry"] = relationship(
        "PairRegistry", back_populates="backtest_runs"
    )

    def __repr__(self) -> str:
        return (
            f"<BacktestRun(id={self.id}, pair_id={self.pair_id}, "
            f"sharpe={self.sharpe_ratio}, passed={self.passed_gate})>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pair_id": self.pair_id,
            "run_date": self.run_date.isoformat(),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "entry_threshold": float(self.entry_threshold),
            "exit_threshold": float(self.exit_threshold),
            "stop_loss_threshold": float(self.stop_loss_threshold),
            "z_score_window": self.z_score_window,
            "initial_capital": float(self.initial_capital),
            "total_return": (
                float(self.total_return) if self.total_return is not None else None
            ),
            "annualized_return": (
                float(self.annualized_return)
                if self.annualized_return is not None
                else None
            ),
            "sharpe_ratio": (
                float(self.sharpe_ratio) if self.sharpe_ratio is not None else None
            ),
            "max_drawdown": (
                float(self.max_drawdown) if self.max_drawdown is not None else None
            ),
            "win_rate": float(self.win_rate) if self.win_rate is not None else None,
            "profit_factor": (
                float(self.profit_factor) if self.profit_factor is not None else None
            ),
            "total_trades": self.total_trades,
            "avg_hold_time_hours": (
                float(self.avg_hold_time_hours) if self.avg_hold_time_hours else None
            ),
            "kelly_fraction": (
                float(self.kelly_fraction) if self.kelly_fraction is not None else None
            ),
            "passed_gate": self.passed_gate,
            "equity_curve": self.equity_curve,
            "trade_log": self.trade_log,
            "notes": self.notes,
        }


class PortfolioRiskState(Base):
    """
    Single-row table tracking portfolio-level risk state across Prefect flow runs.

    id is always 1 — enforced by PRIMARY KEY constraint.
    Seeded by migration 24_add_portfolio_risk_controls.sql.

    peak_equity              — highest total portfolio equity seen; used to measure drawdown
    circuit_breaker_active   — True = no new entries allowed until manually reset
    circuit_breaker_triggered_at — when the circuit breaker last fired
    drawdown_threshold       — fraction (e.g. 0.05 = 5%) below peak that triggers breaker
    """

    __tablename__ = "portfolio_risk_state"
    __table_args__ = {"schema": "strategy_engine"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    peak_equity: Mapped[float] = mapped_column(
        Numeric(15, 2), nullable=False, default=0.0
    )
    circuit_breaker_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    circuit_breaker_triggered_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True)
    )
    drawdown_threshold: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=0.05
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<PortfolioRiskState(peak={self.peak_equity}, "
            f"cb_active={self.circuit_breaker_active}, "
            f"threshold={self.drawdown_threshold})>"
        )

    def to_dict(self) -> dict:
        return {
            "peak_equity": float(self.peak_equity),
            "circuit_breaker_active": self.circuit_breaker_active,
            "circuit_breaker_triggered_at": (
                self.circuit_breaker_triggered_at.isoformat()
                if self.circuit_breaker_triggered_at
                else None
            ),
            "drawdown_threshold": float(self.drawdown_threshold),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
