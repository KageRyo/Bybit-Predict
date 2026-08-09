from __future__ import annotations

from bybit_predict.exceptions import SymbolNotFoundError
from bybit_predict.models import Candle, SignalTrend
from bybit_predict.services.predictor import PredictionService


class FakeMarketData:
    def __init__(self, candles: tuple[Candle, ...], *, valid: bool = True) -> None:
        self.candles = candles
        self.valid = valid
        self.requested_symbol: str | None = None

    def is_valid_symbol(self, symbol: str) -> bool:
        self.requested_symbol = symbol
        return self.valid

    def get_candles(self, symbol: str, interval: str, limit: int) -> tuple[Candle, ...]:
        assert symbol == self.requested_symbol
        assert interval == "240"
        assert limit == 42
        return self.candles


def test_prediction_service_composes_symbol_validation_data_and_strategy(
    candles: tuple[Candle, ...],
) -> None:
    market = FakeMarketData(candles)
    result = PredictionService(market).analyze("btcusdt", interval="240", limit=42)

    assert result.symbol == "BTCUSDT"
    assert result.trend is SignalTrend.BULLISH


def test_prediction_service_does_not_fetch_invalid_symbols(candles: tuple[Candle, ...]) -> None:
    market = FakeMarketData(candles, valid=False)

    try:
        PredictionService(market).analyze("missing")
    except SymbolNotFoundError:
        pass
    else:
        raise AssertionError("Expected invalid symbols to raise SymbolNotFoundError")
