#!/usr/bin/env python3
# Mutation action IDs: claude-vm.remove-images, claude-vm.remove-bundle, claude-vm.lock, claude-vm.unlock
"""Inspect or reclaim Claude Desktop's local-agent VM images safely."""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path.home() / "Library" / "Application Support" / "Claude"
BUNDLE = ROOT / "vm_bundles" / "claudevm.bundle"
CONFIRM_REMOVE = "REMOVE CLAUDE VM IMAGES"
CONFIRM_REMOVE_BUNDLE = "REMOVE CLAUDE VM BUNDLE"
CONFIRM_LOCK = "LOCK CLAUDE VM DIRECTORY"
ISSUE_URL = "https://github.com/anthropics/claude-code/issues/65577"


def size(path):
    if not path.exists():
        return 0
    result = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True, check=False)
    return int(result.stdout.split()[0]) * 1024 if result.returncode == 0 and result.stdout else 0


def processes():
    result = subprocess.run(["pgrep", "-fal", "vfkit|gvisor|claudevm"], capture_output=True, text=True, check=False)
    return result.stdout.splitlines() if result.returncode == 0 else []


def report():
    images = [BUNDLE / "rootfs.img", BUNDLE / "sessiondata.img"]
    return {
        "issue_url": ISSUE_URL,
        "issue_status_note": "Open; stale; no assignee, milestone, project, branch, or pull request observed during the last review",
        "claude_support_path": str(ROOT),
        "vm_bundle_path": str(BUNDLE),
        "vm_bundle_exists": BUNDLE.exists(),
        "vm_bundle_bytes": size(BUNDLE),
        "images": [{"path": str(path), "exists": path.exists(), "bytes": size(path)} for path in images],
        "processes_holding_vm": processes(),
        "lock_state": subprocess.run(["ls", "-ldO", str(ROOT / "vm_bundles")], capture_output=True, text=True, check=False).stdout.strip(),
        "warning": "Deleting VM images disables or rebuilds Claude Cowork/local-agent execution and must be done only while Claude is fully quit.",
    }


def inspect(_args):
    print(json.dumps(report(), ensure_ascii=False, indent=2))


def remove(args):
    if args.confirm != CONFIRM_REMOVE:
        raise SystemExit(f"Type exactly: {CONFIRM_REMOVE}")
    active = processes()
    if active:
        raise SystemExit("Claude VM-related processes are running; quit Claude and retry: " + " | ".join(active))
    deleted = []
    for name in ("rootfs.img", "sessiondata.img"):
        path = BUNDLE / name
        if path.exists():
            path.unlink()
            deleted.append(str(path))
    print(json.dumps({"action_id": "claude-vm.remove-images", "deleted": deleted, "remaining_bundle_bytes": size(BUNDLE), "issue_url": ISSUE_URL}, ensure_ascii=False, indent=2))


def remove_bundle(args):
    if args.confirm != CONFIRM_REMOVE_BUNDLE:
        raise SystemExit(f"Type exactly: {CONFIRM_REMOVE_BUNDLE}")
    active = processes()
    if active:
        raise SystemExit("Claude VM-related processes are running; quit Claude and retry: " + " | ".join(active))
    deleted_bytes = size(BUNDLE)
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    print(json.dumps({"action_id": "claude-vm.remove-bundle", "deleted_bundle": str(BUNDLE), "deleted_bytes": deleted_bytes, "exists": BUNDLE.exists(), "issue_url": ISSUE_URL}, ensure_ascii=False, indent=2))


def lock(args):
    if args.confirm != CONFIRM_LOCK:
        raise SystemExit(f"Type exactly: {CONFIRM_LOCK}")
    if processes():
        raise SystemExit("Claude VM-related processes are running; quit Claude before locking the directory.")
    target = ROOT / "vm_bundles"
    target.mkdir(parents=True, exist_ok=True)
    os.chmod(target, 0)
    subprocess.run(["chflags", "uchg", str(target)], check=True)
    print(json.dumps({"action_id": "claude-vm.lock", "status": "locked", "target": str(target)}, ensure_ascii=False, indent=2))


def unlock(_args):
    target = ROOT / "vm_bundles"
    subprocess.run(["chflags", "nouchg", str(target)], check=False)
    if target.exists():
        os.chmod(target, 0o700)
    print(json.dumps({"action_id": "claude-vm.unlock", "status": "unlocked", "target": str(target)}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(required=True)
    for name, func in (("inspect", inspect), ("remove", remove), ("remove-bundle", remove_bundle), ("lock", lock), ("unlock", unlock)):
        command = sub.add_parser(name)
        if name in {"remove", "remove-bundle"}:
            command.add_argument("--confirm", required=True)
        elif name == "lock":
            command.add_argument("--confirm", required=True)
        command.set_defaults(func=func)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
