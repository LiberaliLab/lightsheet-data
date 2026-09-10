"""Fetch reference light-sheet microscopy OME-Zarr datasets from Zenodo.

    import lsdata
    lsdata.info()
    path = lsdata.download('001-mini', 'v0.1')
"""

from __future__ import annotations

from pathlib import Path

from . import _cache, _zenodo
from ._datasets import DatasetInfo, datasets_from_record

__version__ = "0.1.0"
__all__ = ["DatasetInfo", "info", "download", "clear_cache"]


def _resolve(version: str | None) -> dict:
    try:
        versions = _zenodo.get_versions()
    except Exception:
        if version is None or version.lower() == "latest":
            raise
        cached = _cache.load_cached_record(version)
        if cached is None:
            raise
        return cached
    record = _zenodo.resolve_version(version, versions)
    _cache.save_record(record["metadata"]["version"], record)
    return record


def info(version: str | None = None) -> list[DatasetInfo]:
    """Print and return the datasets available for `version` (default: latest)."""
    record = _resolve(version)
    entries = datasets_from_record(record)

    resolved_version = record["metadata"]["version"]
    print(f"Datasets available for version {resolved_version}:\n")
    name_w = max((len(d.name) for d in entries), default=4)
    for d in entries:
        print(f"  {d.name:<{name_w}}  {d.size_gb:>7.2f} GB  {d.description}")

    return entries


def download(name: str, version: str | None = None) -> Path:
    """Download (if needed), verify, and extract dataset `name` at `version`
    (default: latest). Returns the path to the dataset's root directory
    (e.g. containing raw.ome.zarr, deconv.ome.zarr, ...) — if the archive
    contains a single top-level folder, that folder is returned directly
    rather than the cache's own nesting level."""
    record = _resolve(version)
    entries = {d.name: d for d in datasets_from_record(record)}

    dataset = entries.get(name)
    if dataset is None:
        available = ", ".join(sorted(entries))
        raise ValueError(f"Unknown dataset {name!r}. Available datasets: {available}")

    return _cache.ensure_downloaded(dataset)


def clear_cache(name: str | None = None, version: str | None = None) -> list[Path]:
    """Delete cached dataset(s) from local disk and return the paths removed.

    - clear_cache(): wipe the entire cache (all versions, all datasets).
    - clear_cache(version='v0.1'): wipe everything cached for that version.
    - clear_cache(name='001-mini'): wipe that dataset across all cached versions.
    - clear_cache(name='001-mini', version='v0.1'): wipe just that one entry.
    """
    return _cache.clear(name, version)
