#!/usr/bin/env python3
"""TDD contracts for explainable URL normalization and duplicate review."""

from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
ITEM_FIXTURE = ROOT / "tests" / "fixtures" / "schema_contract" / "browser-item-v1.json"
sys.path.insert(0, str(ROOT / "scripts"))

import browser_review  # noqa: E402
import schema_contract  # noqa: E402


class BrowserReviewTests(unittest.TestCase):
    def item(
        self,
        item_id: str,
        url: str,
        *,
        title: str = "Fictional item",
        browser: str = "safari",
        profile_scope: str = "shared_across_profiles",
        profile_ref: str | None = None,
        account_ref: str | None = None,
        collection: str = "bookmarks",
    ) -> dict:
        item = json.loads(ITEM_FIXTURE.read_text(encoding="utf-8"))
        item["item_id"] = item_id
        item["title"] = title
        item["url"]["original"] = url
        item["source"]["browser"] = browser
        item["source"]["profile_scope"] = profile_scope
        item["source"]["profile_ref"] = profile_ref
        item["source"]["account_ref"] = account_ref
        item["item_type"] = "reading_list" if collection == "reading_list" else "bookmark"
        item["collection"]["kind"] = collection
        item["collection"]["path"] = ["Reading List" if collection == "reading_list" else "Bookmarks"]
        item["read_state"] = "unknown" if collection == "reading_list" else "not_applicable"
        return item

    def test_registered_policy_is_valid_and_non_authorizing(self) -> None:
        result = browser_review.validate_policy()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertFalse(result["execution_authorized"])
        schema_contract.load_and_validate(
            ROOT / "settings" / "browser-url-normalization.json",
            "browser-url-policy",
        )

    def test_removes_only_allowlisted_tracking_parameters_and_preserves_structure(self) -> None:
        result = browser_review.normalize_url(
            "HTTPS://Example.INVALID:443/path/%2F?x=1&utm_source=newsletter&x=2&utm_content=top#section"
        )
        self.assertEqual(result["status"], "proposed")
        self.assertEqual(
            result["canonical_url"],
            "https://example.invalid/path/%2F?x=1&x=2#section",
        )
        self.assertEqual(result["removed_parameters"], ["utm_source", "utm_content"])
        self.assertIn("lowercase_scheme_and_host", result["rule_ids"])
        self.assertIn("remove_default_port", result["rule_ids"])
        self.assertTrue(result["fragment_preserved"])
        self.assertTrue(result["query_order_preserved"])

    def test_signed_or_identity_sensitive_query_blocks_all_changes(self) -> None:
        original = (
            "https://files.example.invalid/report?utm_source=email"
            "&X-Amz-Signature=abc&X-Amz-Expires=60"
        )
        result = browser_review.normalize_url(original)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["canonical_url"])
        self.assertEqual(result["removed_parameters"], [])
        self.assertIn("protected_query_parameter", result["blocked_reasons"])
        self.assertNotIn("abc", json.dumps(result))

    def test_semantic_parameters_repeats_fragment_and_non_default_port_are_preserved(self) -> None:
        original = "https://Example.invalid:8443/view?ref=mail&source=app&id=1&id=2#part-2"
        result = browser_review.normalize_url(original)
        self.assertEqual(
            result["canonical_url"],
            "https://example.invalid:8443/view?ref=mail&source=app&id=1&id=2#part-2",
        )
        self.assertEqual(result["removed_parameters"], [])
        self.assertNotIn("remove_default_port", result["rule_ids"])

    def test_unsupported_or_credentialed_urls_are_not_normalized(self) -> None:
        for url, reason in (
            ("mailto:person@example.invalid", "unsupported_scheme"),
            ("https://user:password@example.invalid/private", "userinfo_present"),
            ("https:///missing-host", "missing_host"),
            ("https://example.invalid/?utm_source=x;id=42", "ambiguous_query_separator"),
            ("https://example.invalid\\@evil.invalid/path", "ambiguous_authority"),
        ):
            with self.subTest(url=url):
                result = browser_review.normalize_url(url)
                self.assertEqual(result["status"], "blocked")
                self.assertIn(reason, result["blocked_reasons"])
                self.assertIsNone(result["canonical_url"])

    def test_empty_query_and_fragment_delimiters_are_not_silently_dropped(self) -> None:
        self.assertEqual(
            browser_review.normalize_url("https://example.invalid/path?")["canonical_url"],
            "https://example.invalid/path?",
        )
        self.assertEqual(
            browser_review.normalize_url("https://example.invalid/path#")["canonical_url"],
            "https://example.invalid/path#",
        )

    def test_duplicate_review_is_explainable_and_stays_within_identity_boundary(self) -> None:
        safari_one = self.item(
            "bri_fixture_00000011",
            "https://example.invalid/article?id=42&utm_source=newsletter",
            title="First title",
        )
        safari_two = self.item(
            "bri_fixture_00000012",
            "https://EXAMPLE.invalid:443/article?id=42&utm_medium=email",
            title="Second title",
            collection="reading_list",
        )
        chrome_other_profile = self.item(
            "bri_fixture_00000013",
            "https://example.invalid/article?id=42",
            browser="chrome",
            profile_scope="profile_specific",
            profile_ref="fictional-profile-b",
            account_ref="fictional-account-b",
        )

        result = browser_review.review_items(
            [safari_one, safari_two, chrome_other_profile]
        )
        self.assertEqual(len(result["duplicate_groups"]), 1)
        group = result["duplicate_groups"][0]
        self.assertEqual(
            group["member_item_ids"],
            ["bri_fixture_00000011", "bri_fixture_00000012"],
        )
        self.assertEqual(group["match_type"], "canonical_url_match")
        self.assertEqual(group["confidence"], "medium")
        self.assertFalse(group["cross_identity_boundary"])
        self.assertFalse(group["execution_authorized"])
        self.assertIn("title_mismatch", group["evidence_types"])
        self.assertIn("collection_mismatch", group["evidence_types"])
        self.assertNotIn("bri_fixture_00000013", group["member_item_ids"])

        reviewed = {item["item_id"]: item for item in result["items"]}
        for item_id in ("bri_fixture_00000011", "bri_fixture_00000012"):
            self.assertEqual(reviewed[item_id]["url"]["canonicalization_status"], "proposed")
            self.assertTrue(reviewed[item_id]["conflict_evidence"])
            self.assertEqual(schema_contract.validate_document(reviewed[item_id], "browser-item"), [])

    def test_identical_urls_in_different_profiles_do_not_form_a_group(self) -> None:
        items = [
            self.item(
                "bri_fixture_00000021",
                "https://example.invalid/same",
                browser="chrome",
                profile_scope="profile_specific",
                profile_ref="profile-a",
                account_ref="account-a",
            ),
            self.item(
                "bri_fixture_00000022",
                "https://example.invalid/same",
                browser="chrome",
                profile_scope="profile_specific",
                profile_ref="profile-b",
                account_ref="account-b",
            ),
        ]
        result = browser_review.review_items(items)
        self.assertEqual(result["duplicate_groups"], [])
        self.assertEqual(result["cross_identity_groups"], 0)
        self.assertEqual(result["cross_identity_collisions_suppressed"], 1)

    def test_cli_summary_never_emits_urls_titles_paths_or_item_ids(self) -> None:
        html = b"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p><DT><A HREF=\"https://secret.example.invalid/a?utm_source=x\">PRIVATE TITLE</A>
