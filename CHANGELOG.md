# Changelog

All notable changes to Bybit-Predict are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project follows [Semantic Versioning](https://semver.org/).

## [4.1.3] - 2026-08-12

### Fixed

- Restored the complete official GNU General Public License version 2 text in
  the distributed `LICENSE` file.

### Changed

- Updated GitHub Actions artifact dependencies and the development Twine
  requirement used by CI.
- Pin build metadata to Core Metadata 2.4 until release-validation tooling
  supports 2.5.

## [4.1.2] - 2026-08-09

### Fixed

- Corrected released-version labels in the English and 正體中文 README files.
- Replaced stale future-release references in release and legacy migration
  documentation.

### Changed

- PyPI metadata now describes the reproducible backtesting toolkit and includes
  matching discovery keywords.
- Labelled the Chinese documentation as 正體中文.
- CLI help now names both market analysis and reproducible backtesting.

## [4.1.1] - 2026-08-09

### Added

- PyPI distribution metadata, package-artifact verification, and a Trusted
  Publishing workflow for future releases.

### Changed

- Installation documentation now prioritizes PyPI and pipx usage after the
  first PyPI release.

## [4.1.0] - 2026-08-09

### Added

- Reproducible historical backtesting with explicit UTC ranges, saved normalized
  candle CSV input, declared execution assumptions, performance metrics, and
  buy-and-hold plus SMA direction baselines.
- Historical Bybit V5 candle pagination for date-range evaluation.

## [4.0.0] - 2026-08-09

### Added

- Installable `bybit_predict` package and CLI.
- Bybit V5 public market-data client with typed candles.
- Stateless legacy rule-based signal strategy.
- Discord slash-command interface and environment-based configuration.
- Automated tests, linting, type checks, CI, and dependency updates.

### Changed

- Public market analysis no longer requires Bybit API credentials.
- Discord configuration now uses environment variables instead of a tracked JSON file.
- `LegacyRuleBasedStrategy` intentionally uses the complete analysis window,
  UTC time handling, and correctly aligned bearish Fibonacci labels. See
  [legacy strategy migration notes](docs/legacy-strategy-changes.md).

## [3.1] - Legacy release

- Latest release before the v4 architecture modernization.
