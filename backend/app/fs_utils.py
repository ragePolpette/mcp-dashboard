"""Filesystem helpers shared by the dashboard state stores."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_bytes(path: Path, data: bytes, *, mode: int | None = None) -> None:
    """Write data to a temporary file in the same directory, then atomically replace path.

    Without an explicit mode the permissions of an existing target are kept, and new
    files get 0644 rather than the 0600 that mkstemp would leave behind.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode is None:
        try:
            mode = target.stat().st_mode & 0o777
        except OSError:
            mode = 0o644
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_name, mode)
        os.replace(tmp_name, target)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def atomic_write_text(path: Path, text: str, *, mode: int | None = None) -> None:
    atomic_write_bytes(path, text.encode("utf-8"), mode=mode)


def atomic_write_json(path: Path, payload: Any, *, mode: int | None = None) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=True, indent=2), mode=mode)


__all__ = ["atomic_write_bytes", "atomic_write_json", "atomic_write_text"]
