# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Descriptor-relative dataset I/O for untrusted CLI paths."""

from __future__ import annotations

import contextlib
import errno
import hashlib
import json
import os
import secrets
import stat
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from bybit_predict.backtest.data import (
    MANIFEST_SUFFIX,
    _build_expected_manifest,
    _parse_candles_csv_bytes,
    _parse_manifest,
    _serialize_candles_csv,
    _serialize_manifest,
    _validate_manifest_matches,
)
from bybit_predict.backtest.models import DatasetManifest
from bybit_predict.exceptions import BacktestError
from bybit_predict.models import Candle

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows has no fcntl module
    fcntl = None  # type: ignore[assignment]


_SAFE_DESCRIPTOR_IO = (
    os.name == "posix"
    and fcntl is not None
    and hasattr(os, "O_DIRECTORY")
    and hasattr(os, "O_NOFOLLOW")
    and all(
        operation in os.supports_dir_fd
        for operation in (os.open, os.mkdir, os.unlink, os.stat, os.link, os.rename)
    )
)

_TEMP_FILE_PREFIX = ".bybit-predict-temp-"
_BACKUP_FILE_PREFIX = ".bybit-predict-backup-"
_TEMP_NAME_ATTEMPTS = 32


@dataclass(frozen=True, slots=True)
class _OpenedDatasetParent:
    root_fd: int
    parent_fd: int


@dataclass(frozen=True, slots=True)
class SafeDatasetPath:
    """A CLI dataset path reduced to trusted-root-relative components."""

    trusted_root: Path
    relative_parts: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not self.trusted_root.is_absolute()
            or not self.relative_parts
            or any(
                part in {"", ".", ".."} or Path(part).is_absolute() or Path(part).parts != (part,)
                for part in self.relative_parts
            )
        ):
            raise ValueError("Safe dataset paths must contain normal relative components")

    @property
    def csv_name(self) -> str:
        return self.relative_parts[-1]

    @property
    def manifest_name(self) -> str:
        return f"{self.csv_name}{MANIFEST_SUFFIX}"

    @property
    def display_csv_path(self) -> Path:
        return self.trusted_root.joinpath(*self.relative_parts)

    @property
    def display_manifest_path(self) -> Path:
        return self.display_csv_path.with_name(self.manifest_name)


def load_candles_csv_safely(
    path: SafeDatasetPath,
    *,
    symbol: str,
    category: str,
    interval: str,
    requested_start: datetime,
    requested_end: datetime,
) -> tuple[Candle, ...]:
    """Load a CLI dataset through descriptor-relative, no-follow file handles."""
    expected = _build_expected_manifest(
        symbol=symbol,
        category=category,
        interval=interval,
        requested_start=requested_start,
        requested_end=requested_end,
    )
    manifest_bytes, csv_bytes = _read_dataset_files(path)
    try:
        raw_manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise BacktestError(
            f"Could not read dataset manifest JSON {path.display_manifest_path}: {error}"
        ) from error
    manifest = _parse_manifest(raw_manifest, path.display_manifest_path)
    _validate_manifest_matches(manifest, expected)
    actual_content_sha256 = hashlib.sha256(csv_bytes).hexdigest()
    if actual_content_sha256 != manifest.content_sha256:
        raise BacktestError(
            "Dataset content hash mismatch: "
            f"manifest={manifest.content_sha256} actual={actual_content_sha256}"
        )
    return _parse_candles_csv_bytes(csv_bytes, path.display_csv_path)


