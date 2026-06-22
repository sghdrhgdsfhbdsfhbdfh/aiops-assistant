"""Upload file validation helpers."""

from __future__ import annotations

import re
from pathlib import Path


_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_RESERVED_WINDOWS_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def parse_allowed_extensions(value: str) -> set[str]:
    """Parse comma-separated extension config into normalized values."""
    return {
        extension.strip().lower().lstrip(".")
        for extension in value.split(",")
        if extension.strip()
    }


def get_file_extension(filename: str) -> str:
    """Return lowercase file extension without the leading dot."""
    return Path(filename).suffix.lower().lstrip(".")


def sanitize_filename(filename: str, *, max_length: int = 120) -> str:
    """Convert a user supplied filename into a safe basename."""
    original_name = Path(filename).name.strip().replace(" ", "_")
    sanitized = _UNSAFE_FILENAME_CHARS.sub("_", original_name).strip("._")

    if not sanitized:
        raise ValueError("文件名不能为空")

    stem = Path(sanitized).stem
    suffix = Path(sanitized).suffix
    if stem.upper() in _RESERVED_WINDOWS_NAMES:
        sanitized = f"file_{sanitized}"

    if len(sanitized) > max_length:
        suffix_len = len(suffix)
        stem_limit = max(1, max_length - suffix_len)
        sanitized = f"{Path(sanitized).stem[:stem_limit]}{suffix}"

    return sanitized


def ensure_path_within_directory(path: Path, directory: Path) -> Path:
    """Resolve a path and ensure it stays inside a base directory."""
    resolved_path = path.resolve()
    resolved_directory = directory.resolve()

    try:
        resolved_path.relative_to(resolved_directory)
    except ValueError as exc:
        raise ValueError("路径必须位于上传目录内") from exc

    return resolved_path


def build_non_conflicting_path(directory: Path, filename: str) -> Path:
    """Return a destination path, adding a numeric suffix when needed."""
    destination = directory / filename
    if not destination.exists():
        return destination

    path = Path(filename)
    for index in range(1, 1000):
        candidate = directory / f"{path.stem}-{index}{path.suffix}"
        if not candidate.exists():
            return candidate

    raise ValueError("无法生成唯一文件名")
