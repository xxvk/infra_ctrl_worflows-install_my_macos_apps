#!/usr/bin/env python3
"""Create and apply auditable, capacity-aware macOS app plans."""
import argparse
import datetime as dt
import json
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references" / "app-catalog.json"
STATE = ROOT / "state"
APP_DIRS = [Path("/Applications"), Path.home() / "Applications", Path("/System/Applications")]


def stamp():
    return dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def write_record(prefix, value):
    STATE.mkdir(exist_ok=True)
    path = STATE / f"{prefix}-{stamp()}.json"
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return path


def catalog():
    return json.loads(CATALOG.read_text())


def installed_brew_casks():
    """Return installed Homebrew cask tokens when Homebrew is available."""
    brew = shutil.which("brew")
    if not brew:
        for candidate in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew"):
            if Path(candidate).is_file():
                brew = candidate
                break
    if not brew:
        return set()
    result = subprocess.run([brew, "list", "--cask"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return set()
    return {line.strip().casefold() for line in result.stdout.splitlines() if line.strip()}


def app_store_receipt(path):
    """Return the App Store receipt path, if this bundle has one."""
    receipt = Path(path) / "Contents" / "_MASReceipt" / "receipt"
    if receipt.is_file():
        return str(receipt)
    # Newer/legacy Mac Catalyst packages may retain iTunes metadata in a
    # Wrapper directory without the traditional _MASReceipt bundle.
    metadata = Path(path) / "Wrapper" / "iTunesMetadata.plist"
    return str(metadata) if metadata.is_file() else None


def expected_source(app):
    if app.get("app_store_url"):
        return "app_store"
    if app.get("brew_cask") or app.get("brew_formula"):
        return "homebrew"
    if app.get("system_app"):
        return "system"
    if app.get("official_url"):
        return "official_web"
    return "unknown"


def detect_source(catalog_app, installed_item, brew_casks):
    """Compare an installed bundle with its catalog delivery method.

    This is evidence-based rather than forensic: an App Store receipt is strong
    evidence, and a matching installed Homebrew cask is useful evidence. A
    downloaded DMG/ZIP cannot be distinguished from another manual source, so it
    is reported as ``manual_or_unknown`` and is never silently accepted as a
    verified App Store/Homebrew install.
    """
    path = installed_item["path"]
    receipt = app_store_receipt(path)
    token = catalog_app.get("brew_cask")
    brew_match = bool(token and token.casefold() in brew_casks)
    detected = []
    if receipt:
        detected.append("app_store")
    if brew_match:
        detected.append("homebrew")
    if catalog_app.get("system_app") and path.startswith("/System/Applications/"):
        detected.append("system")
    if not detected:
        detected.append("manual_or_unknown")
    expected = expected_source(catalog_app)
    source = detected[0]
    if expected in {"app_store", "homebrew", "system"}:
        match = expected == source
    elif expected == "official_web":
        # A downloaded DMG/ZIP has no portable provenance marker. Unknown is
        # therefore a manual verification item, not proof that the vendor is
        # wrong; a known App Store/Homebrew/system source is a real mismatch.
        match = None if source == "manual_or_unknown" else source == expected
    else:
        match = None
    return {
        "expected": expected,
        "detected": source,
        "detected_sources": detected,
        "match": match,
        "evidence": {"path": path, "app_store_receipt": receipt, "homebrew_cask": token if brew_match else None},
    }


def installed_apps(data=None):
    data = data or catalog()
    by_name = {}
    for app in data["apps"]:
        for name in [app["name"], *app.get("aliases", [])]:
            by_name[name.casefold()] = app
    brew_casks = installed_brew_casks()
    found = []
    for directory in APP_DIRS:
        if not directory.is_dir():
            continue
        for app in directory.glob("*.app"):
            info = app / "Contents" / "Info.plist"
            name = app.stem
            version = None
            bundle_identifier = None
            try:
                with info.open("rb") as f:
                    meta = plistlib.load(f)
                name = meta.get("CFBundleDisplayName") or meta.get("CFBundleName") or name
                version = meta.get("CFBundleShortVersionString")
                bundle_identifier = meta.get("CFBundleIdentifier")
            # Some third-party bundles contain a malformed Info.plist. Keep the
            # inventory useful by falling back to the bundle filename.
            except Exception:
                pass
            item = {"name": name, "version": version, "path": str(app)}
            if bundle_identifier:
                item["bundle_identifier"] = bundle_identifier
            entry = by_name.get(name.casefold())
            if entry:
                item["source"] = detect_source(entry, item, brew_casks)
            else:
                receipt = app_store_receipt(app)
                item["source"] = {
                    "expected": "unlisted",
                    "detected": "app_store" if receipt else "manual_or_unknown",
                    "detected_sources": ["app_store"] if receipt else ["manual_or_unknown"],
                    "match": None,
                    "evidence": {"path": str(app), "app_store_receipt": receipt, "homebrew_cask": None},
                }
            found.append(item)
    return sorted(found, key=lambda item: item["name"].casefold())


def app_present(app, installed_names):
    command = app.get("check_command")
    if command:
        return shutil.which(command) is not None
    names = [app["name"], *app.get("aliases", [])]
    if any(name.casefold() in installed_names for name in names):
        return True
    identifiers = {value.casefold() for value in app.get("bundle_identifiers", [])}
    return bool(identifiers & installed_names)


def storage_gb():
    return shutil.disk_usage("/").total / 1024 ** 3


def choose_profile(requested):
    if requested != "auto":
        return requested
    return "expanded" if storage_gb() >= 512 else "portable"


def scan(_args):
    applications = installed_apps()
    result = {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "computer_name": os.uname().nodename,
        "macos_version": subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True).stdout.strip(),
        "storage_total_gb": round(storage_gb(), 1),
        "applications": applications,
    }
    path = write_record("scan", result)
    print(f"Wrote {path}")
    print(f"Found {len(result['applications'])} apps; storage: {result['storage_total_gb']} GB")
    mismatches = [item for item in applications if item.get("source", {}).get("match") is False]
    if mismatches:
        print(f"Source mismatches requiring review: {len(mismatches)}")
        for item in mismatches:
            source = item["source"]
            print(f"- {item['name']}: expected {source['expected']}, detected {source['detected']}")


def plan(args):
    data = catalog()
    profile = choose_profile(args.profile)
    installed = installed_apps(data)
    installed_names = {
        value.casefold()
        for item in installed
        for value in (item["name"], item.get("bundle_identifier", ""))
        if value
    }
    selected = []
    for app in data["apps"]:
        if app["tier"] == "heavy" and profile == "portable":
            continue
        selected.append(app)
    missing = [app for app in selected if not app_present(app, installed_names)]
    mismatches = []
    for item in installed:
        if not item.get("source") or item["source"].get("match") is not False:
            continue
        mismatches.append({"app": item["name"], "path": item["path"], "source": item["source"]})
    follow_up = [{"app": app["name"], "tasks": app.get("follow_up", [])} for app in missing if app.get("follow_up")]
    result = {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "profile": profile,
        "storage_total_gb": round(storage_gb(), 1),
        "catalog": str(CATALOG.relative_to(ROOT)),
        "installed_count": len(installed),
        "selected_count": len(selected),
        "missing": missing,
        "source_mismatches": mismatches,
        "estimated_download_gb": round(sum(app.get("size_gb", 0) for app in missing), 1),
        "follow_up": follow_up,
        "completion_notes": []
    }
    path = write_record("plan", result)
    print(f"Wrote {path}")
    print(f"Profile: {profile}; missing: {len(missing)}; estimated footprint: {result['estimated_download_gb']} GB")
    for app in missing:
        if app.get("brew_cask"):
            delivery = f"brew install --cask {app['brew_cask']}"
        elif app.get("brew_formula"):
            delivery = f"brew install {app['brew_formula']}"
        else:
            delivery = app.get("app_store_url") or app.get("official_url", "no source recorded")
        print(f"- {app['name']}: {delivery}")
    if mismatches:
        print("Source mismatches (review and reinstall from the expected source):")
        for item in mismatches:
            source = item["source"]
            print(f"- {item['app']}: expected {source['expected']}, detected {source['detected']} ({item['path']})")


def run(command, apply):
    print("+", " ".join(command))
    if apply:
        subprocess.run(command, check=True)


def path_size(path):
    """Return a path's apparent size in bytes, or 0 when it is absent."""
    target = Path(path)
    if not target.exists():
        return 0
    result = subprocess.run(["du", "-skL", str(target)], capture_output=True, text=True, check=True)
    return int(result.stdout.split()[0]) * 1024


def brew_cache_path(app):
    """Ask Homebrew for the artifact cache path for a catalog entry."""
    identifier = app.get("brew_cask") or app.get("brew_formula")
    if not identifier:
        return None
    command = ["brew", "--cache"]
    if app.get("brew_cask"):
        command.append("--cask")
    command.append(identifier)
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    path = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    return Path(path) if path else None


def installed_size(app):
    """Measure installed bytes for a GUI app or Homebrew formula."""
    if app.get("brew_formula"):
        result = subprocess.run(["brew", "--prefix", app["brew_formula"]], capture_output=True, text=True, check=False)
        return path_size(result.stdout.strip()) if result.returncode == 0 else 0
    return path_size(Path("/Applications") / f"{app['name']}.app")


def install(args):
    plan_file = Path(args.plan).expanduser().resolve()
    plan_data = json.loads(plan_file.read_text())
    selected = plan_data["missing"]
    if not args.only:
        raise SystemExit("Select one or two apps with --only; do not install an entire plan at once.")
    if len(args.only) > 2:
        raise SystemExit("A run may contain at most two --only app names.")
    wanted = {name.casefold() for name in args.only}
    selected = [app for app in selected if app["name"].casefold() in wanted]
    absent = wanted - {app["name"].casefold() for app in selected}
    if absent:
        raise SystemExit("App not found in this plan: " + ", ".join(sorted(absent)))
    brew_apps = [app for app in selected if app.get("brew_cask") or app.get("brew_formula")]
    manual_apps = [app for app in selected if not (app.get("brew_cask") or app.get("brew_formula"))]
    if not args.apply:
        print("DRY RUN — nothing will be installed. Re-run with --apply after review.")
    if brew_apps and not shutil.which("brew"):
        print("Homebrew is not installed.")
        run(["/bin/bash", "-c", "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"], args.apply)
        if args.apply:
            print("Restart the shell if Homebrew is not yet on PATH, then rerun this command.")
            return
    measurements = []
    for app in brew_apps:
        command = ["brew", "install"]
        if app.get("brew_cask"):
            command.extend(["--cask", app["brew_cask"]])
        else:
            command.append(app["brew_formula"])
        cache_path = brew_cache_path(app)
        before_download = path_size(cache_path) if cache_path else 0
        started = dt.datetime.now().astimezone().isoformat()
        run(command, args.apply)
        after_download = path_size(cache_path) if cache_path else 0
        measurements.append({
            "app": app["name"],
            "started_at": started,
            "finished_at": dt.datetime.now().astimezone().isoformat(),
            "download_bytes": max(after_download - before_download, 0) or after_download,
            "installed_bytes": installed_size(app) if args.apply else 0,
            "status": "installed" if args.apply else "dry_run",
        })
    if manual_apps:
        print("\nManual/App Store items (not downloaded automatically):")
        for app in manual_apps:
            print(f"- {app['name']}: {app.get('app_store_url') or app.get('official_url') or 'source missing'}")
    log = {"executed_at": dt.datetime.now().astimezone().isoformat(), "plan": str(plan_file), "apply": args.apply,
           "homebrew_items": [app["name"] for app in brew_apps], "manual_items": [app["name"] for app in manual_apps],
           "measurements": measurements}
    path = write_record("install", log)
    print(f"Wrote {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(required=True)
    scan_parser = sub.add_parser("scan", help="Inventory Applications folders")
    scan_parser.set_defaults(func=scan)
    plan_parser = sub.add_parser("plan", help="Compare catalog with this Mac")
    plan_parser.add_argument("--profile", choices=["auto", "portable", "expanded"], default="auto")
    plan_parser.set_defaults(func=plan)
    install_parser = sub.add_parser("install", help="Install Homebrew-cask items from a saved plan")
    install_parser.add_argument("plan", help="Path to a generated plan JSON")
    install_parser.add_argument("--only", action="append", help="Exact app name; required and limited to two values")
    install_parser.add_argument("--apply", action="store_true", help="Make changes; omit for dry run")
    install_parser.set_defaults(func=install)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
