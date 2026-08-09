# Bybit-Predict

[![License: GPL-2.0-or-later](https://img.shields.io/badge/License-GPL--2.0--or--later-blue.svg)](LICENSE)
[![CI](https://github.com/KageRyo/Bybit-Predict/actions/workflows/ci.yml/badge.svg)](https://github.com/KageRyo/Bybit-Predict/actions/workflows/ci.yml)

**以 Bybit V5 公開市場資料為基礎的規則式加密貨幣市場分析、訊號產生與 Discord 整合工具。**

> **目前正式版本：v4.0.0。**這個 major release 在保留 repo、issues、外部貢獻、forks 與 Git history 的前提下完成現代化重構；前一個 legacy release 為 v3.1。

[English](README.md)

## Bybit-Predict 是什麼／不是什麼

Bybit-Predict 從 Bybit 取得 OHLCV K 線，產生供參考的市場訊號與參考價位。目前的
`legacy-rule-based-v4` 策略使用 K 線型態、量能、百分位數、IQR，以及 Fibonacci
概念的價位計算。

它**不是機器學習模型**，也**不是交易機器人**。它不會下單、不要求 Bybit API
憑證，也不保證任何市場結果。

> **風險聲明：**加密貨幣市場波動極高。所有輸出僅供資訊參考，不構成財務建議、交易指令或獲利保證。

## 特色

- 一次 Bybit V5 K-line request 最多可取得 1,000 根 K 線；預設分析用 180 根，取代舊版 180 次獨立 request。
- 使用 typed、UTC 正規化的 `Candle` 與 immutable `PredictionResult` 資料模型。
- 無 global state 的 legacy strategy：同時執行多次分析不會混用資料。
- 提供 CLI，以及可選用、非阻塞的 Discord slash command。
- 透過 Bybit instrument metadata 驗證有效交易對，不再 hard-code 幣種清單。
- 具備測試、Ruff、Pyright、GitHub Actions CI 與 Dependabot。

## 系統需求

- Python 3.11 以上
- 可連線至 Bybit 公開市場 API

使用公開市場資料**不需要 Bybit 帳戶、API key 或 API secret**。只有選用 Discord
介面時才需要 Discord bot token。

## 安裝

```bash
git clone https://github.com/KageRyo/Bybit-Predict.git
cd Bybit-Predict
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install .
```

若要開發、執行完整測試及 Discord 介面：

```bash
python -m pip install -e ".[dev]"
```

## CLI

使用預設 180 根四小時 K 線進行分析：

```bash
bybit-predict analyze BTCUSDT
```

指定 Bybit 支援的 interval 與 K 線數：

```bash
bybit-predict analyze ETHUSDT --interval 60 --limit 240
```

輸出範例：

```text
Symbol: BTCUSDT
Strategy: legacy-rule-based-v4 (rule-based, not ML)
Timeframe: 240
Candles: 180
Trend: Bullish
Signal strength: 68.00%

Reference levels:
     0%  ...
  23.6%  ...
```

若 symbol、參數或市場資料有錯，CLI 會以非零 status code 結束。也可使用
`python -m bybit_predict analyze BTCUSDT`。

## Discord slash commands

安裝 Discord optional dependency、建立 Discord application/bot，並以 `bot` 和
`applications.commands` scopes 邀請機器人：

```bash
python -m pip install ".[discord]"
cp .env.example .env
```

請以安全方式設定環境變數（例如本機 source `.env` 或在部署平台使用 secret manager）：

```bash
export DISCORD_BOT_TOKEN="your-token"
# 選填：立即將 command sync 到單一開發伺服器。
export DISCORD_GUILD_ID="your-development-guild-id"
```

啟動介面：

```bash
bybit-predict discord
```

在 Discord 使用 slash command：

```text
/predict symbol:BTCUSDT interval:240 candles:180
```

command 會把外部市場請求放到 thread 執行，因此緩慢的 Bybit request 不會 block
Discord event loop。回覆包含 strategy、趨勢、訊號強度、分析 K 線期間與中性的
**參考價位**，而不是下單建議。

請勿 commit `.env`、bot token、API key 或下載的市場資料；它們都已在 `.gitignore`
中排除。

## 設定

| 變數 | 是否必要 | 用途 |
| --- | --- | --- |
| `DISCORD_BOT_TOKEN` | 僅 Discord | Discord bot authentication token。 |
| `DISCORD_GUILD_ID` | 否 | 開發用 guild，用於立即同步 command。 |
| `BYBIT_TESTNET` | 否 | 設為 `true` 時使用 Bybit testnet 公開資料；預設 `false`。 |

市場資料 client 刻意沒有 Bybit credential 設定：公開的 K-line 與 instrument
endpoints 不需要 authentication。

## 架構

```text
Bybit V5 public API
        │
BybitV5MarketClient ──→ normalized UTC Candles
        │
PredictionService ──→ LegacyRuleBasedStrategy ──→ PredictionResult
        │                         │
        ├──────── CLI             └── future strategies / v4.1 backtesting
        └──────── Discord slash command
```

- `market/` 負責 Bybit V5 requests、retry 範圍、pagination 與 response normalization。
- `strategies/` 存放純粹、deterministic 的訊號計算，不依賴 Bybit 或 Discord。
- `services/` 組合 market data 和 strategy。
- `interfaces/` 僅處理使用者輸入／輸出。

## 策略與評估

`LegacyRuleBasedStrategy` 是刻意保留下來的歷史核心：它分類 K 線實體與影線、比較顯著多空量能，並從 IQR 和 percentile 算出選用的參考價位。明確命名策略後，未來新策略才能公平比較。v4 刻意修正 v3 的 zero/six-candle volume window、時間處理，以及 bearish Fibonacci label ordering；完整 compatibility baseline 與保留的語意請見 [legacy strategy migration notes](docs/legacy-strategy-changes.md)。

預計在 **v4.1.0** 完成的 backtesting（[#25](https://github.com/KageRyo/Bybit-Predict/issues/25)）會先定義 entry/exit semantics，再量測方向正確率、win rate、average return、maximum drawdown 與適當 baseline。在此之前，本專案不宣稱訊號具有任何已驗證的預測能力。

## 開發與品質檢查

```bash
ruff check .
ruff format --check .
pyright
pytest
```

PR 會在 Python 3.11、3.12 與 3.13 執行上述檢查。請參閱
[CONTRIBUTING.md](CONTRIBUTING.md)，其中包含開發設定與必須遵守的
`feature/<issue>-<description>` branch 命名規範。

## Roadmap

- **v4.0.0：**package 架構、公開 Bybit V5 client、stateless legacy strategy、CLI、Discord slash command、設定、品質 gate 與文件。
- **v4.1.0：**reproducible backtesting 與評估（[#25](https://github.com/KageRyo/Bybit-Predict/issues/25)）。
- **後續：**可在同一 strategy contract 下加入更多策略；ML 是未來可能方向，並非現有功能。

## 貢獻與歷史

專案刻意保留 repo 名稱、issues、forks、stars、已 merge 的 PR 與 Git history。感謝先前貢獻者，包括 [RRAaru](https://github.com/RRAaru)。歡迎新 contributor 從 [good first issues](https://github.com/KageRyo/Bybit-Predict/labels/good%20first%20issue) 開始，或閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License 與著作權

Bybit-Predict 採用 [GNU General Public License v2.0 or later](LICENSE)。

Copyright © 2022–2026 **CodeRyo Studio**、**Chien-Hsun Chang** 與
[contributors](CONTRIBUTORS.md)。CodeRyo Studio 是專案維護者；完整歸屬聲明請見
[NOTICE](NOTICE)。
