# Bybit-Predict

![Bybit-Predict](https://img.shields.io/badge/License-GPL--2.0-blue.svg)  
使用 Python 和 Bybit 交易所 API 預測加密貨幣價格趨勢。

## 專案概述

Bybit-Predict 是一個開源專案，旨在通過 Bybit 交易所 API 分析並預測加密貨幣價格趨勢。整合 Discord 提供便捷的操作體驗，同時注重用戶隱私，無需向開發者上傳任何個人資料。

> **⚠️ 免責聲明**：任何投資均具有風險。本軟體僅提供參考意見，開發團隊不保證投資績效，使用者需自行承擔盈虧責任。

## 功能特色

- **趨勢預測**：利用 Bybit API 預測加密貨幣價格走勢。
- **Discord 整合**：通過 Discord 機器人監控預測。
- **隱私保護**：無需向開發者分享個人資料。
- **開源項目**：採用 GPL-2.0 License，歡迎參與開源貢獻。

## 目錄

- [安裝](#安裝)
- [使用方法](#使用方法)
- [配置](#配置)
- [支援語言](#支援語言)
- [貢獻](#貢獻)
- [License](#License)
- [聯繫方式](#聯繫方式)
- [免責聲明](#免責聲明)

## 安裝

### 前置條件
- Python 3.8 或更高版本
- Git
- Bybit 帳戶與 API 金鑰
- Discord 機器人Token

### 安裝步驟
1. 複製專案：
   ```bash
   git clone https://github.com/KageRyo/Bybit-Predict.git
   cd Bybit-Predict
   ```

2. 安裝所需依賴：
   ```bash
   pip install discord
   pip install numpy
   pip install pybit
   ```

## 使用方法

1. 編輯 `config.json` 文件，輸入 Bybit API 金鑰和 Discord 機器人 Token（請見 [配置](#配置)）。
2. 將 Discord 機器人加入您的伺服器並授予必要權限。
3. 執行主程式：
   ```bash
   python main.py
   ```

## 配置

修改 `config.json` 文件，需包含：
- **Bybit API 金鑰與密鑰**：從 Bybit 帳戶獲取。
- **Discord 機器人 Token**：從 Discord 開發者門戶生成。
- **其他設定**：根據需求調整預測參數或日誌設定。

範例 `config.json`：
```json
{
  "bybit_api_key": "您的_BYBIT_API_金鑰",
  "bybit_api_secret": "您的_BYBIT_API_密鑰",
  "discord_bot_token": "您的_DISCORD_BOT_Token"
}
```

請參閱 Bybit API 文件和 Discord 開發者平臺以獲取詳細設定指引。

## 支援語言

- 正體中文
- 歡迎貢獻其他語言！

## 貢獻

我們歡迎社區貢獻！貢獻方式如下：
1. Fork 本專案。
2. 創建功能分支（`git checkout -b feature/您的功能`）。
3. 提交更改（`git commit -m '新增您的功能'`）。
4. 推送分支（`git push origin feature/您的功能`）。
5. 開啟 Pull Request。

如發現錯誤或有改進建議，請透過 [Issues](https://github.com/KageRyo/Bybit-Predict/issues) 提出。

## License

本專案採用 [GPL-2.0 許可證](LICENSE)。詳情請見 LICENSE 文件。

## 聯繫方式

如有疑問或需要支援，請聯繫：[hello@coderyo.com](mailto:hello@coderyo.com)。

## 免責聲明

加密貨幣投資存在重大風險。本軟體僅供參考，不構成財務建議。使用者需自行承擔投資決策及其結果。
