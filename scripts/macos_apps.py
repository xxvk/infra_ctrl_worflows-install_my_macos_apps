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


def installed_apps():
    found = []
    for directory in APP_DIRS:
        if not directory.is_dir():
            continue
        for app in directory.glob("*.app"):
            info = app / "Contents" / "Info.plist"
            name = app.stem
            version = None
            try:
                with info.open("rb") as f:
                    meta = plistlib.load(f)
                name = meta.get("CFBundleDisplayName") or meta.get("CFBundleName") or name
                version = meta.get("CFBundleShortVersionString")
            # Some third-party bundles contain a malformed Info.plist. Keep the
            # inventory useful by falling back to the bundle filename.
            except Exception:
                pass
            found.append({"name": name, "version": version, "path": str(app)})
    return sorted(found, key=lambda item: item["name"].casefold())


def app_present(app, installed_names):
    command = app.get("check_command")
    if command:
        return shutil.which(command) is not None
    return app["name"].casefold() in installed_names


def storage_gb():
    return shutil.disk_usage("/").total / 1024 ** 3


def choose_profile(requested):
    if requested != "auto":
        return requested
    return "expanded" if storage_gb() >= 512 else "portable"


def scan(_args):
    result = {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "computer_name": os.uname().nodename,
        "macos_version": subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True).stdout.strip(),
        "storage_total_gb": round(storage_gb(), 1),
        "applications": installed_apps(),
    }
    path = write_record("scan", result)
    print(f"Wrote {path}")
    print(f"Found {len(result['applications'])} apps; storage: {result['storage_total_gb']} GB")


def plan(args):
    data = catalog()
    profile = choose_profile(args.profile)
    installed = installed_apps()
    installed_names = {item["name"].casefold() for item in installed}
    selected = []
    for app in data["apps"]:
        if app["tier"] == "heavy" and profile == "portable":
            continue
        selected.append(app)
    missing = [app for app in selected if not app_present(app, installed_names)]
    follow_up = [{"app": app["name"], "tasks": app.get("follow_up", [])} for app in missing if app.get("follow_up")]
    result = {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "profile": profile,
        "storage_total_gb": round(storage_gb(), 1),
        "catalog": str(CATALOG.relative_to(ROOT)),
        "installed_count": len(installed),
        "selected_count": len(selected),
        "missing": missing,
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
