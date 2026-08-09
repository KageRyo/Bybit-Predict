from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from bybit_predict.backtest.engine import BacktestEngine
from bybit_predict.backtest.metrics import annualized_sharpe, maximum_drawdown, periods_per_year
from bybit_predict.exceptions import BacktestError
from bybit_predict.models import Candle, PredictionResult, SignalTrend


def candle(index: int, *, open_price: float, close: float) -> Candle:
    return Candle(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC) + timedelta(hours=4 * index),
        open=open_price,
        high=max(open_price, close) + 1,
        low=min(open_price, close) - 1,
        close=close,
        volume=100 + index,
    )


def result_for(candles: tuple[Candle, ...], trend: SignalTrend) -> PredictionResult:
    return PredictionResult(
        symbol="BTCUSDT",
        interval="240",
        strategy="test-strategy",
        trend=trend,
        signal_strength=1.0 if trend is not SignalTrend.NEUTRAL else 0.0,
        candle_count=len(candles),
        period_start=candles[0].timestamp,
        period_end=candles[-1].timestamp,
        bullish_power=1.0,
        bearish_power=0.0,
        reference_levels=(),
        time_references=(),
    )


@dataclass
class FixedStrategy:
    trend: SignalTrend
    name: str = "fixed"
    minimum_candles: int = 2
    windows: list[tuple[Candle, ...]] = field(default_factory=list)

    def analyze(
        self, candles: tuple[Candle, ...], *, symbol: str, interval: str
    ) -> PredictionResult:
        self.windows.append(candles)
        return result_for(candles, self.trend)


def test_engine_uses_closed_trailing_window_then_next_candle_execution() -> None:
    candles = (
        candle(0, open_price=10, close=10),
        candle(1, open_price=10, close=11),
        candle(2, open_price=12, close=13),
        candle(3, open_price=13, close=12),
    )
    strategy = FixedStrategy(SignalTrend.BULLISH)

    result = BacktestEngine(strategy, analysis_window=2).run(
        candles, symbol="BTCUSDT", interval="240"
    )

    assert [tuple(item.timestamp for item in window) for window in strategy.windows] == [
        (candles[0].timestamp, candles[1].timestamp),
        (candles[1].timestamp, candles[2].timestamp),
    ]
    assert result.signal_count == 2
    assert result.trade_count == 2
    assert result.trades[0].signal_timestamp == candles[1].timestamp
    assert result.trades[0].entry_timestamp == candles[2].timestamp
    assert result.trades[0].entry_price == 12
    assert result.trades[0].exit_price == 13
    assert result.metrics.directional_accuracy == pytest.approx(0.5)
    assert result.metrics.win_rate == pytest.approx(0.5)
    assert result.metrics.total_return == pytest.approx(0.0)
    assert result.baselines[0].name == "buy-and-hold"
    assert result.baselines[0].total_return == pytest.approx(0.0)


def test_engine_keeps_neutral_signals_in_cash_and_marks_inapplicable_metrics() -> None:
    candles = tuple(candle(index, open_price=10 + index, close=10 + index) for index in range(4))

    result = BacktestEngine(FixedStrategy(SignalTrend.NEUTRAL), analysis_window=2).run(
        candles, symbol="BTCUSDT", interval="240"
    )

    assert result.trade_count == 0
    assert result.metrics.directional_accuracy is None
    assert result.metrics.win_rate is None
    assert result.metrics.average_trade_return is None
    assert result.metrics.total_return == 0
    assert result.metrics.maximum_drawdown == 0
    assert result.metrics.sharpe_ratio is None


def test_engine_applies_fee_and_slippage_to_trade_returns() -> None:
    candles = (
        candle(0, open_price=10, close=10),
        candle(1, open_price=10, close=11),
        candle(2, open_price=12, close=13),
    )

    result = BacktestEngine(
        FixedStrategy(SignalTrend.BULLISH), analysis_window=2, fee_rate=0.01, slippage_rate=0.01
    ).run(candles, symbol="BTCUSDT", interval="240")

    trade = result.trades[0]
    assert trade.entry_price == pytest.approx(12.12)
    assert trade.exit_price == pytest.approx(12.87)
    assert trade.net_return == pytest.approx(trade.gross_return - 0.02)
    assert result.assumptions.fee_rate == 0.01
    assert result.assumptions.slippage_rate == 0.01
    assert result.baselines[0].total_return == pytest.approx(12.87 / 12.12 - 1 - 0.02)


def test_engine_requires_one_execution_candle_after_its_window() -> None:
    candles = (candle(0, open_price=10, close=10), candle(1, open_price=10, close=11))

    with pytest.raises(BacktestError, match="more candles"):
        BacktestEngine(FixedStrategy(SignalTrend.BULLISH), analysis_window=2).run(
            candles, symbol="BTCUSDT", interval="240"
        )


def test_metric_helpers_cover_drawdown_sharpe_and_interval_scaling() -> None:
    assert maximum_drawdown((1.0, 1.2, 0.9, 1.1)) == pytest.approx(-0.25)
    assert annualized_sharpe((0.0, 0.0), 365) is None
    assert annualized_sharpe((0.01, -0.01, 0.02), 365) is not None
    assert periods_per_year("240") == 2190
    assert periods_per_year("D") == 365