<DT><A HREF=\"https://secret.example.invalid/a\">PRIVATE DUPLICATE</A></DL><p>"""
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "private-export.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
                output.writestr("Bookmarks.html", html)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                returncode = browser_review.main(["inspect-safari-export", str(archive)])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(returncode, 0)
        self.assertEqual(payload["duplicate_group_count"], 1)
        self.assertFalse(payload["private_content_emitted"])
        self.assertFalse(payload["execution_authorized"])
        rendered = stdout.getvalue()
        for secret in ("secret.example.invalid", "PRIVATE TITLE", "bri_", "private-export.zip"):
            self.assertNotIn(secret, rendered)

    def test_private_duplicate_export_is_preview_only_by_default(self) -> None:
        html = b"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p><DT><A HREF=\"https://secret.example.invalid/a\">PRIVATE TITLE</A>
<DT><A HREF=\"https://secret.example.invalid/a\">PRIVATE DUPLICATE</A></DL><p>"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_root = root / "Private"
            archive = root / "private-export.zip"
            output = private_root / "browser" / "duplicate-review.json"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as target:
                target.writestr("Bookmarks.html", html)
            stdout = io.StringIO()
            with mock.patch.object(browser_review, "ROOT", root), mock.patch.object(
                browser_review, "PRIVATE_ROOT", private_root
            ), redirect_stdout(stdout):
                returncode = browser_review.main(
                    [
                        "export-private-duplicates",
                        str(archive),
                        "--output",
                        str(output),
                    ]
                )
            self.assertFalse(output.exists())

        payload = json.loads(stdout.getvalue())
        self.assertEqual(returncode, 0)
        self.assertEqual(payload["status"], "preview")
        self.assertEqual(payload["duplicate_group_count"], 1)
        self.assertEqual(payload["duplicate_item_count"], 2)
        self.assertTrue(payload["would_write"])
        self.assertFalse(payload["writes_performed"])
        for secret in (
            "secret.example.invalid",
            "PRIVATE TITLE",
            "bri_",
            "duplicate-review.json",
            str(private_root),
        ):
            self.assertNotIn(secret, stdout.getvalue())

    def test_private_duplicate_export_requires_exact_confirmation_and_writes_mode_0600(self) -> None:
        html = b"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p><DT><A HREF=\"https://secret.example.invalid/a\">PRIVATE TITLE</A>
