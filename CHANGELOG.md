# Changelog

All notable changes to Bybit-Predict are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
