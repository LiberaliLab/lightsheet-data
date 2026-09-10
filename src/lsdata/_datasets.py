"""Turn a Zenodo record's file listing into dataset entries."""

from __future__ import annotations

import re
from dataclasses import dataclass

_NAME_RE = re.compile(r"^(?P<base>\d+)-(?P<size>mini|small|full)(?P<variant>-lowT|-varT)?$")

_SIZE_DESC = {
    "full": "Full movie, all 667 frames.",
    "small": "Contiguous time-slice subsample, ~50 frames.",
    "mini": "Contiguous time-slice subsample, 5 frames.",
}

_VARIANT_DESC = {
    "-lowT": " Reduced temporal resolution.",
    "-varT": " Simulated variable acquisition rate.",
}

_GENERIC_DESC = "Light-sheet microscopy dataset from the lightsheet-data Zenodo record."


@dataclass(frozen=True)
class DatasetInfo:
    name: str
    version: str
    size_gb: float
    description: str
    size_bytes: int
    checksum_md5: str
    download_url: str


def _describe(name: str) -> str:
    match = _NAME_RE.match(name)
    if not match:
        return _GENERIC_DESC
    desc = _SIZE_DESC[match.group("size")]
    variant = match.group("variant")
    if variant:
        desc += _VARIANT_DESC[variant]
    return desc


def datasets_from_record(record: dict) -> list[DatasetInfo]:
    """Build DatasetInfo entries from a resolved Zenodo record's file listing."""
    version = record["metadata"]["version"]
    result = []
    for f in record["files"]:
        if not f["key"].endswith(".zip"):
            continue
        name = f["key"][: -len(".zip")]
        checksum = f["checksum"]
        checksum_md5 = checksum.split(":", 1)[1] if ":" in checksum else checksum
        result.append(
            DatasetInfo(
                name=name,
                version=version,
                size_gb=round(f["size"] / 1e9, 2),
                description=_describe(name),
                size_bytes=f["size"],
                checksum_md5=checksum_md5,
                download_url=f["links"]["self"],
            )
        )
    return sorted(result, key=lambda d: d.name)
