# PyPI publishing

Bybit-Predict is distributed through PyPI. The workflow builds both an sdist
and a universal wheel from each release tag, validates their metadata and
rendered README, verifies the GPL license is packaged, and smoke-tests the
installed wheel's console script.

A final SemVer tag builds and validates the artifacts, publishes them through
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/), then
creates a GitHub Release with those exact artifacts attached. The publish job
receives job-scoped `id-token: write` permission and exchanges GitHub Actions'
OIDC identity for a short-lived PyPI credential; no long-lived `PYPI_TOKEN` is
used.

## Maintainer setup

This setup is already done for `bybit-predict`. Repeat it only if the GitHub
environment or the PyPI trusted publisher needs to be recreated.

1. In GitHub repository settings, create a protected environment named `release`
   and require the release maintainer as an approver. The workflow separately
   verifies that every release tag is reachable from `main`.
2. On PyPI, open **Your projects → `bybit-predict` → Manage → Publishing**, add
   a GitHub publisher, and enter:

   | Setting | Value |
   | --- | --- |
   | Owner | `KageRyo` |
   | Repository | `Bybit-Predict` |
   | Workflow filename | `release.yml` |
   | Environment name | `release` |

## Release procedure

1. Merge a release-preparation PR that sets the package and runtime versions to
   the immutable final PEP 440 value (for example `4.1.2`) and dates the
   changelog entry. Confirm main CI is green.
2. Create the annotated release tag (`v<version>`, for example `v4.1.2`) at
   that verified main commit.
3. Push the tag. The `release.yml` workflow rejects a tag that is not reachable
   from `main` or whose version differs from `pyproject.toml`. It then builds
   and validates the distributions, waits for approval in the protected
   `release` environment, and publishes to PyPI. Only after that succeeds does
   it create the GitHub Release and attach the exact wheel and sdist.
4. Verify `python -m pip install bybit-predict==<version>` from a fresh virtual
   environment and run `bybit-predict --help`.

Do not add PyPI API tokens to GitHub secrets. To stop a release, stop the
GitHub deployment or revoke the PyPI Trusted Publisher.
