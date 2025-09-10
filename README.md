# Bybit-Predict

![Bybit-Predict](https://img.shields.io/badge/License-GPL--2.0-blue.svg)  
Predict cryptocurrency price trends using Python and the Bybit exchange API.

## Overview

Bybit-Predict is an open-source project designed to analyze and predict cryptocurrency price trends using the Bybit exchange API. Integrated with Discord for seamless user interaction, this tool provides a reference for market analysis while prioritizing user privacy by requiring no data uploads to developers.

> **⚠️ Disclaimer**: All investments carry inherent risks. This software provides reference insights only. The development team does not guarantee investment performance, and users are solely responsible for their financial decisions.

## Features

- **Trend Prediction**: Leverages Bybit API to forecast cryptocurrency price movements.
- **Discord Integration**: Control and monitor predictions through a Discord bot.
- **Privacy-Focused**: No personal data is shared with developers.
- **Open Source**: Licensed under GPL-2.0, encouraging community contributions.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Supported Languages](#supported-languages)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Disclaimer](#disclaimer)

## Installation

### Prerequisites
- Python 3.8 or higher
- Git
- A Bybit account with API keys
- A Discord bot token

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/KageRyo/Bybit-Predict.git
   cd Bybit-Predict
   ```

2. Install required dependencies:
   ```bash
   pip install discord
   pip install numpy
   pip install pybit
   ```

## Usage

1. Configure the `config.json` file with your Bybit API keys and Discord bot token (see [Configuration](#configuration)).
2. Add your Discord bot to your server and grant necessary permissions.
3. Run the main script:
   ```bash
   python main.py
   ```

## Configuration

Edit the `config.json` file to include:
- **Bybit API Key and Secret**: Obtain from your Bybit account.
- **Discord Bot Token**: Generate from the Discord Developer Portal.
- **Other Settings**: Adjust prediction parameters or logging preferences as needed.

Example `config.json`:
```json
{
  "bybit_api_key": "YOUR_BYBIT_API_KEY",
  "bybit_api_secret": "YOUR_BYBIT_API_SECRET",
  "discord_bot_token": "YOUR_DISCORD_BOT_TOKEN"
}
```

Refer to the Bybit API documentation and Discord Developer Portal for detailed setup instructions.

## Supported Languages

- Traditional Chinese (正體中文)
- Contributions for additional languages are welcome!

## Contributing

We welcome contributions from the community! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add YourFeature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a Pull Request.

Please report bugs or suggest improvements via [Issues](https://github.com/KageRyo/Bybit-Predict/issues).

## License

This project is licensed under the [GPL-2.0 License](LICENSE). See the LICENSE file for details.

## Contact

For questions or support, email: [hello@coderyo.com](mailto:hello@coderyo.com).

## Disclaimer

Investing in cryptocurrencies involves significant risks. This software is for informational purposes only and does not constitute financial advice. Users are responsible for their own investment decisions and outcomes.
