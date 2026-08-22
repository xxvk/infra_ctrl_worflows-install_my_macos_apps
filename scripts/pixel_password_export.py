#!/usr/bin/env python3
"""Build a reviewed Chrome password CSV for the Pixel's needs-login apps.

The script reads an Apple Passwords CSV locally. It never prints passwords or
usernames. Exact hosts come from a reviewed Private allowlist, while account
choices are SHA-256 selectors in a separate Private decisions file.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "Private"
CATALOG = ROOT / "references/android-app-catalog.json"
GOOGLE_HOSTS = {"google.com", "accounts.google.com", "myaccount.google.com"}


def secure_write(path: Path, writer) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer(handle)
    os.chmod(path, 0o600)


def host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def latest_scan() -> Path:
    scans = sorted(PRIVATE.glob("android-login-scan-final-*.json"))
    if not scans:
        raise SystemExit("No Private/android-login-scan-final-*.json found.")
    return scans[-1]


def build_scope(scan_path: Path, scope_path: Path) -> list[dict]:
    scan = json.loads(scan_path.read_text())
    catalog = json.loads(CATALOG.read_text())["apps"]
    by_package = {item["play_store_package"]: item for item in catalog}
    apps = []
    for result in scan["results"]:
        if result.get("status") != "needs_login":
            continue
        package = result["package"]
        item = by_package.get(package, {})
        apps.append({"package": package, "name": item.get("name"), "category": item.get("category", "unmapped")})
    apps.sort(key=lambda item: (item["category"], item["name"] or "", item["package"]))
    payload = {
        "schema_version": 1,
        "kind": "pixel_password_import_scope",
        "source": {"login_scan": str(scan_path.relative_to(ROOT)), "selection": "status == needs_login"},
        "excluded_identity_providers": sorted(GOOGLE_HOSTS),
        "apps": apps,
    }
    secure_write(scope_path, lambda handle: handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n"))
    return apps


def load_hosts(allowlist: Path, packages: set[str]) -> set[str]:
    hosts: set[str] = set()
    with allowlist.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("decision") != "import" or row.get("package") not in packages:
                continue
            hosts.update(value for value in row.get("allowed_hosts", "").split(";") if value)
    forbidden = hosts & GOOGLE_HOSTS
    if forbidden:
        raise SystemExit(f"Allowlist must not include Google hosts: {sorted(forbidden)}")
    return hosts


def load_decisions(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    return {item["host"]: item for item in json.loads(path.read_text()).get("decisions", [])}


def allowed(row: dict, decisions: dict[str, dict]) -> bool:
    decision = decisions.get(host(row["URL"]))
    if not decision or decision["action"] == "keep_all":
        return True
    if decision["action"] == "exclude":
        return False
    selected = sha256(row.get("Username", "")) == decision.get("username_sha256")
    return selected if decision["action"] == "keep_only_username_sha256" else not selected


def run(args: argparse.Namespace) -> int:
    scan = Path(args.scan) if args.scan else latest_scan()
    scope = Path(args.scope)
    apps = build_scope(scan, scope)
    hosts = load_hosts(Path(args.allowlist), {app["package"] for app in apps})
    decisions = load_decisions(Path(args.decisions))
    rows, seen = [], set()
    with Path(args.apple_csv).open(newline="") as handle:
        for row in csv.DictReader(handle):
            if host(row.get("URL", "")) not in hosts or not allowed(row, decisions):
                continue
            record = (row.get("URL", ""), row.get("Username", ""), row.get("Password", ""))
            if record not in seen:
                seen.add(record)
                rows.append(record)
    rows.sort(key=lambda row: (host(row[0]), row[1], row[0]))
    by_host, by_pair = defaultdict(set), Counter()
    for url, username, password in rows:
        by_host[host(url)].add(username)
        by_pair[(host(url), username)] += 1
    conflicts = {
        "hosts_with_multiple_usernames": sorted(name for name, users in by_host.items() if len(users) > 1),
        "host_username_pairs_with_multiple_records": sorted(f"{name}:{user}" for (name, user), count in by_pair.items() if count > 1),
    }
    def write_export(handle):
        writer = csv.writer(handle)
        writer.writerow(["url", "username", "password"])
        writer.writerows(rows)
    secure_write(Path(args.output), write_export)
    def write_review(handle):
        writer = csv.writer(handle)
        writer.writerow(["host", "credential_count", "distinct_username_count", "decision"])
        for name in sorted(by_host):
            writer.writerow([name, sum(host(url) == name for url, *_ in rows), len(by_host[name]), decisions.get(name, {}).get("action", "review_required")])
    secure_write(Path(args.review), write_review)
    summary = {"scope_app_count": len(apps), "records": len(rows), "allowed_host_count": len(hosts), **conflicts}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.final and any(conflicts.values()):
        print("Unresolved duplicate-account decisions remain; refusing final export.", file=sys.stderr)
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apple-csv", required=True, help="Apple Passwords CSV; stays local and is never logged")
    parser.add_argument("--allowlist", required=True, help="Private host allowlist CSV with exact approved hosts")
    parser.add_argument("--decisions", default=PRIVATE / "pixel-password-import-decisions.json")
    parser.add_argument("--scan", help="Defaults to the newest Private Android login scan")
    parser.add_argument("--scope", default=PRIVATE / "pixel-password-import-scope.json")
    parser.add_argument("--output", required=True, help="Chrome CSV output; contains plaintext passwords")
    parser.add_argument("--review", required=True, help="Password-free host review CSV")
    parser.add_argument("--final", action="store_true", help="Fail when any host has unresolved multiple usernames")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
