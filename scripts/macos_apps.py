#!/usr/bin/env python3
# Mutation action ID: apps.install
"""Create and apply auditable, capacity-aware macOS app plans."""
import argparse
import datetime as dt
import json
import os
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from config_layers import load_app_catalog
import machine_roles
import pnpm_global
from schema_contract import SchemaContractError, load_and_validate
from state_paths import add_state_dir_argument, resolve_state_dir
from supply_chain import provenance_for

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references" / "mac-app-catalog.json"
STATE = resolve_state_dir()
APP_DIRS = [
    Path("/Applications"),
    Path.home() / "Applications",
    Path.home() / "Applications" / "WebCatalog Apps",
    Path("/System/Applications"),
    Path.home() / "Library/Containers/io.playcover.PlayCover/Applications",
]


def stamp():
    return dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def write_record(prefix, value):
    STATE.mkdir(parents=True, exist_ok=True)
    path = STATE / f"{prefix}-{stamp()}.json"
    if isinstance(value, dict) and "schema_version" not in value:
        value = {"schema_version": 1, **value}
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return path


def update_guide_measurement(app, measurement):
    """Keep measurements in the ignored install state record, never in guides."""
    return


def catalog():
    return load_app_catalog(CATALOG)


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
    if app.get("npm_package"):
        return "npm_global"
    if app.get("runtime_manager"):
        return "version_manager_runtime"
    if app.get("system_app"):
        return "system"
    if app.get("official_url"):
        return "official_web"
    return "unknown"


def version_key(value):
    """Compare dotted app versions without treating a missing suffix as text."""
    if not value:
        return ()
    return tuple(int(part) if part.isdigit() else 0 for part in str(value).split("."))


def version_below(actual, minimum):
    if not actual or not minimum:
        return False
    left, right = version_key(actual), version_key(minimum)
    width = max(len(left), len(right))
    return left + (0,) * (width - len(left)) < right + (0,) * (width - len(right))


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
    # Tapped casks are cataloged as ``tap/name/cask`` for installation, while
    # `brew list --cask` reports only the final cask token.
    cask_tokens = {str(token).casefold(), str(token).rsplit("/", 1)[-1].casefold()} if token else set()
    brew_match = bool(cask_tokens & brew_casks)
    package_receipt = catalog_app.get("package_receipt")
    pkg_match = False
    if package_receipt:
        pkg_match = subprocess.run(
            ["pkgutil", "--pkg-info", package_receipt],
            capture_output=True,
            text=True,
            check=False,
        ).returncode == 0
    detected = []
    if catalog_app.get("delivery_method") == "webcatalog-wrapper" and "/WebCatalog Apps/" in path:
        detected.append("webcatalog")
    if catalog_app.get("delivery_method") == "playcover-ipa" and "io.playcover.PlayCover/Applications/" in path:
        detected.append("playcover")
    if receipt:
        detected.append("app_store")
    # A vendor-published bundle identifier is portable evidence for a website
    # build when no App Store receipt is present. It does not override a receipt.
    website_ids = {str(value).casefold() for value in catalog_app.get("bundle_identifiers", [])}
    if (expected_source(catalog_app) == "official_web" and not receipt and
            (installed_item.get("bundle_identifier") or "").casefold() in website_ids):
        detected.append("official_web")
    if brew_match:
        detected.append("homebrew")
    if pkg_match:
        detected.append("package_receipt")
    if catalog_app.get("system_app") and path.startswith("/System/Applications/"):
        detected.append("system")
    if not detected:
        detected.append("manual_or_unknown")
    expected = expected_source(catalog_app)
    allowed_sources = catalog_app.get("allowed_sources")
    source = detected[0]
    if allowed_sources:
        match = source in allowed_sources
    elif expected in {"app_store", "homebrew", "system"}:
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
        "allowed_sources": allowed_sources,
        "detected": source,
        "detected_sources": detected,
        "match": match,
        "evidence": {"path": path, "app_store_receipt": receipt, "homebrew_cask": token if brew_match else None,
                     "package_receipt": package_receipt if pkg_match else None},
    }


