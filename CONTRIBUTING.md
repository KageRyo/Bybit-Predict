# Contributing to Bybit-Predict

Thanks for helping improve Bybit-Predict. The project is maintained by CodeRyo
Studio and welcomes bug fixes, documentation improvements, tests, and new
strategies.

## Before you start

- Read the open [issues](https://github.com/KageRyo/Bybit-Predict/issues) and
  comment before starting a larger change.
- Small, newcomer-friendly tasks are labeled
  [`good first issue`](https://github.com/KageRyo/Bybit-Predict/labels/good%20first%20issue).
- Never commit API keys, Discord tokens, `.env` files, or generated market data.

## Development setup

```bash
git clone https://github.com/KageRyo/Bybit-Predict.git
cd Bybit-Predict
uv venv --python 3.11 .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
uv pip install -e ".[dev]"
```

Run the same checks used by CI before opening a pull request:

```bash
ruff check .
ruff format --check .
pyright
pytest
```

The test command fails if total coverage drops below **80%**. Coverage is
currently about 86%, so the floor allows small differences between platforms
and dependency versions but still catches a large drop. Pyright runs in basic
mode but treats missing imports as errors; the `.[dev]` extra installs the
dependencies it expects.

## Protected main branch

`main` accepts changes only through a pull request. The pull request must pass
all four required CI jobs: `Python 3.11`, `Python 3.12`, `Python 3.13`, and
`Build package distribution`. Direct pushes, force pushes, and deletion of
`main` are blocked. Because the project has a single maintainer, no approving
review is required. Administrators are not exempt: they must also use a pull
request that passes the required checks.

## Branches and pull requests

Use the following branch convention for every contribution:

```text
feature/<issue-number>-<short-description>
```

For example: `feature/20-bybit-v5-client`.

Keep each PR focused on one issue or one independently reviewable change. Add
tests for behavior changes, update both README files when user-facing
behavior changes, and explain the checks you ran in the PR description.

## Design guidelines

- Keep strategies deterministic: candles in, immutable result out.
- Keep Bybit access in `market/`; strategies must not import `pybit`.
- Keep Discord and CLI modules as interfaces only; do not put analysis logic in
  them.
- Use public Bybit market endpoints without credentials.
- Describe outputs as market-analysis signals or reference levels, never as
  investment advice or a guarantee.

## License and attribution

By contributing, you agree that your contribution is licensed under
GPL-2.0-or-later. Retain existing copyright and SPDX notices. Your contribution is
credited through Git history and the project contributors record.
