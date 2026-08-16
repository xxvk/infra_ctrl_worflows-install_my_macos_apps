from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeepSeekHarnessMigrationDocsTests(unittest.TestCase):
    def test_vl_migration_contract_is_persistent_and_secret_safe(self) -> None:
        operations = (
            ROOT / "references" / "deepseek-harness-operations.md"
        ).read_text(encoding="utf-8")

        required_contract = (
            "Provider and VL migration into an isolated Desktop profile",
            "DASHSCOPE_API_KEY",
            "Never bulk-copy or replace `.credentials.yaml`",
            "Apply the desired default model through the running Harness",
            "Quit and relaunch once more",
            "Do not send a paid model request",
        )
        for statement in required_contract:
            self.assertIn(statement, operations)

    def test_component_routes_to_provider_migration_contract(self) -> None:
        component = (
            ROOT / "components" / "deepseek-harness-desktop.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "#provider-and-vl-migration-into-an-isolated-desktop-profile",
            component,
        )
        self.assertIn(
            "Never replace the destination credential or settings file wholesale",
            component,
        )

    def test_anywhere_v2_is_blocked_and_recovery_is_profile_aware(self) -> None:
        component = (
            ROOT / "components" / "deepseek-harness-desktop.md"
        ).read_text(encoding="utf-8")
        operations = (
            ROOT / "references" / "deepseek-harness-operations.md"
        ).read_text(encoding="utf-8")

        self.assertIn("anywhere-labs/deepseek-harness-desktop` v2.0.0", component)
        self.assertIn("blocked and must not be installed", component)
        self.assertIn("not a claim that", component)
        for expected in (
            "identify the profile from the",
            "actual Host process arguments",
            "computer-use-host",
            "computer-use-tool",
            "exactly once",
            "dynamic loopback port",
            "Polyglot",
        ):
            self.assertIn(expected, operations)


if __name__ == "__main__":
    unittest.main()
