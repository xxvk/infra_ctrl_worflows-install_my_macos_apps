#!/usr/bin/env python3
"""Render safe, localized, accessible TUI and HTML views of audit JSON."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

import localization


ROOT = Path(__file__).resolve().parents[1]

BROWSER_STAGE_BY_KIND = {
    "safari_export_redacted_summary": "scan",
    "browser_review_redacted_summary": "review",
    "browser_lifecycle_redacted_summary": "review",
    "browser_transaction_redacted_summary": "plan",
    "browser_transaction_apply_summary": "apply",
    "browser_transaction_verification_summary": "verify",
    "browser_history_redacted_summary": "history",
    "browser_live_acceptance_summary": "verify",
}
BROWSER_METRICS_BY_KIND = {
    "safari_export_redacted_summary": (
        "bookmark_count",
        "reading_list_count",
    ),
    "browser_review_redacted_summary": (
        "bookmark_count",
        "reading_list_count",
        "normalization_proposal_count",
        "normalization_blocked_count",
        "duplicate_group_count",
        "duplicate_item_count",
    ),
    "browser_lifecycle_redacted_summary": (
        "queued_count",
        "suppressed_count",
    ),
    "browser_transaction_redacted_summary": (
        "operation_count",
        "backup_verified",
        "exact_rollback_supported",
        "apply_interface",
    ),
    "browser_transaction_apply_summary": (
        "manual_handoff_only",
    ),
    "browser_transaction_verification_summary": (
        "verified_operation_count",
        "failed_operation_count",
        "apply_interface",
    ),
    "browser_history_redacted_summary": (
        "custom_classification_count",
        "decision_count",
        "active_decision_count",
    ),
    "browser_live_acceptance_summary": (
        "bookmark_count",
        "reading_list_count",
        "queued_count",
        "suppressed_count",
        "planned_operation_count",
        "verified_operation_count",
        "failed_operation_count",
    ),
}
BROWSER_STATUSES = {"passed", "partial", "preview", "written", "unchanged", "blocked", "failed"}


def _locale(value: str) -> str:
    return localization.resolve_locale(value)


def _safe_name(row: Any, key: str) -> str:
    if isinstance(row, dict) and isinstance(row.get(key), str):
        return row[key]
    return "unknown"


def _summarize_browser(report: dict[str, Any]) -> dict[str, Any]:
    source_kind = report["kind"]
    if report.get("schema_version") != 1:
        raise ValueError("browser report schema_version must be 1")
    content_flag = (
        report.get("item_content_emitted")
        if source_kind == "safari_export_redacted_summary"
        else report.get("private_content_emitted")
    )
    if content_flag is not False or report.get("execution_authorized") is not False:
        raise ValueError("browser report input is not explicitly redacted")
    if source_kind == "safari_export_redacted_summary" and (
        report.get("input_path_emitted") is not False
        or report.get("artifact_ref_emitted") is not False
    ):
        raise ValueError("browser report input is not explicitly redacted")
    metrics: dict[str, int | bool | str] = {}
    source_metrics = (
        report.get("counts", {})
        if source_kind == "browser_live_acceptance_summary"
        else report
    )
    for field in BROWSER_METRICS_BY_KIND[source_kind]:
        value = source_metrics.get(field)
        if isinstance(value, bool):
            metrics[field] = value
        elif isinstance(value, int) and value >= 0:
            metrics[field] = value
        elif field == "apply_interface" and value == "unavailable":
            metrics[field] = value
    source_status = report.get("status")
    if source_status not in BROWSER_STATUSES:
        source_status = "unavailable"
    return {
        "schema_version": 1,
        "kind": "browser_audit_report_summary",
        "source_kind": source_kind,
        "stage": BROWSER_STAGE_BY_KIND[source_kind],
        "source_status": source_status,
        "overall_status": (
            "passed"
            if source_status in {"passed", "preview", "written", "unchanged"}
            else "review_required"
        ),
        "metrics": metrics,
        "private_content_emitted": False,
        "execution_authorized": False,
    }


def summarize(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("kind") in BROWSER_STAGE_BY_KIND:
        return _summarize_browser(report)
    if isinstance(report.get("kind"), str) and report["kind"].startswith(
        ("browser_", "safari_export_")
    ):
        raise ValueError("unsupported browser report kind")
    app = report.get("app_drift") if isinstance(report.get("app_drift"), dict) else {}
    permissions = report.get("permission_drift") if isinstance(report.get("permission_drift"), dict) else {}
    preferences = report.get("preference_drift") if isinstance(report.get("preference_drift"), dict) else {}
    missing_core = [item for item in app.get("missing_core", []) if isinstance(item, str)]
    mismatches = [_safe_name(item, "app") for item in app.get("source_mismatches", []) if isinstance(item, dict)]
    preference_count = len(preferences.get("mismatches", [])) if isinstance(preferences.get("mismatches"), list) else 0
    return {
        "schema_version": 1,
        "kind": "audit_report_summary",
        "captured_at": report.get("captured_at"),
        "overall_status": "review_required" if missing_core or mismatches or preference_count or any(value != 0 for value in report.get("step_returncodes", {}).values()) else "passed",
        "missing_core": missing_core,
        "source_mismatches": mismatches,
        "permission_counts": {key: value for key, value in permissions.items() if isinstance(value, int)},
        "preference_status": preferences.get("status", "unavailable"),
        "preference_mismatch_count": preference_count,
    }


def _browser_value(value: int | bool | str, locale_name: str) -> str:
    if value is True:
        return localization.message("browser.value.true", locale_name)
    if value is False:
        return localization.message("browser.value.false", locale_name)
    if value == "unavailable":
        return localization.message("browser.value.unavailable", locale_name)
    return str(value)


def _render_browser_tui(summary: dict[str, Any], lang: str) -> str:
    locale_name = _locale(lang)
    title = localization.message("browser.report.title", locale_name)
    status_label = localization.message("report.status", locale_name)
    status = localization.message(
        f"browser.status.{summary['source_status']}", locale_name
    )
    stage_label = localization.message("browser.stage", locale_name)
    stage = localization.message(f"browser.stage.{summary['stage']}", locale_name)
    lines = [
        title,
        f"{status_label}: {status}",
        f"{stage_label}: {stage}",
    ]
    for field, value in summary["metrics"].items():
        label = localization.message(f"browser.metric.{field}", locale_name)
        lines.append(f"{label}: {_browser_value(value, locale_name)}")
    lines.extend(
        [
            localization.message("browser.report.next", locale_name),
            localization.message("browser.report.policy", locale_name),
        ]
    )
    return "\n".join(lines) + "\n"


def _render_browser_html(summary: dict[str, Any], lang: str) -> str:
    locale_name = _locale(lang)
    title = localization.message("browser.report.title", locale_name)
    status_label = localization.message("report.status", locale_name)
    status = localization.message(
        f"browser.status.{summary['source_status']}", locale_name
    )
    stage_label = localization.message("browser.stage", locale_name)
    stage = localization.message(f"browser.stage.{summary['stage']}", locale_name)
    rows = [(stage_label, stage)]
    rows.extend(
        (
            localization.message(f"browser.metric.{field}", locale_name),
            _browser_value(value, locale_name),
        )
        for field, value in summary["metrics"].items()
    )
    table = "".join(
        f'<tr><th scope="row">{html.escape(label)}</th><td>{html.escape(value)}</td></tr>'
        for label, value in rows
    )
    next_text = localization.message("browser.report.next", locale_name)
    policy = localization.message("browser.report.policy", locale_name)
    return f'''<!doctype html>
<html lang="{html.escape(locale_name)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;line-height:1.5;margin:2rem;max-width:56rem}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #555;padding:.6rem;text-align:left}} .status{{font-weight:700}}</style></head>
<body><main id="browser-audit-report"><h1>{html.escape(title)}</h1><p class="status" aria-label="Status: {html.escape(status.lower())}">{html.escape(status_label)}: {html.escape(status)}</p>
<h2>{html.escape(stage_label)}</h2><table><tbody>{table}</tbody></table><h2>{html.escape(localization.message('report.next', locale_name))}</h2><p>{html.escape(next_text)}</p><p>{html.escape(policy)}</p></main></body></html>'''


def render_tui(summary: dict[str, Any], lang: str = "system") -> str:
    if summary.get("kind") == "browser_audit_report_summary":
        return _render_browser_tui(summary, lang)
    locale_name = _locale(lang)
    labels = {name: localization.message(f"report.{name}", locale_name) for name in ("title", "status", "passed", "review_required", "missing_core", "source_mismatches", "permission", "preferences", "next", "rerun", "none", "count", "policy")}
    status = labels[summary["overall_status"]]
    lines = [labels["title"], f"{labels['status']}: {status}"]
    lines.append(f"{labels['missing_core']}: " + (", ".join(summary["missing_core"]) or labels["none"]))
    lines.append(f"{labels['source_mismatches']}: " + (", ".join(summary["source_mismatches"]) or labels["none"]))
    preference_status = labels["passed"] if summary["preference_status"] == "match" else labels["review_required"] if summary["preference_status"] == "mismatch" else summary["preference_status"]
    lines.append(f"{labels['preferences']}: {preference_status} ({labels['count']}: {summary['preference_mismatch_count']})")
    if summary["permission_counts"]:
        lines.append(labels["permission"] + ": " + ", ".join(f"{key}={value}" for key, value in sorted(summary["permission_counts"].items())))
    lines.extend([f"{labels['next']}: {labels['rerun']}", labels["policy"]])
    return "\n".join(lines) + "\n"


def render_html(summary: dict[str, Any], lang: str = "system") -> str:
    if summary.get("kind") == "browser_audit_report_summary":
        return _render_browser_html(summary, lang)
    locale_name = _locale(lang)
    labels = {name: localization.message(f"report.{name}", locale_name) for name in ("title", "status", "passed", "review_required", "missing_core", "source_mismatches", "permission", "preferences", "next", "rerun", "none", "count", "policy")}
    status = labels[summary["overall_status"]]
    def list_items(values: list[str]) -> str:
        return "<li>" + "</li><li>".join(html.escape(item) for item in values) + "</li>" if values else f"<li>{html.escape(labels['none'])}</li>"
    rows = [
        (labels["missing_core"], ", ".join(summary["missing_core"]) or labels["none"]),
        (labels["source_mismatches"], ", ".join(summary["source_mismatches"]) or labels["none"]),
        (labels["preferences"], f"{labels['passed'] if summary['preference_status'] == 'match' else labels['review_required'] if summary['preference_status'] == 'mismatch' else summary['preference_status']} ({summary['preference_mismatch_count']})"),
    ]
    table = "".join(f"<tr><th scope=\"row\">{html.escape(key)}</th><td>{html.escape(value)}</td></tr>" for key, value in rows)
    return f'''<!doctype html>
<html lang="{html.escape(locale_name)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(labels['title'])}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;line-height:1.5;margin:2rem;max-width:56rem}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #555;padding:.6rem;text-align:left}} .status{{font-weight:700}}</style></head>
<body><main id="audit-report"><h1>{html.escape(labels['title'])}</h1><p class="status" aria-label="Status: {html.escape(status.lower())}">{html.escape(labels['status'])}: {html.escape(status)}</p>
<h2>{html.escape(labels['status'])}</h2><table><thead><tr><th scope="col">{html.escape(labels['status'])}</th><th scope="col">{html.escape(labels['count'])}</th></tr></thead><tbody>{table}</tbody></table>
<h2>{html.escape(labels['missing_core'])}</h2><ul>{list_items(summary['missing_core'])}</ul><h2>{html.escape(labels['next'])}</h2><p>{html.escape(labels['rerun'])}</p></main></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="existing JSON drift/audit report")
    parser.add_argument("--format", choices=["tui", "html", "json"], default="tui")
    parser.add_argument("--lang", default="system")
    parser.add_argument("--output", type=Path, help="write rendered report to a separate path")
    args = parser.parse_args()
    try:
        report = json.loads(args.input.read_text(encoding="utf-8"))
        summary = summarize(report)
        if args.format == "json":
            rendered = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
        elif args.format == "html":
            rendered = render_html(summary, args.lang)
        else:
            rendered = render_tui(summary, args.lang)
        if args.output:
            if args.output.exists():
                raise ValueError("output already exists")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(json.dumps({"output": str(args.output), "summary": summary}, ensure_ascii=False, indent=2))
        else:
            print(rendered, end="")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
