# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""A no-look-ahead, one-candle execution engine for deterministic strategies."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean

from bybit_predict.backtest.metrics import annualized_sharpe, maximum_drawdown, periods_per_year
from bybit_predict.backtest.models import (
    BacktestAssumptions,
    BacktestResult,
    BaselineResult,
    EquityPoint,
    PerformanceMetrics,
    Trade,
)
from bybit_predict.exceptions import BacktestError
from bybit_predict.models import Candle, SignalTrend
from bybit_predict.strategies.base import Strategy


@dataclass(frozen=True, slots=True)
class BacktestEngine:
    """Evaluate a strategy without allowing a signal to see its execution candle."""

    strategy: Strategy
    analysis_window: int = 180
    fee_rate: float = 0.0
    slippage_rate: float = 0.0

    def __post_init__(self) -> None:
        minimum = getattr(self.strategy, "minimum_candles", 1)
        if self.analysis_window < minimum:
            raise ValueError(
                f"analysis_window must be at least the strategy minimum of {minimum} candles"
            )
        if self.fee_rate < 0 or self.slippage_rate < 0:
            raise ValueError("fee_rate and slippage_rate cannot be negative")

    def run(self, candles: tuple[Candle, ...], *, symbol: str, interval: str) -> BacktestResult:
        """Run expanding historical signals using a fixed trailing analysis window.

        A signal is calculated only after its window has closed. A non-neutral
        result enters at the next candle's open and exits at that same candle's
        close. Neutral signals remain in cash for that candle. This deliberately
        prevents the strategy from using an execution candle to create its signal.
        """
        self._validate_candles(candles)
        assumptions = BacktestAssumptions(
            analysis_window=self.analysis_window,
            fee_rate=self.fee_rate,
            slippage_rate=self.slippage_rate,
        )
        trades: list[Trade] = []
        step_returns: list[float] = []
        directional_matches: list[bool] = []
        equity = 1.0
        equity_curve: list[EquityPoint] = []

        for signal_index in range(self.analysis_window - 1, len(candles) - 1):
            window = candles[signal_index - self.analysis_window + 1 : signal_index + 1]
            signal = self.strategy.analyze(window, symbol=symbol, interval=interval)
            execution = candles[signal_index + 1]
            step_return = 0.0
            if signal.trend is not SignalTrend.NEUTRAL:
                directional_matches.append(
                    self._is_directionally_correct(signal.trend, window[-1].close, execution.close)
                )
                trade = self._trade(signal.trend, window[-1], execution)
                trades.append(trade)
                step_return = trade.net_return
            equity *= 1 + step_return
            step_returns.append(step_return)
            equity_curve.append(EquityPoint(timestamp=execution.timestamp, value=equity))

        metrics = self._metrics(
            trades=tuple(trades),
            step_returns=tuple(step_returns),
            directional_matches=tuple(directional_matches),
            equity_curve=tuple(equity_curve),
            interval=interval,
        )
        return BacktestResult(
            symbol=symbol.upper(),
            interval=str(interval).upper(),
            strategy=self.strategy.name,
            period_start=candles[0].timestamp,
            period_end=candles[-1].timestamp,
            candle_count=len(candles),
            signal_count=len(step_returns),
            trade_count=len(trades),
            assumptions=assumptions,
            metrics=metrics,
            baselines=self._baselines(candles, interval),
            trades=tuple(trades),
            equity_curve=tuple(equity_curve),
        )

    def _trade(self, trend: SignalTrend, signal_candle: Candle, execution: Candle) -> Trade:
        entry_price = self._entry_price(execution.open, trend)
        exit_price = self._exit_price(execution.close, trend)
        if entry_price <= 0 or exit_price <= 0:
            raise BacktestError("Backtesting requires strictly positive execution prices")
        gross_return = (
            exit_price / entry_price - 1
            if trend is SignalTrend.BULLISH
            else entry_price / exit_price - 1
        )
        net_return = gross_return - 2 * self.fee_rate
        return Trade(
            signal_timestamp=signal_candle.timestamp,
            entry_timestamp=execution.timestamp,
            exit_timestamp=execution.timestamp,
            trend=trend,
            entry_price=entry_price,
            exit_price=exit_price,
            gross_return=gross_return,
            net_return=net_return,
        )

    def _entry_price(self, price: float, trend: SignalTrend) -> float:
        adjustment = (
            1 + self.slippage_rate if trend is SignalTrend.BULLISH else 1 - self.slippage_rate
        )
        return price * adjustment

    def _exit_price(self, price: float, trend: SignalTrend) -> float:
        adjustment = (
            1 - self.slippage_rate if trend is SignalTrend.BULLISH else 1 + self.slippage_rate
        )
        return price * adjustment

    @staticmethod
    def _is_directionally_correct(
        trend: SignalTrend, prior_close: float, future_close: float
    ) -> bool:
        return (trend is SignalTrend.BULLISH and future_close > prior_close) or (
            trend is SignalTrend.BEARISH and future_close < prior_close
        )

    def _metrics(
        self,
        *,
        trades: tuple[Trade, ...],
        step_returns: tuple[float, ...],
        directional_matches: tuple[bool, ...],
        equity_curve: tuple[EquityPoint, ...],
        interval: str,
    ) -> PerformanceMetrics:
        return PerformanceMetrics(
            directional_accuracy=(fmean(directional_matches) if directional_matches else None),
            win_rate=(fmean(trade.net_return > 0 for trade in trades) if trades else None),
            average_trade_return=(fmean(trade.net_return for trade in trades) if trades else None),
            total_return=(equity_curve[-1].value - 1 if equity_curve else 0.0),
            maximum_drawdown=maximum_drawdown(tuple(point.value for point in equity_curve)),
            sharpe_ratio=annualized_sharpe(step_returns, periods_per_year(interval)),
        )

    def _baselines(self, candles: tuple[Candle, ...], interval: str) -> tuple[BaselineResult, ...]:
        first_execution = candles[self.analysis_window]
        if first_execution.open <= 0 or candles[-1].close <= 0:
            raise BacktestError("Backtesting baselines require strictly positive prices")
        buy_and_hold_entry = self._entry_price(first_execution.open, SignalTrend.BULLISH)
        buy_and_hold_exit = self._exit_price(candles[-1].close, SignalTrend.BULLISH)
        buy_and_hold = buy_and_hold_exit / buy_and_hold_entry - 1 - 2 * self.fee_rate
        sma_return, sma_trades = self._sma_direction_return(candles)
        return (
            BaselineResult(
                name="buy-and-hold",
                description=(
                    "Buy at the first executable candle open and hold to the final close, "
                    "using the declared fee and slippage assumptions."
                ),
                total_return=buy_and_hold,
                trade_count=1,
            ),
            BaselineResult(
                name="sma-10-20-direction",
                description=(
                    "Long when the 10-candle SMA exceeds the 20-candle SMA, short when below; "
                    "uses the same next-open to close execution model."
                ),
                total_return=sma_return,
                trade_count=sma_trades,
            ),
        )

    def _sma_direction_return(self, candles: tuple[Candle, ...]) -> tuple[float, int]:
        equity = 1.0
        trade_count = 0
        for signal_index in range(self.analysis_window - 1, len(candles) - 1):
            closes = tuple(candle.close for candle in candles[: signal_index + 1])
            short_average = fmean(closes[-10:])
            long_average = fmean(closes[-20:])
            if short_average == long_average:
                continue
            trend = SignalTrend.BULLISH if short_average > long_average else SignalTrend.BEARISH
            trade = self._trade(trend, candles[signal_index], candles[signal_index + 1])
            equity *= 1 + trade.net_return
            trade_count += 1
        return equity - 1, trade_count

    def _validate_candles(self, candles: tuple[Candle, ...]) -> None:
        if len(candles) <= self.analysis_window:
            raise BacktestError(
                "Backtesting requires more candles than the analysis window so at least one "
                "signal can be executed"
            )
        if any(
            first.timestamp >= second.timestamp
            for first, second in zip(candles, candles[1:], strict=False)
        ):
            raise BacktestError("Candles must be in strictly ascending chronological order")
