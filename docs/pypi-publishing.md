# PyPI publishing

Bybit-Predict v4.1.1 introduces distribution validation and automated PyPI
publishing. The workflow builds both an sdist and a universal wheel from a
release tag, validates their metadata and rendered README, verifies the GPL
license is packaged, and smoke-tests the installed wheel's console script.

It follows this project's HalfRand release pattern: a final SemVer tag builds
and validates the artifacts, publishes them through
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/), then
creates a GitHub Release with those exact artifacts attached. The publish job
receives job-scoped `id-token: write` permission and exchanges GitHub Actions'
OIDC identity for a short-lived PyPI credential; no long-lived `PYPI_TOKEN` is
used.

## One-time maintainer setup

These steps require a verified PyPI account with permission to create a
project. They cannot be completed from this repository alone.

1. In GitHub repository settings, create a protected environment named `release`
   and require the release maintainer as an approver. The workflow separately
   verifies that every release tag is reachable from `main`.
2. In PyPI, open **Account settings → Publishing → Add a new pending
   publisher**, select GitHub, and enter:

   | Setting | Value |
   | --- | --- |
   | PyPI project name | `bybit-predict` |
   | Owner | `KageRyo` |
   | Repository | `Bybit-Predict` |
   | Workflow filename | `release.yml` |
   | Environment name | `release` |

A pending publisher does not reserve a PyPI project name. Publish promptly
after configuring it; otherwise another account may claim the name first.

## Release procedure

1. Merge a release-preparation PR that changes the package version from its
   alpha form (for example `4.1.1a0`) to the final version (`4.1.1`) and dates
   the changelog entry. Confirm main CI is green.
2. Create and push the annotated release tag (for example `v4.1.1`) at that
   verified main commit. The publishing workflow rejects an untagged ref, a tag
   that is not reachable from `main`, or a tag whose version differs from
   `pyproject.toml`.
3. Push the tag. The `release.yml` workflow verifies the tag is reachable from
   `main` and matches `pyproject.toml`, builds and validates the distributions,
   waits for the protected `release` environment approval, then publishes to
   PyPI. Only after that succeeds does it create the GitHub Release and attach
   the exact wheel and sdist.
4. Verify `python -m pip install bybit-predict==4.1.1` from a fresh virtual
   environment and run `bybit-predict --help`.

Do not add PyPI API tokens to GitHub secrets. If a release must be stopped,
stop the GitHub deployment or revoke the PyPI Trusted Publisher rather than
introducing a credential-based bypass.
