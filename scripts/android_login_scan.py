#!/usr/bin/env python3
"""Recurring Android login-state scan and status update.

Implements the documented method in
references/android-application-workflow.md#login-state-scan
(know-how, verified 2026-08-21): resolve each app's launcher activity,
force-stop, go home, start it, wait, and read the foreground activity from
`topResumedActivity`. An activity name matching the login/onboarding signal
list means the app is not logged in; a bare MainActivity/HomeActivity is
NOT proof of login by itself.

This script is the reusable replacement for the ad-hoc adb/python one-liners
used in the first two manual passes (2026-08-21/22). Each `scan` run:

1. Diffs `adb shell pm list packages -3` against the previous
   Private/android-login-scan-final-*.json to find newly installed packages.
2. Classifies new (or --recheck) packages with the documented method.
3. Writes a new dated Private/android-login-scan-final-<date>.json
   (cumulative -- carries forward every previously known package).
4. Back-fills references/android-app-catalog.json's login_required /
   login_status fields for matched packages.
5. Regenerates Private/android-inventory.json's login_tracking section.
6. Regenerates a dated Private/android-login-checklist-<date>.json grouped
   by catalog category, using the canonical status vocabulary only:
   needs_login / logged_in / google_system / no_login.

Never touches credentials, tokens, or account data. Never automates login;
`--confirm-login` only records that the *user* signed in manually.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "Private"
CATALOG_PATH = ROOT / "references/android-app-catalog.json"
IGNORE_LIST_PATH = ROOT / "references/ignore-list.json"
EVIDENCE_PATH = PRIVATE / "login-evidence.json"
INVENTORY_PATH = PRIVATE / "android-inventory.json"

CANONICAL_STATUSES = {"needs_login", "logged_in", "google_system", "no_login"}

# Packages/prefixes that are system/infra plumbing, not separately
# login-tracked apps. Google apps follow the device's system account
# (documented rule); FeliCa/Osaifu-Keitai packages are payment-rail
# infrastructure, not user-facing login surfaces.
SYSTEM_PACKAGE_PREFIXES = (
    "com.google.android.",
    "com.felicanetworks.",
)
SYSTEM_PACKAGE_EXACT = {
    "com.google.android.apps.docs.editors.docs",  # still matched by prefix above; kept for clarity
}

# Signal list from the documented method: an activity class name containing
# any of these (case-insensitive) means the app is on a login/onboarding
# screen, i.e. not logged in.
LOGIN_SIGNAL_RE = re.compile(
    r"login|signin|auth|welcome|onboard|loggedout|firsttimeuse|registration|eula|signup|prelogin",
    re.IGNORECASE,
)

SAMPLE_WAITS = (7, 10, 12)  # seconds, per the documented 3-sample method


def sh(args: list[str], timeout: int = 30) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False, timeout=timeout)
    return (result.stdout or "").strip()


def adb(args: list[str], timeout: int = 30) -> str:
    return sh(["adb"] + args, timeout=timeout)


def ensure_device() -> str:
    out = sh(["adb", "devices"])
    lines = [line for line in out.splitlines()[1:] if line.strip().endswith("\tdevice")]
    if not lines:
        recovery = ROOT / "scripts/adb-pixel.sh"
        if recovery.is_file():
            subprocess.run(["bash", str(recovery), "--once"], check=False, timeout=60)
            out = sh(["adb", "devices"])
            lines = [line for line in out.splitlines()[1:] if line.strip().endswith("\tdevice")]
    if not lines:
        print("No adb device connected (adb devices returned none). Aborting.", file=sys.stderr)
        raise SystemExit(1)
    serial = lines[0].split()[0]
    return serial


TOP_RE = re.compile(r"topResumedActivity=ActivityRecord\{\S+\s+u\d+\s+(\S+)")


def probe_foreground(pkg: str, wait_s: int = 13) -> str:
    """Bring `pkg` to the front and report its foreground activity.

    Deliberately does NOT force-stop: a warm launch is what a logged-in app
    actually looks like day to day. Cold starts push some apps (notably JP
    brokerages such as iGrow) back through a re-authentication flow and make a
    signed-in account look signed-out. Uses the LAUNCHER intent because
    `am start -n <component>` fails on activity-alias entry points.
    See references/android-application-workflow.md#login-state-scan.
    """
    adb(["shell", "input", "keyevent", "KEYCODE_HOME"])
    time.sleep(1)
    adb(["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])
    time.sleep(wait_s)
    matches = TOP_RE.findall(adb(["shell", "dumpsys", "activity", "activities"]))
    own = [m for m in matches if m.startswith(pkg + "/")]
    return own[0] if own else (matches[0] if matches else "")


def load_evidence() -> dict[str, dict]:
    """Per-package login evidence (Private/, gitignored -- holds account handles).

    Each value: {"evidence": "<UI marker that proves a signed-in session>",
                 "front_when_logged_in": "<pkg>/<activity>", "observed_at": "<date>"}

    This is the migration baseline. Activity names alone are NOT a reliable
    signal in either direction -- IKEA sits on `WelcomeActivity` while signed
    in, Figma Mirror sits on `MainActivity` while signed out, and Tailscale
    reads "Not connected" (its VPN switch) while the account is fine. The
    `evidence` string is the durable check: it survives activity renames and
    transfers to a new device.
    """
    if not EVIDENCE_PATH.exists():
        return {}
    return json.loads(EVIDENCE_PATH.read_text()).get("packages", {})


def save_evidence(store: dict[str, dict]) -> None:
    EVIDENCE_PATH.write_text(json.dumps({
        "schema_version": 1,
        "kind": "android_login_evidence",
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "purpose": "Per-app proof-of-login baseline for device migration; see load_evidence().",
        "packages": store,
    }, ensure_ascii=False, indent=2) + "\n")


def ignored_packages() -> set[str]:
    """Packages the user explicitly excluded (references/ignore-list.json).

    These are dropped from the scan and from every generated artifact: the
    app may still be installed, but it is not something we track a login
    state for. Kept in ignore-list.json rather than deleted so the exclusion
    stays auditable and reversible.
    """
    if not IGNORE_LIST_PATH.exists():
        return set()
    data = json.loads(IGNORE_LIST_PATH.read_text())
    return {e["play_store_package"] for e in data.get("entries", []) if e.get("play_store_package")}


def installed_third_party_packages() -> set[str]:
    out = adb(["shell", "pm", "list", "packages", "-3"])
    return {line.split(":", 1)[1].strip() for line in out.splitlines() if line.startswith("package:")}


def latest_scan_file() -> Path | None:
    candidates = sorted(PRIVATE.glob("android-login-scan-final-*.json"))
    return candidates[-1] if candidates else None


def load_latest_scan() -> dict:
    path = latest_scan_file()
    if path is None:
        return {"schema_version": 1, "kind": "android_login_status_scan", "results": []}
    return json.loads(path.read_text())


def is_system_package(pkg: str) -> bool:
    return any(pkg.startswith(prefix) for prefix in SYSTEM_PACKAGE_PREFIXES) or pkg in SYSTEM_PACKAGE_EXACT


def classify_package(pkg: str) -> dict:
    """Apply the documented 3-sample resolve/force-stop/start/read method."""
    entry_out = adb(["shell", "cmd", "package", "resolve-activity", "--brief", pkg])
    entry_lines = [l for l in entry_out.splitlines() if l.strip() and "No activity found" not in l]
    entry = entry_lines[-1].strip() if entry_lines else ""
    if not entry or "/" not in entry:
        return {"package": pkg, "status": "needs_login", "entry": entry, "front": "",
                "note": "resolve-activity returned no usable entry; treated as unresolved, needs manual check"}

    adb(["shell", "am", "force-stop", pkg])
    adb(["shell", "input", "keyevent", "KEYCODE_HOME"])
    time.sleep(1)
    # Launch via the LAUNCHER intent, not `am start -n <component>`.
    # Some apps (e.g. com.nikkei.newspaper) declare a launcher activity that
    # resolve-activity reports but that `am start -n` rejects with
    # "Activity class ... does not exist" -- typically an activity-alias.
    # `monkey` fires the same MAIN/LAUNCHER intent the home screen does, so
    # it succeeds where the explicit component does not. Falling back to
    # `am start -n` keeps the old path for anything monkey cannot launch.
    launch = adb(["shell", "monkey", "-p", pkg, "-c",
                  "android.intent.category.LAUNCHER", "1"])
    if "Events injected: 1" not in launch:
        adb(["shell", "am", "start", "-n", entry])

    # Real output: "topResumedActivity=ActivityRecord{<hash> u0 <pkg>/<activity> t<taskId>}"
    # -- there can be one such line per display, so collect all matches and
    # prefer the one belonging to the target package.
    top_re = re.compile(r"topResumedActivity=ActivityRecord\{\S+\s+u\d+\s+(\S+)")

    fronts = []
    for wait_s in SAMPLE_WAITS:
        time.sleep(wait_s)
        chosen = ""
        # Stacked permission dialogs can require dismissing more than once
        # before the target app's own activity actually gets focus.
        for _dismiss_attempt in range(3):
            top = adb(["shell", "dumpsys", "activity", "activities"])
            matches = top_re.findall(top)
            own = [m for m in matches if m.startswith(pkg + "/")]
            chosen = own[0] if own else (matches[0] if matches else "")
            if own or "permissioncontroller" not in chosen:
                break
            adb(["shell", "input", "keyevent", "KEYCODE_BACK"])
            time.sleep(2)
        if chosen:
            fronts.append(chosen)

    adb(["shell", "input", "keyevent", "KEYCODE_HOME"])

    # Prefer the last sample that actually belongs to the target package.
    own = [f for f in fronts if f.startswith(pkg + "/")]
    front = own[-1] if own else (fronts[-1] if fronts else "")

    if front.startswith(pkg + "/") and LOGIN_SIGNAL_RE.search(front.split("/", 1)[1]):
        status = "needs_login"
        note = f"front={front}"
    elif own:
        # Reached its own MainActivity/HomeActivity -- not proof of login
        # per the documented rule; default to needs_login with a note.
        status = "needs_login"
        note = f"front={front}; MainActivity reached but not proof of login (documented rule)"
    else:
        status = "needs_login"
        note = f"could not confirm own foreground activity (samples={fronts}); needs manual check"

    return {"package": pkg, "status": status, "entry": entry, "front": front, "note": note}


def catalog_lookup() -> dict[str, dict]:
    catalog = json.loads(CATALOG_PATH.read_text())
    apps = catalog["apps"] if isinstance(catalog, dict) else catalog
    lookup = {}

    def walk(obj):
        if isinstance(obj, dict):
            if "play_store_package" in obj:
                lookup[obj["play_store_package"]] = obj
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(apps)
    return lookup


def backfill_catalog(results: list[dict]) -> int:
    catalog = json.loads(CATALOG_PATH.read_text())
    apps = catalog["apps"] if isinstance(catalog, dict) else catalog
    by_pkg = {}

    def walk(obj):
        if isinstance(obj, dict):
            if "play_store_package" in obj:
                by_pkg[obj["play_store_package"]] = obj
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(apps)

    changed = 0
    for r in results:
        app = by_pkg.get(r["package"])
        if not app or r["status"] not in CANONICAL_STATUSES:
            continue
        # Only `login_required` belongs in the public catalog: it is a property
        # of the *app* ("does this need an account at all"), matching
        # account_required in the iOS and macOS catalogs. The per-device answer
        # to "is this user signed in" is personal state and stays in Private/
        # (scan file, inventory login_tracking, login-evidence.json) -- this
        # repository is public.
        new_required = r["status"] not in ("google_system", "no_login")
        if app.get("login_required") != new_required:
            app["login_required"] = new_required
            changed += 1
        if app.pop("login_status", None) is not None:
            changed += 1

    if changed:
        CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    return changed


def update_inventory(results: list[dict], catalog_lookup_map: dict[str, dict]) -> None:
    tracking = {"needs_login": [], "logged_in": [], "google_system": [], "no_login": []}
    for r in results:
        status = r["status"]
        if status not in tracking:
            continue
        info = catalog_lookup_map.get(r["package"], {})
        tracking[status].append({"name": info.get("name", r["package"]), "package": r["package"]})
    for bucket in tracking.values():
        bucket.sort(key=lambda a: a["name"])

    inventory = json.loads(INVENTORY_PATH.read_text()) if INVENTORY_PATH.is_file() else {"schema_version": 1}
    inventory["login_tracking"] = {
        "schema_version": 1,
        "updated_at": dt.datetime.now().astimezone().isoformat(),
        "source": f"{latest_scan_file().name if latest_scan_file() else 'android_login_scan.py'} via scripts/android_login_scan.py",
        "tracking": tracking,
        "summary": {k: len(v) for k, v in tracking.items()},
    }
    INVENTORY_PATH.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")


def write_checklist(results: list[dict], catalog_lookup_map: dict[str, dict], date_tag: str) -> Path:
    needs = [r for r in results if r["status"] == "needs_login"]
    groups: dict[str, list[dict]] = {}
    for r in needs:
        info = catalog_lookup_map.get(r["package"], {})
        category = info.get("category", "Uncategorized")
        groups.setdefault(category, []).append({"name": info.get("name", r["package"]), "package": r["package"]})
    for apps in groups.values():
        apps.sort(key=lambda a: a["name"])
    priority_order = sorted(groups.keys(), key=lambda c: -len(groups[c]))

    checklist = {
        "schema_version": 1,
        "kind": "android_login_checklist",
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "source": f"Private/android-login-scan-final-{date_tag}.json",
        "purpose": f"{len(needs)} apps requiring account login, grouped by category",
        "priority_order": priority_order,
        "groups": groups,
        "total": len(needs),
    }
    path = PRIVATE / f"android-login-checklist-{date_tag}.json"
    path.write_text(json.dumps(checklist, ensure_ascii=False, indent=2) + "\n")
    return path


def cmd_scan(args: argparse.Namespace) -> int:
    ensure_device()
    previous = load_latest_scan()
    by_pkg = {r["package"]: r for r in previous.get("results", [])}

    ignored = ignored_packages()
    installed = installed_third_party_packages() - ignored
    for pkg in ignored & set(by_pkg):
        del by_pkg[pkg]
    known = set(by_pkg)
    new_pkgs = sorted(installed - known)
    recheck_pkgs = set(args.recheck.split(",")) if args.recheck else set()
    if args.recheck_all:
        recheck_pkgs |= installed

    to_scan = sorted(set(new_pkgs) | recheck_pkgs)

    print(f"installed (3rd-party): {len(installed)}; known from previous scan: {len(known)}; "
          f"new: {len(new_pkgs)}; rechecking: {len(recheck_pkgs)}; "
          f"ignored: {len(ignored)}", file=sys.stderr)

    for pkg in to_scan:
        if is_system_package(pkg):
            by_pkg[pkg] = {"package": pkg, "status": "google_system",
                            "entry": "", "front": "", "note": "system/infra package, excluded from login tracking"}
            print(f"  {pkg}: google_system (excluded)", file=sys.stderr)
            continue
        result = classify_package(pkg)
        by_pkg[pkg] = result
        print(f"  {pkg}: {result['status']} ({result['note'][:60]})", file=sys.stderr)

    evidence = load_evidence()

    for raw in args.set_evidence or []:
        pkg, _, text = raw.partition("=")
        pkg, text = pkg.strip(), text.strip()
        if not pkg or not text:
            print(f"  !! --set-evidence needs <pkg>=<text>, got {raw!r}", file=sys.stderr)
            continue
        ev = evidence.setdefault(pkg, {})
        ev["evidence"] = text
        ev["observed_at"] = dt.date.today().isoformat()
        print(f"  {pkg}: evidence recorded", file=sys.stderr)

    for pkg in args.confirm_login.split(",") if args.confirm_login else []:
        pkg = pkg.strip()
        if not pkg:
            continue
        # Probe rather than blanking the record: the foreground activity seen
        # while signed in is half the migration baseline (the other half is
        # the `evidence` string). This previously wrote empty strings and
        # threw that observation away.
        front = "" if args.no_probe else probe_foreground(pkg)
        by_pkg[pkg] = {"package": pkg, "status": "logged_in",
                        "entry": front, "front": front,
                        "note": f"user confirmed: logged in (manual, {dt.date.today().isoformat()})"}
        if front:
            ev = evidence.setdefault(pkg, {})
            ev["front_when_logged_in"] = front
            ev.setdefault("observed_at", dt.date.today().isoformat())
        print(f"  {pkg}: logged_in (user-confirmed, front={front or 'not probed'})", file=sys.stderr)

    save_evidence(evidence)

    for pkg in args.mark_no_login.split(",") if args.mark_no_login else []:
        pkg = pkg.strip()
        if not pkg:
            continue
        by_pkg[pkg] = {"package": pkg, "status": "no_login", "entry": "", "front": "",
                        "note": "manually marked: no login required"}

    for rec in by_pkg.values():
        ev = evidence.get(rec["package"], {})
        if ev.get("evidence"):
            rec["login_evidence"] = ev["evidence"]
        # Back-fill the activity baseline for records written before
        # --confirm-login started probing (they carry empty entry/front).
        if not rec.get("front") and ev.get("front_when_logged_in"):
            rec["front"] = ev["front_when_logged_in"]
            rec["entry"] = ev["front_when_logged_in"]

    results = list(by_pkg.values())
    date_tag = dt.date.today().strftime("%Y%m%d")
    scan_out = {
        "schema_version": 1,
        "kind": "android_login_status_scan",
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "method": "resolve-activity + force-stop/start + topResumedActivity, 3 samples "
                  "(see references/android-application-workflow.md#login-state-scan)",
        "results": results,
        "summary": dict(Counter(r["status"] for r in results)),
    }
    scan_path = PRIVATE / f"android-login-scan-final-{date_tag}.json"
    scan_path.write_text(json.dumps(scan_out, ensure_ascii=False, indent=2) + "\n")

    lookup = catalog_lookup()
    changed = backfill_catalog(results)
    update_inventory(results, lookup)
    checklist_path = write_checklist(results, lookup, date_tag)

    print(json.dumps({
        "scan_file": str(scan_path),
        "checklist_file": str(checklist_path),
        "catalog_entries_updated": changed,
        "inventory_file": str(INVENTORY_PATH),
        "summary": scan_out["summary"],
    }, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Diff installed packages, classify new ones, back-fill catalog/inventory")
    scan.add_argument("--recheck", default="", help="comma-separated packages to re-classify even if already known")
    scan.add_argument("--recheck-all", action="store_true", help="re-classify every installed package (slow)")
    scan.add_argument("--confirm-login", default="", help="comma-separated packages the user manually confirmed logging into")
    scan.add_argument("--mark-no-login", default="", help="comma-separated packages that don't require login")
    scan.add_argument("--set-evidence", action="append", metavar="PKG=TEXT",
                      help="record the on-screen marker that proves a signed-in session, e.g. "
                           "--set-evidence com.reddit.frontpage='\"Signed in as u/...\" toast'. "
                           "Repeatable. Stored in Private/login-evidence.json.")
    scan.add_argument("--no-probe", action="store_true",
                      help="with --confirm-login, skip bringing each app to the front "
                           "(records status without capturing the activity baseline)")
    scan.set_defaults(func=cmd_scan)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
