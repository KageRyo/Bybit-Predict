# Contributing to Bybit-Predict

Thanks for helping improve Bybit-Predict. The project is maintained by CodeRyo
Studio and welcomes bug fixes, documentation improvements, tests, and new
strategies.

## Before you start

- Read the open [issues](https://github.com/KageRyo/Bybit-Predict/issues) and
  comment before starting a larger change.
- Small, newcomer-friendly tasks are labelled
  [`good first issue`](https://github.com/KageRyo/Bybit-Predict/labels/good%20first%20issue).
- Never commit API keys, Discord tokens, `.env` files, or generated market data.

## Development setup

```bash
git clone https://github.com/KageRyo/Bybit-Predict.git
cd Bybit-Predict
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the same checks used by CI before opening a pull request:

```bash
ruff check .
ruff format --check .
pyright
pytest
```

## Branches and pull requests

Use the following branch convention for every contribution:

```text
feature/<issue-number>-<short-description>
```

For example: `feature/20-bybit-v5-client`.

Keep each PR focused on one issue or one independently reviewable change. Add
tests for behaviour changes, update both README files when user-facing
behaviour changes, and explain the checks you ran in the PR description.

## Design guidelines

- Keep strategies deterministic: candles in, immutable result out.
- Keep Bybit access in `market/`; strategies must not import `pybit`.
- Keep Discord and CLI modules as interfaces only; do not put analysis logic in
  them.
- Use public Bybit market endpoints without credentials unless an explicitly
  authenticated feature is added in the future.
- Describe outputs as market-analysis signals or reference levels, never as
  guaranteed investment advice.

## License and attribution

By contributing, you agree that your contribution is licensed under
GPL-2.0-only. Retain existing copyright and SPDX notices. Your contribution is
credited through Git history and the project contributors record.