def installed_apps(data=None):
    data = data or catalog()
    by_name = {}
    by_bundle = {}
    for app in data["apps"]:
        for name in [app["name"], *app.get("aliases", [])]:
            by_name[name.casefold()] = app
        for identifier in app.get("bundle_identifiers", []):
            by_bundle[str(identifier).casefold()] = app
    brew_casks = installed_brew_casks()
    found = []
    for directory in APP_DIRS:
        if not directory.is_dir():
            continue
        for app in directory.glob("*.app"):
            info = app / "Contents" / "Info.plist"
            if not info.is_file():
                info = app / "Info.plist"
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
            entry = by_name.get(name.casefold()) or by_bundle.get((bundle_identifier or "").casefold())
            if entry:
                item["catalog_name"] = entry["name"]
                if entry.get("allow_multiple_bundles"):
                    item["allow_multiple_bundles"] = True
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


def source_mismatches(applications):
    """Return true mismatches while tolerating duplicate bundles.

    If an expected-source copy exists alongside an older/manual copy, report
    the duplicate separately rather than treating the catalog item as wholly
    misinstalled.
    """
    grouped = {}
    for item in applications:
        key = item.get("catalog_name") or item.get("name")
        grouped.setdefault(key.casefold(), []).append(item)
    mismatches = []
    for items in grouped.values():
        has_match = any(item.get("source", {}).get("match") is True for item in items)
        for item in items:
            if item.get("source", {}).get("match") is False and not has_match:
                mismatches.append(item)
    return mismatches


def duplicate_apps(applications):
    grouped = {}
    for item in applications:
        key = item.get("catalog_name")
        if item.get("allow_multiple_bundles"):
            continue
        if key:
            grouped.setdefault(key.casefold(), []).append(item)
    return [items for items in grouped.values() if len(items) > 1]


