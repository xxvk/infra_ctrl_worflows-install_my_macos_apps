#!/usr/bin/env python3
"""Validate and resolve the localized, accessible macomrade message catalogs."""

from __future__ import annotations

import argparse
import json
import os
import string
from pathlib import Path
from typing import Any

from schema_contract import SchemaContractError, load_and_validate


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "settings" / "localization.json"
LOCALE_DIR = ROOT / "locales"
LOCALES = ("en", "ja", "zh-Hans")


class LocalizationError(RuntimeError):
    """Raised when locale catalogs cannot safely be used."""


def load_policy(path: Path = POLICY) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocalizationError(f"cannot read localization policy: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise LocalizationError("localization policy schema_version must be 1")
    if value.get("kind") != "macomrade_localization_policy":
        raise LocalizationError("localization policy kind is invalid")
    if value.get("supported_locales") != ["zh-Hans", "ja", "en"]:
        raise LocalizationError("supported_locales must be zh-Hans, ja, en")
    return value


def load_catalogs(locale_dir: Path = LOCALE_DIR) -> dict[str, dict[str, Any]]:
    result = {}
    for locale_name in LOCALES:
        path = locale_dir / f"messages.{locale_name}.json"
        try:
            value = load_and_validate(path, "localization-catalog")
        except SchemaContractError as exc:
            raise LocalizationError(str(exc)) from exc
        if value.get("locale") != locale_name:
            raise LocalizationError(f"locale catalog name mismatch: {path.name}")
        result[locale_name] = value
    return result


def _placeholders(template: str) -> set[str]:
    names = set()
    for _literal, field_name, _format_spec, _conversion in string.Formatter().parse(template):
        if field_name:
            names.add(field_name.split(".", 1)[0].split("[", 1)[0])
    return names


def validate_catalogs(catalogs: dict[str, dict[str, Any]]) -> None:
    expected_locales = set(LOCALES)
    if set(catalogs) != expected_locales:
        raise LocalizationError("locale catalog set is incomplete")
    baseline = catalogs["en"].get("messages")
    if not isinstance(baseline, dict) or not baseline:
        raise LocalizationError("English message catalog is empty")
    baseline_keys = set(baseline)
    for locale_name in LOCALES:
        messages = catalogs[locale_name].get("messages")
        if not isinstance(messages, dict):
            raise LocalizationError(f"{locale_name} messages must be an object")
        if set(messages) != baseline_keys:
            raise LocalizationError(f"message keys differ for {locale_name}")
        for key in sorted(baseline_keys):
            if not isinstance(messages[key], str) or not messages[key]:
                raise LocalizationError(f"{locale_name} message is empty: {key}")
            if _placeholders(messages[key]) != _placeholders(baseline[key]):
                raise LocalizationError(
                    f"placeholder set differs for {locale_name}: {key}"
                )


def validate() -> dict[str, Any]:
    try:
        policy = load_policy()
        catalogs = load_catalogs()
        validate_catalogs(catalogs)
    except LocalizationError as exc:
        return {"schema_version": 1, "status": "failed", "errors": [str(exc)]}
    return {
        "schema_version": 1,
        "status": "passed",
        "locales": list(LOCALES),
        "message_count": len(catalogs["en"]["messages"]),
        "accessibility": policy["accessibility"],
        "errors": [],
    }


def resolve_locale(requested: str | None = None) -> str:
    if requested and requested != "system":
        if requested not in LOCALES:
            raise LocalizationError(f"unsupported locale: {requested}")
        return requested
    value = os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or ""
    lowered = value.replace("_", "-").lower()
    if lowered.startswith("zh"):
        return "zh-Hans"
    if lowered.startswith("ja"):
        return "ja"
    return "en"


def message(message_id: str, locale_name: str | None = None, **parameters: Any) -> str:
    catalogs = load_catalogs()
    validate_catalogs(catalogs)
    locale_name = resolve_locale(locale_name)
    template = catalogs[locale_name]["messages"].get(message_id)
    if template is None:
        raise LocalizationError(f"unknown message id: {message_id}")
    try:
        return template.format(**parameters)
    except KeyError as exc:
        raise LocalizationError(f"missing message parameter for {message_id}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate locale parity and accessibility policy")
    message_parser = subparsers.add_parser("message", help="render one declared message")
    message_parser.add_argument("message_id")
    message_parser.add_argument("--lang", default="system")
    message_parser.add_argument("--roles")
    args = parser.parse_args()
    if args.command == "validate":
        result = validate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1
    try:
        parameters = {"roles": args.roles} if args.roles is not None else {}
        print(message(args.message_id, args.lang, **parameters))
        return 0
    except LocalizationError as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
