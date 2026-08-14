#!/usr/bin/env python3
# Mutation action IDs: storage.icloud-offload, storage.cache-purge,
# storage.archive, storage.trash-stage, storage.trash-purge,
# storage.restore, storage.decision-sync
"""Remembered, policy-bounded storage decisions for macomrade 0.2.0."""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from backup_precondition_check import check_time_machine
from drift_monitor import power_status
from schema_contract import validate_document
from state_paths import add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_POLICY_PATH = ROOT / "settings" / "storage-policy.json"
PRIVATE_POLICY_PATH = ROOT / "Private" / "storage-policy.json"
SWIFT_SOURCE = ROOT / "scripts" / "storage_metadata.swift"
MIB = 1024**2
GIB = 1024**3
DECISIONS = {
    "keep_local",
    "cloud_on_demand",
    "archive",
    "review_after",
    "safe_cache",
    "delete_after_backup",
    "protected",
    "unknown",
}
CONFIRMATIONS = {
    "icloud_offload": "REMOVE ICLOUD LOCAL COPIES",
    "safe_cache": "PURGE APPROVED REGENERABLE CACHES",
    "archive": "ARCHIVE VERIFIED STORAGE ITEMS",
    "trash": "MOVE STORAGE ITEMS TO TRASH",
    "trash_purge": "PURGE MANIFEST BOUND TRASH ITEMS",
    "restore": "RESTORE STORAGE ITEMS",
    "decision_sync": "SYNC STORAGE DECISIONS",
}
ACTION_IDS = {
    "icloud_offload": "storage.icloud-offload",
    "safe_cache": "storage.cache-purge",
    "archive": "storage.archive",
    "trash": "storage.trash-stage",
    "trash_purge": "storage.trash-purge",
    "restore": "storage.restore",
    "decision_sync": "storage.decision-sync",
}
APP_MANAGED_LIBRARY_SUFFIXES = (
    ".photoslibrary",
    ".photolibrary",
    ".musiclibrary",
    ".imovielibrary",
    ".fcpbundle",
)
MANUAL_HANDOFF_KINDS = {"system_temp_review", "optional_app_handoff", "os_managed"}
SIZE_UNITS = {
    "": 1,
    "b": 1,
    "kib": 1024,
    "mib": MIB,
    "gib": GIB,
    "tib": 1024 * GIB,
    "kb": 1000,
    "mb": 1000**2,
    "gb": 1000**3,
    "tb": 1000**4,
}


class StorageError(RuntimeError):
    """Raised when a storage fact or transaction cannot be trusted."""


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def parse_target_request(value: str, *, current_free_bytes: int) -> tuple[int, str]:
    """Resolve auto-independent human storage targets without hiding units."""
    text = value.strip()
    match = re.fullmatch(r"(?P<relative>\+)?(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z]*)", text)
    if not match:
        raise StorageError("target must be auto, bytes, an absolute size such as 80GiB, or a relative size such as +10GiB")
    unit = match.group("unit").casefold()
    if unit not in SIZE_UNITS:
        raise StorageError(f"target uses an unsupported size unit: {match.group('unit')}")
    amount = int(float(match.group("number")) * SIZE_UNITS[unit])
    if amount < 0:
        raise StorageError("target must not be negative")
    if match.group("relative"):
        return current_free_bytes + amount, "relative"
    return amount, "absolute"


def _sha(value: str | bytes) -> str:
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _document_hash(value: Mapping[str, Any], field: str) -> str:
    normalized = dict(value)
    normalized.pop(field, None)
    return _sha(_canonical(normalized))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StorageError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StorageError(f"invalid JSON: {path}: {exc}") from exc


def _checked(value: dict[str, Any], kind: str) -> dict[str, Any]:
    errors = validate_document(value, kind)
    if errors:
        raise StorageError(f"{kind} schema validation failed: {'; '.join(errors)}")
    return value


def display_path(path: Path | str) -> str:
    value = str(Path(path).expanduser())
    home = str(Path.home())
    return "~" + value[len(home):] if value == home or value.startswith(home + os.sep) else value


def resolved_path(value: str | Path) -> Path:
    text = str(value)
    if text == "~" or text.startswith("~/"):
        return Path.home() / text[2:] if text != "~" else Path.home()
    return Path(text).expanduser()


def default_policy_for_tests() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "storage_policy",
        "default_role": "compact",
        "role_targets_bytes": {"compact": 50 * GIB, "expanded": 100 * GIB},
        "target_free_bytes": 50 * GIB,
        "candidate_thresholds": {
            "allocated_bytes": 100 * MIB,
            "cloud_logical_bytes": GIB,
            "cloud_local_ratio_max": 0.10,
            "summary_limit": 50,
            "weekly_new_bytes": 5 * GIB,
        },
        "decision_ttl_days": {"keep_local": 180, "safe_cache": 30},
        "path_rules": [],
        "archive_targets": [],
        "execution_authorized": False,
    }


def merge_policy(public: Mapping[str, Any], private: Mapping[str, Any] | None) -> dict[str, Any]:
    if public.get("kind") != "storage_policy" or public.get("schema_version") != 1:
        raise StorageError("public storage policy metadata is invalid")
    merged = json.loads(json.dumps(public))
    allowed = set(public.get("private_overridable", ["target_free_bytes", "path_rules", "archive_targets"]))
    if private:
        if private.get("kind") != "storage_private_policy" or private.get("schema_version") != 1:
            raise StorageError("Private storage policy metadata is invalid")
        for key in allowed:
            if key in private:
                if key == "path_rules":
                    merged[key] = json.loads(json.dumps([*private[key], *public.get("path_rules", [])]))
                else:
                    merged[key] = json.loads(json.dumps(private[key]))
    # Neither tracked nor Private policy is an execution grant.
    merged["execution_authorized"] = False
    return merged


def load_policy(
    public_path: Path = PUBLIC_POLICY_PATH,
    private_path: Path = PRIVATE_POLICY_PATH,
    *,
    public_only: bool | None = None,
) -> dict[str, Any]:
    public = _checked(_read_json(public_path), "storage-policy")
    disabled = public_only if public_only is not None else os.environ.get("MACOMRADE_PUBLIC_ONLY", "").lower() in {"1", "true", "yes", "on"}
    private = None if disabled or not private_path.is_file() else _checked(_read_json(private_path), "storage-policy")
    return merge_policy(public, private)


def _allocated(stat_result: os.stat_result) -> int:
    blocks = getattr(stat_result, "st_blocks", None)
    return int(blocks) * 512 if isinstance(blocks, int) else int(stat_result.st_size)


