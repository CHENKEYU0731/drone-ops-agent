from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, model_validator

from packages.drone_schemas import read_json_file


ALLOWED_DOWNLOAD_HOSTS = {"raw.githubusercontent.com"}
MAX_SOURCE_SIZE_BYTES = 10_000_000


class OpenSourceLogSource(BaseModel):
    source_id: str
    title: str
    repository: str
    commit: str
    source_path: str
    download_url: str
    filename: str
    format: str
    size_bytes: int = Field(gt=0, le=MAX_SOURCE_SIZE_BYTES)
    sha256: str
    license_spdx: str
    license_url: str
    provenance_class: str
    real_world_flight_verified: bool
    usage_note: str

    @model_validator(mode="after")
    def validate_source(self) -> "OpenSourceLogSource":
        parsed = urlparse(self.download_url)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
            raise ValueError(f"source {self.source_id} uses an unsupported download host")
        if not re.fullmatch(r"[0-9a-f]{40}", self.commit):
            raise ValueError(f"source {self.source_id} must pin a 40-character commit")
        if self.commit not in parsed.path:
            raise ValueError(f"source {self.source_id} download URL must include the pinned commit")
        expected_download_path = f"/{self.repository}/{self.commit}/{self.source_path}"
        if parsed.path != expected_download_path:
            raise ValueError(f"source {self.source_id} download URL does not match repository metadata")
        source_path = PurePosixPath(self.source_path)
        if source_path.is_absolute() or ".." in source_path.parts:
            raise ValueError(f"source {self.source_id} has an unsafe source_path")
        if not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise ValueError(f"source {self.source_id} has an invalid SHA-256")
        if self.filename != Path(self.source_path).name or Path(self.filename).name != self.filename:
            raise ValueError(f"source {self.source_id} filename must match source_path")
        if self.format != "px4-ulog" or Path(self.filename).suffix.lower() != ".ulg":
            raise ValueError(f"source {self.source_id} must declare a PX4 ULog file")
        license_url = urlparse(self.license_url)
        if license_url.scheme != "https" or license_url.hostname != "github.com" or self.commit not in license_url.path:
            raise ValueError(f"source {self.source_id} license URL must pin the same commit")
        return self


class OpenSourceLogRegistry(BaseModel):
    schema_version: int
    registry_id: str
    description: str
    sources: list[OpenSourceLogSource]
    safety_boundary: dict[str, bool]

    @model_validator(mode="after")
    def normalize_registry(self) -> "OpenSourceLogRegistry":
        ids = [source.source_id for source in self.sources]
        filenames = [source.filename for source in self.sources]
        if len(ids) != len(set(ids)) or len(filenames) != len(set(filenames)):
            raise ValueError("open-source log registry contains duplicate sources")
        required_flags = {
            "explicit_download_only",
            "offline_analysis_only",
            "no_real_drone_connection",
            "no_mavlink_command_execution",
            "human_review_required",
        }
        if not required_flags.issubset(self.safety_boundary) or not all(
            self.safety_boundary.get(flag) is True for flag in required_flags
        ):
            raise ValueError("open-source log registry safety boundary is incomplete")
        self.sources = sorted(self.sources, key=lambda source: source.source_id)
        self.safety_boundary = dict(sorted(self.safety_boundary.items()))
        return self


def load_open_source_log_registry(path: Path) -> OpenSourceLogRegistry:
    payload = read_json_file(path)
    if not isinstance(payload, dict):
        raise ValueError(f"open-source log registry must be a JSON object: {path}")
    return OpenSourceLogRegistry.model_validate(payload)


def validate_open_source_log_registry(path: Path) -> dict[str, Any]:
    registry = load_open_source_log_registry(path)
    return {
        "schema_version": 1,
        "registry_id": registry.registry_id,
        "status": "PASS",
        "source_count": len(registry.sources),
        "source_ids": [source.source_id for source in registry.sources],
        "licenses": sorted({source.license_spdx for source in registry.sources}),
        "all_sources_pinned": True,
        "all_real_world_flight_verified": all(source.real_world_flight_verified for source in registry.sources),
        "safety_boundary": registry.safety_boundary,
        "human_review_required": True,
    }


def verify_cached_source(source: OpenSourceLogSource, cache_dir: Path) -> Path:
    target = Path(cache_dir).resolve() / source.filename
    _verify_file(target, source)
    return target


def _verify_file(path: Path, source: OpenSourceLogSource) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"open-source log cache file is missing: {path}")
    if path.stat().st_size != source.size_bytes:
        raise ValueError(f"source {source.source_id} size mismatch")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != source.sha256:
        raise ValueError(f"source {source.source_id} SHA-256 mismatch")