def save_candles_csv_safely(
    path: SafeDatasetPath,
    candles: tuple[Candle, ...],
    *,
    symbol: str,
    category: str,
    interval: str,
    requested_start: datetime,
    requested_end: datetime,
) -> DatasetManifest:
    """Save a CLI dataset through descriptor-relative, no-follow file handles."""
    metadata = _build_expected_manifest(
        symbol=symbol,
        category=category,
        interval=interval,
        requested_start=requested_start,
        requested_end=requested_end,
    )
    csv_bytes = _serialize_candles_csv(candles)
    manifest = DatasetManifest(
        schema_version=metadata.schema_version,
        symbol=metadata.symbol,
        category=metadata.category,
        interval=metadata.interval,
        source=metadata.source,
        requested_start=metadata.requested_start,
        requested_end=metadata.requested_end,
        generated_at=metadata.generated_at,
        content_sha256=hashlib.sha256(csv_bytes).hexdigest(),
    )
    manifest_bytes = _serialize_manifest(manifest)
    _write_dataset_files(path, csv_bytes, manifest_bytes)
    return manifest


def _read_dataset_files(path: SafeDatasetPath) -> tuple[bytes, bytes]:
    try:
        with (
            _open_dataset_parent(path, create=False) as opened,
            _dataset_lock(opened.parent_fd, exclusive=False),
            contextlib.ExitStack() as stack,
        ):
            _require_directory_beneath(opened.root_fd, opened.parent_fd)
            try:
                manifest_fd = os.open(
                    path.manifest_name,
                    os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
                    dir_fd=opened.parent_fd,
                )
            except FileNotFoundError as error:
                raise BacktestError(
                    f"Dataset manifest is required at {path.display_manifest_path}; "
                    "save the CSV with --save-data"
                ) from error
            manifest_file = stack.enter_context(os.fdopen(manifest_fd, "rb"))
            _require_regular_file(manifest_fd)
            _require_directory_beneath(opened.root_fd, opened.parent_fd)
            try:
                csv_fd = os.open(
                    path.csv_name,
                    os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
                    dir_fd=opened.parent_fd,
                )
            except FileNotFoundError as error:
                raise BacktestError(
                    f"Could not read candle CSV {path.display_csv_path}: {error}"
                ) from error
            csv_file = stack.enter_context(os.fdopen(csv_fd, "rb"))
            _require_regular_file(csv_fd)
            _require_directory_beneath(opened.root_fd, opened.parent_fd)
            manifest_bytes = manifest_file.read()
            csv_bytes = csv_file.read()
            _require_directory_beneath(opened.root_fd, opened.parent_fd)
            return manifest_bytes, csv_bytes
    except BacktestError:
        raise
    except FileNotFoundError as error:
        raise BacktestError(
            f"Dataset manifest is required at {path.display_manifest_path}; "
            "save the CSV with --save-data"
        ) from error
    except OSError as error:
        raise BacktestError(
            f"Could not safely read dataset files below the trusted root for "
            f"{path.display_csv_path}: {error}"
        ) from error


def _write_dataset_files(path: SafeDatasetPath, csv_bytes: bytes, manifest_bytes: bytes) -> None:
    try:
        with (
            _open_dataset_parent(path, create=True) as opened,
            _dataset_lock(opened.parent_fd, exclusive=True),
        ):
            _write_dataset_pair(
                opened.root_fd,
                opened.parent_fd,
                (
                    (path.csv_name, csv_bytes),
                    (path.manifest_name, manifest_bytes),
                ),
            )
    except OSError as error:
        raise BacktestError(
            f"Could not safely write dataset files below the trusted root for "
            f"{path.display_csv_path}: {error}"
        ) from error