def scan_path(path: Path, *, cross_filesystems: bool = False) -> dict[str, Any]:
    """Collect metadata only; never follow symlinks or open file contents."""
    path = path.expanduser()
    try:
        root_stat = path.lstat()
    except OSError as exc:
        raise StorageError(f"cannot inspect path: {display_path(path)}: {exc}") from exc
    root_device = root_stat.st_dev
    seen: set[tuple[int, int]] = set()
    totals = {
        "logical_bytes": 0,
        "allocated_bytes": 0,
        "file_count": 0,
        "latest_mtime_ns": root_stat.st_mtime_ns,
        "device": root_device,
        "inode": root_stat.st_ino,
        "volume": str(root_device),
        "hardlink_duplicates": 0,
        "symlink_count": 0,
        "inaccessible_count": 0,
        "cross_device_skipped": 0,
        "git_repository_count": 0,
        "clone_exclusive_unknown": True,
    }

    def visit(current: Path) -> None:
        try:
            info = current.lstat()
        except OSError:
            totals["inaccessible_count"] += 1
            return
        if stat.S_ISLNK(info.st_mode):
            totals["symlink_count"] += 1
            return
        if info.st_dev != root_device and not cross_filesystems:
            totals["cross_device_skipped"] += 1
            return
        if current.name == ".git" and (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
            totals["git_repository_count"] += 1
        totals["latest_mtime_ns"] = max(totals["latest_mtime_ns"], info.st_mtime_ns)
        if stat.S_ISREG(info.st_mode):
            identity = (info.st_dev, info.st_ino)
            if identity in seen:
                totals["hardlink_duplicates"] += 1
                return
            seen.add(identity)
            totals["logical_bytes"] += info.st_size
            totals["allocated_bytes"] += _allocated(info)
            totals["file_count"] += 1
            return
        if not stat.S_ISDIR(info.st_mode):
            return
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    visit(Path(entry.path))
        except OSError:
            totals["inaccessible_count"] += 1

    visit(path)
    return totals


def default_cloud_metadata() -> dict[str, Any]:
    return {
        "provider": "none",
        "is_ubiquitous": False,
        "is_uploaded": None,
        "is_uploading": None,
        "is_downloading": None,
        "has_unresolved_conflicts": None,
        "downloading_status": None,
        "is_dataless": False,
    }


def _is_app_managed_library(path: Path) -> bool:
    return path.name.lower().endswith(APP_MANAGED_LIBRARY_SUFFIXES)


def _candidate_kind(path: Path, rule: Mapping[str, Any] | None, metrics: Mapping[str, Any]) -> str:
    # These are hard safety boundaries. Private rules may not turn an app-owned
    # library or source repository into a generic archive/Trash candidate.
    if rule and rule.get("kind") == "app_support_aggregate":
        return "app_support_aggregate"
    if _is_app_managed_library(path):
        return "app_managed_library"
    if int(metrics.get("git_repository_count", 0)) > 0:
        return "source_repository_tree"
    if rule and rule.get("kind"):
        return str(rule["kind"])
    text = display_path(path)
    if "/Library/Caches/" in text or text.endswith("/Library/Caches"):
        return "developer_cache"
    if text.startswith("~/Library/Application Support"):
        return "app_support_aggregate"
    return "user_item"


def _matching_rule(path: Path, policy: Mapping[str, Any]) -> Mapping[str, Any] | None:
    displayed = display_path(path)
    for rule in policy.get("path_rules", []):
        if isinstance(rule, dict) and isinstance(rule.get("pattern"), str) and fnmatch.fnmatch(displayed, rule["pattern"]):
            return rule
    return None


def classify_candidate(
    *,
    path: Path,
    metrics: Mapping[str, Any],
    cloud: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    displayed = display_path(path)
    cloud = dict(cloud)
    cloud_storage_root = Path.home() / "Library" / "CloudStorage"
    try:
        path.expanduser().resolve().relative_to(cloud_storage_root.resolve())
        if cloud.get("provider") == "none":
            cloud["provider"] = "third_party_file_provider"
    except ValueError:
        pass
    rule = _matching_rule(path, policy)
    thresholds = policy["candidate_thresholds"]
    logical = int(metrics.get("logical_bytes", 0))
    allocated = int(metrics.get("allocated_bytes", 0))
    reasons: list[str] = []
    provider = cloud.get("provider", "none")
    is_cloud = provider != "none" or cloud.get("is_ubiquitous") is True
    cloud_sparse = is_cloud and logical >= int(thresholds["cloud_logical_bytes"]) and allocated <= logical * float(thresholds["cloud_local_ratio_max"])
    if allocated >= int(thresholds["allocated_bytes"]):
        reasons.append("allocated_threshold")
    if cloud_sparse:
        reasons.append("cloud_placeholder_low_local_allocation")
    kind = _candidate_kind(path, rule, metrics)
    decision = rule.get("decision") if rule else None
    protected = decision == "protected" or kind in {
        "app_support_aggregate",
        "app_managed_library",
        "source_repository_tree",
    }
    eligible = allocated >= int(thresholds["allocated_bytes"]) and not protected
    action_class = "review"
    proposed_action_class: str | None = None
    risk = "review"
    confidence = "medium"
    reclaimable = allocated if eligible else 0
    potential_reclaimable = allocated if allocated >= int(thresholds["allocated_bytes"]) else 0
    if protected:
        eligible = False
        reclaimable = 0
    elif is_cloud and not cloud.get("is_ubiquitous"):
        action_class = "provider_ui"
        risk = "manual"
        confidence = "medium"
        eligible = False
        reclaimable = 0
        reasons.append("third_party_provider_read_only")
    elif cloud.get("is_ubiquitous"):
        confidence = "high" if cloud.get("is_uploaded") is True and cloud.get("has_unresolved_conflicts") is False else "low"
        if decision == "cloud_on_demand":
            action_class = "icloud_offload"
            risk = "low"
            eligible = eligible and cloud.get("is_uploaded") is True and cloud.get("is_uploading") is not True and cloud.get("is_downloading") is not True and cloud.get("has_unresolved_conflicts") is False and str(cloud.get("downloading_status", "")).lower() not in {"downloading", "downloaded_pending"}
        else:
            proposed_action_class = "icloud_offload"
            eligible = False
            reclaimable = 0
            reasons.append("review_required_before_icloud_offload")
    elif decision == "safe_cache" and rule and rule.get("regeneration_proof"):
        action_class = "safe_cache"
        risk = "low"
        confidence = "high"
    elif decision == "archive":
        action_class = "archive"
        risk = "reversible"
        confidence = "high"
    elif decision == "delete_after_backup":
        action_class = "trash"
        risk = "reversible"
    else:
        proposed_action_class = "trash"
        eligible = False
        reclaimable = 0
        reasons.append("review_required_before_file_action")
    if cloud_sparse:
        if action_class == "icloud_offload" and not protected:
            reclaimable = allocated if allocated >= int(thresholds["allocated_bytes"]) else 0
            eligible = eligible and reclaimable > 0
        else:
            reclaimable = 0
            eligible = False
    if protected:
        if kind == "app_managed_library":
            reasons.append("protected_app_managed_library")
        elif kind == "source_repository_tree":
            reasons.append("contains_git_repository")
        else:
            reasons.append("protected_or_app_specific")
        reclaimable = 0
    reclaim_confidence = confidence
    if metrics.get("clone_exclusive_unknown") and reclaim_confidence == "high":
        reclaim_confidence = "medium"
        reasons.append("apfs_clone_exclusive_bytes_unknown")
    path_hash = _sha(str(path.expanduser().resolve()))
    stable_cloud_keys = {
        "provider",
        "is_ubiquitous",
        "is_uploaded",
        "is_uploading",
        "is_downloading",
        "has_unresolved_conflicts",
        "downloading_status",
        "is_dataless",
        "resource_identifier",
        "volume_uuid",
    }
    fingerprint_payload = {
        "path": str(path.expanduser().resolve()),
        "device": metrics.get("device"),
        "inode": metrics.get("inode"),
        "mtime": metrics.get("latest_mtime_ns"),
        "logical": logical,
        "allocated": allocated,
        "git_repository_count": int(metrics.get("git_repository_count", 0)),
        "cloud": {key: cloud.get(key) for key in sorted(stable_cloud_keys)},
    }
    return {
        "id": f"storage-{path_hash[:16]}",
        "path": displayed,
        "path_hash": path_hash,
        "kind": kind,
        "logical_bytes": logical,
        "allocated_bytes": allocated,
        "estimated_reclaimable_bytes": reclaimable,
        "potential_reclaimable_bytes": potential_reclaimable,
        "file_count": int(metrics.get("file_count", 0)),
        "confidence": confidence,
        "reclaim_confidence": reclaim_confidence,
        "risk": risk,
        "action_class": action_class,
        "proposed_action_class": proposed_action_class,
        "eligible": bool(eligible),
        "fingerprint": _sha(_canonical(fingerprint_payload)),
        "volume": metrics.get("volume"),
        "device": metrics.get("device"),
        "inode": metrics.get("inode"),
        "latest_mtime_ns": metrics.get("latest_mtime_ns"),
        "hardlink_duplicates": int(metrics.get("hardlink_duplicates", 0)),
        "symlink_count": int(metrics.get("symlink_count", 0)),
        "inaccessible_count": int(metrics.get("inaccessible_count", 0)),
        "git_repository_count": int(metrics.get("git_repository_count", 0)),
        "clone_exclusive_unknown": bool(metrics.get("clone_exclusive_unknown", True)),
        "cloud": dict(cloud),
        "policy_decision": decision,
        "regeneration_proof": rule.get("regeneration_proof") if rule else None,
        "archive_target_id": rule.get("archive_target_id") if rule else None,
        "reasons": reasons or ["below_candidate_threshold"],
    }


DEVELOPER_ARTIFACT_MARKERS: dict[str, tuple[str, ...]] = {
    "node_modules": ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"),
    ".next": ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"),
    ".turbo": ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"),
    ".parcel-cache": ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"),
    "build": ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradlew"),
    ".gradle": ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradlew"),
    "target": ("pom.xml",),
}


def active_process_working_directories() -> set[Path] | None:
    """Return process cwd paths, or None when lsof cannot provide trustworthy evidence."""
    completed = subprocess.run(
        ["/usr/sbin/lsof", "-Fn", "-a", "-u", str(os.getuid()), "-d", "cwd"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode not in {0, 1}:
        return None
    return {
        Path(line[1:]).resolve()
        for line in completed.stdout.splitlines()
        if line.startswith("n/") and Path(line[1:]).exists()
    }


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _git_output(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _git_repository(path: Path) -> Path | None:
    completed = _git_output(path, "rev-parse", "--show-toplevel")
    if completed.returncode != 0 or not completed.stdout.strip():
        return None
    return Path(completed.stdout.strip()).resolve()


def _developer_artifact_candidate(
    path: Path,
    *,
    policy: Mapping[str, Any],
    active_cwds: set[Path] | None,
) -> dict[str, Any] | None:
    if path.name not in DEVELOPER_ARTIFACT_MARKERS or path.is_symlink() or not path.exists():
        return None
    repo = _git_repository(path.parent)
    if repo is None or not _inside(path, repo):
        return None
    relative = str(path.resolve().relative_to(repo))
    ignored = _git_output(repo, "check-ignore", "-q", "--", relative).returncode == 0
    tracked = _git_output(repo, "ls-files", "--", relative)
    if tracked.returncode != 0:
        return None
    tracked_count = len([line for line in tracked.stdout.splitlines() if line.strip()])
    marker_parents: list[Path] = []
    parent = path.parent.resolve()
    while _inside(parent, repo):
        marker_parents.append(parent)
        if parent == repo:
            break
        parent = parent.parent
    marker = next(
        (
            parent / name
            for parent in marker_parents
            for name in DEVELOPER_ARTIFACT_MARKERS[path.name]
            if (parent / name).is_file()
        ),
        None,
    )
    cwd_unknown = active_cwds is None
    active = False if cwd_unknown else any(_inside(cwd, repo) for cwd in active_cwds)
    metrics = scan_path(path)
    candidate = classify_candidate(
        path=path,
        metrics=metrics,
        cloud=default_cloud_metadata(),
        policy=policy,
    )
    reasons = [reason for reason in candidate["reasons"] if reason != "review_required_before_file_action"]
    proof_ok = ignored and tracked_count == 0 and marker is not None and not active and not cwd_unknown
    if not ignored:
        reasons.append("not_git_ignored")
    if tracked_count:
        reasons.append("contains_tracked_files")
    if marker is None:
        reasons.append("missing_rebuild_marker")
    if active:
        reasons.append("active_project_working_directory")
    if cwd_unknown:
        reasons.append("active_working_directory_evidence_unavailable")
    above_threshold = metrics["allocated_bytes"] >= int(policy["candidate_thresholds"]["allocated_bytes"])
    candidate.update(
        {
            "kind": "developer_artifact",
            "action_class": "safe_cache",
            "proposed_action_class": None,
            "risk": "low",
            "confidence": "high" if proof_ok else "low",
            "eligible": bool(proof_ok and above_threshold),
            "estimated_reclaimable_bytes": metrics["allocated_bytes"] if proof_ok and above_threshold else 0,
            "regeneration_proof": f"Git-ignored {path.name} is reproducible from {display_path(marker) if marker else 'a required project manifest'}.",
            "git_ignored": ignored,
            "tracked_file_count": tracked_count,
            "rebuild_marker": display_path(marker) if marker else None,
            "project_root": display_path(repo),
            "active_project_working_directory": active,
            "reasons": reasons or (["allocated_threshold"] if above_threshold else ["below_candidate_threshold"]),
        }
    )
    candidate["fingerprint"] = _sha(
        _canonical(
            {
                "base": candidate["fingerprint"],
                "git_ignored": ignored,
                "tracked_file_count": tracked_count,
                "rebuild_marker": candidate["rebuild_marker"],
                "project_root": candidate["project_root"],
            }
        )
    )
    return candidate


def discover_developer_artifacts(
    search_root: Path,
    *,
    policy: Mapping[str, Any],
    active_cwds: set[Path] | None = None,
) -> list[dict[str, Any]]:
    """Find only Git-ignored, manifest-rebuildable artifact directories."""
    root = search_root.expanduser()
    if not root.is_dir():
        return []
    repository = _git_repository(root)
    repositories = [repository] if repository else []
    if not repository:
        for current, directories, _files in os.walk(root):
            if ".git" in directories:
                repositories.append(Path(current).resolve())
                directories.remove(".git")
            directories[:] = [name for name in directories if name not in DEVELOPER_ARTIFACT_MARKERS]
    results: list[dict[str, Any]] = []
    for repo in dict.fromkeys(repositories):
        for current, directories, _files in os.walk(repo):
            if ".git" in directories:
                directories.remove(".git")
            artifact_names = [name for name in directories if name in DEVELOPER_ARTIFACT_MARKERS]
            for name in artifact_names:
                candidate = _developer_artifact_candidate(
                    Path(current) / name,
                    policy=policy,
                    active_cwds=active_cwds,
                )
                if candidate:
                    results.append(candidate)
            directories[:] = [name for name in directories if name not in DEVELOPER_ARTIFACT_MARKERS]
    return results


class SwiftMetadataBackend:
    """Compile the checked-in Foundation helper into machine-local state."""

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.binary = self._binary_path()

    def _binary_path(self) -> Path:
        digest = _sha(SWIFT_SOURCE.read_bytes())[:16]
        return self.state_dir / "bin" / f"storage-metadata-{digest}"

    def ensure_compiled(self) -> Path:
        if self.binary.is_file() and os.access(self.binary, os.X_OK):
            return self.binary
        self.binary.parent.mkdir(parents=True, exist_ok=True)
        module_cache = self.state_dir / "build" / "swift-module-cache"
        module_cache.mkdir(parents=True, exist_ok=True)
        environment = dict(os.environ)
        environment["CLANG_MODULE_CACHE_PATH"] = str(module_cache)
        environment["SWIFT_MODULECACHE_PATH"] = str(module_cache)
        completed = subprocess.run(["/usr/bin/xcrun", "swiftc", str(SWIFT_SOURCE), "-o", str(self.binary)], env=environment, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise StorageError(f"cannot compile Swift storage helper: {completed.stderr.strip()}")
        return self.binary

    def _call(self, command: str, path: Path) -> dict[str, Any]:
        completed = subprocess.run([str(self.ensure_compiled()), command, str(path)], capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise StorageError(completed.stderr.strip() or f"Swift helper failed: {command}")
        value = json.loads(completed.stdout)
        if not isinstance(value, dict):
            raise StorageError("Swift helper returned a non-object")
        return value

    def inspect(self, path: Path) -> dict[str, Any]:
        return self._call("inspect", path)

    def evict(self, path: Path) -> dict[str, Any]:
        return self._call("evict", path)

    def download(self, path: Path) -> dict[str, Any]:
        return self._call("download", path)


def parse_apfs_inventory(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a privacy-bounded startup APFS summary from diskutil plist data."""
    containers = [row for row in payload.get("Containers", []) if isinstance(row, dict)]
    startup = next(
        (
            row
            for row in containers
            if {role for volume in row.get("Volumes", []) if isinstance(volume, dict) for role in volume.get("Roles", [])}
            >= {"System", "Data"}
        ),
        None,
    )
    if startup is None:
        raise StorageError("startup APFS container was not found")
    volumes = []
    for volume in startup.get("Volumes", []):
        if not isinstance(volume, dict):
            continue
        volumes.append(
            {
                "roles": [str(value) for value in volume.get("Roles", [])],
                "allocated_bytes": max(0, int(volume.get("CapacityInUse", 0))),
                "eligible": False,
                "action_class": "protected",
                "reason": "apfs_volume_os_managed",
            }
        )
    return {
        "status": "available",
        "capacity_bytes": max(0, int(startup.get("CapacityCeiling", 0))),
        "free_bytes": max(0, int(startup.get("CapacityFree", 0))),
        "volumes": volumes,
    }


def parse_apfs_snapshots(payload: Mapping[str, Any]) -> dict[str, Any]:
    items = []
    for row in payload.get("Snapshots", []):
        if not isinstance(row, dict):
            continue
        name = str(row.get("SnapshotName", ""))
        if name.startswith("com.apple.os.update"):
            kind = "os_update"
        elif "TimeMachine" in name:
            kind = "time_machine"
        else:
            kind = "system"
        items.append(
            {
                "kind": kind,
                "purgeable": bool(row.get("Purgeable", False)),
                "limits_container_shrink": bool(row.get("LimitingContainerShrink", False)),
                "eligible": False,
                "action_class": "protected",
                "reason": "snapshot_requires_supported_os_management",
            }
        )
    return {"status": "available", "items": items}


def parse_swapusage(output: str) -> dict[str, Any]:
    match = re.search(
        r"total\s*=\s*([0-9.]+)M\s+used\s*=\s*([0-9.]+)M\s+free\s*=\s*([0-9.]+)M",
        output,
    )
    if not match:
        raise StorageError("vm.swapusage output is unavailable or unrecognized")
    total, used, free = (int(float(value) * MIB) for value in match.groups())
    return {
        "status": "available",
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
        "eligible": False,
        "action_class": "reboot_handoff",
        "durability": "transient",
        "reason": "swap_may_return_under_memory_pressure",
    }


def _manual_handoff_candidate(
    path: Path,
    metrics: Mapping[str, Any],
    *,
    kind: str,
    reasons: list[str],
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    allocated = max(0, int(metrics.get("allocated_bytes", 0)))
    logical = max(allocated, int(metrics.get("logical_bytes", allocated)))
    path_hash = _sha(str(resolved))
    fingerprint = _sha(
        _canonical(
            {
                "path": str(resolved),
                "allocated": allocated,
                "logical": logical,
                "mtime": metrics.get("latest_mtime_ns"),
                "inode": metrics.get("inode"),
                "kind": kind,
            }
        )
    )
    return {
        "id": f"storage-{path_hash[:16]}",
        "path": display_path(path),
        "path_hash": path_hash,
        "kind": kind,
        "logical_bytes": logical,
        "allocated_bytes": allocated,
        "estimated_reclaimable_bytes": 0,
        "potential_reclaimable_bytes": allocated,
        "file_count": int(metrics.get("file_count", 0)),
        "confidence": "medium",
        "reclaim_confidence": "low",
        "risk": "manual",
        "action_class": "manual_handoff",
        "proposed_action_class": None,
        "eligible": False,
        "fingerprint": fingerprint,
        "volume": metrics.get("volume"),
        "device": metrics.get("device"),
        "inode": metrics.get("inode"),
        "latest_mtime_ns": metrics.get("latest_mtime_ns"),
        "hardlink_duplicates": int(metrics.get("hardlink_duplicates", 0)),
        "symlink_count": int(metrics.get("symlink_count", 0)),
        "inaccessible_count": int(metrics.get("inaccessible_count", 0)),
        "git_repository_count": int(metrics.get("git_repository_count", 0)),
        "clone_exclusive_unknown": bool(metrics.get("clone_exclusive_unknown", True)),
        "cloud": default_cloud_metadata(),
        "policy_decision": None,
        "regeneration_proof": None,
        "archive_target_id": None,
        "reasons": reasons,
        "handoff": dict(details or {}),
    }


def discover_private_tmp_handoffs(
    root: Path,
    *,
    threshold_bytes: int,
    metrics_for_path: Callable[[Path], Mapping[str, Any]] = scan_path,
) -> list[dict[str, Any]]:
    """Identify exact large tmp trees without granting a filesystem action."""
    if not root.is_dir():
        return []
    rows = []
    for child in sorted(root.iterdir(), key=lambda value: value.name.casefold()):
        if child.is_symlink():
            continue
        try:
            metrics = metrics_for_path(child)
        except (OSError, StorageError):
            continue
        if int(metrics.get("allocated_bytes", 0)) < threshold_bytes:
            continue
        rows.append(
            _manual_handoff_candidate(
                child,
                metrics,
                kind="system_temp_review",
                reasons=["exact_path_review_required", "process_check_required", "provenance_required"],
                details={"route": "manual_temp_review", "execution_authorized": False},
            )
        )
    return rows


def discover_optional_app_handoffs(
    catalog_data: Mapping[str, Any],
    installed_items: Iterable[Mapping[str, Any]],
    *,
    metrics_for_path: Callable[[Path], Mapping[str, Any]] = scan_path,
) -> list[dict[str, Any]]:
    """Expose installed Optional app bundles as app-manager handoffs only."""
    optional = {
        str(row.get("name")): row
        for row in catalog_data.get("apps", [])
        if isinstance(row, dict)
        and str(row.get("tier", "")).casefold() in {"optional", "option"}
        and row.get("lifecycle_status") != "retired"
    }
    rows = []
    seen: set[str] = set()
    for installed in installed_items:
        catalog_name = str(installed.get("catalog_name") or installed.get("name") or "")
        app = optional.get(catalog_name)
        path_value = installed.get("path")
        if not app or not isinstance(path_value, str) or path_value in seen:
            continue
        path = Path(path_value)
        if not path.is_dir():
            continue
        seen.add(path_value)
        try:
            metrics = metrics_for_path(path)
        except (OSError, StorageError):
            continue
        rows.append(
            _manual_handoff_candidate(
                path,
                metrics,
                kind="optional_app_handoff",
                reasons=["optional_app_installed", "app_manager_uninstall_review_required"],
                details={
                    "route": "app_uninstall_review",
                    "component_id": app.get("id") or app.get("component_id"),
                    "guide": app.get("guide"),
                    "app": app.get("name"),
                    "execution_authorized": False,
                },
            )
        )
    return rows


def _run_plist(command: list[str]) -> Mapping[str, Any]:
    completed = subprocess.run(command, capture_output=True, check=False)
    if completed.returncode != 0:
        raise StorageError("system fact command is unavailable")
    value = plistlib.loads(completed.stdout)
    if not isinstance(value, dict):
        raise StorageError("system fact command returned a non-object plist")
    return value


def _mole_home_overview(home: Path) -> list[dict[str, Any]]:
    mole = shutil.which("mole")
    if not mole:
        return []
    completed = subprocess.run([mole, "analyze", "--json"], capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return []
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    rows = []
    for entry in payload.get("entries", []) if isinstance(payload, dict) else []:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            continue
        path = Path(entry["path"])
        if path not in {home, home / "Library"}:
            continue
        rows.append(
            {
                "path": display_path(path),
                "reported_bytes": max(0, int(entry.get("size", 0))),
                "authority": "mole_evidence_only",
                "eligible": False,
                "action_class": "evidence_only",
            }
        )
    return sorted(rows, key=lambda row: (-row["reported_bytes"], row["path"]))


def _deep_home_top_facts(home: Path) -> tuple[list[dict[str, Any]], bool]:
    """Use one bounded du traversal instead of rescanning every child tree."""
    if not home.is_dir():
        return [], False
    completed = subprocess.run(
        ["/usr/bin/du", "-k", "-d", "1", str(home)],
        capture_output=True,
        text=True,
        check=False,
    )
    rows = []
    for line in completed.stdout.splitlines():
        size, separator, path_value = line.partition("\t")
        if not separator or not size.isdigit():
            continue
        path = Path(path_value)
        if path.parent != home:
            continue
        rows.append(
            {
                "path": display_path(path),
                "allocated_bytes": int(size) * 1024,
                "authority": "filesystem_allocated_evidence",
                "eligible": False,
                "action_class": "evidence_only",
            }
        )
    return sorted(rows, key=lambda row: (-row["allocated_bytes"], row["path"])), completed.returncode == 0


def collect_system_context(
    *,
    mode: str,
    policy: Mapping[str, Any],
    home: Path | None = None,
    temp_root: Path = Path("/private/tmp"),
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Collect read-only OS facts and non-executable handoff opportunities."""
    errors: list[dict[str, str]] = []
    diskutil = shutil.which("diskutil") or "/usr/sbin/diskutil"
    sysctl = shutil.which("sysctl") or "/usr/sbin/sysctl"
    try:
        startup_apfs = parse_apfs_inventory(_run_plist([diskutil, "apfs", "list", "-plist"]))
    except (OSError, StorageError, plistlib.InvalidFileException):
        startup_apfs = {"status": "unavailable", "volumes": []}
        errors.append({"source": "apfs", "error": "unavailable"})
    try:
        snapshots = parse_apfs_snapshots(_run_plist([diskutil, "apfs", "listSnapshots", "/", "-plist"]))
    except (OSError, StorageError, plistlib.InvalidFileException):
        snapshots = {"status": "unavailable", "items": []}
        errors.append({"source": "snapshots", "error": "unavailable"})
    try:
        completed = subprocess.run([sysctl, "vm.swapusage"], capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise StorageError("swap unavailable")
        swap = parse_swapusage(completed.stdout)
    except (OSError, StorageError):
        swap = {"status": "unavailable", "eligible": False, "durability": "transient"}
        errors.append({"source": "swap", "error": "unavailable"})
    vm_allocated = next(
        (
            int(row.get("allocated_bytes", 0))
            for row in startup_apfs.get("volumes", [])
            if "VM" in row.get("roles", [])
        ),
        0,
    )
    vm = {**swap, "volume_allocated_bytes": vm_allocated}
    protected_aggregates = []
    for path, owner in (
        (Path("/System/Volumes/Data/System/Library/AssetsV2"), "system_assets"),
        (Path("/System/Volumes/VM"), "virtual_memory"),
    ):
        if not path.exists():
            continue
        try:
            metrics = scan_path(path, cross_filesystems=False) if mode == "deep" else None
            protected_aggregates.append(
                {
                    "path": str(path),
                    "owner": owner,
                    "allocated_bytes": int(metrics.get("allocated_bytes", 0)) if metrics else vm_allocated if owner == "virtual_memory" else 0,
                    "eligible": False,
                    "action_class": "protected",
                }
            )
        except (OSError, StorageError):
            errors.append({"source": owner, "error": "unavailable"})
    home_root = home or Path.home()
    if mode == "deep":
        home_top, home_complete = _deep_home_top_facts(home_root)
        if not home_complete:
            errors.append({"source": "home_top", "error": "partial"})
    else:
        home_top = _mole_home_overview(home_root)
    handoffs: list[dict[str, Any]] = []
    if mode == "deep":
        handoffs.extend(
            discover_private_tmp_handoffs(
                temp_root,
                threshold_bytes=int(policy["candidate_thresholds"]["allocated_bytes"]),
            )
        )
        try:
            import macos_apps

            handoffs.extend(discover_optional_app_handoffs(macos_apps.catalog(), macos_apps.installed_apps()))
        except (OSError, StorageError, ValueError, KeyError, json.JSONDecodeError):
            errors.append({"source": "optional_apps", "error": "unavailable"})
    facts = {
        "status": "complete" if not errors else "partial",
        "execution_authorized": False,
        "startup_apfs": startup_apfs,
        "snapshots": snapshots,
        "vm": vm,
        "protected_aggregates": protected_aggregates,
        "home_top": home_top,
        "errors": errors,
    }
    return facts, handoffs


def scan_fixture(*, free_bytes: int, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "storage_scan",
        "scan_id": "scan-fixture",
        "generated_at": "2026-08-14T00:00:00+00:00",
        "mode": "quick",
        "volume": {"path": "/", "capacity_bytes": 256 * GIB, "free_bytes": free_bytes},
        "system_facts": {
            "status": "fixture",
            "execution_authorized": False,
            "startup_apfs": {"status": "fixture", "volumes": []},
            "snapshots": {"status": "fixture", "items": []},
            "vm": {"status": "fixture", "eligible": False, "durability": "transient"},
            "protected_aggregates": [],
            "home_top": [],
            "errors": [],
        },
        "roots": [],
        "candidates": candidates,
        "summary_candidate_ids": [row["id"] for row in candidates],
        "errors": [],
    }


def _scan_roots(policy: Mapping[str, Any], mode: str, explicit: list[str]) -> list[Path]:
    if explicit:
        return [resolved_path(item) for item in explicit]
    roots = policy.get("scan_roots", {}).get(mode, policy.get("scan_roots", {}).get("quick", []))
    return [resolved_path(item) for item in roots]


def build_scan(
    *,
    policy: Mapping[str, Any],
    mode: str,
    roots: list[Path],
    metadata: SwiftMetadataBackend | None = None,
    system_facts: Mapping[str, Any] | None = None,
    handoff_candidates: Iterable[Mapping[str, Any]] = (),
    disk_usage: Callable[[str], shutil._ntuple_diskusage] = shutil.disk_usage,
) -> dict[str, Any]:
    if mode not in {"quick", "deep"}:
        raise StorageError("scan mode must be quick or deep")
    volume = disk_usage("/")
    candidates: list[dict[str, Any]] = []
    root_rows = []
    errors = []
    for path in roots:
        if not path.exists():
            root_rows.append({"path": display_path(path), "status": "missing"})
            continue
        try:
            cloud = metadata.inspect(path) if metadata else default_cloud_metadata()
            metrics = scan_path(path, cross_filesystems=False)
            candidate = classify_candidate(path=path, metrics=metrics, cloud=cloud, policy=policy)
            root_row = {
                "path": display_path(path),
                "status": "scanned",
                "logical_bytes": metrics["logical_bytes"],
                "allocated_bytes": metrics["allocated_bytes"],
                "file_count": metrics["file_count"],
                "candidate_id": candidate["id"],
                "expanded": False,
            }
            should_expand = (
                mode == "deep"
                and "allocated_threshold" in candidate["reasons"]
                and candidate["kind"] != "app_support_aggregate"
                and path.is_dir()
                and not path.is_symlink()
            )
            if should_expand:
                root_row["expanded"] = True
                child_count = 0
                with os.scandir(path) as entries:
                    for entry in entries:
                        child = Path(entry.path)
                        if entry.is_symlink():
                            continue
                        try:
                            child_cloud = metadata.inspect(child) if metadata else default_cloud_metadata()
                            child_metrics = scan_path(child, cross_filesystems=False)
                            child_candidate = classify_candidate(path=child, metrics=child_metrics, cloud=child_cloud, policy=policy)
                            if (
                                child_candidate["eligible"]
                                or "allocated_threshold" in child_candidate["reasons"]
                                or "cloud_placeholder_low_local_allocation" in child_candidate["reasons"]
                            ):
                                candidates.append(child_candidate)
                            child_count += 1
                        except (StorageError, OSError, json.JSONDecodeError) as exc:
                            errors.append({"path": display_path(child), "error": str(exc)})
                root_row["expanded_children"] = child_count
            else:
                candidates.append(candidate)
            root_rows.append(root_row)
        except (StorageError, OSError, json.JSONDecodeError) as exc:
            errors.append({"path": display_path(path), "error": str(exc)})
    if mode == "deep":
        active_cwds = active_process_working_directories()
        known_ids = {row["id"] for row in candidates}
        for search_root in policy.get("developer_artifact_roots", []):
            try:
                for candidate in discover_developer_artifacts(
                    resolved_path(search_root),
                    policy=policy,
                    active_cwds=active_cwds,
                ):
                    if candidate["id"] not in known_ids:
                        candidates.append(candidate)
                        known_ids.add(candidate["id"])
            except (StorageError, OSError) as exc:
                errors.append({"path": display_path(resolved_path(search_root)), "error": str(exc)})
    candidates.extend(dict(row) for row in handoff_candidates)
    candidates.sort(
        key=lambda row: (
            not row["eligible"],
            -int(row["estimated_reclaimable_bytes"] if row["eligible"] else row.get("potential_reclaimable_bytes", 0)),
            row["path_hash"],
        )
    )
    limit = int(policy["candidate_thresholds"]["summary_limit"])
    payload = {
        "schema_version": 1,
        "kind": "storage_scan",
        "scan_id": f"scan-{_sha(iso_now())[:16]}",
        "generated_at": iso_now(),
        "mode": mode,
        "volume": {"path": "/", "capacity_bytes": volume.total, "free_bytes": volume.free},
        "system_facts": dict(system_facts or {
            "status": "not_collected",
            "execution_authorized": False,
            "startup_apfs": {"status": "not_collected", "volumes": []},
            "snapshots": {"status": "not_collected", "items": []},
            "vm": {"status": "not_collected", "eligible": False, "durability": "transient"},
            "protected_aggregates": [],
            "home_top": [],
            "errors": [],
        }),
        "roots": root_rows,
        "candidates": candidates,
        "summary_candidate_ids": [row["id"] for row in candidates[:limit]],
        "errors": errors,
    }
    return _checked(payload, "storage-scan")


def build_decision(candidate: Mapping[str, Any], decision: str, *, review_after: str | None = None, note: str | None = None) -> dict[str, Any]:
    if decision not in DECISIONS:
        raise StorageError(f"unknown storage decision: {decision}")
    if decision == "review_after" and not review_after:
        raise StorageError("review_after decision requires --review-after YYYY-MM-DD")
    if review_after:
        try:
            dt.date.fromisoformat(review_after)
        except ValueError as exc:
            raise StorageError("review_after must be an ISO date") from exc
    return {
        "candidate_id": candidate["id"],
        "path_pattern": candidate["path"],
        "path_hash": candidate["path_hash"],
        "fingerprint": candidate["fingerprint"],
        "decision": decision,
        "decided_at": iso_now(),
        "review_after": review_after,
        "note": note,
        "execution_authorized": False,
    }


def decision_effect(candidate: Mapping[str, Any], record: Mapping[str, Any], *, now: dt.datetime | None = None, policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    current = now or utc_now()
    decision = record.get("decision")
    if decision == "protected":
        return {"suppress": True, "reason": "protected"}
    if decision == "review_after":
        review = record.get("review_after")
        return {"suppress": bool(review and current.date() < dt.date.fromisoformat(str(review))), "reason": "review_after"}
    if decision == "cloud_on_demand" and record.get("fingerprint") != candidate.get("fingerprint"):
        return {"suppress": False, "reason": "rematerialized_or_changed"}
    ttl = (policy or default_policy_for_tests()).get("decision_ttl_days", {}).get(decision)
    if ttl is not None:
        decided = dt.datetime.fromisoformat(str(record["decided_at"]).replace("Z", "+00:00"))
        return {"suppress": current < decided + dt.timedelta(days=int(ttl)), "reason": "ttl"}
    return {"suppress": decision in DECISIONS - {"unknown"}, "reason": "decision"}


def _find_decision(candidate: Mapping[str, Any], decisions: Iterable[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    rows = [row for row in decisions if row.get("candidate_id") == candidate.get("id") or row.get("path_hash") == candidate.get("path_hash")]
    return rows[-1] if rows else None


def _reviewed_candidate(
    candidate: Mapping[str, Any],
    record: Mapping[str, Any],
    *,
    policy: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Promote an unchanged, explicitly reviewed candidate without weakening hard boundaries."""
    decision = record.get("decision")
    effect = decision_effect(candidate, record, policy=policy)
    if decision in {"protected", "keep_local", "review_after"} and effect["suppress"]:
        return None
    if decision == "unknown":
        return dict(candidate)
    if record.get("fingerprint") != candidate.get("fingerprint"):
        return None
    if candidate.get("kind") in {"app_support_aggregate", "app_managed_library", "source_repository_tree", *MANUAL_HANDOFF_KINDS}:
        return None
    promoted = dict(candidate)
    potential = int(candidate.get("potential_reclaimable_bytes", 0))
    if potential <= 0 or candidate.get("confidence") == "low":
        return None
    if decision == "delete_after_backup":
        promoted.update(action_class="trash", risk="reversible", eligible=True, estimated_reclaimable_bytes=potential)
        return promoted
    if decision == "archive":
        promoted.update(action_class="archive", risk="reversible", eligible=True, estimated_reclaimable_bytes=potential)
        return promoted
    if decision == "cloud_on_demand":
        cloud = candidate.get("cloud", {})
        if (
            cloud.get("provider") != "icloud"
            or cloud.get("is_ubiquitous") is not True
            or cloud.get("is_uploaded") is not True
            or cloud.get("is_uploading") is True
            or cloud.get("is_downloading") is True
            or cloud.get("has_unresolved_conflicts") is not False
        ):
            return None
        promoted.update(action_class="icloud_offload", risk="low", eligible=True, estimated_reclaimable_bytes=potential)
        return promoted
    if decision == "safe_cache" and candidate.get("regeneration_proof"):
        promoted.update(action_class="safe_cache", risk="low", eligible=True, estimated_reclaimable_bytes=potential)
        return promoted
    return None


def _target(policy: Mapping[str, Any], scan: Mapping[str, Any], requested: str) -> tuple[int, str]:
    if requested != "auto":
        return parse_target_request(requested, current_free_bytes=int(scan["volume"]["free_bytes"]))
    if isinstance(policy.get("target_free_bytes"), int):
        return int(policy["target_free_bytes"]), "private_override"
    role = str(policy.get("default_role", "compact"))
    if role == "auto":
        role = "expanded" if int(scan["volume"]["capacity_bytes"]) >= 512 * GIB else "compact"
    return int(policy["role_targets_bytes"][role]), "role"


def build_plan(scan: Mapping[str, Any], policy: Mapping[str, Any], *, decisions: list[Mapping[str, Any]], target: str) -> dict[str, Any]:
    target_bytes, target_mode = _target(policy, scan, target)
    free = int(scan["volume"]["free_bytes"])
    needed = max(0, target_bytes - free)
    actionable = []
    suppressed = []
    for candidate in scan.get("candidates", []):
        record = _find_decision(candidate, decisions)
        if record:
            reviewed = _reviewed_candidate(candidate, record, policy=policy)
            if reviewed is None:
                suppressed.append(candidate["id"])
                continue
            candidate = reviewed
        if candidate.get("eligible") and candidate.get("confidence") != "low" and int(candidate.get("estimated_reclaimable_bytes", 0)) > 0:
            actionable.append(candidate)
    rank = {"safe_cache": 0, "icloud_offload": 1, "archive": 2, "trash": 3}
    actionable.sort(key=lambda row: (rank.get(str(row.get("action_class")), 9), -int(row["estimated_reclaimable_bytes"]), row["id"]))
    low = [row for row in actionable if row.get("risk") == "low"]
    reversible = [row for row in actionable if row.get("risk") == "reversible"]
    minimum = []
    accumulated = 0
    for row in actionable:
        if accumulated >= needed:
            break
        item = {"candidate_id": row["id"], "action_class": row["action_class"], "estimated_reclaimable_bytes": row["estimated_reclaimable_bytes"], "path": row["path"], "fingerprint": row["fingerprint"], "candidate": row}
        minimum.append(item)
        accumulated += int(row["estimated_reclaimable_bytes"])
    plan = {
        "schema_version": 1,
        "kind": "storage_plan",
        "plan_id": f"plan-{_sha(str(scan['scan_id']) + iso_now())[:16]}",
        "created_at": iso_now(),
        "scan_id": scan["scan_id"],
        "volume": scan["volume"],
        "target_request": target,
        "target_mode": target_mode,
        "target_free_bytes": target_bytes,
        "needed_bytes": needed,
        "estimated_reclaimable_bytes": accumulated,
        "staged_bytes": 0,
        "curves": {
            "low_risk": [{"candidate_id": row["id"], "action_class": row["action_class"], "estimated_reclaimable_bytes": row["estimated_reclaimable_bytes"]} for row in low],
            "reversible": [{"candidate_id": row["id"], "action_class": row["action_class"], "estimated_reclaimable_bytes": row["estimated_reclaimable_bytes"]} for row in reversible],
        },
        "minimum_action_set": minimum,
        "suppressed_candidate_ids": suppressed,
        "requires_replan_after_target": True,
        "execution_authorized": False,
    }
    return _checked(freeze_plan(plan), "storage-plan")


def plan_fixture(candidates: list[dict[str, Any]], *, free_bytes: int = 10 * GIB, target_free_bytes: int = 50 * GIB) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "storage_plan",
        "plan_id": "plan-fixture",
        "created_at": "2026-08-14T00:00:00+00:00",
        "scan_id": "scan-fixture",
        "volume": {"path": "/", "capacity_bytes": 256 * GIB, "free_bytes": free_bytes},
        "target_request": str(target_free_bytes),
        "target_mode": "absolute",
        "target_free_bytes": target_free_bytes,
        "needed_bytes": max(0, target_free_bytes - free_bytes),
        "estimated_reclaimable_bytes": sum(int(row["estimated_reclaimable_bytes"]) for row in candidates),
        "staged_bytes": 0,
        "curves": {"low_risk": [], "reversible": []},
        "minimum_action_set": [{"candidate_id": row["id"], "action_class": row["action_class"], "estimated_reclaimable_bytes": row["estimated_reclaimable_bytes"], "path": row["path"], "fingerprint": row["fingerprint"], "candidate": row} for row in candidates],
        "suppressed_candidate_ids": [],
        "requires_replan_after_target": True,
        "execution_authorized": False,
    }


def freeze_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(plan))
    result["plan_sha256"] = _document_hash(result, "plan_sha256")
    return result


class FakeActionBackend:
    def __init__(self, *, free_bytes: list[int] | None = None):
        self.calls: list[tuple[str, str]] = []
        self._free = iter(free_bytes or [10 * GIB] * 100)

    def free_bytes(self, _volume: str = "/") -> int:
        return next(self._free)

    def verify_candidate(self, _candidate: Mapping[str, Any]) -> bool:
        return True

    def execute(self, action_class: str, candidate: Mapping[str, Any]) -> dict[str, Any]:
        self.calls.append((action_class, str(candidate["id"])))
        return {"status": "applied", "trash_path": f"~/.Trash/{candidate['id']}" if action_class == "trash" else None}

    def purge(self, row: Mapping[str, Any]) -> dict[str, Any]:
        self.calls.append(("trash_purge", str(row["candidate_id"])))
        return {"status": "purged"}


class LocalActionBackend:
    def __init__(self, state_dir: Path, policy: Mapping[str, Any]):
        self.state_dir = state_dir
        self.policy = policy
        self.metadata = SwiftMetadataBackend(state_dir)

    def free_bytes(self, volume: str = "/") -> int:
        return shutil.disk_usage(volume).free

    def verify_candidate(self, candidate: Mapping[str, Any]) -> bool:
        path = resolved_path(str(candidate["path"]))
        if not path.exists():
            return False
        if candidate.get("kind") == "developer_artifact":
            current = _developer_artifact_candidate(
                path,
                policy=self.policy,
                active_cwds=active_process_working_directories(),
            )
            return bool(
                current
                and current["eligible"]
                and current["fingerprint"] == candidate.get("fingerprint")
                and current["inode"] == candidate.get("inode")
                and current["allocated_bytes"] == candidate.get("allocated_bytes")
            )
        metrics = scan_path(path)
        cloud = self.metadata.inspect(path)
        current = classify_candidate(path=path, metrics=metrics, cloud=cloud, policy=self.policy)
        return current["fingerprint"] == candidate.get("fingerprint") and current["inode"] == candidate.get("inode") and current["allocated_bytes"] == candidate.get("allocated_bytes")

    def _trash(self, path: Path) -> str:
        result = self.metadata._call("trash", path)
        value = result.get("resulting_path")
        if not isinstance(value, str) or not value:
            raise StorageError("Trash operation did not return a recovery path")
        return display_path(value)

    def _archive(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        target_id = candidate.get("archive_target_id")
        target = next((row for row in self.policy.get("archive_targets", []) if row.get("id") == target_id), None)
        if not target:
            raise StorageError("archive target is not explicitly configured in Private policy")
        destination_root = resolved_path(str(target["path"]))
        if not destination_root.is_dir():
            raise StorageError("archive target is offline")
        source = resolved_path(str(candidate["path"]))
        required = int(candidate["logical_bytes"])
        if shutil.disk_usage(destination_root).free < required:
            raise StorageError("archive target has insufficient capacity")
        probe = destination_root / f".macomrade-write-test-{os.getpid()}"
        try:
            probe.write_bytes(b"macomrade")
            if probe.read_bytes() != b"macomrade":
                raise StorageError("archive target hash read-back failed")
        finally:
            probe.unlink(missing_ok=True)
        destination = destination_root / source.name
        if destination.exists():
            raise StorageError("archive destination already exists")
        if source.is_dir():
            shutil.copytree(source, destination, symlinks=True)
        else:
            shutil.copy2(source, destination, follow_symlinks=False)
        source_metrics = scan_path(source)
        destination_metrics = scan_path(destination)
        if source_metrics["logical_bytes"] != destination_metrics["logical_bytes"] or source_metrics["file_count"] != destination_metrics["file_count"]:
            raise StorageError("archive metadata read-back differs from source")
        if _tree_digest(source) != _tree_digest(destination):
            raise StorageError("archive content hash read-back differs from source")
        return {"status": "archived", "archive_path": display_path(destination), "trash_path": self._trash(source)}

    def execute(self, action_class: str, candidate: Mapping[str, Any]) -> dict[str, Any]:
        path = resolved_path(str(candidate["path"]))
        if action_class == "icloud_offload":
            return self.metadata.evict(path)
        if action_class == "safe_cache":
            if not candidate.get("regeneration_proof"):
                raise StorageError("cache has no public regeneration proof")
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
            return {"status": "purged"}
        if action_class == "archive":
            return self._archive(candidate)
        if action_class == "trash":
            return {"status": "staged", "trash_path": self._trash(path)}
        if action_class == "restore":
            return self.metadata.download(path)
        raise StorageError(f"unsupported action class: {action_class}")

    def purge(self, row: Mapping[str, Any]) -> dict[str, Any]:
        path = resolved_path(str(row["trash_path"]))
        if not path.exists() or path.is_symlink():
            raise StorageError("manifest-bound Trash path is missing or unsafe")
        info = path.lstat()
        if int(row.get("trash_inode", info.st_ino)) != info.st_ino:
            raise StorageError("manifest-bound Trash item changed")
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        return {"status": "purged"}

    def restore_manifest_row(self, row: Mapping[str, Any]) -> dict[str, Any]:
        source = resolved_path(str(row["trash_path"]))
        destination = resolved_path(str(row["original_path"]))
        if destination.exists():
            raise StorageError("restore destination already exists")
        if not source.exists() or source.is_symlink():
            raise StorageError("manifest-bound restore source is missing or unsafe")
        info = source.lstat()
        if int(row.get("trash_inode", info.st_ino)) != info.st_ino:
            raise StorageError("manifest-bound restore item changed")
        destination.parent.mkdir(parents=True, exist_ok=True)
        moved = shutil.move(str(source), str(destination))
        return {"status": "restored", "path": display_path(moved)}


def _tree_digest(path: Path) -> str:
    """Hash a verified local archive tree without following symlinks."""
    digest = hashlib.sha256()
    rows: list[Path] = []
    if path.is_dir() and not path.is_symlink():
        rows = sorted((row for row in path.rglob("*") if not row.is_symlink()), key=lambda row: str(row.relative_to(path)))
    else:
        rows = [path]
    for row in rows:
        relative = "." if row == path else str(row.relative_to(path))
        info = row.lstat()
        digest.update(relative.encode("utf-8"))
        digest.update(str(stat.S_IMODE(info.st_mode)).encode("ascii"))
        if row.is_file():
            with row.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
    return digest.hexdigest()


def _validate_confirmation(action_class: str, confirmation: str) -> None:
    expected = CONFIRMATIONS.get(action_class)
    if expected is None:
        raise StorageError(f"unknown action class: {action_class}")
    if confirmation != expected:
        raise StorageError(f"confirmation must be exactly: {expected}")


def _validate_icloud(candidate: Mapping[str, Any]) -> None:
    cloud = candidate.get("cloud", {})
    status = str(cloud.get("downloading_status", "")).lower()
    if cloud.get("provider") != "icloud" or cloud.get("is_ubiquitous") is not True:
        raise StorageError("candidate is not an iCloud ubiquitous item")
    if cloud.get("is_uploaded") is not True or cloud.get("is_uploading") is True:
        raise StorageError("iCloud item is not fully uploaded")
    if cloud.get("has_unresolved_conflicts") is not False:
        raise StorageError("iCloud item has unresolved or unknown conflicts")
    if cloud.get("is_downloading") is True or status in {"downloading", "downloaded_pending"}:
        raise StorageError("iCloud item is downloading")
    if int(candidate.get("allocated_bytes", 0)) <= 0:
        raise StorageError("iCloud item has no local allocation to evict")


def apply_plan(
    plan: Mapping[str, Any],
    *,
    action_class: str,
    confirmation: str,
    backend: FakeActionBackend | LocalActionBackend,
    time_machine: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if plan.get("plan_sha256") != _document_hash(plan, "plan_sha256"):
        raise StorageError("frozen plan hash does not match")
    _validate_confirmation(action_class, confirmation)
    selected = [row for row in plan.get("minimum_action_set", []) if row.get("action_class") == action_class]
    if not selected:
        raise StorageError(f"frozen plan has no {action_class} actions")
    before = backend.free_bytes(str(plan.get("volume", {}).get("path", "/")))
    target = int(plan["target_free_bytes"])
    actions = []
    trash_manifest = []
    staged = 0
    status = "applied_replan_required"
    for row in selected:
        candidate = row.get("candidate")
        if not isinstance(candidate, dict):
            raise StorageError("plan action is missing its frozen candidate")
        if action_class == "icloud_offload":
            _validate_icloud(candidate)
        if action_class == "safe_cache" and not candidate.get("regeneration_proof"):
            raise StorageError("cache action is not backed by regeneration proof")
        if not backend.verify_candidate(candidate):
            raise StorageError(f"candidate drifted before apply: {candidate.get('id')}")
        result = backend.execute(action_class, candidate)
        actions.append({"candidate_id": candidate["id"], "status": result.get("status"), "result": result})
        if action_class in {"trash", "archive"} and result.get("trash_path"):
            staged += int(candidate["allocated_bytes"])
            trash_path = resolved_path(str(result["trash_path"]))
            inode = trash_path.lstat().st_ino if trash_path.exists() else candidate.get("inode")
            trash_manifest.append({"candidate_id": candidate["id"], "original_path": candidate["path"], "trash_path": result["trash_path"], "trash_inode": inode, "fingerprint": candidate["fingerprint"], "staged_bytes": candidate["allocated_bytes"]})
        current = backend.free_bytes(str(plan.get("volume", {}).get("path", "/")))
        if current >= target:
            status = "target_reached_replan_required"
            break
    after = current
    measured = max(0, after - before)
    if action_class in {"trash", "archive"}:
        measured = 0
    return _checked({
        "schema_version": 1,
        "kind": "storage_apply_record",
        "record_id": f"apply-{_sha(iso_now())[:16]}",
        "created_at": iso_now(),
        "plan_id": plan["plan_id"],
        "plan_sha256": plan["plan_sha256"],
        "action_id": ACTION_IDS[action_class],
        "action_class": action_class,
        "status": status,
        "target_free_bytes": target,
        "free_bytes_before": before,
        "free_bytes_after": after,
        "estimated_reclaimable_bytes": sum(int(row["estimated_reclaimable_bytes"]) for row in selected),
        "staged_bytes": staged,
        "measured_reclaimed_bytes": measured,
        "actions": actions,
        "trash_manifest": trash_manifest,
        "time_machine": dict(time_machine or {"status": "not_checked", "blocking": False}),
        "replan_required": True,
    }, "storage-transaction")


def build_verify_record(source: Mapping[str, Any], *, observed_free_bytes: int) -> dict[str, Any]:
    """Verify an apply record without attributing later volume changes to it."""
    if source.get("kind") != "storage_apply_record":
        raise StorageError("verify storage requires a storage_apply_record")
    before = int(source["free_bytes_before"])
    after = int(source["free_bytes_after"])
    measured = int(source["measured_reclaimed_bytes"])
    return _checked({
        "schema_version": 1,
        "kind": "storage_verify_record",
        "record_id": f"verify-{_sha(iso_now())[:16]}",
        "created_at": iso_now(),
        "plan_id": source["plan_id"],
        "apply_record_id": source["record_id"],
        "action_id": source["action_id"],
        "status": "verified_replan_required",
        "free_bytes_before": before,
        "free_bytes_after": after,
        "observed_free_bytes_at_verify": int(observed_free_bytes),
        "measurement_scope": "apply_transaction",
        "staged_bytes": int(source.get("staged_bytes", 0)),
        "measured_reclaimed_bytes": measured,
        "actions": source.get("actions", []),
        "replan_required": True,
    }, "storage-transaction")


def purge_manifest(record: Mapping[str, Any], *, confirmation: str, backend: FakeActionBackend | LocalActionBackend) -> dict[str, Any]:
    _validate_confirmation("trash_purge", confirmation)
    manifest = record.get("trash_manifest", [])
    if not manifest:
        raise StorageError("apply record has no manifest-bound Trash items")
    before = backend.free_bytes("/")
    actions = []
    for row in manifest:
        actions.append({"candidate_id": row["candidate_id"], **backend.purge(row)})
    after = backend.free_bytes("/")
    return _checked({
        "schema_version": 1,
        "kind": "storage_verify_record",
        "record_id": f"purge-{_sha(iso_now())[:16]}",
        "created_at": iso_now(),
        "plan_id": record["plan_id"],
        "apply_record_id": record["record_id"],
        "action_id": ACTION_IDS["trash_purge"],
        "status": "purged_replan_required",
        "free_bytes_before": before,
        "free_bytes_after": after,
        "staged_bytes": 0,
        "measured_reclaimed_bytes": max(0, after - before),
        "actions": actions,
        "replan_required": True,
    }, "storage-transaction")


def restore_manifest(record: Mapping[str, Any], *, confirmation: str, backend: LocalActionBackend) -> dict[str, Any]:
    _validate_confirmation("restore", confirmation)
    manifest = record.get("trash_manifest", [])
    if not manifest:
        raise StorageError("apply record has no manifest-bound restore items")
    actions = [{"candidate_id": row["candidate_id"], **backend.restore_manifest_row(row)} for row in manifest]
    current = backend.free_bytes("/")
    return _checked({
        "schema_version": 1,
        "kind": "storage_verify_record",
        "record_id": f"restore-{_sha(iso_now())[:16]}",
        "created_at": iso_now(),
        "plan_id": record["plan_id"],
        "apply_record_id": record["record_id"],
        "action_id": ACTION_IDS["restore"],
        "status": "restored_replan_required",
        "free_bytes_before": current,
        "free_bytes_after": current,
        "staged_bytes": 0,
        "measured_reclaimed_bytes": 0,
        "actions": actions,
        "replan_required": True,
    }, "storage-transaction")


def sync_decisions(
    ledger: Mapping[str, Any],
    *,
    confirmation: str,
    destination: Path = PRIVATE_POLICY_PATH,
    public_policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _validate_confirmation("decision_sync", confirmation)
    reusable = []
    for row in ledger.get("decisions", []):
        if row.get("decision") == "unknown":
            continue
        reusable.append({"pattern": row["path_pattern"], "decision": row["decision"]})
    existing = _read_json(destination) if destination.is_file() else {
        "schema_version": 1,
        "kind": "storage_private_policy",
        "path_rules": [],
        "archive_targets": [],
        "execution_authorized": False,
    }
    by_pattern = {
        row.get("pattern"): dict(row)
        for row in existing.get("path_rules", [])
        if isinstance(row, dict) and isinstance(row.get("pattern"), str)
    }
    for row in reusable:
        by_pattern[row["pattern"]] = row
    existing["path_rules"] = [by_pattern[key] for key in sorted(by_pattern)]
    existing["execution_authorized"] = False
    before = destination.read_bytes() if destination.is_file() else None
    encoded = json.dumps(existing, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    if before != encoded:
        _write_json(destination, existing)
    merged = merge_policy(public_policy or _read_json(PUBLIC_POLICY_PATH), existing)
    if merged.get("execution_authorized") is not False:
        raise StorageError("synced Private policy unexpectedly authorized execution")
    return _checked({
        "schema_version": 1,
        "kind": "storage_apply_record",
        "record_id": f"sync-{_sha(iso_now())[:16]}",
        "created_at": iso_now(),
        "plan_id": "decision-ledger",
        "plan_sha256": _sha(_canonical(ledger)),
        "action_id": ACTION_IDS["decision_sync"],
        "action_class": "decision_sync",
        "status": "unchanged" if before == encoded else "synced",
        "target_free_bytes": 0,
        "free_bytes_before": 0,
        "free_bytes_after": 0,
        "estimated_reclaimable_bytes": 0,
        "staged_bytes": 0,
        "measured_reclaimed_bytes": 0,
        "actions": [{"path_rules": len(reusable), "execution_authorized": False}],
        "trash_manifest": [],
        "time_machine": {"status": "not_applicable", "blocking": False},
        "replan_required": True,
    }, "storage-transaction")


def import_mole_history(payload: Mapping[str, Any], *, existing: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(row["evidence_id"]): dict(row) for row in existing if isinstance(row, dict) and row.get("evidence_id")}
    for section in ("sessions", "deletions", "logs"):
        for row in payload.get(section, []) if isinstance(payload.get(section, []), list) else []:
            if not isinstance(row, dict):
                continue
            evidence_id = f"mole-{_sha(_canonical({'section': section, 'row': row}))[:20]}"
            by_id[evidence_id] = {"evidence_id": evidence_id, "source": "mole", "section": section, "authority": "evidence_only", "observed": row}
    return sorted(by_id.values(), key=lambda row: row["evidence_id"])


def should_notify_weekly(*, free_bytes: int, target_free_bytes: int, new_high_confidence_bytes: int, battery_percent: int | None, on_ac_power: bool, cooldown_active: bool) -> bool:
    if cooldown_active:
        return False
    if battery_percent is not None and battery_percent < 20 and not on_ac_power:
        return False
    return free_bytes < target_free_bytes or new_high_confidence_bytes >= 5 * GIB


def evaluate_weekly_scan(scan: Mapping[str, Any], policy: Mapping[str, Any], previous: Mapping[str, Any] | None, *, power: Mapping[str, Any], now: dt.datetime | None = None) -> dict[str, Any]:
    current = now or utc_now()
    weekly = policy.get("weekly", {})
    minimum_power = int(weekly.get("low_battery_percent", 20))
    if power.get("available") and not power.get("charging") and isinstance(power.get("percentage"), int) and int(power["percentage"]) < minimum_power:
        return {"mode": "deferred_low_battery", "notify": False, "auto_cleanup": False, "power": dict(power)}
    prior_fingerprints = set((previous or {}).get("candidate_fingerprints", []))
    fresh = [row for row in scan.get("candidates", []) if row.get("eligible") and row.get("confidence") == "high" and row.get("fingerprint") not in prior_fingerprints]
    fresh_bytes = sum(int(row.get("estimated_reclaimable_bytes", 0)) for row in fresh)
    last = (previous or {}).get("last_notified_at")
    cooldown_active = False
    if isinstance(last, str):
        try:
            cooldown_active = current - dt.datetime.fromisoformat(last.replace("Z", "+00:00")) < dt.timedelta(hours=int(weekly.get("cooldown_hours", 168)))
        except ValueError:
            cooldown_active = False
    target, _target_mode = _target(policy, scan, "auto")
    notify = should_notify_weekly(
        free_bytes=int(scan["volume"]["free_bytes"]),
        target_free_bytes=target,
        new_high_confidence_bytes=fresh_bytes,
        battery_percent=power.get("percentage") if isinstance(power.get("percentage"), int) else None,
        on_ac_power=bool(power.get("charging")),
        cooldown_active=cooldown_active,
    )
    return {
        "mode": "read_only_weekly_scan",
        "notify": notify,
        "auto_cleanup": False,
        "below_target": int(scan["volume"]["free_bytes"]) < target,
        "target_free_bytes": target,
        "new_high_confidence_bytes": fresh_bytes,
        "new_candidate_ids": [row["id"] for row in fresh],
        "candidate_fingerprints": [row["fingerprint"] for row in scan.get("candidates", [])],
        "last_notified_at": current.isoformat() if notify else last,
        "evaluated_at": current.isoformat(),
        "power": dict(power),
    }


def redact_for_export(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if key in {"path", "record", "original_path", "trash_path", "archive_path"} and isinstance(child, str):
                result[f"{key}_alias"] = "~/..." if child.startswith(str(Path.home())) or child.startswith("~/") else "/..."
                result[f"{key}_hash"] = _sha(child)
            else:
                result[key] = redact_for_export(child)
        return result
    if isinstance(value, list):
        return [redact_for_export(item) for item in value]
    return value


def _latest(directory: Path, pattern: str) -> Path:
    rows = sorted(directory.glob(pattern), key=lambda path: path.stat().st_mtime_ns)
    if not rows:
        raise StorageError(f"no machine-local {pattern} record found")
    return rows[-1]


def _ledger_path(state_dir: Path) -> Path:
    return state_dir / "storage" / "decision-ledger.json"


def _load_ledger(path: Path) -> dict[str, Any]:
    if path.is_file():
        value = _read_json(path)
        if isinstance(value, dict) and isinstance(value.get("decisions"), list):
            return _checked(value, "storage-decision-ledger")
        raise StorageError("decision ledger is invalid")
    return _checked({"schema_version": 1, "kind": "storage_decision_ledger", "updated_at": iso_now(), "decisions": [], "mole_evidence": []}, "storage-decision-ledger")


def _record_path(storage_state: Path, prefix: str) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return storage_state / f"{prefix}-{stamp}.json"


def _print(value: Any, *, redacted: bool = False) -> None:
    print(json.dumps(redact_for_export(value) if redacted else value, ensure_ascii=False, indent=2))


def scan_summary(result: Mapping[str, Any], record: Path) -> dict[str, Any]:
    visible = set(result.get("summary_candidate_ids", []))
    console_limit = 20
    candidate_fields = (
        "id",
        "path",
        "kind",
        "logical_bytes",
        "allocated_bytes",
        "estimated_reclaimable_bytes",
        "potential_reclaimable_bytes",
        "confidence",
        "risk",
        "action_class",
        "proposed_action_class",
        "eligible",
        "policy_decision",
        "reasons",
        "handoff",
    )
    candidates = [
        {key: row[key] for key in candidate_fields if key in row}
        for row in result.get("candidates", [])
        if row.get("id") in visible
    ][:console_limit]
    system_facts = dict(result["system_facts"])
    home_top = list(system_facts.get("home_top", []))
    system_facts["home_top"] = home_top[:20]
    system_facts["omitted_home_top_count"] = max(0, len(home_top) - 20)
    return {
        "record": display_path(record),
        "schema_version": result["schema_version"],
        "kind": result["kind"],
        "scan_id": result["scan_id"],
        "generated_at": result["generated_at"],
        "mode": result["mode"],
        "volume": result["volume"],
        "system_facts": system_facts,
        "roots": result["roots"],
        "candidates": candidates,
        "candidate_count": len(result.get("candidates", [])),
        "omitted_candidate_count": max(0, len(result.get("candidates", [])) - len(candidates)),
        "errors": result["errors"],
        **({"weekly": result["weekly"]} if "weekly" in result else {}),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan")
    scan.add_argument("--mode", choices=["quick", "deep"], default="quick")
    scan.add_argument("--root", action="append", default=[])
    scan.add_argument("--weekly", action="store_true")
    scan.add_argument("--redacted", action="store_true")
    add_state_dir_argument(scan)
    review = sub.add_parser("review")
    review.add_argument("--candidate", required=True)
    review.add_argument("--decision", choices=sorted(DECISIONS), required=True)
    review.add_argument("--review-after")
    review.add_argument("--note")
    review.add_argument("--scan", type=Path)
    review.add_argument("--apply", action="store_true")
    add_state_dir_argument(review)
    plan = sub.add_parser("plan")
    plan.add_argument("--scan", type=Path)
    target_group = plan.add_mutually_exclusive_group()
    target_group.add_argument("--target", default="auto")
    target_group.add_argument("--target-free")
    plan.add_argument("--redacted", action="store_true")
    add_state_dir_argument(plan)
    apply = sub.add_parser("apply")
    apply.add_argument("plan", type=Path)
    apply.add_argument("--action-class", choices=sorted(CONFIRMATIONS), required=True)
    apply.add_argument("--apply", action="store_true")
    apply.add_argument("--confirm", default="")
    add_state_dir_argument(apply)
    verify = sub.add_parser("verify")
    verify.add_argument("record", type=Path)
    verify.add_argument("--redacted", action="store_true")
    add_state_dir_argument(verify)
    history = sub.add_parser("history")
    history.add_argument("--import-mole", action="store_true")
    history.add_argument("--import-mole-json", type=Path)
    history.add_argument("--redacted", action="store_true")
    add_state_dir_argument(history)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    state_dir = resolve_state_dir(args.state_dir)
    storage_state = state_dir / "storage"
    try:
        policy = load_policy()
        if args.command == "scan":
            roots = _scan_roots(policy, args.mode, args.root)
            system_facts, handoffs = collect_system_context(mode=args.mode, policy=policy)
            result = build_scan(
                policy=policy,
                mode=args.mode,
                roots=roots,
                metadata=SwiftMetadataBackend(state_dir),
                system_facts=system_facts,
                handoff_candidates=handoffs,
            )
            if args.weekly:
                weekly_path = storage_state / "weekly-ledger.json"
                previous = _read_json(weekly_path) if weekly_path.is_file() else None
                result["weekly"] = evaluate_weekly_scan(result, policy, previous, power=power_status())
                if result["weekly"]["mode"] != "deferred_low_battery":
                    _write_json(weekly_path, result["weekly"])
            path = _record_path(storage_state, "scan")
            _write_json(path, result)
            _print(scan_summary(result, path), redacted=args.redacted)
            return 0
        if args.command == "review":
            scan_path_value = args.scan or _latest(storage_state, "scan-*.json")
            scan = _read_json(scan_path_value)
            candidate = next((row for row in scan.get("candidates", []) if row.get("id") == args.candidate), None)
            if not candidate:
                raise StorageError(f"candidate not found in scan: {args.candidate}")
            decision = build_decision(candidate, args.decision, review_after=args.review_after, note=args.note)
            if not args.apply:
                _print({"status": "preview", "decision": decision, "writes": False})
                return 0
            ledger_path = _ledger_path(state_dir)
            ledger = _load_ledger(ledger_path)
            ledger["decisions"] = [row for row in ledger["decisions"] if row.get("candidate_id") != candidate["id"]]
            ledger["decisions"].append(decision)
            ledger["updated_at"] = iso_now()
            _write_json(ledger_path, ledger)
            _print({"status": "recorded", "record": display_path(ledger_path), "decision": decision})
            return 0
        if args.command == "plan":
            source = args.scan or _latest(storage_state, "scan-*.json")
            scan = _read_json(source)
            ledger = _load_ledger(_ledger_path(state_dir))
            requested_target = args.target_free if args.target_free is not None else args.target
            result = build_plan(scan, policy, decisions=ledger["decisions"], target=requested_target)
            path = _record_path(storage_state, "plan")
            _write_json(path, result)
            _print({"record": display_path(path), **result}, redacted=args.redacted)
            return 0
        if args.command == "apply":
            plan = _read_json(args.plan)
            if not args.apply:
                if args.action_class in {"trash_purge", "restore"}:
                    targets = [row.get("candidate_id") for row in plan.get("trash_manifest", [])]
                elif args.action_class == "decision_sync":
                    targets = [row.get("candidate_id") for row in plan.get("decisions", [])]
                else:
                    targets = [row["candidate_id"] for row in plan.get("minimum_action_set", []) if row.get("action_class") == args.action_class]
                _print({"status": "dry_run", "plan_id": plan.get("plan_id"), "action_class": args.action_class, "would_apply": targets, "required_confirmation": CONFIRMATIONS[args.action_class], "writes": False})
                return 0
            backend = LocalActionBackend(state_dir, policy)
            if args.action_class == "trash_purge":
                result = purge_manifest(plan, confirmation=args.confirm, backend=backend)
            elif args.action_class == "restore":
                result = restore_manifest(plan, confirmation=args.confirm, backend=backend)
            elif args.action_class == "decision_sync":
                result = sync_decisions(plan, confirmation=args.confirm)
            else:
                result = apply_plan(plan, action_class=args.action_class, confirmation=args.confirm, backend=backend, time_machine={**check_time_machine(), "blocking": False})
            path = _record_path(storage_state, "transaction")
            _write_json(path, result)
            _print({"record": display_path(path), **result})
            return 0
        if args.command == "verify":
            source = _read_json(args.record)
            current = shutil.disk_usage("/").free
            result = build_verify_record(source, observed_free_bytes=current)
            path = _record_path(storage_state, "verify")
            _write_json(path, result)
            _print({"record": display_path(path), **result}, redacted=args.redacted)
            return 0
        ledger_path = _ledger_path(state_dir)
        ledger = _load_ledger(ledger_path)
        if args.import_mole:
            completed = subprocess.run(["mole", "history", "--json"], capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                raise StorageError(completed.stderr.strip() or "mole history --json failed")
            ledger["mole_evidence"] = import_mole_history(json.loads(completed.stdout), existing=ledger["mole_evidence"])
            ledger["updated_at"] = iso_now()
            _write_json(ledger_path, ledger)
        if args.import_mole_json:
            ledger["mole_evidence"] = import_mole_history(_read_json(args.import_mole_json), existing=ledger["mole_evidence"])
            ledger["updated_at"] = iso_now()
            _write_json(ledger_path, ledger)
        records = [display_path(path) for path in sorted(storage_state.glob("*.json"))]
        _print({"schema_version": 1, "kind": "storage_history", "ledger": ledger, "records": records}, redacted=args.redacted)
        return 0
    except (StorageError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
