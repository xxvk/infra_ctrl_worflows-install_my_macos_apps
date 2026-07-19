#!/usr/bin/env python3
"""Read-only inventory of local Google Chrome profiles.

This reads profile labels and the email exposed in Chrome's Local State only;
it never reads cookies, passwords, tokens, or Keychain data.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def local_state_path() -> Path:
    return Path.home() / "Library/Application Support/Google/Chrome/Local State"


def inspect(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "profiles": [], "error": "Local State not found"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"path": str(path), "profiles": [], "error": str(exc)}

    cache = data.get("profile", {}).get("info_cache", {})
    profiles = []
    for directory, info in sorted(cache.items()):
        if not isinstance(info, dict):
            info = {}
        profiles.append(
            {
                "profile_directory": directory,
                "display_name": info.get("name", directory),
                "account_email": info.get("user_name", ""),
                "gaia_name_present": bool(info.get("gaia_name")),
                "user_name_present": bool(info.get("user_name")),
                "is_using_default_name": bool(info.get("is_using_default_name", False)),
            }
        )
    return {
        "path": str(path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profiles": profiles,
        "privacy_note": "Only Chrome Local State profile labels and account emails were read; no cookies, passwords, tokens, or Keychain data were read.",
    }


def compare(inventory: dict, expected_path: Path) -> dict:
    try:
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"error": str(exc)}
    actual = inventory.get("profiles", [])
    expected_profiles = expected.get("profiles", [])
    actual_by_email = {p.get("account_email", "").casefold(): p for p in actual if p.get("account_email")}
    expected_by_email = {p.get("account_email", "").casefold(): p for p in expected_profiles if p.get("account_email")}
    missing = sorted(expected_by_email[email].get("account_email", "") for email in set(expected_by_email) - set(actual_by_email))
    extra = sorted(actual_by_email[email].get("account_email", "") for email in set(actual_by_email) - set(expected_by_email))
    directory_mismatches, name_mismatches = [], []
    for email in sorted(set(expected_by_email) & set(actual_by_email)):
        exp, got = expected_by_email[email], actual_by_email[email]
        if exp.get("profile_directory") != got.get("profile_directory"):
            directory_mismatches.append({"account_email": exp.get("account_email", ""), "expected": exp.get("profile_directory", ""), "detected": got.get("profile_directory", "")})
        if exp.get("display_name") != got.get("display_name"):
            name_mismatches.append({"account_email": exp.get("account_email", ""), "expected": exp.get("display_name", ""), "detected": got.get("display_name", "")})
    return {
        "expected": str(expected_path),
        "expected_count": len(expected_profiles),
        "detected_count": len(actual),
        "missing": missing,
        "extra": extra,
        "directory_mismatches": directory_mismatches,
        "directory_match_is_informational": True,
        "name_mismatches": name_mismatches,
        "email_matching": not missing and not extra,
        "profile_identity_rule": "account_email",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory Chrome profiles without reading credentials")
    parser.add_argument("--path", type=Path, default=local_state_path())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected", type=Path, help="tracked expected profile registry to compare")
    args = parser.parse_args()
    result = inspect(args.path)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if args.expected:
        print(json.dumps({"comparison": compare(result, args.expected)}, ensure_ascii=False, indent=2))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
