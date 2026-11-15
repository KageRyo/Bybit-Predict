# Bybit-Predict

[![License: GPL-2.0-or-later](https://img.shields.io/badge/License-GPL--2.0--or--later-blue.svg)](LICENSE)
[![CI](https://github.com/KageRyo/Bybit-Predict/actions/workflows/ci.yml/badge.svg)](https://github.com/KageRyo/Bybit-Predict/actions/workflows/ci.yml)

**用 Bybit V5 公開市場資料做規則式加密貨幣市場分析、產生訊號，並可整合 Discord。**

> **目前正式版本：v4.1.6**。這版修正線性合約空單報酬的算法，最大回撤也改為把初始資金算進去，即時 CLI／Discord 分析則改成只用已收線 K 線。同時也包含 v4.1.5 的可靠性改進、v4.1.1 開始的 PyPI 發行，以及 v4.1.0 的可重現歷史回測；最後一個 legacy 版本是 v3.1。

[English](README.md)

用舊版跑出的回測，請用當初保存的 CSV／manifest，搭配相同的分析視窗、手續費與滑價重新計算，並保留原報告比較。詳見 [CHANGELOG.md](CHANGELOG.md) 的 v4.1.6 升級說明。

## Bybit-Predict 是什麼／不是什麼

Bybit-Predict 從 Bybit 取得 OHLCV K 線，產生市場訊號與參考價位。目前的 `legacy-rule-based-v4` 策略使用 K 線型態、量能、百分位數、IQR，以及參考 Fibonacci 比例的價位計算。

它**不是機器學習模型**，也**不是交易機器人**。它不會下單，也不需要 Bybit API 憑證。

> **風險聲明**：加密貨幣市場波動很大。所有輸出僅供參考，不構成財務建議或獲利保證。

## 特色

- 即時分析只用已收線 K 線：預設 180 根通常只要抓一頁資料，要 1,000 根時可能得再往前補抓一頁。
- `Candle` 有完整型別、時間統一為 UTC；`PredictionResult` 建立後不能修改。
- legacy 策略不使用全域狀態，同時跑多個分析也不會混到資料。
- 提供 CLI，以及可選用、非阻塞的 Discord slash command。
- 用 Bybit 的 instrument metadata 確認交易對可以交易，不再寫死幣種清單。
- 具備測試、Ruff、Pyright、GitHub Actions CI 與 Dependabot。
- 可重現的歷史回測：可保存 CSV 輸入資料與經過驗證的 manifest，列出模擬假設、計算績效指標，並和兩個簡單的 baseline 比較。

## 系統需求

- Python 3.11 以上
- 可連線至 Bybit 公開市場 API

使用公開市場資料**不需要 Bybit 帳戶、API key 或 API secret**。只有選用 Discord 介面時才需要 Discord bot token。

## 安裝

### 從 PyPI 安裝

從 PyPI 安裝 CLI 和預設的 Bybit V5 相依套件：

```bash
python -m pip install bybit-predict
```

需要 Discord 介面時，再安裝選用的 `discord` extra：

```bash
python -m pip install "bybit-predict[discord]"
```

想把 CLI 裝在獨立環境，可以用 [pipx](https://pipx.pypa.io/)：

```bash
pipx install bybit-predict
```

### 從原始碼安裝

```bash
git clone https://github.com/KageRyo/Bybit-Predict.git
cd Bybit-Predict
uv venv --python 3.11 .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install .
```

若要開發、執行完整測試及 Discord 介面：

```bash
uv pip install -e ".[dev]"
```

## CLI

用預設的 180 根 4 小時 K 線分析：

```bash
bybit-predict analyze BTCUSDT
```

指定 Bybit 支援的其他週期（interval）與 K 線數量：

```bash
bybit-predict analyze ETHUSDT --interval 60 --limit 240
```

CLI 的 `--limit` 與 Discord 的 `candles` 指的是已收線 K 線數量，範圍 42–1,000 根，預設 180 根。還沒收線的那一根不納入，到了它的 UTC 收線時間才算進去。分鐘、日線和週線的收線時間從開盤時間往後推算；月線則在下一個 UTC 曆月的月初收線，不是固定 30 天。同一次分析的所有請求和重試都用同一個 UTC 時間點判斷。最多抓兩頁資料仍不夠時，分析會直接報錯，並列出要求的根數與實際可用的已收線根數。目前沒有選項可以納入未收線 K 線。輸出的資料期間，仍是第一根與最後一根分析 K 線的開盤時間。

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

symbol 或參數無效、或取得市場資料失敗時，CLI 會以非零 exit code 結束。也可使用 `python -m bybit_predict analyze BTCUSDT`。

### 歷史回測

`backtest` 指令會在過去的日期區間重跑策略：策略只看得到前面固定根數的已收線 K 線；出現看多或看空訊號時，在下一根 K 線開盤模擬進場、同一根收盤出場。輸出會列出模擬假設、績效指標和兩個 baseline。

```bash
bybit-predict backtest BTCUSDT \
  --interval 240 \
  --start 2024-01-01 \
  --end 2025-01-01 \
  --strategy legacy \
  --window 180 \
  --save-data data/btcusdt-2024-4h.csv
```

要離線重跑相同的 normalized CSV 資料：

```bash
bybit-predict backtest BTCUSDT \
  --interval 240 \
  --start 2024-01-01 \
  --end 2025-01-01 \
  --strategy legacy \
  --window 180 \
  --data data/btcusdt-2024-4h.csv
```

`--start` 包含起點、`--end` 不包含終點，時間以 UTC 計算。用 `--save-data` 保存 CSV 時，會一併寫出 `<csv-name>.manifest.json`；請把它和 CSV 放在一起，`--data` 重跑前會先用它驗證資料。資料檔路徑必須在目前工作目錄底下。

報酬算法、指標定義、manifest 格式、路徑規則和限制，請見[回測與評估說明](docs/backtesting.md)（英文）。

## Discord slash commands

安裝 Discord 選用套件，在 Discord 建立 application 與 bot，再用 `bot` 和 `applications.commands` 兩個 scope 邀請機器人：

```bash
python -m pip install ".[discord]"
cp .env.example .env
```

請以安全方式設定環境變數（例如本機 source `.env` 或在部署平台使用 secret manager）：

```bash
export DISCORD_BOT_TOKEN="your-token"
# 選填：讓指令立即同步到單一開發用伺服器。
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

指令會在另一個 thread 向 Bybit 抓資料，所以 Bybit 回應慢也不會卡住 Discord 的 event loop。回覆內容包含策略名稱、趨勢、訊號強度、分析的 K 線期間，以及中性的**參考價位**。

請勿 commit `.env`、bot token、API key 或下載的市場資料；它們都已在 `.gitignore` 中排除。

## 設定

| 變數 | 是否必要 | 用途 |
| --- | --- | --- |
| `DISCORD_BOT_TOKEN` | 僅 Discord | Discord bot authentication token。 |
| `DISCORD_GUILD_ID` | 否 | 開發用的 guild，設定後指令會立即同步。 |
| `BYBIT_TESTNET` | 否 | 設為 `true` 時使用 Bybit testnet 公開資料；預設 `false`。 |

市場資料 client 沒有 Bybit 憑證設定，因為公開的 K 線與 instrument endpoint 不需要驗證。

## 架構

```text
Bybit V5 public API
        │
BybitV5MarketClient ──→ normalized UTC Candles
        │
        ├── PredictionService ──→ LegacyRuleBasedStrategy ──→ PredictionResult
        │         │                         │
        │         ├──────── CLI             └── future strategies
        │         └──────── Discord slash command
        │
        └── BacktestEngine ─────→ LegacyRuleBasedStrategy ──→ BacktestResult
                  │
                  ├──────── historical CLI
                  └──────── saved CSV input/output
```

- `market/` 負責 Bybit V5 請求、重試範圍、分頁，以及回應資料的正規化。
- `strategies/` 放純粹、結果可重現（deterministic）的訊號計算，不依賴 Bybit 或 Discord。
- `services/` 組合 market data 和 strategy。
- `interfaces/` 僅處理使用者輸入／輸出。

## 策略與評估

`LegacyRuleBasedStrategy` 保留了專案最早的核心邏輯：分類 K 線實體與影線、比較顯著的多空量能，並用 IQR 和百分位數算出可選的參考價位。策略有明確名稱，之後的新策略才能拿它公平比較。v4 修正了 v3 的三個問題：量能視窗只取 0 或 6 根 K 線、時間處理，以及空頭 Fibonacci 標籤順序；完整的相容性基準與保留的語意請見 [legacy 策略遷移說明](docs/legacy-strategy-changes.md)（英文）。

**v4.1.0** 的回測（[#25](https://github.com/KageRyo/Bybit-Predict/issues/25)）先定義規則：固定長度的 trailing 分析視窗、下一根開盤進場、同一根收盤出場、中性訊號時持有現金；再計算 close-to-close directional accuracy、win rate、平均報酬、最大回撤，以及無風險利率設為 0 的 Sharpe ratio，並與 buy-and-hold 和 10/20 SMA 方向 baseline 比較。確切規則與限制請見[回測與評估說明](docs/backtesting.md)（英文）。

## 開發與品質檢查

```bash
ruff check .
ruff format --check .
pyright
pytest
```

總覆蓋率低於 **80%** 時 `pytest` 會失敗。Pyright 使用 basic mode，但缺少 import 會視為錯誤；`dev` extra 會安裝這些檢查需要的相依套件。

PR 會在 Python 3.11、3.12 與 3.13 執行上述檢查。請參閱 [CONTRIBUTING.md](CONTRIBUTING.md)，其中包含開發設定與必須遵守的 `feature/<issue>-<description>` branch 命名規範。

## 發布

推送正式版 tag 後，workflow 會建立 sdist 與 universal wheel、先驗證這些檔案、透過 PyPI Trusted Publishing 發布，最後建立附上同一批檔案的 GitHub Release。一次性設定與發布流程請見 [PyPI 發布說明](docs/pypi-publishing.md)（英文，給維護者）；repo 和 GitHub Actions secrets 都沒有存放長效的 PyPI API token。

## 發行歷史與規劃

- **v4.0.0**：改為 package 架構，加入公開 Bybit V5 client、無狀態的 legacy 策略、CLI、Discord slash command、設定、品質檢查與文件。
- **v4.1.0**：可重現的回測與評估（[#25](https://github.com/KageRyo/Bybit-Predict/issues/25)）。
- **v4.1.1**：PyPI 發行、Trusted Publishing 與套件發布自動化（[#37](https://github.com/KageRyo/Bybit-Predict/issues/37)）。
- **v4.1.2**：文件與 PyPI metadata 修正（[#40](https://github.com/KageRyo/Bybit-Predict/issues/40)）。
- **v4.1.3**：更新 CI 相依套件，並還原完整的 GPL v2 授權條文。
- **v4.1.4**：所有 distribution 使用標準 GPL v2 授權條文，並由 GitHub 辨識為 GPL-2.0。
- **v4.1.5**：加強 Candle 與 API 的穩定性、驗證 interval 與 dataset 重跑、SMA baseline 改為線性時間計算、明確定義指標語意、強制品質檢查，以及 `main` 分支保護規則。
- **v4.1.6**：修正線性合約空單報酬，最大回撤改計入初始資金；即時分析改用已收線 K 線，資料不夠時最多再補抓一頁（[#64](https://github.com/KageRyo/Bybit-Predict/issues/64)–[#66](https://github.com/KageRyo/Bybit-Predict/issues/66)）。
- **後續**：可在同一 strategy contract 下加入更多策略；ML 是未來可能的方向。

## 貢獻與歷史

這個專案保留了原本的 repo 名稱、issues、forks、stars、已合併的 PR 與 Git 歷史。感謝先前貢獻者，包括 [RRAaru](https://github.com/RRAaru)。歡迎新 contributor 從標有 [good first issue](https://github.com/KageRyo/Bybit-Predict/labels/good%20first%20issue) 的 issue 開始，或閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License 與著作權

Bybit-Predict 採用 [GNU General Public License v2.0 or later](LICENSE)。

Copyright © 2022–2026 **CodeRyo Studio**、**Chien-Hsun Chang** 與 [contributors](CONTRIBUTORS.md)。CodeRyo Studio 是專案維護者；完整歸屬聲明請見 [NOTICE](NOTICE)。