<DT><A HREF=\"https://secret.example.invalid/a\">PRIVATE DUPLICATE</A></DL><p>"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_root = root / "Private"
            archive = root / "private-export.zip"
            output = private_root / "browser" / "duplicate-review.json"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as target:
                target.writestr("Bookmarks.html", html)

            with mock.patch.object(browser_review, "ROOT", root), mock.patch.object(
                browser_review, "PRIVATE_ROOT", private_root
            ):
                stderr = io.StringIO()
                with redirect_stdout(io.StringIO()), mock.patch("sys.stderr", stderr):
                    wrong_code = browser_review.main(
                        [
                            "export-private-duplicates",
                            str(archive),
                            "--output",
                            str(output),
                            "--apply",
                            "--confirm",
                            "wrong",
                        ]
                    )
                self.assertEqual(wrong_code, 1)
                self.assertFalse(output.exists())

                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    returncode = browser_review.main(
                        [
                            "export-private-duplicates",
                            str(archive),
                            "--output",
                            str(output),
                            "--apply",
                            "--confirm",
                            "EXPORT PRIVATE BROWSER REVIEW",
                        ]
                    )

            self.assertEqual(returncode, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "written")
            self.assertTrue(payload["writes_performed"])
            self.assertFalse(payload["private_content_emitted"])
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            private_payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                schema_contract.validate_document(
                    private_payload, "browser-private-duplicate-review"
                ),
                [],
            )
            self.assertEqual(private_payload["duplicate_group_count"], 1)
            self.assertEqual(private_payload["duplicate_item_count"], 2)
            self.assertIn("PRIVATE TITLE", json.dumps(private_payload))
            self.assertFalse(private_payload["execution_authorized"])
            self.assertNotIn("PRIVATE TITLE", stdout.getvalue())

    def test_private_duplicate_export_refuses_non_private_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_root = root / "Private"
            with self.assertRaisesRegex(browser_review.BrowserReviewError, "Private/browser"):
                browser_review.resolve_private_output(
                    root / "public-review.json",
                    root=root,
                    private_root=private_root,
                )


if __name__ == "__main__":
    unittest.main()
