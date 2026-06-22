import shutil
import uuid
from pathlib import Path

import pytest

from app.utils.uploads import (
    build_non_conflicting_path,
    ensure_path_within_directory,
    get_file_extension,
    parse_allowed_extensions,
    sanitize_filename,
)


@pytest.fixture()
def local_tmp_dir() -> Path:
    path = Path("tests") / ".tmp" / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_parse_allowed_extensions_normalizes_values():
    assert parse_allowed_extensions("txt,.MD, markdown,") == {"txt", "md", "markdown"}


def test_get_file_extension_returns_lowercase_suffix():
    assert get_file_extension("Incident.Report.MD") == "md"


def test_sanitize_filename_removes_paths_and_unsafe_chars():
    assert sanitize_filename("../bad name<script>.md") == "bad_name_script_.md"


def test_sanitize_filename_rejects_empty_names():
    with pytest.raises(ValueError, match="文件名不能为空"):
        sanitize_filename("../")


def test_ensure_path_within_directory_allows_child_path(local_tmp_dir: Path):
    upload_root = local_tmp_dir / "uploads"
    upload_root.mkdir()
    child = upload_root / "doc.md"

    assert ensure_path_within_directory(child, upload_root) == child.resolve()


def test_ensure_path_within_directory_rejects_path_escape(local_tmp_dir: Path):
    upload_root = local_tmp_dir / "uploads"
    upload_root.mkdir()
    outside = local_tmp_dir / "outside.md"

    with pytest.raises(ValueError, match="路径必须位于上传目录内"):
        ensure_path_within_directory(outside, upload_root)


def test_build_non_conflicting_path_adds_suffix(local_tmp_dir: Path):
    existing = local_tmp_dir / "doc.md"
    existing.write_text("old", encoding="utf-8")

    assert build_non_conflicting_path(local_tmp_dir, "doc.md") == local_tmp_dir / "doc-1.md"