def npm_package_present(app):
    """Require the exact npm package version in its declared fnm runtime."""
    if app.get("npm_runtime_manager") != "fnm" or not shutil.which("fnm"):
        return False
    runtime = str(app.get("npm_runtime_version", ""))
    expected = str(app.get("npm_version", ""))
    if not runtime or not expected:
        return False
    if app.get("npm_install_client", "npm") == "pnpm":
        return pnpm_global.package_present(runtime, app["npm_package"], expected)
    result = subprocess.run(
        [
            "fnm", "exec", f"--using={runtime}", "npm", "list", "--global",
            "--depth=0", "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    try:
        observed = json.loads(result.stdout).get("dependencies", {}).get(app["npm_package"], {})
    except json.JSONDecodeError:
        return False
    return observed.get("version") == expected


def app_present(app, installed_names):
    if app.get("npm_package"):
        return npm_package_present(app)
    extension_id = app.get("chrome_extension_id")
    if extension_id:
        chrome_root = Path.home() / "Library/Application Support/Google/Chrome"
        if chrome_root.is_dir():
            for profile in [chrome_root / "Default", *sorted(chrome_root.glob("Profile *"))]:
                if not profile.is_dir():
                    continue
                if (profile / "Extensions" / extension_id).is_dir():
                    return True
                for filename in ("Preferences", "Secure Preferences"):
                    preferences = profile / filename
                    if preferences.is_file():
                        try:
                            if extension_id in preferences.read_text(errors="ignore"):
                                return True
                        except OSError:
                            pass
    if app.get("runtime_manager") == "fnm":
        version = str(app.get("runtime_version", ""))
        command = str(app.get("runtime_command", "node"))
        if not version or not shutil.which("fnm"):
            return False
        result = subprocess.run(
            ["fnm", "exec", f"--using={version}", command, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    command = app.get("check_command")
    if command:
        if str(command).startswith("test "):
            return subprocess.run(command, shell=True, check=False).returncode == 0
        # Catalog checks may include a version probe (for example
        # ``java -version``). Presence is determined by the executable token;
        # arguments are for the component's verification step, not PATH lookup.
        try:
            executable = shlex.split(str(command))[0]
        except (ValueError, IndexError):
            executable = str(command).split()[0] if str(command).split() else ""
        return bool(executable and shutil.which(executable))
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
        "schema_version": 1,
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "computer_name": os.uname().nodename,
        "macos_version": subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True).stdout.strip(),
        "storage_total_gb": round(storage_gb(), 1),
        "applications": applications,
    }
    path = write_record("scan", result)
    print(f"Wrote {path}")
    print(f"Found {len(result['applications'])} apps; storage: {result['storage_total_gb']} GB")
    mismatches = source_mismatches(applications)
    if mismatches:
        print(f"Source mismatches requiring review: {len(mismatches)}")
        for item in mismatches:
            source = item["source"]
            print(f"- {item['name']}: expected {source['expected']}, detected {source['detected']}")
    duplicates = duplicate_apps(applications)
    if duplicates:
        print(f"Duplicate catalog app bundles requiring review: {len(duplicates)}")
        for items in duplicates:
            print("- " + (items[0].get("catalog_name") or items[0]["name"]) + ": " + ", ".join(item["path"] for item in items))


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
    requested_roles = getattr(args, "roles", None) or "auto"
    try:
        role_selection = machine_roles.resolve(
            machine_roles.load_roles(),
            data,
            [item for item in requested_roles.split(",") if item],
            storage_gb=storage_gb(),
            include_apps=getattr(args, "include_app", []),
            exclude_apps=getattr(args, "exclude_app", []),
        )
    except machine_roles.MachineRoleError as exc:
        raise SystemExit(f"Machine-role selection failed: {exc}") from exc
    selected_names = set(role_selection["selected_apps"])
    selected = [
        app for app in data["apps"]
        if app["name"] in selected_names
        and app.get("lifecycle_status") != "retired"
        and not (app["tier"] == "heavy" and profile == "portable")
    ]
    missing = [app for app in selected if not app_present(app, installed_names)]
    mismatches = []
    for item in source_mismatches(installed):
        mismatches.append({"app": item["name"], "path": item["path"], "source": item["source"]})
    unlisted = [
        {"app": item["name"], "path": item["path"], "bundle_identifier": item.get("bundle_identifier")}
        for item in installed
        if not item.get("catalog_name")
        and not str(item.get("bundle_identifier") or "").casefold().startswith("com.apple.")
    ]
    version_issues = []
    for app in selected:
        minimum = app.get("minimum_version")
        if not minimum:
            continue
        names = {name.casefold() for name in [app["name"], *app.get("aliases", [])]}
        installed_item = next((item for item in installed if item["name"].casefold() in names), None)
        if installed_item and version_below(installed_item.get("version"), minimum):
            version_issues.append({
                "app": app["name"],
                "installed_version": installed_item.get("version"),
                "minimum_version": minimum,
                "path": installed_item["path"],
            })
    follow_up = [{"app": app["name"], "tasks": app.get("follow_up", [])} for app in missing if app.get("follow_up")]
    result = {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "profile": profile,
        "role_selection": role_selection,
        "storage_total_gb": round(storage_gb(), 1),
        "catalog": str(CATALOG.relative_to(ROOT)),
        "installed_count": len(installed),
        "selected_count": len(selected),
        "missing": missing,
        "source_mismatches": mismatches,
        "unlisted_apps": unlisted,
        "version_issues": version_issues,
        "account_hints": [{"app": app["name"], "account": app["preferred_account"],
                           "verification": app.get("account_verification", "manual")}
                          for app in selected if app.get("preferred_account")],
        "version_constraints": [{"app": app["name"], "minimum_version": app["minimum_version"]}
                                for app in selected if app.get("minimum_version")],
        "estimated_download_gb": round(sum(app.get("size_gb", 0) for app in missing), 1),
        "follow_up": follow_up,
        "completion_notes": []
    }
    path = write_record("plan", result)
    print(f"Wrote {path}")
    print(f"Profile: {profile}; missing: {len(missing)}; estimated footprint: {result['estimated_download_gb']} GB")
    if role_selection:
        print("Roles: " + ", ".join(role_selection["roles"]))
    for app in missing:
        if app.get("brew_cask"):
            delivery = f"brew install --cask {app['brew_cask']}"
        elif app.get("brew_formula"):
            tap = f" (after brew tap {app['brew_tap']})" if app.get('brew_tap') else ""
            delivery = f"brew install {app['brew_formula']}{tap}"
        elif app.get("npm_package"):
            delivery = shlex.join(install_commands(app)[0])
        elif app.get("runtime_manager") == "fnm":
            delivery = f"fnm install {app['runtime_version']} && fnm default {app['runtime_version']}"
        else:
            delivery = app.get("app_store_url") or app.get("official_url", "no source recorded")
        print(f"- {app['name']}: {delivery}")
    if mismatches:
        print("Source mismatches (review and reinstall from the expected source):")
        for item in mismatches:
            source = item["source"]
            print(f"- {item['app']}: expected {source['expected']}, detected {source['detected']} ({item['path']})")
    if unlisted:
        print("Unlisted installed apps (review for removal or catalog entry):")
        for item in unlisted:
            print(f"- {item['app']}: {item['path']}")
    duplicates = duplicate_apps(installed)
    if duplicates:
        print("Duplicate catalog app bundles (keep the preferred-source copy):")
        for items in duplicates:
            print("- " + (items[0].get("catalog_name") or items[0]["name"]) + ": " + ", ".join(item["path"] for item in items))
    if version_issues:
        print("Version constraints requiring review:")
        for item in version_issues:
            print(f"- {item['app']}: installed {item['installed_version']}, minimum {item['minimum_version']} ({item['path']})")
    for hint in result["account_hints"]:
        print(f"Login reminder - {hint['app']}: use {hint['account']}; do not automate login")


def run(command, apply):
    print("+", " ".join(command))
    if apply:
        env = None
        if len(command) > 3 and command[:2] == ["fnm", "exec"] and command[3] == "pnpm":
            env = pnpm_global.runtime_environment(command[2].removeprefix("--using="))
        subprocess.run(command, check=True, env=env)


def install_commands(app, *, force=False):
    """Render deterministic external commands for one catalog app."""
    commands = []
    if app.get("runtime_manager") == "fnm":
        version = str(app.get("runtime_version", ""))
        if not version:
            raise ValueError(f"{app['name']}: runtime_version must be pinned")
        return [["fnm", "install", version], ["fnm", "default", version]]
    if app.get("brew_tap"):
        commands.append([
            "env",
            "HOMEBREW_NO_AUTO_UPDATE=1",
            "HOMEBREW_NO_INSTALL_UPGRADE=1",
            "brew",
            "tap",
            app["brew_tap"],
        ])
    if app.get("brew_trust_cask"):
        commands.append([
            "env",
            "HOMEBREW_NO_AUTO_UPDATE=1",
            "brew",
            "trust",
            "--cask",
            app["brew_trust_cask"],
        ])
    if app.get("brew_cask") or app.get("brew_formula"):
        command = [
            "env",
            "HOMEBREW_NO_AUTO_UPDATE=1",
            "HOMEBREW_NO_INSTALL_UPGRADE=1",
            "brew",
            "install",
        ]
        if force:
            command.append("--force")
        if app.get("brew_cask"):
            command.extend(["--cask", app["brew_cask"]])
        else:
            command.append(app["brew_formula"])
        commands.append(command)
    elif app.get("npm_package"):
        version = app.get("npm_version")
        if not version:
            raise ValueError(f"{app['name']}: npm_version must be pinned")
        manager = app.get("npm_runtime_manager")
        runtime = str(app.get("npm_runtime_version", ""))
        if manager != "fnm":
            raise ValueError(f"{app['name']}: npm_runtime_manager must be fnm")
        if not runtime:
            raise ValueError(f"{app['name']}: npm_runtime_version must be pinned")
        client = app.get("npm_install_client", "npm")
        if client == "pnpm":
            policy = app.get("npm_lifecycle_policy")
            allowed = app.get("npm_allowed_builds", [])
            command = ["fnm", "exec", f"--using={runtime}", "pnpm", "add", "--global"]
            if policy == "ignore_all" and not allowed:
                command.append("--ignore-scripts")
            elif policy == "allow_listed" and allowed:
                command.extend(f"--allow-build={name}" for name in allowed)
            else:
                raise ValueError(f"{app['name']}: invalid pnpm lifecycle policy")
            command.append(f"{app['npm_package']}@{version}")
            commands.append(command)
            return commands
        if client != "npm":
            raise ValueError(f"{app['name']}: unsupported npm_install_client")
        commands.append([
            "fnm", "exec", f"--using={runtime}", "npm", "install", "--global",
            f"{app['npm_package']}@{version}",
        ])
    return commands


def verify_tap_source(app, *, runner=subprocess.run):
    """Stop when a third-party tap differs from the reviewed remote or commit."""
    tap = app.get("brew_tap")
    expected_remote = app.get("brew_tap_repository")
    expected_revision = app.get("brew_tap_revision")
    if not tap or not expected_remote or not expected_revision:
        return None
    repository = runner(
        ["brew", "--repository", tap],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    remote = runner(
        ["git", "-C", repository, "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    revision = runner(
        ["git", "-C", repository, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if remote != expected_remote or revision != expected_revision:
        raise RuntimeError(
            f"{app['name']}: third-party tap drift; expected "
            f"{expected_remote}@{expected_revision}, observed {remote}@{revision}"
        )
    return {
        "tap": tap,
        "repository": remote,
        "revision": revision,
        "status": "verified",
    }


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
    if app.get("npm_package"):
        runtime = str(app.get("npm_runtime_version", ""))
        if app.get("npm_install_client", "npm") == "pnpm":
            root = pnpm_global.package_root(runtime, app["npm_package"])
            return path_size(root) if root else 0
        result = subprocess.run(
            ["fnm", "exec", f"--using={runtime}", "npm", "root", "-g"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return path_size(Path(result.stdout.strip()) / app["npm_package"])
        return 0
    if app.get("application_path"):
        return path_size(Path(app["application_path"]).expanduser())
    return path_size(Path("/Applications") / f"{app['name']}.app")


def install(args):
    plan_file = Path(args.plan).expanduser().resolve()
    try:
        plan_data = load_and_validate(plan_file, "app-plan")
    except SchemaContractError as exc:
        raise SystemExit(str(exc)) from exc
    # A source correction is an install target too: the app may already exist,
    # but must be replaced/reinstalled from the catalog's preferred source.
    catalog = load_app_catalog(CATALOG)["apps"]
    catalog_by_name = {}
    for app in catalog:
        for label in [app["name"], *app.get("aliases", [])]:
            catalog_by_name[label.casefold()] = app
    mismatch_names = {item["app"].casefold() for item in plan_data.get("source_mismatches", [])}
    selected = list(plan_data["missing"])
    for name in mismatch_names:
        app = catalog_by_name.get(name)
        if app and (app.get("brew_cask") or app.get("brew_formula")):
            if all(existing["name"].casefold() != name for existing in selected):
                selected.append(app)
    if not args.only:
        raise SystemExit("Select one to five apps with --only; do not install an entire plan at once.")
    if len(args.only) > 5:
        raise SystemExit("A run may contain at most five --only app names.")
    wanted = {name.casefold() for name in args.only}
    def matches_wanted(app):
        labels = {app["name"].casefold(), *(alias.casefold() for alias in app.get("aliases", []))}
        return bool(labels & wanted)

    selected = [app for app in selected if matches_wanted(app)]
    selected_labels = {
        label.casefold()
        for app in selected
        for label in [app["name"], *app.get("aliases", [])]
    }
    absent = wanted - selected_labels
    if absent:
        raise SystemExit("App not found in this plan: " + ", ".join(sorted(absent)))
    brew_apps = [app for app in selected if app.get("brew_cask") or app.get("brew_formula")]
    runtime_apps = [app for app in selected if app.get("runtime_manager")]
    npm_apps = [app for app in selected if app.get("npm_package")]
    manual_apps = [app for app in selected if not (app.get("brew_cask") or app.get("brew_formula") or app.get("npm_package") or app.get("runtime_manager"))]
    if not args.apply:
        print("DRY RUN — nothing will be installed. Re-run with --apply after review.")
    if brew_apps and not shutil.which("brew"):
        raise SystemExit(
            "Homebrew is required for this plan. Automatic network-to-shell "
            "bootstrap is disabled; install Homebrew through a separately "
            "reviewed bootstrap procedure, then rerun."
        )
    measurements = []
    for app in brew_apps:
        # Prevent an app install from silently upgrading unrelated installed
        # formulae/casks. Explicit dependency upgrades require confirmation.
        commands = install_commands(
            app,
            force=app["name"].casefold() in mismatch_names,
        )
        cache_path = brew_cache_path(app) if args.apply else None
        before_download = path_size(cache_path) if cache_path else 0
        started = dt.datetime.now().astimezone().isoformat()
        tap_verification = None
        for command in commands:
            run(command, args.apply)
            if args.apply and command[-2:] == ["tap", app.get("brew_tap")]:
                tap_verification = verify_tap_source(app)
        after_download = path_size(cache_path) if cache_path else 0
        measurement = {
            "app": app["name"],
            "started_at": started,
            "finished_at": dt.datetime.now().astimezone().isoformat(),
            "download_bytes": max(after_download - before_download, 0) or after_download,
            "installed_bytes": installed_size(app) if args.apply else 0,
            "status": "installed" if args.apply else "dry_run",
            "provenance": {
                **provenance_for(app),
                "tap_verification": tap_verification,
            },
        }
        measurements.append(measurement)
        update_guide_measurement(app, measurement)
    for app in runtime_apps:
        if args.apply and not shutil.which(app["runtime_manager"]):
            raise SystemExit(
                f"{app['runtime_manager']} is required before installing {app['name']}"
            )
        started = dt.datetime.now().astimezone().isoformat()
        for command in install_commands(app):
            run(command, args.apply)
        measurements.append({
            "app": app["name"],
            "started_at": started,
            "finished_at": dt.datetime.now().astimezone().isoformat(),
            "download_bytes": None,
            "installed_bytes": 0,
            "status": "installed" if args.apply else "dry_run",
            "provenance": provenance_for(app),
        })
    for app in npm_apps:
        commands = install_commands(app)
        started = dt.datetime.now().astimezone().isoformat()
        for command in commands:
            run(command, args.apply)
        measurement = {
            "app": app["name"],
            "started_at": started,
            "finished_at": dt.datetime.now().astimezone().isoformat(),
            "download_bytes": None,
            "installed_bytes": installed_size(app) if args.apply else 0,
            "status": "installed" if args.apply else "dry_run",
            "provenance": provenance_for(app),
        }
        measurements.append(measurement)
        update_guide_measurement(app, measurement)
    if manual_apps:
        print("\nManual/App Store items (not downloaded automatically):")
        for app in manual_apps:
            print(f"- {app['name']}: {app.get('app_store_url') or app.get('official_url') or 'source missing'}")
    log = {"action_id": "apps.install",
           "executed_at": dt.datetime.now().astimezone().isoformat(), "plan": str(plan_file), "apply": args.apply,
           "homebrew_items": [app["name"] for app in brew_apps],
           "runtime_items": [app["name"] for app in runtime_apps],
           "npm_items": [app["name"] for app in npm_apps],
           "manual_items": [app["name"] for app in manual_apps],
           "measurements": measurements}
    path = write_record("install", log)
    print(f"Wrote {path}")


def main():
    global STATE
    parser = argparse.ArgumentParser(description=__doc__)
    add_state_dir_argument(parser)
    sub = parser.add_subparsers(required=True)
    scan_parser = sub.add_parser("scan", help="Inventory Applications folders")
    scan_parser.set_defaults(func=scan)
    plan_parser = sub.add_parser("plan", help="Compare catalog with this Mac")
    plan_parser.add_argument("--profile", choices=["auto", "portable", "expanded"], default="auto")
    plan_parser.add_argument(
        "--roles",
        default="auto",
        help="Comma-separated composable roles; defaults to auto for base plus compact/expanded capacity role.",
    )
    plan_parser.add_argument("--include-app", action="append", default=[], help="Explicitly include one catalog app in this plan")
    plan_parser.add_argument("--exclude-app", action="append", default=[], help="Explicitly exclude one catalog app from this plan")
    plan_parser.set_defaults(func=plan)
    install_parser = sub.add_parser("install", help="Install Homebrew-cask items from a saved plan")
    install_parser.add_argument("plan", help="Path to a generated plan JSON")
    install_parser.add_argument("--only", action="append", help="Exact app name; required and limited to two values")
    install_parser.add_argument("--apply", action="store_true", help="Make changes; omit for dry run")
    install_parser.set_defaults(func=install)
    args = parser.parse_args()
    STATE = resolve_state_dir(args.state_dir)
    args.func(args)


if __name__ == "__main__":
    main()
