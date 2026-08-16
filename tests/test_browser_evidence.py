#!/usr/bin/env python3
"""TDD contracts for immutable Private Safari export evidence."""

from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_evidence  # noqa: E402


class BrowserEvidenceTests(unittest.TestCase):
    def export(self, root: Path, *, title: str = "Fictional") -> Path:
        path = root / "Safari Export.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as output:
            output.writestr(
                "Bookmarks.html",
                f"""<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p>
<DT><A HREF=\"https://example.invalid/\">{title}</A></DL><p>""",
            )
            output.writestr(
                "ReadingList.html",
                """<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p>
<DT><H3>com.apple.ReadingList</H3><DL><p>
<DT><A HREF=\"https://later.example.invalid/\">Later</A>
</DL><p></DL><p>""",
            )
        return path

    def test_preview_is_redacted_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.export(root)
            private = root / "Private"
            result = browser_evidence.import_evidence(
                source,
                exported_on="2026-08-15",
                apply=False,
                confirmation="",
                root=root,
                private_root=private,
            )
            self.assertEqual(result["status"], "preview")
            self.assertEqual(result["item_count"], 2)
            self.assertFalse(result["writes_performed"])
            self.assertFalse(private.exists())
            rendered = json.dumps(result)
            self.assertNotIn("example.invalid", rendered)
            self.assertNotIn(str(source), rendered)
            self.assertNotIn(hashlib.sha256(source.read_bytes()).hexdigest(), rendered)

    def test_exact_confirmation_copies_identical_bytes_mode_600(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.export(root)
            private = root / "Private"
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "IMPORT PRIVATE BROWSER EVIDENCE"):
                browser_evidence.import_evidence(
                    source,
                    exported_on="2026-08-15",
                    apply=True,
                    confirmation="wrong",
                    root=root,
                    private_root=private,
                )
            self.assertFalse(private.exists())

            result = browser_evidence.import_evidence(
                source,
                exported_on="2026-08-15",
                apply=True,
                confirmation="IMPORT PRIVATE BROWSER EVIDENCE",
                root=root,
                private_root=private,
            )
            destination = (
                private
                / "browser"
                / "evidence"
                / f"safari-export-2026-08-15-{digest[:12]}.zip"
            )
            self.assertEqual(result["status"], "written")
            self.assertEqual(destination.read_bytes(), source.read_bytes())
            self.assertEqual(destination.stat().st_mode & 0o777, 0o600)
            repeated = browser_evidence.import_evidence(
                source,
                exported_on="2026-08-15",
                apply=True,
                confirmation="IMPORT PRIVATE BROWSER EVIDENCE",
                root=root,
                private_root=private,
            )
            self.assertEqual(repeated["status"], "unchanged")
            self.assertFalse(repeated["writes_performed"])

    def test_conflicting_or_non_regular_destination_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.export(root)
            private = root / "Private"
            destination = browser_evidence.evidence_destination(
                source,
                exported_on="2026-08-15",
                private_root=private,
            )
            destination.parent.mkdir(parents=True)
            destination.write_bytes(b"different")
            with self.assertRaisesRegex(
                browser_evidence.BrowserEvidenceError,
                "different browser evidence",
            ):
                browser_evidence.import_evidence(
                    source,
                    exported_on="2026-08-15",
                    apply=True,
                    confirmation="IMPORT PRIVATE BROWSER EVIDENCE",
                    root=root,
                    private_root=private,
                )

    def test_invalid_date_or_export_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "not-export.zip"
            source.write_bytes(b"not a zip")
            for exported_on in ("2026-8-15", "2026-02-30"):
                with self.subTest(exported_on=exported_on):
                    with self.assertRaises(browser_evidence.BrowserEvidenceError):
                        browser_evidence.import_evidence(
                            source,
                            exported_on=exported_on,
                            apply=False,
                            confirmation="",
                            root=root,
                            private_root=root / "Private",
                        )

    def test_cli_failure_and_preview_never_emit_private_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.export(root)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = browser_evidence.main(
                    ["import-safari-export", str(source), "--exported-on", "2026-08-15"]
                )
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["status"], "preview")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                code = browser_evidence.main(
                    ["import-safari-export", "/missing/private.zip", "--exported-on", "2026-08-15"]
                )
            self.assertEqual(code, 1)
            self.assertFalse(json.loads(stderr.getvalue())["private_content_emitted"])


if __name__ == "__main__":
    unittest.main()
