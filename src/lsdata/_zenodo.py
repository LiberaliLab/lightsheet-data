"""Client for the Zenodo REST API, scoped to the lightsheet-data record."""

from __future__ import annotations

import requests

# Any known record id belonging to the concept. Zenodo's /versions endpoint
# is concept-scoped, so this keeps resolving *all* versions (including future
# ones) even though the id below only names one specific version.
ANCHOR_RECORD_ID = "22078388"

API_BASE = "https://zenodo.org/api/records"


def get_versions() -> list[dict]:
    """Return the raw Zenodo record JSON for every published version."""
    resp = requests.get(f"{API_BASE}/{ANCHOR_RECORD_ID}/versions", timeout=30)
    resp.raise_for_status()
    return resp.json()["hits"]["hits"]


def _normalize_version(version: str) -> str:
    return version.lower().lstrip("v")


def resolve_version(version: str | None, versions: list[dict] | None = None) -> dict:
    """Return the record JSON matching `version` ('latest'/None picks the newest)."""
    versions = versions if versions is not None else get_versions()
    if not versions:
        raise RuntimeError("Zenodo returned no versions for this record")

    if version is None or version.lower() == "latest":
        return max(versions, key=lambda v: v["created"])

    target = _normalize_version(version)
    for record in versions:
        if _normalize_version(record["metadata"]["version"]) == target:
            return record

    available = ", ".join(sorted(r["metadata"]["version"] for r in versions))
    raise ValueError(f"Unknown version {version!r}. Available versions: {available}")


def file_checksum(file_entry: dict) -> str:
    """Extract the bare hex MD5 from a Zenodo file entry's 'checksum' field."""
    checksum = file_entry["checksum"]
    return checksum.split(":", 1)[1] if ":" in checksum else checksum