def _write_dataset_pair(
    root_fd: int,
    parent_fd: int,
    files: tuple[tuple[str, bytes], tuple[str, bytes]],
) -> None:
    """Install two dataset files with per-file atomic replacement and rollback."""
    temporary_names: list[str] = []
    backup_names: dict[str, str] = {}
    installed_names: set[str] = set()
    target_names = tuple(name for name, _ in files)
    try:
        _require_directory_beneath(root_fd, parent_fd)
        for _, content in files:
            temporary_names.append(_create_temporary_file(parent_fd, content))
        _require_directory_beneath(root_fd, parent_fd)

        for name in target_names:
            backup_name = _backup_existing_file(parent_fd, name)
            if backup_name is not None:
                backup_names[name] = backup_name
        _require_directory_beneath(root_fd, parent_fd)

        for (name, _), temporary_name in zip(files, tuple(temporary_names), strict=True):
            _require_directory_beneath(root_fd, parent_fd)
            _rename_relative(parent_fd, temporary_name, name)
            temporary_names.remove(temporary_name)
            installed_names.add(name)
        _require_directory_beneath(root_fd, parent_fd)
        os.fsync(parent_fd)
    except OSError:
        _rollback_dataset_pair(
            parent_fd,
            target_names,
            temporary_names,
            backup_names,
            installed_names,
        )
        raise
    else:
        _cleanup_relative_names(parent_fd, temporary_names)
        _cleanup_relative_names(parent_fd, backup_names.values())


def _create_temporary_file(parent_fd: int, content: bytes) -> str:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
    for _ in range(_TEMP_NAME_ATTEMPTS):
        name = f"{_TEMP_FILE_PREFIX}{secrets.token_hex(16)}"
        try:
            file_descriptor = os.open(name, flags, 0o600, dir_fd=parent_fd)
        except FileExistsError:
            continue
        try:
            _require_regular_file(file_descriptor, reject_hard_links=True)
            try:
                _write_file_contents(file_descriptor, content)
            finally:
                os.close(file_descriptor)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(name, dir_fd=parent_fd)
            raise
        return name
    raise OSError(errno.EEXIST, "could not allocate a unique temporary dataset file")


