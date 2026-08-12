from __future__ import annotations

import tomllib
from pathlib import Path

import bybit_predict


def test_runtime_version_matches_package_metadata() -> None:
    project_root = Path(__file__).parents[2]
    with (project_root / "pyproject.toml").open("rb") as file:
        metadata = tomllib.load(file)

    assert bybit_predict.__version__ == metadata["project"]["version"] == "4.1.4"
