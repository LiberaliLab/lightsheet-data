"""Local cache: download, checksum-verify, and extract dataset archives."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

import requests
from platformdirs import user_cache_dir

from ._datasets import DatasetInfo
from ._zenodo import _normalize_version

_COMPLETE_MARKER = ".lsdata_complete"
_CHUNK_SIZE = 1024 * 1024  # 1MB


def cache_root() -> Path:
    override = os.environ.get("LSDATA_CACHE_DIR")
    return Path(override) if override else Path(user_cache_dir("lsdata"))


def record_cache_path(version: str) -> Path:
    return cache_root() / version / "record.json"


def save_record(version: str, record: dict) -> None:
    path = record_cache_path(version)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")


def load_cached_record(version: str) -> dict | None:
    path = record_cache_path(version)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _target_dir(dataset: DatasetInfo) -> Path:
    return cache_root() / dataset.version / dataset.name


def _print_progress(downloaded: int, total: int) -> None:
    pct = downloaded / total * 100 if total else 0
    mb = downloaded / 1e6
    total_mb = total / 1e6
    sys.stderr.write(f"\r  {mb:8.1f} / {total_mb:8.1f} MB ({pct:5.1f}%)")
    sys.stderr.flush()


def _download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with dest.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=_CHUNK_SIZE):
                fh.write(chunk)
                downloaded += len(chunk)
                _print_progress(downloaded, total)
    sys.stderr.write("\n")


def _verify_checksum(path: Path, expected_md5: str) -> None:
    digest = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected_md5:
        raise ValueError(
            f"Checksum mismatch for {path.name}: expected {expected_md5}, got {actual}"
        )


def _dataset_root(target: Path) -> Path:
    """If `target`'s only content (besides the completion marker) is a single
    directory, the zip had one top-level dir — treat that as the real dataset
    root instead of adding a redundant nesting level."""
    entries = [p for p in target.iterdir() if p.name != _COMPLETE_MARKER]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return target


def clear(name: str | None = None, version: str | None = None) -> list[Path]:
    """Delete cached data and return the list of directories removed.

    - clear(): wipe the entire cache root (all versions, all datasets).
    - clear(version='v0.1'): wipe everything cached for that version.
    - clear(name='001-mini'): wipe that dataset across all cached versions.
    - clear(name='001-mini', version='v0.1'): wipe just that one entry.

    Version matching tolerates a leading 'v' (like ensure_downloaded()). This
    never hits the network — it only touches what's already on disk, so a
    missing/mismatched name or version is simply a no-op, not an error.
    """
    root = cache_root()
    if not root.exists():
        return []

    if name is None and version is None:
        removed = [root]
        shutil.rmtree(root)
        return removed

    version_dirs = [d for d in root.iterdir() if d.is_dir()]
    if version is not None:
        target_norm = _normalize_version(version)
        version_dirs = [d for d in version_dirs if _normalize_version(d.name) == target_norm]

    removed = []
    for version_dir in version_dirs:
        target = version_dir / name if name is not None else version_dir
        if target.exists():
            shutil.rmtree(target)
            removed.append(target)
    return removed


def ensure_downloaded(dataset: DatasetInfo) -> Path:
    """Download, verify, and extract `dataset` into the cache if not already
    present. Returns the extracted dataset's root directory."""
    target = _target_dir(dataset)
    marker = target / _COMPLETE_MARKER
    if marker.exists():
        return _dataset_root(target)

    target.mkdir(parents=True, exist_ok=True)
    zip_path = target.parent / f"{dataset.name}.zip.part"

    print(f"Downloading {dataset.name} ({dataset.size_gb} GB)...", file=sys.stderr)
    _download(dataset.download_url, zip_path)

    print("Verifying checksum...", file=sys.stderr)
    _verify_checksum(zip_path, dataset.checksum_md5)

    print("Extracting...", file=sys.stderr)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(target)

    zip_path.unlink()
    marker.write_text("", encoding="utf-8")
    return _dataset_root(target)