def _backup_existing_file(parent_fd: int, name: str) -> str | None:
    try:
        _require_existing_output_file(parent_fd, name)
    except FileNotFoundError:
        return None

    for _ in range(_TEMP_NAME_ATTEMPTS):
        backup_name = f"{_BACKUP_FILE_PREFIX}{secrets.token_hex(16)}"
        try:
            os.link(
                name,
                backup_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileExistsError:
            continue
        except FileNotFoundError:
            return None
        return backup_name
    raise OSError(errno.EEXIST, "could not allocate a unique dataset backup file")


def _require_existing_output_file(parent_fd: int, name: str) -> None:
    file_stat = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISREG(file_stat.st_mode):
        raise OSError(errno.EINVAL, "dataset output must be a regular file")
    if file_stat.st_nlink > 1:
        raise OSError(errno.EMLINK, "dataset output must not be a hard link")


def _rename_relative(parent_fd: int, source: str, destination: str) -> None:
    """Atomically replace a sibling name without resolving either path anew."""
    os.rename(
        source,
        destination,
        src_dir_fd=parent_fd,
        dst_dir_fd=parent_fd,
    )


def _rollback_dataset_pair(
    parent_fd: int,
    target_names: tuple[str, ...],
    temporary_names: list[str],
    backup_names: dict[str, str],
    installed_names: set[str],
) -> None:
    rollback_error: OSError | None = None
    for name in reversed(target_names):
        backup_name = backup_names.get(name)
        try:
            if name in installed_names:
                if backup_name is None:
                    os.unlink(name, dir_fd=parent_fd)
                else:
                    _rename_relative(parent_fd, backup_name, name)
                    with contextlib.suppress(OSError):
                        os.unlink(backup_name, dir_fd=parent_fd)
                    backup_names.pop(name, None)
            elif backup_name is not None:
                _rename_relative(parent_fd, backup_name, name)
                with contextlib.suppress(OSError):
                    os.unlink(backup_name, dir_fd=parent_fd)
                backup_names.pop(name, None)
        except OSError as error:
            rollback_error = rollback_error or error
    _cleanup_relative_names(parent_fd, temporary_names)
    _cleanup_relative_names(parent_fd, backup_names.values())
    if rollback_error is not None:
        raise OSError(
            errno.EIO, f"dataset write rollback failed: {rollback_error}"
        ) from rollback_error


def _cleanup_relative_names(parent_fd: int, names: Iterable[str]) -> None:
    for name in names:
        with contextlib.suppress(OSError):
            os.unlink(name, dir_fd=parent_fd)


@contextlib.contextmanager
def _dataset_lock(directory_fd: int, *, exclusive: bool) -> Iterator[None]:
    if fcntl is None:
        raise BacktestError("Secure CLI dataset I/O requires POSIX advisory locking support")
    operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    fcntl.flock(directory_fd, operation)
    try:
        yield
    finally:
        fcntl.flock(directory_fd, fcntl.LOCK_UN)


def _write_file_contents(file_descriptor: int, content: bytes) -> None:
    view = memoryview(content)
    while view:
        written = os.write(file_descriptor, view)
        if written <= 0:
            raise OSError(errno.EIO, "dataset file write made no progress")
        view = view[written:]
    os.fsync(file_descriptor)


def _require_regular_file(file_descriptor: int, *, reject_hard_links: bool = False) -> None:
    file_stat = os.fstat(file_descriptor)
    if not stat.S_ISREG(file_stat.st_mode):
        raise OSError(errno.EINVAL, "dataset path must reference a regular file")
    if reject_hard_links and file_stat.st_nlink > 1:
        raise OSError(errno.EMLINK, "dataset output must not be a hard link")


@contextlib.contextmanager
def _open_dataset_parent(path: SafeDatasetPath, *, create: bool) -> Iterator[_OpenedDatasetParent]:
    if not _SAFE_DESCRIPTOR_IO:
        raise BacktestError(
            "Secure CLI dataset I/O requires POSIX descriptor-relative no-follow support"
        )
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    root_fd = os.open(path.trusted_root, directory_flags)
    current_fd = root_fd
    try:
        for component in path.relative_parts[:-1]:
            next_fd = _open_directory_at(
                current_fd, component, create=create, flags=directory_flags
            )
            try:
                _require_directory_beneath(root_fd, next_fd)
            except OSError:
                os.close(next_fd)
                raise
            if current_fd != root_fd:
                os.close(current_fd)
            current_fd = next_fd
        _require_directory_beneath(root_fd, current_fd)
        yield _OpenedDatasetParent(root_fd=root_fd, parent_fd=current_fd)
    finally:
        if current_fd != root_fd:
            os.close(current_fd)
        os.close(root_fd)


def _require_directory_beneath(root_fd: int, directory_fd: int) -> None:
    """Reject a directory FD whose current ancestry no longer reaches root_fd."""
    root_stat = os.fstat(root_fd)
    current_fd = os.dup(directory_fd)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        while True:
            current_stat = os.fstat(current_fd)
            if current_stat.st_dev == root_stat.st_dev and current_stat.st_ino == root_stat.st_ino:
                return
            parent_fd: int | None = None
            try:
                parent_fd = os.open("..", directory_flags, dir_fd=current_fd)
                parent_stat = os.fstat(parent_fd)
            except OSError:
                if parent_fd is not None:
                    os.close(parent_fd)
                raise
            os.close(current_fd)
            assert parent_fd is not None
            current_fd = parent_fd
            if (
                parent_stat.st_dev == current_stat.st_dev
                and parent_stat.st_ino == current_stat.st_ino
            ):
                break
    finally:
        os.close(current_fd)
    raise OSError(errno.EXDEV, "dataset directory moved outside the trusted root")


def _open_directory_at(parent_fd: int, name: str, *, create: bool, flags: int) -> int:
    try:
        return os.open(name, flags, dir_fd=parent_fd)
    except FileNotFoundError:
        if not create:
            raise
        with contextlib.suppress(FileExistsError):
            os.mkdir(name, 0o755, dir_fd=parent_fd)
        return os.open(name, flags, dir_fd=parent_fd)
